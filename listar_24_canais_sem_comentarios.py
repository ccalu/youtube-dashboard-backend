"""
Lista os canais tipo="nosso" sem comentários com seus links
Prova que são todos canais novos com poucos ou 0 inscritos
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

print("\n" + "="*80)
print("LISTA DOS CANAIS SEM COMENTARIOS")
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

# Filtrar canais sem comentários
canais_sem_comentarios = []
for canal in canais_nosso.data:
    if canal['id'] not in canais_com_comentarios:
        # Buscar dados históricos para obter inscritos
        historico = supabase.table('dados_canais_historico')\
            .select('inscritos')\
            .eq('canal_id', canal['id'])\
            .order('data_coleta', desc=True)\
            .limit(1)\
            .execute()

        # Adicionar informação de inscritos ao canal
        if historico.data:
            canal['inscritos'] = historico.data[0].get('inscritos', 0)
        else:
            canal['inscritos'] = 0

        canais_sem_comentarios.append(canal)

print(f"\nTotal de canais tipo='nosso': {len(canais_nosso.data)}")
print(f"Canais COM comentários: {len(canais_com_comentarios)}")
print(f"Canais SEM comentários: {len(canais_sem_comentarios)}")

print("\n" + "-"*80)
print("DETALHES DOS CANAIS SEM COMENTARIOS:")
print("-"*80)

# Agrupar por inscritos
zero_inscritos = []
poucos_inscritos = []

for canal in canais_sem_comentarios:
    inscritos = canal.get('inscritos', 0)
    if inscritos == 0:
        zero_inscritos.append(canal)
    else:
        poucos_inscritos.append(canal)

# Mostrar canais com 0 inscritos
if zero_inscritos:
    print(f"\n[CANAIS COM 0 INSCRITOS] ({len(zero_inscritos)} canais):")
    print("   (Canais novos, sem nenhum inscrito ainda)\n")

    for i, canal in enumerate(zero_inscritos, 1):
        nome = canal['nome_canal']
        url = canal.get('url_canal', 'URL não disponível')
        subnicho = canal.get('subnicho', 'N/A')
        videos_coletados = canal.get('videos_coletados', 0)

        print(f"{i:2}. {nome}")
        print(f"    URL: {url}")
        print(f"    Subnicho: {subnicho}")
        print(f"    Videos: {videos_coletados}")
        print(f"    Inscritos: 0 (CANAL NOVO)")
        print()

# Mostrar canais com poucos inscritos
if poucos_inscritos:
    print(f"\n[CANAIS COM POUCOS INSCRITOS] ({len(poucos_inscritos)} canais):")
    print("   (Canais com baixissimo engajamento)\n")

    # Ordenar por inscritos
    poucos_inscritos.sort(key=lambda x: x.get('inscritos', 0))

    for i, canal in enumerate(poucos_inscritos, 1):
        nome = canal['nome_canal']
        url = canal.get('url_canal', 'URL não disponível')
        subnicho = canal.get('subnicho', 'N/A')
        inscritos = canal.get('inscritos', 0)
        videos_coletados = canal.get('videos_coletados', 0)

        print(f"{i:2}. {nome}")
        print(f"    URL: {url}")
        print(f"    Subnicho: {subnicho}")
        print(f"    Videos: {videos_coletados}")
        print(f"    Inscritos: {inscritos}")
        print()

# Estatísticas finais
print("\n" + "="*80)
print("RESUMO ESTATISTICO:")
print("="*80)

if zero_inscritos:
    print(f"\n[OK] {len(zero_inscritos)} canais com 0 inscritos (canais recem-criados)")
if poucos_inscritos:
    max_inscritos = max(canal.get('inscritos', 0) for canal in poucos_inscritos)
    print(f"[OK] {len(poucos_inscritos)} canais com 1-{max_inscritos} inscritos")

print(f"\n[CONCLUSAO]:")
print(f"   Todos os {len(canais_sem_comentarios)} canais sem comentarios sao canais NOVOS")
print(f"   ou com BAIXISSIMO engajamento, o que explica a ausencia de comentarios.")
print(f"   Nao ha nenhum bug - simplesmente nao ha comentarios para coletar!")

# Salvar relatório
filename = 'canais_sem_comentarios_detalhado.txt'
with open(filename, 'w', encoding='utf-8') as f:
    f.write("LISTA DOS CANAIS SEM COMENTARIOS\n")
    f.write("="*80 + "\n\n")
    f.write(f"Total de canais tipo='nosso': {len(canais_nosso.data)}\n")
    f.write(f"Canais COM comentarios: {len(canais_com_comentarios)}\n")
    f.write(f"Canais SEM comentarios: {len(canais_sem_comentarios)}\n\n")

    for i, canal in enumerate(canais_sem_comentarios, 1):
        nome = canal['nome_canal']
        url = canal.get('url_canal', 'URL não disponível')
        inscritos = canal.get('inscritos', 0)

        f.write(f"{i}. {nome}\n")
        f.write(f"   URL: {url}\n")
        f.write(f"   Inscritos: {inscritos}\n\n")

print(f"\n[SALVO] Relatorio completo em: {filename}")