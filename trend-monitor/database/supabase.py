"""
TREND MONITOR - Supabase Database Module
=========================================
Gerenciamento do banco de dados Supabase para armazenar trends e padroes.

TABELAS:
- trends: Todos os trends coletados (historico completo)
- trend_patterns: Analise de padroes (evergreen, crescente, etc.)
- collections: Metadados de cada coleta diaria

CONFIGURACAO:
    Defina as variaveis de ambiente:
    - SUPABASE_URL: URL do projeto Supabase
    - SUPABASE_KEY: Chave anonima (anon key)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from supabase import create_client, Client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendDatabaseSupabase:
    """
    Gerenciador do banco de dados Supabase para trends.

    Uso:
        db = TrendDatabaseSupabase()
        db.save_trends(trends_list)
        evergreen = db.get_evergreen_trends(min_days=7)
    """

    def __init__(self):
        """
        Inicializa conexao com Supabase.

        Requer variaveis de ambiente:
        - SUPABASE_URL
        - SUPABASE_KEY
        """
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            logger.warning("SUPABASE_URL ou SUPABASE_KEY nao definidos. Usando modo offline.")
            self.client = None
            self.offline_mode = True
        else:
            self.client: Client = create_client(self.url, self.key)
            self.offline_mode = False
            logger.info(f"Supabase conectado: {self.url[:30]}...")

    def is_connected(self) -> bool:
        """Verifica se esta conectado ao Supabase"""
        return self.client is not None and not self.offline_mode

    def save_trends(self, trends: List[Dict], collected_at: datetime = None) -> int:
        """
        Salva lista de trends no Supabase.

        Args:
            trends: Lista de dicts com dados dos trends
            collected_at: Timestamp da coleta (default: agora)

        Returns:
            Numero de trends salvos
        """
        if not self.is_connected():
            logger.warning("Supabase nao conectado. Trends nao salvos.")
            return 0

        if not trends:
            return 0

        if collected_at is None:
            collected_at = datetime.now()

        collected_date = collected_at.date().isoformat()

        records = []
        for trend in trends:
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

            # URLs
            url = trend.get("url") or ""
            hn_url = trend.get("hn_url") or ""
            permalink = trend.get("permalink") or ""

            record = {
                "title": title,
                "source": source,
                "country": country,
                "language": language,
                "volume": volume,
                "url": url,
                "hn_url": hn_url,
                "permalink": permalink,
                "subreddit": trend.get("subreddit", ""),
                "channel_title": trend.get("channel_title", ""),
                "author": trend.get("author", ""),
                "num_comments": trend.get("num_comments", 0),
                "collected_at": collected_at.isoformat(),
                "collected_date": collected_date,
                "raw_data": trend
            }
            records.append(record)

        if not records:
            return 0

        try:
            # Upsert para evitar duplicatas (usando constraint UNIQUE)
            result = self.client.table("trends").upsert(
                records,
                on_conflict="title,source,collected_date"
            ).execute()

            saved = len(result.data) if result.data else 0

            # Registrar coleta
            sources = list(set(t.get("source", "unknown") for t in trends))
            countries = list(set(t.get("country", "global") for t in trends))

            self.client.table("collections").upsert({
                "collected_date": collected_date,
                "collected_at": collected_at.isoformat(),
                "total_trends": saved,
                "sources_used": sources,
                "countries_collected": countries,
                "status": "completed"
            }, on_conflict="collected_date").execute()

            logger.info(f"Salvos {saved} trends no Supabase")
            return saved

        except Exception as e:
            logger.error(f"Erro ao salvar trends no Supabase: {e}")
            return 0

    def update_patterns(self):
        """
        Atualiza tabela de padroes baseado nos trends coletados.
        Detecta evergreen (7+ dias) e trends crescentes.
        """
        if not self.is_connected():
            logger.warning("Supabase nao conectado. Patterns nao atualizados.")
            return

        try:
            # Buscar agregacoes via SQL (usando RPC function ou query direta)
            # Por simplicidade, vamos buscar todos os trends e agregar em Python
            result = self.client.table("trends").select(
                "title, source, country, volume, collected_date"
            ).execute()

            if not result.data:
                return

            # Agregar por titulo normalizado
            from collections import defaultdict
            patterns = defaultdict(lambda: {
                "first_seen": None,
                "last_seen": None,
                "dates": set(),
                "total_volume": 0,
                "sources": set(),
                "countries": set()
            })

            for trend in result.data:
                title = trend["title"].lower().strip()
                date = trend["collected_date"]
                volume = trend.get("volume", 0) or 0

                p = patterns[title]
                if p["first_seen"] is None or date < p["first_seen"]:
                    p["first_seen"] = date
                if p["last_seen"] is None or date > p["last_seen"]:
                    p["last_seen"] = date
                p["dates"].add(date)
                p["total_volume"] += volume
                p["sources"].add(trend.get("source", "unknown"))
                p["countries"].add(trend.get("country", "global"))

            # Atualizar tabela de patterns
            records = []
            for title, p in patterns.items():
                days_active = len(p["dates"])
                avg_volume = p["total_volume"] // days_active if days_active > 0 else 0

                records.append({
                    "title_normalized": title,
                    "first_seen": p["first_seen"],
                    "last_seen": p["last_seen"],
                    "days_active": days_active,
                    "total_volume": p["total_volume"],
                    "avg_volume": avg_volume,
                    "sources_found": ",".join(p["sources"]),
                    "countries_found": ",".join(p["countries"]),
                    "is_evergreen": days_active >= 7,
                    "is_growing": days_active >= 3,
                    "updated_at": datetime.now().isoformat()
                })

            if records:
                self.client.table("trend_patterns").upsert(
                    records,
                    on_conflict="title_normalized"
                ).execute()

            logger.info(f"Atualizados {len(records)} padroes de trends")

        except Exception as e:
            logger.error(f"Erro ao atualizar patterns: {e}")

    def get_evergreen_trends(self, min_days: int = 7) -> List[Dict]:
        """
        Retorna trends que estao em alta ha X dias ou mais.

        Args:
            min_days: Minimo de dias para considerar evergreen

        Returns:
            Lista de trends evergreen
        """
        if not self.is_connected():
            logger.warning("Supabase nao conectado.")
            return []

        try:
            result = self.client.table("trend_patterns") \
                .select("*") \
                .gte("days_active", min_days) \
                .order("days_active", desc=True) \
                .order("avg_volume", desc=True) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar evergreen trends: {e}")
            return []

    def get_trends_by_source(self, source: str, date: str = None, limit: int = 100) -> List[Dict]:
        """
        Retorna trends filtrados por fonte.

        Args:
            source: 'google_trends', 'youtube', 'reddit', 'hackernews'
            date: Data especifica (YYYY-MM-DD) ou None para hoje
            limit: Maximo de resultados

        Returns:
            Lista de trends
        """
        if not self.is_connected():
            return []

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            result = self.client.table("trends") \
                .select("*") \
                .eq("source", source) \
                .eq("collected_date", date) \
                .order("volume", desc=True) \
                .limit(limit) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar trends por fonte: {e}")
            return []

    def get_trends_by_country(self, country: str, date: str = None, limit: int = 100) -> List[Dict]:
        """
        Retorna trends filtrados por pais.

        Args:
            country: Codigo do pais (US, BR, etc.)
            date: Data especifica ou None para hoje
            limit: Maximo de resultados

        Returns:
            Lista de trends
        """
        if not self.is_connected():
            return []

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            result = self.client.table("trends") \
                .select("*") \
                .eq("country", country) \
                .eq("collected_date", date) \
                .order("volume", desc=True) \
                .limit(limit) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar trends por pais: {e}")
            return []

    def get_all_trends(self, date: str = None, limit: int = 500) -> List[Dict]:
        """
        Retorna todos os trends de uma data.

        Args:
            date: Data especifica ou None para hoje
            limit: Maximo de resultados

        Returns:
            Lista de trends
        """
        if not self.is_connected():
            return []

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            result = self.client.table("trends") \
                .select("*") \
                .eq("collected_date", date) \
                .order("volume", desc=True) \
                .limit(limit) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar todos os trends: {e}")
            return []

    def get_new_opportunities(self, subnicho_keywords: Dict[str, List[str]], min_days: int = 7) -> List[Dict]:
        """
        Detecta temas em alta que NAO estao nos subnichos atuais.
        Potenciais oportunidades de novos canais.

        Args:
            subnicho_keywords: Dict com keywords de cada subnicho
            min_days: Minimo de dias em alta

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
            title = trend.get("title_normalized", "").lower()

            # Verificar se NAO match com nenhum subnicho
            matches_subnicho = any(kw in title for kw in all_keywords)

            if not matches_subnicho:
                opportunities.append({
                    "title": trend.get("title_normalized", ""),
                    "days_active": trend.get("days_active", 0),
                    "first_seen": trend.get("first_seen"),
                    "last_seen": trend.get("last_seen"),
                    "avg_volume": trend.get("avg_volume", 0),
                    "sources": trend.get("sources_found", ""),
                    "countries": trend.get("countries_found", ""),
                    "recommendation": "Considerar abertura de canal ou adicionar aos subnichos"
                })

        return opportunities

    def get_stats(self) -> Dict:
        """
        Retorna estatisticas gerais do banco.

        Returns:
            Dict com estatisticas
        """
        if not self.is_connected():
            return {
                "total_trends": 0,
                "total_days_collected": 0,
                "evergreen_count": 0,
                "by_source": {},
                "connected": False
            }

        try:
            # Total de trends
            trends_result = self.client.table("trends").select("id", count="exact").execute()
            total_trends = trends_result.count if hasattr(trends_result, 'count') else len(trends_result.data or [])

            # Total de dias
            dates_result = self.client.table("trends").select("collected_date").execute()
            unique_dates = set(t["collected_date"] for t in (dates_result.data or []))
            total_days = len(unique_dates)

            # Evergreen count
            evergreen_result = self.client.table("trend_patterns") \
                .select("id", count="exact") \
                .eq("is_evergreen", True) \
                .execute()
            evergreen_count = evergreen_result.count if hasattr(evergreen_result, 'count') else 0

            # Por fonte
            by_source = {}
            for source in ["google_trends", "youtube", "reddit", "hackernews"]:
                source_result = self.client.table("trends") \
                    .select("id", count="exact") \
                    .eq("source", source) \
                    .execute()
                by_source[source] = source_result.count if hasattr(source_result, 'count') else 0

            return {
                "total_trends": total_trends,
                "total_days_collected": total_days,
                "evergreen_count": evergreen_count,
                "by_source": by_source,
                "connected": True
            }

        except Exception as e:
            logger.error(f"Erro ao buscar stats: {e}")
            return {
                "total_trends": 0,
                "total_days_collected": 0,
                "evergreen_count": 0,
                "by_source": {},
                "connected": False,
                "error": str(e)
            }


# =============================================================================
# SQL PARA CRIAR TABELAS NO SUPABASE
# =============================================================================

CREATE_TABLES_SQL = """
-- Execute este SQL no Supabase SQL Editor para criar as tabelas

-- Tabela 1: Todos os trends coletados
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
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
    collected_at TIMESTAMPTZ NOT NULL,
    collected_date DATE NOT NULL,
    raw_data JSONB,
    UNIQUE(title, source, collected_date)
);

-- Tabela 2: Padroes detectados (evergreen, crescente)
CREATE TABLE IF NOT EXISTS trend_patterns (
    id SERIAL PRIMARY KEY,
    title_normalized TEXT NOT NULL UNIQUE,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    days_active INTEGER DEFAULT 1,
    total_volume BIGINT DEFAULT 0,
    avg_volume INTEGER DEFAULT 0,
    sources_found TEXT,
    countries_found TEXT,
    is_evergreen BOOLEAN DEFAULT FALSE,
    is_growing BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ
);

-- Tabela 3: Metadados de coleta
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    collected_date DATE UNIQUE NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    total_trends INTEGER DEFAULT 0,
    sources_used JSONB,
    countries_collected JSONB,
    status TEXT DEFAULT 'completed'
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_trends_source ON trends(source);
CREATE INDEX IF NOT EXISTS idx_trends_country ON trends(country);
CREATE INDEX IF NOT EXISTS idx_trends_date ON trends(collected_date);
CREATE INDEX IF NOT EXISTS idx_trends_title ON trends(title);
CREATE INDEX IF NOT EXISTS idx_patterns_evergreen ON trend_patterns(is_evergreen);

-- Habilitar RLS (Row Level Security) - opcional
-- ALTER TABLE trends ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trend_patterns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
"""


# =============================================================================
# TESTE DO MODULO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE - Supabase Database")
    print("=" * 60)

    # Verificar se credenciais estao configuradas
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("\n[!] SUPABASE_URL e SUPABASE_KEY nao configurados.")
        print("    Para testar, defina as variaveis de ambiente:")
        print("    export SUPABASE_URL='https://xxx.supabase.co'")
        print("    export SUPABASE_KEY='eyJhbGciOiJIUz...'")
        print("\n    Ou crie um arquivo .env com as variaveis.")
        print("\n" + "-" * 60)
        print("SQL para criar tabelas no Supabase:")
        print("-" * 60)
        print(CREATE_TABLES_SQL)
    else:
        # Testar conexao
        db = TrendDatabaseSupabase()

        if db.is_connected():
            print("\n[OK] Conectado ao Supabase!")

            # Testar stats
            stats = db.get_stats()
            print(f"\nEstatisticas:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            # Testar dados mock
            test_trends = [
                {
                    "title": "Test Trend from Python",
                    "source": "hackernews",
                    "country": "global",
                    "volume": 1234,
                    "url": "https://example.com/test"
                }
            ]

            print("\nSalvando trend de teste...")
            saved = db.save_trends(test_trends)
            print(f"  Salvos: {saved}")

        else:
            print("\n[!] Nao foi possivel conectar ao Supabase.")
            print("    Verifique as credenciais.")
