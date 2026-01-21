"""
FASE 4 - ETAPA 2: Analisar TODOS os comentários pendentes com GPT
Analisa e salva análises dos comentários coletados na ETAPA 1
"""
import sys
import io
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from database import SupabaseClient
from gpt_analyzer import GPTAnalyzer
import json

# Configurar encoding UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

print("\n" + "="*80)
print("ETAPA 2: ANALISE DE TODOS OS COMENTARIOS COLETADOS")
print("Analisa comentarios pendentes (analyzed_at=NULL) com GPT")
print("="*80)
print("\nAVISO: Esta analise pode usar muitos tokens GPT!")
print("Para automaticamente ao atingir 90% do limite diario")

async def analisar_todos():
    db = SupabaseClient()
    start_time = time.time()

    # Estatísticas
    stats = {
        'total_pendentes': 0,
        'analisados': 0,
        'salvos': 0,
        'erros': 0,
        'tokens_usados': 0,
        'batches_processados': 0
    }

    # 1. Buscar TODOS os comentários pendentes
    print("\n[1] Buscando comentarios pendentes de analise...")

    response = db.supabase.table('video_comments')\
        .select('*')\
        .is_('analyzed_at', 'null')\
        .execute()

    pendentes = response.data if response.data else []
    stats['total_pendentes'] = len(pendentes)

    print(f">>> {stats['total_pendentes']:,} comentarios pendentes")

    if stats['total_pendentes'] == 0:
        print("Nenhum comentario pendente - todos ja analisados!")
        return stats

    # 2. Inicializar GPT Analyzer
    print("\n[2] Inicializando GPT Analyzer...")

    try:
        analyzer = GPTAnalyzer()
        print(f">>> Modelo: {analyzer.model}")
        print(f">>> Limite diario: 1.000.000 tokens")
    except Exception as e:
        print(f"ERRO ao inicializar GPT: {e}")
        return stats

    # 3. Processar em batches
    print(f"\n[3] Processando {stats['total_pendentes']:,} comentarios em batches de 100...")
    print("="*80)

    batch_size = 100
    total_batches = (stats['total_pendentes'] + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, stats['total_pendentes'])
        batch_comments = pendentes[start_idx:end_idx]

        print(f"\n[BATCH {batch_num + 1}/{total_batches}] Processando comentarios {start_idx + 1}-{end_idx}...")

        # Preparar para análise
        comments_for_gpt = []
        for comment in batch_comments:
            comments_for_gpt.append({
                'comment_id': comment.get('comment_id'),
                'text': comment.get('comment_text_original', ''),
                'author': comment.get('author_name', 'Unknown'),
                'published_at': comment.get('published_at', ''),
                'like_count': comment.get('like_count', 0)
            })

        # Analisar com GPT
        try:
            analyzed = await analyzer.analyze_batch(
                comments=comments_for_gpt,
                video_title="Batch de comentarios historicos",
                canal_name="Diversos canais"
            )

            if analyzed and len(analyzed) > 0:
                stats['analisados'] += len(analyzed)
                stats['batches_processados'] += 1

                # Salvar análises no banco
                for analyzed_comment in analyzed:
                    try:
                        comment_id = analyzed_comment.get('comment_id')
                        gpt_analysis = analyzed_comment.get('gpt_analysis', {})

                        if not gpt_analysis:
                            continue

                        sentiment = gpt_analysis.get('sentiment', {})

                        update_data = {
                            'gpt_analysis': json.dumps(gpt_analysis),
                            'analyzed_at': datetime.utcnow().isoformat(),
                            'sentiment_category': sentiment.get('category'),
                            'sentiment_score': sentiment.get('score'),
                            'sentiment_confidence': sentiment.get('confidence'),
                            'primary_category': gpt_analysis.get('primary_category'),
                            'priority_score': analyzed_comment.get('priority_score', 0),
                            'requires_response': analyzed_comment.get('requires_response', False),
                            'updated_at': datetime.utcnow().isoformat()
                        }

                        result = db.supabase.table('video_comments')\
                            .update(update_data)\
                            .eq('comment_id', comment_id)\
                            .execute()

                        if result.data:
                            stats['salvos'] += 1
                        else:
                            stats['erros'] += 1

                    except Exception as e:
                        stats['erros'] += 1

                # Atualizar tokens usados
                tokens_input = analyzer.daily_metrics['total_tokens_input']
                tokens_output = analyzer.daily_metrics['total_tokens_output']
                stats['tokens_usados'] = tokens_input + tokens_output

                percentual = (stats['tokens_usados'] / 1_000_000) * 100

                print(f"  >>> {len(analyzed)} analisados | {stats['salvos']} salvos")
                print(f"  >>> Tokens: {stats['tokens_usados']:,} ({percentual:.1f}%)")

                # Parar se chegar perto do limite
                if percentual >= 90:
                    print(f"\n  !!! LIMITE DIARIO PROXIMO ({percentual:.1f}%)")
                    print(f"  !!! Parando analise preventivamente")
                    break

            else:
                print(f"  !!! GPT nao retornou analises para este batch")
                stats['erros'] += len(batch_comments)

        except Exception as e:
            print(f"  !!! ERRO no batch: {e}")
            stats['erros'] += len(batch_comments)

    # 4. Relatório final
    tempo_total = time.time() - start_time

    print("\n" + "="*80)
    print("RELATORIO FINAL DA ANALISE")
    print("="*80)

    print(f"\nComentarios:")
    print(f"  Pendentes: {stats['total_pendentes']:,}")
    print(f"  Analisados: {stats['analisados']:,}")
    print(f"  Salvos: {stats['salvos']:,}")
    print(f"  Erros: {stats['erros']:,}")

    print(f"\nTokens GPT:")
    print(f"  Usados: {stats['tokens_usados']:,}")
    print(f"  Percentual: {(stats['tokens_usados'] / 1_000_000) * 100:.1f}%")
    print(f"  Restantes: {1_000_000 - stats['tokens_usados']:,}")

    print(f"\nTempo: {tempo_total/60:.1f} minutos")
    print(f"Batches processados: {stats['batches_processados']}/{total_batches}")

    # Verificar quantos ainda estão pendentes
    ainda_pendentes = db.supabase.table('video_comments')\
        .select('*', count='exact')\
        .is_('analyzed_at', 'null')\
        .limit(0)\
        .execute()

    total_ainda_pendentes = ainda_pendentes.count if hasattr(ainda_pendentes, 'count') else 0

    print(f"\nAinda pendentes: {total_ainda_pendentes:,}")

    print("\n" + "="*80)

    if total_ainda_pendentes == 0:
        print("SUCESSO! Todos os comentarios foram analisados!")
    elif total_ainda_pendentes < stats['total_pendentes']:
        processados = stats['total_pendentes'] - total_ainda_pendentes
        print(f"PARCIAL: {processados:,} de {stats['total_pendentes']:,} analisados")
        print(f"Restam {total_ainda_pendentes:,} para proxima execucao")
    else:
        print("FALHA: Nenhum comentario foi analisado")

    print("="*80)

    return stats

if __name__ == "__main__":
    print("\n>>> ETAPA 2: ANALISE COM GPT <<<")
    print(">>> Analisar TODOS os comentarios pendentes")
    print("\nDeseja continuar? (digite 'SIM' para confirmar): ")

    confirmacao = input().strip().upper()

    if confirmacao == 'SIM':
        result = asyncio.run(analisar_todos())
        print(f"\nETAPA 2 FINALIZADA!")
        print(f"Comentarios analisados: {result['analisados']:,}")
        print(f"Tokens usados: {result['tokens_usados']:,}")
    else:
        print("\nAnalise cancelada")