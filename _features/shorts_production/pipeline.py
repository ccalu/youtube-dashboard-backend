"""
Pipeline de produção de Shorts — orquestra Roteirista + Diretor.

Recebe tema, canal, subnicho e língua.
Retorna JSON completo pronto pro Freepik Spaces.
"""

import json
import os
import logging
from .scriptwriter import write_script
from .director import generate_scenes

logger = logging.getLogger(__name__)

# Estilos visuais por subnicho (essência do Lucca, adaptado pra 9:16)
ESTILOS_VISUAIS = {
    "Guerras e Civilizações": "Cinematic epic hyperrealistic style. Ancient battles, empires, sieges. Warm golden tones for glory, cold desaturated for defeat. Vertical 9:16 composition.",
    "Frentes de Guerra": "Authentic WWII documentary photography style. As if captured by a 1940s military field camera. Black and white, sepia, or muted colorized options. Vertical 9:16.",
    "Relatos de Guerra": "Authentic WWII documentary photography style. Individual stories, equipment details, dramatic moments. Period film grain. Vertical 9:16.",
    "Reis Perversos": "Renaissance oil painting with dramatic Baroque lighting. Inspired by Caravaggio, Rembrandt. Candlelight, chiaroscuro, rich textures. Vertical 9:16.",
    "Historias Sombrias": "Renaissance oil painting with dramatic Baroque lighting. Dark revelations, disturbing historical truths. Tenebrism, sfumato. Vertical 9:16.",
    "Culturas Macabras": "Renaissance oil painting with dramatic Baroque lighting. Ancient rituals, macabre customs. Candlelight, deep shadows. Vertical 9:16.",
    "Monetizados": "",  # Usar estilo do canal específico
}

# Descrições dos subnichos (do SUBNICHOS.md)
SUBNICHO_DESCS = {
    "Guerras e Civilizações": "Grandes batalhas da antiguidade e medievais narradas como épicos cinematográficos. Roma, Grécia, Pérsia, Mongóis, Vikings, Cruzadas. Exclusivamente antiguidade e medieval, nada moderno.",
    "Frentes de Guerra": "Momentos épicos, batalhas decisivas e figuras-chave da Segunda Guerra Mundial. Foco em momentos de virada, inovações, reações de oficiais. Narrativa cinematográfica ampla.",
    "Relatos de Guerra": "Histórias individuais, equipamentos, táticas e momentos decisivos da WWII. Soldados específicos, armas que mudaram batalhas, operações secretas. Tom dramático-militar.",
    "Reis Perversos": "Histórias chocantes de reis, imperadores, tiranos. Crueldade, perversão, rituais, torturas, traições, segredos de haréns. Tudo baseado em fatos históricos reais.",
    "Historias Sombrias": "O lado oculto de figuras históricas famosas. O que aconteceu antes da morte, segredos que a história omitiu, práticas bizarras de outras épocas.",
    "Culturas Macabras": "Práticas, rituais e costumes macabros de civilizações antigas e medievais. Tom antropológico-chocante, sem julgamento moral.",
    "Monetizados": "Canais monetizados com temas variados. Usar contexto do canal específico.",
}


def run_production(topic: str, canal: str, canal_id: int, subnicho: str, lingua: str) -> dict:
    """
    Executa o pipeline completo de produção.

    Returns:
        Dict pronto pro Supabase com titulo, descricao, script, cenas, etc.
    """
    logger.info(f"[pipeline] Iniciando: {topic} | {canal} | {subnicho} | {lingua}")

    # 1. Pegar contexto do subnicho
    subnicho_desc = SUBNICHO_DESCS.get(subnicho, "")
    estilo_visual = ESTILOS_VISUAIS.get(subnicho, "")

    # Para Monetizados, usar contexto específico do canal
    if subnicho == "Monetizados":
        if "Mansões" in canal or "Mansoes" in canal:
            subnicho_desc = "Mansões, casas, palácios e propriedades históricas com foco no lado sombrio. Tragédias, abandonos, quedas de dinastias, contraste luxo/ruína."
            estilo_visual = "Cinematic hyperrealistic documentary photography. Era-adaptive: daguerreotype, silver gelatin, early 20th century, modern. Vertical 9:16."
        elif "WWII" in canal or "Guerre" in canal or "Erzähl" in canal:
            subnicho_desc = SUBNICHO_DESCS.get("Relatos de Guerra", "")
            estilo_visual = ESTILOS_VISUAIS.get("Relatos de Guerra", "")
        elif "Королей" in canal or "Шёпот" in canal:
            subnicho_desc = SUBNICHO_DESCS.get("Reis Perversos", "")
            estilo_visual = ESTILOS_VISUAIS.get("Reis Perversos", "")

    # 2. Roteirista gera script (com validação)
    script_data = write_script(
        topic=topic,
        canal=canal,
        subnicho=subnicho,
        lingua=lingua,
        subnicho_desc=subnicho_desc,
    )

    # Validar output do roteirista
    for key in ("titulo", "descricao", "script"):
        if not script_data.get(key):
            raise RuntimeError(f"Roteirista não gerou '{key}'")

    # 3. Diretor gera cenas (imagem + animação juntos)
    cenas = generate_scenes(
        script=script_data.get("script", ""),
        canal=canal,
        subnicho=subnicho,
        lingua=lingua,
        estilo_visual=estilo_visual,
        total_cenas=script_data.get("total_cenas", 16),
    )

    # Validar output do diretor
    if len(cenas) != 16:
        raise RuntimeError(f"Diretor gerou {len(cenas)} cenas (devem ser exatamente 16)")
    for i, cena in enumerate(cenas):
        if not cena.get("prompt_imagem") or not cena.get("prompt_animacao"):
            raise RuntimeError(f"Cena {i+1} sem prompt de imagem ou animação")

    # 4. Montar JSON de produção
    producao_json = {
        "titulo": script_data.get("titulo", ""),
        "descricao": script_data.get("descricao", ""),
        "script": script_data.get("script", ""),
        "canal": canal,
        "subnicho": subnicho,
        "lingua": lingua,
        "cenas": cenas,
    }

    # 5. Criar pasta local e salvar arquivos
    titulo_curto = " ".join(producao_json["titulo"].split()[:3])
    shorts_root = os.getenv("SHORTS_LOCAL_PATH", "C:\\Users\\PC\\Downloads\\SHORTS")
    pasta_base = os.path.join(shorts_root, subnicho, f"({lingua[:2].upper()}) {canal}", titulo_curto)
    os.makedirs(os.path.join(pasta_base, "img"), exist_ok=True)
    os.makedirs(os.path.join(pasta_base, "clips"), exist_ok=True)

    # Salvar JSON
    with open(os.path.join(pasta_base, "producao.json"), "w", encoding="utf-8") as f:
        json.dump(producao_json, f, ensure_ascii=False, indent=2)

    # Salvar copy.txt
    with open(os.path.join(pasta_base, "copy.txt"), "w", encoding="utf-8") as f:
        f.write(f"TÍTULO:\n{producao_json['titulo']}\n\n")
        f.write(f"DESCRIÇÃO:\n{producao_json['descricao']}\n\n")
        f.write(f"SCRIPT:\n{producao_json['script']}\n")

    logger.info(f"[pipeline] Produção salva em: {pasta_base}")

    return {
        "canal_id": canal_id,
        "canal": canal,
        "subnicho": subnicho,
        "lingua": lingua,
        "titulo": producao_json["titulo"],
        "estrutura": script_data.get("estrutura", ""),
        "producao_json": producao_json,
        "drive_link": pasta_base,
    }
