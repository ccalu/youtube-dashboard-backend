"""
Roteirista de Shorts — gera título, descrição, script e estimativa de cenas.

Usa Claude CLI (plano Max) para gerar o script completo.
Output: JSON com titulo, descricao, script, estrutura, total_cenas.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um roteirista especialista em YouTube Shorts virais. Você estudou centenas de shorts com milhões de views e domina os padrões que prendem a atenção do espectador do primeiro ao último segundo. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicação.

=== SEU CÉREBRO DE ROTEIRISTA ===

## TIPOS DE HOOK (primeira frase do script)
O hook NUNCA resume o vídeo. Ele abre um LOOP DE CURIOSIDADE que só se resolve no final.

1. DILEMA IMPOSSÍVEL — Apresenta duas opções extremas e pergunta ao viewer.
   Ex: "Um avô chinês recebeu duas opções: trair as próprias netas ou pular pra morte num rio. O que você acha que ele fez?"

2. CLAIM CHOCANTE — Afirmação absurda que parece mentira.
   Ex: "Essa rainha obrigava homens a duelar até a morte antes de dormir com o vencedor."

3. SUPERLATIVO ÚNICO — Algo que foi o único/primeiro/último a acontecer.
   Ex: "Essa mulher foi a única freira a ter a cabeça espetada numa lança na Ponte de Londres."

4. DID YOU KNOW — Fato bizarro que ninguém conhece.
   Ex: "Você sabia que pessoas baixas não podiam ser presas na China antiga?"

5. PERGUNTA INTERATIVA — Envolve o viewer numa escolha.
   Ex: "Qual dessas mulheres você levaria pra um encontro?"

6. LISTICLE DIRETO — Apresenta o tema como lista com promessa de absurdo.
   Ex: "Três crianças que receberam poder demais cedo demais."

Escolha o tipo de hook que MELHOR se encaixa no tema. Varie entre os tipos.

## ESTRUTURAS NARRATIVAS (escolha UMA por script)

A) DILEMA → CONTEXTO → RETORNO
   Abre com escolha impossível. Explica como chegaram lá. Volta ao dilema sem resolver 100%.

B) ESCALADA DE CHOQUE
   Cada parágrafo é mais absurdo que o anterior. O viewer pensa "não tem como piorar" — e piora.

C) ASCENSÃO E QUEDA
   Pessoa comum ganha fama ou poder. Conflito com alguém maior. Destruição.

D) LISTICLE COM ESCALADA (2-3 itens)
   Cada item mais bizarro que o anterior. Cada item é uma mini-história com punchline própria.

## ESTRUTURA OBRIGATÓRIA DE 4 ATOS (todo script DEVE seguir)

1. HOOK (parágrafos 1-2): Abre uma PERGUNTA implícita ou cena impossível. NUNCA entrega o que aconteceu — cria curiosidade pura.
2. BUILD (parágrafos 3-9): Tensão CRESCENTE. Cada parágrafo aproxima da resposta sem entregar. O viewer sente que está chegando perto mas não sabe do quê.
3. CLIMAX (parágrafos 10-12): O momento "holy shit". A cena mais forte, mais chocante, mais absurda do vídeo inteiro. Tudo converge aqui.
4. PAYOFF (parágrafos 13-14): Fecha o LOOP com o hook. Reconecta com o início de forma INESPERADA. O viewer pensa "agora tudo faz sentido" ou "não acredito que acabou assim".

REGRA DE OURO: O PAYOFF deve reconectar com o HOOK. Se o hook abre uma pergunta, o payoff responde de forma surpreendente. Se o hook mostra uma cena, o payoff revela o que aconteceu depois de um jeito que ninguém esperava.

## RETENÇÃO E COPY
- O engajamento vem da HISTÓRIA, não de fórmulas. NUNCA use frases de transição genéricas ou templates prontos.
- A tensão deve vir NATURALMENTE do storytelling — cada frase existe porque a anterior criou necessidade dela.
- Se precisar de uma frase tipo "mas fica pior" pra manter atenção, o script está fraco. Reescreva.
- Tom conversacional e direto. Presente narrativo ("ele morre", não "ele morreu").
- Traduzir números em algo tangível ("o que um artesão ganhava em dez anos").
- Humor negro sutil — descrever horror de forma understated.
- Contraste dramático — justapor normalidade com absurdo.
- MENOS TEXTO, MAIS IMPACTO. Zero floreio. Cada palavra merece estar ali.

## FINALIZAÇÃO (últimas 1-2 frases)
NUNCA use CTA explícito ("se inscreva", "curta", "comenta"). O engajamento vem do conteúdo.
Use uma dessas duas formas:

1. OPEN LOOP — Não resolve completamente. Viewer comenta.
   Ex: "Eu te deixo adivinhar o que aconteceu depois."
   Ex: "Agora imagina o que fizeram com ele na manhã seguinte."

2. TWIST FINAL — Último fato é o mais absurdo do vídeo inteiro.
   Ex: "Ela só desfez o harém aos setenta e cinco anos. E casou com o membro mais jovem."
   Ex: "Ele fez um tribunal militar formal pro rato. E condenou o rato à morte."

## REGRA CRÍTICA DE NARRAÇÃO (TTS)
O script será narrado por Text-to-Speech. Portanto:
- TODOS os números escritos POR EXTENSO: "dois" NÃO "2", "mil quinhentos" NÃO "1500"
- Algarismos romanos SEMPRE por extenso: "Henrique oitavo" NÃO "Henrique VIII", "Luís décimo quarto" NÃO "Luís XIV"
- Esta regra é APENAS para o campo "script". No TÍTULO e DESCRIÇÃO pode usar números e romanos normalmente.
"""


MUSIC_CATEGORIES = {
    "Guerras e Civilizações": {
        "folder": "Musicas 02",
        "categories": ["battle", "cinematic", "documentary", "emotional", "military", "suspense", "tension"],
    },
    "Guerras e Civilizacoes": {
        "folder": "Musicas 02",
        "categories": ["battle", "cinematic", "documentary", "emotional", "military", "suspense", "tension"],
    },
    "Relatos de Guerra": {
        "folder": "Musicas 03",
        "categories": ["battle", "cinematic", "documentary", "emotional", "military", "suspense", "tension"],
    },
    "Frentes de Guerra": {
        "folder": "Musicas 03",
        "categories": ["battle", "cinematic", "documentary", "emotional", "military", "suspense", "tension"],
    },
    "Reis Perversos": {
        "folder": "Musicas 05",
        "categories": ["court", "documentary", "dramatic", "ecclesiastical", "emotional", "horror", "suspense", "tension"],
    },
    "Historias Sombrias": {
        "folder": "Musicas 05",
        "categories": ["court", "documentary", "dramatic", "ecclesiastical", "emotional", "horror", "suspense", "tension"],
    },
    "Culturas Macabras": {
        "folder": "Musicas 05",
        "categories": ["court", "documentary", "dramatic", "ecclesiastical", "emotional", "horror", "suspense", "tension"],
    },
    "Monetizados": {
        "folder": "Musicas 06",
        "categories": ["decay", "documentary", "dramatic", "emotional", "grandeur", "suspense", "tension"],
    },
}


CATEGORY_DESCRIPTIONS = {
    "battle": "combate, guerra ativa, conflito intenso",
    "cinematic": "epico, grandioso, momentos de revelacao",
    "documentary": "narrativo neutro, informativo, tom de documentario",
    "emotional": "perda, sacrificio, tragedia pessoal, morte",
    "military": "marcha, estrategia, operacoes militares",
    "suspense": "misterio, revelacao gradual, segredos",
    "tension": "medo, terror psicologico, dread, opressao",
    "court": "intriga palaciana, politica, conspiracao na corte",
    "dramatic": "climax, poder, queda dramatica, confronto",
    "ecclesiastical": "religioso, ritual, inquisicao, cerimonia",
    "horror": "macabro, ritual sinistro, tortura, sobrenatural",
    "decay": "abandono, ruina, degradacao, decadencia",
    "grandeur": "opulencia, riqueza, mansoes, poder economico",
}


def _get_music_categories(subnicho: str) -> str:
    """Retorna categorias de música com descrições pro subnicho."""
    info = MUSIC_CATEGORIES.get(subnicho)
    if not info:
        return "Categorias: tension, emotional, dramatic, suspense"
    lines = []
    for cat in info["categories"]:
        desc = CATEGORY_DESCRIPTIONS.get(cat, "")
        lines.append(f"  - {cat}: {desc}")
    return "Categorias de musica de fundo (exemplos de uso, nao se limite a eles — escolha pelo TOM GERAL do script):\n" + "\n".join(lines)


def write_script(topic: str, canal: str, subnicho: str, lingua: str, subnicho_desc: str = "", titulos_ref: str = "") -> dict:
    """
    Gera script completo para um YouTube Short.

    Args:
        topic: Tema do Short
        canal: Nome do canal
        subnicho: Nome do subnicho
        lingua: Língua do canal (ex: "Português", "Inglês")
        subnicho_desc: Descrição do subnicho (do SUBNICHOS.md)
        titulos_ref: Títulos de referência do canal

    Returns:
        Dict com titulo, descricao, script, estrutura, total_cenas
    """
    ref_block = ""
    if titulos_ref:
        ref_block = f"\nTítulos de referência do canal (use como inspiração de tom e estilo):\n{titulos_ref}\n"

    user_prompt = f"""Crie um script de YouTube Short completo.

Canal: {canal} | Subnicho: {subnicho} | Língua: {lingua} | Tema: {topic}

Contexto do subnicho: {subnicho_desc}
{ref_block}
REGRAS DE FORMATO:
- Script na língua "{lingua}". Título e descrição também em "{lingua}".
- OBRIGATORIO: entre 850 e 1100 caracteres no campo "script" (menos que 850 fica curto demais, mais que 1100 fica longo demais)
- OBRIGATÓRIO: 14 parágrafos = 14 cenas visuais (separe por \\n\\n)
- Título: max 60 caracteres, curiosidade extrema
- Descrição: 1-2 frases + 5 hashtags relevantes
- NUNCA editorialize, só mostre fatos

Aplique TUDO que você sabe sobre hooks, estrutura narrativa, técnicas de retenção, copy e finalização. Escolha o tipo de hook e a estrutura narrativa que melhor se encaixam no tema.

No campo "estrutura", indique qual você usou: "dilema", "escalada", "ascensao_queda" ou "listicle".

MÚSICA DE FUNDO: escolha a categoria que melhor combina com o tom do script.
{_get_music_categories(subnicho)}

Retorne SOMENTE:

[JSON_START]
{{
  "titulo": "título max 60 chars",
  "descricao": "descrição com #hashtags",
  "script": "texto narrado com 14 paragrafos separados por \\n\\n",
  "estrutura": "tipo_escolhido",
  "music_category": "categoria_escolhida",
  "total_cenas": 14
}}
[JSON_END]
"""

    logger.info(f"[scriptwriter] Gerando script: {topic} | {canal} | {lingua}")

    raw = call_claude_cli(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model="claude-opus-4-6",
        timeout=300,
    )

    # Extract JSON
    match = re.search(r'\[JSON_START\](.*?)\[JSON_END\]', raw, re.DOTALL)
    if match:
        result = json.loads(match.group(1).strip())
        logger.info(f"[scriptwriter] OK: {result.get('titulo', '?')}")
        return result

    # Fallback: try parsing the whole response as JSON
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.error(f"[scriptwriter] Failed to parse response: {raw[:200]}")
        raise RuntimeError("Scriptwriter: could not parse JSON from response")
