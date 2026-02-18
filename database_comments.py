"""
Database module for YouTube Comments with GPT Analysis
Handles all database operations for the comments system with GPT integration
Author: Cellibs
Date: 2026-01-19
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class CommentsDB:
    """Database client for comments system with GPT analysis"""

    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env")

        self.client: Client = create_client(url, key)
        logger.info("CommentsDB initialized successfully")

    # ========================================
    # SALVAR DADOS
    # ========================================

    async def save_video_comments(self, video_id: str, canal_id: int, comments: List[Dict]) -> bool:
        """
        Salva comentários analisados pelo GPT no banco de dados.

        Args:
            video_id: ID do vídeo YouTube
            canal_id: ID do canal no banco
            comments: Lista de comentários com análise GPT

        Returns:
            bool: True se salvou com sucesso
        """
        try:
            if not comments:
                logger.warning(f"Nenhum comentário para salvar: video_id={video_id}")
                return True

            # Preparar dados para inserção
            records = []
            for comment in comments:
                # Extrair dados básicos
                record = {
                    'comment_id': comment.get('comment_id'),
                    'video_id': video_id,
                    'video_title': comment.get('video_title'),
                    'canal_id': canal_id,
                    'author_name': comment.get('author_name'),
                    'author_channel_id': comment.get('author_channel_id'),
                    'comment_text_original': comment.get('text', comment.get('comment_text_original')),
                    'like_count': comment.get('like_count', 0),
                    'reply_count': comment.get('reply_count', 0),
                    'is_reply': comment.get('is_reply', False),
                    'parent_comment_id': comment.get('parent_comment_id'),
                    'published_at': comment.get('published_at'),
                    'collected_at': datetime.utcnow().isoformat()
                }

                # Se tem análise GPT, adicionar campos
                if 'gpt_analysis' in comment:
                    gpt = comment['gpt_analysis']
                    record['gpt_analysis'] = json.dumps(gpt) if isinstance(gpt, dict) else gpt
                    record['analyzed_at'] = datetime.utcnow().isoformat()

                    # Extrair campos principais para queries rápidas
                    sentiment = gpt.get('sentiment', {})
                    record['sentiment_category'] = sentiment.get('category')
                    record['sentiment_score'] = sentiment.get('score')
                    record['sentiment_confidence'] = sentiment.get('confidence')

                    record['categories'] = gpt.get('categories', [])
                    record['primary_category'] = gpt.get('primary_category')
                    record['emotional_tone'] = gpt.get('emotional_tone')

                # Campos de priorização e resposta
                record['priority_score'] = comment.get('priority_score', 0)
                record['urgency_level'] = comment.get('urgency_level')
                record['requires_response'] = comment.get('requires_response', False)
                record['suggested_response'] = comment.get('suggested_response')
                record['response_tone'] = comment.get('response_tone')
                record['insight_summary'] = comment.get('insight_summary')

                if comment.get('actionable_items'):
                    record['actionable_items'] = json.dumps(comment['actionable_items'])

                records.append(record)

            # Filtrar apenas comentários que ainda não existem no banco (INSERT, nunca sobrescrever)
            existing = self.client.table('video_comments').select('comment_id').eq('video_id', video_id).execute()
            existing_ids = set(r['comment_id'] for r in existing.data) if existing.data else set()
            new_records = [r for r in records if r.get('comment_id') not in existing_ids]

            if new_records:
                response = self.client.table('video_comments').insert(new_records).execute()
                logger.info(f"✅ {len(new_records)} novos comentários inseridos para vídeo {video_id} ({len(records) - len(new_records)} já existiam)")

                # Atualizar resumo do vídeo
                await self.update_video_summary(video_id, canal_id)
                return True
            else:
                logger.info(f"ℹ️ Todos {len(records)} comentários já existem para vídeo {video_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Erro ao salvar comentários: {e}")
            return False

    async def save_gpt_analysis(self, comment_id: str, analysis: Dict) -> bool:
        """
        Atualiza análise GPT de um comentário existente.

        Args:
            comment_id: ID do comentário
            analysis: Dicionário com análise GPT completa

        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            # Preparar dados para atualização
            update_data = {
                'gpt_analysis': json.dumps(analysis['gpt_analysis']) if 'gpt_analysis' in analysis else None,
                'analyzed_at': datetime.utcnow().isoformat()
            }

            # Extrair campos da análise
            if 'gpt_analysis' in analysis:
                gpt = analysis['gpt_analysis']
                sentiment = gpt.get('sentiment', {})

                update_data.update({
                    'sentiment_category': sentiment.get('category'),
                    'sentiment_score': sentiment.get('score'),
                    'sentiment_confidence': sentiment.get('confidence'),
                    'categories': gpt.get('categories', []),
                    'primary_category': gpt.get('primary_category'),
                    'emotional_tone': gpt.get('emotional_tone')
                })

            # Adicionar campos de priorização
            if 'priority_score' in analysis:
                update_data['priority_score'] = analysis['priority_score']
            if 'urgency_level' in analysis:
                update_data['urgency_level'] = analysis['urgency_level']
            if 'requires_response' in analysis:
                update_data['requires_response'] = analysis['requires_response']
            if 'suggested_response' in analysis:
                update_data['suggested_response'] = analysis['suggested_response']
            if 'response_tone' in analysis:
                update_data['response_tone'] = analysis['response_tone']
            if 'insight_summary' in analysis:
                update_data['insight_summary'] = analysis['insight_summary']
            if 'actionable_items' in analysis:
                update_data['actionable_items'] = json.dumps(analysis['actionable_items'])

            # Atualizar no banco
            response = self.client.table('video_comments').update(
                update_data
            ).eq('comment_id', comment_id).execute()

            if response.data:
                logger.info(f"✅ Análise GPT salva para comentário {comment_id}")
                return True
            else:
                logger.error(f"❌ Erro ao salvar análise GPT")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao salvar análise GPT: {e}")
            return False

    async def update_video_summary(self, video_id: str, canal_id: int) -> bool:
        """
        Atualiza resumo de comentários de um vídeo.

        Args:
            video_id: ID do vídeo
            canal_id: ID do canal

        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            # Buscar estatísticas dos comentários
            comments = self.client.table('video_comments').select(
                'sentiment_category, priority_score, categories, requires_response, '
                'is_reviewed, is_responded, is_resolved, published_at, analyzed_at'
            ).eq('video_id', video_id).execute()

            if not comments.data:
                logger.info(f"Nenhum comentário para resumir: {video_id}")
                return True

            # Calcular estatísticas
            total = len(comments.data)
            analyzed = sum(1 for c in comments.data if c['analyzed_at'])

            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0}
            priority_counts = {'high': 0, 'medium': 0, 'low': 0}
            category_counts = {'problem': 0, 'praise': 0, 'question': 0, 'suggestion': 0}

            requires_response = 0
            reviewed = 0
            responded = 0
            resolved = 0

            for comment in comments.data:
                # Sentimento
                sent = comment.get('sentiment_category')
                if sent in sentiment_counts:
                    sentiment_counts[sent] += 1

                # Prioridade
                score = comment.get('priority_score', 0)
                if score >= 70:
                    priority_counts['high'] += 1
                elif score >= 40:
                    priority_counts['medium'] += 1
                else:
                    priority_counts['low'] += 1

                # Categorias
                categories = comment.get('categories', [])
                for cat in categories:
                    if cat in category_counts:
                        category_counts[cat] += 1

                # Status
                if comment.get('requires_response'):
                    requires_response += 1
                if comment.get('is_reviewed'):
                    reviewed += 1
                if comment.get('is_responded'):
                    responded += 1
                if comment.get('is_resolved'):
                    resolved += 1

            # Calcular percentuais
            positive_pct = round((sentiment_counts['positive'] / total * 100), 1) if total > 0 else 0
            negative_pct = round((sentiment_counts['negative'] / total * 100), 1) if total > 0 else 0

            # Buscar título do vídeo (se disponível)
            video_title = comments.data[0].get('video_title') if comments.data else None

            # Preparar dados do resumo
            summary_data = {
                'video_id': video_id,
                'video_title': video_title,
                'canal_id': canal_id,
                'total_comments': total,
                'analyzed_comments': analyzed,
                'positive_count': sentiment_counts['positive'],
                'negative_count': sentiment_counts['negative'],
                'neutral_count': sentiment_counts['neutral'],
                'mixed_count': sentiment_counts['mixed'],
                'positive_percentage': positive_pct,
                'negative_percentage': negative_pct,
                'problems_count': category_counts['problem'],
                'praise_count': category_counts['praise'],
                'questions_count': category_counts['question'],
                'suggestions_count': category_counts['suggestion'],
                'high_priority_count': priority_counts['high'],
                'medium_priority_count': priority_counts['medium'],
                'low_priority_count': priority_counts['low'],
                'requires_response_count': requires_response,
                'reviewed_count': reviewed,
                'responded_count': responded,
                'resolved_count': resolved,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Upsert no banco
            response = self.client.table('video_comments_summary').upsert(
                summary_data,
                on_conflict='video_id'
            ).execute()

            if response.data:
                logger.info(f"✅ Resumo atualizado para vídeo {video_id}")
                return True
            else:
                logger.error(f"❌ Erro ao atualizar resumo")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar resumo: {e}")
            return False

    async def record_gpt_metrics(self, metrics: Dict) -> bool:
        """
        Registra métricas diárias de uso do GPT.

        Args:
            metrics: Dicionário com métricas do dia

        Returns:
            bool: True se registrou com sucesso
        """
        try:
            # Preparar dados
            metrics_data = {
                'date': datetime.utcnow().date().isoformat(),
                'total_analyzed': metrics.get('total_analyzed', 0),
                'total_tokens_input': metrics.get('total_tokens_input', 0),
                'total_tokens_output': metrics.get('total_tokens_output', 0),
                'avg_response_time_ms': metrics.get('avg_response_time_ms'),
                'success_rate': metrics.get('success_rate'),
                'errors_count': metrics.get('errors_count', 0),
                'estimated_cost_usd': metrics.get('estimated_cost_usd', 0),
                'high_confidence_count': metrics.get('high_confidence_count', 0),
                'medium_confidence_count': metrics.get('medium_confidence_count', 0),
                'low_confidence_count': metrics.get('low_confidence_count', 0)
            }

            # Upsert no banco (atualiza se já existe para o dia)
            response = self.client.table('gpt_analysis_metrics').upsert(
                metrics_data,
                on_conflict='date'
            ).execute()

            if response.data:
                logger.info(f"✅ Métricas GPT registradas para {metrics_data['date']}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao registrar métricas GPT: {e}")
            return False

    # ========================================
    # BUSCAR DADOS
    # ========================================

    async def get_priority_comments(
        self,
        canal_id: Optional[int] = None,
        min_priority: int = 50,
        category: Optional[str] = None,
        urgency: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Busca comentários prioritários.

        Args:
            canal_id: Filtrar por canal (None = todos nossos canais)
            min_priority: Score mínimo (default: 50)
            category: Filtrar por categoria
            urgency: Filtrar por urgência
            limit: Quantidade máxima
            offset: Paginação

        Returns:
            Lista de comentários ordenados por priority_score DESC
        """
        try:
            # Construir query
            query = self.client.table('priority_comments_view').select('*')

            # Aplicar filtros
            query = query.gte('priority_score', min_priority)

            if canal_id:
                query = query.eq('canal_id', canal_id)

            if category:
                query = query.contains('categories', [category])

            if urgency:
                query = query.eq('urgency_level', urgency)

            # Ordenar e limitar
            query = query.order('priority_score', desc=True)
            query = query.limit(limit).offset(offset)

            # Executar
            response = query.execute()

            if response.data:
                logger.info(f"📊 {len(response.data)} comentários prioritários encontrados")
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar comentários prioritários: {e}")
            return []

    async def get_pending_responses(
        self,
        canal_id: Optional[int] = None,
        urgency: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Busca comentários pendentes de resposta.

        Args:
            canal_id: Filtrar por canal
            urgency: Filtrar por urgência
            limit: Quantidade máxima
            offset: Paginação

        Returns:
            Lista de comentários que requerem resposta
        """
        try:
            # Usar view específica
            query = self.client.table('pending_response_view').select('*')

            # Aplicar filtros
            if canal_id:
                query = query.eq('canal_id', canal_id)

            if urgency:
                query = query.eq('urgency_level', urgency)

            # Ordenar e limitar
            query = query.order('priority_score', desc=True)
            query = query.limit(limit).offset(offset)

            # Executar
            response = query.execute()

            if response.data:
                logger.info(f"📬 {len(response.data)} comentários pendentes de resposta")
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar pendentes: {e}")
            return []

    async def get_comments_by_category(
        self,
        canal_id: int,
        category: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Busca comentários por categoria.

        Args:
            canal_id: ID do canal
            category: Categoria (problem, praise, question, suggestion, feedback)
            limit: Quantidade
            offset: Paginação

        Returns:
            Lista de comentários da categoria
        """
        try:
            query = self.client.table('video_comments').select('*')
            query = query.eq('canal_id', canal_id)
            query = query.contains('categories', [category])
            query = query.order('priority_score', desc=True)
            query = query.limit(limit).offset(offset)

            response = query.execute()

            if response.data:
                logger.info(f"📁 {len(response.data)} comentários na categoria '{category}'")
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar por categoria: {e}")
            return []

    async def get_comments_stats(
        self,
        canal_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        Retorna estatísticas gerais de comentários.

        Args:
            canal_id: Filtrar por canal (None = todos)
            days: Período em dias

        Returns:
            Dicionário com estatísticas
        """
        try:
            # Data limite
            date_limit = (datetime.utcnow() - timedelta(days=days)).isoformat()

            # Buscar comentários do período
            query = self.client.table('video_comments').select(
                'sentiment_category, sentiment_score, priority_score, categories, '
                'urgency_level, requires_response, is_responded, analyzed_at'
            ).gte('collected_at', date_limit)

            if canal_id:
                query = query.eq('canal_id', canal_id)

            response = query.execute()

            if not response.data:
                return {
                    'total_comments': 0,
                    'analyzed_comments': 0,
                    'pending_analysis': 0,
                    'high_priority_count': 0,
                    'requires_response_count': 0,
                    'pending_response_count': 0,
                    'avg_sentiment_score': 0,
                    'sentiment_distribution': {},
                    'category_distribution': {},
                    'urgency_distribution': {}
                }

            # Calcular estatísticas
            total = len(response.data)
            analyzed = sum(1 for c in response.data if c['analyzed_at'])
            pending_analysis = total - analyzed

            high_priority = sum(1 for c in response.data if c.get('priority_score', 0) >= 70)
            requires_response = sum(1 for c in response.data if c.get('requires_response'))
            pending_response = sum(1 for c in response.data
                                  if c.get('requires_response') and not c.get('is_responded'))

            # Média de sentimento
            sentiment_scores = [c['sentiment_score'] for c in response.data if c.get('sentiment_score')]
            avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0

            # Distribuições
            sentiment_dist = {}
            category_dist = {}
            urgency_dist = {}

            for comment in response.data:
                # Sentimento
                sent = comment.get('sentiment_category', 'unknown')
                sentiment_dist[sent] = sentiment_dist.get(sent, 0) + 1

                # Categorias
                for cat in comment.get('categories', []):
                    category_dist[cat] = category_dist.get(cat, 0) + 1

                # Urgência
                urg = comment.get('urgency_level', 'low')
                urgency_dist[urg] = urgency_dist.get(urg, 0) + 1

            return {
                'total_comments': total,
                'analyzed_comments': analyzed,
                'pending_analysis': pending_analysis,
                'high_priority_count': high_priority,
                'requires_response_count': requires_response,
                'pending_response_count': pending_response,
                'avg_sentiment_score': avg_sentiment,
                'sentiment_distribution': sentiment_dist,
                'category_distribution': category_dist,
                'urgency_distribution': urgency_dist
            }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return {}

    async def get_comments_by_video(
        self,
        video_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Busca comentários de um vídeo específico.

        Args:
            video_id: ID do vídeo
            limit: Quantidade máxima
            offset: Paginação

        Returns:
            Lista de comentários do vídeo
        """
        try:
            query = self.client.table('video_comments').select('*')
            query = query.eq('video_id', video_id)
            query = query.order('like_count', desc=True)  # Mais curtidos primeiro
            query = query.limit(limit).offset(offset)

            response = query.execute()

            if response.data:
                logger.info(f"💬 {len(response.data)} comentários encontrados para vídeo {video_id}")
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar comentários do vídeo: {e}")
            return []

    # ========================================
    # ATUALIZAR STATUS
    # ========================================

    async def update_comment_status(
        self,
        comment_id: str,
        is_reviewed: Optional[bool] = None,
        is_responded: Optional[bool] = None,
        is_resolved: Optional[bool] = None
    ) -> bool:
        """
        Atualiza status de tratamento de um comentário.

        Args:
            comment_id: ID do comentário
            is_reviewed: Marcar como revisado
            is_responded: Marcar como respondido
            is_resolved: Marcar como resolvido

        Returns:
            bool: True se atualizou com sucesso
        """
        try:
            # Preparar dados para atualização
            update_data = {'updated_at': datetime.utcnow().isoformat()}

            if is_reviewed is not None:
                update_data['is_reviewed'] = is_reviewed
                if is_reviewed:
                    update_data['reviewed_at'] = datetime.utcnow().isoformat()

            if is_responded is not None:
                update_data['is_responded'] = is_responded
                if is_responded:
                    update_data['responded_at'] = datetime.utcnow().isoformat()

            if is_resolved is not None:
                update_data['is_resolved'] = is_resolved
                if is_resolved:
                    update_data['resolved_at'] = datetime.utcnow().isoformat()

            # Atualizar no banco
            response = self.client.table('video_comments').update(
                update_data
            ).eq('comment_id', comment_id).execute()

            if response.data:
                status_msgs = []
                if is_reviewed: status_msgs.append("revisado")
                if is_responded: status_msgs.append("respondido")
                if is_resolved: status_msgs.append("resolvido")

                if status_msgs:
                    logger.info(f"✅ Comentário {comment_id} marcado como: {', '.join(status_msgs)}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar status: {e}")
            return False

    async def mark_as_reviewed(self, comment_id: str, reviewed_by: Optional[str] = None) -> bool:
        """
        Marca comentário como revisado.

        Args:
            comment_id: ID do comentário
            reviewed_by: Quem revisou (opcional)

        Returns:
            bool: True se marcou com sucesso
        """
        return await self.update_comment_status(comment_id, is_reviewed=True)

    async def mark_as_responded(self, comment_id: str, actual_response: Optional[str] = None) -> bool:
        """
        Marca comentário como respondido.

        Args:
            comment_id: ID do comentário
            actual_response: Resposta que foi dada (opcional)

        Returns:
            bool: True se marcou com sucesso
        """
        try:
            update_data = {
                'is_responded': True,
                'responded_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            if actual_response:
                update_data['actual_response'] = actual_response

            response = self.client.table('video_comments').update(
                update_data
            ).eq('comment_id', comment_id).execute()

            if response.data:
                logger.info(f"✅ Comentário {comment_id} marcado como respondido")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao marcar como respondido: {e}")
            return False

    async def mark_as_resolved(self, comment_id: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Marca comentário como resolvido.

        Args:
            comment_id: ID do comentário
            resolution_notes: Notas sobre a resolução (opcional)

        Returns:
            bool: True se marcou com sucesso
        """
        try:
            update_data = {
                'is_resolved': True,
                'resolved_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            if resolution_notes:
                update_data['resolution_notes'] = resolution_notes

            response = self.client.table('video_comments').update(
                update_data
            ).eq('comment_id', comment_id).execute()

            if response.data:
                logger.info(f"✅ Comentário {comment_id} marcado como resolvido")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao marcar como resolvido: {e}")
            return False