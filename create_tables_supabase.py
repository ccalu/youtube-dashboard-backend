"""
Cria tabelas financeiras direto no Supabase via SQL
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Lê o SQL do arquivo
with open('create_financial_tables.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Conecta ao Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("=" * 60)
print("CRIANDO TABELAS FINANCEIRAS NO SUPABASE")
print("=" * 60)

# Divide o SQL em statements individuais
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

total = len(statements)
sucesso = 0
erros = 0

for i, statement in enumerate(statements, 1):
    if not statement:
        continue

    print(f"\n[{i}/{total}] Executando statement...")

    # Identifica o tipo de statement
    if 'CREATE TABLE' in statement.upper():
        table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split()[-1]
        print(f"  → Criando tabela: {table_name}")
    elif 'CREATE INDEX' in statement.upper():
        index_name = statement.split('CREATE INDEX')[1].split('ON')[0].strip().split()[-1]
        print(f"  → Criando índice: {index_name}")
    elif 'CREATE TRIGGER' in statement.upper():
        trigger_name = statement.split('CREATE TRIGGER')[1].split('BEFORE')[0].strip()
        print(f"  → Criando trigger: {trigger_name}")
    elif 'CREATE OR REPLACE FUNCTION' in statement.upper():
        print(f"  → Criando função...")
    elif 'COMMENT ON' in statement.upper():
        print(f"  → Adicionando comentário...")

    try:
        # Executa via RPC (Supabase não tem endpoint SQL direto na client lib)
        # Vamos usar psycopg2 se disponível
        result = supabase.rpc('exec_sql', {'query': statement + ';'}).execute()
        print(f"  ✓ Sucesso")
        sucesso += 1
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
            print(f"  ⚠ Já existe (ignorado)")
            sucesso += 1
        else:
            print(f"  ✗ Erro: {error_msg}")
            erros += 1

print("\n" + "=" * 60)
print("RESULTADO")
print("=" * 60)
print(f"Total: {total} statements")
print(f"Sucesso: {sucesso}")
print(f"Erros: {erros}")
print("=" * 60)
