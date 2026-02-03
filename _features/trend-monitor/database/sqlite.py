"""
TREND MONITOR - Database Module
================================
Gerenciamento do banco de dados SQLite para armazenar trends e padrões.

TABELAS:
- trends: Todos os trends coletados (histórico completo)
- trend_patterns: Análise de padrões (evergreen, crescente, etc.)
- collections: Metadados de cada coleta diária
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho do banco
DB_PATH = os.path.join(DATA_DIR, "trends.db")


class TrendDatabase:
    """
    Gerenciador do banco de dados de trends.

    Uso:
        db = TrendDatabase()
        db.save_trends(trends_list)
        evergreen = db.get_evergreen_trends(min_days=7)
    """

    def __init__(self, db_path: str = None):
        """
        Inicializa o banco de dados.

        Args:
            db_path: Caminho do arquivo SQLite (default: data/trends.db)
        """
        self.db_path = db_path or DB_PATH

        # Garantir que diretório existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Inicializar banco
        self._init_db()
        logger.info(f"Database inicializado: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Cria tabelas se não existirem"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Tabela de trends (todos os dados coletados)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                country TEXT DEFAULT 'global',
                language TEXT DEFAULT 'en',
                volume INTEGER DEFAULT 0,
                url TEXT,
                hn_url TEXT,
                permalink TEXT,
                subreddit TEXT,
                channel_title TEXT,
                author TEXT,
                num_comments INTEGER DEFAULT 0,
                collected_at DATETIME NOT NULL,
                collected_date DATE NOT NULL,
                raw_data TEXT,
                UNIQUE(title, source, collected_date)
            )
        """)

        # Tabela de padrões detectados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_normalized TEXT NOT NULL,
                first_seen DATE NOT NULL,
                last_seen DATE NOT NULL,
                days_active INTEGER DEFAULT 1,
                total_volume INTEGER DEFAULT 0,
                avg_volume INTEGER DEFAULT 0,
                sources_found TEXT,
                countries_found TEXT,
                is_evergreen BOOLEAN DEFAULT 0,
                is_growing BOOLEAN DEFAULT 0,
                updated_at DATETIME,
                UNIQUE(title_normalized)
            )
        """)

        # Tabela de coletas (metadados)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_date DATE UNIQUE NOT NULL,
                collected_at DATETIME NOT NULL,
                total_trends INTEGER DEFAULT 0,
                sources_used TEXT,
                countries_collected TEXT,
                status TEXT DEFAULT 'completed'
            )
        """)

        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_source ON trends(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_country ON trends(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_date ON trends(collected_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_title ON trends(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_evergreen ON trend_patterns(is_evergreen)")

        conn.commit()
        conn.close()

    def save_trends(self, trends: List[Dict], collected_at: datetime = None) -> int:
        """
        Salva lista de trends no banco.

        Args:
            trends: Lista de dicts com dados dos trends
            collected_at: Timestamp da coleta (default: agora)

        Returns:
            Número de trends salvos
        """
        if not trends:
            return 0

        if collected_at is None:
            collected_at = datetime.now()

        collected_date = collected_at.date()

        conn = self._get_connection()
        cursor = conn.cursor()

        saved = 0
        for trend in trends:
            try:
                # Extrair dados
                title = trend.get("title", "")
                if not title:
                    continue

                source = trend.get("source", "unknown")
                country = trend.get("country", "global")
                language = trend.get("language", "en")

                # Volume pode vir de diferentes campos
                volume = (
                    trend.get("volume") or
                    trend.get("view_count") or
                    trend.get("score") or
                    0
                )

                # URL pode vir de diferentes campos
                url = trend.get("url") or ""
                hn_url = trend.get("hn_url") or ""
                permalink = trend.get("permalink") or ""

                cursor.execute("""
                    INSERT OR REPLACE INTO trends (
                        title, source, country, language, volume,
                        url, hn_url, permalink, subreddit, channel_title,
                        author, num_comments, collected_at, collected_date, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    source,
                    country,
                    language,
                    volume,
                    url,
                    hn_url,
                    permalink,
                    trend.get("subreddit", ""),
                    trend.get("channel_title", ""),
                    trend.get("author", ""),
                    trend.get("num_comments", 0),
                    collected_at.isoformat(),
                    collected_date.isoformat(),
                    json.dumps(trend)
                ))
                saved += 1

            except Exception as e:
                logger.error(f"Erro ao salvar trend '{trend.get('title', '')}': {e}")

        # Registrar coleta
        sources = list(set(t.get("source", "unknown") for t in trends))
        countries = list(set(t.get("country", "global") for t in trends))

        cursor.execute("""
            INSERT OR REPLACE INTO collections (
                collected_date, collected_at, total_trends, sources_used, countries_collected
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            collected_date.isoformat(),
            collected_at.isoformat(),
            saved,
            json.dumps(sources),
            json.dumps(countries)
        ))

        conn.commit()
        conn.close()

        logger.info(f"Salvos {saved} trends no banco de dados")
        return saved

    def update_patterns(self):
        """
        Atualiza tabela de padrões baseado nos trends coletados.
        Detecta evergreen (7+ dias) e trends crescentes.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Buscar todos os títulos únicos normalizados
        cursor.execute("""
            SELECT
                LOWER(TRIM(title)) as title_normalized,
                MIN(collected_date) as first_seen,
                MAX(collected_date) as last_seen,
                COUNT(DISTINCT collected_date) as days_active,
                SUM(volume) as total_volume,
                AVG(volume) as avg_volume,
                GROUP_CONCAT(DISTINCT source) as sources_found,
                GROUP_CONCAT(DISTINCT country) as countries_found
            FROM trends
            GROUP BY LOWER(TRIM(title))
            HAVING days_active >= 1
        """)

        patterns = cursor.fetchall()

        for pattern in patterns:
            days_active = pattern["days_active"]
            is_evergreen = days_active >= 7
            is_growing = days_active >= 3

            cursor.execute("""
                INSERT OR REPLACE INTO trend_patterns (
                    title_normalized, first_seen, last_seen, days_active,
                    total_volume, avg_volume, sources_found, countries_found,
                    is_evergreen, is_growing, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern["title_normalized"],
                pattern["first_seen"],
                pattern["last_seen"],
                days_active,
                pattern["total_volume"],
                int(pattern["avg_volume"]),
                pattern["sources_found"],
                pattern["countries_found"],
                is_evergreen,
                is_growing,
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        logger.info(f"Atualizados {len(patterns)} padrões de trends")

    def get_evergreen_trends(self, min_days: int = 7) -> List[Dict]:
        """
        Retorna trends que estão em alta há X dias ou mais.

        Args:
            min_days: Mínimo de dias para considerar evergreen

        Returns:
            Lista de trends evergreen
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM trend_patterns
            WHERE days_active >= ?
            ORDER BY days_active DESC, avg_volume DESC
        """, (min_days,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_trends_by_source(self, source: str, date: str = None, limit: int = 100) -> List[Dict]:
        """
        Retorna trends filtrados por fonte.

        Args:
            source: 'google_trends', 'youtube', 'reddit', 'hackernews'
            date: Data específica (YYYY-MM-DD) ou None para hoje
            limit: Máximo de resultados

        Returns:
            Lista de trends
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT * FROM trends
            WHERE source = ? AND collected_date = ?
            ORDER BY volume DESC
            LIMIT ?
        """, (source, date, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_trends_by_country(self, country: str, date: str = None, limit: int = 100) -> List[Dict]:
        """
        Retorna trends filtrados por país.

        Args:
            country: Código do país (US, BR, etc.)
            date: Data específica ou None para hoje
            limit: Máximo de resultados

        Returns:
            Lista de trends
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT * FROM trends
            WHERE country = ? AND collected_date = ?
            ORDER BY volume DESC
            LIMIT ?
        """, (country, date, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_all_trends(self, date: str = None, limit: int = 500) -> List[Dict]:
        """
        Retorna todos os trends de uma data.

        Args:
            date: Data específica ou None para hoje
            limit: Máximo de resultados

        Returns:
            Lista de trends
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT * FROM trends
            WHERE collected_date = ?
            ORDER BY volume DESC
            LIMIT ?
        """, (date, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_new_opportunities(self, subnicho_keywords: Dict[str, List[str]], min_days: int = 7) -> List[Dict]:
        """
        Detecta temas em alta que NÃO estão nos subnichos atuais.
        Potenciais oportunidades de novos canais.

        Args:
            subnicho_keywords: Dict com keywords de cada subnicho
            min_days: Mínimo de dias em alta

        Returns:
            Lista de oportunidades detectadas
        """
        # Flatten todas as keywords
        all_keywords = set()
        for keywords in subnicho_keywords.values():
            all_keywords.update(kw.lower() for kw in keywords)

        # Buscar evergreen
        evergreen = self.get_evergreen_trends(min_days)

        opportunities = []
        for trend in evergreen:
            title = trend["title_normalized"].lower()

            # Verificar se NÃO match com nenhum subnicho
            matches_subnicho = any(kw in title for kw in all_keywords)

            if not matches_subnicho:
                opportunities.append({
                    "title": trend["title_normalized"],
                    "days_active": trend["days_active"],
                    "first_seen": trend["first_seen"],
                    "last_seen": trend["last_seen"],
                    "avg_volume": trend["avg_volume"],
                    "sources": trend["sources_found"],
                    "countries": trend["countries_found"],
                    "recommendation": "Considerar abertura de canal ou adicionar aos subnichos"
                })

        return opportunities

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas gerais do banco.

        Returns:
            Dict com estatísticas
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total de trends
        cursor.execute("SELECT COUNT(*) as total FROM trends")
        total_trends = cursor.fetchone()["total"]

        # Total de dias coletados
        cursor.execute("SELECT COUNT(DISTINCT collected_date) as days FROM trends")
        total_days = cursor.fetchone()["days"]

        # Trends evergreen
        cursor.execute("SELECT COUNT(*) as total FROM trend_patterns WHERE is_evergreen = 1")
        evergreen_count = cursor.fetchone()["total"]

        # Por fonte
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM trends
            GROUP BY source
        """)
        by_source = {row["source"]: row["count"] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_trends": total_trends,
            "total_days_collected": total_days,
            "evergreen_count": evergreen_count,
            "by_source": by_source
        }


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Trend Database")
    print("=" * 60)

    # Criar instância
    db = TrendDatabase()

    # Dados de teste
    test_trends = [
        {
            "title": "Roman Empire Documentary",
            "source": "youtube",
            "country": "US",
            "volume": 1250000,
            "url": "https://youtube.com/watch?v=test123"
        },
        {
            "title": "Psychology of Manipulation",
            "source": "reddit",
            "country": "global",
            "volume": 45000,
            "url": "https://reddit.com/r/psychology/test"
        },
        {
            "title": "Roman Empire Documentary",  # Duplicata para testar
            "source": "google_trends",
            "country": "BR",
            "volume": 320000,
            "url": "https://trends.google.com/test"
        }
    ]

    # Salvar
    print("\nSalvando trends de teste...")
    saved = db.save_trends(test_trends)
    print(f"Salvos: {saved}")

    # Atualizar padrões
    print("\nAtualizando padrões...")
    db.update_patterns()

    # Stats
    print("\nEstatísticas:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Buscar por fonte
    print("\nTrends do YouTube hoje:")
    yt_trends = db.get_trends_by_source("youtube")
    for t in yt_trends[:3]:
        print(f"  - {t['title']}")
