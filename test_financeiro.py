"""
Script de Testes - Sistema Financeiro
Testa todos os endpoints e funcionalidades
"""

import asyncio
from database import SupabaseClient
from financeiro import FinanceiroService


async def test():
    """Testa sistema financeiro completo"""
    print("=" * 60)
    print("TESTES - SISTEMA FINANCEIRO")
    print("=" * 60)

    db = SupabaseClient()
    financeiro = FinanceiroService(db)

    # TESTE 1: Listar categorias
    print("\n[TESTE 1] Listar Categorias")
    try:
        categorias = await financeiro.listar_categorias()
        print(f"✓ {len(categorias)} categorias encontradas")
        for cat in categorias[:3]:
            print(f"  - {cat['nome']} ({cat['tipo']})")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 2: Criar lançamento de despesa fixa
    print("\n[TESTE 2] Criar Despesa Fixa")
    try:
        categorias = await financeiro.listar_categorias()
        cat_salarios = next((c for c in categorias if 'Salários' in c['nome']), None)

        if cat_salarios:
            lancamento = await financeiro.criar_lancamento(
                categoria_id=cat_salarios['id'],
                valor=8000.00,
                data="2024-12-01",
                descricao="Pagamento Time - Dezembro",
                tipo="despesa",
                recorrencia="fixa",
                usuario="teste"
            )
            print(f"✓ Despesa fixa criada: R$ {lancamento['valor']}")
        else:
            print("✗ Categoria 'Salários' não encontrada")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 3: Criar lançamento de despesa única
    print("\n[TESTE 3] Criar Despesa Única")
    try:
        cat_ferramentas = next((c for c in categorias if 'Ferramentas' in c['nome']), None)

        if cat_ferramentas:
            lancamento = await financeiro.criar_lancamento(
                categoria_id=cat_ferramentas['id'],
                valor=320.00,
                data="2024-12-15",
                descricao="OpenAI API - Dezembro",
                tipo="despesa",
                recorrencia="unica",
                usuario="teste"
            )
            print(f"✓ Despesa única criada: R$ {lancamento['valor']}")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 4: Ver overview
    print("\n[TESTE 4] Overview (30 dias)")
    try:
        overview = await financeiro.get_overview("30d")
        print(f"✓ Overview gerado:")
        print(f"  Receita Bruta: R$ {overview['receita_bruta']:,.2f}")
        print(f"  Despesas Totais: R$ {overview['despesas_totais']:,.2f}")
        print(f"    - Fixas: R$ {overview['despesas_fixas']:,.2f} ({overview['despesas_fixas_pct']:.1f}%)")
        print(f"    - Únicas: R$ {overview['despesas_unicas']:,.2f} ({overview['despesas_unicas_pct']:.1f}%)")
        print(f"  Taxas: R$ {overview['taxas_totais']:,.2f}")
        print(f"  Lucro Líquido: R$ {overview['lucro_liquido']:,.2f}")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 5: Editar taxa
    print("\n[TESTE 5] Editar Taxa (3% → 5%)")
    try:
        taxas = await financeiro.listar_taxas()
        if taxas:
            taxa_id = taxas[0]['id']
            await financeiro.editar_taxa(taxa_id, {"percentual": 5.0})
            print(f"✓ Taxa editada para 5%")

            # Ver overview com nova taxa
            overview = await financeiro.get_overview("30d")
            print(f"  Nova taxa calculada: R$ {overview['taxas_totais']:,.2f}")
            print(f"  Novo lucro: R$ {overview['lucro_liquido']:,.2f}")

            # Voltar para 3%
            await financeiro.editar_taxa(taxa_id, {"percentual": 3.0})
            print(f"✓ Taxa restaurada para 3%")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 6: Criar meta
    print("\n[TESTE 6] Criar Meta")
    try:
        meta = await financeiro.criar_meta(
            nome="Receita Q1 2025",
            tipo="receita",
            valor_objetivo=150000.00,
            periodo_inicio="2025-01-01",
            periodo_fim="2025-03-31"
        )
        print(f"✓ Meta criada: {meta['nome']} (R$ {meta['valor_objetivo']:,.2f})")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 7: Gráficos
    print("\n[TESTE 7] Gerar Gráficos")
    try:
        # Receita vs Despesas
        grafico_linha = await financeiro.get_grafico_receita_despesas("30d")
        print(f"✓ Gráfico linha: {len(grafico_linha)} pontos de dados")

        # Breakdown despesas
        breakdown = await financeiro.get_grafico_despesas_breakdown("30d")
        print(f"✓ Breakdown despesas:")
        print(f"  - Por categoria: {len(breakdown['por_categoria'])} categorias")
        print(f"  - Por recorrência: Fixas ({breakdown['por_recorrencia'][0]['percentual']:.1f}%) / Únicas ({breakdown['por_recorrencia'][1]['percentual']:.1f}%)")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 8: Listar lançamentos com filtros
    print("\n[TESTE 8] Filtrar Lançamentos")
    try:
        # Todas despesas fixas
        fixas = await financeiro.listar_lancamentos("30d", tipo="despesa", recorrencia="fixa")
        print(f"✓ Despesas fixas: {len(fixas)}")

        # Todas despesas únicas
        unicas = await financeiro.listar_lancamentos("30d", tipo="despesa", recorrencia="unica")
        print(f"✓ Despesas únicas: {len(unicas)}")

        # Todas receitas
        receitas = await financeiro.listar_lancamentos("30d", tipo="receita")
        print(f"✓ Receitas: {len(receitas)}")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # TESTE 9: Receita YouTube
    print("\n[TESTE 9] Consultar Receita YouTube")
    try:
        revenue = await financeiro.get_youtube_revenue("30d")
        print(f"✓ Receita YouTube (30d): R$ {revenue:,.2f}")
    except Exception as e:
        print(f"✗ Erro: {e}")

    # RESUMO
    print("\n" + "=" * 60)
    print("RESUMO FINAL DOS TESTES")
    print("=" * 60)
    try:
        categorias = await financeiro.listar_categorias()
        taxas = await financeiro.listar_taxas()
        lancamentos = await financeiro.listar_lancamentos("90d")
        metas = await financeiro.listar_metas()

        print(f"✓ Categorias: {len(categorias)}")
        print(f"✓ Taxas ativas: {len(taxas)}")
        print(f"✓ Lançamentos (90d): {len(lancamentos)}")
        print(f"✓ Metas: {len(metas)}")

        overview = await financeiro.get_overview("30d")
        print(f"\n📊 OVERVIEW (30 dias):")
        print(f"   Receita: R$ {overview['receita_bruta']:,.2f} ({'+' if overview['receita_variacao'] >= 0 else ''}{overview['receita_variacao']}%)")
        print(f"   Despesas: R$ {overview['despesas_totais']:,.2f} ({'+' if overview['despesas_variacao'] >= 0 else ''}{overview['despesas_variacao']}%)")
        print(f"   Lucro: R$ {overview['lucro_liquido']:,.2f} ({'+' if overview['lucro_variacao'] >= 0 else ''}{overview['lucro_variacao']}%)")

    except Exception as e:
        print(f"✗ Erro ao gerar resumo: {e}")

    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test())
