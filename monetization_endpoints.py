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

            # Buscar últimos 3 dias
            today = datetime.now().date()
            three_days_ago = (today - timedelta(days=3)).isoformat()

            metrics_query = db.supabase.table("yt_daily_metrics")\
                .select("date, revenue, views, is_estimate")\
                .eq("channel_id", channel_id)\
                .gte("date", three_days_ago)\
                .order("date", desc=True)\
                .limit(3)

            if type_filter == "real_only":
                metrics_query = metrics_query.eq("is_estimate", False)

            metrics_response = metrics_query.execute()
            last_3_days = metrics_response.data or []

            # Calcular RPM médio
            rpm_avg = calculate_channel_rpm(channel_id)

            # Formatar dados
            last_3_days_formatted = []

            for day in last_3_days:
                last_3_days_formatted.append({
                    "date": day['date'],
                    "revenue": round(day.get('revenue', 0) or 0, 2),
                    "views": day.get('views', 0) or 0,
                    "is_estimate": day.get('is_estimate', False),
                    "badge": "estimate" if day.get('is_estimate', False) else "real"
                })

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
                "rpm_avg": rpm_avg,
                "last_3_days": last_3_days_formatted
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
    language: Optional[str] = None,
    subnicho: Optional[str] = None
):
    """
    Retorna dados para o card Analytics
    - Projeção mensal
    - Comparação períodos
    - Melhor/pior dia
    - Retenção, tempo médio, CTR
    """
    try:
        today = datetime.now().date()
        seven_days_ago = (today - timedelta(days=7)).isoformat()
        fourteen_days_ago = (today - timedelta(days=14)).isoformat()

        # Query base
        base_query = db.supabase.table("yt_daily_metrics").select("*")

        # Filtros (se aplicável)
        # TODO: Implementar filtros por língua/subnicho

        # Últimos 7 dias
        current_metrics = base_query.gte("date", seven_days_ago).execute()
        current_data = current_metrics.data or []

        current_revenue = sum(m.get('revenue', 0) or 0 for m in current_data)

        # 7 dias anteriores
        previous_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .gte("date", fourteen_days_ago)\
            .lt("date", seven_days_ago)\
            .execute()

        previous_data = previous_metrics.data or []
        previous_revenue = sum(m.get('revenue', 0) or 0 for m in previous_data)

        # Comparação
        growth_pct = round(((current_revenue - previous_revenue) / previous_revenue) * 100, 1) if previous_revenue > 0 else 0.0

        # Projeção mensal (últimos 7 dias × 4.3)
        projection_monthly = round(current_revenue * 4.3, 2)

        # Calcular crescimento mensal (comparar com mês passado se tiver dados)
        thirty_days_ago = (today - timedelta(days=30)).isoformat()
        last_month_metrics = db.supabase.table("yt_daily_metrics")\
            .select("revenue")\
            .gte("date", thirty_days_ago)\
            .execute()

        last_month_revenue = sum(m.get('revenue', 0) or 0 for m in (last_month_metrics.data or []))
        growth_vs_last_month = round(((projection_monthly - last_month_revenue) / last_month_revenue) * 100, 1) if last_month_revenue > 0 else 0.0

        # Melhor/pior dia da semana (análise histórica)
        best_day, worst_day = analyze_best_worst_days()

        # Métricas de analytics (média de todos os canais)
        analytics_metrics = db.supabase.table("yt_daily_metrics")\
            .select("avg_retention_pct, avg_view_duration_sec, ctr_approx")\
            .gte("date", seven_days_ago)\
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
            "comparison_7d": {
                "current_period_revenue": round(current_revenue, 2),
                "previous_period_revenue": round(previous_revenue, 2),
                "growth_pct": growth_pct
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

def analyze_best_worst_days():
    """Analisa melhor e pior dia da semana baseado em histórico"""
    try:
        # Buscar últimos 30 dias
        thirty_days_ago = (datetime.now().date() - timedelta(days=30)).isoformat()

        metrics = db.supabase.table("yt_daily_metrics")\
            .select("date, revenue")\
            .gte("date", thirty_days_ago)\
            .execute()

        data = metrics.data or []

        # Agrupar por dia da semana
        revenue_by_weekday = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday

        for item in data:
            date_obj = date.fromisoformat(item['date'])
            weekday = date_obj.weekday()
            revenue = item.get('revenue', 0) or 0
            revenue_by_weekday[weekday].append(revenue)

        # Calcular média por dia
        avg_by_weekday = {}
        weekday_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

        for weekday, revenues in revenue_by_weekday.items():
            if revenues:
                avg_by_weekday[weekday] = sum(revenues) / len(revenues)
            else:
                avg_by_weekday[weekday] = 0

        # Encontrar melhor e pior
        if avg_by_weekday:
            best_weekday = max(avg_by_weekday, key=avg_by_weekday.get)
            worst_weekday = min(avg_by_weekday, key=avg_by_weekday.get)

            return {
                "day_of_week": weekday_names[best_weekday],
                "avg_revenue": round(avg_by_weekday[best_weekday], 2)
            }, {
                "day_of_week": weekday_names[worst_weekday],
                "avg_revenue": round(avg_by_weekday[worst_weekday], 2)
            }

        return {"day_of_week": "N/A", "avg_revenue": 0}, {"day_of_week": "N/A", "avg_revenue": 0}

    except Exception as e:
        logger.error(f"Erro ao analisar dias: {e}")
        return {"day_of_week": "N/A", "avg_revenue": 0}, {"day_of_week": "N/A", "avg_revenue": 0}

# =============================================================================
# ENDPOINT 5: TOP PERFORMERS
# =============================================================================

@router.get("/top-performers")
async def get_top_performers(days: int = 7):
    """
    Retorna Top 3 canais por RPM e Revenue
    """
    try:
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()

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
            "period_days": days,
            "top_rpm": [{"name": c['name'], "rpm": c['rpm']} for c in top_rpm],
            "top_revenue": [{"name": c['name'], "revenue": c['revenue']} for c in top_revenue]
        }

    except Exception as e:
        logger.error(f"Erro em /top-performers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 6: BY LANGUAGE
# =============================================================================

@router.get("/by-language")
async def get_monetization_by_language(days: int = 7):
    """
    Análise por língua: RPM, Views, Revenue
    """
    try:
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()

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
            "period_days": days,
            "languages": list(by_language.values())
        }

    except Exception as e:
        logger.error(f"Erro em /by-language: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINT 7: BY SUBNICHO
# =============================================================================

@router.get("/by-subnicho")
async def get_monetization_by_subnicho(days: int = 7):
    """
    Análise por subnicho: RPM, Views, Revenue
    """
    try:
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()

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
            "period_days": days,
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
    Retorna lista de canais monetizados ativos
    Usado para configuração/gerenciamento
    """
    try:
        channels = db.supabase.table("yt_channels")\
            .select("channel_id, channel_name, monetization_start_date, is_monetized")\
            .eq("is_monetized", True)\
            .execute()

        return {
            "monetized_channels": channels.data or []
        }

    except Exception as e:
        logger.error(f"Erro em /config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
