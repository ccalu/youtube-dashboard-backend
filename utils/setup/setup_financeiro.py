"""
Script de Setup - Sistema Financeiro
Cria categorias padrão, taxa padrão e sincroniza receita YouTube
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

    # Inicializar serviços
    db = SupabaseClient()
    financeiro = FinanceiroService(db)

    # 1. Criar categorias padrão
    print("\n1. Criando categorias padrão...")
    categorias_padrao = [
        {"nome": "YouTube AdSense", "tipo": "receita", "cor": "#00FF00", "icon": "youtube"},
        {"nome": "Patrocínios", "tipo": "receita", "cor": "#00CC00", "icon": "handshake"},
        {"nome": "Outros", "tipo": "receita", "cor": "#00AA00", "icon": "dollar"},
        {"nome": "Ferramentas/Software", "tipo": "despesa", "cor": "#FF0000", "icon": "tools"},
        {"nome": "Salários", "tipo": "despesa", "cor": "#CC0000", "icon": "users"},
        {"nome": "Marketing", "tipo": "despesa", "cor": "#FF4444", "icon": "bullhorn"},
        {"nome": "Infraestrutura", "tipo": "despesa", "cor": "#DD0000", "icon": "server"},
        {"nome": "Contabilidade", "tipo": "despesa", "cor": "#AA0000", "icon": "calculator"},
    ]

    for cat in categorias_padrao:
        try:
            # Verificar se já existe
            existentes = await financeiro.listar_categorias()
            if any(c['nome'] == cat['nome'] for c in existentes):
                print(f"   ✓ {cat['nome']} já existe")
                continue

            await financeiro.criar_categoria(
                nome=cat['nome'],
                tipo=cat['tipo'],
                cor=cat['cor'],
                icon=cat['icon']
            )
            print(f"   ✓ {cat['nome']} criada")
        except Exception as e:
            print(f"   ✗ Erro ao criar {cat['nome']}: {e}")

    # 2. Criar taxa padrão (3% Imposto)
    print("\n2. Criando taxa padrão...")
    try:
        # Verificar se já existe
        taxas_existentes = await financeiro.listar_taxas()
        if any(t['nome'] == 'Imposto' for t in taxas_existentes):
            print("   ✓ Taxa 'Imposto' já existe")
        else:
            await financeiro.criar_taxa(
                nome="Imposto",
                percentual=3.0,
                aplica_sobre="receita_bruta"
            )
            print("   ✓ Taxa 'Imposto' (3%) criada")
    except Exception as e:
        print(f"   ✗ Erro ao criar taxa: {e}")

    # 3. Sincronizar receita YouTube (últimos 3 meses)
    print("\n3. Sincronizando receita YouTube (últimos 90 dias)...")
    try:
        resultado = await financeiro.sync_youtube_revenue("90d")
        print(f"   ✓ {resultado['sincronizados']} meses sincronizados")
        print(f"   ✓ Total de {resultado['meses']} meses processados")
    except Exception as e:
        print(f"   ✗ Erro ao sincronizar YouTube: {e}")

    # 4. Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    try:
        categorias = await financeiro.listar_categorias()
        taxas = await financeiro.listar_taxas()
        lancamentos = await financeiro.listar_lancamentos("90d")

        print(f"✓ Categorias criadas: {len(categorias)}")
        print(f"✓ Taxas ativas: {len(taxas)}")
        print(f"✓ Lançamentos (90d): {len(lancamentos)}")

        # Mostrar overview
        overview = await financeiro.get_overview("30d")
        print(f"\nOVERVIEW (últimos 30 dias):")
        print(f"  Receita Bruta: R$ {overview['receita_bruta']:,.2f}")
        print(f"  Despesas: R$ {overview['despesas_totais']:,.2f}")
        print(f"  Taxas: R$ {overview['taxas_totais']:,.2f}")
        print(f"  Lucro Líquido: R$ {overview['lucro_liquido']:,.2f}")

    except Exception as e:
        print(f"✗ Erro ao gerar resumo: {e}")

    print("\n" + "=" * 60)
    print("SETUP CONCLUÍDO!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(setup())
