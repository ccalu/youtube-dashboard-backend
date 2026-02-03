"""
TREND MONITOR - Google Trends Collector (RSS)
==============================================
Coleta trending searches do Google Trends usando RSS feeds.

IMPORTANTE:
- Usa RSS feed publico do Google Trends (nao bloqueado)
- URL: https://trends.google.com/trends/trendingsearches/daily/rss?geo=XX
- Retorna ~20 trends por pais
- Sem autenticacao necessaria
- Sem rate limiting

Documentacao: https://trends.google.com/trends/
"""

import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    print("AVISO: feedparser nao instalado. Execute: pip install feedparser")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COUNTRIES, COLLECTION_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrendItem:
    """Estrutura de um item de trend"""
    title: str
    source: str = "google_trends"
    country: str = ""
    language: str = ""
    rank: int = 0
    volume: Optional[int] = None
    category: str = "general"
    url: str = ""
    timestamp: str = ""
    description: str = ""
    news_items: List[str] = None


class GoogleTrendsCollector:
    """
    Coletor de Google Trends via RSS para multiplos paises.

    Uso:
        collector = GoogleTrendsCollector()
        trends = collector.collect_all_countries()
    """

    # Base URL do RSS feed do Google Trends (URL atualizada 2024)
    RSS_BASE_URL = "https://trends.google.com/trending/rss"

    def __init__(self, timeout: int = 30, retries: int = 3):
        """
        Inicializa o coletor.

        Args:
            timeout: Timeout em segundos para requests
            retries: Numero de tentativas em caso de erro
        """
        self.timeout = timeout
        self.retries = retries

        if not FEEDPARSER_AVAILABLE:
            logger.error("feedparser nao disponivel")
        else:
            logger.info("Google Trends RSS collector inicializado")

    def _parse_traffic(self, traffic_str: str) -> int:
        """
        Converte string de trafego (ex: '500K+') para numero.

        Args:
            traffic_str: String do trafego aproximado

        Returns:
            Numero inteiro do volume
        """
        if not traffic_str:
            return 0

        traffic_str = traffic_str.replace('+', '').replace(',', '').strip()

        try:
            if 'M' in traffic_str.upper():
                return int(float(traffic_str.upper().replace('M', '')) * 1000000)
            elif 'K' in traffic_str.upper():
                return int(float(traffic_str.upper().replace('K', '')) * 1000)
            else:
                return int(traffic_str)
        except (ValueError, AttributeError):
            return 0

    def _clean_html(self, text: str) -> str:
        """Remove tags HTML de um texto"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&')
        clean = clean.replace('&lt;', '<').replace('&gt;', '>')
        return clean.strip()

    def collect_country(self, country_code: str) -> List[Dict]:
        """
        Coleta trends de um pais especifico via RSS.

        Args:
            country_code: Codigo do pais (US, BR, ES, etc.)

        Returns:
            Lista de dicts com trends do pais
        """
        if not FEEDPARSER_AVAILABLE:
            logger.warning(f"feedparser nao disponivel, retornando lista vazia para {country_code}")
            return []

        country_info = COUNTRIES.get(country_code)
        if not country_info:
            logger.warning(f"Pais nao configurado: {country_code}")
            return []

        geo = country_info["google_geo"]
        language = country_info["language"]
        flag = country_info["flag"]

        logger.info(f"Coletando Google Trends RSS para {flag} {country_code}...")

        trends = []
        url = f"{self.RSS_BASE_URL}?geo={geo}"

        for attempt in range(self.retries):
            try:
                feed = feedparser.parse(url)

                if feed.bozo and not feed.entries:
                    logger.warning(f"RSS feed vazio ou erro para {country_code}: {feed.bozo_exception}")
                    continue

                for rank, entry in enumerate(feed.entries, 1):
                    title = entry.get('title', '').strip()

                    if not title:
                        continue

                    # Extrair trafego aproximado
                    traffic_str = entry.get('ht_approx_traffic', '')
                    if not traffic_str:
                        # Tentar extrair de outro campo
                        traffic_str = entry.get('ht_traffic', '')

                    volume = self._parse_traffic(traffic_str)

                    # Extrair descricao/noticias relacionadas
                    description = self._clean_html(entry.get('summary', ''))

                    # Extrair noticias relacionadas do campo ht_news_item
                    news_items = []
                    if hasattr(entry, 'ht_news_items'):
                        for news in entry.ht_news_items:
                            if hasattr(news, 'ht_news_item_title'):
                                news_items.append(news.ht_news_item_title)

                    # URL do trend no Google Trends
                    trend_url = entry.get('link', '')
                    if not trend_url:
                        trend_url = f"https://trends.google.com/trends/explore?q={title.replace(' ', '+')}&geo={geo}"

                    trend = TrendItem(
                        title=title,
                        source="google_trends",
                        country=country_code,
                        language=language,
                        rank=rank,
                        volume=volume,
                        url=trend_url,
                        timestamp=datetime.now().isoformat(),
                        description=description[:500] if description else "",
                        news_items=news_items[:5] if news_items else []
                    )

                    trend_dict = asdict(trend)
                    # Garantir que news_items seja lista
                    if trend_dict.get('news_items') is None:
                        trend_dict['news_items'] = []

                    trends.append(trend_dict)

                    # Limitar ao numero configurado
                    if rank >= COLLECTION_CONFIG["trends_per_country"]:
                        break

                # Sucesso - sair do loop de retry
                break

            except Exception as e:
                logger.error(f"Erro ao coletar RSS de {country_code} (tentativa {attempt + 1}): {e}")
                if attempt < self.retries - 1:
                    time.sleep(2)

        logger.info(f"  {flag} {country_code}: {len(trends)} trends coletados")

        # Pequeno delay entre paises (respeito ao servidor)
        time.sleep(0.5)

        return trends

    def collect_all_countries(self) -> Dict[str, List[Dict]]:
        """
        Coleta trends de todos os paises configurados.

        Returns:
            Dict com pais como chave e lista de trends como valor
        """
        all_trends = {}
        total = 0

        logger.info("=" * 50)
        logger.info("GOOGLE TRENDS (RSS) - Iniciando coleta")
        logger.info("=" * 50)

        for country_code in COUNTRIES.keys():
            trends = self.collect_country(country_code)
            all_trends[country_code] = trends
            total += len(trends)

        logger.info("=" * 50)
        logger.info(f"GOOGLE TRENDS (RSS) - Coleta finalizada: {total} trends")
        logger.info("=" * 50)

        return all_trends


# =============================================================================
# MOCK DATA (para testes sem API)
# =============================================================================

def get_mock_google_trends_data() -> Dict[str, List[Dict]]:
    """Retorna dados mock realistas para testes sem API"""
    timestamp = datetime.now().isoformat()

    mock_trends = {
        "US": [
            {"title": "Roman Empire collapse", "volume": 850000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=Roman+Empire+collapse&geo=US"},
            {"title": "Psychology manipulation tactics", "volume": 720000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=Psychology+manipulation&geo=US"},
            {"title": "Unsolved mysteries 2024", "volume": 680000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=Unsolved+mysteries&geo=US"},
            {"title": "Haunted places documentary", "volume": 590000, "rank": 4,
             "url": "https://trends.google.com/trends/explore?q=Haunted+places&geo=US"},
            {"title": "Self made billionaire story", "volume": 540000, "rank": 5,
             "url": "https://trends.google.com/trends/explore?q=Self+made+billionaire&geo=US"},
        ],
        "BR": [
            {"title": "Imperio Romano queda", "volume": 320000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=Imperio+Romano&geo=BR"},
            {"title": "Psicologia dark", "volume": 280000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=Psicologia+dark&geo=BR"},
            {"title": "Misterios sem solucao Brasil", "volume": 245000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=Misterios+Brasil&geo=BR"},
            {"title": "Historia Segunda Guerra", "volume": 210000, "rank": 4,
             "url": "https://trends.google.com/trends/explore?q=Segunda+Guerra&geo=BR"},
            {"title": "Empreendedorismo digital", "volume": 195000, "rank": 5,
             "url": "https://trends.google.com/trends/explore?q=Empreendedorismo&geo=BR"},
        ],
        "ES": [
            {"title": "Imperio Romano historia", "volume": 180000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=Imperio+Romano&geo=ES"},
            {"title": "Misterios sin resolver", "volume": 165000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=Misterios+sin+resolver&geo=ES"},
            {"title": "Psicologia oscura", "volume": 142000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=Psicologia+oscura&geo=ES"},
        ],
        "FR": [
            {"title": "Empire Romain chute", "volume": 210000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=Empire+Romain&geo=FR"},
            {"title": "Psychologie manipulation", "volume": 185000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=Psychologie+manipulation&geo=FR"},
            {"title": "Mysteres non resolus", "volume": 156000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=Mysteres+non+resolus&geo=FR"},
        ],
        "KR": [
            {"title": "고대 제국 역사", "volume": 145000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=고대+제국&geo=KR"},
            {"title": "미스터리 미해결", "volume": 128000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=미스터리&geo=KR"},
        ],
        "JP": [
            {"title": "ローマ帝国 崩壊", "volume": 175000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=ローマ帝国&geo=JP"},
            {"title": "心理学 操作", "volume": 152000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=心理学&geo=JP"},
            {"title": "未解決事件", "volume": 138000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=未解決事件&geo=JP"},
        ],
        "IT": [
            {"title": "Impero Romano caduta", "volume": 165000, "rank": 1,
             "url": "https://trends.google.com/trends/explore?q=Impero+Romano&geo=IT"},
            {"title": "Misteri irrisolti", "volume": 142000, "rank": 2,
             "url": "https://trends.google.com/trends/explore?q=Misteri+irrisolti&geo=IT"},
            {"title": "Psicologia oscura", "volume": 118000, "rank": 3,
             "url": "https://trends.google.com/trends/explore?q=Psicologia+oscura&geo=IT"},
        ]
    }

    # Adicionar campos padrao
    for country_code, trends in mock_trends.items():
        country_info = COUNTRIES.get(country_code, {})
        for trend in trends:
            trend["source"] = "google_trends"
            trend["country"] = country_code
            trend["language"] = country_info.get("language", "en")
            trend["timestamp"] = timestamp
            trend["category"] = "general"
            trend["description"] = ""
            trend["news_items"] = []

    return mock_trends


# =============================================================================
# TESTE DO MODULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Google Trends RSS Collector")
    print("=" * 60)

    collector = GoogleTrendsCollector()

    # Testar coleta de um pais
    print("\nTestando coleta dos EUA (US)...")
    us_trends = collector.collect_country("US")

    if us_trends:
        print(f"\nTop 10 trends US:")
        for trend in us_trends[:10]:
            volume = trend.get('volume', 0)
            volume_str = f"{volume:,}" if volume else "N/A"
            print(f"  #{trend['rank']}: {trend['title']} ({volume_str} buscas)")
    else:
        print("Nenhum trend coletado (verifique conexao)")

    # Testar coleta do Brasil
    print("\nTestando coleta do Brasil (BR)...")
    br_trends = collector.collect_country("BR")

    if br_trends:
        print(f"\nTop 10 trends BR:")
        for trend in br_trends[:10]:
            volume = trend.get('volume', 0)
            volume_str = f"{volume:,}" if volume else "N/A"
            print(f"  #{trend['rank']}: {trend['title']} ({volume_str} buscas)")
    else:
        print("Nenhum trend coletado (verifique conexao)")

    # Resumo
    print("\n" + "=" * 60)
    print(f"RESUMO: US={len(us_trends)} trends, BR={len(br_trends)} trends")
    print("=" * 60)
