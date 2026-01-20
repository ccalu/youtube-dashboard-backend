"""
Script para testar coleta manual em canais "sem comentários"
Descobre onde está o bug e por que aparecem sem comentários
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

async def testar_canais_problematicos():
    """Testa coleta manual em canais que aparecem sem comentários"""

    from database import SupabaseClient
    from collector import YouTubeCollector
    import json

    print("\n" + "="*60)
    print("TESTE DE CANAIS PROBLEMÁTICOS")
    print("="*60)

    try:
        db = SupabaseClient()
        collector = YouTubeCollector()

        # Buscar canais tipo="nosso"
        canais_nosso = db.supabase.table('canais_monitorados')\
            .select('*')\
            .eq('tipo', 'nosso')\
            .eq('status', 'ativo')\
            .execute()

        # Buscar canais com comentários
        canais_com_comentarios_query = db.supabase.table('video_comments')\
            .select('canal_id')\
            .execute()

        canais_com_comentarios = set()
        for c in canais_com_comentarios_query.data or []:
            if c.get('canal_id'):
                canais_com_comentarios.add(c['canal_id'])

        # Identificar canais sem comentários
        canais_sem_comentarios = []
        for canal in canais_nosso.data or []:
            if canal['id'] not in canais_com_comentarios:
                canais_sem_comentarios.append(canal)

        print(f"\n[INFO] Total de canais tipo='nosso': {len(canais_nosso.data)}")
        print(f"[INFO] Canais COM comentários: {len(canais_com_comentarios)}")
        print(f"[INFO] Canais SEM comentários: {len(canais_sem_comentarios)}")

        if not canais_sem_comentarios:
            print("[OK] Todos os canais têm comentários!")
            return

        # Testar 5 canais diferentes (variados subnichos)
        canais_teste = []
        subnichos_testados = set()

        for canal in canais_sem_comentarios:
            subnicho = canal.get('subnicho', 'N/A')
            if subnicho not in subnichos_testados:
                canais_teste.append(canal)
                subnichos_testados.add(subnicho)
                if len(canais_teste) >= 5:
                    break

        # Se não conseguir 5 subnichos diferentes, pegar os primeiros
        if len(canais_teste) < 5:
            for canal in canais_sem_comentarios:
                if canal not in canais_teste:
                    canais_teste.append(canal)
                    if len(canais_teste) >= 5:
                        break

        print(f"\n[TESTE] Testando {len(canais_teste)} canais de subnichos variados...")
        print("-" * 50)

        resultados = []

        for idx, canal in enumerate(canais_teste, 1):
            print(f"\n[CANAL {idx}/{len(canais_teste)}] {canal['nome_canal']}")
            print(f"  ID: {canal['id']}")
            print(f"  URL: {canal['url_canal']}")
            print(f"  Subnicho: {canal.get('subnicho', 'N/A')}")

            resultado = {
                'canal_id': canal['id'],
                'nome': canal['nome_canal'],
                'url': canal['url_canal'],
                'subnicho': canal.get('subnicho', 'N/A'),
                'erros': [],
                'comentarios_encontrados': 0,
                'videos_testados': 0
            }

            # 1. Verificar se tem dados históricos no banco (indicador de vídeos)
            dados_banco = db.supabase.table('dados_canais_historico')\
                .select('*')\
                .eq('canal_id', canal['id'])\
                .order('data_coleta', desc=True)\
                .limit(1)\
                .execute()

            if not dados_banco.data:
                print(f"  [AVISO] Nenhum dado histórico no banco")
                # Não é erro crítico, pode continuar
            else:
                videos_coletados = dados_banco.data[0].get('videos_coletados', 0)
                print(f"  [OK] Canal tem {videos_coletados} vídeos coletados (histórico)")

            # 2. Tentar obter channel_id
            channel_id = await collector.get_channel_id(canal['url_canal'], canal['nome_canal'])

            if not channel_id:
                print(f"  [ERRO] Não foi possível obter channel_id da URL")
                resultado['erros'].append('Channel ID não encontrado')
                resultados.append(resultado)
                continue

            print(f"  [OK] Channel ID: {channel_id}")

            # 3. Buscar vídeos recentes via API
            try:
                videos_api = await collector.get_channel_videos(channel_id, canal['nome_canal'], days=30)

                if not videos_api:
                    print(f"  [AVISO] Nenhum vídeo retornado pela API (últimos 30 dias)")
                    resultado['erros'].append('API não retornou vídeos')
                else:
                    print(f"  [OK] {len(videos_api)} vídeos encontrados via API")

                    # 4. Testar coleta de comentários nos 3 primeiros vídeos
                    videos_para_testar = videos_api[:3] if videos_api else []

                    for video in videos_para_testar:
                        resultado['videos_testados'] += 1
                        video_id = video['video_id']
                        titulo = video['titulo'][:50]

                        print(f"\n    [VIDEO] {titulo}...")
                        print(f"            ID: {video_id}")
                        print(f"            Views: {video.get('views_atuais', 0):,}")

                        # Tentar coletar comentários
                        try:
                            comments = await collector.get_video_comments(
                                video_id,
                                video['titulo'],
                                max_results=10  # Só 10 para teste
                            )

                            if comments and len(comments) > 0:
                                print(f"            ✅ {len(comments)} comentários encontrados!")
                                resultado['comentarios_encontrados'] += len(comments)

                                # Verificar se estão salvos no banco
                                comments_banco = db.supabase.table('video_comments')\
                                    .select('id')\
                                    .eq('video_id', video_id)\
                                    .execute()

                                if comments_banco.data:
                                    print(f"            💾 {len(comments_banco.data)} salvos no banco")
                                else:
                                    print(f"            ❌ NENHUM salvo no banco!")
                                    resultado['erros'].append(f'Comentários não salvos para vídeo {video_id}')
                            else:
                                print(f"            ⚠️ Sem comentários (desabilitados ou sem engajamento)")

                        except Exception as e:
                            print(f"            ❌ Erro ao coletar: {str(e)[:100]}")
                            resultado['erros'].append(f'Erro coleta: {str(e)[:50]}')

            except Exception as e:
                print(f"  [ERRO] Falha ao buscar vídeos: {str(e)[:100]}")
                resultado['erros'].append(f'Erro API: {str(e)[:50]}')

            resultados.append(resultado)

        # Relatório final
        print("\n" + "="*60)
        print("RELATÓRIO DE TESTE")
        print("="*60)

        canais_com_comentarios_nao_salvos = 0
        total_comentarios_encontrados = 0

        for r in resultados:
            print(f"\n{r['nome']} (ID: {r['canal_id']})")
            print(f"  Subnicho: {r['subnicho']}")
            print(f"  Vídeos testados: {r['videos_testados']}")
            print(f"  Comentários encontrados: {r['comentarios_encontrados']}")

            if r['comentarios_encontrados'] > 0:
                total_comentarios_encontrados += r['comentarios_encontrados']
                if 'Comentários não salvos' in str(r['erros']):
                    canais_com_comentarios_nao_salvos += 1
                    print(f"  ⚠️ COMENTÁRIOS EXISTEM MAS NÃO FORAM SALVOS!")

            if r['erros']:
                print(f"  Erros: {', '.join(r['erros'])}")

        print("\n" + "="*60)
        print("DESCOBERTAS CRÍTICAS")
        print("="*60)

        if canais_com_comentarios_nao_salvos > 0:
            print(f"🚨 {canais_com_comentarios_nao_salvos} canais TÊM comentários mas NÃO estão salvos!")
            print(f"🚨 Total de comentários perdidos: {total_comentarios_encontrados}")
            print("\n[CAUSA PROVÁVEL]")
            print("1. Comentários foram coletados mas GPT falhou")
            print("2. Sistema descartou por não ter análise GPT")
            print("3. Correção já aplicada mas não retroativa")
        else:
            print("✅ Todos os canais testados que têm comentários estão salvando corretamente")

        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"teste_canais_problematicos_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] Relatório salvo em: {filename}")

    except Exception as e:
        print(f"\n[ERRO] Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(testar_canais_problematicos())