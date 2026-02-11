# -*- coding: utf-8 -*-
import os, sys
from datetime import date
from collections import defaultdict

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

env_path = r"D:\ContentFactory\youtube-dashboard-backend\.env"
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERRO: Credenciais nao encontradas")
    sys.exit(1)

supabase = create_client(url, key)
today = date.today().isoformat()

print("=" * 100)
print(f"ANALISE DE DUPLICADOS - {today}")
print("=" * 100)

# Buscar registros
response = supabase.table("yt_canal_upload_diario").select("*").eq("data", today).execute()
diario = response.data
print(f"
Total registros hoje: {len(diario)}")

# Agrupar por channel_id
canais_dict = defaultdict(list)
for r in diario:
    canais_dict[r["channel_id"]].append(r)

duplicados = {ch: recs for ch, recs in canais_dict.items() if len(recs) > 1}

if duplicados:
    print(f"
DUPLICADOS: {len(duplicados)} canais
")
    print("=" * 100)
    
    for ch_id, recs in duplicados.items():
        print(f"
CANAL: {recs[0].get("nome_canal", "N/A")}")
        print(f"Channel ID: {ch_id}")
        print(f"Total: {len(recs)} registros
")
        
        for i, r in enumerate(sorted(recs, key=lambda x: x.get("created_at", "")), 1):
            print(f"  [{i}] ID: {r["id"]}")
            print(f"      Status: {r.get("status", "N/A")}")
            print(f"      Video ID: {r.get("video_id", "NULL")}")
            print(f"      Playlist ID: {r.get("playlist_id", "NULL")}")
            print(f"      Titulo: {r.get("titulo_video", "N/A")[:60]}")
            print(f"      Criado: {r.get("created_at", "N/A")}")
            
            has_video = r.get("video_id") not in [None, "", "NULL"]
            has_playlist = r.get("playlist_id") not in [None, "", "NULL"]
            
            if has_video and has_playlist:
                print(f"      >>> COMPLETO")
            elif has_video:
                print(f"      >>> PARCIAL (sem playlist)")
            else:
                print(f"      >>> INCOMPLETO (sem video_id)")
            print()
        
        print("-" * 100)
else:
    print("
OK: Nenhum duplicado\!")

# Historico
print("
" + "=" * 100)
print("HISTORICO")
response = supabase.table("yt_canal_upload_historico").select("*").eq("data", today).execute()
historico = response.data
print(f"Total no historico hoje: {len(historico)}")

hist_dict = defaultdict(list)
for h in historico:
    hist_dict[h["channel_id"]].append(h)

mult = {ch: recs for ch, recs in hist_dict.items() if len(recs) > 1}

if mult:
    print(f"
Multiplos uploads: {len(mult)} canais
")
    for ch_id, recs in mult.items():
        print(f"  {recs[0].get("channel_name", "N/A")}: {len(recs)} uploads")
        for r in sorted(recs, key=lambda x: x.get("created_at", "")):
            tent = r.get("tentativa_numero", "?")
            tent_txt = "MANUAL" if tent == 99 else f"tent.{tent}"
            print(f"    - {tent_txt:8} | {r.get("status", "N/A"):10} | {r.get("youtube_video_id", "NULL"):15}")

# Sugestoes
if duplicados:
    print("
" + "=" * 100)
    print("SUGESTOES DE LIMPEZA
")
    
    for ch_id, recs in duplicados.items():
        recs_sorted = sorted(recs, key=lambda x: x.get("created_at", ""), reverse=True)
        
        completo = None
        for r in recs_sorted:
            if r.get("video_id") and r.get("video_id") not in ["", "NULL"]:
                if not completo:
                    completo = r
                    break
        
        manter = completo or recs_sorted[0]
        deletar = [r for r in recs_sorted if r["id"] \!= manter["id"]]
        
        print(f"{recs_sorted[0].get("nome_canal", "N/A")} ({ch_id})")
        print(f"  MANTER: ID {manter["id"]}")
        if deletar:
            print(f"  DELETAR: {len(deletar)} registro(s): {[r["id"] for r in deletar]}")
        print()

print("=" * 100)
print("FIM")
