# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, date

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Carregar .env manualmente
env_path = r"D:\ContentFactory\youtube-dashboard-backend\.env"
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from supabase import create_client
from collections import defaultdict

# Configurar Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERRO: Credenciais nao encontradas")
    sys.exit(1)

supabase = create_client(url, key)

# Data de hoje
today = date.today().isoformat()
print(f"Analisando uploads de: {today}\n")

# 1. Buscar TODOS registros do dia
print("Buscando registros em yt_canal_upload_diario...")
try:
    response = supabase.table("yt_canal_upload_diario").select("*").eq("data", today).execute()
    uploads_diarios = response.data
    print(f"   OK: {len(uploads_diarios)} registros encontrados\n")
except Exception as e:
    print(f"   ERRO: {e}")
    sys.exit(1)

# 2. Agrupar por channel_id
canais_dict = defaultdict(list)
for record in uploads_diarios:
    canais_dict[record['channel_id']].append(record)

# 3. Identificar duplicados
duplicados = {ch_id: records for ch_id, records in canais_dict.items() if len(records) > 1}

if duplicados:
    print(f"DUPLICADOS ENCONTRADOS: {len(duplicados)} canais\n")
    print("=" * 100)
    
    for channel_id, records in duplicados.items():
        print(f"\nCanal: {records[0].get('nome_canal', 'N/A')}")
        print(f"Channel ID: {channel_id}")
        print(f"Total duplicados: {len(records)}")
        print("-" * 100)
        
        for i, rec in enumerate(records, 1):
            print(f"\n   [{i}] ID registro: {rec['id']}")
            print(f"       Status: {rec.get('status', 'N/A')}")
            print(f"       Video ID: {rec.get('video_id', 'NULL')}")
            print(f"       Playlist ID: {rec.get('playlist_id', 'NULL')}")
            titulo = rec.get('titulo_video', 'N/A')
            if titulo and len(titulo) > 60:
                titulo = titulo[:60] + "..."
            print(f"       Titulo: {titulo}")
            print(f"       Criado: {rec.get('created_at', 'N/A')}")
            print(f"       Atualizado: {rec.get('updated_at', 'N/A')}")
            
            has_video = rec.get('video_id') not in [None, '', 'NULL']
            has_playlist = rec.get('playlist_id') not in [None, '', 'NULL']
            
            if has_video and has_playlist:
                print(f"       >>> COMPLETO")
            elif has_video:
                print(f"       >>> PARCIAL (sem playlist)")
            else:
                print(f"       >>> INCOMPLETO (sem video_id)")
        
        print("-" * 100)
else:
    print("OK: Nenhum duplicado!\n")

# 4. Historico
print("\n" + "=" * 100)
print("Buscando historico (hoje)...\n")
try:
    response = supabase.table("yt_canal_upload_historico").select("*").eq("data_upload", today).execute()
    historico = response.data
    print(f"   OK: {len(historico)} registros no historico\n")
    
    historico_dict = defaultdict(list)
    for h in historico:
        historico_dict[h['channel_id']].append(h)
    
    hist_dup = {ch_id: recs for ch_id, recs in historico_dict.items() if len(recs) > 1}
    
    if hist_dup:
        print(f"Historico com duplicados: {len(hist_dup)} canais\n")
        for ch_id, recs in hist_dup.items():
            print(f"   Canal: {ch_id} ({len(recs)} registros)")
            for r in recs:
                print(f"      {r.get('status')} | Video: {r.get('video_id', 'NULL')} | {r.get('created_at')}")
    
except Exception as e:
    print(f"   ERRO: {e}")

# 5. Sugestoes
if duplicados:
    print("\n" + "=" * 100)
    print("SUGESTOES DE LIMPEZA:\n")
    
    for ch_id, recs in duplicados.items():
        recs_sorted = sorted(recs, key=lambda x: x.get('created_at', ''), reverse=True)
        
        completo = None
        deletar = []
        
        for r in recs_sorted:
            if r.get('video_id') and r.get('video_id') not in ['', 'NULL']:
                if not completo:
                    completo = r
                else:
                    deletar.append(r)
            else:
                deletar.append(r)
        
        print(f"\n{recs_sorted[0].get('nome_canal', 'N/A')} ({ch_id})")
        
        if completo:
            print(f"   MANTER: {completo['id']} (video: {completo.get('video_id')})")
        else:
            print(f"   PROBLEMA: Nenhum com video_id!")
            print(f"   Sugestao: Manter mais recente ({recs_sorted[0]['id']})")
        
        if deletar:
            print(f"   DELETAR ({len(deletar)}):")
            for d in deletar:
                motivo = "sem video_id" if not d.get('video_id') else "duplicado"
                print(f"      - {d['id']} ({motivo})")

print("\n" + "=" * 100)
print("Fim da analise!")
