"""
Scanner automático de planilhas Google Sheets

Varre todas as planilhas dos canais ativos a cada X minutos,
detecta vídeos prontos para upload e adiciona na fila automaticamente.

Autor: Sistema automatizado
Data: 2025-12-27
"""

import logging
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
import os
import json
from google.oauth2 import service_account
import gspread
from supabase import create_client

logger = logging.getLogger(__name__)

class SpreadsheetScanner:
    """
    Scanner de planilhas Google Sheets para detecção automática de vídeos.

    Características:
    - Rate limiting (processa em batches)
    - Timeout por planilha (15s)
    - Circuit breaker (desliga após N erros)
    - Logs muito detalhados
    - Prevenção de duplicatas
    """

    def __init__(self):
        """Inicializa scanner com configurações"""

        # Configurações (via env vars ou padrão)
        self.batch_size = int(os.getenv("SCANNER_BATCH_SIZE", "2"))  # 2 para suporte 70+ canais
        self.timeout_per_sheet = int(os.getenv("SCANNER_TIMEOUT_SECONDS", "15"))
        self.max_errors = int(os.getenv("SCANNER_MAX_ERRORS", "3"))

        # Estado interno
        self.error_count = 0
        self.is_active = True

        # Conexões (lazy initialization)
        self._sheets_client = None
        self._supabase_client = None

        logger.info(f"📊 Scanner configurado:")
        logger.info(f"   Batch size: {self.batch_size} planilhas")
        logger.info(f"   Timeout: {self.timeout_per_sheet}s por planilha")
        logger.info(f"   Max errors: {self.max_errors}")

    @property
    def sheets_client(self):
        """Google Sheets client (singleton)"""
        if self._sheets_client is None:
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_2')
            if not creds_json:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS_2 não configurado!")

            # Parse JSON credentials
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )

            self._sheets_client = gspread.authorize(credentials)
            logger.info("✅ Google Sheets client autenticado")

        return self._sheets_client

    @property
    def supabase_client(self):
        """Supabase client (singleton)"""
        if self._supabase_client is None:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            if not url or not key:
                raise ValueError("SUPABASE_URL ou SUPABASE_KEY não configurados!")

            self._supabase_client = create_client(url, key)
            logger.info("✅ Supabase client conectado")

        return self._supabase_client

    async def scan_all_spreadsheets(self):
        """
        Varre todas as planilhas dos canais ativos.

        Processo:
        1. Busca canais ativos com spreadsheet_id
        2. Processa em batches (rate limiting)
        3. Para cada planilha, detecta vídeos prontos
        4. Adiciona na fila se passar validações
        5. Logs detalhados de tudo
        """

        if not self.is_active:
            logger.warning("🚨 Scanner desativado (circuit breaker)")
            return

        logger.info("=" * 80)
        logger.info("🔍 SCANNER INICIADO")
        logger.info(f"⏰ Timestamp: {datetime.now().isoformat()}")

        start_time = datetime.now()
        total_videos_found = 0
        total_videos_added = 0
        total_videos_skipped = 0
        total_errors = 0
        total_sheets_success = 0
        total_sheets_failed = 0

        try:
            # 1. Busca canais ativos
            channels = await self._get_active_channels()

            if not channels:
                logger.warning("⚠️  Nenhum canal ativo com spreadsheet_id encontrado")
                return

            logger.info(f"📊 Canais para varrer: {len(channels)}")
            logger.info("=" * 80)

            # 2. Processa em batches
            num_batches = (len(channels) - 1) // self.batch_size + 1

            for i in range(0, len(channels), self.batch_size):
                batch = channels[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1

                logger.info(f"📦 Batch {batch_num}/{num_batches} (canais {i+1}-{i+len(batch)})")

                # Processa batch em paralelo
                tasks = [self._scan_channel(ch) for ch in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Consolida resultados
                for result in results:
                    if isinstance(result, dict):
                        total_videos_found += result['found']
                        total_videos_added += result['added']
                        total_videos_skipped += result['skipped']
                        total_sheets_success += 1  # Planilha processada com sucesso
                    elif isinstance(result, Exception):
                        logger.error(f"   ❌ Erro no batch: {result}")
                        total_errors += 1
                        total_sheets_failed += 1  # Planilha falhou

                # Pausa entre batches (rate limiting - Google Sheets quota: 60 req/min)
                if i + self.batch_size < len(channels):
                    await asyncio.sleep(15)  # 15s para margem de 87% (suporte 70+ canais)

            # 3. Sucesso - reseta contador de erros
            self.error_count = 0

        except Exception as e:
            logger.error(f"💔 Erro crítico no scanner: {e}", exc_info=True)
            total_errors += 1
            self.error_count += 1

            # Circuit breaker
            if self.error_count >= self.max_errors:
                self.is_active = False
                logger.critical(f"🚨 SCANNER DESATIVADO após {self.max_errors} erros consecutivos!")
                logger.critical("   Para reativar: reinicie o Railway ou defina SCANNER_ENABLED=true")
                return

        # 4. Logs finais
        elapsed = (datetime.now() - start_time).total_seconds()
        total_sheets = total_sheets_success + total_sheets_failed

        logger.info("=" * 80)
        logger.info("✅ SCANNER CONCLUÍDO")
        logger.info(f"⏱️  Tempo total: {elapsed:.1f}s")
        logger.info(f"📊 Planilhas processadas: {total_sheets_success}/{total_sheets} ({(total_sheets_success/total_sheets*100) if total_sheets > 0 else 0:.0f}%)")
        if total_sheets_failed > 0:
            logger.warning(f"   ⚠️  Falhas: {total_sheets_failed} planilhas com erro")
        logger.info(f"📹 Vídeos encontrados: {total_videos_found}")
        logger.info(f"✅ Vídeos adicionados: {total_videos_added}")
        logger.info(f"⏭️  Vídeos skipados: {total_videos_skipped}")
        logger.info(f"❌ Erros: {total_errors}")
        logger.info("=" * 80)

    async def _get_active_channels(self) -> List[Dict]:
        """Busca canais ativos com spreadsheet_id configurado"""

        try:
            result = self.supabase_client.table('yt_channels').select(
                'channel_id, channel_name, spreadsheet_id, subnicho, lingua'
            ).eq('is_active', True).not_.is_('spreadsheet_id', 'null').execute()

            return result.data or []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar canais: {e}", exc_info=True)
            return []

    async def _scan_channel(self, channel: Dict) -> Dict:
        """
        Varre planilha de um canal específico.

        Args:
            channel: Dict com channel_id, channel_name, spreadsheet_id

        Returns:
            Dict com found, added, skipped
        """

        channel_id = channel['channel_id']
        spreadsheet_id = channel['spreadsheet_id']
        channel_name = channel.get('channel_name', 'Unknown')

        logger.info(f"  📊 Canal: {channel_name} ({channel_id})")
        logger.info(f"     Planilha: {spreadsheet_id}")

        try:
            # Timeout de N segundos por planilha (wait_for compatível com Python 3.10)
            result = await asyncio.wait_for(self._scan_spreadsheet(channel), timeout=self.timeout_per_sheet)

            # Mostra linhas lidas vs processadas (otimização de últimas 15)
            if result['rows_read'] > result.get('rows_processed', 0):
                logger.info(f"     ✅ Linhas lidas: {result['rows_read']} (processadas: {result.get('rows_processed', 0)})")
            else:
                logger.info(f"     ✅ Linhas lidas: {result['rows_read']}")

            logger.info(f"     📹 Vídeos encontrados: {result['found']}")

            if result['added'] > 0:
                logger.info(f"     ✅ Vídeos adicionados: {result['added']}")

            if result['skipped'] > 0:
                logger.info(f"     ⏭️  Vídeos skipados: {result['skipped']}")

            return result

        except asyncio.TimeoutError:
            logger.warning(f"     ⏰ Timeout ({self.timeout_per_sheet}s) - skipando")
            return {'found': 0, 'added': 0, 'skipped': 0, 'rows_read': 0, 'rows_processed': 0}

        except Exception as e:
            logger.error(f"     ❌ Erro: {e}", exc_info=True)
            return {'found': 0, 'added': 0, 'skipped': 0, 'rows_read': 0, 'rows_processed': 0}

    async def _scan_spreadsheet(self, channel: Dict) -> Dict:
        """
        Lê planilha, filtra linhas e adiciona vídeos prontos na fila.

        Args:
            channel: Dict com dados do canal

        Returns:
            Dict com found, added, skipped, rows_read
        """

        channel_id = channel['channel_id']
        spreadsheet_id = channel['spreadsheet_id']
        subnicho = channel.get('subnicho', '')
        lingua = channel.get('lingua', 'en')

        # 1. Abre planilha (sync - gspread não é async)
        # NOTA: Rodando em thread separada para não bloquear event loop
        def _read_sheet():
            try:
                sheet = self.sheets_client.open_by_key(spreadsheet_id)
                worksheet = sheet.worksheet('Página1')  # SEM espaço!
                return worksheet.get_all_values()
            except gspread.WorksheetNotFound:
                logger.warning(f"     ⚠️  Aba 'Página1' não encontrada")
                return []
            except Exception as e:
                logger.error(f"     ❌ Erro ao ler planilha: {e}")
                return []

        # Executa em thread pool (não bloqueia)
        loop = asyncio.get_event_loop()
        all_values = await loop.run_in_executor(None, _read_sheet)

        if not all_values or len(all_values) < 2:
            return {'found': 0, 'added': 0, 'skipped': 0, 'rows_read': 0, 'rows_processed': 0}

        # 2. Otimização: Processa apenas últimas 15 linhas (vídeos prontos são sequenciais)
        total_rows = len(all_values) - 1  # -1 para excluir header
        rows_limit = 15

        # Pega últimas N linhas (ou todas se < N)
        if total_rows > rows_limit:
            rows_to_process = all_values[-rows_limit:]
            start_row_number = len(all_values) - rows_limit + 1  # +1 porque row 1 = header
        else:
            rows_to_process = all_values[1:]  # Pula header
            start_row_number = 2  # Primeira linha de dados

        found = 0
        added = 0
        skipped = 0

        for offset, row_data in enumerate(rows_to_process):
            row_idx = start_row_number + offset  # Número real da linha na planilha

            # Valida se linha está pronta para upload
            if self._is_video_ready(row_data):
                found += 1

                # Tenta adicionar na fila
                success = await self._add_to_queue(
                    channel_id=channel_id,
                    spreadsheet_id=spreadsheet_id,
                    row_number=row_idx,
                    row_data=row_data,
                    subnicho=subnicho,
                    lingua=lingua
                )

                if success:
                    added += 1
                else:
                    skipped += 1

        return {
            'found': found,
            'added': added,
            'skipped': skipped,
            'rows_read': total_rows,
            'rows_processed': len(rows_to_process)
        }

    def _is_video_ready(self, row_data: List[str]) -> bool:
        """
        Verifica se linha está pronta para upload.

        Condições (TODAS devem ser TRUE):
        - J (Status) == "done"
        - K (Post) == vazio
        - O (Upload) == vazio
        - A (Name) preenchido
        - M (Drive URL) preenchido

        Args:
            row_data: Lista com valores das colunas

        Returns:
            bool: True se pronto, False caso contrário
        """

        # Garante que tem pelo menos 15 colunas
        if len(row_data) < 15:
            return False

        # Extrai valores (índice 0-based)
        name = row_data[0] if len(row_data) > 0 else ''           # A - Name
        status = row_data[9] if len(row_data) > 9 else ''         # J - Status
        post = row_data[10] if len(row_data) > 10 else ''         # K - Post
        video_url = row_data[12] if len(row_data) > 12 else ''    # M - Drive URL
        upload = row_data[14] if len(row_data) > 14 else ''       # O - Upload

        # Validações
        if status != 'done':
            return False  # Não renderizado

        if post and post.strip():
            return False  # Já tem data de publicação

        # Aceita vazio OU "❌ Erro" (para retry)
        # Ignora se = "✅" (sucesso) ou "❌ Erro Final" (limite de 3 tentativas)
        if upload and upload.strip():
            # Permite retry apenas se tiver exatamente "❌ Erro" (sem "Final")
            upload_clean = upload.strip()
            if upload_clean in ["❌ Erro", "❌ erro", "erro", "Erro"]:
                # Permite retry (não retorna False)
                pass
            else:
                # Qualquer outro valor = ignora (sucesso, erro final, etc)
                return False

        if not name or not name.strip():
            return False  # Sem título

        if not video_url or not video_url.strip():
            return False  # Sem URL

        # ✅ PASSOU EM TODAS!
        return True

    async def _add_to_queue(
        self,
        channel_id: str,
        spreadsheet_id: str,
        row_number: int,
        row_data: List[str],
        subnicho: str,
        lingua: str
    ) -> bool:
        """
        Adiciona vídeo na fila de upload (se não existir duplicata).

        Args:
            channel_id: ID do canal
            spreadsheet_id: ID da planilha
            row_number: Número da linha
            row_data: Dados da linha
            subnicho: Subnicho do canal
            lingua: Língua do canal

        Returns:
            bool: True se adicionou, False se skipou (duplicata)
        """

        # Extrai dados
        titulo = row_data[0].strip() if len(row_data) > 0 else ''
        descricao = row_data[1].strip() if len(row_data) > 1 else ''
        video_url = row_data[12].strip() if len(row_data) > 12 else ''

        # 1. Verifica duplicata no banco + controle de retry
        try:
            # Busca registro existente (qualquer status)
            existing = self.supabase_client.table('yt_upload_queue').select('id, status, retry_count').match({
                'spreadsheet_id': spreadsheet_id,
                'sheets_row_number': row_number
            }).execute()

            if existing.data:
                record = existing.data[0]

                # Se já está em processamento, skip
                if record['status'] in ['pending', 'downloading', 'uploading']:
                    logger.info(f"        ⏭️  Row {row_number}: Já em processamento (ID {record['id']})")
                    return False

                # Se já tentou 3 vezes, skip
                retry_count = record.get('retry_count', 0)
                if retry_count >= 3:
                    logger.info(f"        ⏭️  Row {row_number}: Limite de 3 tentativas atingido (ID {record['id']})")
                    return False

                # ✅ CORREÇÃO: Se status='failed' e retry_count < 3, fazer UPDATE para retry
                if record['status'] == 'failed':
                    # Reativar upload - muda status para 'pending'
                    self.supabase_client.table('yt_upload_queue').update({
                        'status': 'pending',
                        'error_message': None,  # Limpa erro anterior
                        'started_at': None,
                        'completed_at': None
                    }).eq('id', record['id']).execute()

                    logger.info(f"        🔁 Row {row_number}: Retry ativado (ID {record['id']}, tentativa {retry_count + 1}/3)")
                    return True  # Retorna True pois reativou com sucesso

                # Se status='completed', skip (já foi uploaded com sucesso)
                if record['status'] == 'completed':
                    logger.info(f"        ⏭️  Row {row_number}: Já uploaded com sucesso (ID {record['id']})")
                    return False

        except Exception as e:
            logger.error(f"        ❌ Erro ao verificar duplicata: {e}")
            return False

        # 2. Adiciona na fila
        try:
            result = self.supabase_client.table('yt_upload_queue').insert({
                'channel_id': channel_id,
                'video_url': video_url,
                'titulo': titulo,
                'descricao': descricao,
                'subnicho': subnicho,
                'lingua': lingua,
                'spreadsheet_id': spreadsheet_id,
                'sheets_row_number': row_number,
                'status': 'pending'
            }).execute()

            if not result.data:
                logger.error(f"        ❌ Erro ao inserir na fila (row {row_number})")
                return False

            upload_id = result.data[0]['id']
            logger.info(f"        ✅ Row {row_number}: \"{titulo[:40]}...\" → Fila (ID {upload_id})")

            # 3. Marca planilha como "processing" (DESABILITADO - economiza 1 req/vídeo)
            # await self._update_sheet_status(spreadsheet_id, row_number, "⏳ processing...")

            return True

        except Exception as e:
            logger.error(f"        ❌ Erro ao adicionar na fila (row {row_number}): {e}", exc_info=True)
            return False

    async def _update_sheet_status(self, spreadsheet_id: str, row_number: int, status: str):
        """Atualiza coluna O (Upload) na planilha"""

        try:
            def _update():
                sheet = self.sheets_client.open_by_key(spreadsheet_id)
                worksheet = sheet.worksheet('Página1')
                worksheet.update_cell(row_number, 15, status)  # Coluna O = 15

            # Executa em thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _update)

        except Exception as e:
            logger.warning(f"        ⚠️  Erro ao atualizar planilha (row {row_number}): {e}")
