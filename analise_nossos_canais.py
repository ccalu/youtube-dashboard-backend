"""
Script para analisar desempenho dos nossos canais
Métricas: inscritos, vídeos publicados, views 7d, views 30d
Ordenação: pior → melhor
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client

# Forçar UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar credenciais
SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

def calcular_score_desempenho(views_7d, views_30d, inscritos, videos_7d):
    """
    Calcula um score de desempenho baseado nas métricas.
    Score mais baixo = desempenho pior
    """
    if inscritos == 0:
        return 0

    # Engagement rate (views vs inscritos)
    engagement_7d = views_7d / inscritos if inscritos > 0 else 0
    engagement_30d = views_30d / inscritos if inscritos > 0 else 0

    # Views por vídeo (se tiver publicado)
    views_por_video = views_7d / videos_7d if videos_7d > 0 else 0

    # Score combinado (peso maior em engagement recente)
    score = (engagement_7d * 50) + (engagement_30d * 30) + (views_por_video * 0.01) + (videos_7d * 5)

    return round(score, 2)

def main():
    print("Analisando nossos canais...\n")

    # Conectar Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Buscar todos os canais "nosso"
    canais_response = supabase.table("canais_monitorados")\
        .select("*")\
        .eq("tipo", "nosso")\
        .eq("status", "ativo")\
        .execute()

    canais = canais_response.data
    print(f"Encontrados {len(canais)} canais nossos\n")

    # 2. Buscar histórico recente (últimos 2 dias)
    dois_dias_atras = (datetime.now() - timedelta(days=2)).date().isoformat()
    historico_response = supabase.table("dados_canais_historico")\
        .select("*")\
        .gte("data_coleta", dois_dias_atras)\
        .execute()

    # Organizar histórico por canal_id
    historico_por_canal = {}
    for h in historico_response.data:
        canal_id = h["canal_id"]
        if canal_id not in historico_por_canal:
            historico_por_canal[canal_id] = []
        historico_por_canal[canal_id].append(h)

    # 3. Processar cada canal
    resultados = []

    for canal in canais:
        canal_id = canal["id"]
        nome = canal["nome_canal"]
        subnicho = canal.get("subnicho", "N/A")

        # Dados padrão
        dados = {
            "nome": nome,
            "subnicho": subnicho,
            "inscritos": 0,
            "videos_7d": 0,
            "views_7d": 0,
            "views_30d": 0,
            "ultima_coleta": canal.get("ultima_coleta", "Sem coleta"),
            "score": 0
        }

        # Se tem histórico, pegar dados mais recentes
        if canal_id in historico_por_canal:
            # Ordenar por data (mais recente primeiro)
            historicos = sorted(historico_por_canal[canal_id],
                              key=lambda x: x.get("data_coleta", ""),
                              reverse=True)

            if historicos:
                h_recente = historicos[0]
                dados["inscritos"] = h_recente.get("inscritos", 0)
                dados["videos_7d"] = h_recente.get("videos_publicados_7d", 0)
                dados["views_7d"] = h_recente.get("views_7d", 0)
                dados["views_30d"] = h_recente.get("views_30d", 0)

        # Calcular score de desempenho
        dados["score"] = calcular_score_desempenho(
            dados["views_7d"],
            dados["views_30d"],
            dados["inscritos"],
            dados["videos_7d"]
        )

        resultados.append(dados)

    # 4. Ordenar do PIOR para o MELHOR (score crescente)
    resultados.sort(key=lambda x: x["score"])

    # 5. Exibir resultados
    print("=" * 120)
    print(f"{'#':<4} {'CANAL':<30} {'SUBNICHO':<20} {'INSCRITOS':>12} {'VÍDEOS 7D':>12} {'VIEWS 7D':>15} {'VIEWS 30D':>15} {'SCORE':>10}")
    print("=" * 120)

    for i, canal in enumerate(resultados, 1):
        print(f"{i:<4} {canal['nome'][:28]:<30} {canal['subnicho'][:18]:<20} "
              f"{canal['inscritos']:>12,} {canal['videos_7d']:>12} "
              f"{canal['views_7d']:>15,} {canal['views_30d']:>15,} "
              f"{canal['score']:>10.2f}")

    print("=" * 120)

    # Estatísticas gerais
    total_inscritos = sum(c["inscritos"] for c in resultados)
    total_videos = sum(c["videos_7d"] for c in resultados)
    total_views_7d = sum(c["views_7d"] for c in resultados)
    total_views_30d = sum(c["views_30d"] for c in resultados)

    print("\nTOTAIS:")
    print(f"   Inscritos totais: {total_inscritos:,}")
    print(f"   Videos publicados (7d): {total_videos}")
    print(f"   Views totais (7d): {total_views_7d:,}")
    print(f"   Views totais (30d): {total_views_30d:,}")

    # Médias
    if resultados:
        print("\nMEDIAS:")
        print(f"   Inscritos por canal: {total_inscritos // len(resultados):,}")
        print(f"   Views 7d por canal: {total_views_7d // len(resultados):,}")
        print(f"   Views 30d por canal: {total_views_30d // len(resultados):,}")

    # Alertas (piores 5)
    print("\nTOP 5 CANAIS COM PIOR DESEMPENHO:")
    for i, canal in enumerate(resultados[:5], 1):
        engagement = (canal['views_30d'] / canal['inscritos'] * 100) if canal['inscritos'] > 0 else 0
        print(f"   {i}. {canal['nome']} - Score: {canal['score']:.2f} | Engagement: {engagement:.2f}%")

if __name__ == "__main__":
    main()
