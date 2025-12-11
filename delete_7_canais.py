"""
Script para deletar 7 canais inativos do banco
Executado em 11/12/2025
"""
import os
import sys
import io
from dotenv import load_dotenv
from supabase import create_client, Client

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# IDs para deletar
canais_deletar = [265, 275, 12, 412, 664, 673, 165]

print("=" * 80)
print("DELETANDO 7 CANAIS INATIVOS")
print("=" * 80)
print()

# Buscar info antes de deletar (para log)
for canal_id in canais_deletar:
    canal = supabase.table("canais_monitorados")\
        .select("id, nome_canal, url_canal")\
        .eq("id", canal_id)\
        .execute()

    if canal.data:
        info = canal.data[0]
        print(f"[{info['id']}] {info['nome_canal']}")
        print(f"     URL: {info['url_canal']}")

        # Deletar notificacoes (foreign key)
        notif_result = supabase.table("notificacoes")\
            .delete()\
            .eq("canal_id", canal_id)\
            .execute()

        print(f"     Notificacoes: {len(notif_result.data) if notif_result.data else 0} registros deletados")

        # Deletar historico primeiro (foreign key)
        hist_result = supabase.table("dados_canais_historico")\
            .delete()\
            .eq("canal_id", canal_id)\
            .execute()

        print(f"     Historico dados: {len(hist_result.data) if hist_result.data else 0} registros deletados")

        # Deletar videos_historico (foreign key)
        videos_result = supabase.table("videos_historico")\
            .delete()\
            .eq("canal_id", canal_id)\
            .execute()

        print(f"     Historico videos: {len(videos_result.data) if videos_result.data else 0} registros deletados")

        # Deletar canal
        canal_result = supabase.table("canais_monitorados")\
            .delete()\
            .eq("id", canal_id)\
            .execute()

        print(f"     Status: DELETADO ✓")
    else:
        print(f"[{canal_id}] NAO ENCONTRADO (ja foi deletado?)")

    print()

print("=" * 80)
print("DELECAO COMPLETA")
print("=" * 80)
