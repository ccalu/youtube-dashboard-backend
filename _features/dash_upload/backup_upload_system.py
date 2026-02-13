#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backup completo do sistema de upload
Salva ambas as tabelas e código do dashboard em JSON com timestamp
Permite restauração se necessário
"""

import os
import json
import shutil
from datetime import datetime, timezone
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configurar cliente Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Usar service role para bypass RLS
)

def criar_backup():
    """Cria backup completo do sistema de upload"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"_runtime/backups/upload_system_{timestamp}"

    # Criar diretórios
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(f"{backup_dir}/tabelas", exist_ok=True)
    os.makedirs(f"{backup_dir}/codigo", exist_ok=True)

    print(f"[BACKUP] BACKUP COMPLETO DO SISTEMA DE UPLOAD")
    print(f"[INFO] Pasta: {backup_dir}")
    print(f"[INFO] Timestamp: {timestamp}\n")

    # ========== BACKUP DAS TABELAS ==========
    print("[TABELAS] BACKUP DAS TABELAS SUPABASE")
    print("-" * 40)

    # 1. Backup tabela diária
    print("\n[1/2] Backup: yt_canal_upload_diario...")
    try:
        # Buscar TODOS os registros (sem limite)
        all_diario = []
        offset = 0
        limit = 1000

        while True:
            result = supabase.table('yt_canal_upload_diario')\
                .select('*')\
                .range(offset, offset + limit - 1)\
                .order('id')\
                .execute()

            if not result.data:
                break

            all_diario.extend(result.data)
            offset += limit

            if len(result.data) < limit:
                break

        # Salvar em JSON
        with open(f"{backup_dir}/tabelas/yt_canal_upload_diario.json", 'w', encoding='utf-8') as f:
            json.dump(all_diario, f, indent=2, ensure_ascii=False, default=str)

        print(f"   [OK] {len(all_diario)} registros salvos")

    except Exception as e:
        print(f"   [ERRO]Erro: {e}")

    # 2. Backup tabela histórico
    print("\n[2/2]Backup: yt_canal_upload_historico...")
    try:
        # Buscar TODOS os registros (sem limite)
        all_historico = []
        offset = 0
        limit = 1000

        while True:
            result = supabase.table('yt_canal_upload_historico')\
                .select('*')\
                .range(offset, offset + limit - 1)\
                .order('id')\
                .execute()

            if not result.data:
                break

            all_historico.extend(result.data)
            offset += limit

            if len(result.data) < limit:
                break

        # Salvar em JSON
        with open(f"{backup_dir}/tabelas/yt_canal_upload_historico.json", 'w', encoding='utf-8') as f:
            json.dump(all_historico, f, indent=2, ensure_ascii=False, default=str)

        print(f"   [OK]{len(all_historico)} registros salvos")

    except Exception as e:
        print(f"   [ERRO]Erro: {e}")

    # ========== BACKUP DO CÓDIGO ==========
    print("\n[CODIGO]BACKUP DO CÓDIGO")
    print("-" * 40)

    arquivos_backup = [
        'dash_upload_final.py',
        'daily_uploader.py',
        'forcar_upload_manual_fixed.py',
        'migrate_historico.py'
    ]

    for arquivo in arquivos_backup:
        if os.path.exists(arquivo):
            try:
                shutil.copy2(arquivo, f"{backup_dir}/codigo/{arquivo}")
                print(f"   [OK]{arquivo}")
            except Exception as e:
                print(f"   [ERRO]{arquivo}: {e}")
        else:
            print(f"   [AVISO]{arquivo} não encontrado")

    # ========== SALVAR METADADOS ==========
    print("\n[INFO]SALVANDO METADADOS")
    print("-" * 40)

    metadados = {
        'timestamp': timestamp,
        'data_hora': datetime.now().isoformat(),
        'total_diario': len(all_diario) if 'all_diario' in locals() else 0,
        'total_historico': len(all_historico) if 'all_historico' in locals() else 0,
        'arquivos_backup': arquivos_backup,
        'supabase_url': os.getenv("SUPABASE_URL"),
        'versao': '1.0',
        'motivo': 'Backup antes de corrigir sistema de múltiplos uploads'
    }

    with open(f"{backup_dir}/metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadados, f, indent=2, ensure_ascii=False)

    print(f"   [OK]Metadados salvos")

    # ========== RESUMO FINAL ==========
    print("\n" + "=" * 50)
    print("[OK]BACKUP COMPLETO REALIZADO COM SUCESSO!")
    print("=" * 50)
    print(f"[PASTA]Localização: {backup_dir}")
    print(f"[TABELA]Total tabela diária: {metadados['total_diario']} registros")
    print(f"[TABELA]Total tabela histórico: {metadados['total_historico']} registros")
    print(f"[CODIGO]Arquivos de código: {len(arquivos_backup)}")
    print("\n[AVISO]IMPORTANTE: Guarde o nome da pasta do backup!")
    print(f"   Para restaurar: python backup_upload_system.py restaurar {backup_dir}")

    return backup_dir

def restaurar_backup(backup_dir):
    """Restaura backup se necessário"""

    print(f"[RESTAURAR]RESTAURANDO BACKUP")
    print(f"[PASTA]Pasta: {backup_dir}\n")

    if not os.path.exists(backup_dir):
        print(f"❌ Erro: Pasta de backup não encontrada: {backup_dir}")
        return False

    # Ler metadados
    try:
        with open(f"{backup_dir}/metadata.json", 'r', encoding='utf-8') as f:
            metadados = json.load(f)

        print(f"[INFO]Backup de: {metadados['data_hora']}")
        print(f"   Total diário: {metadados['total_diario']}")
        print(f"   Total histórico: {metadados['total_historico']}\n")

    except Exception as e:
        print(f"❌ Erro ao ler metadados: {e}")
        return False

    resposta = input("[AVISO]ATENÇÃO: Isso vai SOBRESCREVER os dados atuais. Continuar? (s/n): ")
    if resposta.lower() != 's':
        print("❌ Restauração cancelada")
        return False

    # ========== RESTAURAR TABELAS ==========
    print("\n[TABELA]RESTAURANDO TABELAS")
    print("-" * 40)

    # 1. Restaurar tabela diária
    print("\n[1/2]Restaurando: yt_canal_upload_diario...")
    try:
        with open(f"{backup_dir}/tabelas/yt_canal_upload_diario.json", 'r', encoding='utf-8') as f:
            data_diario = json.load(f)

        # Limpar tabela atual
        print("   Limpando tabela atual...")
        supabase.table('yt_canal_upload_diario').delete().neq('id', 0).execute()

        # Inserir dados do backup
        print(f"   Inserindo {len(data_diario)} registros...")
        for registro in data_diario:
            registro.pop('id', None)  # Remove ID para evitar conflito
            try:
                supabase.table('yt_canal_upload_diario')\
                    .insert(registro)\
                    .execute()
            except Exception as e:
                print(f"   [AVISO]Erro no registro: {e}")

        print(f"   [OK]Tabela restaurada")

    except Exception as e:
        print(f"   [ERRO]Erro: {e}")

    # 2. Restaurar tabela histórico
    print("\n[2/2]Restaurando: yt_canal_upload_historico...")
    try:
        with open(f"{backup_dir}/tabelas/yt_canal_upload_historico.json", 'r', encoding='utf-8') as f:
            data_historico = json.load(f)

        # Limpar tabela atual
        print("   Limpando tabela atual...")
        supabase.table('yt_canal_upload_historico').delete().neq('id', 0).execute()

        # Inserir dados do backup
        print(f"   Inserindo {len(data_historico)} registros...")
        for registro in data_historico:
            registro.pop('id', None)
            try:
                supabase.table('yt_canal_upload_historico')\
                    .insert(registro)\
                    .execute()
            except Exception as e:
                print(f"   [AVISO]Erro no registro: {e}")

        print(f"   [OK]Tabela restaurada")

    except Exception as e:
        print(f"   [ERRO]Erro: {e}")

    # ========== RESTAURAR CÓDIGO ==========
    print("\n[CODIGO]RESTAURANDO CÓDIGO")
    print("-" * 40)

    for arquivo in metadados.get('arquivos_backup', []):
        origem = f"{backup_dir}/codigo/{arquivo}"
        if os.path.exists(origem):
            try:
                shutil.copy2(origem, arquivo)
                print(f"   [OK]{arquivo}")
            except Exception as e:
                print(f"   [ERRO]{arquivo}: {e}")

    print("\n" + "=" * 50)
    print("[OK]RESTAURAÇÃO COMPLETA!")
    print("=" * 50)

    return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'restaurar':
        if len(sys.argv) < 3:
            print("❌ Uso: python backup_upload_system.py restaurar <pasta_backup>")
            print("   Exemplo: python backup_upload_system.py restaurar _runtime/backups/upload_system_20260211_123456")
            sys.exit(1)
        restaurar_backup(sys.argv[2])
    else:
        criar_backup()