# -*- coding: utf-8 -*-
"""
Sistema de Upload Diário Automático
Executa 1 upload por dia por canal após coleta diária
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from supabase import create_client
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cliente Supabase (usa SERVICE_ROLE_KEY para bypass RLS)
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Mudado de SUPABASE_KEY para SERVICE_ROLE_KEY
)

# Cache de planilhas (evita spam no Google Sheets)
SPREADSHEET_CACHE = {}
CACHE_DURATION = 300  # 5 minutos
MAX_CACHE_SIZE = 100  # Máximo de entradas no cache

def limpar_cache_expirado():
    """Remove entradas expiradas do cache de planilhas"""
    global SPREADSHEET_CACHE
    tempo_atual = time.time()
    entradas_expiradas = []

    for cache_key, (cache_time, _) in SPREADSHEET_CACHE.items():
        if tempo_atual - cache_time > CACHE_DURATION:
            entradas_expiradas.append(cache_key)

    for key in entradas_expiradas:
        del SPREADSHEET_CACHE[key]

    if entradas_expiradas:
        logger.info(f"Cache limpo: {len(entradas_expiradas)} entradas removidas")

    # Limitar tamanho do cache
    if len(SPREADSHEET_CACHE) > MAX_CACHE_SIZE:
        # Remove as entradas mais antigas
        sorted_cache = sorted(SPREADSHEET_CACHE.items(), key=lambda x: x[1][0])
        entries_to_remove = len(SPREADSHEET_CACHE) - MAX_CACHE_SIZE
        for key, _ in sorted_cache[:entries_to_remove]:
            del SPREADSHEET_CACHE[key]
        logger.info(f"Cache reduzido: {entries_to_remove} entradas removidas (limite de tamanho)")

class DailyUploader:
    """Sistema de upload diário automático"""

    def __init__(self):
        self.supabase = supabase
        self.sheets_client = self._init_sheets_client()
        self.upload_count = 0
        self.error_count = 0

    def _init_sheets_client(self):
        """Inicializa cliente Google Sheets"""
        try:
            creds_str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_2")
            if not creds_str:
                logger.error("GOOGLE_SHEETS_CREDENTIALS_2 não configurado!")
                return None

            creds = json.loads(creds_str)
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
            return gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Sheets: {e}")
            return None

    async def execute_daily_upload(self, retry_attempt: int = 1) -> Dict[str, List]:
        """
        Execução principal do upload diário

        Args:
            retry_attempt: 1 (após coleta), 2 (6:30), 3 (7:00)

        Returns:
            Dicionário com resultados por status
        """
        hoje = datetime.now().date()
        hora_inicio = datetime.now(timezone.utc)

        logger.info(f"🚀 INICIANDO UPLOAD DIÁRIO - Tentativa {retry_attempt}/3")

        # Limpar cache expirado periodicamente
        limpar_cache_expirado()

        # Verificação crítica: Google Sheets deve estar configurado
        if not self.sheets_client:
            logger.error("❌ ERRO CRÍTICO: Google Sheets não está configurado!")
            logger.error("Configure GOOGLE_SHEETS_CREDENTIALS_2 no ambiente")
            return {"sucesso": [], "erro": [], "sem_video": [], "pulado": []}

        # Inicializa log diário
        log_id = self._criar_log_diario(hoje, hora_inicio, retry_attempt)

        # Buscar canais elegíveis
        canais = self._get_eligible_channels(retry_attempt)

        if not canais:
            logger.info("Nenhum canal elegível para upload")
            self._finalizar_log_diario(log_id, hora_inicio, 0, 0, 0, 0, 0)
            return {"sucesso": [], "erro": [], "sem_video": [], "pulado": []}

        # Priorizar monetizados
        monetizados = [c for c in canais if c.get('is_monetized')]
        nao_monetizados = [c for c in canais if not c.get('is_monetized')]
        canais_ordenados = monetizados + nao_monetizados

        logger.info(f"📊 Canais para processar: {len(canais_ordenados)}")
        logger.info(f"    💰 Monetizados: {len(monetizados)}")
        logger.info(f"    📺 Não monetizados: {len(nao_monetizados)}")

        # Processar cada canal
        resultados = {
            "sucesso": [],
            "erro": [],
            "sem_video": [],
            "pulado": []
        }

        for i, canal in enumerate(canais_ordenados, 1):
            logger.info(f"\n[{i}/{len(canais_ordenados)}] Processando: {canal['channel_name']}")

            try:
                resultado = await self._process_canal_upload(canal, hoje, retry_attempt)
                status = resultado.get('status', 'erro')
                resultados[status].append(resultado)

                # Log do resultado
                if status == 'sucesso':
                    logger.info(f"    ✅ Upload realizado: {resultado.get('video_title', 'N/A')}")
                elif status == 'sem_video':
                    logger.warning(f"    ⚠️ Sem vídeos disponíveis")
                elif status == 'pulado':
                    logger.info(f"    ⏭️ Já fez upload hoje")
                else:
                    logger.error(f"    ❌ Erro: {resultado.get('error', 'Erro desconhecido')}")

            except Exception as e:
                logger.error(f"    ❌ Erro crítico: {str(e)}")
                resultados['erro'].append({
                    'status': 'erro',
                    'channel_id': canal['channel_id'],
                    'channel_name': canal['channel_name'],
                    'error': str(e)
                })

            # Pequeno delay para não sobrecarregar
            await asyncio.sleep(1)

        # Finalizar log diário
        self._finalizar_log_diario(
            log_id=log_id,
            hora_inicio=hora_inicio,
            total_canais=len(canais_ordenados),
            total_sucesso=len(resultados['sucesso']),
            total_erro=len(resultados['erro']),
            total_sem_video=len(resultados['sem_video']),
            total_pulado=len(resultados['pulado'])
        )

        # Resumo final
        logger.info("\n" + "=" * 60)
        logger.info("📊 RESUMO DO UPLOAD DIÁRIO")
        logger.info(f"   ✅ Sucesso: {len(resultados['sucesso'])}")
        logger.info(f"   ❌ Erros: {len(resultados['erro'])}")
        logger.info(f"   ⚠️ Sem vídeo: {len(resultados['sem_video'])}")
        logger.info(f"   ⏭️ Pulados: {len(resultados['pulado'])}")
        logger.info("=" * 60)

        return resultados

    def _get_eligible_channels(self, retry_attempt: int) -> List[Dict]:
        """
        Busca canais elegíveis para upload

        Se retry_attempt > 1, busca apenas canais com erro
        """
        try:
            if retry_attempt == 1:
                # Primeira execução: todos com upload_automatico=true
                result = self.supabase.table('yt_channels')\
                    .select('*')\
                    .eq('is_active', True)\
                    .eq('upload_automatico', True)\
                    .execute()
                return result.data
            else:
                # Retry: apenas canais com erro hoje
                hoje = datetime.now().date().isoformat()
                result = self.supabase.table('yt_canal_upload_diario')\
                    .select('channel_id')\
                    .eq('data', hoje)\
                    .eq('status', 'erro')\
                    .lt('tentativa_numero', retry_attempt)\
                    .execute()

                if not result.data:
                    return []

                # Buscar dados completos dos canais
                channel_ids = [r['channel_id'] for r in result.data]
                canais = []
                for channel_id in channel_ids:
                    canal_result = self.supabase.table('yt_channels')\
                        .select('*')\
                        .eq('channel_id', channel_id)\
                        .single()\
                        .execute()
                    if canal_result.data:
                        canais.append(canal_result.data)

                return canais

        except Exception as e:
            logger.error(f"Erro ao buscar canais elegíveis: {e}")
            return []

    async def _process_canal_upload(self, canal: Dict, data: Any, retry_attempt: int) -> Dict:
        """
        Processa upload de 1 canal
        """
        channel_id = canal['channel_id']
        channel_name = canal['channel_name']
        spreadsheet_id = canal.get('spreadsheet_id')

        # REMOVIDO: Verificação de "já fez upload hoje" - permitir múltiplos uploads
        # Agora verifica apenas se tem vídeo disponível na planilha

        # Verificar se tem planilha configurada
        if not spreadsheet_id:
            logger.warning(f"Canal {channel_name} sem planilha configurada")
            self._registrar_canal_diario(channel_id, channel_name, data, 'erro',
                                        'Sem planilha configurada', retry_attempt)
            return {
                'status': 'erro',
                'channel_id': channel_id,
                'channel_name': channel_name,
                'error': 'Sem planilha configurada'
            }

        # Limpa cache para forçar busca atualizada (importante para uploads forçados)
        if spreadsheet_id in SPREADSHEET_CACHE:
            del SPREADSHEET_CACHE[spreadsheet_id]
            logger.debug(f"Cache limpo para planilha de {channel_name}")

        # Buscar vídeo pronto na planilha
        video_pronto = await self._find_ready_video(spreadsheet_id, channel_name)

        if not video_pronto:
            # Registra que não tem vídeo
            self._registrar_canal_diario(channel_id, channel_name, data, 'sem_video',
                                        None, retry_attempt)
            return {
                'status': 'sem_video',
                'channel_id': channel_id,
                'channel_name': channel_name
            }

        # Verificar duplicata (proteção extra)
        if self._video_ja_foi_uploaded(channel_id, video_pronto['titulo']):
            logger.info(f"Vídeo '{video_pronto['titulo']}' já foi uploaded anteriormente")
            return {
                'status': 'pulado',
                'channel_id': channel_id,
                'channel_name': channel_name,
                'message': 'Vídeo já foi uploaded'
            }

        # Adicionar na fila de upload
        upload_id = self._add_to_queue(canal, video_pronto)

        if not upload_id:
            self._registrar_canal_diario(channel_id, channel_name, data, 'erro',
                                        'Falha ao adicionar na fila', retry_attempt)
            return {
                'status': 'erro',
                'channel_id': channel_id,
                'channel_name': channel_name,
                'error': 'Falha ao adicionar na fila'
            }

        # Processar upload (chama o sistema existente)
        try:
            # Importa função de upload existente
            from main import process_upload_task

            # Processa upload imediatamente
            result = await process_upload_task(upload_id)

            # Verifica resultado
            upload_status = self._check_upload_status(upload_id)

            if upload_status == 'completed':
                # Registra sucesso
                self._registrar_canal_diario(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    data=data,
                    status='sucesso',
                    erro_mensagem=None,
                    tentativa_numero=retry_attempt,
                    upload_id=upload_id,
                    video_titulo=video_pronto['titulo'],
                    video_url=video_pronto.get('video_url')
                )

                return {
                    'status': 'sucesso',
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'video_title': video_pronto['titulo'],
                    'upload_id': upload_id
                }
            else:
                # Busca mensagem de erro
                erro_msg = self._get_upload_error(upload_id)

                # Registra erro
                self._registrar_canal_diario(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    data=data,
                    status='erro',
                    erro_mensagem=erro_msg,
                    tentativa_numero=retry_attempt,
                    upload_id=upload_id,
                    video_titulo=video_pronto['titulo']
                )

                return {
                    'status': 'erro',
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'error': erro_msg or 'Upload falhou',
                    'upload_id': upload_id
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro ao processar upload: {error_msg}")

            # Registra erro
            self._registrar_canal_diario(
                channel_id=channel_id,
                channel_name=channel_name,
                data=data,
                status='erro',
                erro_mensagem=error_msg,
                tentativa_numero=retry_attempt,
                video_titulo=video_pronto.get('titulo')
            )

            return {
                'status': 'erro',
                'channel_id': channel_id,
                'channel_name': channel_name,
                'error': error_msg,
                'upload_id': upload_id
            }

    async def _find_ready_video(self, spreadsheet_id: str, channel_name: str, skip_count: int = 0) -> Optional[Dict]:
        """
        Busca vídeo pronto na planilha

        Condições:
        - Coluna J (Status) = "done"
        - Coluna K (Post) = vazio
        - Coluna L (Published Date) = vazio
        - Coluna O (Upload) = vazio ou contém "Erro"
        - Coluna A (Name) preenchido
        - Coluna M (Drive URL) preenchido

        Args:
            spreadsheet_id: ID da planilha Google Sheets
            channel_name: Nome do canal (para logs)
            skip_count: Quantos vídeos prontos pular (0 = primeiro, 1 = segundo, etc)
        """
        try:
            # Verifica cache
            cache_key = spreadsheet_id
            if cache_key in SPREADSHEET_CACHE:
                cache_time, cached_data = SPREADSHEET_CACHE[cache_key]
                if time.time() - cache_time < CACHE_DURATION:
                    logger.info(f"Usando cache da planilha para {channel_name}")
                    return self._process_cached_data(cached_data, skip_count)

            # Busca nova se não tem cache
            if not self.sheets_client:
                logger.error("Cliente Google Sheets não inicializado")
                return None

            # Abre planilha
            # Delay antes de abrir planilha para evitar quota exceeded
            await asyncio.sleep(2)

            sheet = self.sheets_client.open_by_key(spreadsheet_id)

            # Delay após abrir planilha
            await asyncio.sleep(1)

            worksheet = sheet.get_worksheet(0)  # Primeira aba

            # Delay antes de buscar valores
            await asyncio.sleep(1)

            # Pega todas as linhas (otimização: últimas 50)
            all_values = worksheet.get_all_values()

            # Delay após buscar todos os valores
            await asyncio.sleep(1)

            # Cache para próximas consultas
            SPREADSHEET_CACHE[cache_key] = (time.time(), all_values)

            # Processa dados
            return self._process_cached_data(all_values, skip_count)

        except Exception as e:
            logger.error(f"Erro ao buscar vídeo pronto: {e}")
            return None

    def _process_cached_data(self, all_values: List[List], skip_count: int = 0) -> Optional[Dict]:
        """Processa dados da planilha e encontra vídeo pronto

        Args:
            all_values: Dados da planilha
            skip_count: Quantos vídeos prontos pular antes de retornar (0 = primeiro)
        """
        videos_found = 0

        # Pula header (linha 0)
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) < 15:  # Precisa ter pelo menos até coluna O
                continue

            # Colunas (0-indexed):
            # A=0 (Name), J=9 (Status), K=10 (Post), L=11 (Published Date)
            # M=12 (Drive URL), O=14 (Upload)

            name = row[0] if len(row) > 0 else ""
            status = row[9] if len(row) > 9 else ""
            post = row[10] if len(row) > 10 else ""
            published_date = row[11] if len(row) > 11 else ""
            drive_url = row[12] if len(row) > 12 else ""
            upload_status = row[14] if len(row) > 14 else ""

            # Validações
            if status.lower() != "done":
                continue
            if post:  # Post deve estar vazio
                continue
            if published_date:  # Published Date deve estar vazio
                continue
            if not name:  # Nome é obrigatório
                continue
            if not drive_url:  # Drive URL é obrigatório
                continue
            # Aceita: vazio, None, ou contém "erro" (case-insensitive)
            if upload_status and upload_status.strip() != "" and "erro" not in upload_status.lower():
                continue  # Pula se já foi uploaded com sucesso

            # Vídeo pronto encontrado!
            # Verifica se deve pular este
            if videos_found < skip_count:
                videos_found += 1
                continue
            # Busca descrição (geralmente coluna B ou C)
            descricao = row[1] if len(row) > 1 else ""
            if not descricao and len(row) > 2:
                descricao = row[2]

            return {
                'titulo': name.strip(),
                'descricao': descricao.strip() if descricao else "",
                'video_url': drive_url.strip(),
                'row_number': i,  # Número da linha na planilha
                'status': status
            }

        return None  # Nenhum vídeo pronto

    def _ja_fez_upload_hoje(self, channel_id: str, data: Any) -> bool:
        """Verifica se canal já fez upload hoje com sucesso"""
        try:
            result = self.supabase.table('yt_canal_upload_diario')\
                .select('id')\
                .eq('channel_id', channel_id)\
                .eq('data', data.isoformat())\
                .eq('upload_realizado', True)\
                .execute()

            return len(result.data) > 0
        except:
            return False

    def _video_ja_foi_uploaded(self, channel_id: str, titulo: str) -> bool:
        """Verifica se este vídeo específico já foi uploaded (proteção duplicata)"""
        try:
            # Busca nos últimos 30 dias
            data_limite = (datetime.now() - timedelta(days=30)).isoformat()

            result = self.supabase.table('yt_upload_queue')\
                .select('id')\
                .eq('channel_id', channel_id)\
                .eq('titulo', titulo)\
                .eq('status', 'completed')\
                .gte('completed_at', data_limite)\
                .execute()

            return len(result.data) > 0
        except:
            return False

    def _add_to_queue(self, canal: Dict, video_data: Dict) -> Optional[int]:
        """Adiciona vídeo na fila de upload"""
        try:
            data = {
                'channel_id': canal['channel_id'],
                'video_url': video_data['video_url'],
                'titulo': video_data['titulo'],
                'descricao': video_data.get('descricao', ''),
                'subnicho': canal.get('subnicho', ''),
                'lingua': canal.get('lingua', 'pt'),
                'spreadsheet_id': canal.get('spreadsheet_id'),
                'sheets_row_number': video_data.get('row_number'),
                'status': 'pending',
                'retry_count': 0,
                'scheduled_at': datetime.now(timezone.utc).isoformat()
            }

            result = self.supabase.table('yt_upload_queue')\
                .insert(data)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            return None

        except Exception as e:
            logger.error(f"Erro ao adicionar na fila: {e}")
            return None

    def _check_upload_status(self, upload_id: int) -> str:
        """Verifica status do upload"""
        try:
            result = self.supabase.table('yt_upload_queue')\
                .select('status')\
                .eq('id', upload_id)\
                .single()\
                .execute()

            return result.data.get('status', 'unknown')
        except:
            return 'unknown'

    def _get_upload_error(self, upload_id: int) -> Optional[str]:
        """Busca mensagem de erro do upload"""
        try:
            result = self.supabase.table('yt_upload_queue')\
                .select('error_message')\
                .eq('id', upload_id)\
                .single()\
                .execute()

            return result.data.get('error_message')
        except:
            return None

    def _criar_log_diario(self, data: Any, hora_inicio: datetime, tentativa: int) -> int:
        """Cria registro de log diário"""
        try:
            data_log = {
                'data': data.isoformat(),
                'hora_inicio': hora_inicio.isoformat(),
                'tentativa_numero': tentativa,
                'total_canais': 0,
                'total_elegiveis': 0,
                'total_sem_video': 0,
                'total_sucesso': 0,
                'total_erro': 0,
                'total_pulado': 0
            }

            result = self.supabase.table('yt_upload_daily_logs')\
                .insert(data_log)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            return 0

        except Exception as e:
            logger.error(f"Erro ao criar log diário: {e}")
            return 0

    def _finalizar_log_diario(self, log_id: int, hora_inicio: datetime, total_canais: int,
                              total_sucesso: int, total_erro: int, total_sem_video: int,
                              total_pulado: int):
        """Finaliza log diário com estatísticas"""
        if not log_id:
            return

        try:
            hora_fim = datetime.now(timezone.utc)

            # Buscar IDs dos canais com problema
            hoje = datetime.now().date().isoformat()

            # Canais sem vídeo
            sem_video_result = self.supabase.table('yt_canal_upload_diario')\
                .select('channel_id')\
                .eq('data', hoje)\
                .eq('status', 'sem_video')\
                .execute()
            canais_sem_video = [r['channel_id'] for r in sem_video_result.data]

            # Canais com erro
            erro_result = self.supabase.table('yt_canal_upload_diario')\
                .select('channel_id')\
                .eq('data', hoje)\
                .eq('status', 'erro')\
                .execute()
            canais_com_erro = [r['channel_id'] for r in erro_result.data]

            # Atualiza log
            update_data = {
                'hora_fim': hora_fim.isoformat(),
                'total_canais': total_canais,
                'total_elegiveis': total_canais - total_pulado,
                'total_sucesso': total_sucesso,
                'total_erro': total_erro,
                'total_sem_video': total_sem_video,
                'total_pulado': total_pulado,
                'canais_sem_video': canais_sem_video,
                'canais_com_erro': canais_com_erro
            }

            self.supabase.table('yt_upload_daily_logs')\
                .update(update_data)\
                .eq('id', log_id)\
                .execute()

        except Exception as e:
            logger.error(f"Erro ao finalizar log diário: {e}")

    def _registrar_canal_diario(self, channel_id: str, channel_name: str, data: Any,
                                status: str, erro_mensagem: Optional[str] = None,
                                tentativa_numero: int = 1, upload_id: Optional[int] = None,
                                video_titulo: Optional[str] = None, video_url: Optional[str] = None):
        """Registra ou atualiza status do canal no dia"""
        try:
            data_dict = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'data': data.isoformat(),
                'upload_realizado': (status == 'sucesso'),
                'status': status,
                'erro_mensagem': erro_mensagem,
                'tentativa_numero': tentativa_numero,
                'hora_processamento': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            if upload_id:
                data_dict['upload_id'] = upload_id
            if video_titulo:
                data_dict['video_titulo'] = video_titulo
            if video_url:
                data_dict['video_url'] = video_url

            # Upsert (insert or update)
            self.supabase.table('yt_canal_upload_diario')\
                .upsert(data_dict, on_conflict='channel_id,data')\
                .execute()

            # TAMBÉM adicionar ao histórico (preserva todos os uploads)
            # Somente registrar no histórico se for sucesso ou erro (não registrar pendente)
            if status in ['sucesso', 'erro']:
                # Buscar spreadsheet_id do canal
                spreadsheet_id = None
                video_row = None
                try:
                    canal_info = self.supabase.table('yt_channels')\
                        .select('spreadsheet_id')\
                        .eq('channel_id', channel_id)\
                        .single()\
                        .execute()
                    if canal_info.data:
                        spreadsheet_id = canal_info.data.get('spreadsheet_id')
                except:
                    pass

                self._adicionar_historico(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    data=data,
                    status=status,
                    erro_mensagem=erro_mensagem,
                    tentativa_numero=tentativa_numero,
                    upload_id=upload_id,
                    video_titulo=video_titulo,
                    video_url=video_url,
                    sheets_row_number=video_row  # Corrigido: usar sheets_row_number
                )

        except Exception as e:
            logger.error(f"Erro ao registrar canal diário: {e}")

    def _adicionar_historico(self,
                           channel_id: str,
                           channel_name: str,
                           data,
                           status: str = 'pendente',
                           erro_mensagem: Optional[str] = None,
                           tentativa_numero: int = 1,
                           upload_id: Optional[int] = None,
                           video_titulo: Optional[str] = None,
                           video_url: Optional[str] = None,
                           sheets_row_number: Optional[int] = None) -> None:
        """
        Adiciona registro ao histórico de uploads (preserva todos os uploads do dia)

        Args:
            Mesmos parâmetros de _registrar_canal_diario
        """
        try:
            # Dados para inserir no histórico
            historico_data = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'data': data.isoformat(),
                'status': status,
                'tentativa_numero': tentativa_numero,
                'hora_processamento': datetime.now(timezone.utc).isoformat()
            }

            # Adicionar campos opcionais se existirem
            if video_titulo:
                historico_data['video_titulo'] = video_titulo
            if video_url:
                # Extrair youtube_video_id da URL se possível
                if 'youtube.com/watch?v=' in video_url:
                    video_id = video_url.split('v=')[1].split('&')[0]
                    historico_data['youtube_video_id'] = video_id
                elif 'youtu.be/' in video_url:
                    video_id = video_url.split('youtu.be/')[1].split('?')[0]
                    historico_data['youtube_video_id'] = video_id
                # Salvar URL do Google Drive (não YouTube)
                historico_data['video_url'] = video_url
            if erro_mensagem:
                historico_data['erro_mensagem'] = erro_mensagem
            if upload_id:
                historico_data['upload_id'] = upload_id
            if sheets_row_number:
                historico_data['sheets_row_number'] = sheets_row_number

            # Inserir no histórico (sempre INSERT, nunca UPSERT)
            result = self.supabase.table('yt_canal_upload_historico')\
                .insert(historico_data)\
                .execute()

            if result.data:
                logger.info(f"📝 Histórico registrado para {channel_name}")

        except Exception as e:
            # Se a tabela não existe, apenas registra aviso (não quebra o fluxo)
            if "relation" in str(e) and "does not exist" in str(e):
                logger.debug("Tabela de histórico ainda não existe")
            else:
                logger.error(f"Erro ao adicionar ao histórico: {e}")

    async def retry_failed_channels(self, retry_attempt: int = 2, manual: bool = False) -> Dict:
        """
        Retry para canais que falharam

        Args:
            retry_attempt: Número da tentativa (2 ou 3)
            manual: Se foi disparado manualmente pelo dashboard
        """
        if manual:
            logger.info("🔁 RETRY MANUAL - Reprocessando canais com erro")
        else:
            logger.info(f"🔁 RETRY AUTOMÁTICO {retry_attempt}/3")

        return await self.execute_daily_upload(retry_attempt)

    async def upload_next_video(self, channel_id: str) -> Dict:
        """
        Pula o vídeo com erro atual e faz upload do próximo na fila

        Args:
            channel_id: ID do canal

        Returns:
            Dict com status do upload
        """
        try:
            # Busca dados do canal
            result = self.supabase.table('yt_channels')\
                .select('*')\
                .eq('channel_id', channel_id)\
                .single()\
                .execute()

            if not result.data:
                return {
                    'status': 'erro',
                    'error': 'Canal não encontrado'
                }

            canal = result.data
            channel_name = canal['channel_name']
            spreadsheet_id = canal.get('spreadsheet_id')
            hoje = datetime.now().date()

            if not spreadsheet_id:
                return {
                    'status': 'erro',
                    'error': 'Canal sem planilha configurada'
                }

            # Limpa cache para forçar busca atualizada
            if spreadsheet_id in SPREADSHEET_CACHE:
                del SPREADSHEET_CACHE[spreadsheet_id]

            # Busca o PRÓXIMO vídeo (skip_count=1 pula o primeiro)
            video_pronto = await self._find_ready_video(spreadsheet_id, channel_name, skip_count=1)

            if not video_pronto:
                logger.info(f"⚠️ Não há próximo vídeo disponível para {channel_name}")
                return {
                    'status': 'sem_video',
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'message': 'Não há próximo vídeo na fila'
                }

            logger.info(f"⏭️ Upload Próximo para {channel_name}: '{video_pronto['titulo']}'")

            # Adicionar na fila de upload
            upload_id = self._add_to_queue(canal, video_pronto)

            if not upload_id:
                return {
                    'status': 'erro',
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'error': 'Falha ao adicionar na fila'
                }

            # Processar upload
            try:
                from main import process_upload_task
                result = await process_upload_task(upload_id)

                # Verifica resultado
                upload_status = self._check_upload_status(upload_id)

                if upload_status == 'completed':
                    # Registra sucesso
                    self._registrar_canal_diario(
                        channel_id=channel_id,
                        channel_name=channel_name,
                        data=hoje,
                        status='sucesso',
                        erro_mensagem=None,
                        tentativa_numero=99,  # Marca como manual
                        upload_id=upload_id,
                        video_titulo=video_pronto['titulo'],
                        video_url=video_pronto.get('video_url')
                    )

                    return {
                        'status': 'sucesso',
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'video_title': video_pronto['titulo'],
                        'upload_id': upload_id,
                        'message': 'Upload do próximo vídeo realizado com sucesso!'
                    }
                else:
                    erro_msg = self._get_upload_error(upload_id)
                    return {
                        'status': 'erro',
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'error': erro_msg or 'Upload falhou',
                        'upload_id': upload_id
                    }

            except Exception as e:
                return {
                    'status': 'erro',
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'error': str(e)
                }

        except Exception as e:
            logger.error(f"Erro no upload_next_video: {e}")
            return {
                'status': 'erro',
                'error': str(e)
            }

    async def retry_single_channel(self, channel_id: str, manual: bool = True) -> Dict:
        """Retry para um canal específico"""
        try:
            # Busca dados do canal
            result = self.supabase.table('yt_channels')\
                .select('*')\
                .eq('channel_id', channel_id)\
                .single()\
                .execute()

            if not result.data:
                return {
                    'status': 'erro',
                    'error': 'Canal não encontrado'
                }

            canal = result.data
            hoje = datetime.now().date()

            # Busca tentativa atual
            retry_result = self.supabase.table('yt_canal_upload_diario')\
                .select('tentativa_numero')\
                .eq('channel_id', channel_id)\
                .eq('data', hoje.isoformat())\
                .single()\
                .execute()

            tentativa = 1
            if retry_result.data:
                tentativa = retry_result.data.get('tentativa_numero', 0) + 1

            logger.info(f"🔁 Retry manual para {canal['channel_name']} (tentativa {tentativa})")

            # Processa upload
            resultado = await self._process_canal_upload(canal, hoje, tentativa)

            return resultado

        except Exception as e:
            logger.error(f"Erro no retry individual: {e}")
            return {
                'status': 'erro',
                'error': str(e)
            }


# ============================================================
# SCHEDULER DE EXECUÇÃO
# ============================================================

async def check_collection_finished():
    """
    Verifica se a coleta diária terminou

    Métodos possíveis:
    1. Verificar último registro em coletas_historico
    2. Verificar se todos canais foram coletados hoje
    3. Aguardar horário fixo (ex: 5:45 AM)
    """
    try:
        # Método 1: Verificar se teve coleta nos últimos 30 minutos
        limite = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

        result = supabase.table('coletas_historico')\
            .select('created_at')\
            .gte('created_at', limite)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        if result.data:
            logger.info("Coleta detectada nos últimos 30 minutos")
            return True

        # Método 2: Verificar horário (backup)
        now = datetime.now()
        if now.hour == 5 and now.minute >= 30:
            logger.info("Horário de coleta atingido (5:30+)")
            return True

        return False

    except Exception as e:
        logger.error(f"Erro ao verificar coleta: {e}")
        return False


async def schedule_daily_uploader():
    """
    Scheduler principal do sistema de upload diário

    Horários:
    - Após coleta (~5:30-6:00): Execução principal
    - 6:30 AM: Retry 1
    - 7:00 AM: Retry 2
    """
    uploader = DailyUploader()
    last_execution_date = None

    while True:
        try:
            now = datetime.now()
            hoje = now.date()

            # Reseta flag no início do dia
            if now.hour == 0 and now.minute < 5:
                last_execution_date = None
                await asyncio.sleep(300)  # Aguarda 5 minutos
                continue

            # Execução principal (após coleta)
            if last_execution_date != hoje:
                if await check_collection_finished():
                    logger.info("=" * 60)
                    logger.info("📤 SISTEMA DE UPLOAD DIÁRIO - EXECUÇÃO PRINCIPAL")
                    logger.info("=" * 60)

                    await uploader.execute_daily_upload(retry_attempt=1)
                    last_execution_date = hoje

                    # Aguarda 30 minutos antes de permitir retry
                    await asyncio.sleep(1800)

            # Retry 1: 6:30 AM
            if now.hour == 6 and 30 <= now.minute < 35:
                if last_execution_date == hoje:  # Só faz retry se já executou hoje
                    logger.info("=" * 60)
                    logger.info("🔁 RETRY 1/2 - 6:30 AM")
                    logger.info("=" * 60)

                    await uploader.retry_failed_channels(retry_attempt=2)
                    await asyncio.sleep(300)  # Previne dupla execução

            # Retry 2: 7:00 AM
            if now.hour == 7 and 0 <= now.minute < 5:
                if last_execution_date == hoje:  # Só faz retry se já executou hoje
                    logger.info("=" * 60)
                    logger.info("🔁 RETRY 2/2 (FINAL) - 7:00 AM")
                    logger.info("=" * 60)

                    await uploader.retry_failed_channels(retry_attempt=3)
                    await asyncio.sleep(300)  # Previne dupla execução

            # Aguarda 30 segundos antes de verificar novamente
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Erro no scheduler: {e}")
            await asyncio.sleep(60)  # Aguarda 1 minuto em caso de erro


# ============================================================
# EXECUÇÃO MANUAL (PARA TESTES)
# ============================================================

async def test_daily_upload():
    """Função para testar o upload diário manualmente"""
    logger.info("🧪 MODO TESTE - Executando upload diário manualmente")

    uploader = DailyUploader()
    resultados = await uploader.execute_daily_upload(retry_attempt=1)

    print("\n" + "=" * 60)
    print("RESULTADOS DO TESTE:")
    print(f"Sucesso: {len(resultados['sucesso'])} canais")
    print(f"Erro: {len(resultados['erro'])} canais")
    print(f"Sem vídeo: {len(resultados['sem_video'])} canais")
    print(f"Pulados: {len(resultados['pulado'])} canais")
    print("=" * 60)

    if resultados['erro']:
        print("\nERROS DETECTADOS:")
        for erro in resultados['erro']:
            print(f"  - {erro['channel_name']}: {erro.get('error', 'Erro desconhecido')}")

    if resultados['sem_video']:
        print("\nCANAIS SEM VÍDEO:")
        for sv in resultados['sem_video']:
            print(f"  - {sv['channel_name']}")

    return resultados


if __name__ == "__main__":
    # Teste manual
    asyncio.run(test_daily_upload())