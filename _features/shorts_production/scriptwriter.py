"""
Roteirista de Shorts — gera titulo, descricao, script e estimativa de cenas.

Usa Claude CLI (plano Max) para gerar o script completo.
Output: JSON com titulo, descricao, script, estrutura, total_cenas, music_category.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Voce e um roteirista profissional de YouTube Shorts virais de historia. Voce entende POR QUE as coisas funcionam e aplica de forma criativa. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicacao."""


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
    """Retorna categorias de musica com descricoes pro subnicho."""
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
        lingua: Lingua do canal (ex: "Portugues", "Ingles")
        subnicho_desc: Descricao do subnicho (do SUBNICHOS.md)
        titulos_ref: Titulos de referencia do canal

    Returns:
        Dict com titulo, descricao, script, estrutura, total_cenas, music_category
    """
    ref_block = ""
    if titulos_ref:
        ref_block = f"\nTitulos de referencia do canal (use como inspiracao de tom e estilo):\n{titulos_ref}\n"

    user_prompt = f"""Crie um script de YouTube Short completo.

Canal: {canal} | Subnicho: {subnicho} | Lingua: {lingua} | Tema: {topic}

Contexto do subnicho: {subnicho_desc}
{ref_block}

=== FILOSOFIA ===

Um short viral e uma EXPERIENCIA de 60 segundos. Cada frase cria uma IMAGEM na cabeca do viewer.
"Ele era poderoso" = nada. "Ele decidia quem vivia e quem morria antes do cafe da manha" = cena.
Tom: conversacional e direto, como se estivesse contando a historia pra um amigo. NAO e texto academico nem formal demais — e narrado, falado, humano. Use linguagem do dia a dia sem ser vulgar.

GANCHO (frases 1-2): abre LOOP que so fecha no final. Escolha o tipo que MELHOR serve o angulo do tema (cena impossivel, promessa de choque, pergunta com gap, segredo revelado, contraste extremo). O gancho DEVE ser congruente com a energia do tema — se e brutalidade, promete algo perturbador, nao uma curiosidade famosa.

CORPO: cada frase EMPURRA a narrativa. Se tirar e nada muda, deletar. Contexto carrega tensao junto ("Subiu ao trono com dezessete anos. Ninguem imaginava que em tres anos Roma estaria em chamas."). Ritmo variado: curta (impacto), longa (construcao), curta (virada). Tensao ESCALA.

CLIMAX: UM MOMENTO especifico, nao resumo. Mostre a cena.

FECHAMENTO: fecha o loop do gancho. Variar: loop fechado, twist, reflexao, ou CTA natural (as vezes).

COMPLIANCE YOUTUBE (obrigatorio):
- NUNCA descrever violencia grafica contra criancas ou menores
- NUNCA conteudo sexual ou nudez explicita
- NUNCA discurso de odio, racismo ou discriminacao
- Usar eufemismos e atmosfera em vez de descricoes graficas explicitas

TTS: numeros por extenso no script. Anos COMPLETOS ("mil novecentos e quarenta e dois" NAO "quarenta e dois"). Titulo e descricao podem usar numeros normais.

FORMATO:
- Script na lingua "{lingua}". Titulo e descricao tambem em "{lingua}".
- OBRIGATORIO: entre 800 e 900 caracteres no campo "script" (para Coreano e Japones: entre 300 e 400 caracteres — essas linguas sao mais densas e geram narracao mais longa)
- OBRIGATORIO: 14 paragrafos separados por \\n\\n (cada paragrafo = 1 cena visual de ~5s)
- Titulo: max 60 caracteres, curiosidade extrema
- Descricao: 1-2 frases + 5 hashtags estrategicas (3 em ingles + 2 no idioma do canal). Hashtags devem ter ALCANCE AMPLO mas relevantes ao tema — nao nichadas demais (ex: #mummification e muito especifico, #history e melhor). Mix ideal: hashtags que milhoes de pessoas buscam MAS que se conectam com o conteudo. NUNCA usar #viral #fyp #trending.
- O video final tera ~60 segundos — cada palavra conta

Aplique toda sua filosofia de roteiro: gancho que abre loop, cada frase empurra a narrativa, tensao escalando, climax como MOMENTO especifico, fechamento que completa o ciclo. Crie algo que o viewer NAO CONSEGUE parar de assistir.

MUSICA DE FUNDO: escolha a categoria que melhor combina com o tom do script.
{_get_music_categories(subnicho)}

Retorne SOMENTE:

[JSON_START]
{{
  "titulo": "titulo max 60 chars",
  "descricao": "descricao com #hashtags",
  "script": "texto narrado com 14 paragrafos separados por \\n\\n",
  "estrutura": "tipo_de_gancho_usado",
  "music_category": "categoria_escolhida",
  "total_cenas": 14
}}
[JSON_END]
"""

    logger.info(f"[scriptwriter] Gerando script: {topic} | {canal} | {lingua}")

    # Retry ate 3x se nao retornar JSON valido
    for attempt in range(3):
        try:
            raw = call_claude_cli(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model="claude-opus-4-6",
                timeout=360,
            )
        except Exception as e:
            if attempt < 2:
                logger.warning(f"[scriptwriter] Tentativa {attempt+1} falhou: {str(e)[:100]}. Retentando...")
                continue
            raise

        # Extract JSON entre markers
        match = re.search(r'\[JSON_START\](.*?)\[JSON_END\]', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                try:
                    logger.info(f"[scriptwriter] OK: {result.get('titulo', '?')}")
                except UnicodeEncodeError:
                    logger.info(f"[scriptwriter] OK: {result.get('titulo', '?').encode('ascii','replace').decode()}")
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: tentar extrair JSON com { } do raw
        json_match = re.search(r'\{[^{}]*"titulo"[^{}]*"script"[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{.*"titulo".*"script".*\}', raw, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                try:
                    logger.info(f"[scriptwriter] OK (fallback): {result.get('titulo', '?')}")
                except UnicodeEncodeError:
                    logger.info(f"[scriptwriter] OK (fallback)")
                return result
            except json.JSONDecodeError:
                pass

        # Fallback: parse raw inteiro
        try:
            result = json.loads(raw.strip())
            return result
        except json.JSONDecodeError:
            pass

        if attempt < 2:
            logger.warning(f"[scriptwriter] Tentativa {attempt+1}: JSON nao encontrado. Retentando...")
        else:
            try:
                logger.error(f"[scriptwriter] Falhou 3x. Resposta: {raw[:200]}")
            except UnicodeEncodeError:
                logger.error(f"[scriptwriter] Falhou 3x.")
            raise RuntimeError("Scriptwriter: nao conseguiu gerar JSON valido apos 3 tentativas")
