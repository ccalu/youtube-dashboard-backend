"""
Backfill: escreve nas planilhas de Shorts as producoes que ficaram sem sheets_row_num
por causa do bug do service-account missing.

Passos por producao:
  1. Le producao do Supabase (canal, subnicho, tom, formato, video_ref, titulo, producao_json)
  2. Extrai script/descricao/prompts do producao_json
  3. Chama write_production_to_sheet -> retorna row_num
  4. Atualiza sheets_row_num no Supabase
  5. Se ja tem drive_link ou youtube_video_id, tambem popula esses campos na planilha
"""
import io, sys, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from database import SupabaseClient
from _features.shorts_production.sheets_writer import write_production_to_sheet, update_drive_link

db = SupabaseClient()

# 1. Pegar producoes SEM sheets_row_num (qualquer idade)
# IMPORTANTE: selecionar AMBOS drive_link (path local) e drive_url (URL Drive).
# A coluna "Link Drive" da planilha PRECISA usar drive_url — bug anterior usou drive_link
# (path local) e resultou em paths literais aparecendo na planilha.
prods = db.supabase.table("shorts_production").select(
    "id, canal, subnicho, lingua, titulo, tom, formato, video_ref, producao_json, drive_link, drive_url, youtube_video_id, created_at, status"
).is_("sheets_row_num", "null").order("created_at", desc=False).execute().data or []

print(f"{len(prods)} producoes sem sheets_row_num encontradas\n")

if not prods:
    print("Nada pra fazer.")
    sys.exit(0)

success = []
failures = []

for i, p in enumerate(prods):
    pid = p["id"]
    canal = p.get("canal", "")
    subnicho = p.get("subnicho", "")
    try:
        titulo_safe = (p.get("titulo") or "").encode('ascii', 'replace').decode()[:50]
    except Exception:
        titulo_safe = "?"

    pj = p.get("producao_json") or {}
    cenas = pj.get("cenas", [])
    prompts_img = "\n".join(c.get("prompt_imagem", "") for c in cenas)
    prompts_anim = "\n".join(c.get("prompt_animacao", "") for c in cenas)

    # Formatar data a partir do created_at (YYYY-MM-DD -> DD/MM/YYYY)
    created = p.get("created_at", "")
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        data_fmt = dt.strftime("%d/%m/%Y")
    except Exception:
        data_fmt = datetime.utcnow().strftime("%d/%m/%Y")

    row_data = {
        "data": data_fmt,
        "tom": p.get("tom") or "-",
        "titulo": p.get("titulo", ""),
        "descricao": pj.get("descricao", ""),
        "script": pj.get("script", ""),
        "prompts_imagem": prompts_img,
        "prompts_animacao": prompts_anim,
        "formato": p.get("formato", "livre"),
        "video_ref": p.get("video_ref", "") or "",
    }

    print(f"[{i+1}/{len(prods)}] ID {pid} | {canal[:25]:<25} | {titulo_safe}")

    try:
        row_num = write_production_to_sheet(canal, subnicho, row_data)
        if row_num <= 0:
            raise RuntimeError(f"row_num retornou {row_num}")

        # Atualizar sheets_row_num no Supabase
        db.supabase.table("shorts_production").update({
            "sheets_row_num": row_num,
        }).eq("id", pid).execute()

        print(f"   OK linha {row_num}")

        # Se ja tem drive_url (URL Drive, nao path local!), atualizar na planilha.
        # drive_link == path local (C:\...) — NUNCA usar pra coluna Link Drive.
        drive_url = p.get("drive_url") or ""
        if drive_url.startswith("http"):
            try:
                update_drive_link(canal, subnicho, row_num, drive_url)
                print(f"   + drive_url aplicado")
            except Exception as e:
                print(f"   ! drive_url falhou: {str(e)[:80]}")

        success.append(pid)

        # Dar uma respirada pra nao estourar rate limit do Sheets
        time.sleep(0.5)

    except Exception as e:
        msg = str(e)[:200]
        print(f"   FAIL: {msg}")
        failures.append((pid, msg))

# Resumo
print(f"\n{'='*70}")
print(f"RESULTADO:")
print(f"  OK:    {len(success)}/{len(prods)}")
print(f"  FAIL:  {len(failures)}/{len(prods)}")
if failures:
    print(f"\nFalhas:")
    for pid, msg in failures:
        print(f"  [{pid}] {msg}")
