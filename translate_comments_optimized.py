# -*- coding: utf-8 -*-
"""
Modulo de Traducao Otimizado usando GPT-4 Mini
Data: 04/02/2026
Objetivo: Traduzir comentarios usando OpenAI GPT-4 Mini via httpx
Funciona para todas as linguas -> PT-BR
"""

import asyncio
import logging
import os
import json
import httpx
from typing import List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carregar variaveis de ambiente
load_dotenv()


class OptimizedTranslator:
    """Tradutor otimizado usando GPT-4 Mini via httpx direto"""

    def __init__(self):
        """Inicializa tradutor"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY nao configurada")
            raise ValueError("OPENAI_API_KEY nao configurada")

        self.model = "gpt-4o-mini"
        self.batch_size = 20
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Traduz batch de textos para portugues brasileiro usando GPT-4 Mini

        Args:
            texts: Lista de textos para traduzir

        Returns:
            Lista de textos traduzidos para PT-BR
        """
        if not texts:
            return []

        translated = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Processar em sub-batches
                for i in range(0, len(texts), self.batch_size):
                    sub_batch = texts[i:i + self.batch_size]

                    # Criar prompt para traducao em batch
                    comments_json = json.dumps(
                        [{"id": idx, "text": text} for idx, text in enumerate(sub_batch)],
                        ensure_ascii=False
                    )

                    system_prompt = """Voce e um tradutor especializado em adaptar textos para portugues brasileiro.

TAREFA: Traduza os comentarios para PT-BR mantendo o tom e contexto original.

DIRETRIZES:
1. Se ja estiver em portugues, retorne como esta
2. Adapte girias e expressoes culturais quando possivel
3. Mantenha emojis e formatacao
4. Use linguagem natural brasileira (nao traducao literal)
5. Retorne APENAS um JSON array com os textos traduzidos na mesma ordem

FORMATO DE RESPOSTA:
["texto traduzido 1", "texto traduzido 2", ...]"""

                    user_prompt = f"Traduza estes comentarios para PT-BR:\n{comments_json}"

                    # Payload da requisicao
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }

                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }

                    try:
                        # Fazer chamada HTTP direta
                        response = await client.post(
                            self.api_url,
                            json=payload,
                            headers=headers
                        )

                        if response.status_code != 200:
                            error_text = response.text
                            logger.error(f"Erro API OpenAI: {response.status_code} - {error_text}")
                            raise Exception(f"API OpenAI retornou {response.status_code}: {error_text}")

                        data = response.json()
                        content = data["choices"][0]["message"]["content"].strip()

                        # Tentar fazer parse do JSON
                        try:
                            # Limpar possiveis marcadores de codigo
                            if content.startswith("```"):
                                content = content.split("```")[1]
                                if content.startswith("json"):
                                    content = content[4:]

                            translations = json.loads(content)

                            if isinstance(translations, list):
                                translated.extend(translations)
                            else:
                                logger.error(f"Resposta nao e uma lista: {type(translations)}")
                                raise Exception(f"Formato inesperado: {type(translations)}")

                        except json.JSONDecodeError as e:
                            logger.error(f"Erro ao fazer parse do JSON: {e}")
                            logger.error(f"Conteudo recebido: {content[:500]}")
                            raise Exception(f"Erro ao parsear resposta: {e}")

                        logger.info(f"[TRADUTOR GPT] Traduzidos {len(sub_batch)} textos")

                        # Pequena pausa entre batches
                        if i + self.batch_size < len(texts):
                            await asyncio.sleep(1)

                    except httpx.TimeoutException as e:
                        logger.error(f"Timeout na chamada OpenAI: {e}")
                        raise
                    except Exception as e:
                        logger.error(f"Erro na chamada GPT-4 Mini: {e}")
                        raise

            logger.info(f"[TRADUTOR GPT] Total traduzido: {len(translated)} textos")
            return translated

        except Exception as e:
            logger.error(f"Erro critico no tradutor: {e}")
            raise

    async def translate_single(self, text: str) -> str:
        """
        Traduz um unico texto para PT-BR
        """
        if not text or text.strip() == "":
            return text

        result = await self.translate_batch([text])
        return result[0] if result else text


# Teste rapido
async def test_translator():
    """Testa o tradutor com alguns exemplos"""
    translator = OptimizedTranslator()

    test_texts = [
        "This is amazing! Keep up the great work!",
        "C'est incroyable, j'adore cette video!",
        "Este video ja esta em portugues",
    ]

    print("\n" + "=" * 60)
    print("TESTE DO TRADUTOR GPT-4 MINI")
    print("=" * 60)

    translations = await translator.translate_batch(test_texts)

    for original, trans in zip(test_texts, translations):
        print(f"\nOriginal: {original}")
        print(f"Traduzido: {trans}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_translator())
