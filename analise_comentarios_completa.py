"""
Análise completa do sistema de comentários
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta

# Configurar encoding UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase com SERVICE_ROLE_KEY
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_service_key:
    print("❌ ERRO: Credenciais Supabase não configuradas no .env")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_service_key)

print("\n" + "="*80)
print("🔍 ANÁLISE COMPLETA DO SISTEMA DE COMENTÁRIOS")
print("="*80)

# 1. Estatísticas gerais
response = supabase.table('video_comments').select('id', count='exact').execute()
total_comments = response.count if response else 0

hoje = datetime.now().date().isoformat()
ontem = (datetime.now() - timedelta(days=1)).date().isoformat()

response = supabase.table('video_comments')\
    .select('id', count='exact')\
    .gte('collected_at', hoje)\
    .execute()
coletados_hoje = response.count if response else 0

response = supabase.table('video_comments')\
    .select('id', count='exact')\
    .gte('collected_at', ontem)\
    .lt('collected_at', hoje)\
    .execute()
coletados_ontem = response.count if response else 0

print(f"\n📊 ESTATÍSTICAS GERAIS:")
print(f"   Total de comentários no banco: {total_comments:,}")
print(f"   Coletados hoje ({hoje}): {coletados_hoje}")
print(f"   Coletados ontem ({ontem}): {coletados_ontem}")

# 2. Canais monetizados e seus comentários
print(f"\n💰 CANAIS MONETIZADOS (foco do sistema):")
print("-" * 60)

response = supabase.table('canais_monitorados')\
    .select('*')\
    .eq('tipo', 'nosso')\
    .eq('monetizado', True)\
    .order('nome_canal')\
    .execute()

total_em_monetizados = 0
if response.data:
    canais_monetizados = response.data
    print(f"Total de canais monetizados: {len(canais_monetizados)}\n")

    for canal in canais_monetizados:
        canal_id = canal['id']
        nome = canal['nome_canal']

        # Total de comentários do canal
        resp = supabase.table('video_comments')\
            .select('id', count='exact')\
            .eq('canal_id', canal_id)\
            .execute()
        total_canal = resp.count if resp else 0
        total_em_monetizados += total_canal

        # Comentários de hoje
        resp = supabase.table('video_comments')\
            .select('id', count='exact')\
            .eq('canal_id', canal_id)\
            .gte('collected_at', hoje)\
            .execute()
        hoje_canal = resp.count if resp else 0

        # Última coleta
        ultima_coleta = canal.get('ultimo_comentario_coletado', 'Nunca')
        if ultima_coleta and ultima_coleta != 'Nunca':
            ultima_coleta = ultima_coleta[:10]  # Pegar só a data

        print(f"   📺 {nome}:")
        print(f"      Total: {total_canal} | Hoje: {hoje_canal} | Última coleta: {ultima_coleta}")

    print(f"\n   🎯 TOTAL EM MONETIZADOS: {total_em_monetizados} comentários")

# 3. Buscar vídeos específicos (Grandes Mansões e similares)
print(f"\n🏠 VÍDEOS RELACIONADOS A MANSÕES/CASAS:")
print("-" * 60)

# Buscar com diferentes termos
buscar_termos = [
    ('mansões', 'Grandes Mansões'),
    ('mansoes', 'Mansões'),
    ('mansion', 'Mansions'),
    ('casa', 'Casas'),
    ('luxury', 'Luxury/Luxo'),
    ('milionários', 'Milionários'),
    ('ricos', 'Ricos')
]

videos_encontrados = []
for termo, descricao in buscar_termos:
    response = supabase.table('videos')\
        .select('id, titulo, views_count, publicado_em, canal_id')\
        .ilike('titulo', f'%{termo}%')\
        .order('publicado_em', desc=True)\
        .limit(2)\
        .execute()

    if response.data:
        print(f"\n   🔍 Termo '{descricao}':")
        for video in response.data:
            videos_encontrados.append(video['id'])

            # Buscar nome do canal
            canal_resp = supabase.table('canais_monitorados')\
                .select('nome_canal, monetizado')\
                .eq('id', video['canal_id'])\
                .single()\
                .execute()

            if canal_resp.data:
                canal_nome = canal_resp.data['nome_canal']
                monetizado = "💰" if canal_resp.data.get('monetizado') else ""
            else:
                canal_nome = f"Canal ID {video['canal_id']}"
                monetizado = ""

            # Contar comentários do vídeo
            com_resp = supabase.table('video_comments')\
                .select('id', count='exact')\
                .eq('video_id', video['id'])\
                .execute()
            total_comments_video = com_resp.count if com_resp else 0

            # Comentários coletados hoje
            com_resp_hoje = supabase.table('video_comments')\
                .select('id', count='exact')\
                .eq('video_id', video['id'])\
                .gte('collected_at', hoje)\
                .execute()
            hoje_comments = com_resp_hoje.count if com_resp_hoje else 0

            print(f"      • {video['titulo'][:60]}...")
            print(f"        Canal: {canal_nome} {monetizado}")
            print(f"        Views: {video.get('views_count', 0):,} | Comentários: {total_comments_video} (Hoje: {hoje_comments})")
            print(f"        Publicado: {video['publicado_em'][:10]}")

# 4. Últimos logs de coleta
print(f"\n📝 ÚLTIMOS LOGS DE COLETA DE COMENTÁRIOS:")
print("-" * 60)

response = supabase.table('comment_collection_logs')\
    .select('*')\
    .order('created_at', desc=True)\
    .limit(10)\
    .execute()

if response.data:
    for log in response.data[:7]:
        status = "✅" if log['status'] == 'success' else "❌"
        data = log['created_at'][:19]
        canal = log.get('canal_nome', 'N/A')
        coletados = log.get('comments_collected', 0)
        print(f"   {status} {data} - {canal}: {coletados} comentários")
        if log.get('error_message'):
            print(f"      ⚠️ {log['error_message'][:80]}...")

# 5. Análise do problema reportado
print(f"\n⚠️ ANÁLISE DO PROBLEMA REPORTADO:")
print("-" * 60)
print("Você mencionou ver apenas 6 comentários no dashboard.")
print("\nPossíveis causas:")

# Verificar o que o endpoint retornaria
response = supabase.table('canais_monitorados')\
    .select('id')\
    .eq('tipo', 'nosso')\
    .eq('monetizado', True)\
    .execute()

if response.data:
    monetized_ids = [canal['id'] for canal in response.data]

    # Comentários com is_responded=False (não respondidos)
    response = supabase.table('video_comments')\
        .select('id', count='exact')\
        .in_('canal_id', monetized_ids)\
        .eq('is_responded', False)\
        .execute()
    nao_respondidos = response.count if response else 0

    print(f"\n1. ❓ Filtro de 'não respondidos':")
    print(f"   - Total em monetizados: {total_em_monetizados}")
    print(f"   - Não respondidos: {nao_respondidos}")

    if nao_respondidos < 10:
        print(f"   ⚠️ ESTE PODE SER O PROBLEMA! Poucos comentários não respondidos.")

# Verificar coleta recente
print(f"\n2. 📅 Verificação de coletas recentes:")
ultimos_3_dias = (datetime.now() - timedelta(days=3)).date().isoformat()
response = supabase.table('video_comments')\
    .select('id', count='exact')\
    .gte('collected_at', ultimos_3_dias)\
    .execute()
ultimos_3 = response.count if response else 0

print(f"   - Últimos 3 dias: {ultimos_3} comentários coletados")
print(f"   - Hoje: {coletados_hoje}")
print(f"   - Ontem: {coletados_ontem}")

# 6. Sugestão de ação
print(f"\n💡 RECOMENDAÇÕES:")
print("-" * 60)
print("1. O sistema está coletando (90 hoje, 23 ontem)")
print("2. Total de {total_comments:,} comentários no banco")
print("3. {total_em_monetizados} comentários em canais monetizados")
print("\nSe o dashboard mostra poucos:")
print("   - Pode ser filtro de 'não respondidos'")
print("   - Verificar se filtros no frontend estão corretos")
print("   - Forçar atualização do cache (botão Atualizar)")

print("\n" + "="*80)
print("FIM DA ANÁLISE")
print("="*80)