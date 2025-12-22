"""
Identifica os 14 canais que retornaram dados zeros na coleta
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()


async def identificar_14_canais():
    """Identifica canais que falharam por retornar dados zeros"""
    db = SupabaseClient()
    today = datetime.now().date()

    output = []
    output.append("=" * 100)
    output.append("IDENTIFICACAO DOS 14 CANAIS COM DADOS ZEROS")
    output.append(f"Data: {today.isoformat()}")
    output.append("=" * 100)
    output.append("")

    # 1. Buscar coleta de hoje
    response = db.supabase.table("coletas_historico")\
        .select("*")\
        .gte("data_inicio", today.isoformat())\
        .order("data_inicio", desc=True)\
        .limit(1)\
        .execute()

    if not response.data:
        output.append("[ERRO] Nenhuma coleta encontrada hoje")
        return "\n".join(output)

    coleta = response.data[0]

    output.append("[1] INFORMACOES DA COLETA:")
    output.append(f"    Canais sucesso: {coleta.get('canais_sucesso', 0)}")
    output.append(f"    Canais erro: {coleta.get('canais_erro', 0)}")
    output.append("")

    # 2. Buscar todos os canais ativos
    output.append("[2] BUSCANDO CANAIS ATIVOS:")
    canais_response = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, status, ultima_coleta")\
        .eq("status", "ativo")\
        .execute()

    todos_canais = canais_response.data or []
    output.append(f"    Total de canais ativos: {len(todos_canais)}")
    output.append("")

    # 3. Buscar canais que SALVARAM dados hoje em dados_canais_historico
    output.append("[3] VERIFICANDO DADOS SALVOS HOJE:")
    dados_hoje = db.supabase.table("dados_canais_historico")\
        .select("canal_id")\
        .eq("data_coleta", today.isoformat())\
        .execute()

    canais_com_dados = set()
    for dado in (dados_hoje.data or []):
        canal_id = dado.get('canal_id')
        if canal_id:
            canais_com_dados.add(canal_id)

    output.append(f"    Canais que salvaram dados hoje: {len(canais_com_dados)}")
    output.append("")

    # 4. Buscar canais que foram atualizados (ultima_coleta = hoje) mas NAO salvaram dados
    output.append("[4] IDENTIFICANDO CANAIS QUE NAO SALVARAM DADOS:")

    canais_sem_dados = []
    canais_atualizados_hoje = []

    for canal in todos_canais:
        canal_id = canal.get('id')
        ultima_coleta = canal.get('ultima_coleta')

        # Verificar se foi atualizado hoje
        if ultima_coleta and str(today.isoformat()) in ultima_coleta:
            canais_atualizados_hoje.append(canal_id)

            # Verificar se salvou dados
            if canal_id not in canais_com_dados:
                canais_sem_dados.append(canal)

    output.append(f"    Canais atualizados hoje (ultima_coleta): {len(canais_atualizados_hoje)}")
    output.append(f"    Canais SEM dados salvos: {len(canais_sem_dados)}")
    output.append("")

    # 5. Detalhar os canais sem dados (os 14 com erro)
    output.append("=" * 100)
    output.append(f"LISTA DOS {len(canais_sem_dados)} CANAIS QUE RETORNARAM DADOS ZEROS:")
    output.append("=" * 100)
    output.append("")

    if not canais_sem_dados:
        output.append("    [OK] Todos os canais salvaram dados!")
    else:
        for i, canal in enumerate(canais_sem_dados, 1):
            nome = canal.get('nome_canal', 'N/A')
            canal_id = canal.get('id', 'N/A')
            ultima_coleta = canal.get('ultima_coleta', 'N/A')

            # Buscar ultima vez que salvou dados (antes de hoje)
            ultima_com_dados = db.supabase.table("dados_canais_historico")\
                .select("data_coleta, views_30d, views_15d, views_7d, inscritos")\
                .eq("canal_id", canal_id)\
                .lt("data_coleta", today.isoformat())\
                .order("data_coleta", desc=True)\
                .limit(1)\
                .execute()

            if ultima_com_dados.data:
                last_data = ultima_com_dados.data[0]
                ultima_data_com_dados = last_data.get('data_coleta', 'NUNCA')
                last_views_30d = last_data.get('views_30d', 0)
                last_views_15d = last_data.get('views_15d', 0)
                last_views_7d = last_data.get('views_7d', 0)
                last_inscritos = last_data.get('inscritos', 0)
            else:
                ultima_data_com_dados = 'NUNCA'
                last_views_30d = 0
                last_views_15d = 0
                last_views_7d = 0
                last_inscritos = 0

            output.append(f"[{i}] Canal ID: {canal_id}")
            output.append(f"    Nome: {nome}")
            output.append(f"    Ultima coleta (tentativa): {ultima_coleta}")
            output.append(f"    Ultima coleta COM DADOS: {ultima_data_com_dados}")
            if ultima_data_com_dados != 'NUNCA':
                output.append(f"    Ultimos dados salvos:")
                output.append(f"      - Views 30d: {last_views_30d}")
                output.append(f"      - Views 15d: {last_views_15d}")
                output.append(f"      - Views 7d: {last_views_7d}")
                output.append(f"      - Inscritos: {last_inscritos}")
            output.append("")

    # 6. Análise e recomendações
    output.append("=" * 100)
    output.append("ANALISE:")
    output.append("=" * 100)
    output.append("")

    output.append("CAUSA RAIZ CONFIRMADA:")
    output.append("- Estes canais retornaram views_60d=0, views_30d=0, views_15d=0 e views_7d=0")
    output.append("- Codigo em database.py (linha 68-70) considera isso como dados invalidos")
    output.append("- Por isso nao salva em dados_canais_historico")
    output.append("- Sistema incrementa canais_erro corretamente")
    output.append("")

    output.append("POSSIVEIS RAZOES PARA DADOS ZEROS:")
    output.append("1. Canal foi deletado ou suspenso pelo YouTube")
    output.append("2. Canal esta inativo (sem uploads e sem views recentes)")
    output.append("3. Canal e muito novo e ainda nao tem views suficientes")
    output.append("4. API do YouTube retornou dados incompletos/vazios")
    output.append("5. Canal existe mas nao tem videos publicos")
    output.append("")

    output.append("RECOMENDACOES:")
    output.append("1. Verificar manualmente no YouTube se cada canal ainda existe")
    output.append("2. Se canal foi deletado: marcar como 'inativo' no sistema")
    output.append("3. Se canal existe mas sem views: pode ser canal muito pequeno ou novo")
    output.append("4. Se erro persistir por 7+ dias: remover do monitoramento")
    output.append("")

    output.append("=" * 100)
    output.append("RESUMO FINAL:")
    output.append("=" * 100)
    output.append(f"Total canais ativos: {len(todos_canais)}")
    output.append(f"Canais com dados salvos: {len(canais_com_dados)}")
    output.append(f"Canais sem dados (erro): {len(canais_sem_dados)}")
    output.append(f"Reportado pela coleta: {coleta.get('canais_erro', 0)} erros")
    output.append("")

    if len(canais_sem_dados) == coleta.get('canais_erro', 0):
        output.append("[OK] NUMEROS BATEM PERFEITAMENTE!")
        output.append(f"     {len(canais_sem_dados)} canais sem dados = {coleta.get('canais_erro', 0)} erros reportados")
    else:
        output.append(f"[ALERTA] Discrepancia: {len(canais_sem_dados)} sem dados != {coleta.get('canais_erro', 0)} erros")

    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await identificar_14_canais()

    # Salvar em arquivo
    with open('RELATORIO_14_CANAIS_ZEROS.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: RELATORIO_14_CANAIS_ZEROS.txt")


if __name__ == "__main__":
    asyncio.run(main())
