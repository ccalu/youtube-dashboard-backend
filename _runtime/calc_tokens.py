"""Calculo de tokens e custos dos 5 agentes (GPT-4o-mini)"""

# Pricing GPT-4o-mini
# Input: $0.15 per 1M tokens
# Output: $0.60 per 1M tokens

agents = [
    {"name": "Ag.1 Copy",          "calls": 1, "input": 1950,  "output": 500},
    {"name": "Ag.2 Autenticidade",  "calls": 1, "input": 2525,  "output": 688},
    {"name": "Ag.3 Micronichos",    "calls": 2, "input": 3025,  "output": 1188},
    {"name": "Ag.4 Titulo",         "calls": 2, "input": 3700,  "output": 1313},
    {"name": "Ag.5 Temas",          "calls": 2, "input": 4150,  "output": 1813},
]

PRICE_INPUT = 0.15 / 1_000_000
PRICE_OUTPUT = 0.60 / 1_000_000

print("=" * 80)
print("CALCULO DE TOKENS — 5 AGENTES (GPT-4o-mini)")
print("=" * 80)
print()

header = f"  {'Agente':<22} {'Calls':>5} {'Input':>8} {'Output':>8} {'Total':>8} {'Custo USD':>12}"
print(header)
print("  " + "-" * 70)

total_input = 0
total_output = 0
total_calls = 0

for a in agents:
    total = a["input"] + a["output"]
    cost = a["input"] * PRICE_INPUT + a["output"] * PRICE_OUTPUT
    total_input += a["input"]
    total_output += a["output"]
    total_calls += a["calls"]
    name = a["name"]
    print(f"  {name:<22} {a['calls']:>5} {a['input']:>7,} {a['output']:>7,} {total:>7,}   ${cost:.5f}")

total_tokens = total_input + total_output
total_cost = total_input * PRICE_INPUT + total_output * PRICE_OUTPUT

print("  " + "-" * 70)
print(f"  {'TOTAL 1 CANAL':<22} {total_calls:>5} {total_input:>7,} {total_output:>7,} {total_tokens:>7,}   ${total_cost:.5f}")
print()

# Scale
print("=" * 80)
print("PROJECAO DE CUSTOS POR NUMERO DE CANAIS")
print("=" * 80)
print()

for n in [1, 10, 40, 43, 50, 100]:
    cost = n * total_cost
    tokens = n * total_tokens
    print(f"  {n:>3} canais:  {tokens:>10,} tokens   =   ${cost:.4f} USD")

print()
print("=" * 80)
print("PROJECAO POR FREQUENCIA (40 canais)")
print("=" * 80)
print()

freqs = [
    (1,  "1x (execucao unica)"),
    (4,  "4x/mes (semanal)"),
    (8,  "8x/mes (2x semana)"),
    (30, "30x/mes (diario)"),
]
for mult, label in freqs:
    cost = 40 * total_cost * mult
    tokens = 40 * total_tokens * mult
    print(f"  {label:<28} {tokens:>12,} tokens   =   ${cost:.4f} USD/mes")

print()
print("=" * 80)
print("COMPARACAO DE MODELOS (40 canais, 4x/mes)")
print("=" * 80)
print()

models = [
    ("GPT-4o-mini",  0.15,  0.60),
    ("GPT-4o",       2.50,  10.00),
    ("GPT-4.1-mini", 0.40,  1.60),
    ("GPT-4.1",      2.00,  8.00),
    ("Claude Haiku",  0.25,  1.25),
    ("Claude Sonnet", 3.00,  15.00),
]

runs = 40 * 4  # 40 canais, 4x/mes

print(f"  {'Modelo':<18} {'Input/1M':>10} {'Output/1M':>10} {'Custo/mes':>12}")
print("  " + "-" * 55)

for name, pin, pout in models:
    cost = runs * (total_input * pin / 1_000_000 + total_output * pout / 1_000_000)
    print(f"  {name:<18}    ${pin:<7.2f}    ${pout:<7.2f}    ${cost:.4f}")

print()
print("=" * 80)
print("RESUMO")
print("=" * 80)
print()
print(f"  Tokens por canal (5 agentes, 8 LLM calls):  ~{total_tokens:,}")
print(f"  Custo por canal (GPT-4o-mini):               ${total_cost:.5f}")
print(f"  Custo 40 canais (1 execucao):                ${40 * total_cost:.4f}")
print(f"  Custo 40 canais mensal (semanal):            ${40 * 4 * total_cost:.4f}")
print(f"  Conclusao: EXTREMAMENTE BARATO")
print()
