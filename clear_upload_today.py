# -*- coding: utf-8 -*-
"""
Script para limpar o registro de upload de hoje
Para permitir novo teste
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

# Carrega variáveis
load_dotenv()

# Usa SERVICE_ROLE_KEY para bypass RLS
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

channel_id = "UCiMgKMWsYH8a8EFp94TClIQ"
today = date.today().isoformat()

print(f"Limpando registro de upload de hoje ({today}) para canal {channel_id}...")

# Deleta registro de hoje
result = supabase.table('yt_canal_upload_diario')\
    .delete()\
    .eq('channel_id', channel_id)\
    .eq('data', today)\
    .execute()

if result.data:
    print(f"[OK] Registro deletado: {len(result.data)} registro(s)")
else:
    print("[!] Nenhum registro encontrado para deletar")

# Também limpa da fila de upload se tiver algo marcado como completed hoje
result = supabase.table('yt_upload_queue')\
    .delete()\
    .eq('channel_id', channel_id)\
    .eq('status', 'retry')\
    .execute()

if result.data:
    print(f"[OK] Limpou {len(result.data)} item(s) da fila com status 'retry'")

print("\nPronto! Agora pode testar novamente.")