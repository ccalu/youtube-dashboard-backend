"""
Lista canais candidatos a Leva 3: tem OAuth configurado E tem <1000 inscritos.

Cruza:
- canais_monitorados (tipo=nosso, ativo)
- yt_channels (mapeia nome_canal -> channel_id)
- yt_oauth_tokens (channel_id tem token)
- dados_canais_historico (inscritos mais recentes por canal_id interno)
"""
import os
import sys
import io
from dotenv import load_dotenv

# Forçar UTF-8 no stdout (Windows console default e cp1252)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SupabaseClient

THRESHOLD = 1000

db = SupabaseClient()

# 1. Canais nossos ativos
nossos = db.supabase.table("canais_monitorados").select(
    "id, nome_canal, subnicho, lingua"
).eq("tipo", "nosso").eq("status", "ativo").execute().data or []

# 2. yt_channels (nome -> channel_id)
yt = db.supabase.table("yt_channels").select(
    "channel_id, channel_name"
).eq("is_active", True).execute().data or []
yt_name_to_id = {c["channel_name"]: c["channel_id"] for c in yt}

# 3. OAuth tokens
oauth = db.supabase.table("yt_oauth_tokens").select("channel_id").execute().data or []
oauth_ids = {r["channel_id"] for r in oauth}

# 4. Pra cada canal nosso com OAuth, buscar inscritos mais recentes
com_oauth = []
for c in nossos:
    nome = c["nome_canal"]
    ch_id = yt_name_to_id.get(nome)
    if not ch_id or ch_id not in oauth_ids:
        continue
    com_oauth.append(c)

print(f"Total canais com OAuth: {len(com_oauth)}")

# 5. Pra cada canal com oauth, buscar inscritos mais recentes
candidatos = []
for c in com_oauth:
    canal_id_int = c["id"]
    hist = db.supabase.table("dados_canais_historico").select(
        "inscritos, data_coleta"
    ).eq("canal_id", canal_id_int).order("data_coleta", desc=True).limit(1).execute()
    if not hist.data:
        inscritos = None
    else:
        inscritos = hist.data[0].get("inscritos")

    c["inscritos"] = inscritos
    if inscritos is not None and inscritos < THRESHOLD:
        candidatos.append(c)

# 6. Print resultado
print(f"\nCandidatos Leva 3 (OAuth + <{THRESHOLD} inscritos): {len(candidatos)}\n")
print(f"{'Canal':<35} {'Subnicho':<25} {'Lingua':<12} {'Inscritos':>10}")
print("-" * 90)
for c in sorted(candidatos, key=lambda x: (x.get("subnicho") or "", x["nome_canal"])):
    nome = (c["nome_canal"] or "")[:34]
    sub = (c.get("subnicho") or "")[:24]
    lin = (c.get("lingua") or "")[:11]
    ins = c.get("inscritos")
    print(f"{nome:<35} {sub:<25} {lin:<12} {ins:>10}")

# 7. Tambem mostrar canais com OAuth mas SEM dados de inscritos (caso relevante)
sem_dados = [c for c in com_oauth if c.get("inscritos") is None]
if sem_dados:
    print(f"\n[AVISO] {len(sem_dados)} canais com OAuth mas SEM dados de inscritos:")
    for c in sem_dados:
        print(f"  - {c['nome_canal']} ({c.get('subnicho','?')})")
