"""
Endpoints da API de Monetização
8 endpoints para fornecer dados ao frontend Lovable
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from database import SupabaseClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monetization", tags=["monetization"])
db = SupabaseClient()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_monetization_period(reference_date: date = None):
    """
    Calcula período de monetização do YouTube (dia 13 a dia 13)
    YouTube paga no dia 13 de cada mês referente ao período anterior

    Regras:
    - Se hoje < dia 13: período é do dia 13 de 2 meses atrás até dia 12 do mês passado
    - Se hoje >= dia 13: período é do dia 13 do mês passado até dia 12 do mês atual

    Exemplos:
    - 10/12/2025 → 13/10/2025 até 12/11/2025 (pagamento já recebido em 13/11)
    - 15/12/2025 → 13/11/2025 até 12/12/2025 (pagamento será em 13/01/2026)
    """
    if reference_date is None:
        reference_date = datetime.now().date()

    current_day = reference_date.day

    if current_day < 13:
        # Antes do dia 13: mostra período do pagamento anterior (já recebido)
        end_date = (reference_date - relativedelta(months=1)).replace(day=12)
        start_date = (reference_date - relativedelta(months=2)).replace(day=13)
    else:
        # Dia 13 ou depois: mostra período do próximo pagamento
        end_date = reference_date.replace(day=12)
        start_date = (reference_date - relativedelta(months=1)).replace(day=13)

    return start_date.isoformat(), end_date.isoformat()

def calculate_channel_rpm(channel_id: str, days: int = 30) -> float:
    """Calcula RPM médio do canal baseado apenas em dados reais"""
    try:
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()

        response = db.supabase.table("yt_daily_metrics")\
            .select("revenue, views")\
            .eq("channel_id", channel_id)\
            .eq("is_estimate", False)\
            .gte("date", cutoff_date)\
            .execute()

        if not response.data:
            return 0.0

        total_revenue = sum(r.get('revenue', 0) or 0 for r in response.data)
        total_views = sum(r.get('views', 0) or 0 for r in response.data)

        if total_views == 0:
            return 0.0

        return round((total_revenue / total_views) * 1000, 2)

    except Exception as e:
        logger.error(f"Erro ao calcular RPM: {e}")
        return 0.0

def get_growth_rate(channel_id: str, days: int = 7) -> float:
    """Calcula taxa de crescimento (últimos N dias vs N dias anteriores)"""
    try:
        today = datetime.now().date()
        period1_start = (today - timedelta(days=days)).isoformat()
        period1_end = today.isoformat()
        period2_start = (today - timedelta(days=days*2)).isoformat()
        period2_end = period1_start

        # Período atual
        response1 = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .eq("channel_id", channel_id)\
            .gte("date", period1_start)\
            .lte("date", period1_end)\
            .execute()

        # Período anterior
        response2 = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .eq("channel_id", channel_id)\
            .gte("date", period2_start)\
            .lt("date", period2_end)\
            .execute()

        revenue1 = sum(r.get('revenue', 0) or 0 for r in (response1.data or []))
        revenue2 = sum(r.get('revenue', 0) or 0 for r in (response2.data or []))

        if revenue2 == 0:
            return 0.0

        return round(((revenue1 - revenue2) / revenue2) * 100, 1)

    except Exception as e:
        logger.error(f"Erro ao calcular growth rate: {e}")
        return 0.0

# =============================================================================
# ENDPOINT 1: SUMMARY (Cards Principais)
# =============================================================================

@router.get("/summary")
async def get_monetization_summary(
    period: str = Query("total", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$"),
    month: Optional[str] = Query(None, regex="^\\d{4}-\\d{2}$"),  # Formato YYYY-MM
    type_filter: str = Query("real_estimate", regex="^(real_estimate|real_only)$")
):
    """
    Retorna dados para os 4 cards principais
    - Total de canais monetizados
    - Média diária + taxa de crescimento
    - RPM médio
    - Revenue total
    """
    try:
        # Determinar período
        today = datetime.now().date()

        # Se month foi fornecido, usar lógica específica para mês
        if month:
            year, month_num = map(int, month.split('-'))
            # Primeiro dia do mês
            month_start = date(year, month_num, 1)
            # Último dia do mês
            if month_num == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month_num + 1, 1) - timedelta(days=1)

            # Se o mês for o atual, usar hoje como fim
            if month_end > today:
                month_end = today

            start_date = month_start.isoformat()
            end_date = month_end.isoformat()
        else:
            # Lógica original baseada em period
            if period == "monetizacao":
                start_date, end_date = calculate_monetization_period()
            elif period == "24h":
                start_date = (today - timedelta(days=1)).isoformat()
            elif period == "3d":
                start_date = (today - timedelta(days=3)).isoformat()
            elif period == "7d":
                start_date = (today - timedelta(days=7)).isoformat()
            elif period == "15d":
                start_date = (today - timedelta(days=15)).isoformat()
            elif period == "30d":
                start_date = (today - timedelta(days=30)).isoformat()
            else:  # total
                start_date = "2025-10-26"  # Início da monetização

            end_date = today.isoformat()

        # Buscar canais monetizados
        channels_response = db.supabase.table("yt_channels")\
            .select("channel_id")\
            .eq("is_monetized", True)\
            .execute()

        total_monetized_channels = len(channels_response.data) if channels_response.data else 0

        # Buscar métricas do período
        query = db.supabase.table("yt_daily_metrics")\
            .select("revenue, views, channel_id, is_estimate")\
            .gte("date", start_date)\
            .lte("date", end_date)

        if type_filter == "real_only":
            query = query.eq("is_estimate", False)

        metrics_response = query.execute()
        metrics = metrics_response.data or []

        # Calcular totais
        total_revenue = sum(m.get('revenue', 0) or 0 for m in metrics)
        total_views = sum(m.get('views', 0) or 0 for m in metrics)

        # Calcular RPM médio (só dados reais)
        real_metrics = [m for m in metrics if not m.get('is_estimate', False)]
        total_revenue_real = sum(m.get('revenue', 0) or 0 for m in real_metrics)
        total_views_real = sum(m.get('views', 0) or 0 for m in real_metrics)

        rpm_avg = round((total_revenue_real / total_views_real) * 1000, 2) if total_views_real > 0 else 0.0

        # Calcular média diária
        if month:
            # Para mês específico, calcular dias no período
            month_start = date.fromisoformat(start_date)
            month_end = date.fromisoformat(end_date)
            days_count = (month_end - month_start).days + 1
        elif period == "total":
            days_count = (today - date.fromisoformat("2025-10-26")).days + 1
        elif period == "24h":
            days_count = 1
        elif period == "3d":
            days_count = 3
        elif period == "7d":
            days_count = 7
        elif period == "15d":
            days_count = 15
        else:  # 30d
            days_count = 30

        daily_avg = round(total_revenue / days_count, 2) if days_count > 0 else 0.0

        # Calcular taxa de crescimento (últimos 7 dias vs 7 anteriores)
        growth_rate = 0.0

        if period in ["7d", "15d", "30d", "total"]:
            # Período atual (últimos 7 dias)
            current_start = (today - timedelta(days=7)).isoformat()
            current_metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue")\
                .gte("date", current_start)\
                .execute()

            # Período anterior (7 dias antes)
            previous_start = (today - timedelta(days=14)).isoformat()
            previous_end = current_start
            previous_metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue")\
                .gte("date", previous_start)\
                .lt("date", previous_end)\
                .execute()

            current_revenue = sum(m.get('revenue', 0) or 0 for m in (current_metrics.data or []))
            previous_revenue = sum(m.get('revenue', 0) or 0 for m in (previous_metrics.data or []))

            if previous_revenue > 0:
                growth_rate = round(((current_revenue - previous_revenue) / previous_revenue) * 100, 1)

        return {
            "period_filter": period,
            "type_filter": type_filter,
            "total_monetized_channels": total_monetized_channels,
            "daily_avg": {
                "revenue": daily_avg,
                "growth_rate": growth_rate,
                "trend": "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable"
            },
            "rpm_avg": rpm_avg,
            "total_revenue": round(total_revenue, 2)
        }

    except Exception as e:
        logger.error(f"Erro em /summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 2: CHANNELS (Lista de Canais por Subnicho)
# =============================================================================

@router.get("/channels")
async def get_monetization_channels(
    period: str = Query("total", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$"),
    month: Optional[str] = Query(None, regex="^\\d{4}-\\d{2}$"),  # Formato YYYY-MM
    language: Optional[str] = None,
    subnicho: Optional[str] = None,
    type_filter: str = Query("real_estimate", regex="^(real_estimate|real_only)$")
):
    """
    Retorna lista de canais agrupados por subnicho
    Mostra últimos 3 dias para cada canal
    """
    try:
        # Buscar canais monetizados
        channels_query = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name")\
            .eq("is_monetized", True)

        channels_response = channels_query.execute()
        channels = channels_response.data or []

        # Para cada canal, buscar dados dos últimos 3 dias + subnicho/língua
        result_by_subnicho = {}

        for channel in channels:
            channel_id = channel['channel_id']
            channel_name = channel['channel_name']

            # Buscar subnicho/língua em canais_monitorados
            canal_info_response = db.supabase.table("canais_monitorados")\
                .select("subnicho, lingua")\
                .ilike("nome_canal", f"%{channel_name}%")\
                .limit(1)\
                .execute()

            if not canal_info_response.data:
                continue

            canal_info = canal_info_response.data[0]
            canal_subnicho = canal_info.get('subnicho', 'Outros')
            canal_lingua = canal_info.get('lingua', 'N/A')

            # Filtros
            if language and canal_lingua.lower() != language.lower():
                continue

            if subnicho and canal_subnicho.lower() != subnicho.lower():
                continue

            # Calcular start_date e end_date
            today = datetime.now().date()

            # Se month foi fornecido, usar lógica específica para mês
            if month:
                year, month_num = map(int, month.split('-'))
                month_start = date(year, month_num, 1)
                if month_num == 12:
                    month_end = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(year, month_num + 1, 1) - timedelta(days=1)

                if month_end > today:
                    month_end = today

                start_date = month_start.isoformat()
                end_date = month_end.isoformat()
            else:
                # Lógica original baseada em period
                if period == "monetizacao":
                    start_date, end_date = calculate_monetization_period()
                elif period == "total":
                    start_date = "2025-10-26"
                elif period == "24h":
                    start_date = (today - timedelta(days=1)).isoformat()
                elif period == "3d":
                    start_date = (today - timedelta(days=3)).isoformat()
                elif period == "7d":
                    start_date = (today - timedelta(days=7)).isoformat()
                elif period == "15d":
                    start_date = (today - timedelta(days=15)).isoformat()
                else:  # 30d
                    start_date = (today - timedelta(days=30)).isoformat()

                end_date = today.isoformat()

            # Buscar todas as metricas do periodo
            metrics_query = db.supabase.table("yt_daily_metrics")\
                .select("date, revenue, views, is_estimate")\
                .eq("channel_id", channel_id)\
                .gte("date", start_date)\
                .lte("date", end_date)\
                .order("date", desc=True)

            if type_filter == "real_only":
                metrics_query = metrics_query.eq("is_estimate", False)

            metrics_response = metrics_query.execute()
            period_data = metrics_response.data or []

            # Agregar totais do periodo
            total_revenue = 0
            total_views = 0
            has_estimate = False
            last_date = None

            for day in period_data:
                revenue = day.get('revenue', 0) or 0
                views = day.get('views', 0) or 0
                total_revenue += revenue
                total_views += views

                if day.get('is_estimate', False):
                    has_estimate = True

                # Pegar a data mais recente
                if last_date is None or day['date'] > last_date:
                    last_date = day['date']

            # Calcular RPM do periodo
            period_rpm = round((total_revenue / total_views) * 1000, 2) if total_views > 0 else 0.0

            # Formatar data da ultima atualizacao
            date_formatted = "N/A"
            if last_date:
                try:
                    date_obj = date.fromisoformat(last_date)
                    date_formatted = date_obj.strftime("%d/%m")
                except:
                    date_formatted = last_date

            # Determinar badge
            badge = "estimate" if has_estimate else "real"

            # Agrupar por subnicho
            if canal_subnicho not in result_by_subnicho:
                result_by_subnicho[canal_subnicho] = {
                    "name": canal_subnicho,
                    "color": get_subnicho_color(canal_subnicho),
                    "channels": []
                }

            result_by_subnicho[canal_subnicho]["channels"].append({
                "name": channel_name,
                "channel_id": channel_id,
                "language": canal_lingua,
                "period_total": {
                    "revenue": round(total_revenue, 2),
                    "views": total_views,
                    "rpm": period_rpm,
                    "last_update": last_date,
                    "last_update_formatted": date_formatted,
                    "badge": badge
                }
            })

        # Converter para lista
        subnichos = list(result_by_subnicho.values())

        return {
            "period_filter": period,
            "language_filter": language,
            "subnicho_filter": subnicho,
            "type_filter": type_filter,
            "subnichos": subnichos
        }

    except Exception as e:
        logger.error(f"Erro em /channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_subnicho_color(subnicho: str) -> str:
    """Retorna cor para o subnicho"""
    colors = {
        "Terror": "#8B0000",
        "Relatos de Guerra": "#2F4F4F",
        "Histórias Aleatórias": "#4B0082",
        "Historias Sombrias": "#1C1C1C",
        "Contos Familiares": "#556B2F"
    }

    return colors.get(subnicho, "#696969")

# =============================================================================
# ENDPOINT 3: CHANNEL HISTORY (Histórico Completo de um Canal)
# =============================================================================

@router.get("/channel/{channel_id}/history")
async def get_channel_history(channel_id: str):
    """
    Retorna histórico completo de um canal específico
    Usado no modal "Ver Histórico"
    Mostra APENAS dados reais (não estimados)
    """
    try:
        # Buscar nome do canal
        channel_response = db.supabase.table("yt_channels")\
            .select("channel_name, monetization_start_date")\
            .eq("channel_id", channel_id)\
            .limit(1)\
            .execute()

        if not channel_response.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        channel_info = channel_response.data[0]
        channel_name = channel_info['channel_name']
        monetization_start = channel_info.get('monetization_start_date', '2025-10-26')

        # Buscar histórico completo (só dados reais)
        history_response = db.supabase.table("yt_daily_metrics")\
            .select("date, revenue, views, rpm")\
            .eq("channel_id", channel_id)\
            .eq("is_estimate", False)\
            .order("date", desc=True)\
            .execute()

        history = history_response.data or []

        # Calcular totais
        total_revenue_real = sum(h.get('revenue', 0) or 0 for h in history)
        rpm_avg = calculate_channel_rpm(channel_id, days=999)  # Todo histórico

        # Calcular dias monetizados
        today = datetime.now().date()
        start_date = date.fromisoformat(monetization_start)
        days_monetized = (today - start_date).days + 1

        return {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "monetization_start": monetization_start,
            "days_monetized": days_monetized,
            "total_revenue_real": round(total_revenue_real, 2),
            "rpm_avg": rpm_avg,
            "history": [
                {
                    "date": h['date'],
                    "revenue": round(h.get('revenue', 0) or 0, 2),
                    "views": h.get('views', 0) or 0,
                    "rpm": round(h.get('rpm', 0) or 0, 2),
                    "status": "real"
                }
                for h in history
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em /channel/history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 4: ANALYTICS (Card Analytics)
# =============================================================================

@router.get("/analytics")
async def get_monetization_analytics(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$"),
    month: Optional[str] = Query(None, regex="^\\d{4}-\\d{2}$"),  # Formato YYYY-MM
    language: Optional[str] = None,
    subnicho: Optional[str] = None
):
    """
    Retorna dados para o card Analytics
    - Projecao mensal
    - Comparacao periodos (dinâmica baseada no período ou mês)
    - Melhor/pior dia especifico do periodo
    - Retencao, tempo medio, CTR
    """
    try:
        today = datetime.now().date()

        # Se month foi fornecido, usar lógica específica para mês
        if month:
            year, month_num = map(int, month.split('-'))
            # Primeiro dia do mês
            month_start = date(year, month_num, 1)
            # Último dia do mês (próximo mês - 1 dia)
            if month_num == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month_num + 1, 1) - timedelta(days=1)

            # Se o mês for o atual, usar hoje como fim
            if month_end > today:
                month_end = today

            cutoff_date = month_start.isoformat()
            end_date = month_end.isoformat()

            # Para comparison_period quando month é usado
            # Comparar com o mês anterior
            if month_num == 1:
                prev_month_start = date(year - 1, 12, 1)
                prev_month_end = date(year, 1, 1) - timedelta(days=1)
            else:
                prev_month_start = date(year, month_num - 1, 1)
                prev_month_end = month_start - timedelta(days=1)

            comparison_start = prev_month_start.isoformat()
            comparison_end = prev_month_end.isoformat()

        else:
            # Lógica original baseada em period
            if period == "monetizacao":
                start_date, end_date = calculate_monetization_period()
            elif period == "total":
                cutoff_date = "2025-10-26"
                end_date = today.isoformat()
                # Para total, não há comparação de período
                comparison_start = None
                comparison_end = None
            elif period == "24h":
                cutoff_date = (today - timedelta(days=1)).isoformat()
                end_date = today.isoformat()
                comparison_start = (today - timedelta(days=2)).isoformat()
                comparison_end = (today - timedelta(days=1)).isoformat()
            elif period == "3d":
                cutoff_date = (today - timedelta(days=3)).isoformat()
                end_date = today.isoformat()
                comparison_start = (today - timedelta(days=6)).isoformat()
                comparison_end = (today - timedelta(days=3)).isoformat()
            elif period == "7d":
                cutoff_date = (today - timedelta(days=7)).isoformat()
                end_date = today.isoformat()
                comparison_start = (today - timedelta(days=14)).isoformat()
                comparison_end = (today - timedelta(days=7)).isoformat()
            elif period == "15d":
                cutoff_date = (today - timedelta(days=15)).isoformat()
                end_date = today.isoformat()
                comparison_start = (today - timedelta(days=30)).isoformat()
                comparison_end = (today - timedelta(days=15)).isoformat()
            else:  # 30d
                cutoff_date = (today - timedelta(days=30)).isoformat()
                end_date = today.isoformat()
                comparison_start = (today - timedelta(days=60)).isoformat()
                comparison_end = (today - timedelta(days=30)).isoformat()

        # Métricas do período atual
        current_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue, views, avg_retention_pct, avg_view_duration_sec, ctr_approx")\
            .gte("date", cutoff_date)\
            .lte("date", end_date)\
            .execute()

        current_data = current_metrics.data or []
        current_revenue = sum(m.get('revenue', 0) or 0 for m in current_data)

        # Métricas do período de comparação (se aplicável)
        previous_revenue = 0
        growth_pct = 0.0

        if comparison_start and comparison_end:
            previous_metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue")\
                .gte("date", comparison_start)\
                .lte("date", comparison_end)\
                .execute()

            previous_data = previous_metrics.data or []
            previous_revenue = sum(m.get('revenue', 0) or 0 for m in previous_data)

            # Calcular crescimento
            if previous_revenue > 0:
                growth_pct = round(((current_revenue - previous_revenue) / previous_revenue) * 100, 1)

        # Sempre calcular comparison_7d como fallback
        seven_days_ago = (today - timedelta(days=7)).isoformat()
        fourteen_days_ago = (today - timedelta(days=14)).isoformat()

        seven_day_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .gte("date", seven_days_ago)\
            .execute()
        seven_day_revenue = sum(m.get('revenue', 0) or 0 for m in (seven_day_metrics.data or []))

        seven_day_prev_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .gte("date", fourteen_days_ago)\
            .lt("date", seven_days_ago)\
            .execute()
        seven_day_prev_revenue = sum(m.get('revenue', 0) or 0 for m in (seven_day_prev_metrics.data or []))

        seven_day_growth = round(((seven_day_revenue - seven_day_prev_revenue) / seven_day_prev_revenue) * 100, 1) if seven_day_prev_revenue > 0 else 0.0

        # Projecao mensal
        if month:
            # Se estamos visualizando um mês específico, projetar com base nesse mês
            days_in_month = (month_end - month_start).days + 1
            days_passed = (min(month_end, today) - month_start).days + 1
            if days_passed > 0:
                daily_avg = current_revenue / days_passed
                projection_monthly = round(daily_avg * days_in_month, 2)
            else:
                projection_monthly = 0
        else:
            # Projeção baseada nos últimos 7 dias
            projection_monthly = round(seven_day_revenue * 4.3, 2)

        # Calcular crescimento mensal
        thirty_days_ago = (today - timedelta(days=30)).isoformat()
        last_month_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .gte("date", thirty_days_ago)\
            .execute()

        last_month_revenue = sum(m.get('revenue', 0) or 0 for m in (last_month_metrics.data or []))
        growth_vs_last_month = round(((projection_monthly - last_month_revenue) / last_month_revenue) * 100, 1) if last_month_revenue > 0 else 0.0

        # Melhor/pior dia especifico baseado no periodo e filtros
        best_day, worst_day = analyze_best_worst_days(cutoff_date, language, subnicho)

        # Métricas de analytics (média do período selecionado)
        analytics_metrics = db.supabase.table("yt_daily_metrics")\
            .select("avg_retention_pct, avg_view_duration_sec, ctr_approx")\
            .gte("date", cutoff_date)\
            .lte("date", end_date)\
            .execute()

        analytics_data = analytics_metrics.data or []

        # Filtrar valores não nulos e calcular médias
        retention_values = [m['avg_retention_pct'] for m in analytics_data if m.get('avg_retention_pct')]
        duration_values = [m['avg_view_duration_sec'] for m in analytics_data if m.get('avg_view_duration_sec')]
        ctr_values = [m['ctr_approx'] for m in analytics_data if m.get('ctr_approx')]

        avg_retention = round(sum(retention_values) / len(retention_values), 1) if retention_values else None
        avg_duration = round(sum(duration_values) / len(duration_values)) if duration_values else None
        avg_ctr = round(sum(ctr_values) / len(ctr_values), 2) if ctr_values else None

        return {
            "projection_monthly": {
                "value": projection_monthly,
                "growth_vs_last_month": growth_vs_last_month
            },
            "comparison_period": {
                "current_period_revenue": round(current_revenue, 2),
                "previous_period_revenue": round(previous_revenue, 2),
                "growth_pct": growth_pct,
                "period": month if month else period
            },
            "comparison_7d": {
                "current_period_revenue": round(seven_day_revenue, 2),
                "previous_period_revenue": round(seven_day_prev_revenue, 2),
                "growth_pct": seven_day_growth
            },
            "best_day": best_day,
            "worst_day": worst_day,
            "avg_retention_pct": avg_retention,
            "avg_view_duration_sec": avg_duration,
            "ctr_approx": avg_ctr
        }

    except Exception as e:
        logger.error(f"Erro em /analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def analyze_best_worst_days(cutoff_date: str, language: Optional[str] = None, subnicho: Optional[str] = None):
    """Analisa melhor e pior dia especifico do periodo com revenue total"""
    try:
        # Buscar metricas do periodo filtrado
        query = db.supabase.table("yt_daily_metrics")\
            .select("date, revenue, channel_id")\
            .gte("date", cutoff_date)

        metrics = query.execute()
        data = metrics.data or []

        if not data:
            return {"date": "N/A", "revenue": 0}, {"date": "N/A", "revenue": 0}

        # Se houver filtros de lingua/subnicho, precisamos filtrar canais
        if language or subnicho:
            channels_query = db.supabase.table("yt_channels")\
                .select("channel_id, channel_name")\
                .eq("is_monetized", True)

            channels = channels_query.execute().data or []
            filtered_channel_ids = []

            for ch in channels:
                info = db.supabase.table("canais_monitorados")\
                    .select("subnicho, lingua")\
                    .ilike("nome_canal", f"%{ch['channel_name']}%")\
                    .limit(1)\
                    .execute()

                if info.data:
                    canal_info = info.data[0]
                    canal_lingua = canal_info.get('lingua', '')
                    canal_subnicho = canal_info.get('subnicho', '')

                    if language and canal_lingua.lower() != language.lower():
                        continue
                    if subnicho and canal_subnicho.lower() != subnicho.lower():
                        continue

                    filtered_channel_ids.append(ch['channel_id'])

            data = [m for m in data if m['channel_id'] in filtered_channel_ids]

        # Agrupar revenue por data
        revenue_by_date = {}

        for item in data:
            day_date = item['date']
            revenue = item.get('revenue', 0) or 0

            if day_date not in revenue_by_date:
                revenue_by_date[day_date] = 0

            revenue_by_date[day_date] += revenue

        if not revenue_by_date:
            return {"date": "N/A", "revenue": 0}, {"date": "N/A", "revenue": 0}

        # Encontrar melhor e pior dia
        best_date = max(revenue_by_date, key=revenue_by_date.get)
        worst_date = min(revenue_by_date, key=revenue_by_date.get)

        return {
            "date": best_date,
            "revenue": round(revenue_by_date[best_date], 2)
        }, {
            "date": worst_date,
            "revenue": round(revenue_by_date[worst_date], 2)
        }

    except Exception as e:
        logger.error(f"Erro ao analisar dias: {e}")
        return {"date": "N/A", "revenue": 0}, {"date": "N/A", "revenue": 0}

# =============================================================================
# ENDPOINT 5: TOP PERFORMERS
# =============================================================================

@router.get("/top-performers")
async def get_top_performers(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$"),
    month: Optional[str] = Query(None, regex="^\\d{4}-\\d{2}$")  # Formato YYYY-MM
):
    """
    Retorna Top 3 canais por RPM e Revenue
    """
    try:
        # Calcular data de início baseado no período
        today = datetime.now().date()

        # Se month foi fornecido, usar lógica específica para mês
        if month:
            year, month_num = map(int, month.split('-'))
            month_start = date(year, month_num, 1)
            if month_num == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month_num + 1, 1) - timedelta(days=1)

            if month_end > today:
                month_end = today

            cutoff_date = month_start.isoformat()
            end_date = month_end.isoformat()
        else:
            # Lógica original baseada em period
            if period == "monetizacao":
                start_date, end_date = calculate_monetization_period()
            elif period == "total":
                cutoff_date = "2025-10-26"  # Início da monetização
            elif period == "24h":
                cutoff_date = (today - timedelta(days=1)).isoformat()
            elif period == "3d":
                cutoff_date = (today - timedelta(days=3)).isoformat()
            elif period == "7d":
                cutoff_date = (today - timedelta(days=7)).isoformat()
            elif period == "15d":
                cutoff_date = (today - timedelta(days=15)).isoformat()
            else:  # 30d
                cutoff_date = (today - timedelta(days=30)).isoformat()

            end_date = today.isoformat()

        # Buscar canais monetizados
        channels = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name")\
            .eq("is_monetized", True)\
            .execute()

        channels_data = channels.data or []

        # Para cada canal, calcular RPM e Revenue
        channel_stats = []

        for channel in channels_data:
            channel_id = channel['channel_id']
            channel_name = channel['channel_name']

            # Métricas do período
            metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue, views")\
                .eq("channel_id", channel_id)\
                .eq("is_estimate", False)\
                .gte("date", cutoff_date)\
                .lte("date", end_date)\
                .execute()

            data = metrics.data or []

            total_revenue = sum(m.get('revenue', 0) or 0 for m in data)
            total_views = sum(m.get('views', 0) or 0 for m in data)

            rpm = round((total_revenue / total_views) * 1000, 2) if total_views > 0 else 0.0

            channel_stats.append({
                "name": channel_name,
                "rpm": rpm,
                "revenue": round(total_revenue, 2)
            })

        # Top 3 por RPM
        top_rpm = sorted(channel_stats, key=lambda x: x['rpm'], reverse=True)[:3]

        # Top 3 por Revenue
        top_revenue = sorted(channel_stats, key=lambda x: x['revenue'], reverse=True)[:3]

        return {
            "period_filter": period,
            "top_rpm": [
                {
                    "channel_id": "",
                    "channel_name": c['name'],
                    "avg_rpm": c['rpm'],
                    "total_revenue": c['revenue']
                } for c in top_rpm
            ],
            "top_revenue": [
                {
                    "channel_id": "",
                    "channel_name": c['name'],
                    "total_revenue": c['revenue'],
                    "avg_rpm": c['rpm']
                } for c in top_revenue
            ]
        }

    except Exception as e:
        logger.error(f"Erro em /top-performers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 6: BY LANGUAGE
# =============================================================================

@router.get("/by-language")
async def get_monetization_by_language(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$")
):
    """
    Análise por língua: RPM, Views, Revenue
    """
    try:
        # Calcular data de início baseado no período
        today = datetime.now().date()

        if period == "total":
            cutoff_date = "2025-10-26"
        elif period == "24h":
            cutoff_date = (today - timedelta(days=1)).isoformat()
        elif period == "3d":
            cutoff_date = (today - timedelta(days=3)).isoformat()
        elif period == "7d":
            cutoff_date = (today - timedelta(days=7)).isoformat()
        elif period == "15d":
            cutoff_date = (today - timedelta(days=15)).isoformat()
        else:  # 30d
            cutoff_date = (today - timedelta(days=30)).isoformat()

        # Buscar todos os canais monetizados com língua
        channels = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name")\
            .eq("is_monetized", True)\
            .execute()

        channels_data = channels.data or []

        # Agrupar por língua
        by_language = {}

        for channel in channels_data:
            channel_id = channel['channel_id']
            channel_name = channel['channel_name']

            # Buscar língua
            canal_info = db.supabase.table("canais_monitorados")\
                .select("lingua")\
                .ilike("nome_canal", f"%{channel_name}%")\
                .limit(1)\
                .execute()

            if not canal_info.data:
                continue

            lingua = canal_info.data[0].get('lingua', 'N/A')

            # Buscar métricas
            metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue, views")\
                .eq("channel_id", channel_id)\
                .gte("date", cutoff_date)\
                .execute()

            data = metrics.data or []

            revenue = sum(m.get('revenue', 0) or 0 for m in data)
            views = sum(m.get('views', 0) or 0 for m in data)

            if lingua not in by_language:
                by_language[lingua] = {
                    "language": lingua,
                    "revenue": 0,
                    "views": 0,
                    "channels_count": 0
                }

            by_language[lingua]["revenue"] += revenue
            by_language[lingua]["views"] += views
            by_language[lingua]["channels_count"] += 1

        # Calcular RPM por língua
        for lang_data in by_language.values():
            if lang_data["views"] > 0:
                lang_data["rpm_avg"] = round((lang_data["revenue"] / lang_data["views"]) * 1000, 2)
            else:
                lang_data["rpm_avg"] = 0.0

            lang_data["revenue"] = round(lang_data["revenue"], 2)

        return {
            "period_filter": period,
            "languages": list(by_language.values())
        }

    except Exception as e:
        logger.error(f"Erro em /by-language: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 7: BY SUBNICHO
# =============================================================================

@router.get("/by-subnicho")
async def get_monetization_by_subnicho(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$")
):
    """
    Análise por subnicho: RPM, Views, Revenue
    """
    try:
        # Calcular data de início baseado no período
        today = datetime.now().date()

        if period == "total":
            cutoff_date = "2025-10-26"
        elif period == "24h":
            cutoff_date = (today - timedelta(days=1)).isoformat()
        elif period == "3d":
            cutoff_date = (today - timedelta(days=3)).isoformat()
        elif period == "7d":
            cutoff_date = (today - timedelta(days=7)).isoformat()
        elif period == "15d":
            cutoff_date = (today - timedelta(days=15)).isoformat()
        else:  # 30d
            cutoff_date = (today - timedelta(days=30)).isoformat()

        # Similar ao by-language, mas agrupa por subnicho
        channels = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name")\
            .eq("is_monetized", True)\
            .execute()

        channels_data = channels.data or []

        by_subnicho = {}

        for channel in channels_data:
            channel_id = channel['channel_id']
            channel_name = channel['channel_name']

            # Buscar subnicho
            canal_info = db.supabase.table("canais_monitorados")\
                .select("subnicho")\
                .ilike("nome_canal", f"%{channel_name}%")\
                .limit(1)\
                .execute()

            if not canal_info.data:
                continue

            subnicho = canal_info.data[0].get('subnicho', 'Outros')

            # Buscar métricas
            metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue, views")\
                .eq("channel_id", channel_id)\
                .gte("date", cutoff_date)\
                .execute()

            data = metrics.data or []

            revenue = sum(m.get('revenue', 0) or 0 for m in data)
            views = sum(m.get('views', 0) or 0 for m in data)

            if subnicho not in by_subnicho:
                by_subnicho[subnicho] = {
                    "subnicho": subnicho,
                    "revenue": 0,
                    "views": 0,
                    "channels_count": 0
                }

            by_subnicho[subnicho]["revenue"] += revenue
            by_subnicho[subnicho]["views"] += views
            by_subnicho[subnicho]["channels_count"] += 1

        # Calcular RPM por subnicho
        for sub_data in by_subnicho.values():
            if sub_data["views"] > 0:
                sub_data["rpm_avg"] = round((sub_data["revenue"] / sub_data["views"]) * 1000, 2)
            else:
                sub_data["rpm_avg"] = 0.0

            sub_data["revenue"] = round(sub_data["revenue"], 2)

        return {
            "period_filter": period,
            "subnichos": list(by_subnicho.values())
        }

    except Exception as e:
        logger.error(f"Erro em /by-subnicho: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 8: CONFIG (Canais Monetizados Ativos)
# =============================================================================

@router.get("/config")
async def get_monetization_config():
    """
    Retorna lista de canais monetizados ativos com subnicho e lingua
    Usado para filtros dinamicos no frontend
    """
    try:
        # Buscar canais monetizados
        channels = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name, monetization_start_date, is_monetized")\
            .eq("is_monetized", True)\
            .execute()

        channels_data = channels.data or []

        # Para cada canal, buscar subnicho e lingua
        enriched_channels = []

        for channel in channels_data:
            # Buscar dados em canais_monitorados
            canal_info = db.supabase.table("canais_monitorados")\
                .select("subnicho, lingua")\
                .ilike("nome_canal", f"%{channel['channel_name']}%")\
                .limit(1)\
                .execute()

            if canal_info.data:
                enriched_channels.append({
                    "channel_id": channel['channel_id'],
                    "channel_name": channel['channel_name'],
                    "monetization_start_date": channel.get('monetization_start_date'),
                    "subnicho": canal_info.data[0].get('subnicho', 'Outros'),
                    "lingua": canal_info.data[0].get('lingua', 'N/A')
                })

        return {
            "channels": enriched_channels
        }

    except Exception as e:
        logger.error(f"Erro em /config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 9: REVENUE 24H (Resumo últimas 24 horas)
# =============================================================================

@router.get("/revenue-24h")
async def get_revenue_24h():
    """
    Retorna revenue das ultimas 24 horas
    - real: dados coletados (ultima coleta)
    - estimate: estimativa do dia atual
    """
    try:
        today = datetime.now().date()

        # Buscar ultima data com dados reais (is_estimate=false)
        last_real_query = db.supabase.table("yt_daily_metrics")\
            .select("date")\
            .eq("is_estimate", False)\
            .order("date", desc=True)\
            .limit(1)\
            .execute()

        last_real_date = None
        if last_real_query.data:
            last_real_date = last_real_query.data[0]['date']

        # Revenue real (ultima coleta)
        real_revenue = 0
        if last_real_date:
            real_metrics = db.supabase.table("yt_daily_metrics")\
                .select("revenue")\
                .eq("date", last_real_date)\
                .eq("is_estimate", False)\
                .execute()

            for item in real_metrics.data or []:
                real_revenue += item.get('revenue', 0) or 0

        # Buscar dados estimados de ONTEM (D-1)
        yesterday = (today - timedelta(days=1)).isoformat()
        estimate_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .eq("date", yesterday)\
            .eq("is_estimate", True)\
            .execute()

        estimate_revenue = 0
        for item in estimate_metrics.data or []:
            estimate_revenue += item.get('revenue', 0) or 0

        # Formatar datas
        real_date_formatted = "N/A"
        if last_real_date:
            try:
                date_obj = date.fromisoformat(last_real_date)
                real_date_formatted = date_obj.strftime("%d/%m")
            except:
                real_date_formatted = last_real_date

        today_formatted = today.strftime("%d/%m")
        yesterday_formatted = (today - timedelta(days=1)).strftime("%d/%m")

        return {
            "real": {
                "date": last_real_date,
                "date_formatted": real_date_formatted,
                "revenue": round(real_revenue, 2),
                "badge": "real"
            },
            "estimate": {
                "date": yesterday,
                "date_formatted": yesterday_formatted,
                "revenue": round(estimate_revenue, 2),
                "badge": "estimate"
            }
        }

    except Exception as e:
        logger.error(f"Erro em /revenue-24h: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-metrics")
async def get_quality_metrics(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$", description="Período de análise"),
    month: Optional[str] = Query(None, regex="^\\d{4}-\\d{2}$", description="Mês (YYYY-MM)"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)")
):
    """
    Retorna métricas de qualidade (retenção e CTR) agrupadas por subnicho.
    Agora com dados REAIS coletados do YouTube Analytics.
    """
    try:
        today = datetime.now().date()

        # Prioridade 1: Processar parâmetro de mês se fornecido
        if month:
            try:
                # Parse do mês (formato YYYY-MM)
                year, month_num = month.split('-')
                start_date = f"{year}-{month_num}-01"

                # Calcular último dia do mês
                if month_num == "12":
                    next_month = f"{int(year)+1}-01-01"
                else:
                    next_month = f"{year}-{int(month_num)+1:02d}-01"

                end_date = (datetime.strptime(next_month, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

                # Limitar end_date ao dia atual se necessário
                today_str = datetime.now().strftime("%Y-%m-%d")
                if end_date > today_str:
                    end_date = today_str
            except:
                # Fallback para mês atual se houver erro
                today = datetime.now()
                start_date = today.replace(day=1).strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
        # Prioridade 2: Usar datas customizadas se fornecidas
        elif start_date and end_date:
            # Usar as datas fornecidas diretamente
            pass
        # Prioridade 3: Processar período
        else:
            # Calcular datas baseadas no period
            end_date = today.isoformat()

            if period == "monetizacao":
                start_date, end_date = calculate_monetization_period()
            elif period == "total":
                start_date = "2025-10-26"
            elif period == "24h":
                start_date = (today - timedelta(days=1)).isoformat()
            elif period == "3d":
                start_date = (today - timedelta(days=3)).isoformat()
            elif period == "7d":
                start_date = (today - timedelta(days=7)).isoformat()
            elif period == "15d":
                start_date = (today - timedelta(days=15)).isoformat()
            else:  # 30d
                start_date = (today - timedelta(days=30)).isoformat()

        # Buscar canais monetizados (sem subnicho que não existe em yt_channels)
        channels_resp = db.supabase.table("yt_channels")\
            .select("channel_id,channel_name")\
            .eq("is_monetized", True)\
            .execute()

        if not channels_resp.data:
            return {"subnichios": [], "period": {"start": start_date, "end": end_date}}

        # Buscar subnicho de cada canal em canais_monitorados
        subnichios = {}
        for channel in channels_resp.data:
            # Buscar subnicho e lingua em canais_monitorados (mesmo padrão dos outros endpoints)
            subnicho_resp = db.supabase.table("canais_monitorados")\
                .select("subnicho, lingua")\
                .ilike("nome_canal", f"%{channel['channel_name']}%")\
                .limit(1)\
                .execute()

            subnicho = subnicho_resp.data[0]["subnicho"] if subnicho_resp.data else "Outros"
            lingua = subnicho_resp.data[0].get("lingua", "N/A") if subnicho_resp.data else "N/A"

            if subnicho not in subnichios:
                subnichios[subnicho] = []

            channel["subnicho"] = subnicho  # Adicionar subnicho ao channel
            channel["lingua"] = lingua  # Adicionar lingua ao channel
            subnichios[subnicho].append(channel)

        result = []

        for subnicho_name, channels in subnichios.items():
            metrics_data = []

            for channel in channels:
                try:
                    # Buscar métricas REAIS do período incluindo retenção
                    metrics_resp = db.supabase.table("yt_daily_metrics")\
                        .select("views,revenue,avg_retention_pct,avg_view_duration_sec")\
                        .eq("channel_id", channel["channel_id"])\
                        .gte("date", start_date)\
                        .lte("date", end_date)\
                        .execute()

                    if metrics_resp.data and len(metrics_resp.data) > 0:
                        # Calcular médias ponderadas pelos views
                        total_views = sum(m.get("views", 0) for m in metrics_resp.data)
                        total_revenue = sum(m.get("revenue", 0) for m in metrics_resp.data)

                        # Coletar métricas de retenção (ponderar por views)
                        weighted_retention = 0
                        weighted_duration = 0
                        valid_retention_count = 0

                        for metric in metrics_resp.data:
                            views = metric.get("views", 0)
                            if views > 0:
                                # Retenção
                                retention = metric.get("avg_retention_pct")
                                if retention is not None and retention > 0:
                                    weighted_retention += retention * views
                                    valid_retention_count += views

                                # Duração
                                duration = metric.get("avg_view_duration_sec")
                                if duration is not None and duration > 0:
                                    weighted_duration += duration * views

                        # Calcular médias finais
                        avg_retention = (weighted_retention / valid_retention_count) if valid_retention_count > 0 else None
                        avg_duration = (weighted_duration / total_views) if total_views > 0 else None

                        # Se temos dados reais, usar; senão, estimar baseado em RPM
                        if avg_retention is not None:
                            retention = avg_retention
                        else:
                            # Fallback: estimar baseado em RPM se não houver dados
                            if total_views > 0:
                                avg_rpm = (total_revenue / total_views) * 1000
                                retention = min(50, max(15, 20 + avg_rpm * 5))
                            else:
                                retention = 25.0

                        metrics_data.append({
                            "name": channel.get("channel_name", "Unknown"),
                            "channel_id": channel["channel_id"],
                            "language": channel.get("lingua", "N/A"),
                            "retention": round(retention, 1),
                            "avg_duration_sec": round(avg_duration, 0) if avg_duration else None,
                            "total_views": total_views,
                            "performance": "excellent" if retention >= 40 else "good" if retention >= 30 else "medium" if retention >= 20 else "low"
                        })
                except Exception as channel_error:
                    logger.warning(f"Erro ao processar canal {channel.get('channel_id')}: {channel_error}")
                    continue

            if metrics_data:
                # Ordenar canais por retenção
                metrics_data.sort(key=lambda x: x["retention"], reverse=True)

                # Calcular médias do subnicho
                avg_retention = sum(m["retention"] for m in metrics_data) / len(metrics_data) if metrics_data else 0

                result.append({
                    "name": subnicho_name,
                    "channel_count": len(metrics_data),
                    "avg_retention": round(avg_retention, 1),
                    "performance": "excellent" if avg_retention >= 40 else "good" if avg_retention >= 30 else "medium" if avg_retention >= 20 else "low",
                    "channels": metrics_data
                })

        # Ordenar subnichos por retenção
        result.sort(key=lambda x: x.get("avg_retention", 0), reverse=True)

        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "subnichios": result
        }

    except Exception as e:
        logger.error(f"Erro em quality-metrics: {str(e)}")
        return {
            "period": {"start": start_date, "end": end_date},
            "subnichios": [],
            "error": str(e)
        }

# =============================================================================
# ANALYTICS AVANÇADO - NOVO ENDPOINT
# =============================================================================

@router.get("/analytics-advanced")
async def get_advanced_analytics(
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total|monetizacao)$"),
    subnicho: Optional[str] = None,
    channel_id: Optional[str] = None,
    lingua: Optional[str] = None
):
    """
    Retorna analytics avançado com traffic sources, demographics, devices, etc.
    Agrupa por subnicho ou retorna detalhes de canal específico.
    """
    try:
        # Calcular datas baseado no período
        end_date = datetime.now().date()

        if period == "monetizacao":
            # Período de monetização (13 a 13)
            from dateutil.relativedelta import relativedelta
            current_day = end_date.day
            if current_day < 13:
                end_date = (end_date - relativedelta(months=1)).replace(day=12)
                start_date = (end_date - relativedelta(months=1)).replace(day=13)
            else:
                end_date = end_date.replace(day=12)
                start_date = (end_date - relativedelta(months=1)).replace(day=13)
        elif period == "24h":
            start_date = end_date - timedelta(days=1)
        elif period == "3d":
            start_date = end_date - timedelta(days=3)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "15d":
            start_date = end_date - timedelta(days=15)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        else:  # total
            start_date = end_date - timedelta(days=365)

        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        # Se channel_id específico, retornar detalhes do canal
        if channel_id:
            # Traffic Sources
            traffic_query = db.supabase.table("yt_traffic_summary")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .gte("date", start_str)\
                .lte("date", end_str)\
                .order("views", desc=True)
            traffic_data = traffic_query.execute()

            # Search Terms
            search_query = db.supabase.table("yt_search_analytics")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .gte("date", start_str)\
                .lte("date", end_str)\
                .order("views", desc=True)\
                .limit(10)
            search_data = search_query.execute()

            # Suggested Videos
            suggested_query = db.supabase.table("yt_suggested_sources")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .gte("date", start_str)\
                .lte("date", end_str)\
                .order("views_generated", desc=True)\
                .limit(10)
            suggested_data = suggested_query.execute()

            # Demographics
            demo_query = db.supabase.table("yt_demographics")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .gte("date", start_str)\
                .lte("date", end_str)\
                .order("percentage", desc=True)
            demo_data = demo_query.execute()

            # Devices
            device_query = db.supabase.table("yt_device_metrics")\
                .select("*")\
                .eq("channel_id", channel_id)\
                .gte("date", start_str)\
                .lte("date", end_str)\
                .order("views", desc=True)
            device_data = device_query.execute()

            # Buscar info do canal
            channel_info = db.supabase.table("yt_channels")\
                .select("channel_name, performance_score")\
                .eq("channel_id", channel_id)\
                .single()\
                .execute()

            # Buscar subnicho da tabela canais_monitorados
            subnicho_info = None
            if channel_info.data:
                subnicho_resp = db.supabase.table("canais_monitorados")\
                    .select("subnicho")\
                    .ilike("nome_canal", f"%{channel_info.data.get('channel_name')}%")\
                    .limit(1)\
                    .execute()
                if subnicho_resp.data:
                    subnicho_info = subnicho_resp.data[0].get("subnicho")

            # ===================================================================
            # AGREGAR DADOS (múltiplos dias → valores únicos com média/soma)
            # ===================================================================

            # 1. DEMOGRAPHICS - Calcular MÉDIA dos percentuais por age_group/gender
            demo_agg = {}
            for item in (demo_data.data or []):
                key = f"{item['age_group']}_{item['gender']}"
                if key not in demo_agg:
                    demo_agg[key] = []
                demo_agg[key].append(item['percentage'])

            # Calcular médias
            demographics_detailed = [
                {
                    "age_group": key.split('_')[0],
                    "gender": key.split('_')[1],
                    "percentage": round(sum(percentages) / len(percentages), 2)
                }
                for key, percentages in demo_agg.items()
            ]

            # Agrupar POR IDADE (somar masculino + feminino)
            by_age = {}
            for item in demographics_detailed:
                age = item['age_group']
                by_age[age] = by_age.get(age, 0) + item['percentage']

            demographics_by_age = [
                {"age_group": age, "percentage": round(percentage, 2)}
                for age, percentage in sorted(by_age.items(), key=lambda x: x[1], reverse=True)
            ]

            # Agrupar POR GÊNERO (somar todas as idades)
            by_gender = {}
            for item in demographics_detailed:
                gender = item['gender']
                by_gender[gender] = by_gender.get(gender, 0) + item['percentage']

            demographics_by_gender = [
                {"gender": gender, "percentage": round(percentage, 2)}
                for gender, percentage in sorted(by_gender.items(), key=lambda x: x[1], reverse=True)
            ]

            demographics_aggregated = {
                "by_age": demographics_by_age,
                "by_gender": demographics_by_gender
            }

            # 2. TRAFFIC SOURCES - Somar views e recalcular percentuais
            traffic_agg = {}
            for item in (traffic_data.data or []):
                src = item['source_type']
                traffic_agg[src] = traffic_agg.get(src, 0) + item['views']

            # Mapeamento de nomes (tradução)
            SOURCE_NAMES = {
                "SUBSCRIBER": "Recomendados",
                "RELATED_VIDEO": "Vídeos Relacionados",
                "YT_SEARCH": "Busca YouTube",
                "NO_LINK_OTHER": "Outros",
                "YT_CHANNEL": "Página do Canal",
                "YT_OTHER_PAGE": "Outras Páginas",
                "EXT_URL": "Links Externos",
                "PLAYLIST": "Playlists",
                "END_SCREEN": "Tela Final",
                "NOTIFICATION": "Notificações",
                "HASHTAGS": "Hashtags"
            }

            total_traffic_views = sum(traffic_agg.values()) if traffic_agg else 1
            traffic_aggregated = [
                {
                    "source_type": SOURCE_NAMES.get(src, src),
                    "views": views,
                    "percentage": round((views / total_traffic_views) * 100, 2)
                }
                for src, views in sorted(traffic_agg.items(), key=lambda x: x[1], reverse=True)
            ]

            # 3. DEVICE METRICS - Somar views e recalcular percentuais
            device_agg = {}
            for item in (device_data.data or []):
                dev = item['device_type']
                device_agg[dev] = device_agg.get(dev, 0) + item['views']

            total_device_views = sum(device_agg.values()) if device_agg else 1
            devices_aggregated = [
                {
                    "device_type": dev,
                    "views": views,
                    "percentage": round((views / total_device_views) * 100, 2)
                }
                for dev, views in sorted(device_agg.items(), key=lambda x: x[1], reverse=True)
            ]

            # 4. SEARCH TERMS - Somar views por termo (top 10)
            search_agg = {}
            for item in (search_data.data or []):
                term = item['search_term']
                search_agg[term] = search_agg.get(term, 0) + item['views']

            search_aggregated = [
                {
                    "search_term": term,
                    "views": views
                }
                for term, views in sorted(search_agg.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # 5. SUGGESTED VIDEOS - Somar views por vídeo (top 10)
            suggested_agg = {}
            for item in (suggested_data.data or []):
                vid_id = item['source_video_id']
                if vid_id not in suggested_agg:
                    suggested_agg[vid_id] = {
                        'title': item.get('source_video_title', 'Unknown'),
                        'views': 0
                    }
                suggested_agg[vid_id]['views'] += item['views_generated']

            suggested_aggregated = [
                {
                    "source_video_id": vid_id,
                    "source_video_title": data['title'],
                    "views_generated": data['views']
                }
                for vid_id, data in sorted(suggested_agg.items(), key=lambda x: x[1]['views'], reverse=True)[:10]
            ]

            return {
                "channel": {
                    "id": channel_id,
                    "name": channel_info.data.get("channel_name") if channel_info.data else "Unknown",
                    "subnicho": subnicho_info,
                    "performance_score": channel_info.data.get("performance_score") if channel_info.data else 0
                },
                "period": {"start": start_str, "end": end_str},
                "traffic_sources": traffic_aggregated,
                "search_terms": search_aggregated,
                "suggested_videos": suggested_aggregated,
                "demographics": demographics_aggregated,
                "devices": devices_aggregated
            }

        # Senão, retornar agregado por subnicho
        # Buscar canais monetizados
        channels_query = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name")\
            .eq("is_monetized", True)

        if lingua:
            channels_query = channels_query.eq("lingua", lingua)

        channels = channels_query.execute()

        if not channels.data:
            return {
                "period": {"start": start_str, "end": end_str},
                "subnichos": [],
                "message": "Nenhum canal monetizado encontrado"
            }

        # Buscar subnichos da tabela canais_monitorados
        for channel in channels.data:
            subnicho_resp = db.supabase.table("canais_monitorados")\
                .select("subnicho")\
                .ilike("nome_canal", f"%{channel['channel_name']}%")\
                .execute()

            channel['subnicho'] = subnicho_resp.data[0]['subnicho'] if subnicho_resp.data else None

        # Filtrar por subnicho se especificado
        if subnicho:
            channels.data = [c for c in channels.data if c.get('subnicho') and subnicho.lower() in c['subnicho'].lower()]
            if not channels.data:
                return {
                    "period": {"start": start_str, "end": end_str},
                    "subnichos": [],
                    "message": f"Nenhum canal encontrado para o subnicho '{subnicho}'"
                }

        # Agrupar por subnicho
        subnichos_data = {}
        for channel in channels.data:
            subnicho_name = channel.get("subnicho") or "Sem Subnicho"
            if subnicho_name not in subnichos_data:
                subnichos_data[subnicho_name] = {
                    "channels": [],
                    "traffic_sources": {},
                    "search_terms": {},
                    "demographics": {},
                    "devices": {}
                }
            subnichos_data[subnicho_name]["channels"].append(channel)

        # Para cada subnicho, buscar dados agregados
        result = []
        for subnicho_name, subnicho_info in subnichos_data.items():
            channel_ids = [c["channel_id"] for c in subnicho_info["channels"]]

            # Traffic Sources agregado
            traffic_agg = {}
            for cid in channel_ids:
                traffic_resp = db.supabase.table("yt_traffic_summary")\
                    .select("source_type, views")\
                    .eq("channel_id", cid)\
                    .gte("date", start_str)\
                    .lte("date", end_str)\
                    .execute()

                if traffic_resp.data:
                    for item in traffic_resp.data:
                        src = item["source_type"]
                        traffic_agg[src] = traffic_agg.get(src, 0) + item["views"]

            # Top 5 search terms agregado
            search_agg = {}
            for cid in channel_ids:
                search_resp = db.supabase.table("yt_search_analytics")\
                    .select("search_term, views")\
                    .eq("channel_id", cid)\
                    .gte("date", start_str)\
                    .lte("date", end_str)\
                    .execute()

                if search_resp.data:
                    for item in search_resp.data:
                        term = item["search_term"]
                        search_agg[term] = search_agg.get(term, 0) + item["views"]

            # Top 5 search terms
            top_search = sorted(search_agg.items(), key=lambda x: x[1], reverse=True)[:5]

            # Demographics agregado
            demo_agg = {}
            for cid in channel_ids:
                demo_resp = db.supabase.table("yt_demographics")\
                    .select("age_group, gender, percentage")\
                    .eq("channel_id", cid)\
                    .gte("date", start_str)\
                    .lte("date", end_str)\
                    .execute()

                if demo_resp.data:
                    for item in demo_resp.data:
                        key = f"{item['age_group']}_{item['gender']}"
                        if key not in demo_agg:
                            demo_agg[key] = []
                        demo_agg[key].append(item["percentage"])

            # Média de demographics
            demo_avg = {}
            for key, percentages in demo_agg.items():
                demo_avg[key] = round(sum(percentages) / len(percentages), 2)

            # Devices agregado
            device_agg = {}
            for cid in channel_ids:
                device_resp = db.supabase.table("yt_device_metrics")\
                    .select("device_type, views")\
                    .eq("channel_id", cid)\
                    .gte("date", start_str)\
                    .lte("date", end_str)\
                    .execute()

                if device_resp.data:
                    for item in device_resp.data:
                        dev = item["device_type"]
                        device_agg[dev] = device_agg.get(dev, 0) + item["views"]

            # Calcular percentuais
            total_traffic = sum(traffic_agg.values()) if traffic_agg else 1
            total_devices = sum(device_agg.values()) if device_agg else 1

            result.append({
                "subnicho": subnicho_name,
                "channel_count": len(channel_ids),
                "traffic_sources": [
                    {
                        "source": src,
                        "views": views,
                        "percentage": round((views / total_traffic) * 100, 2)
                    }
                    for src, views in sorted(traffic_agg.items(), key=lambda x: x[1], reverse=True)
                ],
                "top_search_terms": [
                    {"term": term, "views": views}
                    for term, views in top_search
                ],
                "demographics": demo_avg,
                "devices": [
                    {
                        "device": dev,
                        "views": views,
                        "percentage": round((views / total_devices) * 100, 2)
                    }
                    for dev, views in sorted(device_agg.items(), key=lambda x: x[1], reverse=True)
                ]
            })

        return {
            "period": {"start": start_str, "end": end_str},
            "subnichos": result
        }

    except Exception as e:
        logger.error(f"Erro em analytics-advanced: {str(e)}")
        return {
            "period": {"start": start_str, "end": end_str},
            "error": str(e)
        }
