# ========================================
# AI ADVISOR AGENT - Conselheiro com GPT-4 Mini
# ========================================
# Funcao: Gerar insights INTELIGENTES usando LLM
# Custo: ~100K tokens/dia (voce tem 10M gratis!)
# ========================================

import logging
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import aiohttp

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class AIAdvisorAgent(BaseAgent):
    """
    Agente que usa GPT-4 Mini para gerar insights INTELIGENTES.

    Diferente do AdvisorAgent normal (regras fixas), este:
    - ENTENDE contexto e nuances
    - EXPLICA por que algo funciona
    - SUGERE ideias criativas
    - GERA titulos otimizados
    - PRIORIZA de forma inteligente

    Custo estimado: ~50-100K tokens/dia
    """

    def __init__(self, db_client, openai_api_key: str = None):
        super().__init__(db_client)

        # API Key da OpenAI
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            # Sanitizar API key para evitar problemas com whitespace/newlines
            self.api_key = self.api_key.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        else:
            logger.warning("OPENAI_API_KEY nao configurada - AI Advisor desabilitado")

        # Configuracoes
        self.model = "gpt-4o-mini"  # GPT-4 Mini - barato e inteligente
        self.max_tokens = 2000
        self.temperature = 0.7

        # Endpoints
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @property
    def name(self) -> str:
        return "AIAdvisorAgent"

    @property
    def description(self) -> str:
        return "Gera insights inteligentes usando GPT-4 Mini baseado em dados reais"

    async def run(self, context_data: Dict = None) -> AgentResult:
        """
        Executa analise com IA.

        Args:
            context_data: Dados dos outros agentes para contexto
        """
        result = self.create_result()

        if not self.api_key:
            return self.fail_result(result, "OPENAI_API_KEY nao configurada")

        try:
            logger.info(f"[{self.name}] Iniciando analise com GPT-4 Mini...")

            # 1. Coletar dados do banco
            data = await self._collect_analysis_data()
            logger.info(f"[{self.name}] Dados coletados: {len(data.get('trending_videos', []))} videos trending")

            # 2. Gerar briefing diario
            daily_briefing = await self._generate_daily_briefing(data)
            logger.info(f"[{self.name}] Briefing diario gerado")

            # 3. Gerar recomendacoes por canal
            channel_recommendations = await self._generate_channel_recommendations(data)
            logger.info(f"[{self.name}] Recomendacoes por canal geradas")

            # 4. Gerar sugestoes de titulos
            title_suggestions = await self._generate_title_suggestions(data)
            logger.info(f"[{self.name}] Sugestoes de titulos geradas")

            # 5. Analisar por que videos viralizaram
            viral_analysis = await self._analyze_viral_videos(data)
            logger.info(f"[{self.name}] Analise de virais concluida")

            metrics = {
                "videos_analisados": len(data.get("trending_videos", [])),
                "canais_analisados": len(data.get("our_channels", [])),
                "tokens_estimados": self._estimate_tokens_used()
            }

            return self.complete_result(result, {
                "daily_briefing": daily_briefing,
                "channel_recommendations": channel_recommendations,
                "title_suggestions": title_suggestions,
                "viral_analysis": viral_analysis,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_used": self.model
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _collect_analysis_data(self) -> Dict:
        """Coleta dados necessarios para analise"""
        data = {
            "trending_videos": [],
            "our_channels": [],
            "competitor_success": [],
            "subnichos": [],
            "languages": []
        }

        try:
            # Videos trending (ultimos 7 dias, > 50K views)
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("titulo, views_atuais, canal_id, data_publicacao, canais_monitorados!inner(nome_canal, subnicho, lingua, tipo)")\
                .gte("data_publicacao", cutoff)\
                .gte("views_atuais", 50000)\
                .order("views_atuais", desc=True)\
                .limit(50)\
                .execute()

            if response.data:
                data["trending_videos"] = response.data

            # Nossos canais
            our_response = self.db.supabase.table("canais_monitorados")\
                .select("id, nome_canal, subnicho, lingua")\
                .eq("tipo", "nosso")\
                .eq("status", "ativo")\
                .execute()

            if our_response.data:
                data["our_channels"] = our_response.data

            # Extrair subnichos e idiomas unicos
            subnichos = set()
            languages = set()
            for canal in data["our_channels"]:
                if canal.get("subnicho"):
                    subnichos.add(canal["subnicho"])
                if canal.get("lingua"):
                    languages.add(canal["lingua"])

            data["subnichos"] = list(subnichos)
            data["languages"] = list(languages)

        except Exception as e:
            logger.error(f"Erro coletando dados: {e}")

        return data

    async def _call_gpt(self, system_prompt: str, user_prompt: str) -> str:
        """Faz chamada para GPT-4 Mini"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error = await response.text()
                        logger.error(f"Erro GPT API: {response.status} - {error}")
                        return f"Erro na API: {response.status}"

        except Exception as e:
            logger.error(f"Erro chamando GPT: {e}")
            return f"Erro: {str(e)}"

    async def _generate_daily_briefing(self, data: Dict) -> str:
        """Gera briefing diario inteligente"""

        system_prompt = """Voce e um analista estrategico de canais de YouTube focados em entretenimento (terror, reis perversos, historias obscuras, etc).

Sua tarefa e analisar dados de videos viralizando e gerar um BRIEFING DIARIO claro e acionavel.

Formato do briefing:
1. PRIORIDADE MAXIMA (1-2 acoes urgentes)
2. TENDENCIAS DO DIA (o que esta bombando)
3. OPORTUNIDADES (gaps de mercado)
4. ALERTAS (problemas a resolver)

Seja direto, pratico e baseado nos dados fornecidos."""

        # Preparar dados para o prompt
        trending_summary = []
        for video in data.get("trending_videos", [])[:20]:
            canal_info = video.get("canais_monitorados", {})
            trending_summary.append({
                "titulo": video.get("titulo", "")[:100],
                "views": video.get("views_atuais", 0),
                "canal": canal_info.get("nome_canal", ""),
                "subnicho": canal_info.get("subnicho", ""),
                "lingua": canal_info.get("lingua", ""),
                "tipo": canal_info.get("tipo", "")
            })

        user_prompt = f"""Analise estes dados e gere o briefing diario:

VIDEOS VIRALIZANDO (ultimos 7 dias):
{json.dumps(trending_summary, indent=2, ensure_ascii=False)}

NOSSOS CANAIS:
{json.dumps(data.get('our_channels', []), indent=2, ensure_ascii=False)}

NOSSOS SUBNICHOS: {', '.join(data.get('subnichos', []))}
NOSSOS IDIOMAS: {', '.join(data.get('languages', []))}

Data: {datetime.now().strftime('%d/%m/%Y')}

Gere o briefing focando em ACOES PRATICAS que podemos tomar HOJE."""

        return await self._call_gpt(system_prompt, user_prompt)

    async def _generate_channel_recommendations(self, data: Dict) -> Dict[str, str]:
        """Gera recomendacoes especificas por canal"""
        recommendations = {}

        # Agrupar videos por subnicho
        videos_by_subnicho = {}
        for video in data.get("trending_videos", []):
            subnicho = video.get("canais_monitorados", {}).get("subnicho", "Unknown")
            if subnicho not in videos_by_subnicho:
                videos_by_subnicho[subnicho] = []
            videos_by_subnicho[subnicho].append(video)

        # Para cada canal nosso, gerar recomendacao
        for canal in data.get("our_channels", [])[:10]:  # Limitar a 10 canais
            subnicho = canal.get("subnicho", "")
            lingua = canal.get("lingua", "")

            relevant_videos = videos_by_subnicho.get(subnicho, [])[:5]

            if not relevant_videos:
                continue

            system_prompt = f"""Voce e um estrategista de conteudo YouTube para canais de {subnicho} em {lingua}.
Analise os videos de sucesso dos concorrentes e sugira O QUE este canal deve criar."""

            videos_info = [
                f"- {v.get('titulo', '')[:80]} ({v.get('views_atuais', 0):,} views)"
                for v in relevant_videos
            ]

            user_prompt = f"""Canal: {canal.get('nome_canal')}
Subnicho: {subnicho}
Idioma: {lingua}

Videos de SUCESSO dos concorrentes neste subnicho:
{chr(10).join(videos_info)}

Sugira 2-3 ideias de videos que este canal deveria criar, explicando POR QUE cada uma funcionaria."""

            recommendation = await self._call_gpt(system_prompt, user_prompt)
            recommendations[canal.get("nome_canal", "")] = recommendation

        return recommendations

    async def _generate_title_suggestions(self, data: Dict) -> List[Dict]:
        """Gera sugestoes de titulos otimizados"""
        suggestions = []

        # Pegar top videos como referencia
        top_videos = data.get("trending_videos", [])[:10]

        if not top_videos:
            return suggestions

        system_prompt = """Voce e um especialista em CTR e titulos de YouTube para nichos de entretenimento obscuro (terror, historia, reis perversos).

Analise os titulos que estao viralizando e:
1. Identifique PADROES que funcionam
2. Gere VARIAÇÕES otimizadas
3. Explique POR QUE cada estrutura funciona

Foque em titulos que geram curiosidade e cliques."""

        titles_info = [
            f"- \"{v.get('titulo', '')}\" ({v.get('views_atuais', 0):,} views) - {v.get('canais_monitorados', {}).get('subnicho', '')}"
            for v in top_videos
        ]

        user_prompt = f"""Titulos VIRALIZANDO agora:
{chr(10).join(titles_info)}

1. Quais PADROES voce identifica?
2. Gere 5 titulos novos usando esses padroes (para diferentes subnichos)
3. Explique a psicologia por tras de cada estrutura"""

        analysis = await self._call_gpt(system_prompt, user_prompt)

        suggestions.append({
            "type": "title_analysis",
            "content": analysis,
            "based_on": len(top_videos),
            "generated_at": datetime.now(timezone.utc).isoformat()
        })

        return suggestions

    async def _analyze_viral_videos(self, data: Dict) -> List[Dict]:
        """Analisa POR QUE videos viralizaram"""
        analysis = []

        # Top 5 videos para analise profunda
        top_videos = sorted(
            data.get("trending_videos", []),
            key=lambda x: x.get("views_atuais", 0),
            reverse=True
        )[:5]

        for video in top_videos:
            canal_info = video.get("canais_monitorados", {})

            system_prompt = """Voce e um analista de conteudo viral no YouTube.
Analise este video e explique POR QUE ele viralizou.
Considere: titulo, timing, subnicho, estrutura, gatilhos psicologicos."""

            user_prompt = f"""Video: "{video.get('titulo', '')}"
Views: {video.get('views_atuais', 0):,}
Canal: {canal_info.get('nome_canal', '')}
Subnicho: {canal_info.get('subnicho', '')}
Idioma: {canal_info.get('lingua', '')}
Publicado: {video.get('data_publicacao', '')}

Por que este video viralizou? O que podemos aprender e replicar?"""

            why_viral = await self._call_gpt(system_prompt, user_prompt)

            analysis.append({
                "video_title": video.get("titulo", ""),
                "views": video.get("views_atuais", 0),
                "subnicho": canal_info.get("subnicho", ""),
                "analysis": why_viral
            })

        return analysis

    def _estimate_tokens_used(self) -> int:
        """Estima tokens usados na execucao"""
        # Estimativa grosseira baseada nas chamadas feitas
        # Cada chamada: ~500 input + ~500 output = ~1000 tokens
        # 4 tipos de analise = ~4000 tokens
        # + recomendacoes por canal (~10 canais * 500 = 5000)
        return 10000  # ~10K tokens por execucao

    async def generate_quick_insight(self, question: str, context: str = "") -> str:
        """
        Gera insight rapido para uma pergunta especifica.
        Util para consultas ad-hoc.
        """
        if not self.api_key:
            return "OPENAI_API_KEY nao configurada"

        system_prompt = """Voce e um consultor estrategico de canais YouTube de entretenimento.
Responda de forma direta e pratica, baseado em dados quando fornecidos."""

        user_prompt = f"""{question}

{f'Contexto: {context}' if context else ''}"""

        return await self._call_gpt(system_prompt, user_prompt)
