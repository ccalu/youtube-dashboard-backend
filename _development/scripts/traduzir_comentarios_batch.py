"""
Script de Traducao em Batch de Comentarios
===========================================
FUNCIONALIDADES:
1. GPT-4o-mini direto via httpx (sem depender de OptimizedTranslator)
2. Batches de 15 comentarios por vez (seguro para max_tokens)
3. NAO traduz portugues (ja salvo como PT na coleta)
4. NAO traduz ja traduzidos (is_translated=True)
5. Paginacao completa sem limites
6. Checkpoint apos cada batch (salva no banco imediatamente)
7. Resume de onde parou
8. Retry com batch menor quando GPT trunca a resposta
9. Textos truncados a 500 chars para evitar overflow
10. Max 3 erros consecutivos no mesmo batch antes de pular

Autor: Claude Code para Cellibs
Data: 13/02/2026
"""

import os
import sys
import json
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Configurar encoding UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traducao_batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar variaveis de ambiente
load_dotenv()

# Configurar Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
openai_api_key_raw = os.getenv('OPENAI_API_KEY')

if not supabase_url or not supabase_service_key:
    logger.error("Credenciais Supabase nao configuradas!")
    sys.exit(1)

if not openai_api_key_raw:
    logger.error("OPENAI_API_KEY nao configurada!")
    sys.exit(1)

OPENAI_API_KEY = openai_api_key_raw.strip().replace('\n', '').replace('\r', '').replace(' ', '')
supabase: Client = create_client(supabase_url, supabase_service_key)

# Configuracoes
CHECKPOINT_FILE = 'traducao_checkpoint.json'
BATCH_SIZE = 15  # 15 comentarios por batch (seguro para max_tokens)
MAX_TEXT_LENGTH = 500  # Truncar textos muito longos
MAX_RETRIES_PER_BATCH = 3  # Maximo de retries antes de pular


def load_checkpoint() -> Dict:
    """Carrega checkpoint se existir"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Checkpoint carregado: {data.get('total_traduzidos', 0)} ja traduzidos nesta execucao")
            return data
    return {'total_traduzidos': 0, 'erros': 0}


def save_checkpoint(stats: Dict):
    """Salva checkpoint"""
    stats['ultima_atualizacao'] = datetime.now(timezone.utc).isoformat()
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)


def get_canais_portugues() -> List[int]:
    """Busca IDs dos canais em portugues (NAO precisam traducao)"""
    canais = supabase.table('canais_monitorados').select('id, lingua').eq('tipo', 'nosso').execute().data

    canais_pt = []
    for canal in canais:
        lingua = canal.get('lingua', '')
        if lingua:
            lingua_lower = lingua.lower()
            if 'portug' in lingua_lower or lingua_lower in ['portuguese', 'pt', 'pt-br']:
                canais_pt.append(canal['id'])

    return canais_pt


def get_pending_comments(canais_pt: List[int], batch_size: int = 15) -> List[Dict]:
    """Busca comentarios que precisam de traducao"""
    try:
        query = supabase.table('video_comments').select(
            'id, comment_text_original, canal_id'
        ).eq('is_translated', False)

        if canais_pt:
            for canal_id in canais_pt:
                query = query.neq('canal_id', canal_id)

        response = query.limit(batch_size).execute()
        return response.data if response.data else []

    except Exception as e:
        logger.error(f"Erro ao buscar comentarios pendentes: {e}")
        return []


def count_pending_comments(canais_pt: List[int]) -> int:
    """Conta total de comentarios pendentes de traducao"""
    try:
        query = supabase.table('video_comments').select(
            'id', count='exact'
        ).eq('is_translated', False)

        if canais_pt:
            for canal_id in canais_pt:
                query = query.neq('canal_id', canal_id)

        result = query.execute()
        return result.count if result.count else 0

    except Exception as e:
        logger.error(f"Erro ao contar pendentes: {e}")
        return 0


def save_translations_to_db(translations_data: List[Dict]) -> int:
    """Salva traducoes no banco de dados, uma por uma para garantir"""
    saved = 0
    now_utc = datetime.now(timezone.utc).isoformat()

    for item in translations_data:
        try:
            supabase.table('video_comments').update({
                'comment_text_pt': item['translation'],
                'is_translated': True,
                'updated_at': now_utc,
            }).eq('id', item['db_id']).execute()
            saved += 1

        except Exception as e:
            logger.error(f"Erro ao salvar traducao ID {item['db_id']}: {e}")

    return saved


async def translate_batch_gpt(texts: List[str], client: httpx.AsyncClient) -> Optional[List[str]]:
    """Traduz batch de textos via GPT-4o-mini com max_tokens adequado"""

    # Truncar textos longos
    truncated = [t[:MAX_TEXT_LENGTH] if len(t) > MAX_TEXT_LENGTH else t for t in texts]

    comments_json = json.dumps(
        [{"id": idx, "text": text} for idx, text in enumerate(truncated)],
        ensure_ascii=False
    )

    system_prompt = """Voce e um tradutor especializado em adaptar textos para portugues brasileiro.

TAREFA: Traduza os comentarios para PT-BR mantendo o tom e contexto original.

DIRETRIZES:
1. Se ja estiver em portugues, retorne como esta
2. Adapte girias e expressoes culturais quando possivel
3. Mantenha emojis e formatacao
4. Use linguagem natural brasileira (nao traducao literal)
5. Retorne APENAS um JSON array com os textos traduzidos na mesma ordem

FORMATO DE RESPOSTA:
["texto traduzido 1", "texto traduzido 2", ...]"""

    user_prompt = f"Traduza estes {len(truncated)} comentarios para PT-BR:\n{comments_json}"

    # Calcular max_tokens proporcional (media ~80 tokens por traducao)
    estimated_tokens = len(texts) * 120 + 200
    max_tokens = min(max(estimated_tokens, 2000), 8000)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=90.0
        )

        if response.status_code != 200:
            logger.error(f"API OpenAI erro: {response.status_code} - {response.text[:200]}")
            return None

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Verificar se resposta foi truncada (finish_reason != stop)
        finish_reason = data["choices"][0].get("finish_reason", "stop")
        if finish_reason != "stop":
            logger.warning(f"Resposta truncada (finish_reason={finish_reason}), batch muito grande")
            return None

        # Limpar marcadores de codigo
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        translations = json.loads(content)

        if isinstance(translations, list) and len(translations) == len(texts):
            return translations
        else:
            logger.error(f"Retornou {len(translations) if isinstance(translations, list) else 'nao-lista'} de {len(texts)} esperados")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"JSON invalido da GPT: {e}")
        return None
    except httpx.TimeoutException:
        logger.error("Timeout na chamada OpenAI")
        return None
    except Exception as e:
        logger.error(f"Erro na traducao GPT: {e}")
        return None


async def translate_with_retry(texts: List[str], db_ids: List[int], client: httpx.AsyncClient) -> List[Dict]:
    """Traduz com retry inteligente - divide batch pela metade se falhar"""
    results = []

    # Tentar batch completo
    translations = await translate_batch_gpt(texts, client)
    if translations:
        for idx, translation in enumerate(translations):
            results.append({'db_id': db_ids[idx], 'translation': translation})
        return results

    # Se batch > 1, dividir pela metade e tentar cada parte
    if len(texts) > 1:
        mid = len(texts) // 2
        logger.info(f"    Dividindo batch: {len(texts)} -> {mid} + {len(texts)-mid}")

        left = await translate_with_retry(texts[:mid], db_ids[:mid], client)
        results.extend(left)
        await asyncio.sleep(1)

        right = await translate_with_retry(texts[mid:], db_ids[mid:], client)
        results.extend(right)

        return results

    # Batch de 1 ainda falhou - marcar como traduzido com texto original
    logger.warning(f"    Comentario ID {db_ids[0]} nao traduziu, salvando original")
    results.append({'db_id': db_ids[0], 'translation': texts[0]})
    return results


async def traduzir_todos():
    """Funcao principal de traducao em batch"""

    logger.info("=" * 80)
    logger.info("TRADUCAO EM BATCH - INICIANDO")
    logger.info("=" * 80)

    # Identificar canais portugues
    canais_pt = get_canais_portugues()
    logger.info(f"Canais em portugues (ignorados): {len(canais_pt)} canais")

    # Contar pendentes
    total_pendentes = count_pending_comments(canais_pt)
    logger.info(f"Comentarios pendentes de traducao: {total_pendentes}")

    if total_pendentes == 0:
        logger.info("Nenhum comentario para traduzir!")
        return

    # Carregar checkpoint
    checkpoint = load_checkpoint()
    stats = {
        'total_traduzidos': checkpoint.get('total_traduzidos', 0),
        'erros': checkpoint.get('erros', 0),
        'inicio': checkpoint.get('inicio', datetime.now(timezone.utc).isoformat()),
        'batches_processados': checkpoint.get('batches_processados', 0),
    }

    logger.info(f"Total a traduzir: {total_pendentes}")
    logger.info(f"Ja traduzidos nesta execucao: {stats['total_traduzidos']}")
    logger.info(f"Batch size: {BATCH_SIZE} | Max texto: {MAX_TEXT_LENGTH} chars")
    logger.info("")

    batch_num = stats['batches_processados']
    consecutive_errors = 0

    async with httpx.AsyncClient() as client:
        # Loop ate nao ter mais pendentes
        while True:
            # Buscar proximo batch
            pending = get_pending_comments(canais_pt, BATCH_SIZE)

            if not pending:
                logger.info("Nenhum comentario pendente restante!")
                break

            batch_num += 1

            # Preparar textos para traducao
            texts = []
            db_ids = []

            for comment in pending:
                text = (comment.get('comment_text_original') or '').strip()
                if text:
                    texts.append(text)
                    db_ids.append(comment['id'])

            if not texts:
                logger.warning(f"Batch {batch_num}: Nenhum texto valido, pulando")
                # Marcar como traduzidos (comentarios vazios)
                for comment in pending:
                    try:
                        supabase.table('video_comments').update({
                            'is_translated': True,
                            'comment_text_pt': '',
                            'updated_at': datetime.now(timezone.utc).isoformat(),
                        }).eq('id', comment['id']).execute()
                    except Exception:
                        pass
                continue

            logger.info(f"BATCH {batch_num}: Traduzindo {len(texts)} comentarios...")

            # Traduzir com retry inteligente
            try:
                translations_data = await translate_with_retry(texts, db_ids, client)

                if translations_data:
                    saved = save_translations_to_db(translations_data)
                    stats['total_traduzidos'] += saved
                    stats['batches_processados'] = batch_num
                    consecutive_errors = 0

                    remaining = total_pendentes - stats['total_traduzidos']
                    logger.info(f"  Batch {batch_num}: {saved} traduzidos | Total: {stats['total_traduzidos']} | ~Restantes: {remaining}")
                else:
                    stats['erros'] += 1
                    consecutive_errors += 1
                    logger.error(f"  Batch {batch_num}: Falhou completamente")

                # Salvar checkpoint
                save_checkpoint(stats)

                # Pausa entre batches
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Erro no batch {batch_num}: {e}")
                stats['erros'] += 1
                consecutive_errors += 1
                save_checkpoint(stats)
                await asyncio.sleep(3)

            # Se muitos erros consecutivos, algo esta errado
            if consecutive_errors >= 5:
                logger.error("5 erros consecutivos! Abortando para evitar loop infinito.")
                break

    # Relatorio final
    stats['fim'] = datetime.now(timezone.utc).isoformat()

    logger.info("")
    logger.info("=" * 80)
    logger.info("RELATORIO FINAL DE TRADUCAO")
    logger.info("=" * 80)
    logger.info(f"  Batches processados: {batch_num}")
    logger.info(f"  Comentarios traduzidos: {stats['total_traduzidos']}")
    logger.info(f"  Erros: {stats['erros']}")

    # Verificar se completou
    remaining = count_pending_comments(canais_pt)
    if remaining == 0:
        logger.info("TRADUCAO 100% COMPLETA!")
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            logger.info("Checkpoint removido (traducao finalizada)")
    else:
        logger.warning(f"TRADUCAO INCOMPLETA: {remaining} comentarios pendentes")
        logger.info("Execute novamente para continuar de onde parou")

    logger.info("=" * 80)

    return stats


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    logger.info("Iniciando traducao em batch...")
    stats = asyncio.run(traduzir_todos())
    logger.info("Script finalizado!")
