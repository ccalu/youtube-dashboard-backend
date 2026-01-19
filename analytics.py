#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Analytics Inteligente para Canais YouTube

Este módulo realiza análises estatísticas avançadas dos canais:
- Identificação de padrões de sucesso
- Clustering de conteúdo por performance
- Detecção de anomalias estatísticas
- Análise temporal (melhor dia/hora)
- Insights acionáveis baseados em dados reais

Autor: cellibs-escritorio
Data: 19/01/2026
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict, Counter
import re
import statistics

logger = logging.getLogger(__name__)


class ChannelAnalytics:
    """Classe principal para análises de canal YouTube"""

    def __init__(self, db_client):
        """
        Inicializa o analisador com cliente do banco

        Args:
            db_client: Instância do SupabaseClient
        """
        self.db = db_client

    async def analyze_channel(self, canal_id: int) -> Dict[str, Any]:
        """
        Análise completa de um canal

        Args:
            canal_id: ID do canal no banco

        Returns:
            Dicionário com todas as análises
        """
        try:
            # 1. Buscar dados do canal
            canal_info = await self._get_canal_info(canal_id)
            if not canal_info:
                logger.error(f"Canal {canal_id} não encontrado")
                return {}

            # 2. Buscar vídeos dos últimos 30 dias
            videos = await self._get_videos_30d(canal_id)

            # 3. Buscar histórico de 60 dias
            historico = await self._get_historico_60d(canal_id)

            # 4. Realizar análises
            metricas = self._calculate_metrics(canal_info, videos, historico)
            top_videos = self._get_top_videos(videos, limit=10)
            padroes = self._identify_patterns(videos)
            clusters = self._cluster_content(videos)
            anomalias = self._detect_anomalies(historico)
            melhor_momento = self._find_best_posting_time(videos)

            # 5. Compilar resultado
            return {
                'canal_info': {
                    'id': canal_info['id'],
                    'nome': canal_info['nome_canal'],
                    'subnicho': canal_info['subnicho'],
                    'lingua': canal_info['lingua'],
                    'tipo': canal_info['tipo'],
                    'url': canal_info['url_canal'],
                    'criado_em': canal_info.get('published_at'),
                    'custom_url': canal_info.get('custom_url'),
                    'inscritos': canal_info.get('inscritos_atual', 0),
                    'total_videos': canal_info.get('video_count', 0),
                    'total_views': canal_info.get('view_count', 0),
                    'frequencia_semanal': canal_info.get('frequencia_semanal', 0)
                },
                'metricas': metricas,
                'top_videos': top_videos,
                'padroes': padroes,
                'clusters': clusters,
                'anomalias': anomalias,
                'melhor_momento': melhor_momento
            }

        except Exception as e:
            logger.error(f"Erro na análise do canal {canal_id}: {e}")
            return {}

    async def _get_canal_info(self, canal_id: int) -> Optional[Dict]:
        """Busca informações básicas do canal"""
        try:
            # Buscar dados do canal
            response = self.db.supabase.table('canais_monitorados')\
                .select('*')\
                .eq('id', canal_id)\
                .execute()

            if not response.data:
                return None

            canal = response.data[0]

            # Buscar último snapshot de inscritos
            historico = self.db.supabase.table('dados_canais_historico')\
                .select('inscritos')\
                .eq('canal_id', canal_id)\
                .order('data_coleta', desc=True)\
                .limit(1)\
                .execute()

            if historico.data:
                canal['inscritos_atual'] = historico.data[0]['inscritos']

            return canal

        except Exception as e:
            logger.error(f"Erro ao buscar info do canal: {e}")
            return None

    async def _get_videos_30d(self, canal_id: int) -> List[Dict]:
        """Busca vídeos dos últimos 30 dias"""
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

            response = self.db.supabase.table('videos_historico')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .gte('data_publicacao', cutoff_date)\
                .order('views_atuais', desc=True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar vídeos: {e}")
            return []

    async def _get_historico_60d(self, canal_id: int) -> List[Dict]:
        """Busca histórico de 60 dias"""
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).date().isoformat()

            response = self.db.supabase.table('dados_canais_historico')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .gte('data_coleta', cutoff_date)\
                .order('data_coleta', desc=False)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []

    def _calculate_metrics(self, canal: Dict, videos: List[Dict], historico: List[Dict]) -> Dict:
        """Calcula métricas avançadas"""
        try:
            # Métricas básicas
            metricas = {
                'views_7d': 0,
                'views_15d': 0,
                'views_30d': 0,
                'growth_7d': 0,
                'growth_15d': 0,
                'growth_30d': 0,
                'engagement_rate': 0,
                'score': 0,
                'inscritos_diff': 0,
                'ranking_subnicho': 0,
                'percentil': 0
            }

            # Pegar dados mais recentes do histórico
            if historico:
                latest = historico[-1] if historico else {}
                metricas['views_7d'] = latest.get('views_7d', 0)
                metricas['views_15d'] = latest.get('views_15d', 0)
                metricas['views_30d'] = latest.get('views_30d', 0)

                # Calcular crescimento
                if len(historico) >= 7:
                    week_ago = historico[-7]
                    if week_ago.get('views_7d', 0) > 0:
                        metricas['growth_7d'] = ((metricas['views_7d'] - week_ago['views_7d']) / week_ago['views_7d']) * 100

                if len(historico) >= 15:
                    two_weeks_ago = historico[-15]
                    if two_weeks_ago.get('views_15d', 0) > 0:
                        metricas['growth_15d'] = ((metricas['views_15d'] - two_weeks_ago['views_15d']) / two_weeks_ago['views_15d']) * 100

                if len(historico) >= 30:
                    month_ago = historico[-30]
                    if month_ago.get('views_30d', 0) > 0:
                        metricas['growth_30d'] = ((metricas['views_30d'] - month_ago['views_30d']) / month_ago['views_30d']) * 100

                # Diferença de inscritos
                if len(historico) >= 2:
                    metricas['inscritos_diff'] = latest.get('inscritos', 0) - historico[-2].get('inscritos', 0)

            # Engagement rate dos vídeos
            if videos:
                total_engagement = sum(v.get('likes', 0) + v.get('comentarios', 0) for v in videos)
                total_views = sum(v.get('views_atuais', 0) for v in videos)
                if total_views > 0:
                    metricas['engagement_rate'] = round((total_engagement / total_views) * 100, 2)

            # Score de performance (0-100)
            inscritos = canal.get('inscritos_atual', 1)
            if inscritos > 0 and metricas['views_30d'] > 0:
                # Score baseado em views por inscrito
                views_per_sub = metricas['views_30d'] / inscritos
                # Normalizar para 0-100 (assumindo que 10 views/inscrito = score 100)
                metricas['score'] = min(100, round(views_per_sub * 10, 1))

            return metricas

        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            return {}

    def _get_top_videos(self, videos: List[Dict], limit: int = 10) -> List[Dict]:
        """Retorna top vídeos com métricas adicionais"""
        try:
            # Ordenar por views
            sorted_videos = sorted(videos, key=lambda x: x.get('views_atuais', 0), reverse=True)[:limit]

            result = []
            now = datetime.now(timezone.utc)

            for video in sorted_videos:
                # Calcular dias desde publicação
                pub_date = datetime.fromisoformat(video['data_publicacao'].replace('Z', '+00:00'))
                dias = (now - pub_date).days

                # Calcular engagement rate do vídeo
                views = video.get('views_atuais', 1)
                engagement = (video.get('likes', 0) + video.get('comentarios', 0)) / views * 100 if views > 0 else 0

                # Thumbnail URL
                video_id = video.get('video_id', '')
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ''

                result.append({
                    'video_id': video_id,
                    'titulo': video.get('titulo', ''),
                    'url': video.get('url_video', ''),
                    'thumbnail_url': thumbnail_url,
                    'views': views,
                    'likes': video.get('likes', 0),
                    'comentarios': video.get('comentarios', 0),
                    'duracao': video.get('duracao', 0),
                    'publicado_ha_dias': dias,
                    'engagement_rate': round(engagement, 2),
                    'views_por_dia': round(views / max(dias, 1))
                })

            return result

        except Exception as e:
            logger.error(f"Erro ao processar top vídeos: {e}")
            return []

    def _identify_patterns(self, videos: List[Dict]) -> List[Dict]:
        """
        Identifica padrões de sucesso com significância estatística

        Returns:
            Lista de padrões identificados com boost percentual
        """
        try:
            if len(videos) < 10:
                return []

            padroes = []

            # Dividir vídeos em quartis
            views_list = [v.get('views_atuais', 0) for v in videos]
            if not views_list:
                return []

            q75 = np.percentile(views_list, 75)
            q25 = np.percentile(views_list, 25)

            top_performers = [v for v in videos if v.get('views_atuais', 0) > q75]
            low_performers = [v for v in videos if v.get('views_atuais', 0) < q25]

            if not top_performers or not low_performers:
                return []

            # PADRÃO 1: Títulos com números
            top_with_numbers = sum(1 for v in top_performers if any(c.isdigit() for c in v.get('titulo', '')))
            low_with_numbers = sum(1 for v in low_performers if any(c.isdigit() for c in v.get('titulo', '')))

            pct_top_numbers = (top_with_numbers / len(top_performers)) * 100 if top_performers else 0
            pct_low_numbers = (low_with_numbers / len(low_performers)) * 100 if low_performers else 0

            if pct_top_numbers > pct_low_numbers * 1.2:  # Só se diferença > 20%
                boost = ((pct_top_numbers / max(pct_low_numbers, 1)) - 1) * 100
                padroes.append({
                    'tipo': 'titulo_numeros',
                    'descricao': 'Títulos com números',
                    'boost': f'+{boost:.0f}%',
                    'evidencia': f'{pct_top_numbers:.0f}% dos top vs {pct_low_numbers:.0f}% dos baixos',
                    'exemplos': [v['titulo'] for v in top_performers if any(c.isdigit() for c in v.get('titulo', ''))][:3]
                })

            # PADRÃO 2: Títulos com perguntas
            top_with_questions = sum(1 for v in top_performers if '?' in v.get('titulo', ''))
            low_with_questions = sum(1 for v in low_performers if '?' in v.get('titulo', ''))

            pct_top_questions = (top_with_questions / len(top_performers)) * 100
            pct_low_questions = (low_with_questions / len(low_performers)) * 100

            if pct_top_questions > pct_low_questions * 1.2:
                boost = ((pct_top_questions / max(pct_low_questions, 1)) - 1) * 100
                padroes.append({
                    'tipo': 'titulo_perguntas',
                    'descricao': 'Títulos com perguntas',
                    'boost': f'+{boost:.0f}%',
                    'evidencia': f'{pct_top_questions:.0f}% dos top vs {pct_low_questions:.0f}% dos baixos',
                    'exemplos': [v['titulo'] for v in top_performers if '?' in v.get('titulo', '')][:3]
                })

            # PADRÃO 3: Duração ideal
            duracao_top = [v.get('duracao', 0) for v in top_performers if v.get('duracao', 0) > 0]
            duracao_low = [v.get('duracao', 0) for v in low_performers if v.get('duracao', 0) > 0]

            if duracao_top and duracao_low:
                media_top = np.mean(duracao_top) / 60  # Converter para minutos
                media_low = np.mean(duracao_low) / 60

                if media_top > media_low * 1.2 or media_top < media_low * 0.8:
                    diff_pct = ((media_top / media_low) - 1) * 100
                    padroes.append({
                        'tipo': 'duracao_ideal',
                        'descricao': f'Duração ideal: {media_top:.1f} minutos',
                        'boost': f'{diff_pct:+.0f}%',
                        'evidencia': f'Top: {media_top:.1f}min vs Baixos: {media_low:.1f}min',
                        'range_ideal': f'{media_top-2:.0f}-{media_top+2:.0f} minutos'
                    })

            # PADRÃO 4: Palavras-chave de sucesso
            palavras_top = self._extract_keywords(top_performers)
            palavras_low = self._extract_keywords(low_performers)

            palavras_exclusivas_top = set(palavras_top.keys()) - set(palavras_low.keys())
            if palavras_exclusivas_top:
                top_keywords = list(palavras_exclusivas_top)[:5]
                padroes.append({
                    'tipo': 'keywords_sucesso',
                    'descricao': 'Palavras-chave de sucesso',
                    'boost': 'Variável',
                    'evidencia': f'Aparecem só nos top performers',
                    'keywords': top_keywords
                })

            return padroes

        except Exception as e:
            logger.error(f"Erro ao identificar padrões: {e}")
            return []

    def _extract_keywords(self, videos: List[Dict]) -> Dict[str, int]:
        """Extrai palavras-chave dos títulos"""
        keywords = Counter()
        stop_words = {'o', 'a', 'de', 'da', 'do', 'em', 'para', 'com', 'por', 'que', 'e', 'os', 'as', 'um', 'uma'}

        for video in videos:
            titulo = video.get('titulo', '').lower()
            # Remover caracteres especiais e dividir em palavras
            palavras = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]+\b', titulo)
            for palavra in palavras:
                if len(palavra) > 3 and palavra not in stop_words:
                    keywords[palavra] += 1

        return dict(keywords.most_common(20))

    def _cluster_content(self, videos: List[Dict]) -> List[Dict]:
        """
        Agrupa vídeos por tema e calcula performance

        Returns:
            Lista de clusters ordenados por ROI
        """
        try:
            if not videos:
                return []

            clusters = defaultdict(lambda: {
                'videos': [],
                'total_views': 0,
                'count': 0
            })

            # Palavras-chave por tema (expandível)
            temas = {
                'Batalhas e Guerras': ['batalha', 'guerra', 'conflito', 'luta', 'combate', 'militar', 'exército'],
                'Imperadores e Líderes': ['imperador', 'césar', 'augustus', 'rei', 'rainha', 'líder', 'general'],
                'Vida Cotidiana': ['vida', 'cotidiano', 'dia a dia', 'romano', 'grego', 'cidadão', 'povo'],
                'Mitologia': ['deus', 'deusa', 'mito', 'lenda', 'olimpo', 'mitologia', 'divindade'],
                'Arte e Cultura': ['arte', 'cultura', 'arquitetura', 'escultura', 'pintura', 'teatro', 'música'],
                'Filosofia': ['filosofia', 'filósofo', 'pensamento', 'ideia', 'teoria', 'sócrates', 'platão'],
                'Tecnologia Antiga': ['tecnologia', 'invenção', 'engenharia', 'construção', 'aqueduto', 'máquina']
            }

            # Classificar cada vídeo
            for video in videos:
                titulo_lower = video.get('titulo', '').lower()
                tema_encontrado = 'Outros'

                # Procurar tema correspondente
                for tema, keywords in temas.items():
                    if any(keyword in titulo_lower for keyword in keywords):
                        tema_encontrado = tema
                        break

                clusters[tema_encontrado]['videos'].append(video)
                clusters[tema_encontrado]['total_views'] += video.get('views_atuais', 0)
                clusters[tema_encontrado]['count'] += 1

            # Calcular métricas e preparar resultado
            total_views_canal = sum(v.get('views_atuais', 0) for v in videos)
            media_geral = total_views_canal / len(videos) if videos else 1

            resultado = []
            for tema, data in clusters.items():
                if data['count'] > 0:
                    media_views = data['total_views'] / data['count']
                    percentual = (data['total_views'] / total_views_canal * 100) if total_views_canal > 0 else 0
                    roi = media_views / media_geral if media_geral > 0 else 0

                    # Classificar performance
                    if roi >= 2:
                        categoria = 'alto'
                        emoji = '🏆'
                    elif roi >= 0.8:
                        categoria = 'medio'
                        emoji = '📈'
                    else:
                        categoria = 'baixo'
                        emoji = '⚠️'

                    resultado.append({
                        'tema': tema,
                        'categoria': categoria,
                        'emoji': emoji,
                        'quantidade_videos': data['count'],
                        'percentual_videos': round((data['count'] / len(videos)) * 100, 1),
                        'media_views': int(media_views),
                        'percentual_views': round(percentual, 1),
                        'roi': round(roi, 2)
                    })

            # Ordenar por ROI
            return sorted(resultado, key=lambda x: x['roi'], reverse=True)

        except Exception as e:
            logger.error(f"Erro ao criar clusters: {e}")
            return []

    def _detect_anomalies(self, historico: List[Dict]) -> List[Dict]:
        """
        Detecta anomalias usando análise estatística

        Returns:
            Lista de anomalias detectadas
        """
        try:
            if len(historico) < 7:
                return []

            anomalias = []

            # Análise de views_7d
            views_series = [h.get('views_7d', 0) for h in historico if h.get('views_7d') is not None]
            if len(views_series) > 3:
                media = np.mean(views_series)
                std = np.std(views_series)

                if std > 0:
                    # Detectar outliers (z-score > 2)
                    for i, views in enumerate(views_series[-7:]):  # Últimos 7 dias
                        z_score = (views - media) / std
                        if abs(z_score) > 2:
                            if z_score > 0:
                                anomalias.append({
                                    'tipo': 'spike_positivo',
                                    'gravidade': 'info',
                                    'emoji': '🚀',
                                    'descricao': f'Spike de views detectado',
                                    'detalhes': f'{abs(z_score):.1f}x acima do normal',
                                    'data': historico[-(7-i)]['data_coleta'] if i < len(historico) else None
                                })
                            else:
                                anomalias.append({
                                    'tipo': 'queda_abrupta',
                                    'gravidade': 'warning',
                                    'emoji': '📉',
                                    'descricao': f'Queda abrupta de views',
                                    'detalhes': f'{abs(z_score):.1f}x abaixo do normal',
                                    'data': historico[-(7-i)]['data_coleta'] if i < len(historico) else None
                                })

            # Análise de tendência (últimos 14 dias)
            if len(historico) >= 14:
                recent = historico[-7:]
                previous = historico[-14:-7]

                media_recent = np.mean([h.get('views_7d', 0) for h in recent])
                media_previous = np.mean([h.get('views_7d', 0) for h in previous])

                if media_previous > 0:
                    change = ((media_recent - media_previous) / media_previous) * 100
                    if change < -30:
                        anomalias.append({
                            'tipo': 'tendencia_negativa',
                            'gravidade': 'critical',
                            'emoji': '⚠️',
                            'descricao': 'Tendência negativa forte',
                            'detalhes': f'Queda de {abs(change):.0f}% na última semana'
                        })
                    elif change > 50:
                        anomalias.append({
                            'tipo': 'tendencia_positiva',
                            'gravidade': 'success',
                            'emoji': '📈',
                            'descricao': 'Crescimento acelerado',
                            'detalhes': f'Alta de {change:.0f}% na última semana'
                        })

            # Análise de engagement
            engagement_series = [h.get('engagement_rate', 0) for h in historico[-14:] if h.get('engagement_rate') is not None]
            if len(engagement_series) >= 7:
                # Verificar queda consistente
                is_declining = all(engagement_series[i] >= engagement_series[i+1] for i in range(len(engagement_series)-1))
                if is_declining and len(engagement_series) >= 5:
                    drop = engagement_series[0] - engagement_series[-1]
                    if drop > 0.5:  # Queda de mais de 0.5pp
                        anomalias.append({
                            'tipo': 'engagement_decline',
                            'gravidade': 'warning',
                            'emoji': '💬',
                            'descricao': 'Engagement em declínio',
                            'detalhes': f'Queda de {drop:.1f}pp em {len(engagement_series)} dias'
                        })

            return anomalias

        except Exception as e:
            logger.error(f"Erro ao detectar anomalias: {e}")
            return []

    def _find_best_posting_time(self, videos: List[Dict]) -> Dict:
        """
        Analisa melhor dia e hora para postar

        Returns:
            Dicionário com melhor momento e boost percentual
        """
        try:
            if len(videos) < 10:
                return {
                    'dia_semana': None,
                    'hora': None,
                    'boost': 0,
                    'mensagem': 'Dados insuficientes'
                }

            performance = defaultdict(list)
            dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']

            # Analisar performance por dia/hora
            for video in videos:
                try:
                    pub_date = datetime.fromisoformat(video['data_publicacao'].replace('Z', '+00:00'))
                    dia = pub_date.weekday()
                    hora = pub_date.hour

                    # Calcular views por dia (métrica normalizada)
                    dias_desde_pub = max((datetime.now(timezone.utc) - pub_date).days, 1)
                    views_por_dia = video.get('views_atuais', 0) / dias_desde_pub

                    key = f"{dia}_{hora}"
                    performance[key].append(views_por_dia)

                except Exception:
                    continue

            if not performance:
                return {
                    'dia_semana': None,
                    'hora': None,
                    'boost': 0,
                    'mensagem': 'Erro ao processar datas'
                }

            # Calcular médias
            medias = {}
            for key, views_list in performance.items():
                if len(views_list) >= 2:  # Mínimo de 2 vídeos para considerar
                    medias[key] = np.mean(views_list)

            if not medias:
                return {
                    'dia_semana': None,
                    'hora': None,
                    'boost': 0,
                    'mensagem': 'Dados insuficientes para análise'
                }

            # Encontrar melhor combinação
            best_key = max(medias, key=medias.get)
            best_dia, best_hora = map(int, best_key.split('_'))
            best_performance = medias[best_key]

            # Calcular boost
            media_geral = np.mean(list(medias.values()))
            boost = ((best_performance / media_geral) - 1) * 100 if media_geral > 0 else 0

            # Análise adicional: ranking de dias
            dias_performance = defaultdict(list)
            for key, value in medias.items():
                dia, _ = key.split('_')
                dias_performance[int(dia)].append(value)

            ranking_dias = []
            for dia, perfs in dias_performance.items():
                media_dia = np.mean(perfs)
                boost_dia = ((media_dia / media_geral) - 1) * 100 if media_geral > 0 else 0
                ranking_dias.append({
                    'dia': dias_semana[dia],
                    'performance': round(boost_dia)
                })

            ranking_dias.sort(key=lambda x: x['performance'], reverse=True)

            return {
                'dia_semana': dias_semana[best_dia],
                'dia_numero': best_dia,
                'hora': best_hora,
                'boost': round(boost),
                'mensagem': f'{dias_semana[best_dia]} às {best_hora}:00',
                'ranking_dias': ranking_dias[:3]  # Top 3 dias
            }

        except Exception as e:
            logger.error(f"Erro ao calcular melhor horário: {e}")
            return {
                'dia_semana': None,
                'hora': None,
                'boost': 0,
                'mensagem': 'Erro na análise'
            }