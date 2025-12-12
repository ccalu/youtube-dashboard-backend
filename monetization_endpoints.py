"""
Endpoints da API de Monetização
8 endpoints para fornecer dados ao frontend Lovable
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta, date
from database import SupabaseClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monetization", tags=["monetization"])
db = SupabaseClient()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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
    period: str = Query("total", regex="^(24h|3d|7d|15d|30d|total)$"),
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

        if period == "24h":
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

        # Buscar canais monetizados
        channels_response = db.supabase.table("yt_channels")\
            .select("channel_id")\
            .eq("is_monetized", True)\
            .execute()

        total_monetized_channels = len(channels_response.data) if channels_response.data else 0

        # Buscar métricas do período
        query = db.supabase.table("yt_daily_metrics")\
            .select("revenue, views, channel_id, is_estimate")\
            .gte("date", start_date)

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
        if period == "total":
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
    period: str = Query("total", regex="^(24h|3d|7d|15d|30d|total)$"),
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

            # Calcular start_date baseado no period
            today = datetime.now().date()

            if period == "total":
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

            # Buscar todas as metricas do periodo
            metrics_query = db.supabase.table("yt_daily_metrics")\
                .select("date, revenue, views, is_estimate")\
                .eq("channel_id", channel_id)\
                .gte("date", start_date)\
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
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total)$"),
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
            if period == "total":
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
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total)$")
):
    """
    Retorna Top 3 canais por RPM e Revenue
    """
    try:
        # Calcular data de início baseado no período
        today = datetime.now().date()

        if period == "total":
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
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total)$")
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
    period: str = Query("7d", regex="^(24h|3d|7d|15d|30d|total)$")
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

        # Buscar dados estimados de hoje
        estimate_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .eq("date", today.isoformat())\
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

        return {
            "real": {
                "date": last_real_date,
                "date_formatted": real_date_formatted,
                "revenue": round(real_revenue, 2),
                "badge": "real"
            },
            "estimate": {
                "date": today.isoformat(),
                "date_formatted": today_formatted,
                "revenue": round(estimate_revenue, 2),
                "badge": "estimate"
            }
        }

    except Exception as e:
        logger.error(f"Erro em /revenue-24h: {e}")
        raise HTTPException(status_code=500, detail=str(e))
