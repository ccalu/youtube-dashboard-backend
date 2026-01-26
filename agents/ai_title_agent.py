# ========================================
# AI TITLE AGENT - Gerador de Titulos com GPT-4 Mini
# ========================================
# Funcao: Gerar titulos OTIMIZADOS baseado em padroes de sucesso
# Custo: ~20-50K tokens/dia
# ========================================

import logging
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import aiohttp

from .base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class AITitleAgent(BaseAgent):
    """
    Agente que usa GPT-4 Mini para gerar titulos otimizados.

    Funcionalidades:
    - Analisa padroes de titulos que funcionam
    - Gera variações otimizadas
    - Adapta titulos para outros idiomas
    - Sugere estruturas por subnicho
    """

    def __init__(self, db_client, openai_api_key: str = None):
        super().__init__(db_client)

        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        self.max_tokens = 1500
        self.temperature = 0.8  # Mais criativo para titulos
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @property
    def name(self) -> str:
        return "AITitleAgent"

    @property
    def description(self) -> str:
        return "Gera titulos otimizados usando GPT-4 Mini baseado em padroes de sucesso"

    async def run(self) -> AgentResult:
        """Executa analise e geracao de titulos"""
        result = self.create_result()

        if not self.api_key:
            return self.fail_result(result, "OPENAI_API_KEY nao configurada")

        try:
            logger.info(f"[{self.name}] Iniciando analise de titulos...")

            # 1. Coletar titulos de sucesso
            successful_titles = await self._get_successful_titles()
            logger.info(f"[{self.name}] {len(successful_titles)} titulos de sucesso coletados")

            # 2. Analisar padroes por subnicho
            patterns_by_subnicho = await self._analyze_patterns_by_subnicho(successful_titles)

            # 3. Gerar banco de titulos sugeridos
            title_bank = await self._generate_title_bank(successful_titles)

            # 4. Gerar estruturas recomendadas
            recommended_structures = await self._get_recommended_structures(successful_titles)

            metrics = {
                "titulos_analisados": len(successful_titles),
                "subnichos_analisados": len(patterns_by_subnicho),
                "titulos_gerados": sum(len(t) for t in title_bank.values())
            }

            return self.complete_result(result, {
                "patterns_by_subnicho": patterns_by_subnicho,
                "title_bank": title_bank,
                "recommended_structures": recommended_structures,
                "successful_titles_analyzed": len(successful_titles)
            }, metrics)

        except Exception as e:
            logger.error(f"[{self.name}] Erro: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.fail_result(result, str(e))

    async def _get_successful_titles(self) -> List[Dict]:
        """Busca titulos de videos de sucesso"""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

            response = self.db.supabase.table("videos_historico")\
                .select("titulo, views_atuais, canais_monitorados!inner(subnicho, lingua, tipo)")\
                .gte("data_publicacao", cutoff)\
                .gte("views_atuais", 30000)\
                .order("views_atuais", desc=True)\
                .limit(100)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Erro buscando titulos: {e}")
            return []

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
                        logger.error(f"Erro GPT API: {response.status}")
                        return ""

        except Exception as e:
            logger.error(f"Erro chamando GPT: {e}")
            return ""

    async def _analyze_patterns_by_subnicho(self, titles: List[Dict]) -> Dict[str, str]:
        """Analisa padroes de titulo por subnicho"""
        patterns = {}

        # Agrupar por subnicho
        by_subnicho = {}
        for t in titles:
            subnicho = t.get("canais_monitorados", {}).get("subnicho", "Unknown")
            if subnicho not in by_subnicho:
                by_subnicho[subnicho] = []
            by_subnicho[subnicho].append(t)

        system_prompt = """Voce e um especialista em titulos virais do YouTube.
Analise os titulos fornecidos e identifique:
1. Estruturas que mais funcionam
2. Palavras-gatilho mais eficazes
3. Comprimento ideal
4. Padroes de pontuacao (?, !, ...)

Seja especifico e pratico."""

        for subnicho, subnicho_titles in by_subnicho.items():
            if len(subnicho_titles) < 3:
                continue

            titles_text = "\n".join([
                f"- \"{t.get('titulo', '')}\" ({t.get('views_atuais', 0):,} views)"
                for t in subnicho_titles[:15]
            ])

            user_prompt = f"""Subnicho: {subnicho}

Titulos de SUCESSO:
{titles_text}

Quais padroes voce identifica? O que faz esses titulos funcionarem?"""

            analysis = await self._call_gpt(system_prompt, user_prompt)
            patterns[subnicho] = analysis

        return patterns

    async def _generate_title_bank(self, titles: List[Dict]) -> Dict[str, List[str]]:
        """Gera banco de titulos sugeridos por subnicho"""
        title_bank = {}

        # Agrupar por subnicho
        by_subnicho = {}
        for t in titles:
            subnicho = t.get("canais_monitorados", {}).get("subnicho", "Unknown")
            if subnicho not in by_subnicho:
                by_subnicho[subnicho] = []
            by_subnicho[subnicho].append(t)

        system_prompt = """Voce e um copywriter especializado em titulos virais de YouTube.
Baseado nos titulos de sucesso fornecidos, gere 10 NOVOS titulos originais.

Regras:
- Mantenha o estilo e tom do subnicho
- Use as estruturas que mais funcionam
- Seja criativo mas realista
- Cada titulo em uma linha
- Apenas os titulos, sem numeracao ou explicacao"""

        for subnicho, subnicho_titles in by_subnicho.items():
            if len(subnicho_titles) < 3:
                continue

            titles_text = "\n".join([
                f"- {t.get('titulo', '')}"
                for t in subnicho_titles[:10]
            ])

            # Identificar idioma predominante
            linguas = [t.get("canais_monitorados", {}).get("lingua", "") for t in subnicho_titles]
            lingua_principal = max(set(linguas), key=linguas.count) if linguas else "english"

            user_prompt = f"""Subnicho: {subnicho}
Idioma: {lingua_principal}

Titulos de referencia (sucesso comprovado):
{titles_text}

Gere 10 titulos NOVOS e ORIGINAIS no mesmo estilo:"""

            new_titles = await self._call_gpt(system_prompt, user_prompt)

            # Parsear titulos (um por linha)
            title_bank[subnicho] = [
                t.strip().strip("-").strip()
                for t in new_titles.split("\n")
                if t.strip() and len(t.strip()) > 10
            ]

        return title_bank

    async def _get_recommended_structures(self, titles: List[Dict]) -> List[Dict]:
        """Retorna estruturas de titulo recomendadas"""

        system_prompt = """Voce e um analista de CTR e titulos virais.
Analise os titulos fornecidos e extraia as ESTRUTURAS mais eficazes.

Para cada estrutura:
1. Nome da estrutura
2. Template/formula
3. Exemplo
4. Por que funciona

Formato JSON array."""

        titles_text = "\n".join([
            f"- \"{t.get('titulo', '')}\" ({t.get('views_atuais', 0):,} views)"
            for t in titles[:30]
        ])

        user_prompt = f"""Titulos de SUCESSO (30+ dias, 30K+ views):
{titles_text}

Extraia as 5 estruturas de titulo mais eficazes.
Responda em JSON: [{{"nome": "...", "template": "...", "exemplo": "...", "porque_funciona": "..."}}]"""

        response = await self._call_gpt(system_prompt, user_prompt)

        # Tentar parsear JSON
        try:
            # Encontrar JSON na resposta
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # Fallback - retornar como texto
        return [{"raw_response": response}]

    async def generate_titles_for_topic(
        self,
        topic: str,
        subnicho: str,
        lingua: str,
        count: int = 10
    ) -> List[str]:
        """
        Gera titulos para um topico especifico.
        Util para uso sob demanda.

        Args:
            topic: Tema do video (ex: "rei que comeu a familia")
            subnicho: Subnicho do canal (ex: "Reis Perversos")
            lingua: Idioma (ex: "spanish")
            count: Quantidade de titulos

        Returns:
            Lista de titulos sugeridos
        """
        if not self.api_key:
            return ["OPENAI_API_KEY nao configurada"]

        # Buscar titulos de referencia do subnicho
        reference_titles = await self._get_successful_titles()
        relevant = [
            t for t in reference_titles
            if t.get("canais_monitorados", {}).get("subnicho", "").lower() == subnicho.lower()
        ][:10]

        reference_text = "\n".join([f"- {t.get('titulo', '')}" for t in relevant])

        system_prompt = f"""Voce e um copywriter de YouTube especializado em {subnicho}.
Gere titulos em {lingua} que maximizem CTR.
Use estruturas comprovadas e gatilhos psicologicos."""

        user_prompt = f"""Topico do video: {topic}
Subnicho: {subnicho}
Idioma: {lingua}

Titulos de referencia (sucesso no mesmo subnicho):
{reference_text}

Gere {count} titulos diferentes para este topico.
Varie as estruturas. Um titulo por linha."""

        response = await self._call_gpt(system_prompt, user_prompt)

        # Parsear titulos
        titles = [
            t.strip().strip("-").strip("1234567890.").strip()
            for t in response.split("\n")
            if t.strip() and len(t.strip()) > 10
        ]

        return titles[:count]

    async def adapt_title_to_language(
        self,
        original_title: str,
        source_lang: str,
        target_lang: str,
        subnicho: str
    ) -> List[str]:
        """
        Adapta um titulo de sucesso para outro idioma.

        Args:
            original_title: Titulo original que funcionou
            source_lang: Idioma original
            target_lang: Idioma destino
            subnicho: Subnicho do conteudo

        Returns:
            Lista de adaptacoes sugeridas
        """
        if not self.api_key:
            return ["OPENAI_API_KEY nao configurada"]

        system_prompt = f"""Voce e um especialista em localizacao de conteudo YouTube.
Adapte titulos mantendo o impacto e CTR alto.
NAO traduza literalmente - ADAPTE para funcionar no idioma destino."""

        user_prompt = f"""Titulo original ({source_lang}): "{original_title}"
Idioma destino: {target_lang}
Subnicho: {subnicho}

Gere 5 adaptacoes que funcionem em {target_lang}.
Mantenha a essencia mas adapte para a cultura/idioma.
Um titulo por linha."""

        response = await self._call_gpt(system_prompt, user_prompt)

        titles = [
            t.strip().strip("-").strip("1234567890.").strip()
            for t in response.split("\n")
            if t.strip() and len(t.strip()) > 10
        ]

        return titles[:5]
