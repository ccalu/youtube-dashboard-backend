"""
TREND MONITOR - Hacker News Collector
=====================================
Coleta top stories do Hacker News usando API pública.

API GRATUITA - SEM CREDENCIAL NECESSÁRIA!
Documentação: https://github.com/HackerNews/API
"""

import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLLECTION_CONFIG, QUALITY_FILTERS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Base URL
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


@dataclass
class HNStory:
    """Estrutura de uma story do Hacker News"""
    title: str
    source: str = "hackernews"
    url: str = ""
    score: int = 0
    num_comments: int = 0
    author: str = ""
    hn_id: int = 0
    hn_url: str = ""  # Link para discussão no HN
    timestamp: str = ""
    country: str = "global"
    language: str = "en"


class HackerNewsCollector:
    """
    Coletor de stories do Hacker News.

    API 100% gratuita, sem limites rigorosos.

    Uso:
        collector = HackerNewsCollector()
        stories = collector.collect_top_stories(limit=50)
    """

    def __init__(self, timeout: int = 30):
        """
        Inicializa o coletor.

        Args:
            timeout: Timeout em segundos para requests
        """
        self.timeout = timeout
        self.session = requests.Session()
        logger.info("HackerNews Collector inicializado (API gratuita)")

    def _get_item(self, item_id: int) -> Optional[Dict]:
        """
        Busca detalhes de um item específico.

        Args:
            item_id: ID do item no HN

        Returns:
            Dict com dados do item ou None se erro
        """
        try:
            url = f"{HN_API_BASE}/item/{item_id}.json"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar item {item_id}: {e}")
            return None

    def _get_story_ids(self, story_type: str = "top") -> List[int]:
        """
        Busca IDs das stories.

        Args:
            story_type: "top", "new", "best"

        Returns:
            Lista de IDs
        """
        endpoints = {
            "top": "topstories",
            "new": "newstories",
            "best": "beststories"
        }

        try:
            endpoint = endpoints.get(story_type, "topstories")
            url = f"{HN_API_BASE}/{endpoint}.json"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar {story_type} stories: {e}")
            return []

    def collect_stories(self, story_type: str = "top", limit: int = 50) -> List[Dict]:
        """
        Coleta stories do Hacker News.

        Args:
            story_type: "top", "new", "best"
            limit: Número máximo de stories

        Returns:
            Lista de stories com dados completos
        """
        logger.info(f"Coletando {limit} {story_type} stories do Hacker News...")

        story_ids = self._get_story_ids(story_type)
        if not story_ids:
            logger.warning("Nenhum ID de story encontrado")
            return []

        stories = []
        for i, story_id in enumerate(story_ids[:limit]):
            item = self._get_item(story_id)

            if not item or item.get("type") != "story":
                continue

            # Pular stories sem URL (são perguntas Ask HN)
            external_url = item.get("url", "")

            story = HNStory(
                title=item.get("title", ""),
                source="hackernews",
                url=external_url,  # URL do artigo original
                score=item.get("score", 0),
                num_comments=item.get("descendants", 0),
                author=item.get("by", ""),
                hn_id=story_id,
                hn_url=f"https://news.ycombinator.com/item?id={story_id}",  # URL da discussão
                timestamp=datetime.now().isoformat(),
                country="global",
                language="en"
            )

            stories.append(asdict(story))

            # Rate limiting leve (API é generosa)
            if i % 10 == 0 and i > 0:
                time.sleep(0.5)

        logger.info(f"  Hacker News: {len(stories)} stories coletadas")
        return stories

    def collect_top_stories(self, limit: int = 50) -> List[Dict]:
        """Coleta top stories"""
        return self.collect_stories("top", limit)

    def collect_new_stories(self, limit: int = 30) -> List[Dict]:
        """Coleta new stories"""
        return self.collect_stories("new", limit)

    def collect_best_stories(self, limit: int = 30) -> List[Dict]:
        """Coleta best stories"""
        return self.collect_stories("best", limit)

    def collect_all(self) -> Dict[str, List[Dict]]:
        """
        Coleta todas as categorias de stories (básico).

        Returns:
            Dict com categorias como chave
        """
        logger.info("=" * 50)
        logger.info("HACKER NEWS - Iniciando coleta")
        logger.info("=" * 50)

        all_stories = {
            "global": []  # HN é sempre global/inglês
        }

        # Coletar top stories
        top = self.collect_top_stories(limit=50)
        all_stories["global"].extend(top)

        # Coletar best stories (sem duplicar)
        best = self.collect_best_stories(limit=20)
        existing_ids = {s["hn_id"] for s in all_stories["global"]}
        for story in best:
            if story["hn_id"] not in existing_ids:
                all_stories["global"].append(story)

        total = len(all_stories["global"])

        logger.info("=" * 50)
        logger.info(f"HACKER NEWS - Coleta finalizada: {total} stories")
        logger.info("=" * 50)

        return all_stories

    def collect_all_expanded(self) -> Dict:
        """
        Coleta EXPANDIDA de stories do Hacker News.
        Coleta 500 stories: 300 top + 200 best (deduplicado).

        API GRATUITA - sem custo!

        Returns:
            Dict com stories e estatísticas
        """
        target = COLLECTION_CONFIG.get("hackernews_stories", 500)
        filters = QUALITY_FILTERS.get("hackernews", {})

        logger.info("=" * 60)
        logger.info("HACKER NEWS COLETA EXPANDIDA - Iniciando")
        logger.info(f"Alvo: {target} stories")
        logger.info("=" * 60)

        all_stories = []
        seen_ids = set()
        filtered_count = 0

        # Filtros
        min_score = filters.get("min_score", 50)
        min_comments = filters.get("min_comments", 10)
        exclude_domains = filters.get("exclude_domains", [])

        # 1. Coletar TOP stories
        logger.info("\n📰 Coletando TOP stories...")
        top_ids = self._get_story_ids("top")
        logger.info(f"  Encontrados: {len(top_ids)} IDs")

        for i, story_id in enumerate(top_ids[:300]):
            item = self._get_item(story_id)

            if not item or item.get("type") != "story":
                continue

            # Verificar duplicata
            if story_id in seen_ids:
                continue

            # Aplicar filtros de qualidade
            score = item.get("score", 0)
            comments = item.get("descendants", 0)
            url = item.get("url", "")

            # Filtro: score mínimo
            if score < min_score:
                filtered_count += 1
                continue

            # Filtro: comentários mínimos
            if comments < min_comments:
                filtered_count += 1
                continue

            # Filtro: domínios excluídos
            if any(domain in url.lower() for domain in exclude_domains):
                filtered_count += 1
                continue

            story = HNStory(
                title=item.get("title", ""),
                source="hackernews",
                url=url,
                score=score,
                num_comments=comments,
                author=item.get("by", ""),
                hn_id=story_id,
                hn_url=f"https://news.ycombinator.com/item?id={story_id}",
                timestamp=datetime.now().isoformat(),
                country="global",
                language="en"
            )

            all_stories.append(asdict(story))
            seen_ids.add(story_id)

            # Rate limiting
            if i % 20 == 0 and i > 0:
                time.sleep(0.5)

        logger.info(f"  ✓ TOP: {len(all_stories)} stories válidas")

        # 2. Coletar BEST stories (complementar)
        logger.info("\n⭐ Coletando BEST stories...")
        best_ids = self._get_story_ids("best")
        logger.info(f"  Encontrados: {len(best_ids)} IDs")

        best_count = 0
        for i, story_id in enumerate(best_ids[:200]):
            if story_id in seen_ids:
                continue

            item = self._get_item(story_id)

            if not item or item.get("type") != "story":
                continue

            score = item.get("score", 0)
            comments = item.get("descendants", 0)
            url = item.get("url", "")

            if score < min_score or comments < min_comments:
                filtered_count += 1
                continue

            if any(domain in url.lower() for domain in exclude_domains):
                filtered_count += 1
                continue

            story = HNStory(
                title=item.get("title", ""),
                source="hackernews",
                url=url,
                score=score,
                num_comments=comments,
                author=item.get("by", ""),
                hn_id=story_id,
                hn_url=f"https://news.ycombinator.com/item?id={story_id}",
                timestamp=datetime.now().isoformat(),
                country="global",
                language="en"
            )

            all_stories.append(asdict(story))
            seen_ids.add(story_id)
            best_count += 1

            if i % 20 == 0 and i > 0:
                time.sleep(0.5)

        logger.info(f"  ✓ BEST: {best_count} stories adicionadas")

        # Ordenar por score
        all_stories.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Resultado
        result = {
            "global": all_stories,
            "stats": {
                "total": len(all_stories),
                "filtered": filtered_count,
                "top_count": len(all_stories) - best_count,
                "best_count": best_count
            }
        }

        logger.info("\n" + "=" * 60)
        logger.info("HACKER NEWS COLETA EXPANDIDA - FINALIZADO")
        logger.info("=" * 60)
        logger.info(f"📊 ESTATÍSTICAS:")
        logger.info(f"  • Total:     {result['stats']['total']} stories")
        logger.info(f"  • Filtradas: {result['stats']['filtered']} (baixa qualidade)")
        logger.info(f"  • Top:       {result['stats']['top_count']} stories")
        logger.info(f"  • Best:      {result['stats']['best_count']} stories")
        logger.info("=" * 60)

        return result


# =============================================================================
# MOCK DATA (para testes sem API)
# =============================================================================

def get_mock_hackernews_data() -> Dict[str, List[Dict]]:
    """Retorna dados mock realistas para testes"""
    timestamp = datetime.now().isoformat()

    mock_stories = {
        "global": [
            {
                "title": "OpenAI Announces GPT-5 with Revolutionary Capabilities",
                "source": "hackernews",
                "url": "https://openai.com/blog/gpt-5",
                "score": 2847,
                "num_comments": 1523,
                "author": "sama",
                "hn_id": 12345678,
                "hn_url": "https://news.ycombinator.com/item?id=12345678",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "The Psychology of Successful Entrepreneurs: A Deep Dive",
                "source": "hackernews",
                "url": "https://blog.example.com/entrepreneur-psychology",
                "score": 1892,
                "num_comments": 876,
                "author": "pg",
                "hn_id": 12345679,
                "hn_url": "https://news.ycombinator.com/item?id=12345679",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "Ancient Roman Engineering: How They Built Structures That Last 2000 Years",
                "source": "hackernews",
                "url": "https://archeology.example.com/roman-engineering",
                "score": 1654,
                "num_comments": 543,
                "author": "historian",
                "hn_id": 12345680,
                "hn_url": "https://news.ycombinator.com/item?id=12345680",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "The Unsolved Mystery of the Dyatlov Pass Incident - New Evidence",
                "source": "hackernews",
                "url": "https://mystery.example.com/dyatlov-pass-2025",
                "score": 1432,
                "num_comments": 892,
                "author": "investigator",
                "hn_id": 12345681,
                "hn_url": "https://news.ycombinator.com/item?id=12345681",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "From Startup Founder to Billionaire: The Story of Stripe",
                "source": "hackernews",
                "url": "https://business.example.com/stripe-story",
                "score": 1287,
                "num_comments": 654,
                "author": "pcollison",
                "hn_id": 12345682,
                "hn_url": "https://news.ycombinator.com/item?id=12345682",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "Dark Psychology: How Manipulation Tactics Work",
                "source": "hackernews",
                "url": "https://psychology.example.com/dark-tactics",
                "score": 1156,
                "num_comments": 723,
                "author": "psychologist",
                "hn_id": 12345683,
                "hn_url": "https://news.ycombinator.com/item?id=12345683",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "The Fall of Civilizations: Lessons from History",
                "source": "hackernews",
                "url": "https://history.example.com/fall-civilizations",
                "score": 1089,
                "num_comments": 445,
                "author": "historian2",
                "hn_id": 12345684,
                "hn_url": "https://news.ycombinator.com/item?id=12345684",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            },
            {
                "title": "Haunted Places: The Science Behind Ghost Sightings",
                "source": "hackernews",
                "url": "https://science.example.com/ghost-science",
                "score": 987,
                "num_comments": 567,
                "author": "skeptic",
                "hn_id": 12345685,
                "hn_url": "https://news.ycombinator.com/item?id=12345685",
                "timestamp": timestamp,
                "country": "global",
                "language": "en"
            }
        ]
    }

    return mock_stories


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Hacker News Collector")
    print("=" * 60)

    collector = HackerNewsCollector()

    # Testar coleta real
    print("\nTestando coleta de top stories...")
    stories = collector.collect_top_stories(limit=10)

    if stories:
        print(f"\nTop 10 stories do Hacker News:")
        for i, story in enumerate(stories, 1):
            score = story.get('score', 0)
            title = story.get('title', '')[:50]
            print(f"  {i}. [{score} pts] {title}...")
            print(f"     URL: {story.get('url', 'N/A')[:50]}...")
            print(f"     HN: {story.get('hn_url', '')}")
    else:
        print("Nenhuma story coletada")
