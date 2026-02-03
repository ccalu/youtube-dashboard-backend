"""
TREND MONITOR - Relevance Filter
=================================
Sistema de scoring para determinar relevância de trends para os subnichos.

COMO FUNCIONA O SCORE:
- Match de keywords: até 60 pontos
- Cross-platform (aparece em múltiplas fontes): até 20 pontos
- Multi-country (aparece em múltiplos países): até 20 pontos
- Score máximo: 100

EXEMPLO:
- "Roman Empire documentary" matchando "roman", "empire", "documentary"
- Aparece no Google Trends + YouTube = +20 pontos
- Aparece em 3 países = +10 pontos
- Score final: 60 + 20 + 10 = 90
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUBNICHO_CONFIG, COUNTRIES, get_active_subnichos

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScoredTrend:
    """Trend com score de relevância calculado"""
    title: str
    source: str
    country: str
    language: str
    score: int
    matched_subnichos: List[Dict]
    sources_found: List[str]
    countries_found: List[str]
    is_cross_platform: bool
    is_multi_country: bool
    suggestion: str = ""
    original_data: Dict = None


class RelevanceFilter:
    """
    Filtro de relevância para classificar trends por subnicho.

    Uso:
        filter = RelevanceFilter()
        scored = filter.score_trend("Roman Empire fall documentary", "en")
        filtered = filter.filter_all_trends(all_trends_data)
    """

    def __init__(self):
        """Inicializa o filtro com subnichos ativos"""
        self.subnichos = get_active_subnichos()
        self._compile_patterns()
        logger.info(f"RelevanceFilter inicializado com {len(self.subnichos)} subnichos")

    def _compile_patterns(self):
        """Compila padrões regex para busca mais rápida"""
        self.patterns = {}

        for subnicho_key, subnicho_data in self.subnichos.items():
            self.patterns[subnicho_key] = {}

            for lang, keywords in subnicho_data.get("keywords", {}).items():
                # Criar pattern que matcha qualquer keyword
                # Escape caracteres especiais e compile
                escaped = [re.escape(kw.lower()) for kw in keywords]
                pattern = re.compile(r'\b(' + '|'.join(escaped) + r')\b', re.IGNORECASE)
                self.patterns[subnicho_key][lang] = pattern

    def score_trend(self, title: str, language: str = "en") -> List[Dict]:
        """
        Calcula score de um trend para cada subnicho.

        Args:
            title: Título do trend
            language: Idioma do conteúdo

        Returns:
            Lista de matches com score para cada subnicho
        """
        matches = []
        title_lower = title.lower()

        for subnicho_key, subnicho_data in self.subnichos.items():
            keywords = subnicho_data.get("keywords", {}).get(language, [])

            # Também checar inglês como fallback
            if language != "en":
                keywords = keywords + subnicho_data.get("keywords", {}).get("en", [])

            matched_keywords = []
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    matched_keywords.append(keyword)

            if matched_keywords:
                # Calcular score baseado em matches
                # Cada keyword match = 15 pontos, máximo 60
                keyword_score = min(len(matched_keywords) * 15, 60)

                matches.append({
                    "subnicho": subnicho_key,
                    "name": subnicho_data["name"],
                    "icon": subnicho_data["icon"],
                    "score": keyword_score,
                    "matched_keywords": matched_keywords
                })

        # Ordenar por score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def analyze_cross_platform(self, trends_by_source: Dict) -> Dict[str, List[str]]:
        """
        Identifica trends que aparecem em múltiplas plataformas.

        Args:
            trends_by_source: Dict com source como key e lista de trends

        Returns:
            Dict com título normalizado e lista de sources onde aparece
        """
        title_sources = defaultdict(set)

        for source, trends in trends_by_source.items():
            for trend in trends:
                title = self._normalize_title(trend.get("title", ""))
                if title:
                    title_sources[title].add(source)

        # Converter sets para lists
        return {k: list(v) for k, v in title_sources.items()}

    def analyze_multi_country(self, trends_by_country: Dict) -> Dict[str, List[str]]:
        """
        Identifica trends que aparecem em múltiplos países.

        Args:
            trends_by_country: Dict com país como key e lista de trends

        Returns:
            Dict com título normalizado e lista de países onde aparece
        """
        title_countries = defaultdict(set)

        for country, trends in trends_by_country.items():
            for trend in trends:
                title = self._normalize_title(trend.get("title", ""))
                if title:
                    title_countries[title].add(country)

        return {k: list(v) for k, v in title_countries.items()}

    def _normalize_title(self, title: str) -> str:
        """
        Normaliza título para comparação.
        Remove pontuação, converte para lowercase.
        """
        if not title:
            return ""

        # Remove caracteres especiais, mantém apenas alfanuméricos e espaços
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        # Remove espaços extras
        normalized = ' '.join(normalized.split())
        return normalized

    def _deduplicate_trends(self, trends: List[Dict]) -> List[Dict]:
        """
        Remove duplicatas de trends.
        - YouTube: deduplica por video_id
        - Outros: deduplica por titulo normalizado
        Mantém o item com mais views/volume e agrega países.
        """
        seen = {}  # key -> trend com mais views

        for trend in trends:
            source = trend.get("source_type", trend.get("source", ""))

            # Gerar chave unica
            if source == "youtube":
                key = trend.get("video_id", "") or self._normalize_title(trend.get("title", ""))
            else:
                key = self._normalize_title(trend.get("title", ""))

            if not key:
                continue

            # Pegar volume para comparacao
            volume = trend.get("volume") or trend.get("view_count") or trend.get("score") or 0
            country = trend.get("country", "global")

            if key in seen:
                existing = seen[key]
                existing_volume = existing.get("volume") or existing.get("view_count") or existing.get("score") or 0

                # Agregar paises
                if "_countries_seen" not in existing:
                    existing["_countries_seen"] = {existing.get("country", "global")}
                existing["_countries_seen"].add(country)

                # Manter o de maior volume
                if volume > existing_volume:
                    trend["_countries_seen"] = existing["_countries_seen"]
                    seen[key] = trend
            else:
                trend["_countries_seen"] = {country}
                seen[key] = trend

        # Converter _countries_seen para lista
        result = []
        for trend in seen.values():
            if "_countries_seen" in trend:
                trend["countries_aggregated"] = list(trend["_countries_seen"])
                del trend["_countries_seen"]
            result.append(trend)

        return result

    def filter_all_trends(self, all_data: Dict) -> Dict:
        """
        Processa todos os trends e retorna dados filtrados e organizados.

        Args:
            all_data: Dict com estrutura:
                {
                    "google_trends": {"US": [...], "BR": [...]},
                    "reddit": {"global": [...], "US": [...]},
                    "youtube": {"US": [...], "BR": [...]}
                }

        Returns:
            Dict com trends organizados por subnicho e país
        """
        logger.info("Iniciando filtragem de relevância...")

        # Preparar estruturas
        all_trends_flat = []
        trends_by_source = defaultdict(list)
        trends_by_country = defaultdict(list)

        # Flatten e organizar
        for source_type, source_data in all_data.items():
            for country, trends in source_data.items():
                for trend in trends:
                    trend["source_type"] = source_type
                    all_trends_flat.append(trend)
                    trends_by_source[source_type].append(trend)
                    trends_by_country[country].append(trend)

        # DEDUPLICAR antes de processar
        original_count = len(all_trends_flat)
        all_trends_flat = self._deduplicate_trends(all_trends_flat)
        dedup_count = len(all_trends_flat)
        logger.info(f"Deduplicação: {original_count} -> {dedup_count} ({original_count - dedup_count} duplicatas removidas)")

        logger.info(f"Total de trends para processar: {len(all_trends_flat)}")

        # Analisar cross-platform e multi-country
        cross_platform = self.analyze_cross_platform(trends_by_source)
        multi_country = self.analyze_multi_country(trends_by_country)

        # Processar cada trend
        scored_trends = []
        by_subnicho = defaultdict(list)
        by_country = defaultdict(list)

        for trend in all_trends_flat:
            title = trend.get("title", "")
            language = trend.get("language", "en")
            country = trend.get("country", "global")
            source = trend.get("source_type", trend.get("source", "unknown"))

            # Calcular score por subnicho
            matches = self.score_trend(title, language)

            if not matches:
                continue

            # Verificar cross-platform e multi-country
            normalized = self._normalize_title(title)
            sources_found = cross_platform.get(normalized, [source])
            countries_found = multi_country.get(normalized, [country])

            is_cross = len(sources_found) > 1
            is_multi = len(countries_found) > 1

            # Bônus para cross-platform e multi-country
            bonus = 0
            if is_cross:
                bonus += 20
            if is_multi:
                bonus += min(len(countries_found) - 1, 4) * 5  # 5 pontos por país extra, max 20

            # Atualizar scores com bônus
            for match in matches:
                match["score"] = min(match["score"] + bonus, 100)

            # Extrair volume/audiência do trend original
            volume = trend.get("volume") or trend.get("view_count") or trend.get("score") or 0

            # Extrair URL
            url = trend.get("url") or trend.get("permalink") or ""

            # Extrair descrição
            description = trend.get("description") or ""

            # Criar scored trend
            best_match = matches[0]

            # Gerar análise breve baseada no score e dados
            analysis = self._generate_analysis(title, best_match, volume, is_cross, is_multi)
            scored = {
                "title": title,
                "source": source,
                "country": country,
                "language": language,
                "score": best_match["score"],
                "best_subnicho": best_match["subnicho"],
                "best_subnicho_name": best_match["name"],
                "best_subnicho_icon": best_match["icon"],
                "all_matches": matches,
                "sources_found": sources_found,
                "countries_found": countries_found,
                "is_cross_platform": is_cross,
                "is_multi_country": is_multi,
                "volume": volume,
                "url": url,
                "description": description,
                "analysis": analysis,
                "original_data": trend
            }

            scored_trends.append(scored)

            # Organizar por subnicho
            by_subnicho[best_match["subnicho"]].append(scored)

            # Organizar por país
            by_country[country].append(scored)

        # Ordenar tudo por score
        for key in by_subnicho:
            by_subnicho[key].sort(key=lambda x: x["score"], reverse=True)

        for key in by_country:
            by_country[key].sort(key=lambda x: x["score"], reverse=True)

        scored_trends.sort(key=lambda x: x["score"], reverse=True)

        # Preparar trends raw por fonte (SEM filtro de subnicho) para ABA GERAL
        raw_by_source = defaultdict(list)
        for trend in all_trends_flat:
            source = trend.get("source_type", trend.get("source", "unknown"))
            title = trend.get("title", "")
            country = trend.get("country", "global")
            language = trend.get("language", "en")
            volume = trend.get("volume") or trend.get("view_count") or trend.get("score") or 0
            url = trend.get("url") or trend.get("permalink") or trend.get("hn_url") or ""

            # Verificar cross-platform e multi-country
            normalized = self._normalize_title(title)
            sources_found = cross_platform.get(normalized, [source])
            countries_found = multi_country.get(normalized, [country])
            is_cross = len(sources_found) > 1
            is_multi = len(countries_found) > 1

            raw_trend = {
                "title": title,
                "source": source,
                "country": country,
                "language": language,
                "volume": volume,
                "url": url,
                "hn_url": trend.get("hn_url", ""),
                "sources_found": sources_found,
                "countries_found": countries_found,
                "is_cross_platform": is_cross,
                "is_multi_country": is_multi,
                "subreddit": trend.get("subreddit", ""),
                "channel_title": trend.get("channel_title", ""),
                "author": trend.get("author", ""),
                "num_comments": trend.get("num_comments", 0),
                "original_data": trend
            }
            raw_by_source[source].append(raw_trend)

        # Ordenar raw trends por volume
        for source in raw_by_source:
            raw_by_source[source].sort(key=lambda x: x.get("volume", 0), reverse=True)

        result = {
            "all_scored": scored_trends,
            "all_raw": all_trends_flat,  # Todos os trends sem filtro (DEDUPLICADOS)
            "raw_by_source": dict(raw_by_source),  # Todos os trends por fonte (para ABA GERAL)
            "by_subnicho": dict(by_subnicho),
            "by_country": dict(by_country),
            "stats": {
                "total_before_dedup": original_count,
                "total_after_dedup": dedup_count,
                "duplicates_removed": original_count - dedup_count,
                "total_processed": len(all_trends_flat),
                "total_relevant": len(scored_trends),
                "total_raw": len(all_trends_flat),
                "cross_platform_count": sum(1 for t in scored_trends if t["is_cross_platform"]),
                "multi_country_count": sum(1 for t in scored_trends if t["is_multi_country"]),
                "by_subnicho_count": {k: len(v) for k, v in by_subnicho.items()},
                "by_country_count": {k: len(v) for k, v in by_country.items()},
                "by_source_count": {k: len(v) for k, v in raw_by_source.items()}
            }
        }

        logger.info(f"Filtragem concluída:")
        logger.info(f"  - Total relevantes: {result['stats']['total_relevant']}")
        logger.info(f"  - Cross-platform: {result['stats']['cross_platform_count']}")
        logger.info(f"  - Multi-country: {result['stats']['multi_country_count']}")

        return result

    def _generate_analysis(self, title: str, match: Dict, volume: int,
                           is_cross: bool, is_multi: bool) -> str:
        """
        Gera análise breve sobre o potencial do trend.

        Args:
            title: Título do trend
            match: Melhor match de subnicho
            volume: Volume/audiência
            is_cross: Se aparece em múltiplas plataformas
            is_multi: Se aparece em múltiplos países

        Returns:
            Análise breve em texto
        """
        parts = []

        # Análise de volume
        if volume >= 1000000:
            parts.append("ALTO VOLUME - Tendência massiva")
        elif volume >= 500000:
            parts.append("Volume significativo - Boa oportunidade")
        elif volume >= 100000:
            parts.append("Volume moderado - Vale explorar")
        elif volume > 0:
            parts.append("Volume inicial - Potencial crescimento")

        # Análise de score
        score = match.get("score", 0)
        if score >= 80:
            parts.append("Match perfeito com seu nicho")
        elif score >= 60:
            parts.append("Boa relevância para seu conteúdo")
        elif score >= 40:
            parts.append("Relevância moderada")

        # Bônus cross-platform
        if is_cross:
            parts.append("Viral em múltiplas plataformas")

        # Bônus multi-country
        if is_multi:
            parts.append("Interesse global - Adaptar para idiomas")

        # Recomendação final
        if score >= 70 and volume >= 500000:
            parts.append("RECOMENDADO: Produzir conteúdo urgente")
        elif score >= 60 and (is_cross or is_multi):
            parts.append("OPORTUNIDADE: Considerar produção")
        elif score >= 50:
            parts.append("MONITORAR: Acompanhar evolução")

        return " | ".join(parts) if parts else "Avaliar manualmente"

    def generate_video_suggestion(self, trend: Dict, language: str = "pt") -> str:
        """
        Gera sugestão de título de vídeo para um trend.

        Args:
            trend: Trend scored
            language: Idioma para o título

        Returns:
            Sugestão de título
        """
        title = trend.get("title", "")
        subnicho = trend.get("best_subnicho", "")

        # Templates por subnicho
        templates = {
            "terror": [
                "A Verdade Assustadora Sobre {topic}",
                "{topic}: O Que Eles Não Querem Que Você Saiba",
                "Por Que {topic} Vai Te Dar Pesadelos"
            ],
            "misterios": [
                "O Mistério de {topic} Que Ninguém Conseguiu Resolver",
                "{topic}: As Teorias Mais Perturbadoras",
                "A Verdade Oculta Por Trás de {topic}"
            ],
            "guerras_civilizacoes": [
                "Como {topic} Mudou a História Para Sempre",
                "A Ascensão e Queda de {topic}",
                "Por Que {topic} Foi o Mais Poderoso da História"
            ],
            "psicologia_mindset": [
                "A Psicologia Por Trás de {topic}",
                "Como {topic} Manipula Sua Mente",
                "O Segredo de {topic} Que Vai Mudar Sua Vida"
            ],
            "historias_sombrias": [
                "O Lado Mais Sombrio de {topic}",
                "{topic}: A História Que Você Nunca Ouviu",
                "Os Segredos Macabros de {topic}"
            ],
            "empreendedorismo": [
                "Como {topic} Construiu um Império",
                "A Estratégia Genial de {topic}",
                "De Zero a Bilhões: A História de {topic}"
            ],
            "relatos_guerra": [
                "O Soldado Que Sobreviveu a {topic}",
                "A História Real de {topic}",
                "Relatos Chocantes de {topic}"
            ]
        }

        default_templates = [
            "A Verdade Sobre {topic}",
            "O Que Você Não Sabe Sobre {topic}",
            "{topic}: A História Completa"
        ]

        # Escolher template
        template_list = templates.get(subnicho, default_templates)
        template = template_list[hash(title) % len(template_list)]

        # Simplificar o topic
        topic = title[:50] if len(title) > 50 else title

        return template.format(topic=topic)


def calculate_relevance_score(title: str, keywords: List[str]) -> int:
    """
    Função helper para calcular score de relevância simples.

    Args:
        title: Título para analisar
        keywords: Lista de keywords para match

    Returns:
        Score de 0-100
    """
    title_lower = title.lower()
    matches = sum(1 for kw in keywords if kw.lower() in title_lower)
    return min(matches * 20, 100)


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Relevance Filter")
    print("=" * 60)

    filter = RelevanceFilter()

    # Testar alguns títulos
    test_titles = [
        ("The Dark History of Roman Emperors", "en"),
        ("Psychology of Manipulation: Dark Tactics", "en"),
        ("Haunted House Documentary 2024", "en"),
        ("How This Entrepreneur Built a Billion Dollar Empire", "en"),
        ("Unsolved Mystery: The Case That Shocked Everyone", "en"),
        ("O Império Romano e Sua Queda", "pt"),
        ("Psicologia do Medo: Como Funciona", "pt"),
    ]

    print("\nTestando scoring de títulos:")
    for title, lang in test_titles:
        matches = filter.score_trend(title, lang)
        if matches:
            print(f"\n\"{title[:40]}...\"")
            for match in matches[:3]:
                print(f"  {match['icon']} {match['name']}: {match['score']}pts")
                print(f"     Keywords: {', '.join(match['matched_keywords'][:3])}")
        else:
            print(f"\n\"{title[:40]}...\" - Nenhum match")

    # Testar sugestão de vídeo
    print("\n\nTestando geração de sugestões:")
    sample_trend = {
        "title": "Roman Empire Fall Documentary",
        "best_subnicho": "guerras_civilizacoes"
    }
    suggestion = filter.generate_video_suggestion(sample_trend)
    print(f"  Original: {sample_trend['title']}")
    print(f"  Sugestão: {suggestion}")
