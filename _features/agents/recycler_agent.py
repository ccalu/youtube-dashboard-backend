# ========================================
# RECYCLER AGENT - Reciclador de Conteudo
# ========================================
# Funcao: Identificar conteudo para reciclar/adaptar
# Custo: ZERO (analisa dados do Supabase)
# ========================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict
import statistics

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class RecyclerAgent(BaseAgent):
    """
    Agente responsavel por identificar conteudo para reciclagem.

    O que busca:
    1. Videos NOSSOS que performaram bem -> Adaptar para outro idioma
    2. Videos NOSSOS antigos -> Atualizar com novo angulo
    3. Temas que funcionaram 1x -> Repetir com variacao
    4. Conteudo evergreen -> Republicar

    Cross-Pollination:
    - Video A bombou no canal EN de Reis Perversos
    - -> Criar versao para ES, PT, IT, AR, KO, JP
    - -> Adaptar para Terror (mesmo tema, angulo diferente)
    """

    def __init__(self, db_client):
        super().__init__(db_client)

        # Thresholds
        self.success_threshold = 50000  # Video de sucesso = > 50K views
        self.old_video_days = 90  # Video antigo = > 90 dias
        self.evergreen_threshold = 30000  # Evergreen se mantem > 30K

    @property
    def name(self) -> str:
        return "RecyclerAgent"

    @property
    def description(self) -> str:
        return "Identifica oportunidades de reciclagem e adaptacao de conteudo"

    async def run(self) -> AgentResult:
        """Executa analise de reciclagem"""
        result = self.create_result()

        try:
            logger.info(f"[{self.name}] Iniciando analise de reciclagem...")

            # 1. Buscar nossos videos de sucesso
            our_successful_videos = await self._get_our_successful_videos()
            logger.info(f"[{self.name}] {len(our_successful_videos)} videos nossos de sucesso")

            # 2. Buscar nossos canais por subnicho/lingua
            our_channels = await self._get_our_channels_grouped()
            logger.info(f"[{self.name}] {len(our_channels)} canais nossos mapeados")

            # 3. Identificar oportunidades de cross-language
            cross_language_opportunities = self._find_cross_language_recycle(
                our_successful_videos, our_channels
            )
            logger.info(f"[{self.name}] {len(cross_language_opportunities)} oportunidades cross-language")

            # 4. Identificar oportunidades de cross-subnicho
            cross_subnicho_opportunities = self._find_cross_subnicho_recycle(
                our_successful_videos, our_channels
            )
            logger.info(f"[{self.name}] {len(cross_subnicho_opportunities)} oportunidades cross-subnicho")

            # 5. Identificar videos antigos para atualizar
            update_opportunities = await self._find_update_opportunities()
            logger.info(f"[{self.name}] {len(update_opportunities)} videos para atualizar")

            # 6. Identificar conteudo evergreen
            evergreen_content = await self._find_evergreen_content()
            logger.info(f"[{self.name}] {len(evergreen_content)} conteudos evergreen")

            # 7. Gerar plano de reciclagem
            recycle_plan = self._generate_recycle_plan(
                cross_language_opportunities,
                cross_subnicho_opportunities,
                update_opportunities,
                evergreen_content
            )

            metrics = {
                "videos_sucesso_analisados": len(our_successful_videos),
                "oportunidades_cross_language": len(cross_language_opportunities),
                "oportunidades_cross_subnicho": len(cross_subnicho_opportunities),
                "videos_para_atualizar": len(update_opportunities),
                "conteudos_evergreen": len(evergreen_content),
                "acoes_totais": len(recycle_plan)
            }

            return self.complete_result(result, {
                "cross_language": cross_language_opportunities,
                "cross_subnicho": cross_subnicho_opportunities,
                "update_candidates": update_opportunities,
                "evergreen": evergreen_content,
                "recycle_plan": recycle_plan,
                "summary": f"{len(recycle_plan)} oportunidades de reciclagem identificadas"
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_our_successful_videos(self) -> List[Dict]:
        """Busca nossos videos que tiveram sucesso"""
        try:
            all_videos = []
            batch_size = 1000
            offset = 0

            while True:
                response = self.db.supabase.table("videos_historico")\
                    .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
                    .eq("canais_monitorados.tipo", "nosso")\
                    .gte("views_atuais", self.success_threshold)\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_videos.extend(response.data)

                if len(response.data) < batch_size:
                    break

                offset += batch_size

            # Deduplicar
            videos_dict = {}
            for video in all_videos:
                video_id = video.get("video_id")
                if video_id not in videos_dict:
                    videos_dict[video_id] = video

            return list(videos_dict.values())

        except Exception as e:
            logger.error(f"Erro buscando nossos videos de sucesso: {e}")
            return []

    async def _get_our_channels_grouped(self) -> Dict:
        """
        Busca nossos canais agrupados por subnicho e lingua.
        Retorna: {subnicho: {lingua: [canais]}}
        """
        try:
            response = self.db.supabase.table("canais_monitorados")\
                .select("*")\
                .eq("status", "ativo")\
                .eq("tipo", "nosso")\
                .execute()

            channels = response.data if response.data else []

            # Agrupar por subnicho e lingua
            grouped = defaultdict(lambda: defaultdict(list))
            for channel in channels:
                subnicho = channel.get("subnicho", "Unknown")
                lingua = channel.get("lingua", "Unknown")
                grouped[subnicho][lingua].append(channel)

            return dict(grouped)

        except Exception as e:
            logger.error(f"Erro buscando nossos canais: {e}")
            return {}

    def _find_cross_language_recycle(
        self,
        successful_videos: List[Dict],
        our_channels: Dict
    ) -> List[Dict]:
        """
        Encontra videos que podem ser adaptados para outros idiomas.
        """
        opportunities = []

        for video in successful_videos:
            canal_info = video.get("canais_monitorados", {})
            source_subnicho = canal_info.get("subnicho", "")
            source_lingua = canal_info.get("lingua", "")

            # Verificar quais idiomas temos no mesmo subnicho
            if source_subnicho in our_channels:
                available_languages = list(our_channels[source_subnicho].keys())

                # Idiomas onde NAO temos esse video
                missing_languages = [
                    lang for lang in available_languages
                    if lang.lower() != source_lingua.lower()
                ]

                if missing_languages:
                    opportunities.append({
                        "type": "cross_language",
                        "original_video": {
                            "titulo": video.get("titulo"),
                            "video_id": video.get("video_id"),
                            "url": video.get("url_video"),
                            "views": video.get("views_atuais"),
                            "canal": canal_info.get("nome_canal"),
                            "lingua": source_lingua,
                            "subnicho": source_subnicho
                        },
                        "target_languages": missing_languages,
                        "potential_channels": [
                            {
                                "lingua": lang,
                                "canais": [c.get("nome_canal") for c in our_channels[source_subnicho][lang]]
                            }
                            for lang in missing_languages
                        ],
                        "priority_score": self._calculate_recycle_priority(video, len(missing_languages)),
                        "action": f"Adaptar '{video.get('titulo', '')[:40]}...' para {', '.join(missing_languages)}"
                    })

        # Ordenar por priority_score
        opportunities.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return opportunities

    def _find_cross_subnicho_recycle(
        self,
        successful_videos: List[Dict],
        our_channels: Dict
    ) -> List[Dict]:
        """
        Encontra videos que podem ser adaptados para outros subnichos.
        """
        opportunities = []

        all_subnichos = list(our_channels.keys())

        for video in successful_videos:
            canal_info = video.get("canais_monitorados", {})
            source_subnicho = canal_info.get("subnicho", "")
            source_lingua = canal_info.get("lingua", "")

            # Verificar outros subnichos
            other_subnichos = [s for s in all_subnichos if s != source_subnicho]

            for target_subnicho in other_subnichos:
                # Verificar se temos canal nesse subnicho com mesmo idioma
                if source_lingua in our_channels.get(target_subnicho, {}):
                    opportunities.append({
                        "type": "cross_subnicho",
                        "original_video": {
                            "titulo": video.get("titulo"),
                            "video_id": video.get("video_id"),
                            "views": video.get("views_atuais"),
                            "subnicho": source_subnicho,
                            "lingua": source_lingua
                        },
                        "target_subnicho": target_subnicho,
                        "target_channels": [
                            c.get("nome_canal")
                            for c in our_channels[target_subnicho].get(source_lingua, [])
                        ],
                        "priority_score": self._calculate_recycle_priority(video, 1) * 0.7,
                        "action": f"Adaptar tema de '{video.get('titulo', '')[:30]}...' para {target_subnicho}"
                    })

        # Ordenar e limitar (muitas combinacoes possiveis)
        opportunities.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return opportunities[:50]

    def _calculate_recycle_priority(self, video: Dict, multiplier: int = 1) -> float:
        """Calcula prioridade de reciclagem baseado em views"""
        views = video.get("views_atuais", 0)

        if views >= 500000:
            base_score = 100
        elif views >= 200000:
            base_score = 80
        elif views >= 100000:
            base_score = 60
        elif views >= 50000:
            base_score = 40
        else:
            base_score = 20

        return base_score * (1 + (multiplier * 0.2))

    async def _find_update_opportunities(self) -> List[Dict]:
        """
        Encontra videos antigos que podem ser atualizados/refeitos.
        Criterio: Video > 90 dias com bom desempenho.
        """
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.old_video_days)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
                .eq("canais_monitorados.tipo", "nosso")\
                .lt("data_publicacao", cutoff_date)\
                .gte("views_atuais", self.evergreen_threshold)\
                .order("views_atuais", desc=True)\
                .limit(50)\
                .execute()

            opportunities = []
            if response.data:
                for video in response.data:
                    canal_info = video.get("canais_monitorados", {})
                    pub_date = video.get("data_publicacao", "")

                    # Calcular idade
                    try:
                        pub_datetime = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        age_days = (datetime.now(timezone.utc) - pub_datetime).days
                    except:
                        age_days = 90

                    opportunities.append({
                        "type": "update",
                        "video": {
                            "titulo": video.get("titulo"),
                            "video_id": video.get("video_id"),
                            "url": video.get("url_video"),
                            "views": video.get("views_atuais"),
                            "age_days": age_days,
                            "canal": canal_info.get("nome_canal"),
                            "subnicho": canal_info.get("subnicho")
                        },
                        "action": f"Atualizar/refazer: '{video.get('titulo', '')[:40]}...' ({age_days} dias)",
                        "reason": f"Video antigo com {video.get('views_atuais', 0):,} views - potencial para versao atualizada"
                    })

            return opportunities

        except Exception as e:
            logger.error(f"Erro buscando videos para atualizar: {e}")
            return []

    async def _find_evergreen_content(self) -> List[Dict]:
        """
        Identifica conteudo evergreen (sempre relevante).
        Criterio: Video antigo que continua recebendo views.
        """
        try:
            # Videos antigos (> 180 dias) que ainda tem boas views
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("*, canais_monitorados!inner(id, nome_canal, subnicho, lingua, tipo)")\
                .eq("canais_monitorados.tipo", "nosso")\
                .lt("data_publicacao", cutoff_date)\
                .gte("views_atuais", self.success_threshold)\
                .order("views_atuais", desc=True)\
                .limit(30)\
                .execute()

            evergreen = []
            if response.data:
                for video in response.data:
                    canal_info = video.get("canais_monitorados", {})

                    evergreen.append({
                        "type": "evergreen",
                        "video": {
                            "titulo": video.get("titulo"),
                            "video_id": video.get("video_id"),
                            "views": video.get("views_atuais"),
                            "canal": canal_info.get("nome_canal"),
                            "subnicho": canal_info.get("subnicho"),
                            "lingua": canal_info.get("lingua")
                        },
                        "recommendation": "Tema evergreen - criar mais conteudo similar",
                        "potential_actions": [
                            "Criar sequencia/parte 2",
                            "Adaptar para outros idiomas",
                            "Criar variacao do tema"
                        ]
                    })

            return evergreen

        except Exception as e:
            logger.error(f"Erro buscando conteudo evergreen: {e}")
            return []

    def _generate_recycle_plan(
        self,
        cross_language: List[Dict],
        cross_subnicho: List[Dict],
        updates: List[Dict],
        evergreen: List[Dict]
    ) -> List[Dict]:
        """
        Gera plano de reciclagem priorizado.
        """
        plan = []

        # 1. Cross-language (prioridade alta)
        for opp in cross_language[:15]:
            plan.append({
                "priority": 1,
                "type": "cross_language",
                "action": opp.get("action"),
                "impact": "Alto - video ja validado, apenas adaptar",
                "effort": "Medio",
                "data": opp
            })

        # 2. Atualizacoes (prioridade media-alta)
        for opp in updates[:10]:
            plan.append({
                "priority": 2,
                "type": "update",
                "action": opp.get("action"),
                "impact": "Medio - retrabalhar conteudo existente",
                "effort": "Medio",
                "data": opp
            })

        # 3. Cross-subnicho (prioridade media)
        for opp in cross_subnicho[:10]:
            plan.append({
                "priority": 3,
                "type": "cross_subnicho",
                "action": opp.get("action"),
                "impact": "Medio - adaptar para outro contexto",
                "effort": "Alto",
                "data": opp
            })

        # 4. Evergreen (prioridade baixa-media)
        for opp in evergreen[:10]:
            plan.append({
                "priority": 4,
                "type": "evergreen",
                "action": f"Explorar tema evergreen: {opp['video']['titulo'][:30]}...",
                "impact": "Medio - tema comprovadamente funciona",
                "effort": "Baixo",
                "data": opp
            })

        # Ordenar por prioridade
        plan.sort(key=lambda x: x.get("priority", 99))

        return plan
