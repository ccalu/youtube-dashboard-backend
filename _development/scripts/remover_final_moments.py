# -*- coding: utf-8 -*-
"""
Script para remover o canal Final Moments (ID 369) do sistema
Data: 03/02/2026
"""

import sys
import io
import os

# Fix para encoding no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SupabaseClient
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def remover_canal_final_moments():
    """Remove o canal Final Moments (ID 369) e todos os seus dados relacionados"""

    print("="*60)
    print("REMOVENDO CANAL: Final Moments")
    print("="*60)

    # ID do canal a ser removido
    CANAL_ID = 369
    CANAL_NOME = "Final Moments"

    # Inicializar cliente Supabase
    db = SupabaseClient()

    # 1. Verificar se o canal existe
    print(f"\n[1] Verificando canal ID {CANAL_ID}...")
    try:
        response = db.supabase.table('canais_monitorados')\
            .select('id, nome_canal, tipo, subnicho, url_canal')\
            .eq('id', CANAL_ID)\
            .execute()

        if not response.data:
            print(f"   [ERRO] Canal ID {CANAL_ID} não encontrado!")
            return

        canal = response.data[0]
        print(f"   [OK] Encontrado: {canal['nome_canal']}")
        print(f"        Tipo: {canal.get('tipo', 'N/A')}")
        print(f"        Subnicho: {canal.get('subnicho', 'N/A')}")
        print(f"        URL: {canal.get('url_canal', 'N/A')}")

        # Confirmar remoção
        print(f"\n   CONFIRMA REMOVER '{canal['nome_canal']}'? (s/n): ", end='')
        confirmacao = input().strip().lower()
        if confirmacao != 's':
            print("   [CANCELADO] Operação cancelada pelo usuário")
            return

    except Exception as e:
        print(f"   [ERRO] Falha ao verificar canal: {str(e)}")
        return

    # Contadores
    total_deletados = {
        'notificacoes': 0,
        'kanban': 0,
        'comentarios': 0,
        'videos_historico': 0,
        'dados_canais_historico': 0
    }

    # 2. Deletar notificações
    print(f"\n[2] Deletando notificações...")
    try:
        response = db.supabase.table('notificacoes')\
            .delete()\
            .eq('canal_id', CANAL_ID)\
            .execute()
        total_deletados['notificacoes'] = len(response.data) if response.data else 0
        print(f"   [OK] {total_deletados['notificacoes']} notificações deletadas")
    except Exception as e:
        print(f"   [AVISO] Erro ao deletar notificações: {str(e)[:100]}")

    # 3. Deletar notas Kanban
    print(f"\n[3] Deletando notas Kanban...")
    try:
        response = db.supabase.table('canal_kanban_notes')\
            .delete()\
            .eq('canal_id', CANAL_ID)\
            .execute()
        total_deletados['kanban'] = len(response.data) if response.data else 0
        print(f"   [OK] {total_deletados['kanban']} notas Kanban deletadas")
    except Exception as e:
        print(f"   [AVISO] Erro ao deletar notas Kanban: {str(e)[:100]}")

    # 4. Deletar comentários de vídeos
    print(f"\n[4] Deletando comentários...")
    try:
        response = db.supabase.table('video_comments')\
            .delete()\
            .eq('canal_id', CANAL_ID)\
            .execute()
        total_deletados['comentarios'] = len(response.data) if response.data else 0
        print(f"   [OK] {total_deletados['comentarios']} comentários deletados")
    except Exception as e:
        print(f"   [AVISO] Erro ao deletar comentários: {str(e)[:100]}")

    # 5. Deletar histórico de vídeos
    print(f"\n[5] Deletando histórico de vídeos...")
    try:
        # Deletar todos de uma vez
        response = db.supabase.table('videos_historico')\
            .delete()\
            .eq('canal_id', CANAL_ID)\
            .execute()

        total_deletados['videos_historico'] = len(response.data) if response.data else 0
        print(f"   [OK] {total_deletados['videos_historico']} registros de vídeos deletados")
    except Exception as e:
        print(f"   [ERRO] Falha ao deletar histórico de vídeos: {str(e)[:100]}")

    # 6. Deletar histórico do canal
    print(f"\n[6] Deletando histórico do canal...")
    try:
        response = db.supabase.table('dados_canais_historico')\
            .delete()\
            .eq('canal_id', CANAL_ID)\
            .execute()
        total_deletados['dados_canais_historico'] = len(response.data) if response.data else 0
        print(f"   [OK] {total_deletados['dados_canais_historico']} registros de histórico deletados")
    except Exception as e:
        print(f"   [ERRO] Falha ao deletar histórico do canal: {str(e)[:100]}")

    # 7. Deletar o canal principal
    print(f"\n[7] Deletando canal principal...")
    try:
        response = db.supabase.table('canais_monitorados')\
            .delete()\
            .eq('id', CANAL_ID)\
            .execute()

        if response.data:
            print(f"   [OK] Canal '{CANAL_NOME}' (ID {CANAL_ID}) removido com sucesso!")
        else:
            print(f"   [ERRO] Falha ao remover canal principal")
            # Tentar desativar como fallback
            print("   Tentando desativar canal...")
            response = db.supabase.table('canais_monitorados')\
                .update({'ativo': False})\
                .eq('id', CANAL_ID)\
                .execute()
            if response.data:
                print(f"   [OK] Canal desativado como fallback")
    except Exception as e:
        print(f"   [ERRO] Falha ao deletar canal: {str(e)}")

    # 8. Verificação final
    print(f"\n[8] Verificação final...")
    try:
        response = db.supabase.table('canais_monitorados')\
            .select('id')\
            .eq('id', CANAL_ID)\
            .execute()

        if not response.data:
            print(f"   [SUCESSO] Canal não existe mais no banco!")
        else:
            print(f"   [AVISO] Canal ainda existe (pode estar desativado)")
    except Exception as e:
        print(f"   [ERRO] Falha na verificação: {str(e)}")

    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DA REMOÇÃO")
    print("="*60)
    print(f"Canal: {CANAL_NOME} (ID {CANAL_ID})")
    print(f"Notificações deletadas: {total_deletados['notificacoes']}")
    print(f"Notas Kanban deletadas: {total_deletados['kanban']}")
    print(f"Comentários deletados: {total_deletados['comentarios']}")
    print(f"Vídeos histórico deletados: {total_deletados['videos_historico']}")
    print(f"Dados canal histórico deletados: {total_deletados['dados_canais_historico']}")
    print(f"Total de registros removidos: {sum(total_deletados.values())}")
    print("="*60)

if __name__ == "__main__":
    remover_canal_final_moments()