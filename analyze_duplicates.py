# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, date
from supabase import create_client
from collections import defaultdict

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERRO: SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configurados")
    sys.exit(1)

supabase = create_client(url, key)

# Data de hoje
today = date.today().isoformat()
print(f"Analisando uploads de: {today}\n")

# 1. Buscar TODOS registros do dia na tabela upload_diario
print("Buscando registros em yt_canal_upload_diario...")
try:
    response = supabase.table("yt_canal_upload_diario").select("*").eq("data", today).execute()
    uploads_diarios = response.data
    print(f"   OK: {len(uploads_diarios)} registros encontrados\n")
except Exception as e:
    print(f"   ERRO ao buscar: {e}")
    sys.exit(1)

# 2. Agrupar por channel_id para detectar duplicados
canais_dict = defaultdict(list)
for record in uploads_diarios:
    canais_dict[record['channel_id']].append(record)

# 3. Identificar duplicados
duplicados = {ch_id: records for ch_id, records in canais_dict.items() if len(records) > 1}

if duplicados:
    print(f"DUPLICADOS ENCONTRADOS: {len(duplicados)} canais com multiplos registros\n")
    print("=" * 100)
    
    for channel_id, records in duplicados.items():
        print(f"\nCanal: {records[0].get('nome_canal', 'N/A')} (ID: {channel_id})")
        print(f"   Total de registros duplicados: {len(records)}")
        print("-" * 100)
        
        for i, rec in enumerate(records, 1):
            print(f"\n   Registro #{i}:")
            print(f"   - ID do registro: {rec['id']}")
            print(f"   - Status: {rec.get('status', 'N/A')}")
            print(f"   - Video ID: {rec.get('video_id', 'NULL')}")
            print(f"   - Playlist ID: {rec.get('playlist_id', 'NULL')}")
            print(f"   - Titulo: {rec.get('titulo_video', 'N/A')[:60]}...")
            print(f"   - Criado em: {rec.get('created_at', 'N/A')}")
            print(f"   - Atualizado em: {rec.get('updated_at', 'N/A')}")
            
            # Verificar se tem dados completos
            has_video_id = rec.get('video_id') is not None and rec.get('video_id') != ''
            has_playlist_id = rec.get('playlist_id') is not None and rec.get('playlist_id') != ''
            
            if has_video_id and has_playlist_id:
                print(f"   OK COMPLETO (tem video_id e playlist_id)")
            elif has_video_id:
                print(f"   PARCIAL (tem video_id, falta playlist_id)")
            else:
                print(f"   INCOMPLETO (falta video_id)")
        
        print("-" * 100)
else:
    print("OK: Nenhum duplicado encontrado!\n")

# 4. Buscar registros no histórico
print("\n" + "=" * 100)
print("Buscando registros em yt_canal_upload_historico (hoje)...\n")
try:
    response = supabase.table("yt_canal_upload_historico").select("*").eq("data_upload", today).execute()
    historico = response.data
    print(f"   OK: {len(historico)} registros no historico\n")
    
    # Agrupar histórico por canal
    historico_dict = defaultdict(list)
    for h in historico:
        historico_dict[h['channel_id']].append(h)
    
    # Mostrar canais com múltiplos registros no histórico
    hist_duplicados = {ch_id: records for ch_id, records in historico_dict.items() if len(records) > 1}
    
    if hist_duplicados:
        print(f"HISTORICO: {len(hist_duplicados)} canais com multiplos registros\n")
        for channel_id, records in hist_duplicados.items():
            print(f"   Canal ID: {channel_id}")
            print(f"   Total no historico: {len(records)}")
            for rec in records:
                print(f"      - {rec.get('status', 'N/A')} | Video ID: {rec.get('video_id', 'NULL')} | {rec.get('created_at', 'N/A')}")
            print()
    
except Exception as e:
    print(f"   ERRO ao buscar historico: {e}")

# 5. SUGESTÕES DE LIMPEZA
if duplicados:
    print("\n" + "=" * 100)
    print("SUGESTOES DE LIMPEZA:\n")
    
    for channel_id, records in duplicados.items():
        # Ordenar por created_at (mais recente primeiro)
        records_sorted = sorted(records, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Identificar qual manter (com video_id) e quais deletar
        completo = None
        incompletos = []
        
        for rec in records_sorted:
            if rec.get('video_id') and rec.get('video_id') != '':
                if not completo:
                    completo = rec
                else:
                    incompletos.append(rec)  # Duplicado mesmo tendo video_id
            else:
                incompletos.append(rec)
        
        print(f"\n{records_sorted[0].get('nome_canal', 'N/A')} (ID: {channel_id})")
        
        if completo:
            print(f"   MANTER: ID {completo['id']} (tem video_id: {completo.get('video_id')})")
        else:
            print(f"   PROBLEMA: Nenhum registro com video_id completo!")
            print(f"   Sugestao: Manter o mais recente (ID {records_sorted[0]['id']})")
        
        if incompletos:
            print(f"   DELETAR ({len(incompletos)} registros):")
            for inc in incompletos:
                reason = "sem video_id" if not inc.get('video_id') else "duplicado desnecessario"
                print(f"      - ID {inc['id']} ({reason})")

print("\n" + "=" * 100)
print("Analise completa!")
