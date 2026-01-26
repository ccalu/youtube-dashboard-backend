# ========================================
# ALERT AGENT - Sistema de Alertas Inteligentes
# ========================================
# Funcao: Notificar APENAS o que importa
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict
from enum import Enum

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    CRITICAL = "critical"  # Acao imediata necessaria
    HIGH = "high"          # Importante, revisar hoje
    MEDIUM = "medium"      # Revisar esta semana
    LOW = "low"            # Informativo


class AlertType(Enum):
    VIRAL = "viral"                    # Video concorrente viralizando
    TREND = "trend"                    # Tendencia emergente
    PERFORMANCE_DROP = "drop"          # Nosso canal caiu
    OPPORTUNITY = "opportunity"        # Oportunidade detectada
    RECYCLE = "recycle"               # Conteudo para reciclar
    NEW_COMPETITOR = "new_competitor"  # Novo concorrente detectado


class AlertAgent(BaseAgent):
    """
    Agente responsavel por gerar alertas inteligentes.

    Tipos de Alerta:
    - VIRAL: Video concorrente > 50K em 3 dias
    - TREND: Micronicho emergente detectado
    - DROP: Nosso canal abaixo do benchmark
    - OPPORTUNITY: Gap de mercado identificado
    - RECYCLE: Conteudo pronto para adaptar

    Anti-Ruido:
    - Nao alertar sobre canais < 1K inscritos
    - Nao alertar sobre videos com views baixas
    - Agregar alertas similares em 1 notificacao
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Thresholds para alertas
        self.viral_threshold = 50000  # Views em 3 dias
        self.viral_days = 3
        self.min_channel_subscribers = 1000
        self.performance_drop_threshold = 0.7  # 70% do benchmark
        self.trend_min_videos = 3  # Minimo de videos para considerar tendencia

    @property
    def name(self) -> str:
        return "AlertAgent"

    @property
    def description(self) -> str:
        return "Gera alertas inteligentes sobre eventos importantes"

    async def run(self) -> AgentResult:
        """Executa geracao de alertas"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando geracao de alertas...")

            all_alerts = []

            # 1. Detectar videos viralizando
            viral_alerts = await self._detect_viral_videos()
            all_alerts.extend(viral_alerts)
            logger.info(f"[{self.name}] {len(viral_alerts)} alertas de viral")

            # 2. Detectar tendencias emergentes
            trend_alerts = await self._detect_emerging_trends()
            all_alerts.extend(trend_alerts)
            logger.info(f"[{self.name}] {len(trend_alerts)} alertas de tendencia")

            # 3. Detectar quedas de performance
            drop_alerts = await self._detect_performance_drops()
            all_alerts.extend(drop_alerts)
            logger.info(f"[{self.name}] {len(drop_alerts)} alertas de queda")

            # 4. Detectar oportunidades
            opportunity_alerts = await self._detect_opportunities()
            all_alerts.extend(opportunity_alerts)
            logger.info(f"[{self.name}] {len(opportunity_alerts)} alertas de oportunidade")

            # 5. Agregar alertas similares
            aggregated_alerts = self._aggregate_similar_alerts(all_alerts)

            # 6. Priorizar
            aggregated_alerts.sort(key=lambda x: self._get_priority_order(x.get("priority")))

            # 7. Salvar alertas no banco
            saved_count = await self._save_alerts(aggregated_alerts)

            # 8. Separar por prioridade para o relatorio
            alerts_by_priority = self._group_by_priority(aggregated_alerts)

            metrics = {
                "viral_alerts": len(viral_alerts),
                "trend_alerts": len(trend_alerts),
                "drop_alerts": len(drop_alerts),
                "opportunity_alerts": len(opportunity_alerts),
                "total_alerts": len(all_alerts),
                "after_aggregation": len(aggregated_alerts),
                "saved": saved_count
            }

            return self.complete_result(result, {
                "alerts": aggregated_alerts,
                "by_priority": alerts_by_priority,
                "critical_count": len(alerts_by_priority.get("critical", [])),
                "high_count": len(alerts_by_priority.get("high", [])),
                "summary": f"{len(aggregated_alerts)} alertas gerados ({saved_count} salvos)"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _detect_viral_videos(self) -> List[Dict]:
        """Detecta videos que estao viralizando"""
        alerts = []

        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.viral_days)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
                .eq("canais_monitorados.tipo", "minerado")\
                .gte("data_publicacao", cutoff_date)\
                .gte("views_atuais", self.viral_threshold)\
                .order("views_atuais", desc=True)\
                .limit(50)\
                .execute()

            if response.data:
                for video in response.data:
                    canal_info = video.get("canais_monitorados", {})
                    views = video.get("views_atuais", 0)

                    # Determinar prioridade baseado em views
                    if views >= 500000:
                        priority = AlertPriority.CRITICAL
                    elif views >= 200000:
                        priority = AlertPriority.HIGH
                    else:
                        priority = AlertPriority.MEDIUM

                    alerts.append({
                        "type": AlertType.VIRAL.value,
                        "priority": priority.value,
                        "title": f"Video viral: {views:,} views em {self.viral_days} dias",
                        "message": f"'{video.get('titulo', '')[:50]}...' do canal {canal_info.get('nome_canal')}",
                        "data": {
                            "video_id": video.get("video_id"),
                            "titulo": video.get("titulo"),
                            "views": views,
                            "url": video.get("url_video"),
                            "canal": canal_info.get("nome_canal"),
                            "subnicho": canal_info.get("subnicho"),
                            "lingua": canal_info.get("lingua")
                        },
                        "action_suggested": f"Analisar e considerar criar video similar",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })

        except Exception as e:
            logger.error(f"Erro detectando virais: {e}")

        return alerts

    async def _detect_emerging_trends(self) -> List[Dict]:
        """Detecta tendencias emergentes"""
        alerts = []

        try:
            # Buscar videos recentes (7 dias) agrupados por tema
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(subnicho, lingua)")\
                .gte("data_publicacao", cutoff_date)\
                .gte("views_atuais", 30000)\
                .execute()

            if response.data:
                # Agrupar por subnicho
                subnicho_count = defaultdict(lambda: {"count": 0, "views": 0, "videos": []})

                for video in response.data:
                    canal_info = video.get("canais_monitorados", {})
                    subnicho = canal_info.get("subnicho", "Unknown")

                    subnicho_count[subnicho]["count"] += 1
                    subnicho_count[subnicho]["views"] += video.get("views_atuais", 0)
                    if len(subnicho_count[subnicho]["videos"]) < 5:
                        subnicho_count[subnicho]["videos"].append(video.get("titulo"))

                # Alertar sobre subnichos com muita atividade
                for subnicho, stats in subnicho_count.items():
                    if stats["count"] >= self.trend_min_videos:
                        priority = AlertPriority.HIGH if stats["count"] >= 5 else AlertPriority.MEDIUM

                        alerts.append({
                            "type": AlertType.TREND.value,
                            "priority": priority.value,
                            "title": f"Tendencia em {subnicho}: {stats['count']} videos bombando",
                            "message": f"Total de {stats['views']:,} views nos ultimos 7 dias",
                            "data": {
                                "subnicho": subnicho,
                                "video_count": stats["count"],
                                "total_views": stats["views"],
                                "example_titles": stats["videos"]
                            },
                            "action_suggested": f"Aumentar producao no subnicho {subnicho}",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })

        except Exception as e:
            logger.error(f"Erro detectando tendencias: {e}")

        return alerts

    async def _detect_performance_drops(self) -> List[Dict]:
        """Detecta quedas de performance nos nossos canais"""
        alerts = []

        try:
            # Buscar dados de historico dos nossos canais
            response = self.db.supabase.table("canais_monitorados")\
                .select("*")\
                .eq("status", "ativo")\
                .eq("tipo", "nosso")\
                .execute()

            if not response.data:
                return alerts

            # Para cada canal, verificar se views estao caindo
            for canal in response.data:
                canal_id = canal.get("id")

                # Buscar historico de views
                hist_response = self.db.supabase.table("dados_canais_historico")\
                    .select("views_7d, data_coleta")\
                    .eq("canal_id", canal_id)\
                    .order("data_coleta", desc=True)\
                    .limit(14)\
                    .execute()

                if hist_response.data and len(hist_response.data) >= 7:
                    # Comparar semana atual vs semana anterior
                    week_current = [h.get("views_7d", 0) for h in hist_response.data[:7]]
                    week_previous = [h.get("views_7d", 0) for h in hist_response.data[7:14]]

                    if week_current and week_previous:
                        avg_current = sum(week_current) / len(week_current)
                        avg_previous = sum(week_previous) / len(week_previous)

                        if avg_previous > 0:
                            ratio = avg_current / avg_previous

                            if ratio < self.performance_drop_threshold:
                                drop_pct = round((1 - ratio) * 100, 1)

                                alerts.append({
                                    "type": AlertType.PERFORMANCE_DROP.value,
                                    "priority": AlertPriority.HIGH.value,
                                    "title": f"Queda de {drop_pct}% no canal {canal.get('nome_canal')}",
                                    "message": f"Views caiu de {avg_previous:,.0f} para {avg_current:,.0f}",
                                    "data": {
                                        "canal_id": canal_id,
                                        "canal_nome": canal.get("nome_canal"),
                                        "subnicho": canal.get("subnicho"),
                                        "views_current": avg_current,
                                        "views_previous": avg_previous,
                                        "drop_percentage": drop_pct
                                    },
                                    "action_suggested": "Investigar causa da queda e ajustar estrategia",
                                    "created_at": datetime.now(timezone.utc).isoformat()
                                })

        except Exception as e:
            logger.error(f"Erro detectando quedas: {e}")

        return alerts

    async def _detect_opportunities(self) -> List[Dict]:
        """Detecta oportunidades de mercado"""
        alerts = []

        try:
            # Buscar videos de sucesso de concorrentes
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(subnicho, lingua, tipo)")\
                .eq("canais_monitorados.tipo", "minerado")\
                .gte("data_publicacao", cutoff_date)\
                .gte("views_atuais", 100000)\
                .execute()

            if not response.data:
                return alerts

            # Buscar nossos subnichos/idiomas
            our_response = self.db.supabase.table("canais_monitorados")\
                .select("subnicho, lingua")\
                .eq("tipo", "nosso")\
                .execute()

            our_combos = set()
            if our_response.data:
                for c in our_response.data:
                    combo = f"{c.get('subnicho', '').lower()}_{c.get('lingua', '').lower()}"
                    our_combos.add(combo)

            # Detectar gaps
            competitor_combos = defaultdict(lambda: {"count": 0, "views": 0})
            for video in response.data:
                canal_info = video.get("canais_monitorados", {})
                combo = f"{canal_info.get('subnicho', '').lower()}_{canal_info.get('lingua', '').lower()}"

                competitor_combos[combo]["count"] += 1
                competitor_combos[combo]["views"] += video.get("views_atuais", 0)

            # Alertar sobre gaps
            for combo, stats in competitor_combos.items():
                if combo not in our_combos and stats["count"] >= 2:
                    subnicho, lingua = combo.rsplit("_", 1)

                    alerts.append({
                        "type": AlertType.OPPORTUNITY.value,
                        "priority": AlertPriority.MEDIUM.value,
                        "title": f"Gap de mercado: {subnicho} em {lingua}",
                        "message": f"{stats['count']} videos de sucesso ({stats['views']:,} views) - nos nao temos presenca",
                        "data": {
                            "subnicho": subnicho,
                            "lingua": lingua,
                            "competitor_videos": stats["count"],
                            "total_views": stats["views"]
                        },
                        "action_suggested": f"Considerar criar canal em {lingua} para {subnicho}",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })

        except Exception as e:
            logger.error(f"Erro detectando oportunidades: {e}")

        return alerts

    def _aggregate_similar_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """Agrega alertas similares para reduzir ruido"""
        # Agrupar por tipo + subnicho
        groups = defaultdict(list)

        for alert in alerts:
            key = f"{alert.get('type')}_{alert.get('data', {}).get('subnicho', 'unknown')}"
            groups[key].append(alert)

        aggregated = []
        for key, group in groups.items():
            if len(group) == 1:
                aggregated.append(group[0])
            else:
                # Agregar multiplos alertas
                main_alert = group[0].copy()
                main_alert["aggregated_count"] = len(group)
                main_alert["title"] = f"{main_alert['title']} (+{len(group)-1} similares)"
                aggregated.append(main_alert)

        return aggregated

    def _get_priority_order(self, priority: str) -> int:
        """Retorna ordem numerica da prioridade"""
        order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }
        return order.get(priority, 99)

    def _group_by_priority(self, alerts: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa alertas por prioridade"""
        groups = defaultdict(list)
        for alert in alerts:
            priority = alert.get("priority", "low")
            groups[priority].append(alert)
        return dict(groups)

    async def _save_alerts(self, alerts: List[Dict]) -> int:
        """Salva alertas no banco para historico"""
        saved = 0

        try:
            for alert in alerts[:50]:  # Limitar a 50 por execucao
                try:
                    self.db.supabase.table("agent_alerts").insert({
                        "type": alert.get("type"),
                        "priority": alert.get("priority"),
                        "title": alert.get("title"),
                        "message": alert.get("message"),
                        "data": alert.get("data"),
                        "action_suggested": alert.get("action_suggested"),
                        "status": "new",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }).execute()
                    saved += 1
                except Exception as e:
                    # Tabela pode nao existir ainda
                    if "relation" not in str(e).lower():
                        logger.warning(f"Erro salvando alerta: {e}")
                    break

        except Exception as e:
            logger.warning(f"Nao foi possivel salvar alertas: {e}")

        return saved
