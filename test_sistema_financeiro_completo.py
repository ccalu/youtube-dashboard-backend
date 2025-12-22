"""
Teste Completo - Sistema Financeiro
Testa TODAS as funcionalidades e logicas
"""

import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import SupabaseClient
from financeiro import FinanceiroService, get_usd_brl_rate

load_dotenv()


async def test_completo():
    """Testa todas as funcionalidades do sistema financeiro"""

    db = SupabaseClient()
    financeiro = FinanceiroService(db)

    print("\n" + "=" * 80)
    print("TESTE COMPLETO - SISTEMA FINANCEIRO")
    print("=" * 80)

    erros = []
    sucessos = []

    # ========== TESTE 1: TAXA DE CAMBIO ==========
    print("\n[TESTE 1] Taxa de Cambio USD-BRL")
    print("-" * 80)
    try:
        taxa = await get_usd_brl_rate()
        assert 'taxa' in taxa, "Taxa deve ter campo 'taxa'"
        assert 'atualizado_em' in taxa, "Taxa deve ter campo 'atualizado_em'"
        assert taxa['taxa'] > 0, "Taxa deve ser maior que 0"
        assert taxa['taxa'] < 10, "Taxa deve ser realista (< 10)"
        print(f"OK - Taxa: R$ {taxa['taxa']:.2f} ({taxa['atualizado_em']})")
        sucessos.append("Taxa de cambio")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Taxa de cambio: {e}")

    # ========== TESTE 2: CATEGORIAS ==========
    print("\n[TESTE 2] Categorias")
    print("-" * 80)
    try:
        # Listar categorias
        categorias = await financeiro.listar_categorias()
        assert len(categorias) >= 8, "Deve ter pelo menos 8 categorias"

        # Verificar categoria YouTube AdSense
        youtube_cat = [c for c in categorias if c['nome'] == 'YouTube AdSense']
        assert len(youtube_cat) == 1, "Deve ter exatamente 1 categoria YouTube"
        assert youtube_cat[0]['tipo'] == 'receita', "YouTube deve ser receita"

        # Contar receitas e despesas
        receitas = [c for c in categorias if c['tipo'] == 'receita']
        despesas = [c for c in categorias if c['tipo'] == 'despesa']

        print(f"OK - Total: {len(categorias)} categorias")
        print(f"     Receitas: {len(receitas)}")
        print(f"     Despesas: {len(despesas)}")
        sucessos.append("Categorias")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Categorias: {e}")

    # ========== TESTE 3: TAXAS ==========
    print("\n[TESTE 3] Taxas")
    print("-" * 80)
    try:
        taxas = await financeiro.listar_taxas()
        assert len(taxas) >= 1, "Deve ter pelo menos 1 taxa"

        imposto = [t for t in taxas if t['nome'] == 'Imposto']
        assert len(imposto) == 1, "Deve ter taxa Imposto"
        assert imposto[0]['percentual'] == 3.0, "Imposto deve ser 3%"
        assert imposto[0]['aplica_sobre'] == 'receita_bruta', "Imposto sobre receita_bruta"

        print(f"OK - Total: {len(taxas)} taxas")
        print(f"     Imposto: {imposto[0]['percentual']}%")
        sucessos.append("Taxas")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Taxas: {e}")

    # ========== TESTE 4: LANCAMENTOS YOUTUBE ==========
    print("\n[TESTE 4] Lancamentos YouTube")
    print("-" * 80)
    try:
        lancamentos = await financeiro.listar_lancamentos("90d")

        # Filtrar apenas YouTube
        youtube_lancamentos = [l for l in lancamentos if 'YouTube' in l.get('descricao', '')]

        assert len(youtube_lancamentos) >= 3, "Deve ter pelo menos 3 meses (Out, Nov, Dez)"

        total = sum(float(l['valor']) for l in youtube_lancamentos)

        print(f"OK - Total lancamentos YouTube: {len(youtube_lancamentos)}")
        print(f"     Valor total: R$ {total:.2f}")

        for l in sorted(youtube_lancamentos, key=lambda x: x['data']):
            print(f"     {l['data']}: R$ {l['valor']:.2f}")

        sucessos.append("Lancamentos YouTube")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Lancamentos YouTube: {e}")

    # ========== TESTE 5: RECEITA YOUTUBE (USD->BRL) ==========
    print("\n[TESTE 5] Receita YouTube (conversao USD->BRL)")
    print("-" * 80)
    try:
        # Buscar revenue em USD direto do Supabase
        response = db.supabase.table('yt_daily_metrics')\
            .select('revenue')\
            .eq('is_estimate', False)\
            .gte('date', '2024-10-26')\
            .execute()

        total_usd = sum(float(item['revenue'] or 0) for item in response.data)

        # Buscar taxa
        taxa_info = await get_usd_brl_rate()
        taxa = taxa_info['taxa']

        # Calcular BRL esperado
        total_brl_esperado = total_usd * taxa

        # Buscar via API
        total_brl_api = await financeiro.get_youtube_revenue("90d")

        # Validar conversao
        diferenca = abs(total_brl_esperado - total_brl_api)
        assert diferenca < 1.0, f"Diferenca muito grande: R$ {diferenca:.2f}"

        print(f"OK - Total USD: $ {total_usd:.2f}")
        print(f"     Taxa: R$ {taxa:.2f}")
        print(f"     Total BRL esperado: R$ {total_brl_esperado:.2f}")
        print(f"     Total BRL API: R$ {total_brl_api:.2f}")
        print(f"     Diferenca: R$ {diferenca:.2f}")

        sucessos.append("Conversao USD->BRL")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Conversao USD->BRL: {e}")

    # ========== TESTE 6: OVERVIEW PERIODOS ==========
    print("\n[TESTE 6] Overview - Diferentes Periodos")
    print("-" * 80)
    try:
        periodos_teste = ['7d', '30d', '60d', '90d']

        for periodo in periodos_teste:
            overview = await financeiro.get_overview(periodo)

            # Validar estrutura
            assert 'receita_bruta' in overview
            assert 'despesas_totais' in overview
            assert 'taxas_totais' in overview
            assert 'lucro_liquido' in overview
            assert 'despesas_fixas' in overview
            assert 'despesas_unicas' in overview

            # Validar calculo lucro
            lucro_calc = overview['receita_bruta'] - overview['despesas_totais'] - overview['taxas_totais']
            assert abs(lucro_calc - overview['lucro_liquido']) < 0.1, f"Erro no calculo lucro ({periodo})"

            # Validar taxas (3% da receita)
            if overview['receita_bruta'] > 0:
                taxa_esperada = overview['receita_bruta'] * 0.03
                assert abs(taxa_esperada - overview['taxas_totais']) < 0.1, f"Erro no calculo taxas ({periodo})"

            print(f"  {periodo}:")
            print(f"    Receita: R$ {overview['receita_bruta']:.2f}")
            print(f"    Despesas: R$ {overview['despesas_totais']:.2f}")
            print(f"    Taxas (3%): R$ {overview['taxas_totais']:.2f}")
            print(f"    Lucro: R$ {overview['lucro_liquido']:.2f}")

        print("OK - Todos os periodos validados")
        sucessos.append("Overview periodos")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Overview periodos: {e}")

    # ========== TESTE 7: FILTRO LANCAMENTOS ==========
    print("\n[TESTE 7] Filtro de Lancamentos")
    print("-" * 80)
    try:
        # Todos
        todos = await financeiro.listar_lancamentos("90d")

        # Por tipo
        receitas = await financeiro.listar_lancamentos("90d", tipo="receita")
        despesas = await financeiro.listar_lancamentos("90d", tipo="despesa")

        assert len(todos) == len(receitas) + len(despesas), "Total deve ser soma de receitas + despesas"

        print(f"OK - Total: {len(todos)}")
        print(f"     Receitas: {len(receitas)}")
        print(f"     Despesas: {len(despesas)}")

        sucessos.append("Filtro lancamentos")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Filtro lancamentos: {e}")

    # ========== TESTE 8: CALCULOS FINANCEIROS ==========
    print("\n[TESTE 8] Calculos Financeiros")
    print("-" * 80)
    try:
        # Receita bruta
        receita = await financeiro.get_receita_bruta("90d")
        assert receita >= 0, "Receita nao pode ser negativa"

        # Despesas
        despesas = await financeiro.get_despesas_totais("90d")
        assert despesas >= 0, "Despesas nao podem ser negativas"

        # Despesas por tipo
        desp_tipo = await financeiro.get_despesas_por_tipo("90d")
        assert 'fixas' in desp_tipo
        assert 'unicas' in desp_tipo
        assert 'total' in desp_tipo
        assert abs((desp_tipo['fixas'] + desp_tipo['unicas']) - desp_tipo['total']) < 0.1

        # Taxas
        taxas = await financeiro.calcular_taxas_totais(receita)
        taxa_esperada = receita * 0.03
        assert abs(taxas - taxa_esperada) < 0.1, "Erro no calculo de taxas"

        # Lucro liquido
        lucro = await financeiro.get_lucro_liquido("90d")
        lucro_esperado = receita - despesas - taxas
        assert abs(lucro - lucro_esperado) < 0.1, "Erro no calculo lucro liquido"

        print(f"OK - Receita bruta: R$ {receita:.2f}")
        print(f"     Despesas totais: R$ {despesas:.2f}")
        print(f"     Despesas fixas: R$ {desp_tipo['fixas']:.2f}")
        print(f"     Despesas unicas: R$ {desp_tipo['unicas']:.2f}")
        print(f"     Taxas (3%): R$ {taxas:.2f}")
        print(f"     Lucro liquido: R$ {lucro:.2f}")

        sucessos.append("Calculos financeiros")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Calculos financeiros: {e}")

    # ========== TESTE 9: GRAFICOS ==========
    print("\n[TESTE 9] Dados para Graficos")
    print("-" * 80)
    try:
        # Grafico receita vs despesas
        grafico1 = await financeiro.get_grafico_receita_despesas("90d")
        assert isinstance(grafico1, list), "Deve retornar lista"

        # Grafico breakdown despesas
        grafico2 = await financeiro.get_grafico_despesas_breakdown("90d")
        assert 'por_categoria' in grafico2
        assert 'por_recorrencia' in grafico2
        assert 'total' in grafico2

        print(f"OK - Grafico receita/despesas: {len(grafico1)} pontos")
        print(f"     Grafico breakdown: {len(grafico2['por_categoria'])} categorias")

        sucessos.append("Graficos")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Graficos: {e}")

    # ========== TESTE 10: CONSISTENCIA DADOS ==========
    print("\n[TESTE 10] Consistencia de Dados")
    print("-" * 80)
    try:
        # Overview 90d
        overview = await financeiro.get_overview("90d")

        # Lancamentos 90d
        lancamentos = await financeiro.listar_lancamentos("90d")
        receitas_lanc = sum(float(l['valor']) for l in lancamentos if l['tipo'] == 'receita')
        despesas_lanc = sum(float(l['valor']) for l in lancamentos if l['tipo'] == 'despesa')

        # Revenue direto
        revenue_direto = await financeiro.get_youtube_revenue("90d")

        # Validacoes
        assert abs(overview['receita_bruta'] - receitas_lanc) < 0.1, "Receita overview != lancamentos"
        assert abs(overview['despesas_totais'] - despesas_lanc) < 0.1, "Despesas overview != lancamentos"
        assert abs(revenue_direto - receitas_lanc) < 1.0, "Revenue direto != lancamentos"

        print(f"OK - Overview receita: R$ {overview['receita_bruta']:.2f}")
        print(f"     Lancamentos receita: R$ {receitas_lanc:.2f}")
        print(f"     Revenue direto: R$ {revenue_direto:.2f}")
        print(f"     Diferenca max: R$ 0.10")

        sucessos.append("Consistencia dados")
    except Exception as e:
        print(f"ERRO: {e}")
        erros.append(f"Consistencia dados: {e}")

    # ========== RESULTADO FINAL ==========
    print("\n" + "=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)

    print(f"\nTestes executados: {len(sucessos) + len(erros)}")
    print(f"Sucessos: {len(sucessos)}")
    print(f"Erros: {len(erros)}")

    if erros:
        print("\n[ERROS ENCONTRADOS]")
        for erro in erros:
            print(f"  - {erro}")
    else:
        print("\n*** TODOS OS TESTES PASSARAM! ***")
        print("Sistema financeiro 100% funcional!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_completo())
