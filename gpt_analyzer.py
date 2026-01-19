"""
GPT Comment Analyzer - Análise inteligente de comentários com OpenAI
Processa comentários do YouTube usando GPT-4 para extrair insights detalhados
Author: Cellibs
Date: 2026-01-19
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class GPTAnalyzer:
    """Analisador de comentários usando OpenAI GPT"""

    def __init__(self):
        """Inicializa cliente OpenAI e configurações"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no .env")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Modelo padrão
        self.max_tokens_per_request = 16000  # Limite seguro para gpt-4o-mini

        # Métricas diárias
        self.daily_metrics = {
            'total_analyzed': 0,
            'total_tokens_input': 0,
            'total_tokens_output': 0,
            'total_requests': 0,
            'total_errors': 0,
            'total_time_ms': 0,
            'estimated_cost_usd': 0.0,
            'high_confidence_count': 0,
            'medium_confidence_count': 0,
            'low_confidence_count': 0
        }

        logger.info(f"GPTAnalyzer inicializado com modelo: {self.model}")

    def _get_system_prompt(self, canal_name: str = "", subnicho: str = "") -> str:
        """
        Retorna o system prompt otimizado para análise de comentários.
        """
        return f"""Você é um analista especializado em comentários de canais YouTube brasileiros.

CONTEXTO DO CANAL:
- Nome: {canal_name}
- Nicho: {subnicho if subnicho else "Dark YouTube / Terror / Mistério"}
- Idioma principal: Português Brasileiro
- Público: Brasileiro, jovem-adulto

SUA TAREFA:
Analisar comentários com precisão profissional, retornando um JSON estruturado.

DIRETRIZES IMPORTANTES:
1. Identifique o sentimento REAL (considere sarcasmo, ironia, contexto brasileiro)
2. Detecte problemas ESPECÍFICOS (não genéricos)
3. Priorize comentários que requerem ação imediata
4. Considere gírias e expressões brasileiras
5. Sugira respostas autênticas e personalizadas (não robotizadas)
6. Identifique oportunidades de conteúdo nas perguntas/sugestões

PRIORIZAÇÃO (0-100):
- 90-100: Problemas críticos que impedem visualização
- 70-89: Erros factuais, problemas técnicos sérios
- 50-69: Sugestões valiosas, perguntas relevantes
- 30-49: Elogios significativos, feedback construtivo
- 10-29: Comentários neutros informativos
- 0-9: Spam, irrelevante, apenas emoji

CATEGORIAS POSSÍVEIS:
- problem: Relata problema técnico ou de conteúdo
- praise: Elogio ao canal ou vídeo
- question: Pergunta genuína
- suggestion: Sugestão de melhoria ou conteúdo
- feedback: Feedback geral (pode ser misto)"""

    def _create_analysis_prompt(self, comments: List[Dict]) -> str:
        """
        Cria o prompt para análise em batch de comentários.
        """
        comments_text = []
        for i, comment in enumerate(comments, 1):
            text = comment.get('text', comment.get('comment_text_original', ''))
            author = comment.get('author_name', 'Anônimo')
            likes = comment.get('like_count', 0)

            comments_text.append(f"""
Comentário #{i}:
Autor: {author}
Likes: {likes}
Texto: {text}
""")

        return f"""Analise os seguintes {len(comments)} comentários e retorne um JSON com a análise de CADA um.

COMENTÁRIOS:
{''.join(comments_text)}

IMPORTANTE:
- Retorne APENAS um JSON válido, sem explicações adicionais
- O JSON deve ter a chave "comments" com um array de objetos
- Cada objeto deve ter EXATAMENTE a estrutura especificada abaixo
- Se não conseguir determinar algo, use null

ESTRUTURA ESPERADA:
{{
  "comments": [
    {{
      "index": 1,
      "sentiment": {{
        "category": "positive|negative|neutral|mixed",
        "score": -1.0 a 1.0,
        "confidence": 0.0 a 1.0,
        "nuances": ["sarcasm", "irony", "genuine", "emotional", etc]
      }},
      "categories": ["problem", "praise", "question", "suggestion", "feedback"],
      "primary_category": "categoria principal",
      "subcategories": {{
        "problem": ["audio", "video", "content", "technical"],
        "praise": ["content", "editing", "narration", "thumbnail"]
      }},
      "topics": ["tópico1", "tópico2"],
      "key_points": ["ponto principal 1", "ponto 2"],
      "emotional_tone": "angry|happy|frustrated|excited|neutral|concerned|curious|grateful",
      "intent": "criticize|compliment|ask|suggest|inform|express|engage",
      "context_indicators": ["frequent_viewer", "first_time", "fan", "critic"],
      "language": "pt|en|es|other",
      "priority_score": 0-100,
      "urgency_level": "low|medium|high|critical",
      "requires_response": true|false,
      "suggested_response": "Texto da resposta sugerida ou null",
      "response_tone": "formal|friendly|empathetic|professional|grateful",
      "insight_summary": "Resumo do insight principal",
      "actionable_items": ["ação 1", "ação 2"] ou null
    }}
  ]
}}"""

    async def analyze_batch(
        self,
        comments: List[Dict],
        video_title: str = "",
        canal_name: str = "",
        batch_size: int = 30
    ) -> List[Dict]:
        """
        Analisa um lote de comentários usando GPT.

        Args:
            comments: Lista de comentários para analisar
            video_title: Título do vídeo (contexto)
            canal_name: Nome do canal
            batch_size: Tamanho máximo do batch (padrão 30)

        Returns:
            Lista de comentários com análise GPT completa
        """
        if not comments:
            return []

        analyzed_comments = []

        # Processar em batches para economizar tokens
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            logger.info(f"Analisando batch {i//batch_size + 1} com {len(batch)} comentários...")

            try:
                # Fazer a análise do batch
                batch_analysis = await self._analyze_single_batch(batch, video_title, canal_name)

                # Combinar comentários originais com análise
                for j, comment in enumerate(batch):
                    if j < len(batch_analysis):
                        analysis = batch_analysis[j]

                        # Merge dados originais com análise
                        analyzed_comment = {
                            'comment_id': comment.get('comment_id', comment.get('commentId')),
                            'video_id': comment.get('video_id', comment.get('videoId')),
                            'video_title': video_title or comment.get('video_title'),
                            'author_name': comment.get('author_name', comment.get('author')),
                            'author_channel_id': comment.get('author_channel_id'),
                            'comment_text_original': comment.get('text', comment.get('comment_text_original')),
                            'like_count': comment.get('like_count', comment.get('likeCount', 0)),
                            'reply_count': comment.get('reply_count', comment.get('replyCount', 0)),
                            'is_reply': comment.get('is_reply', False),
                            'parent_comment_id': comment.get('parent_comment_id'),
                            'published_at': comment.get('published_at', comment.get('publishedAt')),

                            # Adicionar análise GPT
                            'gpt_analysis': {
                                'sentiment': analysis.get('sentiment', {}),
                                'categories': analysis.get('categories', []),
                                'primary_category': analysis.get('primary_category'),
                                'subcategories': analysis.get('subcategories', {}),
                                'topics': analysis.get('topics', []),
                                'key_points': analysis.get('key_points', []),
                                'emotional_tone': analysis.get('emotional_tone'),
                                'intent': analysis.get('intent'),
                                'context_indicators': analysis.get('context_indicators', []),
                                'language': analysis.get('language', 'pt')
                            },

                            # Campos extraídos para queries rápidas
                            'sentiment_category': analysis.get('sentiment', {}).get('category'),
                            'sentiment_score': analysis.get('sentiment', {}).get('score'),
                            'sentiment_confidence': analysis.get('sentiment', {}).get('confidence'),
                            'categories': analysis.get('categories', []),
                            'primary_category': analysis.get('primary_category'),
                            'emotional_tone': analysis.get('emotional_tone'),
                            'priority_score': analysis.get('priority_score', 0),
                            'urgency_level': analysis.get('urgency_level', 'low'),
                            'requires_response': analysis.get('requires_response', False),
                            'suggested_response': analysis.get('suggested_response'),
                            'response_tone': analysis.get('response_tone'),
                            'insight_summary': analysis.get('insight_summary'),
                            'actionable_items': analysis.get('actionable_items')
                        }

                        analyzed_comments.append(analyzed_comment)

                        # Atualizar métricas de confiança
                        confidence = analysis.get('sentiment', {}).get('confidence', 0)
                        if confidence >= 0.8:
                            self.daily_metrics['high_confidence_count'] += 1
                        elif confidence >= 0.5:
                            self.daily_metrics['medium_confidence_count'] += 1
                        else:
                            self.daily_metrics['low_confidence_count'] += 1
                    else:
                        # Se análise falhou para este comentário, adicionar sem análise
                        logger.warning(f"Análise não retornada para comentário {j+1}")
                        analyzed_comments.append(comment)

            except Exception as e:
                logger.error(f"Erro ao analisar batch: {e}")
                self.daily_metrics['total_errors'] += 1
                # Adicionar comentários sem análise em caso de erro
                analyzed_comments.extend(batch)

            # Pequena pausa entre batches para evitar rate limit
            if i + batch_size < len(comments):
                await asyncio.sleep(0.5)

        logger.info(f"✅ Total de {len(analyzed_comments)} comentários analisados")
        self.daily_metrics['total_analyzed'] += len(analyzed_comments)

        return analyzed_comments

    async def _analyze_single_batch(
        self,
        batch: List[Dict],
        video_title: str,
        canal_name: str
    ) -> List[Dict]:
        """
        Analisa um único batch de comentários.

        Returns:
            Lista com análises dos comentários
        """
        start_time = time.time()

        try:
            # Preparar mensagens
            messages = [
                {"role": "system", "content": self._get_system_prompt(canal_name)},
                {"role": "user", "content": self._create_analysis_prompt(batch)}
            ]

            # Chamar API da OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Mais determinístico para análises
                max_tokens=4000,  # Suficiente para ~30 comentários
                response_format={"type": "json_object"}  # Força resposta em JSON
            )

            # Processar resposta
            content = response.choices[0].message.content

            # Parse JSON
            try:
                result = json.loads(content)
                comments_analysis = result.get('comments', [])
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao fazer parse do JSON: {e}")
                logger.error(f"Resposta GPT: {content[:500]}")
                return []

            # Atualizar métricas
            self.daily_metrics['total_requests'] += 1
            if response.usage:
                self.daily_metrics['total_tokens_input'] += response.usage.prompt_tokens
                self.daily_metrics['total_tokens_output'] += response.usage.completion_tokens

                # Calcular custo estimado (GPT-4o-mini)
                input_cost = (response.usage.prompt_tokens / 1_000_000) * 0.15  # $0.15 per 1M
                output_cost = (response.usage.completion_tokens / 1_000_000) * 0.60  # $0.60 per 1M
                self.daily_metrics['estimated_cost_usd'] += (input_cost + output_cost)

            # Tempo de resposta
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.daily_metrics['total_time_ms'] += elapsed_ms

            logger.info(f"✅ Batch analisado em {elapsed_ms}ms - {len(comments_analysis)} comentários")

            return comments_analysis

        except Exception as e:
            logger.error(f"❌ Erro na chamada GPT: {e}")
            self.daily_metrics['total_errors'] += 1
            return []

    async def analyze_single_comment(self, comment: Dict, context: Dict = None) -> Dict:
        """
        Analisa um único comentário (útil para testes ou análise em tempo real).

        Args:
            comment: Comentário para analisar
            context: Contexto adicional (canal, vídeo, etc)

        Returns:
            Comentário com análise completa
        """
        batch_result = await self.analyze_batch(
            [comment],
            video_title=context.get('video_title', '') if context else '',
            canal_name=context.get('canal_name', '') if context else '',
            batch_size=1
        )

        return batch_result[0] if batch_result else comment

    def get_daily_metrics(self) -> Dict:
        """
        Retorna métricas diárias de uso.

        Returns:
            Dicionário com métricas do dia
        """
        # Calcular médias
        avg_response_time = 0
        success_rate = 0

        if self.daily_metrics['total_requests'] > 0:
            avg_response_time = self.daily_metrics['total_time_ms'] // self.daily_metrics['total_requests']
            success_count = self.daily_metrics['total_requests'] - self.daily_metrics['total_errors']
            success_rate = (success_count / self.daily_metrics['total_requests']) * 100

        return {
            'total_analyzed': self.daily_metrics['total_analyzed'],
            'total_tokens_input': self.daily_metrics['total_tokens_input'],
            'total_tokens_output': self.daily_metrics['total_tokens_output'],
            'avg_response_time_ms': avg_response_time,
            'success_rate': round(success_rate, 2),
            'errors_count': self.daily_metrics['total_errors'],
            'estimated_cost_usd': round(self.daily_metrics['estimated_cost_usd'], 2),
            'high_confidence_count': self.daily_metrics['high_confidence_count'],
            'medium_confidence_count': self.daily_metrics['medium_confidence_count'],
            'low_confidence_count': self.daily_metrics['low_confidence_count']
        }

    def reset_daily_metrics(self):
        """Reseta as métricas diárias (chamar à meia-noite)."""
        self.daily_metrics = {
            'total_analyzed': 0,
            'total_tokens_input': 0,
            'total_tokens_output': 0,
            'total_requests': 0,
            'total_errors': 0,
            'total_time_ms': 0,
            'estimated_cost_usd': 0.0,
            'high_confidence_count': 0,
            'medium_confidence_count': 0,
            'low_confidence_count': 0
        }
        logger.info("Métricas diárias resetadas")


# Função auxiliar para teste rápido
async def test_analyzer():
    """Função de teste do analisador"""
    analyzer = GPTAnalyzer()

    # Comentários de exemplo
    test_comments = [
        {
            'comment_id': 'test1',
            'text': 'Cara, o áudio tá muito baixo nesse vídeo! Tive que colocar no máximo e ainda assim mal consegui ouvir.',
            'author_name': 'João Silva',
            'like_count': 45
        },
        {
            'comment_id': 'test2',
            'text': 'Melhor canal de terror do YouTube brasileiro! Continua com esse trabalho incrível!',
            'author_name': 'Maria Santos',
            'like_count': 23
        },
        {
            'comment_id': 'test3',
            'text': 'Quando vai sair a parte 2? Fiquei muito curioso!',
            'author_name': 'Pedro Costa',
            'like_count': 12
        }
    ]

    # Analisar
    results = await analyzer.analyze_batch(
        test_comments,
        video_title="A Casa Assombrada - Parte 1",
        canal_name="Canal Dark",
        batch_size=10
    )

    # Mostrar resultados
    for result in results:
        print("\n" + "="*50)
        print(f"Autor: {result['author_name']}")
        print(f"Texto: {result['comment_text_original']}")
        print(f"Sentimento: {result.get('sentiment_category')} (score: {result.get('sentiment_score')})")
        print(f"Categorias: {result.get('categories')}")
        print(f"Prioridade: {result.get('priority_score')}")
        print(f"Requer resposta: {result.get('requires_response')}")
        if result.get('suggested_response'):
            print(f"Resposta sugerida: {result['suggested_response']}")

    # Mostrar métricas
    print("\n" + "="*50)
    print("MÉTRICAS DO DIA:")
    metrics = analyzer.get_daily_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Teste local
    asyncio.run(test_analyzer())