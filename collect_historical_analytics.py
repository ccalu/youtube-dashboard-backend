"""
Script para coletar dados históricos de Analytics Avançado
Coleta dados das últimas semanas para popular as novas tabelas
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar as funções de coleta do monetization_oauth_collector
from monetization_oauth_collector import (
    get_tokens,
    get_proxy_credentials,
    refresh_access_token,
    update_tokens,
    collect_traffic_sources,
    collect_search_terms,
    collect_suggested_videos,
    collect_demographics,
    collect_device_metrics,
    save_traffic_sources,
    save_search_terms,
    save_suggested_videos,
    save_demographics,
    save_device_metrics
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_analytics.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Importar Supabase
from supabase import create_client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def collect_historical_analytics(days_back=30, start_from_date=None):
    """
    Coleta dados históricos de analytics avançado para todos os canais monetizados

    Args:
        days_back: Número de dias para voltar no histórico (padrão: 30)
        start_from_date: Data específica para iniciar (formato: 'YYYY-MM-DD')
    """
    log.info("=" * 60)
    if start_from_date:
        log.info(f"INICIANDO COLETA HISTÓRICA DESDE {start_from_date}")
    else:
        log.info(f"INICIANDO COLETA HISTÓRICA - ÚLTIMOS {days_back} DIAS")
    log.info("=" * 60)

    # Buscar canais monetizados
    result = supabase.table("yt_channels")\
        .select("channel_id, channel_name, proxy_name")\
        .eq("is_monetized", True)\
        .execute()

    channels = result.data
    log.info(f"Canais monetizados encontrados: {len(channels)}")

    # Para cada canal
    for channel in channels:
        channel_id = channel['channel_id']
        channel_name = channel['channel_name']
        proxy_name = channel.get('proxy_name', 'C000.1')  # Default: C000.1

        log.info(f"\n[{channel_name}] Iniciando coleta histórica... (proxy: {proxy_name})")

        # Obter token OAuth
        token_data = get_tokens(channel_id)
        if not token_data:
            log.error(f"[{channel_name}] Sem token OAuth, pulando...")
            continue

        refresh_token = token_data.get('refresh_token')

        # SEMPRE renovar o token antes de coletar (igual à coleta diária)
        log.info(f"[{channel_name}] Renovando token OAuth...")

        # Buscar credenciais do proxy
        proxy_creds = get_proxy_credentials(proxy_name)
        if not proxy_creds:
            log.error(f"[{channel_name}] Sem credenciais do proxy, pulando...")
            continue

        client_id = proxy_creds['client_id']
        client_secret = proxy_creds['client_secret']

        # Renovar token (refresh_access_token retorna STRING, não dict)
        access_token = refresh_access_token(refresh_token, client_id, client_secret)
        if not access_token:
            log.error(f"[{channel_name}] Falha ao renovar token, pulando...")
            continue

        update_tokens(channel_id, access_token)

        # Coletar dados dia por dia
        end_date = datetime.now().date() - timedelta(days=1)  # Ontem

        if start_from_date:
            start_date = datetime.strptime(start_from_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=days_back)

        current_date = start_date
        days_collected = 0

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            log.info(f"[{channel_name}] Coletando dados de {date_str}...")

            try:
                # 1. TRAFFIC SOURCES (Fontes de tráfego)
                traffic_data = collect_traffic_sources(
                    channel_id,
                    access_token,
                    date_str,
                    date_str
                )
                if traffic_data:
                    save_traffic_sources(channel_id, date_str, traffic_data)
                    log.info(f"  ✓ Traffic sources: {len(traffic_data)} tipos")

                # 2. SEARCH TERMS (Termos de busca)
                search_data = collect_search_terms(
                    channel_id,
                    access_token,
                    date_str,
                    date_str
                )
                if search_data:
                    save_search_terms(channel_id, date_str, search_data)
                    log.info(f"  ✓ Search terms: {len(search_data)} termos")

                # 3. SUGGESTED VIDEOS (Vídeos que recomendam)
                suggested_data = collect_suggested_videos(
                    channel_id,
                    access_token,
                    date_str,
                    date_str
                )
                if suggested_data:
                    save_suggested_videos(channel_id, date_str, suggested_data)
                    log.info(f"  ✓ Suggested videos: {len(suggested_data)} vídeos")

                # 4. DEMOGRAPHICS (Demografia)
                demo_data = collect_demographics(
                    channel_id,
                    access_token,
                    date_str,
                    date_str
                )
                if demo_data:
                    save_demographics(channel_id, date_str, demo_data)
                    log.info(f"  ✓ Demographics: {len(demo_data)} grupos")

                # 5. DEVICE METRICS (Dispositivos)
                device_data = collect_device_metrics(
                    channel_id,
                    access_token,
                    date_str,
                    date_str
                )
                if device_data:
                    save_device_metrics(channel_id, date_str, device_data)
                    log.info(f"  ✓ Device metrics: {len(device_data)} tipos")

                days_collected += 1

            except Exception as e:
                log.error(f"[{channel_name}] Erro ao coletar {date_str}: {str(e)}")

            # Próximo dia
            current_date += timedelta(days=1)

            # Pequena pausa para não sobrecarregar a API
            import time
            time.sleep(0.5)

        log.info(f"[{channel_name}] Coleta completa: {days_collected} dias processados")

    log.info("\n" + "=" * 60)
    log.info("COLETA HISTÓRICA CONCLUÍDA!")
    log.info("=" * 60)

    # Verificar se as tabelas foram populadas
    verify_data()

def verify_data():
    """Verifica se as tabelas foram populadas com dados"""
    log.info("\nVerificando dados nas tabelas...")

    tables = [
        'yt_traffic_summary',
        'yt_search_analytics',
        'yt_suggested_sources',
        'yt_demographics',
        'yt_device_metrics'
    ]

    for table in tables:
        result = supabase.table(table).select("*", count="exact").execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        log.info(f"  {table}: {count} registros")

if __name__ == "__main__":
    # Parâmetros opcionais
    days = 30  # Padrão: 30 dias
    start_date = None

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Se for uma data no formato YYYY-MM-DD
        if '-' in arg and len(arg) == 10:
            start_date = arg
            log.info(f"Iniciando coleta desde {start_date}...")
        else:
            try:
                days = int(arg)
                log.info(f"Iniciando coleta de {days} dias de histórico...")
            except:
                log.error(f"Parâmetro inválido: {arg}")
                log.info("Use: python collect_historical_analytics.py [dias] ou [YYYY-MM-DD]")
                sys.exit(1)

    collect_historical_analytics(days, start_date)