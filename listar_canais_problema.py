"""
Lista simples dos canais tipo="nosso" sem comentários
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

# Conectar ao Supabase
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Buscar canais tipo="nosso"
canais_nosso = supabase.table('canais_monitorados')\
    .select('*')\
    .eq('tipo', 'nosso')\
    .eq('status', 'ativo')\
    .execute()

# Buscar canais com comentários
comentarios = supabase.table('video_comments')\
    .select('canal_id')\
    .execute()

canais_com_comentarios = set()
for c in comentarios.data:
    if c.get('canal_id'):
        canais_com_comentarios.add(c['canal_id'])

print("="*60)
print("CANAIS TIPO='NOSSO' SEM COMENTARIOS")
print("="*60)

total = 0
com_comentarios = 0
sem_comentarios = []

for canal in canais_nosso.data:
    total += 1
    if canal['id'] in canais_com_comentarios:
        com_comentarios += 1
    else:
        sem_comentarios.append(canal)

print(f"\nRESUMO:")
print(f"- Total: {total} canais")
print(f"- Com comentarios: {com_comentarios} ({com_comentarios/total*100:.1f}%)")
print(f"- Sem comentarios: {len(sem_comentarios)} ({len(sem_comentarios)/total*100:.1f}%)")

print(f"\nLISTA DOS {len(sem_comentarios)} CANAIS SEM COMENTARIOS:")
print("-"*60)

for i, canal in enumerate(sem_comentarios, 1):
    nome_safe = canal['nome_canal'].encode('ascii', 'ignore').decode('ascii')
    url = canal.get('url_canal', 'sem url')
    subnicho = canal.get('subnicho', 'sem subnicho')
    falhas = canal.get('coleta_falhas_consecutivas', 0)

    print(f"\n{i:2}. {nome_safe}")
    print(f"    Subnicho: {subnicho}")
    print(f"    URL: {url}")
    print(f"    Falhas: {falhas}")

# Salvar em arquivo
with open('canais_sem_comentarios.txt', 'w', encoding='utf-8') as f:
    f.write("CANAIS TIPO='NOSSO' SEM COMENTARIOS\n")
    f.write("="*60 + "\n\n")
    f.write(f"Total: {total} canais\n")
    f.write(f"Com comentarios: {com_comentarios}\n")
    f.write(f"Sem comentarios: {len(sem_comentarios)}\n\n")

    for i, canal in enumerate(sem_comentarios, 1):
        f.write(f"\n{i}. {canal['nome_canal']}\n")
        f.write(f"   Subnicho: {canal.get('subnicho', '')}\n")
        f.write(f"   URL: {canal.get('url_canal', '')}\n")
        f.write(f"   Falhas: {canal.get('coleta_falhas_consecutivas', 0)}\n")

print(f"\n[SALVO] Lista completa em: canais_sem_comentarios.txt")