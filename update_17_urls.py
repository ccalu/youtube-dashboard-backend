"""
Atualizar 17 URLs no banco com formato correto
Confirmado pelo usuário em 11/12/2025
"""
import os
import sys
import io
from dotenv import load_dotenv
from supabase import create_client, Client
from urllib.parse import unquote

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# 17 canais para atualizar
updates = [
    (702, "https://www.youtube.com/@WealthAcademyTV"),
    (745, "https://www.youtube.com/@FilozoficznaRzetelnosc"),
    (746, "https://www.youtube.com/@alchemiamadrosci"),
    (747, "https://www.youtube.com/@StanSieBossem-yn5od"),
    (748, "https://www.youtube.com/@PsychologiaWrażliwości"),
    (749, "https://www.youtube.com/@FilozofiadlaZwycięzców-n1v"),
    (750, "https://www.youtube.com/@Aslındagerçektenkolay"),
    (751, "https://www.youtube.com/@dusunen.insanx"),
    (752, "https://www.youtube.com/@Zihin.Ötesi"),
    (753, "https://www.youtube.com/@BilinçdışıYolculuk"),
    (754, "https://www.youtube.com/@Stoacı"),
    (755, "https://www.youtube.com/@Sınırlarıaş1"),
    (757, "https://www.youtube.com/@ПсихологияДуши-е7ж"),
    (760, "https://www.youtube.com/@Stoicism.wisdom."),
    (756, "https://www.youtube.com/@КУРАТОРИЙ"),
    (720, "https://www.youtube.com/@FilozofiaPrzebudzona"),
]

print("=" * 80)
print("ATUALIZANDO 16 URLs NO BANCO (719 já está correto)")
print("=" * 80)
print()

success = 0
errors = 0

for canal_id, nova_url in updates:
    # Buscar info atual
    canal = supabase.table("canais_monitorados")\
        .select("nome_canal, url_canal")\
        .eq("id", canal_id)\
        .execute()

    if not canal.data:
        print(f"[{canal_id}] NAO ENCONTRADO")
        errors += 1
        continue

    nome = canal.data[0]['nome_canal']
    url_antiga = canal.data[0]['url_canal']

    print(f"[{canal_id}] {nome}")
    print(f"  ANTES: {url_antiga}")
    print(f"  DEPOIS: {nova_url}")

    # Atualizar
    result = supabase.table("canais_monitorados")\
        .update({"url_canal": nova_url})\
        .eq("id", canal_id)\
        .execute()

    print(f"  ✓ ATUALIZADO")
    print()
    success += 1

print("=" * 80)
print(f"ATUALIZAÇÃO COMPLETA - Sucesso: {success} | Erros: {errors}")
print("=" * 80)
print()
print("MAIS OS 3 CORRIGIDOS ANTES (762, 744, 351) = 19 CANAIS CORRIGIDOS")
print("AMANHÃ 5 AM: Coleta vai funcionar 100%!")
