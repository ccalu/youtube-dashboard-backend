#!/usr/bin/env python3
"""
TREND MONITOR - Migração SQLite → Supabase
==========================================
Migra dados do banco SQLite local para o Supabase na nuvem.

USO:
    python3 database/migrate_to_supabase.py              # Migrar tudo
    python3 database/migrate_to_supabase.py --today      # Só dados de hoje
    python3 database/migrate_to_supabase.py --clear      # Limpar Supabase antes
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATA_DIR

# Carregar .env
try:
    from dotenv import load_dotenv
    import pathlib
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

from supabase import create_client


def get_sqlite_connection():
    """Conecta ao SQLite local"""
    db_path = os.path.join(DATA_DIR, "trends.db")
    return sqlite3.connect(db_path)


def get_supabase_client():
    """Conecta ao Supabase"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ SUPABASE_URL e SUPABASE_KEY não configurados!")
        sys.exit(1)

    return create_client(url, key)


def clear_supabase_data(client, date: str = None):
    """Limpa dados do Supabase (opcional)"""
    print("\n🗑️  Limpando dados existentes no Supabase...")

    if date:
        # Limpar só do dia específico
        client.table("tm_subnicho_matches").delete().eq("collected_date", date).execute()
        client.table("tm_trends").delete().eq("collected_date", date).execute()
        client.table("tm_collections").delete().eq("collected_date", date).execute()
        print(f"   Removidos dados de {date}")
    else:
        # Limpar tudo
        client.table("tm_subnicho_matches").delete().neq("id", 0).execute()
        client.table("tm_patterns").delete().neq("id", 0).execute()
        client.table("tm_trends").delete().neq("id", 0).execute()
        client.table("tm_collections").delete().neq("id", 0).execute()
        print("   Removidos todos os dados")


def fetch_sqlite_trends(conn, date: str = None):
    """Busca trends do SQLite"""
    cursor = conn.cursor()

    if date:
        cursor.execute("""
            SELECT id, title, source, country, language, volume, url,
                   channel_title, author, num_comments, collected_at,
                   collected_date, raw_data
            FROM trends
            WHERE collected_date = ?
            ORDER BY id
        """, (date,))
    else:
        cursor.execute("""
            SELECT id, title, source, country, language, volume, url,
                   channel_title, author, num_comments, collected_at,
                   collected_date, raw_data
            FROM trends
            ORDER BY collected_date, id
        """)

    columns = ['id', 'title', 'source', 'country', 'language', 'volume', 'url',
               'channel_title', 'author', 'num_comments', 'collected_at',
               'collected_date', 'raw_data']

    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def transform_for_supabase(trend: dict) -> dict:
    """Transforma registro SQLite para formato Supabase"""
    # Parse raw_data se existir
    raw_data = {}
    if trend.get('raw_data'):
        try:
            raw_data = json.loads(trend['raw_data'])
        except:
            raw_data = {}

    # Extrair campos adicionais do raw_data
    video_id = raw_data.get('video_id') or raw_data.get('id')
    view_count = raw_data.get('view_count') or raw_data.get('volume') or trend.get('volume', 0)
    like_count = raw_data.get('like_count', 0)
    comment_count = raw_data.get('comment_count') or raw_data.get('num_comments') or trend.get('num_comments', 0)
    duration_seconds = raw_data.get('duration_seconds', 0)
    quality_score = raw_data.get('quality_score', 0)
    thumbnail = raw_data.get('thumbnail', '')
    channel_id = raw_data.get('channel_id', '')
    category_id = raw_data.get('category_id', '')
    published_at = raw_data.get('published_at')
    collection_type = raw_data.get('collection_type', '')
    matched_subnicho = raw_data.get('matched_subnicho')

    # Calcular engagement
    engagement = like_count / max(view_count, 1) if view_count > 0 else 0

    return {
        "title": trend['title'],
        "source": trend['source'],
        "video_id": video_id,
        "country": trend.get('country', 'global'),
        "language": trend.get('language', 'en'),
        "volume": view_count,
        "like_count": like_count,
        "comment_count": comment_count,
        "duration_seconds": duration_seconds,
        "quality_score": quality_score,
        "engagement_ratio": round(engagement, 4),
        "url": trend.get('url', ''),
        "thumbnail": thumbnail,
        "channel_title": trend.get('channel_title', ''),
        "channel_id": channel_id,
        "category_id": category_id,
        "author": trend.get('author', ''),
        "collection_type": collection_type,
        "matched_subnicho": matched_subnicho,
        "published_at": published_at,
        "collected_at": trend['collected_at'],
        "collected_date": trend['collected_date'],
        "raw_data": raw_data
    }


def migrate_trends(sqlite_conn, supabase_client, date: str = None, batch_size: int = 100):
    """Migra trends do SQLite para Supabase"""
    print("\n📥 Buscando trends do SQLite...")
    trends = fetch_sqlite_trends(sqlite_conn, date)
    print(f"   Encontrados: {len(trends)} registros")

    if not trends:
        print("   Nenhum dado para migrar.")
        return 0

    print("\n📤 Enviando para Supabase...")

    # Transformar todos
    records = [transform_for_supabase(t) for t in trends]

    # Enviar em batches
    total_saved = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            result = supabase_client.table("tm_trends").insert(batch).execute()
            saved = len(result.data) if result.data else 0
            total_saved += saved
            print(f"   Batch {i//batch_size + 1}: {saved} registros")
        except Exception as e:
            print(f"   ❌ Erro no batch {i//batch_size + 1}: {e}")

    return total_saved


def update_collections(supabase_client, date: str):
    """Atualiza tabela de collections com totais corretos"""
    print("\n📊 Atualizando collections...")

    # Buscar totais do Supabase
    trends = supabase_client.table("tm_trends").select("source, quality_score").eq("collected_date", date).execute()

    if not trends.data:
        print("   Sem dados para atualizar")
        return

    # Calcular estatísticas
    total = len(trends.data)
    by_source = {}
    scores = []

    for t in trends.data:
        src = t.get('source', 'unknown')
        by_source[src] = by_source.get(src, 0) + 1
        scores.append(t.get('quality_score', 0))

    avg_score = sum(scores) / len(scores) if scores else 0
    above_70 = len([s for s in scores if s >= 70])
    above_50 = len([s for s in scores if s >= 50])

    # Upsert
    collection = {
        "collected_date": date,
        "collected_at": datetime.now().isoformat(),
        "total_trends": total,
        "total_youtube": by_source.get('youtube', 0),
        "total_google": by_source.get('google_trends', 0),
        "total_hackernews": by_source.get('hackernews', 0),
        "avg_quality_score": int(avg_score),
        "trends_above_70": above_70,
        "trends_above_50": above_50,
        "status": "migrated"
    }

    supabase_client.table("tm_collections").upsert(
        collection,
        on_conflict="collected_date"
    ).execute()

    print(f"   Total: {total}")
    print(f"   YouTube: {by_source.get('youtube', 0)}")
    print(f"   Google Trends: {by_source.get('google_trends', 0)}")
    print(f"   Hacker News: {by_source.get('hackernews', 0)}")


def update_patterns(supabase_client):
    """Atualiza tabela de patterns"""
    print("\n🔄 Atualizando patterns...")

    # Buscar todos os trends
    result = supabase_client.table("tm_trends").select(
        "title, source, country, volume, collected_date"
    ).execute()

    if not result.data:
        return

    # Agregar por título normalizado
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

    # Criar registros
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

    # Upsert em batches
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase_client.table("tm_patterns").upsert(
                batch,
                on_conflict="title_normalized"
            ).execute()
        except Exception as e:
            print(f"   ❌ Erro: {e}")

    evergreen = len([r for r in records if r["is_evergreen"]])
    print(f"   Total patterns: {len(records)}")
    print(f"   Evergreen (7+ dias): {evergreen}")


def main():
    parser = argparse.ArgumentParser(description="Migrar SQLite → Supabase")
    parser.add_argument("--today", action="store_true", help="Migrar só dados de hoje")
    parser.add_argument("--date", type=str, help="Migrar dados de uma data específica (YYYY-MM-DD)")
    parser.add_argument("--clear", action="store_true", help="Limpar Supabase antes de migrar")
    args = parser.parse_args()

    # Determinar data
    if args.date:
        target_date = args.date
    elif args.today:
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = None  # Todos

    print("=" * 60)
    print("MIGRAÇÃO SQLite → Supabase")
    print("=" * 60)
    if target_date:
        print(f"Data: {target_date}")
    else:
        print("Data: TODOS os registros")

    # Conectar
    sqlite_conn = get_sqlite_connection()
    supabase = get_supabase_client()

    # Limpar se solicitado
    if args.clear:
        clear_supabase_data(supabase, target_date)

    # Migrar trends
    saved = migrate_trends(sqlite_conn, supabase, target_date)

    # Atualizar collections e patterns
    if target_date:
        update_collections(supabase, target_date)

    update_patterns(supabase)

    # Fechar SQLite
    sqlite_conn.close()

    print("\n" + "=" * 60)
    print(f"✅ MIGRAÇÃO CONCLUÍDA: {saved} trends enviados")
    print("=" * 60)


if __name__ == "__main__":
    main()
