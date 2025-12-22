"""
Script para corrigir tipos de colunas de retenção via Supabase SQL API
"""
import requests
import json

# Configurações Supabase
SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

print("=" * 60)
print("CORRIGINDO TIPOS DE COLUNAS DE RETENÇÃO")
print("=" * 60)

# Instruções para o usuário
print("\nPROBLEMA IDENTIFICADO:")
print("-" * 40)
print("As colunas de retenção foram criadas como INTEGER ao invés de FLOAT.")
print("Isso está causando erro ao salvar valores decimais como 45.3% ou 312.5 segundos.")

print("\n\nSOLUÇÃO - Execute este SQL no Supabase:")
print("-" * 40)
print("""
1. Acesse o Supabase Dashboard:
   https://supabase.com/dashboard/project/prvkmzstyedepvlbppyo

2. Vá em 'SQL Editor' no menu lateral

3. Cole e execute este comando SQL:

-- CORRIGIR TIPOS DE COLUNAS PARA FLOAT
ALTER TABLE yt_daily_metrics
ALTER COLUMN avg_view_duration_sec TYPE FLOAT8 USING avg_view_duration_sec::float8,
ALTER COLUMN avg_retention_pct TYPE FLOAT8 USING avg_retention_pct::float8,
ALTER COLUMN ctr_approx TYPE FLOAT8 USING ctr_approx::float8;

-- VERIFICAR SE FOI CORRIGIDO
SELECT
    column_name,
    data_type
FROM
    information_schema.columns
WHERE
    table_name = 'yt_daily_metrics'
    AND column_name IN ('avg_view_duration_sec', 'avg_retention_pct', 'ctr_approx');
""")

print("-" * 40)
print("\n4. Após executar, você deve ver:")
print("   avg_retention_pct      | double precision")
print("   avg_view_duration_sec  | double precision")
print("   ctr_approx             | double precision")

print("\n\nALTERNATIVA (se preferir recriar as colunas):")
print("-" * 40)
print("""
-- DELETAR COLUNAS ANTIGAS
ALTER TABLE yt_daily_metrics
DROP COLUMN IF EXISTS avg_view_duration_sec,
DROP COLUMN IF EXISTS avg_retention_pct,
DROP COLUMN IF EXISTS ctr_approx;

-- RECRIAR COM TIPO CORRETO
ALTER TABLE yt_daily_metrics
ADD COLUMN avg_view_duration_sec FLOAT8,
ADD COLUMN avg_retention_pct FLOAT8,
ADD COLUMN ctr_approx FLOAT8;
""")

print("\n" + "=" * 60)
print("Após corrigir, execute: python monetization_dashboard/coleta_diaria.py")
print("=" * 60)