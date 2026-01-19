"""
Sistema de Análise de Comentários do YouTube
- Tradução automática para PT-BR
- Análise de sentimento
- Detecção de problemas
- Geração de insights acionáveis
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class CommentAnalyzer:
    """Analisa comentários do YouTube para gerar insights"""

    def __init__(self):

        # Palavras-chave para análise (português e inglês)
        self.problem_keywords = {
            'audio': {
                'pt': ['áudio', 'som', 'volume', 'escuto', 'ouvir', 'barulho', 'chiado', 'eco', 'mudo', 'baixo'],
                'en': ['audio', 'sound', 'volume', 'hear', 'noise', 'static', 'echo', 'mute', 'quiet', 'loud']
            },
            'video': {
                'pt': ['vídeo', 'imagem', 'qualidade', 'pixelado', 'borrado', 'travando', 'lag', 'resolução', 'desfocado'],
                'en': ['video', 'image', 'quality', 'pixelated', 'blurry', 'lagging', 'lag', 'resolution', 'blurred']
            },
            'content': {
                'pt': ['erro', 'errado', 'incorreto', 'confuso', 'não entendi', 'explicar', 'dúvida', 'mentira'],
                'en': ['error', 'wrong', 'incorrect', 'confused', "don't understand", 'explain', 'doubt', 'false']
            },
            'technical': {
                'pt': ['bug', 'problema', 'não funciona', 'quebrado', 'travou', 'crashou', 'falha'],
                'en': ['bug', 'issue', "doesn't work", 'broken', 'crashed', 'crash', 'fail', 'failed']
            }
        }

        self.praise_keywords = {
            'content': {
                'pt': ['ótimo', 'excelente', 'perfeito', 'incrível', 'adorei', 'amei', 'top', 'melhor', 'parabéns', 'genial'],
                'en': ['great', 'excellent', 'perfect', 'amazing', 'loved', 'awesome', 'best', 'congratulations', 'brilliant']
            },
            'editing': {
                'pt': ['edição', 'editado', 'montagem', 'efeitos', 'transições', 'cortes'],
                'en': ['editing', 'edited', 'effects', 'transitions', 'cuts', 'production']
            },
            'narration': {
                'pt': ['voz', 'narração', 'fala', 'explicação', 'didático', 'claro'],
                'en': ['voice', 'narration', 'speech', 'explanation', 'clear', 'teaching']
            },
            'thumbnail': {
                'pt': ['thumb', 'miniatura', 'capa', 'título'],
                'en': ['thumbnail', 'thumb', 'cover', 'title']
            }
        }

        # Palavras negativas e positivas para sentiment
        self.negative_words = {
            'pt': ['ruim', 'péssimo', 'horrível', 'terrível', 'odeio', 'pior', 'chato', 'entediante', 'fraco', 'decepção'],
            'en': ['bad', 'terrible', 'horrible', 'awful', 'hate', 'worst', 'boring', 'weak', 'disappointment', 'trash']
        }

        self.positive_words = {
            'pt': ['bom', 'ótimo', 'excelente', 'maravilhoso', 'fantástico', 'legal', 'bacana', 'show', 'massa', 'dahora'],
            'en': ['good', 'great', 'excellent', 'wonderful', 'fantastic', 'cool', 'nice', 'awesome', 'love', 'amazing']
        }

    async def translate_comment(self, text: str, source_lang: str = 'auto') -> Tuple[str, str, bool]:
        """
        Detecta idioma do comentário (sem tradução automática por enquanto)
        Retorna: (texto_original, idioma_detectado, foi_traduzido=False)
        """
        # Detecção simples de idioma baseada em palavras comuns
        portuguese_words = ['é', 'de', 'que', 'não', 'para', 'com', 'uma', 'por', 'mas', 'muito', 'bom', 'ótimo']
        english_words = ['the', 'is', 'and', 'to', 'of', 'in', 'for', 'with', 'that', 'this', 'good', 'great']
        spanish_words = ['el', 'la', 'es', 'en', 'que', 'y', 'por', 'con', 'muy', 'bueno', 'excelente']

        text_lower = text.lower()

        # Contar palavras de cada idioma
        pt_count = sum(1 for word in portuguese_words if word in text_lower)
        en_count = sum(1 for word in english_words if word in text_lower)
        es_count = sum(1 for word in spanish_words if word in text_lower)

        # Determinar idioma mais provável
        if pt_count > en_count and pt_count > es_count:
            detected_lang = 'pt'
        elif en_count > pt_count and en_count > es_count:
            detected_lang = 'en'
        elif es_count > pt_count and es_count > en_count:
            detected_lang = 'es'
        else:
            detected_lang = 'unknown'

        # Por enquanto, retorna o texto original sem tradução
        return text, detected_lang, False

    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Analisa sentimento do comentário
        Retorna: (score -1 a 1, categoria)
        """
        text_lower = text.lower()

        # Contar palavras positivas e negativas
        positive_count = 0
        negative_count = 0

        # Checar todas as línguas
        for lang in ['pt', 'en']:
            if lang in self.positive_words:
                positive_count += sum(1 for word in self.positive_words[lang] if word in text_lower)
            if lang in self.negative_words:
                negative_count += sum(1 for word in self.negative_words[lang] if word in text_lower)

        # Calcular score
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0, 'neutral'

        # Score de -1 a 1
        score = (positive_count - negative_count) / total_sentiment_words

        # Categorizar
        if score > 0.3:
            category = 'positive'
        elif score < -0.3:
            category = 'negative'
        else:
            category = 'neutral'

        return round(score, 2), category

    def detect_problems(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Detecta problemas no comentário
        Retorna: (tem_problema, tipo_problema, descrição)
        """
        text_lower = text.lower()

        for problem_type, keywords in self.problem_keywords.items():
            for lang in ['pt', 'en']:
                if lang in keywords:
                    for keyword in keywords[lang]:
                        if keyword in text_lower:
                            # Criar descrição específica
                            if problem_type == 'audio':
                                desc = "Problema de áudio detectado - verificar qualidade da gravação"
                            elif problem_type == 'video':
                                desc = "Problema de vídeo detectado - verificar renderização"
                            elif problem_type == 'content':
                                desc = "Possível erro de conteúdo - revisar informações"
                            else:
                                desc = "Problema técnico detectado - investigar causa"

                            return True, problem_type, desc

        return False, None, None

    def detect_praise(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detecta elogios no comentário
        Retorna: (tem_elogio, tipo_elogio)
        """
        text_lower = text.lower()

        for praise_type, keywords in self.praise_keywords.items():
            for lang in ['pt', 'en']:
                if lang in keywords:
                    for keyword in keywords[lang]:
                        if keyword in text_lower:
                            return True, praise_type

        return False, None

    def generate_insight(self, comment: Dict) -> Dict[str, Any]:
        """
        Gera insight completo sobre o comentário
        """
        text = comment.get('comment_text_pt', comment.get('comment_text_original', ''))

        # Análise de sentimento
        sentiment_score, sentiment_category = self.analyze_sentiment(text)

        # Detectar problemas
        has_problem, problem_type, problem_desc = self.detect_problems(text)

        # Detectar elogios
        has_praise, praise_type = self.detect_praise(text)

        # Gerar insight textual
        insight_text = ""
        action_required = False
        suggested_action = ""

        if has_problem:
            insight_text = f"[PROBLEMA] {problem_desc}"
            action_required = True

            if problem_type == 'audio':
                suggested_action = "Revisar configurações de áudio e microfone na próxima gravação"
            elif problem_type == 'video':
                suggested_action = "Verificar configurações de renderização e upload"
            elif problem_type == 'content':
                suggested_action = "Adicionar correção na descrição ou comentário fixado"
            else:
                suggested_action = "Investigar e corrigir problema reportado"

        elif has_praise:
            if praise_type == 'content':
                insight_text = "[ELOGIO] Conteúdo bem recebido - manter formato"
            elif praise_type == 'editing':
                insight_text = "[ELOGIO] Edição elogiada - replicar estilo"
            elif praise_type == 'narration':
                insight_text = "[ELOGIO] Narração aprovada - manter padrão"
            elif praise_type == 'thumbnail':
                insight_text = "[ELOGIO] Thumbnail eficaz - usar como referência"
            else:
                insight_text = "[POSITIVO] Feedback positivo geral"

        else:
            if sentiment_category == 'positive':
                insight_text = "[POSITIVO] Comentário positivo - engajamento saudável"
            elif sentiment_category == 'negative':
                insight_text = "[NEGATIVO] Comentário negativo - avaliar contexto"
                action_required = True
                suggested_action = "Verificar se há padrão em comentários negativos"
            else:
                insight_text = "[NEUTRO] Comentário neutro - sem ação necessária"

        return {
            'sentiment_score': sentiment_score,
            'sentiment_category': sentiment_category,
            'has_problem': has_problem,
            'problem_type': problem_type,
            'problem_description': problem_desc,
            'has_praise': has_praise,
            'praise_type': praise_type,
            'insight_text': insight_text,
            'action_required': action_required,
            'suggested_action': suggested_action
        }

    async def analyze_comment_batch(self, comments: List[Dict]) -> List[Dict]:
        """
        Analisa um lote de comentários
        """
        analyzed_comments = []

        for comment in comments:
            try:
                # Traduzir se necessário
                original_text = comment.get('comment_text_original', '')
                translated_text, original_lang, was_translated = await self.translate_comment(original_text)

                # Adicionar tradução ao comentário
                comment['comment_text_pt'] = translated_text
                comment['original_language'] = original_lang
                comment['is_translated'] = was_translated

                # Gerar insight
                insight = self.generate_insight(comment)

                # Combinar dados
                analyzed_comment = {
                    **comment,
                    **insight
                }

                analyzed_comments.append(analyzed_comment)

                # Pequena pausa para não sobrecarregar tradutor
                if was_translated:
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Erro ao analisar comentário: {e}")
                # Adicionar comentário sem análise
                analyzed_comments.append({
                    **comment,
                    'sentiment_score': 0,
                    'sentiment_category': 'neutral',
                    'has_problem': False,
                    'has_praise': False,
                    'insight_text': 'Erro na análise',
                    'action_required': False
                })

        return analyzed_comments

    def get_video_summary(self, comments: List[Dict]) -> Dict[str, Any]:
        """
        Gera resumo de comentários de um vídeo
        """
        if not comments:
            return {
                'total_comments': 0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'problems_found': [],
                'praises_found': [],
                'actionable_items': []
            }

        total = len(comments)

        # Distribuição de sentimento
        positive = len([c for c in comments if c.get('sentiment_category') == 'positive'])
        negative = len([c for c in comments if c.get('sentiment_category') == 'negative'])
        neutral = total - positive - negative

        # Problemas encontrados
        problems = [
            {
                'type': c['problem_type'],
                'description': c['problem_description'],
                'comment': c['comment_text_pt'][:200],
                'author': c.get('author_name', 'Anônimo')
            }
            for c in comments if c.get('has_problem')
        ]

        # Elogios encontrados
        praises = [
            {
                'type': c['praise_type'],
                'comment': c['comment_text_pt'][:200],
                'author': c.get('author_name', 'Anônimo')
            }
            for c in comments if c.get('has_praise')
        ]

        # Items acionáveis
        actionable = [
            {
                'insight': c['insight_text'],
                'action': c['suggested_action'],
                'comment': c['comment_text_pt'][:200],
                'author': c.get('author_name', 'Anônimo')
            }
            for c in comments if c.get('action_required')
        ]

        return {
            'total_comments': total,
            'sentiment_distribution': {
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'positive_pct': round(positive / total * 100, 1) if total > 0 else 0,
                'negative_pct': round(negative / total * 100, 1) if total > 0 else 0
            },
            'problems_found': problems[:10],  # Top 10 problemas
            'praises_found': praises[:10],    # Top 10 elogios
            'actionable_items': actionable[:10]  # Top 10 ações
        }