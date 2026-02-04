# -*- coding: utf-8 -*-
"""
Modulo de Traducao Otimizado usando GPT-4 Mini
Data: 04/02/2026
Objetivo: Traduzir comentarios usando OpenAI GPT-4 Mini
Funciona para todas as linguas -> PT-BR
"""

import asyncio
import logging
import os
import json
import httpx
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carregar variaveis de ambiente
load_dotenv()


class OptimizedTranslator:
    """Tradutor otimizado usando GPT-4 Mini com cliente assincrono"""

    def __init__(self):
        """Inicializa cliente OpenAI assincrono"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY nao configurada")
            raise ValueError("OPENAI_API_KEY nao configurada")

        # Usar cliente assincrono com timeout configurado
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
            max_retries=3
        )
        self.model = "gpt-4o-mini"  # Modelo eficiente para traducao
        self.batch_size = 20  # Processar 20 textos por vez

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
            # Processar em sub-batches para otimizar tokens
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

                try:
                    # Fazer chamada assincrona para GPT-4 Mini
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=2000
                    )

                    # Extrair traducoes do response
                    content = response.choices[0].message.content.strip()

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
                            raise Exception(f"Formato inesperado da resposta GPT: {type(translations)}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao fazer parse do JSON de traducao: {e}")
                        logger.error(f"Conteudo recebido: {content[:500]}")
                        raise Exception(f"Erro ao parsear resposta do GPT: {e}")

                    logger.info(f"[TRADUTOR GPT] Traduzidos {len(sub_batch)} textos")

                    # Pequena pausa entre batches
                    if i + self.batch_size < len(texts):
                        await asyncio.sleep(1)

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

        Args:
            text: Texto para traduzir

        Returns:
            Texto traduzido
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
