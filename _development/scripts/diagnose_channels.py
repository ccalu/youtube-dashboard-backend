"""
Diagnóstico profundo: canais "nosso" sem métricas / com erros recorrentes
Roda localmente com .env configurado
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Carregar .env do diretório do projeto
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(project_root, ".env"))

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: SUPABASE_URL e SUPABASE_KEY devem estar no .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
sb_service = create_client(SUPABASE_URL, SERVICE_ROLE_KEY) if SERVICE_ROLE_KEY else None

now_utc = datetime.now(timezone.utc)
seven_days_ago = (now_utc - timedelta(days=7)).isoformat()
three_days_ago = (now_utc - timedelta(days=3)).isoformat()

print("=" * 80)
print(f"  DIAGNÓSTICO DE CANAIS - {now_utc.strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 80)

# ─────────────────────────────────────────────────────────────
# 1. TODOS OS CANAIS NOSSO (ativos)
# ─────────────────────────────────────────────────────────────
print("\n\n📋 1. CANAIS NOSSO ATIVOS")
print("-" * 60)

resp = sb.table("canais_monitorados")\
    .select("id, nome_canal, url_canal, subnicho, lingua, tipo, status, ultima_coleta, coleta_falhas_consecutivas, coleta_ultimo_erro, coleta_ultimo_sucesso")\
    .eq("tipo", "nosso")\
    .eq("status", "ativo")\
    .order("subnicho")\
    .execute()

canais_nosso = resp.data
print(f"Total canais nosso ativos: {len(canais_nosso)}")

# ─────────────────────────────────────────────────────────────
# 2. CANAIS COM FALHAS CONSECUTIVAS
# ─────────────────────────────────────────────────────────────
print("\n\n🚨 2. CANAIS COM FALHAS CONSECUTIVAS (coleta_falhas_consecutivas > 0)")
print("-" * 60)

canais_com_falhas = [c for c in canais_nosso if (c.get("coleta_falhas_consecutivas") or 0) > 0]
if canais_com_falhas:
    canais_com_falhas.sort(key=lambda x: x.get("coleta_falhas_consecutivas", 0), reverse=True)
    for c in canais_com_falhas:
        falhas = c.get("coleta_falhas_consecutivas", 0)
        erro = c.get("coleta_ultimo_erro", "N/A")
        ultimo_sucesso = c.get("coleta_ultimo_sucesso", "Nunca")
        print(f"  ❌ {c['nome_canal']}")
        print(f"     Falhas consecutivas: {falhas}")
        print(f"     Último erro: {erro}")
        print(f"     Último sucesso: {ultimo_sucesso}")
        print(f"     Subnicho: {c.get('subnicho')}")
        print()
else:
    print("  ✅ Nenhum canal com falhas consecutivas!")

# ─────────────────────────────────────────────────────────────
# 3. CANAIS SEM COLETA RECENTE (última coleta > 3 dias)
# ─────────────────────────────────────────────────────────────
print("\n\n⏰ 3. CANAIS SEM COLETA RECENTE (última coleta > 3 dias)")
print("-" * 60)

canais_desatualizados = []
for c in canais_nosso:
    ultima = c.get("ultima_coleta")
    if not ultima:
        canais_desatualizados.append((c, "NUNCA COLETADO"))
    else:
        try:
            dt = datetime.fromisoformat(ultima.replace("Z", "+00:00"))
            if dt < now_utc - timedelta(days=3):
                dias_atras = (now_utc - dt).days
                canais_desatualizados.append((c, f"{dias_atras} dias atrás"))
        except:
            canais_desatualizados.append((c, f"Data inválida: {ultima}"))

if canais_desatualizados:
    for c, motivo in canais_desatualizados:
        print(f"  ⚠️  {c['nome_canal']} → {motivo}")
        print(f"     Último erro: {c.get('coleta_ultimo_erro', 'N/A')}")
else:
    print("  ✅ Todos os canais foram coletados nos últimos 3 dias!")

# ─────────────────────────────────────────────────────────────
# 4. HISTÓRICO DE COLETAS (últimos 7 dias)
# ─────────────────────────────────────────────────────────────
print("\n\n📊 4. HISTÓRICO DE COLETAS (últimos 7 dias)")
print("-" * 60)

try:
    resp_coletas = sb.table("coletas_historico")\
        .select("*")\
        .gte("created_at", seven_days_ago)\
        .order("created_at", desc=True)\
        .execute()

    if resp_coletas.data:
        for coleta in resp_coletas.data:
            status = coleta.get("status", "?")
            created = coleta.get("created_at", "?")[:19]
            sucesso = coleta.get("canais_sucesso", "?")
            erro = coleta.get("canais_erro", "?")
            total = coleta.get("canais_processados", "?")
            videos = coleta.get("videos_coletados", "?")
            quota = coleta.get("requisicoes_usadas", "?")

            icon = "✅" if status == "sucesso" else "⚠️" if status == "parcial" else "❌"
            print(f"  {icon} {created} | Status: {status}")
            print(f"     Canais: {sucesso}/{total} sucesso, {erro} erros | Vídeos: {videos} | Quota: {quota}")
    else:
        print("  ❓ Nenhuma coleta registrada nos últimos 7 dias!")
except Exception as e:
    print(f"  ERRO ao buscar coletas_historico: {e}")

# ─────────────────────────────────────────────────────────────
# 5. VÍDEOS RECENTES DOS CANAIS NOSSO (últimos 7 dias)
# ─────────────────────────────────────────────────────────────
print("\n\n🎬 5. VÍDEOS RECENTES POR CANAL (dados em videos_historico, últimos 7 dias)")
print("-" * 60)

channel_ids_nosso = [c["id"] for c in canais_nosso]
nomes_por_id = {c["id"]: c["nome_canal"] for c in canais_nosso}

# Buscar vídeos dos últimos 7 dias para canais nosso
canais_sem_videos = []
canais_com_videos = []

for canal in canais_nosso:
    try:
        resp_videos = sb.table("videos_historico")\
            .select("id, titulo, views_atuais, data_publicacao")\
            .eq("canal_id", canal["id"])\
            .gte("data_publicacao", seven_days_ago)\
            .order("data_publicacao", desc=True)\
            .limit(5)\
            .execute()

        n_videos = len(resp_videos.data) if resp_videos.data else 0
        if n_videos == 0:
            canais_sem_videos.append(canal["nome_canal"])
        else:
            canais_com_videos.append((canal["nome_canal"], n_videos, resp_videos.data))
    except Exception as e:
        canais_sem_videos.append(f"{canal['nome_canal']} (ERRO: {e})")

print(f"\n  Canais COM vídeos nos últimos 7 dias: {len(canais_com_videos)}")
for nome, n, videos in canais_com_videos:
    print(f"    📹 {nome}: {n} vídeos")
    for v in videos[:2]:
        print(f"       - {v.get('titulo', '?')[:50]} ({v.get('views_atuais', 0)} views)")

print(f"\n  Canais SEM vídeos nos últimos 7 dias: {len(canais_sem_videos)}")
for nome in canais_sem_videos:
    print(f"    ⚠️  {nome}")

# ─────────────────────────────────────────────────────────────
# 6. DADOS HISTÓRICOS (dados_canais_historico) - últimos 7 dias
# ─────────────────────────────────────────────────────────────
print("\n\n📈 6. DADOS DE MÉTRICAS DIÁRIAS (dados_canais_historico)")
print("-" * 60)

canais_sem_historico = []
canais_com_historico = []

for canal in canais_nosso:
    try:
        resp_hist = sb.table("dados_canais_historico")\
            .select("id, created_at, views_7d, views_30d, inscritos")\
            .eq("canal_id", canal["id"])\
            .gte("created_at", seven_days_ago)\
            .order("created_at", desc=True)\
            .limit(3)\
            .execute()

        n_registros = len(resp_hist.data) if resp_hist.data else 0
        if n_registros == 0:
            canais_sem_historico.append(canal["nome_canal"])
        else:
            ultimo = resp_hist.data[0]
            canais_com_historico.append((
                canal["nome_canal"],
                n_registros,
                ultimo.get("views_7d", 0),
                ultimo.get("views_30d", 0),
                ultimo.get("inscritos", 0),
                ultimo.get("created_at", "?")[:10]
            ))
    except Exception as e:
        canais_sem_historico.append(f"{canal['nome_canal']} (ERRO: {e})")

print(f"\n  Canais COM dados históricos (últimos 7 dias): {len(canais_com_historico)}")
for nome, n, v7, v30, subs, data in canais_com_historico:
    print(f"    📊 {nome}: {n} registros | Views 7d: {v7:,} | Views 30d: {v30:,} | Subs: {subs:,} | Último: {data}")

print(f"\n  Canais SEM dados históricos (últimos 7 dias): {len(canais_sem_historico)}")
for nome in canais_sem_historico:
    print(f"    🔴 {nome}")

# ─────────────────────────────────────────────────────────────
# 7. CANAIS COM views_7d = 0 ou NULL (possível problema)
# ─────────────────────────────────────────────────────────────
print("\n\n🔍 7. CANAIS COM MÉTRICAS ZERADAS OU SUSPEITAS")
print("-" * 60)

canais_zerados = []
for nome, n, v7, v30, subs, data in canais_com_historico:
    if v7 == 0 and v30 == 0:
        canais_zerados.append((nome, subs, data))
    elif v7 == 0 and v30 > 0:
        canais_zerados.append((nome, f"views_7d=0 mas views_30d={v30:,}", data))

if canais_zerados:
    for item in canais_zerados:
        print(f"  ⚠️  {item[0]} → {item[1]} (último dado: {item[2]})")
else:
    print("  ✅ Nenhum canal com métricas zeradas suspeitas!")

# ─────────────────────────────────────────────────────────────
# 8. COLETA OAUTH (yt_collection_logs) - últimos 7 dias
# ─────────────────────────────────────────────────────────────
print("\n\n🔑 8. LOGS DE COLETA OAUTH (yt_collection_logs) - últimos 7 dias")
print("-" * 60)

try:
    resp_oauth = sb.table("yt_collection_logs")\
        .select("channel_id, status, message, created_at")\
        .eq("status", "error")\
        .gte("created_at", seven_days_ago)\
        .order("created_at", desc=True)\
        .limit(50)\
        .execute()

    if resp_oauth.data:
        # Agrupar por channel_id
        erros_por_canal = {}
        for log in resp_oauth.data:
            ch = log.get("channel_id", "?")
            if ch not in erros_por_canal:
                erros_por_canal[ch] = []
            erros_por_canal[ch].append({
                "msg": log.get("message", "?"),
                "date": log.get("created_at", "?")[:19]
            })

        print(f"  Total erros OAuth: {len(resp_oauth.data)} em {len(erros_por_canal)} canais")
        for ch_id, erros in sorted(erros_por_canal.items(), key=lambda x: len(x[1]), reverse=True):
            # Tentar mapear channel_id para nome via url_canal
            nome = ch_id
            for c in canais_nosso:
                url = c.get("url_canal", "")
                if ch_id in url:
                    nome = c["nome_canal"]
                    break
            print(f"\n  🔴 {nome} ({len(erros)} erros)")
            for e in erros[:3]:
                print(f"     {e['date']} → {e['msg'][:100]}")
            if len(erros) > 3:
                print(f"     ... e mais {len(erros) - 3} erros")
    else:
        print("  ✅ Nenhum erro OAuth nos últimos 7 dias!")
except Exception as e:
    print(f"  Tabela yt_collection_logs não encontrada ou erro: {e}")

# ─────────────────────────────────────────────────────────────
# 9. COMPARAÇÃO: canais_monitorados vs dados_canais_historico
# ─────────────────────────────────────────────────────────────
print("\n\n🔄 9. CONSISTÊNCIA: Canal existe mas NUNCA teve dados coletados?")
print("-" * 60)

for canal in canais_nosso:
    try:
        resp_ever = sb.table("dados_canais_historico")\
            .select("id")\
            .eq("canal_id", canal["id"])\
            .limit(1)\
            .execute()

        if not resp_ever.data:
            print(f"  🔴 {canal['nome_canal']} (id={canal['id']}) → NUNCA teve dados coletados!")
            print(f"     URL: {canal.get('url_canal', 'N/A')}")
            print(f"     Último erro: {canal.get('coleta_ultimo_erro', 'N/A')}")
    except Exception as e:
        print(f"  ERRO consultando canal {canal['nome_canal']}: {e}")

# ─────────────────────────────────────────────────────────────
# 10. RESUMO FINAL
# ─────────────────────────────────────────────────────────────
print("\n\n" + "=" * 80)
print("  RESUMO FINAL")
print("=" * 80)
print(f"  Total canais nosso ativos:       {len(canais_nosso)}")
print(f"  Com falhas consecutivas:         {len(canais_com_falhas)}")
print(f"  Desatualizados (>3 dias):        {len(canais_desatualizados)}")
print(f"  Sem vídeos (7 dias):             {len(canais_sem_videos)}")
print(f"  Sem dados históricos (7 dias):   {len(canais_sem_historico)}")
print(f"  Com métricas zeradas:            {len(canais_zerados)}")
print("=" * 80)
