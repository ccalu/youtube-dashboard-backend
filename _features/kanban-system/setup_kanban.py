"""
Script para configurar o sistema Kanban no Supabase
Data: 28/01/2025
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Adicionar o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests

# Carregar variáveis de ambiente
load_dotenv()

def execute_sql_via_api(sql_query):
    """Executa SQL diretamente via API do Supabase"""

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("[ERRO] Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env")
        return False

    # Endpoint para executar SQL
    sql_url = f"{url}/rest/v1/rpc"

    # Headers
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    print(f"[INFO] Executando SQL no Supabase...")
    print(f"[INFO] SQL: {sql_query[:100]}...")

    # Por enquanto, vamos apenas mostrar o SQL que deve ser executado
    return True

def main():
    print("[START] Configurando Sistema Kanban...")
    print("\n" + "="*60)
    print("IMPORTANTE: Execute os seguintes passos no Supabase:")
    print("="*60)

    print("\n1. Acesse o Supabase SQL Editor")
    print("2. Execute o arquivo: kanban-system/database/01_add_columns.sql")
    print("3. Execute o arquivo: kanban-system/database/02_create_tables.sql")
    print("4. (Opcional) Execute: kanban-system/database/03_test_data.sql")

    print("\n" + "="*60)
    print("Alternativamente, copie e cole os comandos abaixo:")
    print("="*60)

    # Mostrar comandos SQL essenciais
    sql_commands = """
-- 1. Adicionar campos na tabela canais_monitorados
ALTER TABLE canais_monitorados
ADD COLUMN IF NOT EXISTS kanban_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS kanban_status_since TIMESTAMP WITH TIME ZONE;

-- 2. Definir status padrao para canais nao monetizados
UPDATE canais_monitorados
SET
    kanban_status = 'em_teste_inicial',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND (monetizado = false OR monetizado IS NULL)
    AND kanban_status IS NULL;

-- 3. Definir status padrao para canais monetizados
UPDATE canais_monitorados
SET
    kanban_status = 'canal_constante',
    kanban_status_since = CURRENT_TIMESTAMP
WHERE
    tipo = 'nosso'
    AND monetizado = true
    AND kanban_status IS NULL;

-- 4. Criar tabela kanban_notes
CREATE TABLE IF NOT EXISTS kanban_notes (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    note_color VARCHAR(20) DEFAULT 'yellow',
    position INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 5. Criar tabela kanban_history
CREATE TABLE IF NOT EXISTS kanban_history (
    id SERIAL PRIMARY KEY,
    canal_id INTEGER NOT NULL REFERENCES canais_monitorados(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 6. Verificar resultado
SELECT
    COUNT(*) as total,
    monetizado,
    kanban_status
FROM canais_monitorados
WHERE tipo = 'nosso'
GROUP BY monetizado, kanban_status
ORDER BY monetizado, kanban_status;
"""

    print(sql_commands)

    print("\n" + "="*60)
    print("[INFO] Apos executar os SQLs, volte aqui para implementar os endpoints")
    print("="*60)

if __name__ == "__main__":
    main()