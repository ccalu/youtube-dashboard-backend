"""
Teste das correções do Sistema Financeiro
"""

import asyncio
import os
from dotenv import load_dotenv
from database import SupabaseClient
from financeiro import FinanceiroService

load_dotenv()


async def test_correcoes():
    """Testa correções implementadas"""
    print("=" * 60)
    print("TESTE DAS CORREÇÕES - Sistema Financeiro")
    print("=" * 60)

    db = SupabaseClient()
    financeiro = FinanceiroService(db)

    # TESTE 1: Receita bruta com diferentes períodos
    print("\n[TESTE 1] Receita Bruta - Períodos Diferentes")
    print("-" * 60)

    periodos = ["7d", "15d", "30d"]
    for periodo in periodos:
        receita = await financeiro.get_receita_bruta(periodo)
        print(f"  {periodo:5s} - R$ {receita:,.2f}")

    # TESTE 2: Overview com período curto (7d)
    print("\n[TESTE 2] Overview - 7 dias")
    print("-" * 60)
    overview_7d = await financeiro.get_overview("7d")
    print(f"  Receita Bruta: R$ {overview_7d['receita_bruta']:,.2f}")
    print(f"  Despesas: R$ {overview_7d['despesas_totais']:,.2f}")
    print(f"  Taxas: R$ {overview_7d['taxas_totais']:,.2f}")
    print(f"  Lucro Líquido: R$ {overview_7d['lucro_liquido']:,.2f}")

    # TESTE 3: Overview com período médio (15d)
    print("\n[TESTE 3] Overview - 15 dias")
    print("-" * 60)
    overview_15d = await financeiro.get_overview("15d")
    print(f"  Receita Bruta: R$ {overview_15d['receita_bruta']:,.2f}")
    print(f"  Despesas: R$ {overview_15d['despesas_totais']:,.2f}")
    print(f"  Taxas: R$ {overview_15d['taxas_totais']:,.2f}")
    print(f"  Lucro Líquido: R$ {overview_15d['lucro_liquido']:,.2f}")

    # TESTE 4: Overview com período longo (30d) - para comparar
    print("\n[TESTE 4] Overview - 30 dias")
    print("-" * 60)
    overview_30d = await financeiro.get_overview("30d")
    print(f"  Receita Bruta: R$ {overview_30d['receita_bruta']:,.2f}")
    print(f"  Despesas: R$ {overview_30d['despesas_totais']:,.2f}")
    print(f"  Taxas: R$ {overview_30d['taxas_totais']:,.2f}")
    print(f"  Lucro Líquido: R$ {overview_30d['lucro_liquido']:,.2f}")

    # TESTE 5: Criar taxa (simular JSON body)
    print("\n[TESTE 5] Criar Taxa (simulando JSON body)")
    print("-" * 60)
    try:
        # Simular criação de taxa
        taxa_teste = await financeiro.criar_taxa(
            nome="Imposto Teste",
            percentual=5.0,
            aplica_sobre="receita_bruta"
        )
        print(f"  OK Taxa criada: ID {taxa_teste['id']} - {taxa_teste['nome']} ({taxa_teste['percentual']}%)")

        # Deletar taxa de teste
        await financeiro.deletar_taxa(taxa_teste['id'])
        print(f"  OK Taxa de teste deletada")
    except Exception as e:
        print(f"  ERRO ao criar taxa: {e}")

    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    # Validações
    testes_ok = []
    testes_falha = []

    # Validar se periodos curtos NAO retornam 0
    if overview_7d['receita_bruta'] > 0:
        testes_ok.append("OK Periodo 7d funciona (receita > 0)")
    else:
        testes_falha.append("ERRO Periodo 7d ainda retorna 0")

    if overview_15d['receita_bruta'] > 0:
        testes_ok.append("OK Periodo 15d funciona (receita > 0)")
    else:
        testes_falha.append("ERRO Periodo 15d ainda retorna 0")

    # Validar se 30d ainda funciona
    if overview_30d['receita_bruta'] > 0:
        testes_ok.append("OK Periodo 30d continua funcionando")
    else:
        testes_falha.append("ERRO Periodo 30d quebrou")

    # Validar se valores fazem sentido (7d < 15d < 30d)
    if overview_7d['receita_bruta'] <= overview_15d['receita_bruta'] <= overview_30d['receita_bruta']:
        testes_ok.append("OK Valores crescem conforme periodo aumenta")
    else:
        testes_falha.append("ERRO Valores nao fazem sentido")

    print()
    for teste in testes_ok:
        print(teste)

    if testes_falha:
        print()
        for teste in testes_falha:
            print(teste)

    print("\n" + "=" * 60)
    if not testes_falha:
        print("TODOS OS TESTES PASSARAM!")
    else:
        print(f"{len(testes_falha)} TESTE(S) FALHARAM")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_correcoes())
