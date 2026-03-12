import tiktoken, re
enc = tiktoken.encoding_for_model('gpt-4o-mini')
print('Tokenizer: o200k_base (GPT-4o-mini)')

def extract_prompt(content, marker, search_from=0):
    idx = content.find(marker, search_from)
    if idx == -1: return None, -1
    tq = content.find('"""', idx)
    if tq == -1: return None, -1
    end = content.find('"""', tq + 3)
    if end == -1: return None, -1
    return content[tq+3:end], end

# Read all agents
with open('copy_analysis_agent.py', 'r', encoding='utf-8') as f:
    ag1 = f.read()
with open('authenticity_agent.py', 'r', encoding='utf-8') as f:
    ag2 = f.read()
with open('micronicho_agent.py', 'r', encoding='utf-8') as f:
    ag3 = f.read()
with open('title_structure_agent.py', 'r', encoding='utf-8') as f:
    ag4 = f.read()

# Extract prompts
s1, _ = extract_prompt(ag1, 'system_prompt = """')
u1_m = list(re.finditer(r'user_prompt\s*=\s*f"""(.*?)"""', ag1, re.DOTALL))
u1 = u1_m[0].group(1) if u1_m else ''

s2, _ = extract_prompt(ag2, 'system_prompt = """')
u2_m = list(re.finditer(r'user_prompt\s*=\s*f"""(.*?)"""', ag2, re.DOTALL))
u2 = u2_m[0].group(1) if u2_m else ''

s3a, e3 = extract_prompt(ag3, 'system_prompt = """')
s3b, _ = extract_prompt(ag3, 'system_prompt = """', e3+1)
u3_m = list(re.finditer(r'user_prompt\s*=\s*f"""(.*?)"""', ag3, re.DOTALL))
u3a = u3_m[0].group(1) if len(u3_m)>0 else ''
u3b = u3_m[1].group(1) if len(u3_m)>1 else ''

s4a, e4 = extract_prompt(ag4, 'system_prompt = """')
s4b, _ = extract_prompt(ag4, 'system_prompt = """', e4+1)
u4_m = list(re.finditer(r'user_prompt\s*=\s*f"""(.*?)"""', ag4, re.DOTALL))
u4a = u4_m[0].group(1) if len(u4_m)>0 else ''
u4b = u4_m[1].group(1) if len(u4_m)>1 else ''

# Token counts
prompts = {
    'Ag1 Copy sys':   (len(enc.encode(s1)), len(s1)),
    'Ag1 Copy usr':   (len(enc.encode(u1)), len(u1)),
    'Ag2 Auth sys':   (len(enc.encode(s2)), len(s2)),
    'Ag2 Auth usr':   (len(enc.encode(u2)), len(u2)),
    'Ag3 C1 sys':     (len(enc.encode(s3a)), len(s3a)),
    'Ag3 C1 usr':     (len(enc.encode(u3a)), len(u3a)),
    'Ag3 C2 sys':     (len(enc.encode(s3b)), len(s3b)),
    'Ag3 C2 usr':     (len(enc.encode(u3b)), len(u3b)),
    'Ag4 C1 sys':     (len(enc.encode(s4a)), len(s4a)),
    'Ag4 C1 usr':     (len(enc.encode(u4a)), len(u4a)),
    'Ag4 C2 sys':     (len(enc.encode(s4b)), len(s4b)),
    'Ag4 C2 usr':     (len(enc.encode(u4b)), len(u4b)),
}

print()
print('='*70)
print(f'{"Componente":<20} {"Tokens REAIS":>14} {"Chars":>8} {"Chars/Tok":>10}')
print('='*70)

total_t = 0
total_c = 0
for name, (toks, chars) in prompts.items():
    ratio = chars/toks if toks > 0 else 0
    print(f'{name:<20} {toks:>14,} {chars:>8,} {ratio:>10.2f}')
    total_t += toks
    total_c += chars

print('-'*70)
print(f'{"TOTAL FIXO":<20} {total_t:>14,} {total_c:>8,} {total_c/total_t:.2f}')
print()
print(f'FATOR REAL: {total_c/total_t:.2f} chars por token (portugues no o200k_base)')

# --- DADOS DINAMICOS SIMULADOS ---
sample_titles = [
    'O Dia em que a Russia Invadiu um Pais Inteiro em 24 Horas',
    'A Historia SOMBRIA do Soldado que Sobreviveu ao Impossivel',
    'Por que Ninguem Fala sobre ESTE Massacre da Segunda Guerra',
    '5 Batalhas que Mudaram o Curso da Humanidade Para Sempre',
    'A Verdade sobre o Soldado que Matou 300 Inimigos Sozinho',
] * 5
titles_text = '\n'.join(f'{i+1}. {t}' for i, t in enumerate(sample_titles))
titles_tok = len(enc.encode(titles_text))

sample_report = ('OBSERVACOES:\nO canal apresenta forte concentracao no micronicho de '
    'batalhas historicas com media de 45K views. Os 3 micronichos principais '
    'concentram 67% da producao. Micronicho "Soldados Lendarios" performa 2.3x '
    'acima da media do canal.\n\nRECOMENDACOES:\n- Aumentar producao em Soldados '
    'Lendarios (potencial claro)\n- Testar micronicho "Armas Historicas" (2 videos '
    'com 80K+ views)\n- Reduzir "Cronologia Geral" (abaixo da media)\n\nTENDENCIAS:\n'
    'Micronichos de narrativa pessoal (+35% vs generico). Canal migrando naturalmente '
    'para storytelling individual vs resumos historicos.')
report_tok = len(enc.encode(sample_report))

ranking_text = '\n'.join(
    f'{i+1}. {["Soldados Lendarios","Batalhas Decisivas","Guerras Esquecidas","Armas Historicas","Estrategia Militar","Espionagem","Resistencia Civil","Massacres","Tratados de Paz","Cronologia Geral"][i]}: '
    f'{20-i*2} videos | avg {50000-i*3000:,} views | {35-i*2}% concentracao'
    for i in range(10))
ranking_tok = len(enc.encode(ranking_text))

data_copy_lines = []
for i in range(7):
    struct = chr(65+i)
    data_copy_lines.append(f'\nEstrutura {struct}: 4 videos | ret: {35+i:.1f}% | watch: {180+i*20}s | views: {25000+i*5000:,} | desvio: {2.5+i*0.3:.1f}%')
    for j in range(4):
        data_copy_lines.append(f'  "Titulo do video exemplo {j+1} com texto medio" | ret: {33+j:.1f}% | views: {20000+j*3000:,}')
data_copy_text = '\n'.join(data_copy_lines)
data_copy_tok = len(enc.encode(data_copy_text))

data_auth_text = f'Score: 72.5\nLevel: BOM\nStructure Score: 65.3\nTitle Score: 79.7\n\nDistribuicao: A=25%, B=20%, C=15%, D=12%, E=10%, F=10%, G=8%\nEntropy: 1.85\nDominance: 25%\n\nSimilaridade media: 35%\nSerial patterns: 2\nTop keyword: 15%\n\nTitulos:\n{titles_text}'
data_auth_tok = len(enc.encode(data_auth_text))

patterns_text = 'Concentracao: 45% nos top 3 micronichos\nCanibalizacao: Micronicho-1 vs Micronicho-3 (overlap 60%)\nOportunidade: Micronicho-7 subexplorado (2 videos, avg 65K views)'
patterns_tok = len(enc.encode(patterns_text))

prev_list_tok = 100

print()
print('='*70)
print('DADOS DINAMICOS (simulados, 25 videos)')
print('='*70)
print(f'25 titulos:      {titles_tok:>6,} tokens')
print(f'Report anterior: {report_tok:>6,} tokens')
print(f'Ranking (10):    {ranking_tok:>6,} tokens')
print(f'Data copy (7 est x 4 vid): {data_copy_tok:>6,} tokens')
print(f'Data auth:       {data_auth_tok:>6,} tokens')
print(f'Patterns:        {patterns_tok:>6,} tokens')

# --- CALCULO FINAL ---
ag1_in = prompts['Ag1 Copy sys'][0] + prompts['Ag1 Copy usr'][0] + data_copy_tok + report_tok
ag1_out = 800
ag2_in = prompts['Ag2 Auth sys'][0] + prompts['Ag2 Auth usr'][0] + data_auth_tok + report_tok
ag2_out = 1000
ag3c1_in = prompts['Ag3 C1 sys'][0] + prompts['Ag3 C1 usr'][0] + titles_tok + prev_list_tok
ag3c1_out = 400
ag3c2_in = prompts['Ag3 C2 sys'][0] + prompts['Ag3 C2 usr'][0] + ranking_tok + patterns_tok + report_tok
ag3c2_out = 1200
ag4c1_in = prompts['Ag4 C1 sys'][0] + prompts['Ag4 C1 usr'][0] + titles_tok + prev_list_tok + 30
ag4c1_out = 500
ag4c2_in = prompts['Ag4 C2 sys'][0] + prompts['Ag4 C2 usr'][0] + ranking_tok + patterns_tok + report_tok + 80
ag4c2_out = 1300

ag1_total = ag1_in + ag1_out
ag2_total = ag2_in + ag2_out
ag3_total = ag3c1_in + ag3c1_out + ag3c2_in + ag3c2_out
ag4_total = ag4c1_in + ag4c1_out + ag4c2_in + ag4c2_out

print()
print('='*70)
print('TOKENS REAIS POR AGENTE POR CANAL (tiktoken)')
print('='*70)
print(f'Ag1 Copy:          in={ag1_in:>5,} + out~{ag1_out:>5,} = {ag1_total:>6,} tokens/canal')
print(f'Ag2 Autenticidade: in={ag2_in:>5,} + out~{ag2_out:>5,} = {ag2_total:>6,} tokens/canal')
print(f'Ag3 Micro (2 calls): in={ag3c1_in+ag3c2_in:>5,} + out~{ag3c1_out+ag3c2_out:>5,} = {ag3_total:>6,} tokens/canal')
print(f'Ag4 Titulo (2 calls): in={ag4c1_in+ag4c2_in:>5,} + out~{ag4c1_out+ag4c2_out:>5,} = {ag4_total:>6,} tokens/canal')
print(f'4 agentes juntos:                             = {ag1_total+ag2_total+ag3_total+ag4_total:>6,} tokens/canal')

print()
print('='*70)
print('TOTAL POR RUN COMPLETO (Ag1-2: 21 canais | Ag3-4: 40 canais)')
print('='*70)
t1 = ag1_total * 21
t2 = ag2_total * 21
t3 = ag3_total * 40
t4 = ag4_total * 40
total_4 = t1+t2+t3+t4

print(f'Ag1 x 21 canais: {ag1_total:>6,} x 21 = {t1:>10,}')
print(f'Ag2 x 21 canais: {ag2_total:>6,} x 21 = {t2:>10,}')
print(f'Ag3 x 40 canais: {ag3_total:>6,} x 40 = {t3:>10,}')
print(f'Ag4 x 40 canais: {ag4_total:>6,} x 40 = {t4:>10,}')
print(f'{"":->50}')
print(f'TOTAL 4 AGENTES:              {total_4:>10,}')
print(f'% do limite 10M:              {total_4/10_000_000*100:>10.1f}%')

# 7 agentes projecao
ag5_per = ag3_total
ag6_per = 3000
ag7_per = 2000
t5 = ag5_per * 40
t6 = ag6_per * 21
t7 = ag7_per * 15
total_7 = total_4 + t5 + t6 + t7

print()
print(f'PROJECAO 7 AGENTES:')
print(f'Ag5 Temas x 40:  {ag5_per:>6,} x 40 = {t5:>10,}')
print(f'Ag6 Recom x 21:  {ag6_per:>6,} x 21 = {t6:>10,}')
print(f'Ag7 Conc x 15:   {ag7_per:>6,} x 15 = {t7:>10,}')
print(f'+ 4 atuais:                   {total_4:>10,}')
print(f'{"":->50}')
print(f'TOTAL 7 AGENTES:              {total_7:>10,}')
print(f'% do limite 10M:              {total_7/10_000_000*100:>10.1f}%')

print()
print('='*70)
print('VEREDICTO')
print('='*70)
L = 10_000_000
print(f'4 agentes, 1 run/semana:  {total_4:>10,} tokens = {total_4/L*100:.1f}% do limite DIARIO')
print(f'7 agentes, 1 run/semana:  {total_7:>10,} tokens = {total_7/L*100:.1f}% do limite DIARIO')
print(f'7 agentes, 1 run/semana = {total_7/70_000_000*100:.2f}% do limite SEMANAL (70M)')
print(f'Sobra:                    {L-total_7:>10,} tokens/dia ({(L-total_7)/L*100:.1f}%)')
print(f'API calls: 4ag={21*2 + 40*4} | 7ag={21*2 + 40*4 + 40*2 + 21 + 15}')
