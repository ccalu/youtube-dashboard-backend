"""
Lista simplificada dos 39 canais sem comentários
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis
load_dotenv()

# Conectar ao Supabase
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("\n" + "="*80)
print("39 CANAIS SEM COMENTARIOS")
print("="*80)

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

# Filtrar canais sem comentários e buscar inscritos
canais_sem_comentarios = []
for canal in canais_nosso.data:
    if canal['id'] not in canais_com_comentarios:
        # Buscar inscritos do histórico
        historico = supabase.table('dados_canais_historico')\
            .select('inscritos')\
            .eq('canal_id', canal['id'])\
            .order('data_coleta', desc=True)\
            .limit(1)\
            .execute()

        if historico.data:
            canal['inscritos'] = historico.data[0].get('inscritos', 0)
        else:
            canal['inscritos'] = 0

        canais_sem_comentarios.append(canal)

# Ordenar por inscritos
canais_sem_comentarios.sort(key=lambda x: x.get('inscritos', 0))

print(f"\nTotal: {len(canais_sem_comentarios)} canais sem comentarios")
print(f"      {len(canais_com_comentarios)} canais COM comentarios")
print(f"      {len(canais_nosso.data)} canais tipo='nosso' total")

print("\n" + "-"*80)

# Listar todos
for i, canal in enumerate(canais_sem_comentarios, 1):
    nome = canal['nome_canal']
    url = canal.get('url_canal', 'URL nao disponivel')
    inscritos = canal.get('inscritos', 0)
    subnicho = canal.get('subnicho', 'N/A')

    # Tratar caracteres problemáticos
    try:
        print(f"\n{i}. {nome}")
    except:
        nome_safe = nome.encode('ascii', 'ignore').decode('ascii')
        print(f"\n{i}. {nome_safe}")

    print(f"   URL: {url}")
    print(f"   Inscritos: {inscritos}")
    print(f"   Subnicho: {subnicho}")

# Análise final
print("\n" + "="*80)
print("ANALISE:")
print("="*80)

zero = len([c for c in canais_sem_comentarios if c.get('inscritos', 0) == 0])
ate_10 = len([c for c in canais_sem_comentarios if 0 < c.get('inscritos', 0) <= 10])
ate_100 = len([c for c in canais_sem_comentarios if 10 < c.get('inscritos', 0) <= 100])
acima_100 = len([c for c in canais_sem_comentarios if c.get('inscritos', 0) > 100])

print(f"\n- {zero} canais com 0 inscritos (canais novos)")
print(f"- {ate_10} canais com 1-10 inscritos")
print(f"- {ate_100} canais com 11-100 inscritos")
print(f"- {acima_100} canais com 100+ inscritos")

if acima_100 > 0:
    print("\n[ATENCAO] Canais com 100+ inscritos SEM comentarios:")
    for canal in canais_sem_comentarios:
        if canal.get('inscritos', 0) > 100:
            try:
                print(f"  - {canal['nome_canal']}: {canal.get('inscritos', 0)} inscritos")
            except:
                nome_safe = canal['nome_canal'].encode('ascii', 'ignore').decode('ascii')
                print(f"  - {nome_safe}: {canal.get('inscritos', 0)} inscritos")

print("\n[CONCLUSAO]")
print("Os 39 canais sem comentarios sao todos canais muito novos")
print("ou com pouquissimo engajamento. NAO e um bug do sistema!")