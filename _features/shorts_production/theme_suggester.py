"""
Sugestor de Temas — sugere 5 temas para YouTube Shorts.

Usa GPT-4 Mini via API OpenAI para respostas rápidas (~3-5s).
Contexto: subnicho, títulos de referência, adaptação cultural por língua.
"""

import json
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None

def _get_client():
    global _client
    if _client is None:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'), override=True)
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY não encontrada no .env")
        _client = OpenAI(api_key=key)
    return _client

# Descrições dos subnichos (resumidas do SUBNICHOS.md)
SUBNICHO_CONTEXT = {
    "Guerras e Civilizações": {
        "desc": "Grandes batalhas da antiguidade e medievais. Roma, Grécia, Pérsia, Mongóis, Vikings, Cruzadas. Exclusivamente antiguidade e medieval.",
        "titulos_ref": [
            "Como 50 Mil Soldados CONGELARAM Vivos Atravessando os Alpes",
            "A Mentira Sobre os 300 de Esparta Que Você Sempre Acreditou",
            "Como um Rei LEPROSO de 16 Anos Destruiu o Exército de Saladino",
            "How 700 Knights Held Off 40,000 Ottomans for 4 Months",
            "How Slave Soldiers CRUSHED the Mongol Horde",
        ],
        "estruturas": "E5, E6, E7, E8, E9, E11, E12, E18, E20, E22",
    },
    "Frentes de Guerra": {
        "desc": "Momentos épicos e batalhas decisivas da WWII. Momentos de virada, inovações, reações de oficiais, impacto humano.",
        "titulos_ref": [
            "800 P-51 Mustangs Sobre Berlim — O Momento em que o General Soube que Perdeu",
            "O Truque Estúpido de Pintar Olhos Falsos que Fez Pilotos Errarem 80%",
            "Female German POWs Couldn't Believe the Aroma of Bacon",
            "Why 900 Luftwaffe Fighters Disappeared in 180 Minutes",
        ],
        "estruturas": "E4, E5, E6, E11, E16, E17, E21, E22, E27",
    },
    "Relatos de Guerra": {
        "desc": "Histórias individuais, equipamentos, táticas e momentos decisivos da WWII. Soldados, armas, operações secretas.",
        "titulos_ref": [
            "O Shinano Era o Maior Porta-Aviões do Mundo — Afundou 17 Horas Após Zarpar",
            "Comandante de U-Boat Avisou Que Comboio Estava Desprotegido — Até 7 Contratorpedeiros Aparecerem",
            "US Troops Ignored Australian SAS Warning — Until 12 Marines Died",
        ],
        "estruturas": "E4, E5, E6, E11, E16, E17, E21, E22, E27",
    },
    "Reis Perversos": {
        "desc": "Histórias chocantes de reis, tiranos. Crueldade, perversão, rituais, torturas, traições. Fatos históricos reais.",
        "titulos_ref": [
            "O Que Acontecia de Verdade nos Haréns do Império Otomano",
            "What Was Found Inside the Coffins of Henry VIII's 6 Wives",
            "Caligula's Darkest Night: The Ceremony That Made Senators Look Away",
            "Die Schrecklichsten Dinge, die Tiberius Jungen-Sklaven auf Capri Antat",
        ],
        "estruturas": "E4, E5, E15, E20, E21, E23, E24, E25",
    },
    "Historias Sombrias": {
        "desc": "O lado oculto de figuras históricas famosas. O que a história oficial omitiu, práticas bizarras de outras épocas.",
        "titulos_ref": [
            "Os Últimos Dias de Cleópatra Foram Piores do Que Você Pode Imaginar",
            "Ce Qu'ils Ont Fait à Marie-Antoinette Avant la Guillotine",
            "Die Königin, Die Lebend Verfaulte",
        ],
        "estruturas": "E4, E5, E15, E20, E21, E23, E24, E25",
    },
    "Culturas Macabras": {
        "desc": "Práticas e rituais macabros de civilizações antigas e medievais. Tom antropológico-chocante.",
        "titulos_ref": [
            "A Execução de Ana Bolena Foi Muito Pior do Que Você Imagina",
            "Ce Que les Vikings Faisaient aux Épouses des Ennemis Vaincus",
            "몽골군이 바그다드 황실에 한 짓은 죽음보다 끔찍했다",
        ],
        "estruturas": "E4, E5, E15, E20, E21, E23, E24, E25",
    },
    "Monetizados": {
        "desc": "Canais monetizados com temas variados. Mansões, palácios, propriedades históricas com foco sombrio.",
        "titulos_ref": [
            "A História TRÁGICA da MAIOR Propriedade Cafeeira do Brasil",
            "Por Que Eike Batista Deixou Sua Mansão de 100 Milhões Apodrecer",
        ],
        "estruturas": "E4, E11, E12, E15, E16, E20, E23, E25",
    },
}

SYSTEM_PROMPT = """Você é um especialista em títulos virais para YouTube Shorts de história e documentário.

Regras dos títulos:
- Fazer a pessoa PARAR de scrollar e CLICAR imediatamente
- Criar gap de informação irresistível
- Usar números concretos quando possível (datas, quantidades)
- Nunca entregar a resposta no título
- Máximo 60 caracteres quando possível
- Linguagem simples e direta
- O título deve funcionar culturalmente para o público-alvo
- Cada tema deve ter potencial visual forte

Retorne SOMENTE um JSON array válido, sem markdown, sem explicação:
[
  {"titulo": "Título 1", "estrutura": "E20"},
  {"titulo": "Título 2", "estrutura": "E11"},
  {"titulo": "Título 3", "estrutura": "E6"},
  {"titulo": "Título 4", "estrutura": "E23"},
  {"titulo": "Título 5", "estrutura": "E12"}
]"""


def suggest_themes(canal: str, subnicho: str, lingua: str, tema_livre: str = "") -> list:
    """
    Sugere 5 temas para YouTube Shorts via GPT-4 Mini.

    Args:
        canal: Nome do canal (vazio se avulso)
        subnicho: Nome do subnicho (vazio se avulso)
        lingua: Língua do canal
        tema_livre: Tema livre pra sugestões avulsas

    Returns:
        Lista de dicts com titulo e estrutura.
    """
    if not canal or canal == "Avulso":
        # Modo avulso — precisa de tema base, foco TOTAL em viralização
        if not tema_livre:
            return []  # Avulso sem tema = nada pra sugerir

        user_prompt = f"""Tema base: {tema_livre}
Língua: {lingua}

Este é um Short AVULSO (sem canal específico). O ÚNICO objetivo é VIRALIZAR.
Sugira 5 variações desse tema pensando no MÁXIMO potencial de viralização.
Pense em ângulos que geram choque, curiosidade extrema, debate, compartilhamento.
Títulos que fazem a pessoa PRECISAR assistir e COMPARTILHAR com alguém.
Títulos na língua "{lingua}" — extremamente chamativos, CTR máximo.
OBRIGATORIO: Se a lingua NAO for Portugues, SEMPRE inclua traducao em portugues entre parenteses. Ex: '제목 한국어 (Titulo em portugues)'. Sem excecao."""
    else:
        ctx = SUBNICHO_CONTEXT.get(subnicho, SUBNICHO_CONTEXT.get("Monetizados", {}))
        titulos = "\n".join("- " + t for t in ctx.get("titulos_ref", []))

        if tema_livre:
            tema_instrucao = f'O produtor quer sugestões sobre o tema "{tema_livre}". Use como norte pra gerar variações dentro do subnicho.'
        else:
            tema_instrucao = "Sugira 5 temas variados dentro do subnicho."

        user_prompt = f"""Subnicho: {subnicho}
Canal: {canal}
Língua: {lingua}

Descrição: {ctx.get('desc', '')}

Títulos de referência (tom e estilo):
{titulos}

Estruturas disponíveis: {ctx.get('estruturas', '')}

{tema_instrucao}
Títulos na língua "{lingua}" — chamativos, CTR alto, fazem a pessoa clicar.
O título deve funcionar culturalmente para o público "{lingua}".
OBRIGATORIO: Se a lingua NAO for Portugues, SEMPRE inclua traducao em portugues entre parenteses. Ex: '제목 한국어 (Titulo em portugues)'. Sem excecao."""

    logger.info(f"[theme_suggester] GPT-4 Mini: {canal or tema_livre} ({lingua})")

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Limpar markdown se vier
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
        logger.info(f"[theme_suggester] OK: {len(result)} temas via GPT-4 Mini")
        return result
    except json.JSONDecodeError:
        logger.error(f"[theme_suggester] Failed to parse GPT response: {raw[:200]}")
        return []
