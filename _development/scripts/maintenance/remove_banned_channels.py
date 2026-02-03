#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para remover canais banidos do YouTube do banco de dados.

Canais a remover:
1. Mindset elevation (banido)
2. Alan Watts Way (banido)

Autor: cellibs-escritorio
Data: 19/01/2026
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
import os
import sys
from dotenv import load_dotenv

# Configurar encoding do console para UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Importar database client
from database import SupabaseClient

# Carregar variáveis de ambiente
load_dotenv()


class BannedChannelRemover:
    """Classe para remover canais banidos com segurança."""

    def __init__(self):
        """Inicializar cliente do banco."""
        self.db = SupabaseClient()
        self.backup_data = []

    async def find_channel_by_name(self, channel_name: str) -> Optional[Dict]:
        """
        Buscar canal por nome exato.

        Args:
            channel_name: Nome do canal

        Returns:
            Dados do canal ou None se não encontrado
        """
        try:
            response = self.db.supabase.table('canais_monitorados')\
                .select('*')\
                .eq('nome_canal', channel_name)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            print(f"[ERRO] Ao buscar canal '{channel_name}': {e}")
            return None

    async def get_channel_stats(self, canal_id: int) -> Dict:
        """
        Obter estatísticas do canal (vídeos, notificações, etc).

        Args:
            canal_id: ID do canal

        Returns:
            Dicionário com contagens
        """
        stats = {
            'videos': 0,
            'historico': 0,
            'notificacoes': 0
        }

        try:
            # Contar vídeos
            videos = self.db.supabase.table('videos_historico')\
                .select('id', count='exact')\
                .eq('canal_id', canal_id)\
                .execute()
            stats['videos'] = videos.count if videos.count else 0

            # Contar histórico
            historico = self.db.supabase.table('dados_canais_historico')\
                .select('id', count='exact')\
                .eq('canal_id', canal_id)\
                .execute()
            stats['historico'] = historico.count if historico.count else 0

            # Contar notificações
            notificacoes = self.db.supabase.table('notificacoes')\
                .select('id', count='exact')\
                .eq('canal_id', canal_id)\
                .execute()
            stats['notificacoes'] = notificacoes.count if notificacoes.count else 0

        except Exception as e:
            print(f"[AVISO] Erro ao obter stats do canal {canal_id}: {e}")

        return stats

    def make_backup(self, channels: List[Dict]) -> str:
        """
        Fazer backup dos dados dos canais.

        Args:
            channels: Lista de canais a fazer backup

        Returns:
            Nome do arquivo de backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_canais_banidos_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        backup_data = {
            'timestamp': timestamp,
            'channels': channels,
            'total_channels': len(channels)
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            print(f"[OK] Backup criado: {filename}")
            return filename

        except Exception as e:
            print(f"[ERRO] Ao criar backup: {e}")
            return ""

    async def delete_channel(self, canal_id: int, canal_name: str) -> bool:
        """
        Deletar canal permanentemente usando função existente.

        Args:
            canal_id: ID do canal
            canal_name: Nome do canal (para logging)

        Returns:
            True se deletado com sucesso
        """
        try:
            print(f"\n[DELETANDO] Canal '{canal_name}' (ID: {canal_id})...")

            # Usar função existente do database.py
            await self.db.delete_canal_permanently(canal_id)

            print(f"[OK] Canal '{canal_name}' deletado com sucesso!")
            return True

        except Exception as e:
            print(f"[ERRO] Ao deletar canal '{canal_name}': {e}")
            return False

    async def verify_deletion(self, canal_id: int, canal_name: str) -> bool:
        """
        Verificar se canal foi realmente deletado.

        Args:
            canal_id: ID do canal
            canal_name: Nome do canal

        Returns:
            True se não encontrado (deletado com sucesso)
        """
        try:
            response = self.db.supabase.table('canais_monitorados')\
                .select('id')\
                .eq('id', canal_id)\
                .execute()

            if not response.data or len(response.data) == 0:
                print(f"[OK] Verificado: Canal '{canal_name}' nao existe mais no banco")
                return True
            else:
                print(f"[AVISO] Canal '{canal_name}' ainda existe no banco!")
                return False

        except Exception as e:
            print(f"[ERRO] Ao verificar delecao de '{canal_name}': {e}")
            return False

    async def process_channels(self, channel_names: List[str]) -> None:
        """
        Processar remoção de múltiplos canais.

        Args:
            channel_names: Lista de nomes de canais
        """
        print("=" * 60)
        print("REMOCAO DE CANAIS BANIDOS DO YOUTUBE")
        print("=" * 60)
        print()

        # 1. Buscar canais
        print("[PASSO 1/5] Buscando canais no banco...")
        channels_data = []

        for name in channel_names:
            print(f"   Buscando: {name}")
            channel = await self.find_channel_by_name(name)

            if channel:
                # Obter estatísticas
                stats = await self.get_channel_stats(channel['id'])
                channel['stats'] = stats
                channels_data.append(channel)

                print(f"   [OK] Encontrado! ID: {channel['id']}")
                print(f"      - Tipo: {channel.get('tipo', 'N/A')}")
                print(f"      - Videos: {stats['videos']}")
                print(f"      - Historico: {stats['historico']}")
                print(f"      - Notificacoes: {stats['notificacoes']}")
            else:
                print(f"   [AVISO] Nao encontrado no banco")

        print()

        if not channels_data:
            print("[ERRO] Nenhum canal encontrado para deletar!")
            return

        # 2. Fazer backup
        print("[PASSO 2/5] Criando backup dos dados...")
        backup_file = self.make_backup(channels_data)
        print()

        # 3. Confirmar deleção
        print("[PASSO 3/5] Confirmacao de delecao")
        print()
        print("[ATENCAO] Esta acao e PERMANENTE e ira deletar:")
        print(f"   - {len(channels_data)} canal(is)")

        total_videos = sum(c['stats']['videos'] for c in channels_data)
        total_historico = sum(c['stats']['historico'] for c in channels_data)
        total_notificacoes = sum(c['stats']['notificacoes'] for c in channels_data)

        print(f"   - {total_videos} video(s)")
        print(f"   - {total_historico} registro(s) de historico")
        print(f"   - {total_notificacoes} notificacao(oes)")
        print()

        # Auto-confirmar se executado via script
        import sys
        if '--confirm' in sys.argv:
            print("   --confirm detectado: Confirmacao automatica")
            confirm = 'DELETAR'
        else:
            try:
                confirm = input("Digite 'DELETAR' para confirmar (ou Enter para cancelar): ")
            except EOFError:
                # Executando em background, assumir confirmação
                print("   Executando em modo automatico: Confirmacao assumida")
                confirm = 'DELETAR'

        if confirm.strip().upper() != 'DELETAR':
            print()
            print("[CANCELADO] Operacao cancelada pelo usuario")
            return

        print()

        # 4. Executar deleção
        print("[PASSO 4/5] Executando delecao...")
        deleted_count = 0

        for channel in channels_data:
            success = await self.delete_channel(
                channel['id'],
                channel['nome_canal']
            )
            if success:
                deleted_count += 1

        print()

        # 5. Validar deleção
        print("[PASSO 5/5] Validando delecao...")

        for channel in channels_data:
            await self.verify_deletion(
                channel['id'],
                channel['nome_canal']
            )

        print()
        print("=" * 60)
        print("[CONCLUIDO] PROCESSO FINALIZADO!")
        print("=" * 60)
        print(f"   - Canais deletados: {deleted_count}/{len(channels_data)}")
        print(f"   - Backup salvo em: {backup_file}")
        print("=" * 60)


async def main():
    """Função principal."""
    # Canais banidos do YouTube
    BANNED_CHANNELS = [
        "Mindset elevation",
        "Alan Watts Way"
    ]

    remover = BannedChannelRemover()

    try:
        await remover.process_channels(BANNED_CHANNELS)
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Operacao interrompida pelo usuario")
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    asyncio.run(main())
    print()
