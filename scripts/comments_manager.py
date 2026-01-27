"""
Gerenciador de Respostas para Comentários
Data: 26/01/2026
Objetivo: Gerenciar respostas únicas e humanizadas para comentários dos canais monetizados
"""

import random
import re
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CommentsResponseManager:
    """Gerencia geração de respostas únicas e humanizadas"""

    def __init__(self):
        self.used_responses = set()  # Cache de respostas já usadas
        self.response_variations = self._load_variations()

    def _load_variations(self) -> Dict:
        """Carrega banco de variações para humanização"""
        return {
            'greetings': {
                'en': ['Thanks', 'Thank you', 'Thanks so much', 'Thank you so much', 'Appreciate it', 'Thanks a lot'],
                'pt': ['Obrigado', 'Valeu', 'Muito obrigado', 'Brigadão', 'Vlw', 'Agradeço'],
                'es': ['Gracias', 'Muchas gracias', 'Gracias!', 'Mil gracias']
            },
            'emojis': ['😊', '🙏', '❤️', '🔥', '👻', '💪', '✨', '🎬', '🙌', '👍', '💯', '🚀'],
            'punctuation': ['!', '!!', '.', '...'],
            'closings': {
                'en': ['', 'More coming soon', 'Stay tuned', 'New videos weekly', 'Thanks for watching'],
                'pt': ['', 'Tem mais vindo', 'Tmj', 'Abraço', 'Fique ligado', 'Até a próxima'],
                'es': ['', 'Más contenido pronto', 'Hasta la próxima', 'Saludos']
            },
            'negative_responses': {
                'en': [
                    "Thanks for the feedback, we'll improve this",
                    "Appreciate your input! We'll work on it",
                    "Thanks for letting us know, will fix it",
                    "Good point! We'll make it better next time"
                ],
                'pt': [
                    "Obrigado pelo feedback! Vamos melhorar",
                    "Valeu pela dica, vamos ajustar",
                    "Agradeço o comentário, vamos corrigir",
                    "Boa observação! Melhoraremos isso"
                ]
            }
        }

    def detect_language(self, text: str) -> str:
        """Detecta o idioma do comentário"""
        pt_patterns = r'\b(que|para|com|não|você|muito|é|está|fazer|ter|mas|isso|foi|vai)\b'
        es_patterns = r'\b(que|pero|con|muy|está|hacer|tener|esto|fue)\b'

        text_lower = text.lower()

        if len(re.findall(pt_patterns, text_lower)) >= 3:
            return 'pt'
        elif len(re.findall(es_patterns, text_lower)) >= 2:
            return 'es'
        else:
            return 'en'

    def add_human_touches(self, response: str, language: str) -> str:
        """Adiciona imperfeições humanas ocasionais"""
        touches = []

        # 20% chance de adicionar emoji no final
        if random.random() < 0.2:
            emoji = random.choice(self.response_variations['emojis'])
            if emoji not in response:
                response += f" {emoji}"

        # 15% chance de usar minúsculas no início
        if random.random() < 0.15 and language in ['pt', 'en']:
            response = response[0].lower() + response[1:]

        # 10% chance de dupla pontuação
        if random.random() < 0.1 and response.endswith('!'):
            response = response[:-1] + '!!'

        # 5% chance de abreviação (apenas português)
        if random.random() < 0.05 and language == 'pt':
            response = response.replace('muito', 'mt')
            response = response.replace('Muito', 'Mt')

        return response

    def generate_unique_response(self,
                                comment_text: str,
                                author_name: str,
                                sentiment: str,
                                language: Optional[str] = None) -> str:
        """Gera resposta única e humanizada para um comentário"""

        if not language:
            language = self.detect_language(comment_text)

        # Base da resposta baseada no sentimento
        if sentiment == 'negative':
            base_responses = self.response_variations['negative_responses'].get(language,
                                                                               self.response_variations['negative_responses']['en'])
            response = random.choice(base_responses)

        elif sentiment == 'neutral' or '?' in comment_text:
            # Provavelmente uma pergunta
            response = self._handle_question(comment_text, language)

        else:  # positive
            response = self._create_positive_response(comment_text, author_name, language)

        # Garantir unicidade
        attempts = 0
        original_response = response
        while response in self.used_responses and attempts < 10:
            response = self._modify_response(original_response, language)
            attempts += 1

        # Adicionar toques humanos
        response = self.add_human_touches(response, language)

        # Adicionar ao cache
        self.used_responses.add(response)

        return response

    def _handle_question(self, comment: str, language: str) -> str:
        """Trata comentários que são perguntas"""
        comment_lower = comment.lower()

        # Detectar tipo de pergunta
        if any(word in comment_lower for word in ['when', 'quando', 'cuándo', 'next', 'próximo']):
            responses = {
                'en': ['New video coming Friday!', 'Next one drops soon!', 'Every week! Stay tuned'],
                'pt': ['Sexta tem mais!', 'Próximo vem em breve!', 'Toda semana tem novo!'],
                'es': ['¡Nuevo video el viernes!', '¡Pronto más contenido!']
            }
            return random.choice(responses.get(language, responses['en']))

        elif any(word in comment_lower for word in ['how', 'como', 'cómo']):
            responses = {
                'en': ['Great question! We use professional tools', 'Thanks for asking! It\'s a process'],
                'pt': ['Boa pergunta! Usamos ferramentas profissionais', 'Valeu por perguntar! É um processo'],
                'es': ['¡Buena pregunta! Usamos herramientas profesionales']
            }
            return random.choice(responses.get(language, responses['en']))

        else:
            # Resposta genérica para outras perguntas
            responses = {
                'en': ['Thanks for your question!', 'Good question! Check the description'],
                'pt': ['Obrigado pela pergunta!', 'Boa pergunta! Veja a descrição'],
                'es': ['¡Gracias por tu pregunta!', '¡Buena pregunta!']
            }
            return random.choice(responses.get(language, responses['en']))

    def _create_positive_response(self, comment: str, author_name: str, language: str) -> str:
        """Cria resposta para comentários positivos"""
        greetings = self.response_variations['greetings'].get(language, self.response_variations['greetings']['en'])
        closings = self.response_variations['closings'].get(language, self.response_variations['closings']['en'])

        greeting = random.choice(greetings)
        closing = random.choice(closings)

        # 30% chance de usar o nome
        use_name = random.random() < 0.3 and author_name and len(author_name) < 20

        if use_name:
            if language == 'pt':
                response = f"{greeting} {author_name}!"
            else:
                response = f"{greeting} {author_name}!"
        else:
            response = greeting

        # Adicionar closing se houver
        if closing and random.random() < 0.4:
            punctuation = random.choice(self.response_variations['punctuation'])
            response += f"{punctuation} {closing}"
        else:
            response += random.choice(self.response_variations['punctuation'])

        return response

    def _modify_response(self, response: str, language: str) -> str:
        """Modifica resposta para garantir unicidade"""
        modifications = []

        # Trocar sinônimos
        synonyms = {
            'en': {
                'Thanks': 'Thank you',
                'Thank you': 'Thanks',
                'so much': 'a lot',
                'a lot': 'so much'
            },
            'pt': {
                'Obrigado': 'Valeu',
                'Valeu': 'Obrigado',
                'muito': 'demais',
                'demais': 'muito'
            }
        }

        lang_synonyms = synonyms.get(language, synonyms['en'])
        for old, new in lang_synonyms.items():
            if old in response:
                response = response.replace(old, new, 1)
                break

        # Adicionar/remover emoji
        emojis = self.response_variations['emojis']
        if any(emoji in response for emoji in emojis):
            # Remover emoji
            for emoji in emojis:
                response = response.replace(emoji, '')
            response = response.strip()
        else:
            # Adicionar emoji
            response += f" {random.choice(emojis)}"

        return response

    def get_sentiment_indicator(self, sentiment: str, likes: int = 0) -> str:
        """Retorna indicador visual para o sentimento"""
        if likes > 100:
            return "⭐"  # Alto engagement

        indicators = {
            'positive': '🟢',
            'neutral': '🟡',
            'negative': '🔴'
        }
        return indicators.get(sentiment, '🟡')

    def process_comments_batch(self, comments: List[Dict]) -> List[Dict]:
        """Processa batch de comentários gerando respostas únicas"""
        processed = []

        for comment in comments:
            try:
                # Gerar resposta única
                response = self.generate_unique_response(
                    comment_text=comment.get('comment_text', ''),
                    author_name=comment.get('author_name', ''),
                    sentiment=comment.get('sentiment_category', 'neutral')
                )

                # Adicionar resposta e indicador
                comment['suggested_reply'] = response
                comment['sentiment_indicator'] = self.get_sentiment_indicator(
                    comment.get('sentiment_category', 'neutral'),
                    comment.get('like_count', 0)
                )

                processed.append(comment)

            except Exception as e:
                logger.error(f"Erro ao processar comentário {comment.get('comment_id')}: {e}")
                comment['suggested_reply'] = "Thanks for your comment!"
                comment['sentiment_indicator'] = '🟡'
                processed.append(comment)

        return processed

    def reset_cache(self):
        """Limpa cache de respostas usadas (usar diariamente)"""
        self.used_responses.clear()
        logger.info("Cache de respostas resetado")


# Singleton instance
comments_manager = CommentsResponseManager()