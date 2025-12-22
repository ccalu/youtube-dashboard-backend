"""
Diagnóstico completo de erros de coleta
Gera relatório detalhado em arquivo
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()


async def diagnostico_completo():
    """Gera diagnóstico completo em arquivo"""
    db = SupabaseClient()
    today = datetime.now().date()

    # Abrir arquivo de saída
    output = []
    output.append("=" * 100)
    output.append("DIAGNOSTICO COMPLETO - ERROS DE COLETA YOUTUBE")
    output.append(f"Data: {today.isoformat()}")
    output.append("=" * 100)
    output.append("")

    # 1. Buscar coleta de hoje
    response = db.supabase.table("coletas_historico")\
        .select("*")\
        .gte("data_inicio", today.isoformat())\
        .order("data_inicio", desc=True)\
        .execute()

    coletas_hoje = response.data or []

    if not coletas_hoje:
        output.append("[ERRO] Nenhuma coleta encontrada hoje")
        return "\n".join(output)

    # Encontrar coleta com erros
    coleta_com_erros = None
    for coleta in coletas_hoje:
        if coleta.get('canais_erro', 0) > 0:
            coleta_com_erros = coleta
            break

    if not coleta_com_erros:
        output.append("[OK] Nenhuma coleta com erros hoje")
        return "\n".join(output)

    # Informações da coleta
    output.append(f"[1] COLETA COM ERROS IDENTIFICADA:")
    output.append(f"    ID: {coleta_com_erros.get('id')}")
    output.append(f"    Horario: {coleta_com_erros.get('data_inicio')}")
    output.append(f"    Status: {coleta_com_erros.get('status')}")
    output.append(f"    Canais sucesso: {coleta_com_erros.get('canais_sucesso', 0)}")
    output.append(f"    Canais erro: {coleta_com_erros.get('canais_erro', 0)}")
    output.append(f"    Mensagem erro: {coleta_com_erros.get('mensagem_erro', 'N/A')}")
    output.append("")

    # 2. Buscar todos os canais ativos
    output.append("[2] ANALISANDO CANAIS...")
    output.append("")

    canais_response = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, status, ultima_coleta")\
        .eq("status", "ativo")\
        .execute()

    todos_canais = canais_response.data or []
    output.append(f"Total de canais ativos: {len(todos_canais)}")
    output.append("")

    # 3. Buscar canais coletados hoje
    videos_hoje = db.supabase.table("videos_historico")\
        .select("canal_id")\
        .gte("data_coleta", today.isoformat())\
        .execute()

    canais_coletados_hoje = set()
    for video in (videos_hoje.data or []):
        canal_id = video.get('canal_id')
        if canal_id:
            canais_coletados_hoje.add(canal_id)

    output.append(f"Canais coletados hoje: {len(canais_coletados_hoje)}")
    output.append("")

    # 4. Identificar canais não coletados
    canais_nao_coletados = []
    for canal in todos_canais:
        canal_id = canal.get('id')
        if canal_id not in canais_coletados_hoje:
            canais_nao_coletados.append(canal)

    output.append(f"Canais NAO coletados hoje: {len(canais_nao_coletados)}")
    output.append("")

    # 5. Detalhar cada canal não coletado
    output.append("=" * 100)
    output.append("LISTA DE CANAIS NAO COLETADOS (POSSIVEIS ERROS):")
    output.append("=" * 100)
    output.append("")

    for i, canal in enumerate(canais_nao_coletados, 1):
        nome = canal.get('nome_canal', 'N/A')
        canal_id = canal.get('id', 'N/A')
        ultima_coleta = canal.get('ultima_coleta', 'NUNCA')

        # Verificar se já teve coleta antes
        teve_coleta_antes = "SIM" if ultima_coleta and ultima_coleta != 'NUNCA' else "NAO"

        # Calcular dias desde última coleta
        dias_sem_coleta = "N/A"
        if ultima_coleta and ultima_coleta != 'NUNCA':
            try:
                ultima_data = datetime.fromisoformat(ultima_coleta.replace('Z', '+00:00')).date()
                dias = (today - ultima_data).days
                dias_sem_coleta = f"{dias} dias"
            except:
                dias_sem_coleta = "ERRO AO CALCULAR"

        output.append(f"[{i}] Canal ID: {canal_id}")
        output.append(f"    Nome: {nome}")
        output.append(f"    Ja teve coleta antes: {teve_coleta_antes}")
        output.append(f"    Ultima coleta: {ultima_coleta}")
        output.append(f"    Tempo sem coleta: {dias_sem_coleta}")
        output.append("")

    # 6. Análise de padrões
    output.append("=" * 100)
    output.append("ANALISE DE PADROES:")
    output.append("=" * 100)
    output.append("")

    # Contar quantos nunca tiveram coleta
    nunca_coletados = sum(1 for c in canais_nao_coletados if not c.get('ultima_coleta'))
    ja_coletados_antes = len(canais_nao_coletados) - nunca_coletados

    output.append(f"Canais que NUNCA foram coletados: {nunca_coletados}")
    output.append(f"Canais que JA foram coletados antes: {ja_coletados_antes}")
    output.append("")

    # Análise da mensagem de erro
    msg_erro = coleta_com_erros.get('mensagem_erro', '').lower() if coleta_com_erros.get('mensagem_erro') else ''

    output.append("POSSIVEIS CAUSAS:")
    output.append("")

    if not msg_erro:
        output.append("- Mensagem de erro nao disponivel")
        output.append("- Provaveis causas gericas:")
        output.append("  * Quota da API excedida")
        output.append("  * Erro de permissao/OAuth")
        output.append("  * Canal deletado ou suspenso")
        output.append("  * Timeout de conexao")
    elif 'quota' in msg_erro or 'limit' in msg_erro:
        output.append("- CAUSA IDENTIFICADA: Quota da API excedida")
        output.append("- Solucao: Aguardar reset de quota ou adicionar mais API keys")
    elif 'permission' in msg_erro or 'forbidden' in msg_erro:
        output.append("- CAUSA IDENTIFICADA: Erro de permissao/OAuth")
        output.append("- Solucao: Renovar credenciais OAuth")
    elif 'not found' in msg_erro or '404' in msg_erro:
        output.append("- CAUSA IDENTIFICADA: Canal deletado ou suspenso")
        output.append("- Solucao: Remover canais inativos do monitoramento")
    elif 'timeout' in msg_erro or 'network' in msg_erro:
        output.append("- CAUSA IDENTIFICADA: Erro de conexao/timeout")
        output.append("- Solucao: Retentar coleta")
    else:
        output.append(f"- Mensagem original: {coleta_com_erros.get('mensagem_erro', 'N/A')}")

    output.append("")
    output.append("=" * 100)
    output.append("RESUMO:")
    output.append("=" * 100)
    output.append(f"Total canais ativos: {len(todos_canais)}")
    output.append(f"Coletados com sucesso: {len(canais_coletados_hoje)}")
    output.append(f"Nao coletados (erros): {len(canais_nao_coletados)}")
    output.append(f"Nunca coletados: {nunca_coletados}")
    output.append(f"Ja coletados antes mas falharam hoje: {ja_coletados_antes}")
    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await diagnostico_completo()

    # Salvar em arquivo
    with open('RELATORIO_ERROS_COLETA.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console (ASCII apenas)
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio completo salvo em: RELATORIO_ERROS_COLETA.txt")


if __name__ == "__main__":
    asyncio.run(main())
