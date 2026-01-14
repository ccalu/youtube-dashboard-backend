"""
TREND MONITOR - YouTube Collector
==================================
Coleta vídeos em trending do YouTube usando YouTube Data API v3.

NOTA IMPORTANTE:
- Precisa de API key do Google Cloud Console
- Quota: 10.000 unidades/dia (trending = 1 unidade por request)
- Trending retorna até 50 vídeos por país

Documentação: https://developers.google.com/youtube/v3
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("AVISO: google-api-python-client não instalado.")
    print("Execute: pip install google-api-python-client")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COUNTRIES, COLLECTION_CONFIG, API_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class YouTubeVideo:
    """Estrutura de um vídeo do YouTube"""
    title: str
    source: str = "youtube"
    video_id: str = ""
    channel_name: str = ""
    channel_id: str = ""
    country: str = ""
    language: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    published_at: str = ""
    thumbnail: str = ""
    category_id: str = ""
    tags: List[str] = None
    description: str = ""
    url: str = ""
    timestamp: str = ""


class YouTubeCollector:
    """
    Coletor de vídeos em trending do YouTube.

    Uso:
        collector = YouTubeCollector()
        videos = collector.collect_all_countries()
    """

    # Mapeamento de categoria ID para nome
    CATEGORIES = {
        "1": "Film & Animation",
        "2": "Autos & Vehicles",
        "10": "Music",
        "15": "Pets & Animals",
        "17": "Sports",
        "18": "Short Movies",
        "19": "Travel & Events",
        "20": "Gaming",
        "21": "Videoblogging",
        "22": "People & Blogs",
        "23": "Comedy",
        "24": "Entertainment",
        "25": "News & Politics",
        "26": "Howto & Style",
        "27": "Education",
        "28": "Science & Technology",
        "29": "Nonprofits & Activism",
        "30": "Movies",
        "31": "Anime/Animation",
        "32": "Action/Adventure",
        "33": "Classics",
        "34": "Comedy",
        "35": "Documentary",
        "36": "Drama",
        "37": "Family",
        "38": "Foreign",
        "39": "Horror",
        "40": "Sci-Fi/Fantasy",
        "41": "Thriller",
        "42": "Shorts",
        "43": "Shows",
        "44": "Trailers"
    }

    def __init__(self):
        """Inicializa o coletor"""
        self.youtube = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa cliente YouTube API"""
        if not YOUTUBE_API_AVAILABLE:
            logger.error("google-api-python-client não disponível")
            return

        api_key = API_CONFIG.get("youtube", {}).get("api_key")

        if not api_key:
            logger.warning("YouTube API key não configurada.")
            logger.warning("Configure a variável de ambiente YOUTUBE_API_KEY")
            return

        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            logger.info("Cliente YouTube API inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar YouTube API: {e}")
            self.youtube = None

    def collect_country(self, country_code: str) -> List[Dict]:
        """
        Coleta vídeos em trending de um país.

        Args:
            country_code: Código do país (US, BR, etc.)

        Returns:
            Lista de vídeos
        """
        if not self.youtube:
            logger.warning(f"YouTube API não disponível, pulando {country_code}")
            return []

        country_info = COUNTRIES.get(country_code)
        if not country_info:
            return []

        region = country_info["youtube_region"]
        language = country_info["language"]
        flag = country_info["flag"]

        logger.info(f"Coletando YouTube Trending para {flag} {country_code}...")

        videos = []
        try:
            # Primeira request: lista de vídeos trending
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region,
                maxResults=min(50, COLLECTION_CONFIG["youtube_videos_per_country"])
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                video = YouTubeVideo(
                    title=snippet.get("title", ""),
                    source="youtube",
                    video_id=item.get("id", ""),
                    channel_name=snippet.get("channelTitle", ""),
                    channel_id=snippet.get("channelId", ""),
                    country=country_code,
                    language=language,
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)),
                    comment_count=int(stats.get("commentCount", 0)),
                    published_at=snippet.get("publishedAt", ""),
                    thumbnail=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    category_id=snippet.get("categoryId", ""),
                    tags=snippet.get("tags", []),
                    description=snippet.get("description", "")[:500],  # Limitar descrição
                    url=f"https://youtube.com/watch?v={item.get('id', '')}",
                    timestamp=datetime.now().isoformat()
                )
                videos.append(asdict(video))

            logger.info(f"  {flag} {country_code}: {len(videos)} vídeos coletados")

        except HttpError as e:
            logger.error(f"Erro HTTP ao coletar YouTube {country_code}: {e}")
        except Exception as e:
            logger.error(f"Erro ao coletar YouTube {country_code}: {e}")

        # Rate limiting
        time.sleep(0.5)

        return videos

    def collect_all_countries(self) -> Dict[str, List[Dict]]:
        """
        Coleta vídeos em trending de todos os países.

        Returns:
            Dict com país como chave e lista de vídeos
        """
        all_videos = {}
        total = 0

        logger.info("=" * 50)
        logger.info("YOUTUBE - Iniciando coleta")
        logger.info("=" * 50)

        for country_code in COUNTRIES.keys():
            videos = self.collect_country(country_code)
            all_videos[country_code] = videos
            total += len(videos)

        logger.info("=" * 50)
        logger.info(f"YOUTUBE - Coleta finalizada: {total} vídeos")
        logger.info("=" * 50)

        return all_videos

    def get_category_name(self, category_id: str) -> str:
        """Retorna nome da categoria pelo ID"""
        return self.CATEGORIES.get(category_id, "Unknown")

    def search_videos(self, query: str, region: str = "US",
                      max_results: int = 25) -> List[Dict]:
        """
        Busca vídeos por query (útil para pesquisa direcionada).

        Args:
            query: Termo de busca
            region: Código do país
            max_results: Máximo de resultados

        Returns:
            Lista de vídeos encontrados
        """
        if not self.youtube:
            return []

        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                regionCode=region,
                maxResults=max_results
            )
            response = request.execute()

            videos = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")

                videos.append({
                    "title": snippet.get("title", ""),
                    "video_id": video_id,
                    "channel_name": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "url": f"https://youtube.com/watch?v={video_id}"
                })

            return videos

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []


# =============================================================================
# MOCK DATA (para testes sem API)
# =============================================================================

def get_mock_youtube_data() -> Dict[str, List[Dict]]:
    """Retorna dados mock realistas para testes sem API configurada"""
    timestamp = datetime.now().isoformat()

    mock_videos = {
        "US": [
            {"title": "The Dark History of Ancient Empires - What They Don't Teach You",
             "source": "youtube", "video_id": "dQw4w9WgXcQ", "channel_name": "History Explained",
             "view_count": 5200000, "category_id": "27", "language": "en",
             "description": "Exploring the brutal truth behind ancient civilizations"},
            {"title": "Psychology Tricks Manipulators Use On You",
             "source": "youtube", "video_id": "abc123def", "channel_name": "Mind Control",
             "view_count": 3800000, "category_id": "27", "language": "en",
             "description": "Dark psychology tactics used by narcissists"},
            {"title": "The Unsolved Mystery That Terrified America",
             "source": "youtube", "video_id": "xyz789abc", "channel_name": "True Crime Daily",
             "view_count": 2900000, "category_id": "35", "language": "en",
             "description": "A case that remains unsolved after 30 years"},
            {"title": "How This Entrepreneur Built a $10 Billion Empire From Nothing",
             "source": "youtube", "video_id": "biz456def", "channel_name": "Business Insider",
             "view_count": 4100000, "category_id": "22", "language": "en",
             "description": "The incredible story of a self-made billionaire"},
            {"title": "The Most Haunted Place on Earth - Real Footage",
             "source": "youtube", "video_id": "ghost123", "channel_name": "Paranormal Files",
             "view_count": 6700000, "category_id": "39", "language": "en",
             "description": "Actual paranormal activity caught on camera"},
        ],
        "BR": [
            {"title": "A História Sombria dos Reis Medievais Mais Cruéis",
             "source": "youtube", "video_id": "br001", "channel_name": "Canal História",
             "view_count": 1850000, "category_id": "27", "language": "pt",
             "description": "Os monarcas mais brutais da história"},
            {"title": "Mistérios Brasileiros que a Ciência Não Explica",
             "source": "youtube", "video_id": "br002", "channel_name": "Ciência Oculta",
             "view_count": 1420000, "category_id": "28", "language": "pt",
             "description": "Fenômenos inexplicáveis no Brasil"},
            {"title": "O Soldado Brasileiro que Sobreviveu ao Impossível",
             "source": "youtube", "video_id": "br003", "channel_name": "Histórias de Guerra",
             "view_count": 980000, "category_id": "27", "language": "pt",
             "description": "Relato real de um veterano da FEB"},
            {"title": "Psicologia do Dinheiro: Como Milionários Pensam",
             "source": "youtube", "video_id": "br004", "channel_name": "Mente Rica",
             "view_count": 2100000, "category_id": "22", "language": "pt",
             "description": "A mentalidade por trás do sucesso financeiro"},
        ],
        "ES": [
            {"title": "El Imperio Romano: Secretos de su Caída",
             "source": "youtube", "video_id": "es001", "channel_name": "Historia España",
             "view_count": 920000, "category_id": "27", "language": "es",
             "description": "Por qué realmente cayó Roma"},
            {"title": "Los Misterios Más Perturbadores de Latinoamérica",
             "source": "youtube", "video_id": "es002", "channel_name": "Misterios Sin Resolver",
             "view_count": 1150000, "category_id": "35", "language": "es",
             "description": "Casos que nadie puede explicar"},
        ],
        "FR": [
            {"title": "Les Secrets Sombres de la Psychologie Humaine",
             "source": "youtube", "video_id": "fr001", "channel_name": "Psycho France",
             "view_count": 780000, "category_id": "27", "language": "fr",
             "description": "Comment les manipulateurs contrôlent votre esprit"},
            {"title": "L'Empire Français: Gloire et Chute",
             "source": "youtube", "video_id": "fr002", "channel_name": "Histoire TV",
             "view_count": 650000, "category_id": "27", "language": "fr",
             "description": "L'histoire cachée de Napoléon"},
        ],
        "KR": [
            {"title": "한국 역사의 가장 어두운 미스터리",
             "source": "youtube", "video_id": "kr001", "channel_name": "역사채널",
             "view_count": 1350000, "category_id": "27", "language": "ko",
             "description": "한국사에서 가장 미스터리한 사건들"},
            {"title": "성공한 기업가들의 비밀 습관",
             "source": "youtube", "video_id": "kr002", "channel_name": "비즈니스 인사이트",
             "view_count": 890000, "category_id": "22", "language": "ko",
             "description": "한국 재벌들의 성공 비결"},
        ],
        "JP": [
            {"title": "日本の怖い都市伝説 - 本当にあった話",
             "source": "youtube", "video_id": "jp001", "channel_name": "恐怖チャンネル",
             "view_count": 1680000, "category_id": "39", "language": "ja",
             "description": "実際に起きた心霊現象"},
            {"title": "戦国時代の残酷な真実",
             "source": "youtube", "video_id": "jp002", "channel_name": "歴史探訪",
             "view_count": 920000, "category_id": "27", "language": "ja",
             "description": "教科書が教えない戦国の闇"},
        ],
        "IT": [
            {"title": "I Misteri Irrisolti della Storia Italiana",
             "source": "youtube", "video_id": "it001", "channel_name": "Storia Italia",
             "view_count": 520000, "category_id": "27", "language": "it",
             "description": "Casi che nessuno ha mai risolto"},
            {"title": "L'Impero Romano: La Vera Storia della Caduta",
             "source": "youtube", "video_id": "it002", "channel_name": "Roma Antica",
             "view_count": 680000, "category_id": "27", "language": "it",
             "description": "Perché Roma è davvero caduta"},
        ]
    }

    # Adicionar campos faltantes
    for country, videos in mock_videos.items():
        for video in videos:
            video["country"] = country
            video["timestamp"] = timestamp
            video["like_count"] = video.get("view_count", 0) // 20
            video["comment_count"] = video.get("view_count", 0) // 100
            video["url"] = f"https://youtube.com/watch?v={video.get('video_id', '')}"
            video["channel_id"] = ""
            video["thumbnail"] = f"https://img.youtube.com/vi/{video.get('video_id', '')}/hqdefault.jpg"
            video["published_at"] = timestamp
            video["tags"] = []

    return mock_videos


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - YouTube Collector")
    print("=" * 60)

    collector = YouTubeCollector()

    if collector.youtube:
        # Testar coleta real
        print("\nTestando coleta do Brasil...")
        videos = collector.collect_country("BR")

        if videos:
            print(f"\nTop 5 vídeos trending BR:")
            for i, video in enumerate(videos[:5], 1):
                views = video.get('view_count', 0)
                print(f"  {i}. [{views:,} views] {video['title'][:50]}...")
    else:
        print("\nAPI não configurada. Usando dados mock:")
        mock_data = get_mock_youtube_data()
        for country, videos in mock_data.items():
            print(f"\n{COUNTRIES[country]['flag']} {country}:")
            for video in videos[:2]:
                views = video.get('view_count', 0)
                print(f"  - [{views:,} views] {video['title'][:40]}...")
