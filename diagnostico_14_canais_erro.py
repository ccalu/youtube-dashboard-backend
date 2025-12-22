"""
Diagnóstico CORRETO dos 14 canais que falharam na coleta
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient

load_dotenv()


async def diagnostico_correto():
    """Identifica os 14 canais que realmente falharam"""
    db = SupabaseClient()
    today = datetime.now().date()

    output = []
    output.append("=" * 100)
    output.append("DIAGNOSTICO CORRETO - 14 CANAIS COM ERRO DE COLETA")
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
    output.append(f"    ID: {coleta.get('id')}")
    output.append(f"    Horario inicio: {coleta.get('data_inicio')}")
    output.append(f"    Horario fim: {coleta.get('data_fim', 'N/A')}")
    output.append(f"    Status: {coleta.get('status')}")
    output.append(f"    Canais sucesso: {coleta.get('canais_sucesso', 0)}")
    output.append(f"    Canais erro: {coleta.get('canais_erro', 0)}")
    output.append(f"    Videos coletados: {coleta.get('videos_coletados', 0)}")
    output.append(f"    Requisicoes usadas: {coleta.get('requisicoes_usadas', 0)}")
    output.append(f"    Duracao: {coleta.get('duracao_segundos', 0)} segundos")
    output.append("")

    # 2. Verificar total de vídeos coletados hoje
    output.append("[2] VERIFICANDO VIDEOS COLETADOS HOJE:")
    videos_response = db.supabase.table("videos_historico")\
        .select("id", count="exact")\
        .gte("data_coleta", today.isoformat())\
        .execute()

    total_videos_hoje = videos_response.count
    output.append(f"    Total de videos com data_coleta = hoje: {total_videos_hoje}")
    output.append("")

    # 3. Buscar todos os canais ativos
    output.append("[3] ANALISANDO CANAIS ATIVOS:")
    canais_response = db.supabase.table("canais_monitorados")\
        .select("id, nome_canal, status, ultima_coleta")\
        .eq("status", "ativo")\
        .execute()

    todos_canais = canais_response.data or []
    output.append(f"    Total de canais ativos: {len(todos_canais)}")
    output.append("")

    # 4. Identificar canais que NÃO foram atualizados na coleta de hoje
    output.append("[4] IDENTIFICANDO CANAIS QUE NAO FORAM ATUALIZADOS:")

    # Horário da coleta
    coleta_inicio = datetime.fromisoformat(coleta.get('data_inicio').replace('Z', '+00:00'))
    coleta_inicio_str = coleta_inicio.date().isoformat()

    canais_nao_atualizados = []
    canais_atualizados = []

    for canal in todos_canais:
        ultima_coleta = canal.get('ultima_coleta')

        if not ultima_coleta:
            # Canal nunca foi coletado
            canais_nao_atualizados.append({
                **canal,
                'motivo': 'Nunca foi coletado',
                'dias_sem_coleta': 'Infinito'
            })
        else:
            try:
                # Corrigir formato de timestamp inválido (6 dígitos em vez de 7 nos microssegundos)
                ultima_coleta_str = ultima_coleta.replace('Z', '+00:00')

                # Se timestamp tem problema de formatação, extrair apenas a data
                if 'T' in ultima_coleta_str:
                    data_parte = ultima_coleta_str.split('T')[0]
                    ultima_coleta_date = datetime.fromisoformat(data_parte).date()
                else:
                    ultima_coleta_dt = datetime.fromisoformat(ultima_coleta_str)
                    ultima_coleta_date = ultima_coleta_dt.date()

                # Se ultima_coleta NÃO é de hoje, canal não foi atualizado
                if ultima_coleta_date < today:
                    dias_sem_coleta = (today - ultima_coleta_date).days
                    canais_nao_atualizados.append({
                        **canal,
                        'motivo': 'Nao foi atualizado na coleta de hoje',
                        'dias_sem_coleta': dias_sem_coleta
                    })
                else:
                    # Canal foi atualizado hoje
                    canais_atualizados.append(canal)
            except Exception as e:
                # Se der erro mesmo com workaround, tentar pela string
                if str(today.isoformat()) in ultima_coleta:
                    # Tem data de hoje na string, considerar como atualizado
                    canais_atualizados.append(canal)
                else:
                    canais_nao_atualizados.append({
                        **canal,
                        'motivo': f'Erro ao processar data: {e}',
                        'dias_sem_coleta': 'ERRO'
                    })

    output.append(f"    Canais atualizados na coleta de hoje: {len(canais_atualizados)}")
    output.append(f"    Canais NAO atualizados (possiveis erros): {len(canais_nao_atualizados)}")
    output.append("")

    # 5. Detalhar os canais não atualizados (os 14 com erro)
    output.append("=" * 100)
    output.append(f"LISTA DOS {len(canais_nao_atualizados)} CANAIS QUE FALHARAM NA COLETA:")
    output.append("=" * 100)
    output.append("")

    if not canais_nao_atualizados:
        output.append("    [OK] Todos os canais foram coletados com sucesso!")
    else:
        for i, canal in enumerate(canais_nao_atualizados, 1):
            nome = canal.get('nome_canal', 'N/A')
            canal_id = canal.get('id', 'N/A')
            ultima_coleta = canal.get('ultima_coleta', 'NUNCA')
            motivo = canal.get('motivo', 'Desconhecido')
            dias = canal.get('dias_sem_coleta', 'N/A')

            output.append(f"[{i}] Canal ID: {canal_id}")
            output.append(f"    Nome: {nome}")
            output.append(f"    Ultima coleta: {ultima_coleta}")
            output.append(f"    Dias sem coleta: {dias}")
            output.append(f"    Motivo: {motivo}")
            output.append("")

    # 6. Análise e recomendações
    output.append("=" * 100)
    output.append("ANALISE E RECOMENDACOES:")
    output.append("=" * 100)
    output.append("")

    if canais_nao_atualizados:
        nunca_coletados = sum(1 for c in canais_nao_atualizados if not c.get('ultima_coleta') or c.get('ultima_coleta') == 'NUNCA')
        ja_coletados = len(canais_nao_atualizados) - nunca_coletados

        output.append(f"Canais que NUNCA foram coletados: {nunca_coletados}")
        output.append(f"Canais que ja foram coletados mas falharam hoje: {ja_coletados}")
        output.append("")

        output.append("POSSIVEIS CAUSAS:")
        output.append("- Canal foi deletado ou suspenso pelo YouTube")
        output.append("- Erro de permissao/acesso ao canal")
        output.append("- Canal nao tem videos publicos")
        output.append("- Erro temporario de rede durante a coleta desse canal especifico")
        output.append("")

        output.append("RECOMENDACOES:")
        output.append("1. Verificar manualmente se os canais ainda existem no YouTube")
        output.append("2. Tentar coletar novamente manualmente via API")
        output.append("3. Se canal foi deletado, marcar como 'inativo' no sistema")
        output.append("4. Se erro persistir por 3+ dias, investigar causa especifica")
    else:
        output.append("[OK] Nenhum canal falhou na coleta!")

    output.append("")
    output.append("=" * 100)
    output.append("RESUMO FINAL:")
    output.append("=" * 100)
    output.append(f"Total canais ativos: {len(todos_canais)}")
    output.append(f"Coletados com sucesso: {len(canais_atualizados)}")
    output.append(f"Falharam: {len(canais_nao_atualizados)}")
    output.append(f"Videos coletados: {total_videos_hoje}")
    output.append(f"Reportado pela coleta: {coleta.get('canais_sucesso', 0)} sucesso + {coleta.get('canais_erro', 0)} erro")
    output.append("")

    # Verificar se os números batem
    if len(canais_nao_atualizados) == coleta.get('canais_erro', 0):
        output.append("[OK] Numeros batem: canais nao atualizados = canais_erro reportado")
    else:
        output.append(f"[ALERTA] Discrepancia: {len(canais_nao_atualizados)} canais nao atualizados != {coleta.get('canais_erro', 0)} erros reportados")

    output.append("=" * 100)

    return "\n".join(output)


async def main():
    resultado = await diagnostico_correto()

    # Salvar em arquivo
    with open('RELATORIO_14_CANAIS_ERRO.txt', 'w', encoding='utf-8') as f:
        f.write(resultado)

    # Exibir no console
    print(resultado.encode('ascii', 'replace').decode('ascii'))
    print("\n\n>>> Relatorio salvo em: RELATORIO_14_CANAIS_ERRO.txt")


if __name__ == "__main__":
    asyncio.run(main())
