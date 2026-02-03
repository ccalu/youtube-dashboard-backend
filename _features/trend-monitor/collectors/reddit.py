"""
TREND MONITOR - Reddit Collector
=================================
Coleta posts populares do Reddit usando PRAW.

NOTA IMPORTANTE:
- Precisa criar app em https://www.reddit.com/prefs/apps
- Rate limit: 60 requests/minuto
- Gratuito para uso pessoal

Documentação PRAW: https://praw.readthedocs.io/
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("AVISO: praw não instalado. Execute: pip install praw")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COUNTRIES, COLLECTION_CONFIG, API_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Estrutura de um post do Reddit"""
    title: str
    source: str = "reddit"
    subreddit: str = ""
    country: str = ""
    language: str = ""
    score: int = 0
    num_comments: int = 0
    url: str = ""
    permalink: str = ""
    author: str = ""
    created_utc: float = 0
    timestamp: str = ""


class RedditCollector:
    """
    Coletor de posts populares do Reddit.

    Uso:
        collector = RedditCollector()
        posts = collector.collect_all()
    """

    # Subreddits globais (inglês, conteúdo viral)
    GLOBAL_SUBS = [
        "all",
        "videos",
        "Documentaries",
        "todayilearned",
        "interestingasfuck",
        "explainlikeimfive",
        "AskHistorians",
        "history",
        "TrueReddit",
        "Damnthatsinteresting"
    ]

    def __init__(self):
        """Inicializa o coletor"""
        self.reddit = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa cliente PRAW"""
        if not PRAW_AVAILABLE:
            logger.error("praw não disponível")
            return

        config = API_CONFIG.get("reddit", {})
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        user_agent = config.get("user_agent", "TrendMonitor/1.0")

        # Se não tem credenciais, usa modo read-only (limitado)
        if not client_id or not client_secret:
            logger.warning("Credenciais Reddit não configuradas. Usando modo limitado.")
            logger.warning("Configure REDDIT_CLIENT_ID e REDDIT_CLIENT_SECRET")

            # Tenta modo read-only sem autenticação
            try:
                self.reddit = praw.Reddit(
                    client_id="",
                    client_secret="",
                    user_agent=user_agent
                )
                # Isso vai falhar, então marcamos como None
                self.reddit = None
            except:
                self.reddit = None
            return

        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Verificar se está funcionando
            self.reddit.user.me()
            logger.info("Cliente Reddit inicializado (autenticado)")
        except Exception as e:
            logger.warning(f"Usando modo read-only: {e}")
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    check_for_async=False
                )
            except Exception as e2:
                logger.error(f"Erro ao inicializar Reddit: {e2}")
                self.reddit = None

    def collect_subreddit(self, subreddit_name: str, country: str = "global",
                          language: str = "en", limit: int = None) -> List[Dict]:
        """
        Coleta posts de um subreddit específico.

        Args:
            subreddit_name: Nome do subreddit (sem r/)
            country: Código do país associado
            language: Idioma do conteúdo
            limit: Número de posts (usa config padrão se None)

        Returns:
            Lista de posts
        """
        if not self.reddit:
            logger.warning(f"Reddit não disponível, pulando r/{subreddit_name}")
            return []

        if limit is None:
            limit = COLLECTION_CONFIG["reddit_posts_per_sub"]

        logger.info(f"  Coletando r/{subreddit_name}...")

        posts = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            for submission in subreddit.hot(limit=limit):
                # Ignorar stickied posts (geralmente regras/avisos)
                if submission.stickied:
                    continue

                post = RedditPost(
                    title=submission.title,
                    source="reddit",
                    subreddit=subreddit_name,
                    country=country,
                    language=language,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=submission.url,
                    permalink=f"https://reddit.com{submission.permalink}",
                    author=str(submission.author) if submission.author else "[deleted]",
                    created_utc=submission.created_utc,
                    timestamp=datetime.now().isoformat()
                )
                posts.append(asdict(post))

            logger.info(f"    r/{subreddit_name}: {len(posts)} posts")

        except Exception as e:
            logger.error(f"Erro ao coletar r/{subreddit_name}: {e}")

        # Rate limiting
        time.sleep(1)

        return posts

    def collect_country(self, country_code: str) -> List[Dict]:
        """
        Coleta posts de subreddits de um país específico.

        Args:
            country_code: Código do país

        Returns:
            Lista de posts do país
        """
        country_info = COUNTRIES.get(country_code)
        if not country_info:
            return []

        language = country_info["language"]
        subs = country_info.get("reddit_subs", [])
        flag = country_info["flag"]

        logger.info(f"Coletando Reddit para {flag} {country_code}...")

        all_posts = []
        for sub in subs:
            posts = self.collect_subreddit(sub, country_code, language)
            all_posts.extend(posts)

        logger.info(f"  {flag} {country_code}: {len(all_posts)} posts total")
        return all_posts

    def collect_global(self) -> List[Dict]:
        """
        Coleta posts de subreddits globais (inglês).

        Returns:
            Lista de posts globais
        """
        logger.info("Coletando Reddit Global (EN)...")

        all_posts = []
        for sub in self.GLOBAL_SUBS:
            posts = self.collect_subreddit(sub, "global", "en")
            all_posts.extend(posts)

        logger.info(f"  Global: {len(all_posts)} posts total")
        return all_posts

    def collect_all(self) -> Dict[str, List[Dict]]:
        """
        Coleta posts de todos os países + global.

        Returns:
            Dict com país/global como chave e lista de posts
        """
        all_posts = {}
        total = 0

        logger.info("=" * 50)
        logger.info("REDDIT - Iniciando coleta")
        logger.info("=" * 50)

        # Coletar global primeiro
        global_posts = self.collect_global()
        all_posts["global"] = global_posts
        total += len(global_posts)

        # Coletar por país
        for country_code in COUNTRIES.keys():
            posts = self.collect_country(country_code)
            all_posts[country_code] = posts
            total += len(posts)

        logger.info("=" * 50)
        logger.info(f"REDDIT - Coleta finalizada: {total} posts")
        logger.info("=" * 50)

        return all_posts


# =============================================================================
# MOCK DATA (para testes sem API)
# =============================================================================

def get_mock_reddit_data() -> Dict[str, List[Dict]]:
    """Retorna dados mock realistas para testes sem API configurada"""
    timestamp = datetime.now().isoformat()

    mock_posts = {
        "global": [
            {"title": "Scientists discover that ancient civilizations were far more advanced than we thought",
             "source": "reddit", "subreddit": "science", "score": 45200, "language": "en",
             "url": "https://reddit.com/r/science/comments/abc123"},
            {"title": "The psychology behind manipulation: How narcissists control their victims",
             "source": "reddit", "subreddit": "psychology", "score": 38700, "language": "en",
             "url": "https://reddit.com/r/psychology/comments/def456"},
            {"title": "Ancient Roman military tactics that are still used today",
             "source": "reddit", "subreddit": "history", "score": 31500, "language": "en",
             "url": "https://reddit.com/r/history/comments/ghi789"},
            {"title": "The unsolved mystery of the Dyatlov Pass incident - New evidence emerges",
             "source": "reddit", "subreddit": "UnresolvedMysteries", "score": 28900, "language": "en",
             "url": "https://reddit.com/r/UnresolvedMysteries/comments/jkl012"},
            {"title": "How this startup founder went from homeless to billionaire in 5 years",
             "source": "reddit", "subreddit": "Entrepreneur", "score": 24600, "language": "en",
             "url": "https://reddit.com/r/Entrepreneur/comments/mno345"},
            {"title": "Creepy real ghost footage that cannot be explained",
             "source": "reddit", "subreddit": "Ghosts", "score": 19800, "language": "en",
             "url": "https://reddit.com/r/Ghosts/comments/pqr678"},
        ],
        "BR": [
            {"title": "Documentário revela segredos obscuros do Brasil colonial",
             "source": "reddit", "subreddit": "brasil", "score": 8500, "language": "pt",
             "url": "https://reddit.com/r/brasil/comments/br001"},
            {"title": "A história esquecida dos soldados brasileiros na Segunda Guerra",
             "source": "reddit", "subreddit": "brasil", "score": 6200, "language": "pt",
             "url": "https://reddit.com/r/brasil/comments/br002"},
            {"title": "Casos de mistério brasileiro que nunca foram resolvidos",
             "source": "reddit", "subreddit": "brasil", "score": 5100, "language": "pt",
             "url": "https://reddit.com/r/brasil/comments/br003"},
        ],
        "US": [
            {"title": "True crime documentary about the most dangerous serial killer nobody talks about",
             "source": "reddit", "subreddit": "Documentaries", "score": 22400, "language": "en",
             "url": "https://reddit.com/r/Documentaries/comments/us001"},
            {"title": "The dark psychology of cult leaders - How they control minds",
             "source": "reddit", "subreddit": "Documentaries", "score": 18900, "language": "en",
             "url": "https://reddit.com/r/Documentaries/comments/us002"},
        ],
        "ES": [
            {"title": "Los secretos más oscuros del Imperio Español que no te enseñan",
             "source": "reddit", "subreddit": "spain", "score": 4200, "language": "es",
             "url": "https://reddit.com/r/spain/comments/es001"},
        ],
        "FR": [
            {"title": "L'histoire cachée de la Révolution Française",
             "source": "reddit", "subreddit": "france", "score": 3800, "language": "fr",
             "url": "https://reddit.com/r/france/comments/fr001"},
        ],
        "KR": [
            {"title": "한국 전쟁의 알려지지 않은 이야기들",
             "source": "reddit", "subreddit": "korea", "score": 2900, "language": "ko",
             "url": "https://reddit.com/r/korea/comments/kr001"},
        ],
        "JP": [
            {"title": "日本の都市伝説：本当にあった怖い話",
             "source": "reddit", "subreddit": "japan", "score": 3500, "language": "ja",
             "url": "https://reddit.com/r/japan/comments/jp001"},
        ],
        "IT": [
            {"title": "I segreti nascosti del Vaticano",
             "source": "reddit", "subreddit": "italy", "score": 2600, "language": "it",
             "url": "https://reddit.com/r/italy/comments/it001"},
        ]
    }

    # Adicionar campos faltantes
    for country, posts in mock_posts.items():
        for post in posts:
            post["country"] = country if country != "global" else "US"
            post["timestamp"] = timestamp
            post["num_comments"] = post.get("score", 0) // 10
            post["permalink"] = post.get("url", "")
            post["author"] = "reddit_user"
            post["created_utc"] = 0

    return mock_posts


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Reddit Collector")
    print("=" * 60)

    collector = RedditCollector()

    if collector.reddit:
        # Testar coleta real
        print("\nTestando coleta de r/all...")
        posts = collector.collect_subreddit("all", "global", "en", limit=10)

        if posts:
            print(f"\nTop 5 posts de r/all:")
            for i, post in enumerate(posts[:5], 1):
                score = post.get('score', 0)
                print(f"  {i}. [{score:,} pts] {post['title'][:60]}...")
    else:
        print("\nAPI não configurada. Usando dados mock:")
        mock_data = get_mock_reddit_data()
        for country, posts in mock_data.items():
            print(f"\n{country}:")
            for post in posts:
                print(f"  - {post['title'][:50]}...")
