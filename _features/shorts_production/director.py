"""
Diretor de Cinema — gera prompts de imagem e animacao para cada cena.

Recebe o script do Roteirista e gera 14 cenas com prompt de imagem
e prompt de animacao (Kling 2.5) pensados JUNTOS como storyboard.

Output: Lista de 14 cenas com prompt_imagem + prompt_animacao.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Voce e um diretor de cinema profissional criando storyboards para YouTube Shorts. Voce pensa IMAGEM e ANIMACAO juntos desde o inicio — cada cena e planejada como um take cinematografico completo. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicacao."""


def generate_scenes(script: str, canal: str, subnicho: str, lingua: str, estilo_visual: str = "", total_cenas: int = 14) -> list:
    """
    Gera prompts de imagem e animacao para cada cena.

    Args:
        script: Script narrado completo
        canal: Nome do canal
        subnicho: Nome do subnicho
        lingua: Lingua do canal
        estilo_visual: Estilo visual do canal (do DIRETOR_DE_CINEMA.md)
        total_cenas: Numero de cenas (default 14)

    Returns:
        Lista de dicts com cena, prompt_imagem, prompt_animacao
    """
    user_prompt = f"""Crie {total_cenas} cenas visuais para este script de YouTube Short.

Canal: {canal} | Estilo: {estilo_visual}

Script:
{script}

=== COMO PENSAR CADA CENA ===

Voce e um diretor montando um STORYBOARD. Para cada cena, pense PRIMEIRO na acao/movimento que quer mostrar, DEPOIS construa a imagem que melhor serve como frame inicial dessa acao.

Exemplo de raciocinio correto:
- "Essa cena precisa mostrar o rei se levantando do trono com furia"
- Entao a IMAGEM mostra o rei sentado, mao no apoio, corpo inclinando pra frente
- E a ANIMACAO mostra ele se levantando, robes se movendo, mao batendo no apoio

Exemplo de raciocinio ERRADO:
- Gerar uma imagem bonita e depois inventar uma animacao qualquer pra ela
- Isso gera desconexao entre imagem e movimento

=== REGRAS IMAGEM (formato 9:16 vertical, 768x1344) ===
- Prompts em INGLES, 80-150 palavras
- OBRIGATORIO incluir "vertical 9:16 composition, no text, no watermark" no final
- Estrutura: estilo+plano, sujeito detalhado, ambiente, iluminacao, color grade
- VARIAR enquadramento/angulo/iluminacao entre TODAS as cenas — NUNCA repetir consecutivo
- Cada imagem deve ser interessante SOZINHA (se pausar o video, a imagem prende atencao)
- Variar TIPOS de cena: close-up, wide shot, detalhe de objeto, acao, ambiente, POV, grupo
- COMPLIANCE: sem violencia grafica explicita, sem nudez, sem gore

=== REGRAS ANIMACAO (Kling 2.5, clips de 5 segundos) ===
- Prompts em INGLES, 30-40 palavras
- NUNCA descrever o que ja esta na imagem — descrever APENAS o que MUDA e se MOVE
- Movimentos de CORPO e ACAO reais: andar, virar, pegar, soltar, levantar, empurrar, olhar
- Se a cena tem objeto/ambiente sem humano: animar O ELEMENTO PRINCIPAL (fogo, agua, objeto caindo, porta abrindo)
- Cada uma das {total_cenas} animacoes DEVE ser UNICA — nunca repetir o mesmo tipo de movimento/acao entre cenas
- Coerente com a imagem: so descrever movimentos que fazem sentido fisicamente com o que esta na imagem
- PROIBIDO: inventar elementos que nao estao na imagem, efeitos fake (fumaca do nada, explosoes aleatorias), quality boosters ("8K", "masterpiece")
- Dinamico e interessante, mas NAO exagerado ou irreal

=== COERENCIA VISUAL TOTAL ===

TODAS as cenas DEVEM pertencer ao MESMO universo visual:
- Mesmo periodo historico (se e Viking, TUDO e Viking — roupas, armas, cenarios, materiais)
- Mesmo estilo artistico (se comecou realista, TUDO realista. Se comecou pintura a oleo, TUDO pintura a oleo)
- Mesma paleta de cor geral (pode variar iluminacao mas a identidade visual e UMA SO)
- NUNCA misturar elementos de epocas diferentes (nada moderno em cena historica)
- NUNCA inserir objetos, roupas ou cenarios que nao existiriam naquele contexto
- Cada cena deve parecer que faz parte do MESMO filme/documentario
- Se o script fala de um povo/cultura especifica, TODOS os detalhes visuais devem ser fieis a essa cultura

=== VARIEDADE OBRIGATORIA ===

As {total_cenas} cenas DEVEM ter variedade em:
1. Enquadramento: misturar extreme close-up, close-up, medium shot, wide shot, POV, overhead
2. Tipo de cena: retrato, acao, objeto/detalhe, ambiente, grupo, simbolico
3. Animacao: cada cena com tipo DIFERENTE de movimento (nao fazer 3 cenas seguidas de "pessoa virando a cabeca")
4. Iluminacao: variar entre cenas (luz dramatica, natural, fogo, lua, amanhecer)

Cena 1 = HOOK VISUAL (a mais impactante, faz o viewer parar de scrollar).

Retorne SOMENTE:

[JSON_START]
{{
  "cenas": [
    {{"cena": 1, "prompt_imagem": "...", "prompt_animacao": "..."}},
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
