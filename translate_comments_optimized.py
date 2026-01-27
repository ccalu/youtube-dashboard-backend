"""
Módulo de Tradução Otimizado usando GPT-4 Mini
Data: 27/01/2026
Objetivo: Traduzir comentários usando OpenAI GPT-4 Mini
Funciona para todas as línguas -> PT-BR
"""

import asyncio
import logging
import os
import json
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class OptimizedTranslator:
    """Tradutor otimizado usando GPT-4 Mini"""

    def __init__(self):
        """Inicializa cliente OpenAI"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY não configurada no .env")
            raise ValueError("OPENAI_API_KEY não configurada")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Modelo eficiente para tradução
        self.batch_size = 20  # Processar 20 textos por vez

    async def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Traduz batch de textos para português brasileiro usando GPT-4 Mini

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

                # Criar prompt para tradução em batch
                comments_json = json.dumps(
                    [{"id": idx, "text": text} for idx, text in enumerate(sub_batch)],
                    ensure_ascii=False
                )

                system_prompt = """Você é um tradutor especializado em adaptar textos para português brasileiro.

TAREFA: Traduza os comentários para PT-BR mantendo o tom e contexto original.

DIRETRIZES:
1. Se já estiver em português, retorne como está
2. Adapte gírias e expressões culturais quando possível
3. Mantenha emojis e formatação
4. Use linguagem natural brasileira (não tradução literal)
5. Retorne APENAS um JSON array com os textos traduzidos na mesma ordem

FORMATO DE RESPOSTA:
["texto traduzido 1", "texto traduzido 2", ...]"""

                user_prompt = f"Traduza estes comentários para PT-BR:\n{comments_json}"

                try:
                    # Fazer chamada para GPT-4 Mini
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3,  # Baixa temperatura para tradução consistente
                        max_tokens=2000
                    )

                    # Extrair traduções do response
                    content = response.choices[0].message.content.strip()

                    # Tentar fazer parse do JSON
                    try:
                        # Limpar possíveis marcadores de código
                        if content.startswith("```"):
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]

                        translations = json.loads(content)

                        if isinstance(translations, list):
                            translated.extend(translations)
                        else:
                            # Fallback se não for lista
                            logger.warning("Resposta não é uma lista, usando textos originais")
                            translated.extend(sub_batch)

                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao fazer parse do JSON de tradução: {e}")
                        # Em caso de erro, usar textos originais
                        translated.extend(sub_batch)

                    # Log de progresso
                    logger.info(f"[TRADUTOR GPT] Traduzidos {len(sub_batch)} textos")

                    # Pequena pausa entre batches para não sobrecarregar API
                    if i + self.batch_size < len(texts):
                        await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Erro na chamada GPT-4 Mini: {e}")
                    # Em caso de erro, adicionar textos originais
                    translated.extend(sub_batch)

            logger.info(f"[TRADUTOR GPT] Total traduzido: {len(translated)} textos")
            return translated

        except Exception as e:
            logger.error(f"Erro crítico no tradutor: {e}")
            # Retornar textos originais em caso de erro crítico
            return texts

    async def translate_single(self, text: str) -> str:
        """
        Traduz um único texto para PT-BR

        Args:
            text: Texto para traduzir

        Returns:
            Texto traduzido
        """
        if not text or text.strip() == "":
            return text

        result = await self.translate_batch([text])
        return result[0] if result else text


# Teste rápido
async def test_translator():
    """Testa o tradutor com alguns exemplos"""
    translator = OptimizedTranslator()

    test_texts = [
        "This is amazing! Keep up the great work!",
        "C'est incroyable, j'adore cette vidéo!",
        "これは素晴らしいです！",
        "Este vídeo já está em português",
        "¡Qué miedo! Me encantó el video"
    ]

    print("\n" + "="*60)
    print("TESTE DO TRADUTOR GPT-4 MINI")
    print("="*60)

    translations = await translator.translate_batch(test_texts)

    for original, translated in zip(test_texts, translations):
        print(f"\nOriginal: {original}")
        print(f"Traduzido: {translated}")

    print("="*60)


if __name__ == "__main__":
    # Executar teste se rodar diretamente
    asyncio.run(test_translator())