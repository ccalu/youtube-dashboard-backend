"""
Investiga OS OUTROS 12 CANAIS que falharam hoje
(14 erros - 2 deletados = 12 canais restantes)
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()

async def investigate_all_errors():
    """Investiga TODOS os 14 canais com erro"""
    db = SupabaseClient()
    today = datetime.now().date()

    output = []
    output.append("=" * 100)
    output.append("INVESTIGACAO COMPLETA - TODOS OS 14 CANAIS COM ERRO")
    output.append(f"Data: {today.isoformat()}")
    output.append("=" * 100)
    output.append("")

    # 1. Buscar TODOS os canais ativos
    todos_canais = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, url_canal, tipo, status")\
        .eq("status", "ativo")\
        .order("id", desc=False)\
        .execute()

    output.append(f"[1] TOTAL DE CANAIS ATIVOS: {len(todos_canais.data)}")
    output.append("")

    # 2. Buscar canais que SALVARAM dados hoje
    dados_hoje = db.supabase.table("dados_canais_historico")\
        .select("canal_id, views_30d, views_15d, views_7d, inscritos")\
        .eq("data_coleta", today.isoformat())\
        .execute()

    canais_com_dados = {}
    for dado in (dados_hoje.data or []):
        canal_id = dado.get('canal_id')
        if canal_id:
            canais_com_dados[canal_id] = {
                'views_30d': dado.get('views_30d', 0),
                'views_15d': dado.get('views_15d', 0),
                'views_7d': dado.get('views_7d', 0),
                'inscritos': dado.get('inscritos', 0)
            }

    output.append(f"[2] CANAIS QUE SALVARAM DADOS HOJE: {len(canais_com_dados)}")
    output.append("")

    # 3. Identificar canais SEM dados (os 14 com erro)
    canais_erro = []

    for canal in todos_canais.data:
        canal_id = canal.get('id')
        if canal_id not in canais_com_dados:
            canais_erro.append(canal)

    output.append(f"[3] CANAIS SEM DADOS (ERRO): {len(canais_erro)}")
    output.append("")

    # 4. Para cada canal com erro, buscar histórico
    output.append("=" * 100)
    output.append(f"DETALHAMENTO DOS {len(canais_erro)} CANAIS COM ERRO:")
    output.append("=" * 100)
    output.append("")

    # Classificar canais por tipo de problema
    nunca_coletou = []
    tinha_dados_parou = []
    deletados_conhecidos = [416, 711]  # Já sabemos que foram deletados

    for i, canal in enumerate(canais_erro, 1):
        canal_id = canal.get('id')
        nome = canal.get('nome_canal', 'N/A')
        url = canal.get('url_canal', 'N/A')
        tipo = canal.get('tipo', 'N/A')

        output.append(f"[{i}] Canal ID {canal_id} - {nome}")
        output.append(f"    URL: {url}")
        output.append(f"    Tipo: {tipo}")

        # Buscar histórico completo
        historico = db.supabase.table("dados_canais_historico")\
            .select("data_coleta, views_30d, views_15d, views_7d, inscritos")\
            .eq("canal_id", canal_id)\
            .order("data_coleta", desc=True)\
            .limit(5)\
            .execute()

        if not historico.data or len(historico.data) == 0:
            output.append(f"    Status: NUNCA COLETOU")
            output.append(f"    Problema: Canal novo ou URL sempre foi invalida")
            nunca_coletou.append({
                'id': canal_id,
                'nome': nome,
                'url': url
            })
        else:
            # Tem histórico - ver última coleta
            ultima = historico.data[0]
            ultima_data = ultima.get('data_coleta')
            views_30d = ultima.get('views_30d', 0)
            inscritos = ultima.get('inscritos', 0)

            dias_sem_coletar = (today - datetime.fromisoformat(ultima_data).date()).days

            output.append(f"    Status: TINHA DADOS mas PAROU")
            output.append(f"    Ultima coleta: {ultima_data} ({dias_sem_coletar} dias atras)")
            output.append(f"    Ultima views 30d: {views_30d:,}")
            output.append(f"    Ultimos inscritos: {inscritos:,}")

            # Verificar se é um dos deletados conhecidos
            if canal_id in deletados_conhecidos:
                output.append(f"    [CONFIRMADO] Canal DELETADO/SUSPENSO pelo YouTube")
            else:
                output.append(f"    [?] Motivo desconhecido - precisa investigar")

                tinha_dados_parou.append({
                    'id': canal_id,
                    'nome': nome,
                    'url': url,
                    'ultima_coleta': ultima_data,
                    'dias_sem_coletar': dias_sem_coletar,
                    'views_30d': views_30d,
                    'inscritos': inscritos
                })

        output.append("")

    # 5. Resumo por categoria
    output.append("=" * 100)
    output.append("RESUMO POR CATEGORIA DE PROBLEMA:")
    output.append("=" * 100)
    output.append("")

    output.append(f"[A] CANAIS DELETADOS/SUSPENSOS: {len(deletados_conhecidos)}")
    output.append(f"    - Abandoned History (ID 416)")
    output.append(f"    - The Sharpline (ID 711)")
    output.append("")

    output.append(f"[B] CANAIS QUE NUNCA COLETARAM: {len(nunca_coletou)}")
    if nunca_coletou:
        for canal in nunca_coletou:
            output.append(f"    - {canal['nome']} (ID {canal['id']})")
    output.append("")

    output.append(f"[C] CANAIS COM HISTORICO QUE PARARAM: {len(tinha_dados_parou)}")
    if tinha_dados_parou:
        for canal in tinha_dados_parou:
            output.append(f"    - {canal['nome']} (ID {canal['id']})")
            output.append(f"      Ultima coleta: {canal['ultima_coleta']} ({canal['dias_sem_coletar']} dias)")
            output.append(f"      Views: {canal['views_30d']:,} | Inscritos: {canal['inscritos']:,}")
    output.append("")

    # 6. Análise e recomendações
    output.append("=" * 100)
    output.append("ANALISE E RECOMENDACOES:")
    output.append("=" * 100)
    output.append("")

    output.append("CATEGORIA [A] - CANAIS DELETADOS (2):")
    output.append("  Acao: Ja foram removidos ou atualizados")
    output.append("  Status: RESOLVIDO")
    output.append("")

    output.append(f"CATEGORIA [B] - NUNCA COLETARAM ({len(nunca_coletou)}):")
    output.append("  Causa provavel:")
    output.append("    - URLs incorretas desde o inicio")
    output.append("    - Canais nao existem")
    output.append("    - Problemas de permissao")
    output.append("  Acao necessaria:")
    output.append("    1. Validar URLs manualmente no YouTube")
    output.append("    2. Corrigir URLs ou marcar como inativo")
    output.append("")

    output.append(f"CATEGORIA [C] - TINHAM DADOS MAS PARARAM ({len(tinha_dados_parou)}):")
    output.append("  Causa provavel:")
    output.append("    - Throttling temporario da API (mais provavel)")
    output.append("    - Canal mudou de URL")
    output.append("    - Canal ficou privado temporariamente")
    output.append("    - Erro de rede durante coleta")
    output.append("  Acao necessaria:")
    output.append("    1. Validar se canais ainda existem")
    output.append("    2. Tentar nova coleta manualmente")
    output.append("    3. Se erro persistir, investigar individualmente")
    output.append("")

    total_verificado = len(deletados_conhecidos) + len(nunca_coletou) + len(tinha_dados_parou)
    output.append(f"TOTAL VERIFICADO: {total_verificado}/{len(canais_erro)}")

    if total_verificado != len(canais_erro):
        output.append(f"[ALERTA] Faltam {len(canais_erro) - total_verificado} canais na classificacao!")

    output.append("")
    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await investigate_all_errors()

    # Salvar em arquivo
    with open('RELATORIO_12_CANAIS_RESTANTES.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: RELATORIO_12_CANAIS_RESTANTES.txt")


if __name__ == "__main__":
    asyncio.run(main())
