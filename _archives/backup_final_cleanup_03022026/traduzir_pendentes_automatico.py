"""
Script automático para traduzir comentários pendentes
Pode rodar a cada 30 minutos via cron/scheduler
Para quando não há mais nada para traduzir
100% autônomo e resiliente
"""

import asyncio
import sys
import io
from datetime import datetime
from database import SupabaseClient
from translate_comments_optimized import OptimizedTranslator
from dotenv import load_dotenv
import logging

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def traduzir_todos_pendentes():
    """
    Traduz TODOS os comentários pendentes de TODOS os canais
    Para automaticamente quando não há mais nada para traduzir
    """

    print("=" * 80)
    print("TRADUÇÃO AUTOMÁTICA DE COMENTÁRIOS PENDENTES")
    print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Inicializar
    db = SupabaseClient()
    translator = OptimizedTranslator()

    # ============================
    # 1. VERIFICAR SE HÁ PENDENTES
    # ============================
    print("\n🔍 Verificando comentários pendentes...")

    # Contar total de pendentes
    pendentes_total = db.supabase.table('video_comments')\
        .select('id', count='exact')\
        .eq('is_translated', False)\
        .execute()

    if pendentes_total.count == 0:
        print("✅ Nenhum comentário pendente de tradução!")
        print("Sistema 100% traduzido. Nada a fazer.")
        return 0  # Retorna 0 indicando sucesso sem trabalho

    print(f"📊 Total de comentários pendentes: {pendentes_total.count}")

    # ============================
    # 2. AGRUPAR POR CANAL
    # ============================
    print("\n📂 Agrupando comentários por canal...")

    # Buscar canais com comentários pendentes (exceto português)
    canais_query = """
    SELECT DISTINCT
        vc.canal_id,
        cm.nome_canal,
        cm.lingua,
        COUNT(vc.id) as pendentes
    FROM video_comments vc
    JOIN canais_monitorados cm ON vc.canal_id = cm.id
    WHERE vc.is_translated = false
    AND (cm.lingua NOT ILIKE '%portug%' OR cm.lingua IS NULL)
    GROUP BY vc.canal_id, cm.nome_canal, cm.lingua
    ORDER BY pendentes DESC
    """

    # Como Supabase não suporta SQL direto, vamos fazer diferente
    # Buscar APENAS CANAIS NOSSOS (tipo="nosso")
    canais_response = db.supabase.table('canais_monitorados')\
        .select('id, nome_canal, lingua')\
        .eq('tipo', 'nosso')\
        .execute()

    canais_com_pendentes = []

    for canal in canais_response.data:
        # Pular canais em português
        lingua = canal.get('lingua', '').lower()
        if 'portug' in lingua or lingua in ['portuguese', 'português', 'pt', 'pt-br']:
            continue

        # Contar pendentes do canal
        pendentes = db.supabase.table('video_comments')\
            .select('id', count='exact')\
            .eq('canal_id', canal['id'])\
            .eq('is_translated', False)\
            .execute()

        if pendentes.count > 0:
            canais_com_pendentes.append({
                'id': canal['id'],
                'nome': canal['nome_canal'],
                'lingua': canal.get('lingua', 'unknown'),
                'pendentes': pendentes.count
            })

    if not canais_com_pendentes:
        print("✅ Todos os comentários de canais não-PT já estão traduzidos!")
        return 0

    # Ordenar por quantidade de pendentes (maior primeiro)
    canais_com_pendentes.sort(key=lambda x: x['pendentes'], reverse=True)

    print(f"📋 {len(canais_com_pendentes)} canais com comentários pendentes:")
    for c in canais_com_pendentes[:5]:  # Mostrar top 5
        print(f"   - {c['nome']} ({c['lingua']}): {c['pendentes']} pendentes")

    # ============================
    # 3. PROCESSAR CADA CANAL
    # ============================
    total_traduzidos_geral = 0
    canais_processados = 0
    erros_totais = 0

    for canal_info in canais_com_pendentes:
        canal_id = canal_info['id']
        canal_nome = canal_info['nome']
        total_pendentes = canal_info['pendentes']

        print(f"\n{'='*60}")
        print(f"🎯 Canal: {canal_nome} (ID: {canal_id})")
        print(f"   Língua: {canal_info['lingua']}")
        print(f"   Pendentes: {total_pendentes}")
        print(f"{'='*60}")

        traduzidos_canal = 0
        erros_canal = 0
        rodadas = 0

        # Loop até traduzir todos do canal
        while True:
            rodadas += 1

            # Buscar próximo lote
            response = db.supabase.table('video_comments')\
                .select('id, comment_text_original')\
                .eq('canal_id', canal_id)\
                .eq('is_translated', False)\
                .limit(50)\
                .execute()

            if not response.data:
                print(f"   ✅ Canal {canal_nome} completamente traduzido!")
                break

            comentarios = response.data
            print(f"\n   📦 Rodada {rodadas}: {len(comentarios)} comentários")

            # Processar em batches de 20
            batch_size = 20
            for i in range(0, len(comentarios), batch_size):
                batch = comentarios[i:i+batch_size]
                textos = [c['comment_text_original'] for c in batch]

                print(f"      Processando batch {i//batch_size + 1} ({len(batch)} textos)...")

                # Tentar traduzir com retry
                sucesso = False
                for tentativa in range(3):
                    try:
                        # Traduzir
                        traducoes = await translator.translate_batch(textos)

                        # Salvar no banco
                        for j, comentario in enumerate(batch):
                            if j < len(traducoes) and traducoes[j]:
                                update = db.supabase.table('video_comments')\
                                    .update({
                                        'comment_text_pt': traducoes[j],
                                        'is_translated': True
                                    })\
                                    .eq('id', comentario['id'])\
                                    .execute()

                                if update.data:
                                    traduzidos_canal += 1

                        sucesso = True
                        print(f"      ✅ Batch traduzido com sucesso")
                        break  # Sai do loop de retry

                    except Exception as e:
                        if tentativa < 2:
                            wait_time = 5 * (tentativa + 1)
                            print(f"      ⚠️ Erro (tentativa {tentativa + 1}/3): {e}")
                            print(f"      Aguardando {wait_time}s antes de tentar novamente...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"      ❌ Erro após 3 tentativas: {e}")
                            erros_canal += len(batch)

                # Rate limiting entre batches
                await asyncio.sleep(2)

            # Se não traduziu nada nesta rodada, parar
            if traduzidos_canal == 0 and rodadas > 1:
                print(f"   ⚠️ Não conseguiu traduzir mais nada, parando...")
                break

        print(f"\n   📊 Resumo do canal {canal_nome}:")
        print(f"      Traduzidos: {traduzidos_canal}")
        print(f"      Erros: {erros_canal}")
        print(f"      Rodadas: {rodadas}")

        total_traduzidos_geral += traduzidos_canal
        erros_totais += erros_canal
        canais_processados += 1

        # Pausa entre canais
        if canais_processados < len(canais_com_pendentes):
            print("\n   ⏸️ Aguardando 3s antes do próximo canal...")
            await asyncio.sleep(3)

    # ============================
    # 4. VERIFICAÇÃO FINAL
    # ============================
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO FINAL")
    print("=" * 80)

    # Recontar pendentes
    pendentes_final = db.supabase.table('video_comments')\
        .select('id', count='exact')\
        .eq('is_translated', False)\
        .execute()

    # ============================
    # RESUMO
    # ============================
    print("\n" + "=" * 80)
    print("RESUMO DA TRADUÇÃO AUTOMÁTICA")
    print("=" * 80)

    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  - Pendentes inicial: {pendentes_total.count}")
    print(f"  - Canais processados: {canais_processados}")
    print(f"  - Comentários traduzidos: {total_traduzidos_geral}")
    print(f"  - Erros: {erros_totais}")
    print(f"  - Pendentes final: {pendentes_final.count}")

    taxa_sucesso = (total_traduzidos_geral / pendentes_total.count * 100) if pendentes_total.count > 0 else 0
    print(f"  - Taxa de sucesso: {taxa_sucesso:.1f}%")

    if pendentes_final.count == 0:
        print("\n🎉 SISTEMA 100% TRADUZIDO!")
        print("Todos os comentários foram traduzidos com sucesso.")
        return 0  # Sucesso completo
    elif pendentes_final.count < pendentes_total.count:
        print(f"\n✅ PROGRESSO: Reduziu de {pendentes_total.count} para {pendentes_final.count} pendentes")
        print("Execute novamente se necessário.")
        return 1  # Sucesso parcial
    else:
        print("\n⚠️ Nenhum progresso foi feito. Verifique os logs de erro.")
        return 2  # Falha

if __name__ == "__main__":
    # Executar e retornar código de saída
    exit_code = asyncio.run(traduzir_todos_pendentes())

    # Mensagem final baseada no código
    if exit_code == 0:
        print("\n✅ Script finalizado com sucesso - Nada mais a traduzir!")
    elif exit_code == 1:
        print("\n⚠️ Script finalizado - Ainda há pendentes, execute novamente se necessário")
    else:
        print("\n❌ Script finalizado com erros - Verifique os logs")

    sys.exit(exit_code)