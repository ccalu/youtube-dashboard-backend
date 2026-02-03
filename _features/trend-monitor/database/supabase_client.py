"""
TREND MONITOR - Supabase Database Module
=========================================
Gerenciamento do banco de dados Supabase para armazenar trends e padroes.

TABELAS (prefixo tm_ para nao misturar com outros projetos):
- tm_trends: Todos os trends coletados (historico completo)
- tm_patterns: Analise de padroes (evergreen, crescente, etc.)
- tm_collections: Metadados de cada coleta diaria
- tm_subnicho_matches: Matches de trends com subnichos

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

            # Calcular engagement ratio
            views = trend.get("view_count", 0) or 0
            likes = trend.get("like_count", 0) or 0
            engagement = likes / max(views, 1) if views > 0 else 0

            record = {
                "title": title,
                "source": source,
                "video_id": trend.get("video_id"),
                "country": country,
                "language": language,
                "volume": volume,
                "like_count": likes,
                "comment_count": trend.get("comment_count") or trend.get("num_comments") or 0,
                "duration_seconds": trend.get("duration_seconds", 0),
                "quality_score": trend.get("quality_score", 0),
                "engagement_ratio": round(engagement, 4),
                "url": trend.get("url") or trend.get("hn_url") or "",
                "thumbnail": trend.get("thumbnail", ""),
                "channel_title": trend.get("channel_title") or trend.get("channel_name", ""),
                "channel_id": trend.get("channel_id", ""),
                "category_id": trend.get("category_id", ""),
                "author": trend.get("author", ""),
                "collection_type": trend.get("collection_type", ""),
                "matched_subnicho": trend.get("matched_subnicho"),
                "published_at": trend.get("published_at"),
                "collected_at": collected_at.isoformat(),
                "collected_date": collected_date,
                "raw_data": trend
            }
            records.append(record)

        if not records:
            return 0

        try:
            # Inserir em batches de 100
            saved = 0
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                result = self.client.table("tm_trends").insert(batch).execute()
                saved += len(result.data) if result.data else 0

            # Calcular estatisticas
            sources = list(set(t.get("source", "unknown") for t in trends))
            countries = list(set(t.get("country", "global") for t in trends))
            scores = [t.get("quality_score", 0) for t in trends]
            avg_score = sum(scores) / len(scores) if scores else 0

            # Contar por tipo
            youtube_count = len([t for t in trends if t.get("source") == "youtube"])
            google_count = len([t for t in trends if t.get("source") == "google_trends"])
            hn_count = len([t for t in trends if t.get("source") == "hackernews"])

            # Contar por tipo de coleta YouTube
            yt_trending = len([t for t in trends if t.get("collection_type") == "trending"])
            yt_subnicho = len([t for t in trends if t.get("collection_type") == "subnicho"])
            yt_discovery = len([t for t in trends if t.get("collection_type") == "discovery"])

            # Registrar coleta
            self.client.table("tm_collections").upsert({
                "collected_date": collected_date,
                "collected_at": collected_at.isoformat(),
                "total_trends": saved,
                "total_youtube": youtube_count,
                "total_google": google_count,
                "total_hackernews": hn_count,
                "youtube_trending": yt_trending,
                "youtube_subnicho": yt_subnicho,
                "youtube_discovery": yt_discovery,
                "avg_quality_score": int(avg_score),
                "trends_above_70": len([s for s in scores if s >= 70]),
                "trends_above_50": len([s for s in scores if s >= 50]),
                "sources_used": sources,
                "countries_collected": countries,
                "status": "completed"
            }, on_conflict="collected_date").execute()

            logger.info(f"Salvos {saved} trends no Supabase")
            return saved

        except Exception as e:
            logger.error(f"Erro ao salvar trends no Supabase: {e}")
            return 0

    def save_subnicho_matches(self, trends: List[Dict]) -> int:
        """
        Salva matches de subnicho na tabela subnicho_matches.

        Args:
            trends: Lista de trends com matched_subnicho

        Returns:
            Numero de matches salvos
        """
        if not self.is_connected():
            return 0

        # Filtrar trends com match de subnicho
        matched = [t for t in trends if t.get("matched_subnicho")]

        if not matched:
            return 0

        records = []
        collected_date = datetime.now().date().isoformat()

        for trend in matched:
            # Buscar ID do trend (precisa ja ter sido salvo)
            title = trend.get("title", "")
            source = trend.get("source", "")

            # Buscar trend_id
            try:
                result = self.client.table("tm_trends").select("id").eq(
                    "title", title
                ).eq("source", source).eq(
                    "collected_date", collected_date
                ).limit(1).execute()

                if result.data:
                    trend_id = result.data[0]["id"]
                    records.append({
                        "trend_id": trend_id,
                        "subnicho": trend.get("matched_subnicho"),
                        "match_score": trend.get("subnicho_score", 0),
                        "matched_keywords": trend.get("matched_keywords", []),
                        "collected_date": collected_date
                    })
            except:
                continue

        if not records:
            return 0

        try:
            result = self.client.table("tm_subnicho_matches").insert(records).execute()
            saved = len(result.data) if result.data else 0
            logger.info(f"Salvos {saved} matches de subnicho")
            return saved
        except Exception as e:
            logger.error(f"Erro ao salvar subnicho matches: {e}")
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
            result = self.client.table("tm_trends").select(
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
                    "sources_found": list(p["sources"]),
                    "countries_found": list(p["countries"]),
                    "is_evergreen": days_active >= 7,
                    "is_growing": days_active >= 3,
                    "updated_at": datetime.now().isoformat()
                })

            if records:
                self.client.table("tm_patterns").upsert(
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
            result = self.client.table("tm_patterns") \
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
            result = self.client.table("tm_trends") \
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
            result = self.client.table("tm_trends") \
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
            result = self.client.table("tm_trends") \
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
            trends_result = self.client.table("tm_trends").select("id", count="exact").execute()
            total_trends = trends_result.count if hasattr(trends_result, 'count') else len(trends_result.data or [])

            # Total de dias
            dates_result = self.client.table("tm_trends").select("collected_date").execute()
            unique_dates = set(t["collected_date"] for t in (dates_result.data or []))
            total_days = len(unique_dates)

            # Evergreen count
            evergreen_result = self.client.table("tm_patterns") \
                .select("id", count="exact") \
                .eq("is_evergreen", True) \
                .execute()
            evergreen_count = evergreen_result.count if hasattr(evergreen_result, 'count') else 0

            # Por fonte
            by_source = {}
            for source in ["google_trends", "youtube", "reddit", "hackernews"]:
                source_result = self.client.table("tm_trends") \
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
# SQL - Ver arquivo database/supabase_schema.sql
# =============================================================================
# Tabelas usam prefixo tm_:
# - tm_trends
# - tm_patterns
# - tm_collections
# - tm_subnicho_matches


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
        print("\n    SQL para criar tabelas: ver database/supabase_schema.sql")
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
