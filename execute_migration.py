"""
Script para executar migration SQL no Supabase PostgreSQL
Usa psycopg2 para conexão direta ao database
"""
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# Tentar importar psycopg2
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("[AVISO] psycopg2 nao esta instalado. Tentando metodo alternativo...")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://prvkmzstyedepvlbppyo.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Extrair project ref do URL
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

# Connection string do Supabase
# Formato: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

if HAS_PSYCOPG2 and SUPABASE_DB_PASSWORD:
    print("=" * 70)
    print("EXECUTANDO MIGRATION VIA PSYCOPG2")
    print("=" * 70)

    conn_string = f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"

    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Ler migration SQL
        with open('migrations/add_monetization_fields.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        print("\n[INFO] Executando migration SQL...")
        cursor.execute(sql)
        conn.commit()

        print("[OK] Migration executada com sucesso!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERRO] Erro ao executar migration: {e}")
        exit(1)

else:
    # Método alternativo: usar Supabase Client com RPC
    print("=" * 70)
    print("EXECUTANDO MIGRATION VIA SUPABASE CLIENT")
    print("=" * 70)

    from database import SupabaseClient

    db = SupabaseClient()

    print("\n[AVISO] O Supabase REST API nao permite executar DDL (ALTER TABLE) diretamente.")
    print("Tentando executar via SQL direto...")
    print()

    # Tentar executar SQL statements individuais
    print("Tentando executar migration via comandos SQL...")

    try:
        # Criar função que executa a migration
        create_function_sql = """
        CREATE OR REPLACE FUNCTION execute_monetization_migration()
        RETURNS TEXT AS $$
        BEGIN
            -- Adicionar total_views
            ALTER TABLE dados_canais_historico
            ADD COLUMN IF NOT EXISTS total_views BIGINT;

            -- Adicionar is_estimate e analytics
            ALTER TABLE yt_daily_metrics
            ADD COLUMN IF NOT EXISTS is_estimate BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS avg_retention_pct DECIMAL(5,2),
            ADD COLUMN IF NOT EXISTS avg_view_duration_sec INTEGER,
            ADD COLUMN IF NOT EXISTS ctr_approx DECIMAL(5,2);

            -- Criar índices
            CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_estimate
            ON yt_daily_metrics(channel_id, is_estimate);

            CREATE INDEX IF NOT EXISTS idx_yt_daily_metrics_date_channel
            ON yt_daily_metrics(date DESC, channel_id);

            CREATE INDEX IF NOT EXISTS idx_dados_canais_historico_date
            ON dados_canais_historico(data_coleta DESC, canal_id);

            -- Marcar existentes como reais
            UPDATE yt_daily_metrics
            SET is_estimate = FALSE
            WHERE is_estimate IS NULL;

            RETURN 'Migration executada com sucesso!';
        END;
        $$ LANGUAGE plpgsql;
        """

        # Executar via RPC
        result = db.supabase.rpc('execute_monetization_migration').execute()
        print(f"[OK] {result.data}")

    except Exception as e:
        error_msg = str(e)

        if "does not exist" in error_msg or "permission denied" in error_msg:
            print(f"\n[ERRO] Nao foi possivel executar via RPC: {error_msg}")
            print("\n[INFO] Execute manualmente no Supabase Dashboard:")
            print("1. Acesse: https://supabase.com/dashboard")
            print(f"2. Projeto: {project_ref}")
            print("3. SQL Editor -> Cole migrations/add_monetization_fields.sql")
            print("4. Clique RUN")
        else:
            print(f"[ERRO] {e}")

        exit(1)

print("\n" + "=" * 70)
print("MIGRATION FINALIZADA")
print("=" * 70)
