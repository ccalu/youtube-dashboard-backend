"""
TREND MONITOR - Google Trends Collector
========================================
Coleta trending searches do Google Trends usando pytrends.

NOTA IMPORTANTE:
- pytrends usa scraping, não é API oficial
- Rate limit: ~100 requests/hora (recomendado: 1 req/5 segundos)
- Pode dar bloqueio temporário se abusar

Documentação pytrends: https://github.com/GeneralMills/pytrends
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("AVISO: pytrends não instalado. Execute: pip install pytrends")

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


class GoogleTrendsCollector:
    """
    Coletor de Google Trends para múltiplos países.

    Uso:
        collector = GoogleTrendsCollector()
        trends = collector.collect_all_countries()
    """

    def __init__(self, timeout: int = 30, retries: int = 3):
        """
        Inicializa o coletor.

        Args:
            timeout: Timeout em segundos para requests
            retries: Número de tentativas em caso de erro
        """
        self.timeout = timeout
        self.retries = retries
        self.pytrends = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa cliente pytrends"""
        if not PYTRENDS_AVAILABLE:
            logger.error("pytrends não disponível")
            return

        try:
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25),
                retries=self.retries,
                backoff_factor=0.1
            )
            logger.info("Cliente pytrends inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar pytrends: {e}")
            self.pytrends = None

    def collect_country(self, country_code: str) -> List[Dict]:
        """
        Coleta trends de um país específico.

        Args:
            country_code: Código do país (US, BR, ES, etc.)

        Returns:
            Lista de dicts com trends do país
        """
        if not self.pytrends:
            logger.warning(f"pytrends não disponível, retornando lista vazia para {country_code}")
            return []

        country_info = COUNTRIES.get(country_code)
        if not country_info:
            logger.warning(f"País não configurado: {country_code}")
            return []

        geo = country_info["google_geo"]
        language = country_info["language"]
        flag = country_info["flag"]

        logger.info(f"Coletando Google Trends para {flag} {country_code}...")

        trends = []
        try:
            # Trending searches (real-time)
            trending = self.pytrends.trending_searches(pn=geo.lower())

            for rank, row in enumerate(trending.values.tolist(), 1):
                title = row[0] if isinstance(row, list) else row
                if title and isinstance(title, str):
                    trend = TrendItem(
                        title=title.strip(),
                        source="google_trends",
                        country=country_code,
                        language=language,
                        rank=rank,
                        timestamp=datetime.now().isoformat()
                    )
                    trends.append(asdict(trend))

                # Limitar ao número configurado
                if rank >= COLLECTION_CONFIG["trends_per_country"]:
                    break

            logger.info(f"  {flag} {country_code}: {len(trends)} trends coletados")

        except Exception as e:
            logger.error(f"Erro ao coletar trends de {country_code}: {e}")

        # Rate limiting - aguardar entre países
        time.sleep(2)

        return trends

    def collect_all_countries(self) -> Dict[str, List[Dict]]:
        """
        Coleta trends de todos os países configurados.

        Returns:
            Dict com país como chave e lista de trends como valor
        """
        all_trends = {}
        total = 0

        logger.info("=" * 50)
        logger.info("GOOGLE TRENDS - Iniciando coleta")
        logger.info("=" * 50)

        for country_code in COUNTRIES.keys():
            trends = self.collect_country(country_code)
            all_trends[country_code] = trends
            total += len(trends)

            # Rate limiting entre países
            time.sleep(3)

        logger.info("=" * 50)
        logger.info(f"GOOGLE TRENDS - Coleta finalizada: {total} trends")
        logger.info("=" * 50)

        return all_trends

    def get_interest_over_time(self, keywords: List[str], geo: str = "") -> Optional[Dict]:
        """
        Obtém interesse ao longo do tempo para keywords específicas.
        Útil para análise de volume.

        Args:
            keywords: Lista de até 5 keywords
            geo: Código do país (opcional)

        Returns:
            Dict com dados de interesse ou None se erro
        """
        if not self.pytrends:
            return None

        if len(keywords) > 5:
            keywords = keywords[:5]
            logger.warning("Limitando a 5 keywords (máximo do Google Trends)")

        try:
            self.pytrends.build_payload(keywords, cat=0, timeframe='today 1-m', geo=geo)
            interest = self.pytrends.interest_over_time()

            if not interest.empty:
                return interest.to_dict()

        except Exception as e:
            logger.error(f"Erro ao obter interesse: {e}")

        return None


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

    # Adicionar campos padrão
    for country_code, trends in mock_trends.items():
        country_info = COUNTRIES.get(country_code, {})
        for trend in trends:
            trend["source"] = "google_trends"
            trend["country"] = country_code
            trend["language"] = country_info.get("language", "en")
            trend["timestamp"] = timestamp
            trend["category"] = "general"

    return mock_trends


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Google Trends Collector")
    print("=" * 60)

    collector = GoogleTrendsCollector()

    # Testar coleta de um país
    print("\nTestando coleta do Brasil...")
    br_trends = collector.collect_country("BR")

    if br_trends:
        print(f"\nTop 10 trends BR:")
        for trend in br_trends[:10]:
            print(f"  #{trend['rank']}: {trend['title']}")
    else:
        print("Nenhum trend coletado (verifique se pytrends está instalado)")

    # Testar coleta de todos (apenas se quiser - demora)
    # all_trends = collector.collect_all_countries()
