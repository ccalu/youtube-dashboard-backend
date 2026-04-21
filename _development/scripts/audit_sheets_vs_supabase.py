"""
Compara producoes recentes no Supabase com o que esta nas planilhas de Shorts.
Mostra quais producoes ficaram FORA da planilha (devido ao erro do SA file).
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SupabaseClient
from _features.shorts_production.analyst import _get_sheets_service, SPREADSHEET_IDS, _find_tab_name, _sheets_execute

db = SupabaseClient()
sheets = _get_sheets_service()

# 1. Pegar as ultimas 30 producoes do Supabase
prods = db.supabase.table("shorts_production").select(
    "id, canal, subnicho, titulo, status, created_at, sheets_row_num, youtube_video_id, drive_link"
).order("created_at", desc=True).limit(30).execute().data or []

print(f"{len(prods)} producoes recentes no Supabase:\n")
print(f"{'ID':<6} {'Canal':<25} {'Subnicho':<22} {'Status':<9} {'Sheets?':<9} {'YT?':<5} {'Titulo':<40}")
print("-" * 130)

# Agrupar por (subnicho, canal) pra cruzar com sheets
by_key = {}
for p in prods:
    key = (p.get("subnicho", ""), p.get("canal", ""))
    by_key.setdefault(key, []).append(p)
    sheets_ok = p.get("sheets_row_num") is not None
    yt_ok = p.get("youtube_video_id") is not None
    print(f"{p['id']:<6} {(p.get('canal') or '')[:24]:<25} {(p.get('subnicho') or '')[:21]:<22} {(p.get('status') or ''):<9} {'SIM' if sheets_ok else '--NAO--':<9} {'SIM' if yt_ok else '--':<5} {(p.get('titulo') or '')[:39]:<40}")

# 2. Contar quantas NAO tem sheets_row_num
sem_sheets = [p for p in prods if not p.get("sheets_row_num")]
print(f"\n{'='*70}")
print(f"RESUMO:")
print(f"  Total producoes recentes: {len(prods)}")
print(f"  COM sheets_row_num (planilha OK):   {len(prods) - len(sem_sheets)}")
print(f"  SEM sheets_row_num (faltando planilha): {len(sem_sheets)}")

if sem_sheets:
    print(f"\n{'='*70}")
    print(f"Producoes sem registro na planilha (precisam retroativa):")
    for p in sem_sheets[:15]:
        created = (p.get("created_at") or "")[:19]
        print(f"  [{p['id']}] {created} {p.get('canal','')[:25]} | {p.get('titulo','')[:50]}")

# 3. Verificar as ultimas linhas de 1-2 planilhas pra ter certeza
print(f"\n{'='*70}")
print(f"Ultimas linhas nas planilhas (sample):")
for subnicho in ["Reis Perversos", "Relatos de Guerra"]:
    sid = SPREADSHEET_IDS.get(subnicho)
    if not sid: continue
    try:
        # Pegar todas as abas
        ss = _sheets_execute(sheets.spreadsheets().get(spreadsheetId=sid))
        tabs_names = [s['properties']['title'] for s in ss['sheets']]
        print(f"\n  [{subnicho}] abas: {tabs_names[:6]}...")
        # Pra cada aba, ultima linha
        for tab in tabs_names[:3]:
            try:
                vals = _sheets_execute(sheets.spreadsheets().values().get(
                    spreadsheetId=sid, range=f"'{tab}'!A:C"
                ))
                rows = vals.get("values", [])
                last = rows[-1] if len(rows) > 1 else []
                print(f"    {tab}: {len(rows)-1} linhas (sem header) | ultima: {last[:3] if last else 'vazia'}")
            except Exception as e:
                print(f"    {tab}: ERRO {str(e)[:60]}")
    except Exception as e:
        print(f"  [{subnicho}] ERRO: {str(e)[:100]}")
