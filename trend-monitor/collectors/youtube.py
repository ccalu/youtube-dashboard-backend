"""
TREND MONITOR - YouTube Collector (Expandido)
==============================================
Coleta vídeos em trending e busca por keywords no YouTube.

CUSTOS DE API:
- videos.list (trending): 1 unit por request
- search.list (keywords): 100 units por request

COLETA EXPANDIDA:
- Trending: 7 países × 4 páginas = 28 units (~700 vídeos)
- Search Nichado: 7 subnichos × 7 países = 4.900 units (~1.200 vídeos)
- Search Descoberta: 10 keywords × 3 países = 3.000 units (~750 vídeos)
- TOTAL: ~7.928 units (~2.650 vídeos)

Documentação: https://developers.google.com/youtube/v3
"""

import time
import logging
from datetime import datetime, timedelta
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
    duration_seconds: int = 0


# Duracao minima em segundos (3 minutos = 180s)
MIN_VIDEO_DURATION = 180

# Configuracao de coleta expandida
TRENDING_PAGES = 4           # Paginas por pais (4 × 50 = 200 videos max)
SEARCH_RESULTS_PER_QUERY = 25  # Resultados por busca
SEARCH_DAYS_BACK = 7         # Buscar videos dos ultimos 7 dias

# Keywords de busca por subnicho (1 por subnicho × idioma)
SUBNICHO_SEARCH_KEYWORDS = {
    "relatos_guerra": {
        "en": "war veteran story documentary",
        "pt": "história soldado guerra documentário",
        "es": "historia veterano guerra documental",
        "fr": "histoire soldat guerre documentaire",
        "ko": "전쟁 참전용사 이야기",
        "ja": "戦争 兵士 ストーリー",
        "it": "storia soldato guerra documentario"
    },
    "guerras_civilizacoes": {
        "en": "ancient empire documentary history",
        "pt": "império romano documentário história",
        "es": "imperio romano documental historia",
        "fr": "empire romain documentaire histoire",
        "ko": "고대 제국 다큐멘터리",
        "ja": "古代帝国 ドキュメンタリー",
        "it": "impero romano documentario storia"
    },
    "empreendedorismo": {
        "en": "billionaire success story how he built",
        "pt": "bilionário história sucesso como construiu",
        "es": "millonario historia éxito como construyó",
        "fr": "milliardaire histoire succès comment",
        "ko": "억만장자 성공 스토리",
        "ja": "億万長者 成功 ストーリー",
        "it": "miliardario storia successo come ha costruito"
    },
    "terror": {
        "en": "true scary story paranormal real",
        "pt": "história terror real paranormal verdadeira",
        "es": "historia terror real paranormal verdadera",
        "fr": "histoire terreur réelle paranormal",
        "ko": "실화 공포 이야기 초자연",
        "ja": "実話 怖い話 パラノーマル",
        "it": "storia terrore reale paranormale vero"
    },
    "misterios": {
        "en": "unsolved mystery case unexplained",
        "pt": "mistério não resolvido caso inexplicável",
        "es": "misterio sin resolver caso inexplicable",
        "fr": "mystère non résolu cas inexpliqué",
        "ko": "미해결 미스터리 사건",
        "ja": "未解決 ミステリー 事件",
        "it": "mistero irrisolto caso inspiegabile"
    },
    "psicologia_mindset": {
        "en": "dark psychology manipulation tactics mind",
        "pt": "psicologia dark manipulação táticas mente",
        "es": "psicología oscura manipulación tácticas",
        "fr": "psychologie sombre manipulation tactiques",
        "ko": "어두운 심리학 조작 전술",
        "ja": "ダーク心理学 操作 戦術",
        "it": "psicologia oscura manipolazione tattiche"
    },
    "historias_sombrias": {
        "en": "dark history evil king brutal medieval",
        "pt": "história sombria rei cruel medieval brutal",
        "es": "historia oscura rey cruel medieval brutal",
        "fr": "histoire sombre roi cruel médiéval brutal",
        "ko": "어두운 역사 잔인한 왕 중세",
        "ja": "ダーク歴史 残酷な王 中世",
        "it": "storia oscura re crudele medievale brutale"
    }
}

# Keywords de descoberta (busca geral para novos nichos)
DISCOVERY_KEYWORDS = [
    "documentary 2026",
    "true story explained",
    "history documentary",
    "psychology explained",
    "real story what happened",
    "untold story",
    "biggest mystery",
    "dark side of",
    "how he became",
    "rise and fall"
]

# Paises para busca de descoberta (principais)
DISCOVERY_COUNTRIES = ["US", "BR", "ES"]

# Categorias a excluir
EXCLUDE_CATEGORIES = ["10", "17", "20"]  # Music, Sports, Gaming


def parse_duration(duration_str: str) -> int:
    """
    Converte duracao ISO 8601 para segundos.
    Exemplo: PT1H2M30S -> 3750 segundos
    """
    import re
    if not duration_str:
        return 0

    # Regex para extrair horas, minutos, segundos
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


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

    def collect_country(self, country_code: str, max_pages: int = TRENDING_PAGES) -> List[Dict]:
        """
        Coleta vídeos em trending de um país COM PAGINAÇÃO.

        Args:
            country_code: Código do país (US, BR, etc.)
            max_pages: Número de páginas (cada página = 50 vídeos, 1 unit)

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

        logger.info(f"Coletando YouTube Trending para {flag} {country_code} ({max_pages} páginas)...")

        videos = []
        filtered_count = 0
        page_token = None
        pages_fetched = 0

        try:
            while pages_fetched < max_pages:
                # Request com paginação
                request = self.youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    chart="mostPopular",
                    regionCode=region,
                    maxResults=50,
                    pageToken=page_token
                )
                response = request.execute()
                pages_fetched += 1

                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    content = item.get("contentDetails", {})
                    category_id = snippet.get("categoryId", "")

                    # Filtrar categorias indesejadas
                    if category_id in EXCLUDE_CATEGORIES:
                        filtered_count += 1
                        continue

                    # Parsear duracao e filtrar videos curtos
                    duration_str = content.get("duration", "")
                    duration_seconds = parse_duration(duration_str)

                    if duration_seconds < MIN_VIDEO_DURATION:
                        filtered_count += 1
                        continue

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
                        category_id=category_id,
                        tags=snippet.get("tags", []),
                        description=snippet.get("description", "")[:500],
                        url=f"https://youtube.com/watch?v={item.get('id', '')}",
                        timestamp=datetime.now().isoformat(),
                        duration_seconds=duration_seconds
                    )
                    videos.append(asdict(video))

                # Próxima página
                page_token = response.get("nextPageToken")
                if not page_token:
                    break

                time.sleep(0.3)  # Rate limiting entre páginas

            logger.info(f"  {flag} {country_code}: {len(videos)} videos ({filtered_count} filtrados, {pages_fetched} páginas)")

        except HttpError as e:
            logger.error(f"Erro HTTP ao coletar YouTube {country_code}: {e}")
        except Exception as e:
            logger.error(f"Erro ao coletar YouTube {country_code}: {e}")

        time.sleep(0.5)
        return videos

    def search_subnicho(self, subnicho: str, country_code: str) -> List[Dict]:
        """
        Busca vídeos por keywords de um subnicho específico.
        CUSTO: 100 units por busca!

        Args:
            subnicho: Nome do subnicho (ex: 'terror', 'misterios')
            country_code: Código do país

        Returns:
            Lista de vídeos encontrados
        """
        if not self.youtube:
            return []

        country_info = COUNTRIES.get(country_code)
        if not country_info:
            return []

        language = country_info["language"]
        region = country_info["youtube_region"]
        flag = country_info["flag"]

        # Obter keyword para o idioma
        keywords = SUBNICHO_SEARCH_KEYWORDS.get(subnicho, {})
        query = keywords.get(language, keywords.get("en", ""))

        if not query:
            return []

        logger.info(f"  Buscando '{subnicho}' em {flag} {country_code}...")

        # Data de corte (últimos 7 dias)
        published_after = (datetime.now() - timedelta(days=SEARCH_DAYS_BACK)).isoformat() + "Z"

        try:
            # Buscar vídeos
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                regionCode=region,
                publishedAfter=published_after,
                videoDuration="medium",  # 4-20 minutos
                maxResults=SEARCH_RESULTS_PER_QUERY
            )
            response = request.execute()

            # Extrair IDs para buscar detalhes
            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]

            if not video_ids:
                return []

            # Buscar detalhes dos vídeos (1 unit adicional)
            videos = self._get_video_details(video_ids, country_code, language, subnicho)

            logger.info(f"    → {len(videos)} vídeos encontrados")
            return videos

        except HttpError as e:
            logger.error(f"Erro na busca de {subnicho}: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado na busca: {e}")
            return []

    def search_discovery(self, keyword: str, country_code: str) -> List[Dict]:
        """
        Busca vídeos por keyword de descoberta (geral).
        CUSTO: 100 units por busca!

        Args:
            keyword: Termo de busca
            country_code: Código do país

        Returns:
            Lista de vídeos encontrados
        """
        if not self.youtube:
            return []

        country_info = COUNTRIES.get(country_code)
        if not country_info:
            return []

        language = country_info["language"]
        region = country_info["youtube_region"]
        flag = country_info["flag"]

        logger.info(f"  Descoberta: '{keyword}' em {flag} {country_code}...")

        published_after = (datetime.now() - timedelta(days=SEARCH_DAYS_BACK)).isoformat() + "Z"

        try:
            request = self.youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                order="viewCount",
                regionCode=region,
                publishedAfter=published_after,
                videoDuration="medium",
                maxResults=SEARCH_RESULTS_PER_QUERY
            )
            response = request.execute()

            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]

            if not video_ids:
                return []

            videos = self._get_video_details(video_ids, country_code, language, "discovery")

            logger.info(f"    → {len(videos)} vídeos")
            return videos

        except HttpError as e:
            logger.error(f"Erro na busca descoberta: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return []

    def _get_video_details(self, video_ids: List[str], country_code: str,
                           language: str, source_type: str) -> List[Dict]:
        """
        Obtém detalhes completos dos vídeos (statistics, duration).
        CUSTO: 1 unit para até 50 vídeos.

        Args:
            video_ids: Lista de IDs de vídeos
            country_code: Código do país
            language: Idioma
            source_type: Tipo de fonte ('trending', 'subnicho', 'discovery')

        Returns:
            Lista de vídeos com detalhes completos
        """
        if not video_ids:
            return []

        try:
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids[:50])  # Máximo 50 por request
            )
            response = request.execute()

            videos = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                content = item.get("contentDetails", {})
                category_id = snippet.get("categoryId", "")

                # Filtrar categorias indesejadas
                if category_id in EXCLUDE_CATEGORIES:
                    continue

                # Filtrar curtos
                duration_seconds = parse_duration(content.get("duration", ""))
                if duration_seconds < MIN_VIDEO_DURATION:
                    continue

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
                    category_id=category_id,
                    tags=snippet.get("tags", []),
                    description=snippet.get("description", "")[:500],
                    url=f"https://youtube.com/watch?v={item.get('id', '')}",
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=duration_seconds
                )

                video_dict = asdict(video)
                video_dict["source_type"] = source_type  # Marcar origem
                videos.append(video_dict)

            return videos

        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {e}")
            return []

    def collect_all_countries(self) -> Dict[str, List[Dict]]:
        """
        Coleta vídeos em trending de todos os países (básico).

        Returns:
            Dict com país como chave e lista de vídeos
        """
        all_videos = {}
        total = 0

        logger.info("=" * 50)
        logger.info("YOUTUBE - Iniciando coleta trending")
        logger.info("=" * 50)

        for country_code in COUNTRIES.keys():
            videos = self.collect_country(country_code)
            all_videos[country_code] = videos
            total += len(videos)

        logger.info("=" * 50)
        logger.info(f"YOUTUBE - Coleta trending finalizada: {total} vídeos")
        logger.info("=" * 50)

        return all_videos

    def collect_all_expanded(self) -> Dict:
        """
        Coleta COMPLETA expandida: trending + search nichado + discovery.

        CUSTO TOTAL ESTIMADO:
        - Trending: 7 países × 4 páginas = 28 units (~700 vídeos)
        - Search Nichado: 7 subnichos × 7 países × 101 units = 4.949 units (~1.200 vídeos)
        - Search Descoberta: 10 keywords × 3 países × 101 units = 3.030 units (~750 vídeos)
        - TOTAL: ~8.007 units (~2.650 vídeos)

        Returns:
            Dict com 3 categorias: trending, subnicho, discovery
        """
        results = {
            "trending": {},
            "subnicho": {},
            "discovery": [],
            "stats": {
                "total_videos": 0,
                "trending_count": 0,
                "subnicho_count": 0,
                "discovery_count": 0,
                "units_used": 0
            }
        }

        logger.info("=" * 60)
        logger.info("YOUTUBE COLETA EXPANDIDA - Iniciando")
        logger.info("=" * 60)

        # =============================================
        # 1. TRENDING (7 países × 4 páginas = 28 units)
        # =============================================
        logger.info("\n📺 FASE 1: Coletando Trending (28 units)")
        logger.info("-" * 40)

        for country_code in COUNTRIES.keys():
            videos = self.collect_country(country_code, max_pages=TRENDING_PAGES)
            results["trending"][country_code] = videos
            results["stats"]["trending_count"] += len(videos)

        results["stats"]["units_used"] += len(COUNTRIES) * TRENDING_PAGES
        logger.info(f"✓ Trending: {results['stats']['trending_count']} vídeos")

        # =============================================
        # 2. SEARCH NICHADO (7 subnichos × 7 países)
        # =============================================
        logger.info("\n🎯 FASE 2: Buscando por Subnichos (4.949 units)")
        logger.info("-" * 40)

        for subnicho in SUBNICHO_SEARCH_KEYWORDS.keys():
            results["subnicho"][subnicho] = {}
            logger.info(f"\n  📌 {subnicho.upper()}")

            for country_code in COUNTRIES.keys():
                videos = self.search_subnicho(subnicho, country_code)
                results["subnicho"][subnicho][country_code] = videos
                results["stats"]["subnicho_count"] += len(videos)
                # 100 units (search) + 1 unit (video details)
                results["stats"]["units_used"] += 101

                time.sleep(0.5)  # Rate limiting

        logger.info(f"\n✓ Subnichos: {results['stats']['subnicho_count']} vídeos")

        # =============================================
        # 3. SEARCH DESCOBERTA (10 keywords × 3 países)
        # =============================================
        logger.info("\n🔍 FASE 3: Busca de Descoberta (3.030 units)")
        logger.info("-" * 40)

        for keyword in DISCOVERY_KEYWORDS:
            logger.info(f"\n  🔎 '{keyword}'")

            for country_code in DISCOVERY_COUNTRIES:
                videos = self.search_discovery(keyword, country_code)

                # Marcar origem
                for v in videos:
                    v["discovery_keyword"] = keyword

                results["discovery"].extend(videos)
                results["stats"]["discovery_count"] += len(videos)
                results["stats"]["units_used"] += 101

                time.sleep(0.5)

        logger.info(f"\n✓ Descoberta: {results['stats']['discovery_count']} vídeos")

        # =============================================
        # RESUMO FINAL
        # =============================================
        results["stats"]["total_videos"] = (
            results["stats"]["trending_count"] +
            results["stats"]["subnicho_count"] +
            results["stats"]["discovery_count"]
        )

        logger.info("\n" + "=" * 60)
        logger.info("YOUTUBE COLETA EXPANDIDA - FINALIZADO")
        logger.info("=" * 60)
        logger.info(f"📊 ESTATÍSTICAS:")
        logger.info(f"  • Trending:   {results['stats']['trending_count']:,} vídeos")
        logger.info(f"  • Subnichos:  {results['stats']['subnicho_count']:,} vídeos")
        logger.info(f"  • Descoberta: {results['stats']['discovery_count']:,} vídeos")
        logger.info(f"  • TOTAL:      {results['stats']['total_videos']:,} vídeos")
        logger.info(f"  • Units API:  ~{results['stats']['units_used']:,} units")
        logger.info("=" * 60)

        return results

    def flatten_results(self, expanded_results: Dict) -> List[Dict]:
        """
        Converte resultados expandidos em lista única (deduplicada).

        Args:
            expanded_results: Resultado de collect_all_expanded()

        Returns:
            Lista única de vídeos, sem duplicatas
        """
        all_videos = []
        seen_ids = set()

        # 1. Adicionar trending
        for country, videos in expanded_results.get("trending", {}).items():
            for video in videos:
                vid = video.get("video_id")
                if vid and vid not in seen_ids:
                    video["collection_type"] = "trending"
                    all_videos.append(video)
                    seen_ids.add(vid)

        # 2. Adicionar subnichos
        for subnicho, countries in expanded_results.get("subnicho", {}).items():
            for country, videos in countries.items():
                for video in videos:
                    vid = video.get("video_id")
                    if vid and vid not in seen_ids:
                        video["collection_type"] = "subnicho"
                        video["matched_subnicho"] = subnicho
                        all_videos.append(video)
                        seen_ids.add(vid)

        # 3. Adicionar descoberta
        for video in expanded_results.get("discovery", []):
            vid = video.get("video_id")
            if vid and vid not in seen_ids:
                video["collection_type"] = "discovery"
                all_videos.append(video)
                seen_ids.add(vid)

        logger.info(f"Flatten: {len(all_videos)} vídeos únicos (de {expanded_results['stats']['total_videos']} brutos)")

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
