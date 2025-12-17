"""
Script de Setup Simples - Sistema Financeiro (sem unicode)
"""

import asyncio
import os
from dotenv import load_dotenv
from database import SupabaseClient
from financeiro import FinanceiroService

load_dotenv()


async def setup():
    """Configura sistema financeiro com dados iniciais"""
    print("=" * 60)
    print("SETUP FINANCEIRO - Dados Iniciais")
    print("=" * 60)

    db = SupabaseClient()
    financeiro = FinanceiroService(db)

    # 1. Criar categorias padrao (apenas despesas)
    print("\n1. Criando categorias padrao...")
    categorias_padrao = [
        {"nome": "Ferramentas/Software", "tipo": "despesa", "cor": "#FF0000", "icon": "tools"},
        {"nome": "Salarios", "tipo": "despesa", "cor": "#CC0000", "icon": "users"},
        {"nome": "Infraestrutura", "tipo": "despesa", "cor": "#DD0000", "icon": "server"},
        {"nome": "Contabilidade", "tipo": "despesa", "cor": "#AA0000", "icon": "calculator"},
    ]

    for cat in categorias_padrao:
        try:
            existentes = await financeiro.listar_categorias()
            if any(c['nome'] == cat['nome'] for c in existentes):
                print(f"   OK - {cat['nome']} ja existe")
                continue

            await financeiro.criar_categoria(
                nome=cat['nome'],
                tipo=cat['tipo'],
                cor=cat['cor'],
                icon=cat['icon']
            )
            print(f"   OK - {cat['nome']} criada")
        except Exception as e:
            print(f"   ERRO ao criar {cat['nome']}: {e}")

    # 2. Criar taxa padrao (3% Imposto)
    print("\n2. Criando taxa padrao...")
    try:
        taxas_existentes = await financeiro.listar_taxas()
        if any(t['nome'] == 'Imposto' for t in taxas_existentes):
            print("   OK - Taxa 'Imposto' ja existe")
        else:
            await financeiro.criar_taxa(
                nome="Imposto",
                percentual=3.0,
                aplica_sobre="receita_bruta"
            )
            print("   OK - Taxa 'Imposto' (3%) criada")
    except Exception as e:
        print(f"   ERRO ao criar taxa: {e}")

    # 3. Sincronizar receita YouTube (ultimos 3 meses)
    print("\n3. Sincronizando receita YouTube (ultimos 90 dias)...")
    try:
        resultado = await financeiro.sync_youtube_revenue("90d")
        print(f"   OK - {resultado['sincronizados']} meses sincronizados")
        print(f"   OK - Total de {resultado['meses']} meses processados")
    except Exception as e:
        print(f"   ERRO ao sincronizar YouTube: {e}")

    # 4. Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    try:
        categorias = await financeiro.listar_categorias()
        taxas = await financeiro.listar_taxas()
        lancamentos = await financeiro.listar_lancamentos("90d")

        print(f"OK - Categorias criadas: {len(categorias)}")
        print(f"OK - Taxas ativas: {len(taxas)}")
        print(f"OK - Lancamentos (90d): {len(lancamentos)}")

        if lancamentos:
            overview = await financeiro.get_overview("30d")
            print(f"\nOVERVIEW (ultimos 30 dias):")
            print(f"  Receita Bruta: R$ {overview['receita_bruta']:,.2f}")
            print(f"  Despesas: R$ {overview['despesas_totais']:,.2f}")
            print(f"    - Fixas: R$ {overview['despesas_fixas']:,.2f}")
            print(f"    - Unicas: R$ {overview['despesas_unicas']:,.2f}")
            print(f"  Taxas (3%): R$ {overview['taxas_totais']:,.2f}")
            print(f"  Lucro Liquido: R$ {overview['lucro_liquido']:,.2f}")

    except Exception as e:
        print(f"ERRO ao gerar resumo: {e}")

    print("\n" + "=" * 60)
    print("SETUP CONCLUIDO!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(setup())
