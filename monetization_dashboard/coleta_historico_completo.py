"""
Coleta HISTORICO COMPLETO de Métricas do YouTube
Busca últimos 90+ dias incluindo RETENÇÃO e CTR
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coleta_diaria import *
from datetime import datetime, timedelta
import logging

# Reconfigurar logging para arquivo específico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/coleta_historico.log'),
        logging.StreamHandler()
    ],
    force=True
)
log = logging.getLogger(__name__)

def main_historico():
    log.info("=" * 60)
    log.info("INICIANDO COLETA DE HISTORICO COMPLETO")
    log.info("=" * 60)

    # Datas - ÚLTIMOS 90 DIAS!
    end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")  # D-3 (delay YouTube)
    start_date = "2025-09-01"  # Início dos canais (setembro)

    log.info(f"Período: {start_date} até {end_date}")
    log.info("Incluindo: Revenue, Views, Retenção, CTR")

    # Buscar canais
    channels = get_channels()
    log.info(f"Canais encontrados: {len(channels)}")

    total_saved = 0
    total_video_saved = 0

    for channel in channels:
        channel_id = channel["channel_id"]
        channel_name = channel.get("channel_name", channel_id)
        proxy_name = channel.get("proxy_name", "C000.1")

        log.info(f"\n[{channel_name}] Iniciando coleta HISTORICA... (proxy: {proxy_name})")

        # Buscar credenciais do proxy
        credentials = get_proxy_credentials(proxy_name)
        if not credentials:
            log.error(f"[{channel_name}] Credenciais do proxy {proxy_name} não encontradas!")
            continue

        # Buscar tokens
        tokens = get_tokens(channel_id)
        if not tokens:
            log.error(f"[{channel_name}] Sem tokens cadastrados!")
            continue

        # Renovar access_token
        access_token = refresh_access_token(
            tokens["refresh_token"],
            credentials["client_id"],
            credentials["client_secret"]
        )
        if not access_token:
            log.error(f"[{channel_name}] Falha ao renovar token!")
            continue

        # Atualizar token no banco
        update_tokens(channel_id, access_token)

        try:
            # COLETAR MÉTRICAS DIÁRIAS (COM RETENÇÃO!)
            daily_rows = collect_daily_metrics(channel_id, access_token, start_date, end_date)
            saved_daily = save_daily_metrics(channel_id, daily_rows)
            log.info(f"[{channel_name}] Métricas diárias: {saved_daily} dias salvos (incluindo retenção)")
            total_saved += saved_daily

            # Verificar se temos retenção nos dados
            if daily_rows and len(daily_rows[0]) > 10:
                sample_retention = float(daily_rows[0][10]) if daily_rows[0][10] else 0
                sample_ctr = float(daily_rows[0][11]) if len(daily_rows[0]) > 11 and daily_rows[0][11] else 0
                log.info(f"[{channel_name}] ✅ Retenção média: {sample_retention:.1f}% | CTR: {sample_ctr:.2f}%")

            # COLETAR MÉTRICAS POR VÍDEO (TOP 50 com retenção)
            video_rows = collect_video_metrics(channel_id, access_token, start_date, end_date)
            saved_video = save_video_metrics(channel_id, video_rows)
            log.info(f"[{channel_name}] Métricas por vídeo: {saved_video} vídeos salvos")
            total_video_saved += saved_video

            # Salvar snapshot diário dos vídeos
            today = datetime.now().strftime("%Y-%m-%d")
            saved_video_daily = save_video_daily(channel_id, video_rows, today)
            log.info(f"[{channel_name}] Histórico diário vídeos: {saved_video_daily} registros")

            # Atualizar info do canal
            update_channel_info(channel_id, access_token)

            # Log de sucesso
            log_collection(channel_id, "success", f"Histórico completo: {saved_daily} dias, {saved_video} vídeos com retenção")

        except Exception as e:
            log.error(f"[{channel_name}] Erro: {str(e)}")
            log_collection(channel_id, "error", str(e)[:200])

    log.info("\n" + "=" * 60)
    log.info("COLETA HISTÓRICA FINALIZADA")
    log.info(f"Total salvos: {total_saved} registros diários")
    log.info(f"Total vídeos: {total_video_saved} com métricas de retenção")
    log.info("=" * 60)

    # Verificar se salvamos retenção
    log.info("\nVERIFICANDO DADOS DE RETENÇÃO...")

    # Buscar um registro recente para verificar
    import requests
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
        params={
            "select": "date,channel_id,average_view_percentage,card_click_rate",
            "order": "date.desc",
            "limit": "5"
        },
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )

    if resp.status_code == 200 and resp.json():
        log.info("AMOSTRA DOS DADOS SALVOS:")
        for row in resp.json():
            retention = row.get("average_view_percentage", 0)
            ctr = row.get("card_click_rate", 0)
            log.info(f"  {row['date']}: Retenção={retention:.1f}% | CTR={ctr:.2f}%")
    else:
        log.warning("Não foi possível verificar os dados salvos")

if __name__ == "__main__":
    main_historico()