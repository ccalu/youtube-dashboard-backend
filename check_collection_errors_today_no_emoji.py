"""
Script para diagnosticar erros na coleta de canais do YouTube
Identifica quais canais falharam na coleta de hoje
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()


async def check_collection_errors():
    """Verifica erros de coleta de hoje"""
    print("=" * 80)
    print("DIAGNÓSTICO DE ERROS - COLETA YOUTUBE")
    print("=" * 80)

    db = SupabaseClient()
    today = datetime.now().date()

    # 1. Buscar coletas de hoje com erros
    print(f"\n[1] Buscando coletas de hoje ({today.isoformat()})...\n")

    response = db.supabase.table("coletas_historico")\
        .select("*")\
        .gte("data_inicio", today.isoformat())\
        .order("data_inicio", desc=True)\
        .execute()

    coletas_hoje = response.data or []

    if not coletas_hoje:
        print("[ERRO] Nenhuma coleta encontrada hoje")
        return

    print(f"[OK] Encontradas {len(coletas_hoje)} coletas hoje:\n")

    # Mostrar resumo de todas as coletas
    for i, coleta in enumerate(coletas_hoje, 1):
        timestamp = coleta.get('data_inicio', 'N/A')
        sucesso = coleta.get('canais_sucesso', 0)
        erro = coleta.get('canais_erro', 0)
        status = coleta.get('status', 'N/A')
        msg_erro = coleta.get('mensagem_erro', '')

        print(f"  [{i}] {timestamp}")
        print(f"      Status: {status}")
        print(f"      Sucesso: {sucesso} | Erro: {erro}")
        if msg_erro:
            print(f"      Mensagem: {msg_erro}")
        print()

    # 2. Encontrar coleta com 14 erros
    print("\n" + "=" * 80)
    print("[2] Procurando coleta com 14 erros...\n")

    coleta_14_erros = None
    for coleta in coletas_hoje:
        if coleta.get('canais_erro', 0) == 14:
            coleta_14_erros = coleta
            break

    if not coleta_14_erros:
        print("[!]  Nenhuma coleta com exatamente 14 erros encontrada")
        # Mostrar a com mais erros
        coleta_mais_erros = max(coletas_hoje, key=lambda x: x.get('canais_erro', 0))
        erros = coleta_mais_erros.get('canais_erro', 0)
        if erros > 0:
            print(f"\n[!]  Coleta com mais erros: {erros} erros")
            coleta_14_erros = coleta_mais_erros
        else:
            return

    print("[OK] Coleta com erros encontrada:")
    print(f"   ID: {coleta_14_erros.get('id')}")
    print(f"   Timestamp: {coleta_14_erros.get('data_inicio')}")
    print(f"   Canais com sucesso: {coleta_14_erros.get('canais_sucesso', 0)}")
    print(f"   Canais com erro: {coleta_14_erros.get('canais_erro', 0)}")
    print(f"   Status: {coleta_14_erros.get('status')}")
    print(f"   Mensagem de erro: {coleta_14_erros.get('mensagem_erro', 'N/A')}")

    # 3. Tentar identificar os canais com erro
    print("\n" + "=" * 80)
    print("[3] Tentando identificar canais específicos...\n")

    # Estratégia: Buscar canais que NÃO foram atualizados hoje
    print("Estratégia: Identificar canais que NÃO foram coletados hoje\n")

    # Buscar todos os canais monitorados ativos
    canais_response = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, status")\
        .eq("status", "ativo")\
        .execute()

    todos_canais = canais_response.data or []
    print(f"Total de canais ativos: {len(todos_canais)}\n")

    # Buscar canais que FORAM atualizados hoje
    videos_hoje = db.supabase.table("videos_historico")\
        .select("canal_id")\
        .gte("data_coleta", today.isoformat())\
        .execute()

    canais_coletados_hoje = set()
    for video in (videos_hoje.data or []):
        canal_id = video.get('canal_id')
        if canal_id:
            canais_coletados_hoje.add(canal_id)

    print(f"Canais que FORAM coletados hoje: {len(canais_coletados_hoje)}\n")

    # Identificar canais que NÃO foram coletados
    canais_nao_coletados = []
    for canal in todos_canais:
        canal_id = canal.get('id')  # Usar 'id' da tabela canais_monitorados
        if canal_id not in canais_coletados_hoje:
            canais_nao_coletados.append(canal)

    print(f"Canais que NÃO foram coletados hoje: {len(canais_nao_coletados)}\n")

    if canais_nao_coletados:
        print("=" * 80)
        print("CANAIS COM POSSÍVEL ERRO DE COLETA:")
        print("=" * 80)
        print()

        for i, canal in enumerate(canais_nao_coletados, 1):
            nome = canal.get('nome_canal', 'N/A')
            canal_id = canal.get('id', 'N/A')

            print(f"[{i}] {nome}")
            print(f"    ID: {canal_id}")
            print()

    # 4. Análise de padrões de erro
    print("\n" + "=" * 80)
    print("[4] ANÁLISE DE POSSÍVEIS CAUSAS:")
    print("=" * 80)
    print()

    msg_erro = coleta_14_erros.get('mensagem_erro', '').lower()

    # Analisar mensagem de erro
    if 'quota' in msg_erro or 'limit' in msg_erro:
        print("[!]  PROVÁVEL CAUSA: Quota da API excedida")
        print("    Solução: Aguardar reset de quota ou adicionar mais API keys")
    elif 'permission' in msg_erro or 'forbidden' in msg_erro:
        print("[!]  PROVÁVEL CAUSA: Erro de permissão/OAuth")
        print("    Solução: Renovar credenciais OAuth")
    elif 'not found' in msg_erro or '404' in msg_erro:
        print("[!]  PROVÁVEL CAUSA: Canal deletado ou suspenso")
        print("    Solução: Remover canais inativos do monitoramento")
    elif 'timeout' in msg_erro or 'network' in msg_erro:
        print("[!]  PROVÁVEL CAUSA: Erro de conexão/timeout")
        print("    Solução: Retentar coleta")
    else:
        print("[!]  CAUSA NÃO IDENTIFICADA")
        print(f"    Mensagem original: {coleta_14_erros.get('mensagem_erro', 'N/A')}")

    print()
    print("=" * 80)
    print("RESUMO:")
    print("=" * 80)
    print(f"- Total de canais ativos: {len(todos_canais)}")
    print(f"- Canais coletados com sucesso: {len(canais_coletados_hoje)}")
    print(f"- Canais não coletados (possíveis erros): {len(canais_nao_coletados)}")
    print(f"- Erros registrados na coleta: {coleta_14_erros.get('canais_erro', 0)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_collection_errors())
