#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para forçar refresh da MV sem timeout
Data: 28/01/2026

Solução alternativa que não depende do RPC com timeout
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client
import time

# Configurar encoding UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def main():
    print("=" * 60)
    print("FORÇANDO REFRESH DA MV - SOLUÇÃO ALTERNATIVA")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

    # Conectar ao Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Verificar situação atual
    print("[1] VERIFICANDO SITUAÇÃO ATUAL...")

    hoje = datetime.now(timezone.utc).date()
    ontem = hoje - timedelta(days=1)

    # Contar registros de dados
    result_hoje = supabase.table('dados_canais_historico').select(
        'id', count='exact'
    ).gte('data_coleta', hoje.isoformat() + 'T00:00:00'
    ).lte('data_coleta', hoje.isoformat() + 'T23:59:59').execute()

    result_ontem = supabase.table('dados_canais_historico').select(
        'id', count='exact'
    ).gte('data_coleta', ontem.isoformat() + 'T00:00:00'
    ).lte('data_coleta', ontem.isoformat() + 'T23:59:59').execute()

    print(f"   Dados de hoje: {result_hoje.count or 0} registros")
    print(f"   Dados de ontem: {result_ontem.count or 0} registros")

    if (result_hoje.count or 0) == 0 or (result_ontem.count or 0) == 0:
        print("\n[!] ERRO: Dados insuficientes para calcular inscritos_diff")
        print("   Execute uma coleta primeiro!")
        return

    # 2. SOLUÇÃO 1: Tentar criar função temporária para refresh
    print("\n[2] TENTANDO CRIAR FUNÇÃO TEMPORÁRIA...")

    sql_create_function = """
    CREATE OR REPLACE FUNCTION refresh_mv_forcado()
    RETURNS json
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET statement_timeout = '300s'
    AS $$
    BEGIN
        -- Aumenta timeout apenas para esta função
        SET LOCAL statement_timeout = '300s';

        -- Faz o refresh
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;

        RETURN json_build_object(
            'success', true,
            'refreshed_at', clock_timestamp()
        );
    EXCEPTION WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', SQLERRM
        );
    END;
    $$;
    """

    try:
        # Tentar executar via RPC (se houver uma função de execução SQL)
        result = supabase.rpc('execute_sql', {'query': sql_create_function}).execute()
        print("   [OK] Função criada com sucesso")

        # Agora executar a função
        print("\n[3] EXECUTANDO REFRESH COM TIMEOUT AUMENTADO...")
        result = supabase.rpc('refresh_mv_forcado').execute()
        if result.data:
            print(f"   [OK] Refresh executado: {result.data}")
        else:
            print("   [!] Função executada mas sem retorno")

    except Exception as e:
        error_msg = str(e)
        if "not exist" in error_msg or "undefined" in error_msg:
            print("   [!] Não foi possível criar função (sem permissão ou função execute_sql não existe)")
        else:
            print(f"   [!] Erro: {error_msg[:100]}")

    # 3. SOLUÇÃO 2: Forçar recálculo manual dos dados
    print("\n[4] CALCULANDO inscritos_diff MANUALMENTE...")

    # Buscar todos os canais ativos
    canais_result = supabase.table('canais_monitorados').select(
        'id, nome_canal'
    ).eq('status', 'ativo').execute()

    canais = canais_result.data or []
    print(f"   Total de canais: {len(canais)}")

    # Buscar dados de hoje e ontem
    print("   Buscando dados históricos...")

    # Dados de hoje
    hoje_result = supabase.table('dados_canais_historico').select(
        'canal_id, inscritos'
    ).gte('data_coleta', hoje.isoformat() + 'T00:00:00'
    ).lte('data_coleta', hoje.isoformat() + 'T23:59:59').execute()

    # Dados de ontem
    ontem_result = supabase.table('dados_canais_historico').select(
        'canal_id, inscritos'
    ).gte('data_coleta', ontem.isoformat() + 'T00:00:00'
    ).lte('data_coleta', ontem.isoformat() + 'T23:59:59').execute()

    # Criar dicionários
    hoje_dict = {row['canal_id']: row['inscritos'] for row in (hoje_result.data or [])}
    ontem_dict = {row['canal_id']: row['inscritos'] for row in (ontem_result.data or [])}

    # Calcular diferenças
    canais_com_diff = 0
    exemplos = []

    for canal in canais:
        canal_id = canal['id']
        if canal_id in hoje_dict and canal_id in ontem_dict:
            diff = hoje_dict[canal_id] - ontem_dict[canal_id]
            if diff != 0:
                canais_com_diff += 1
                if len(exemplos) < 5:
                    exemplos.append({
                        'nome': canal['nome_canal'],
                        'diff': diff
                    })

    print(f"\n   Canais com diferença calculada: {canais_com_diff}")
    if exemplos:
        print("\n   Exemplos:")
        for ex in exemplos:
            sinal = "+" if ex['diff'] > 0 else ""
            print(f"      - {ex['nome']}: {sinal}{ex['diff']} inscritos")

    # 4. SOLUÇÃO 3: Atualizar tabela temporária para API usar
    print("\n[5] CRIANDO TABELA TEMPORÁRIA COM DADOS CALCULADOS...")

    try:
        # Criar tabela se não existir
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS temp_inscritos_diff (
            canal_id INTEGER PRIMARY KEY,
            inscritos_diff INTEGER,
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """

        # Limpar tabela existente
        supabase.table('temp_inscritos_diff').delete().neq('canal_id', -1).execute()

        # Inserir dados calculados
        batch = []
        for canal_id in hoje_dict:
            if canal_id in ontem_dict:
                diff = hoje_dict[canal_id] - ontem_dict[canal_id]
                batch.append({
                    'canal_id': canal_id,
                    'inscritos_diff': diff,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })

                if len(batch) >= 100:
                    supabase.table('temp_inscritos_diff').insert(batch).execute()
                    batch = []

        if batch:
            supabase.table('temp_inscritos_diff').insert(batch).execute()

        print(f"   [OK] Tabela temporária criada com {len(hoje_dict)} registros")

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            print("   [!] Tabela temp_inscritos_diff não existe. Criar manualmente no Supabase:")
            print("""
   CREATE TABLE temp_inscritos_diff (
       canal_id INTEGER PRIMARY KEY,
       inscritos_diff INTEGER,
       updated_at TIMESTAMP DEFAULT NOW()
   );
            """)
        else:
            print(f"   [!] Erro ao criar tabela temporária: {error_msg[:100]}")

    # 5. Verificar resultado final
    print("\n[6] VERIFICANDO RESULTADO...")

    # Testar a API
    try:
        import requests
        response = requests.get('http://localhost:8000/api/canais?limit=10')

        if response.status_code == 200:
            data = response.json()
            canais_com_diff_api = [c for c in data['canais'] if c.get('inscritos_diff') is not None]

            print(f"   API retornou {len(data['canais'])} canais")
            print(f"   Canais com inscritos_diff: {len(canais_com_diff_api)}")

            if canais_com_diff_api:
                print("\n   Exemplos da API:")
                for c in canais_com_diff_api[:3]:
                    print(f"      - {c['nome_canal']}: {c['inscritos_diff']} diff")

    except Exception as e:
        print(f"   [!] Não foi possível testar API: {str(e)[:50]}")

    print("\n" + "=" * 60)
    print("RESUMO:")
    print("=" * 60)
    print(f"✓ Dados disponíveis: {result_hoje.count} (hoje) / {result_ontem.count} (ontem)")
    print(f"✓ Canais com diferença real: {canais_com_diff}")
    print("\nPRÓXIMOS PASSOS:")
    print("1. Se a MV ainda não funciona, execute no Supabase SQL Editor:")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;")
    print("\n2. Ou use a tabela temporária temp_inscritos_diff")
    print("\n3. Ou modifique database.py para sempre calcular on-the-fly")
    print("=" * 60)

if __name__ == "__main__":
    main()