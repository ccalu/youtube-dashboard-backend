"""
Script de limpeza 100% seguro - Remove apenas arquivos garantidamente desnecessários
Data: 2026-01-19
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def criar_backup(arquivos_para_backup):
    """Cria backup dos arquivos antes de deletar"""
    backup_dir = f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if arquivos_para_backup:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"\n[OK] Criando backup em: {backup_dir}/")

        for arquivo in arquivos_para_backup:
            if os.path.exists(arquivo):
                try:
                    # Criar estrutura de diretórios no backup
                    rel_path = os.path.dirname(arquivo)
                    if rel_path:
                        backup_subdir = os.path.join(backup_dir, rel_path)
                        os.makedirs(backup_subdir, exist_ok=True)

                    # Copiar arquivo ou diretório
                    if os.path.isdir(arquivo):
                        dest = os.path.join(backup_dir, arquivo)
                        shutil.copytree(arquivo, dest)
                        print(f"  [DIR] Backup: {arquivo}/")
                    else:
                        dest = os.path.join(backup_dir, arquivo)
                        shutil.copy2(arquivo, dest)
                        print(f"  [FILE] Backup: {arquivo}")
                except Exception as e:
                    print(f"  [!] Erro ao fazer backup de {arquivo}: {e}")

    return backup_dir

def limpar_arquivos_seguros():
    """Remove apenas arquivos 100% seguros para deletar"""

    print("=" * 60)
    print("LIMPEZA 100% SEGURA DO PROJETO")
    print("=" * 60)

    # Lista de arquivos 100% seguros para deletar
    arquivos_test = [
        "test_coleta_comentarios_integrada.py",
        "test_coleta_simples.py",
        "test_comment_system.py",
        "test_database_comments.py",
        "test_engagement_endpoint.py",
        "test_final_summary.py",
        "test_gpt_integration.py",
        "test_sistema_completo.py",
        "test_validacoes_tipo_nosso.py"
    ]

    arquivos_check = [
        "check_comments_status.py"
    ]

    arquivos_lovable = [
        "LOVABLE_COMPLETE_INSTRUCTIONS.md",
        "LOVABLE_ENGAGEMENT_TAB.md",
        "LOVABLE_PROMPT_COMPLETO.md",
        "INSTRUCOES_DEPLOY_LOVABLE.md",
        "PROMPT_LOVABLE_MODAL_ANALYTICS.md"
    ]

    # Encontrar todos os diretórios __pycache__
    pycache_dirs = []
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            pycache_dirs.append(pycache_path)

    # Combinar todas as listas
    todos_arquivos = arquivos_test + arquivos_check + arquivos_lovable

    # Filtrar apenas arquivos que existem
    arquivos_existentes = [f for f in todos_arquivos if os.path.exists(f)]
    diretorios_existentes = [d for d in pycache_dirs if os.path.exists(d)]

    total_para_deletar = len(arquivos_existentes) + len(diretorios_existentes)

    if total_para_deletar == 0:
        print("\n[OK] Nenhum arquivo para limpar - diretorio ja esta limpo!")
        return

    print(f"\n[INFO] Encontrados para limpeza:")
    print(f"  - {len([f for f in arquivos_test if os.path.exists(f)])} arquivos de teste")
    print(f"  - {len([f for f in arquivos_check if os.path.exists(f)])} arquivos de check")
    print(f"  - {len([f for f in arquivos_lovable if os.path.exists(f)])} documentos Lovable antigos")
    print(f"  - {len(diretorios_existentes)} diretorios __pycache__")
    print(f"\n  Total: {total_para_deletar} itens")

    # Confirmar antes de prosseguir
    resposta = input("\n[?] Deseja prosseguir com a limpeza? (s/n): ")
    if resposta.lower() != 's':
        print("[X] Limpeza cancelada.")
        return

    # Criar backup
    todos_para_backup = arquivos_existentes + diretorios_existentes
    backup_dir = criar_backup(todos_para_backup)

    # Deletar arquivos
    print("\n[DEL] Removendo arquivos...")

    deletados = 0
    erros = 0

    # Deletar arquivos individuais
    for arquivo in arquivos_existentes:
        try:
            os.remove(arquivo)
            print(f"  [OK] Removido: {arquivo}")
            deletados += 1
        except Exception as e:
            print(f"  [ERRO] Erro ao remover {arquivo}: {e}")
            erros += 1

    # Deletar diretórios __pycache__
    for diretorio in diretorios_existentes:
        try:
            shutil.rmtree(diretorio)
            print(f"  [OK] Removido: {diretorio}/")
            deletados += 1
        except Exception as e:
            print(f"  [ERRO] Erro ao remover {diretorio}: {e}")
            erros += 1

    # Resumo final
    print("\n" + "=" * 60)
    print("LIMPEZA CONCLUIDA!")
    print("=" * 60)
    print(f"[OK] Arquivos removidos: {deletados}")
    if erros > 0:
        print(f"[ERRO] Erros: {erros}")
    print(f"[BACKUP] Backup salvo em: {backup_dir}/")
    print("\n[SUCCESS] Seu projeto esta mais limpo e organizado!")

    # Listar o que NÃO foi tocado
    print("\n[INFO] Arquivos/pastas mantidos (nao tocados):")
    importantes = [
        "main.py",
        "collector.py",
        "database.py",
        "gpt_analyzer.py",
        "scripts-temp/",
        "monetization_dashboard/",
        "database/migrations/",
        ".env"
    ]
    for item in importantes[:5]:
        if os.path.exists(item):
            print(f"  [OK] {item}")
    print("  ... e todos os outros arquivos de producao")

if __name__ == "__main__":
    limpar_arquivos_seguros()