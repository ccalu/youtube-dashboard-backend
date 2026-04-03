"""
Diretor de Cinema — gera prompts de imagem e animação para cada cena.

Recebe o script do Roteirista e gera 12 cenas com prompt de imagem (NanoBanana 2)
e prompt de animação (MiniMax Hailuo 2.3 Fast) pensados JUNTOS.

Output: Lista de 12 cenas com prompt_imagem + prompt_animacao.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um diretor de cinema para YouTube Shorts. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicação."""


def generate_scenes(script: str, canal: str, subnicho: str, lingua: str, estilo_visual: str = "", total_cenas: int = 14) -> list:
    """
    Gera prompts de imagem e animação para cada cena.

    Args:
        script: Script narrado completo
        canal: Nome do canal
        subnicho: Nome do subnicho
        lingua: Língua do canal
        estilo_visual: Estilo visual do canal (do DIRETOR_DE_CINEMA.md)
        total_cenas: Número de cenas (default 12)

    Returns:
        Lista de dicts com cena, prompt_imagem, prompt_animacao
    """
    user_prompt = f"""Crie {total_cenas} cenas visuais para este script de YouTube Short.

Canal: {canal} | Estilo: {estilo_visual}

Script:
{script}

REGRAS IMAGEM (NanoBanana 2, formato 9:16 vertical, 768x1344):
- Prompts em INGLÊS, 80-150 palavras
- OBRIGATÓRIO incluir "9:16 vertical format" ou "vertical portrait format 9:16" no prompt
- Estrutura: estilo+plano, sujeito detalhado, ambiente, iluminação, color grade, "9:16 vertical portrait composition, no text, no watermark"
- VARIAR ângulo/plano/iluminação entre cenas (nunca repetir consecutivo)
- Cada imagem interessante SOZINHA
- COMPLIANCE: sem violência gráfica explícita, sem nudez, sem gore. Usar eufemismos e atmosfera em vez de violência direta

REGRAS ANIMAÇÃO (MiniMax Hailuo 2.3, 6s):
- Prompts em INGLÊS, 30-60 palavras
- NUNCA descrever a imagem, SÓ movimento
- Estrutura: câmera movement → subject movement → atmospheric → mood
- PROIBIDO: "8K", "masterpiece", quality boosters
- Frases narrativas fluidas, verbos presente contínuo

Cena 1 = HOOK VISUAL (mais impactante). Pensar imagem+animação JUNTOS.

Retorne SOMENTE:

[JSON_START]
{{
  "cenas": [
    {{"cena": 1, "prompt_imagem": "Cinematic...", "prompt_animacao": "Slow..."}},
    ...exatamente {total_cenas} cenas
  ]
}}
[JSON_END]
"""

    logger.info(f"[director] Gerando {total_cenas} cenas para: {canal}")

    raw = call_claude_cli(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model="claude-sonnet-4-6",
        timeout=300,
    )

    # Extract JSON
    match = re.search(r'\[JSON_START\](.*?)\[JSON_END\]', raw, re.DOTALL)
    if match:
        result = json.loads(match.group(1).strip())
        cenas = result.get('cenas', [])
        logger.info(f"[director] OK: {len(cenas)} cenas geradas")
        return cenas

    try:
        result = json.loads(raw.strip())
        return result.get('cenas', [])
    except json.JSONDecodeError:
        logger.error(f"[director] Failed to parse response: {raw[:200]}")
        raise RuntimeError("Director: could not parse JSON from response")
