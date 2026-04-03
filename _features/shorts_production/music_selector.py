"""
Seletor de música de fundo — escolhe track que combina com o script.

Usa a music_category do scriptwriter + controle de repetição por canal via Supabase.
Cicla pelas tracks: quando esgota todas, volta pro início.
"""

import os
import glob
import random
import logging

logger = logging.getLogger(__name__)

MUSIC_BASE = r"C:\Users\PC\Downloads\SHORTS\MUSICAS-SHORTS"

SUBNICHO_FOLDER = {
    "Guerras e Civilizações": "Musicas 02",
    "Guerras e Civilizacoes": "Musicas 02",
    "Relatos de Guerra": "Musicas 03",
    "Frentes de Guerra": "Musicas 03",
    "Reis Perversos": "Musicas 05",
    "Historias Sombrias": "Musicas 05",
    "Culturas Macabras": "Musicas 05",
    "Monetizados": "Musicas 06",
}


def select_music(subnicho: str, canal: str, music_category: str, db=None) -> str | None:
    """Seleciona uma track de música que ainda não foi usada nesse canal.

    Args:
        subnicho: Subnicho do vídeo
        canal: Nome do canal (pra controle de repetição)
        music_category: Categoria escolhida pelo scriptwriter (ex: "tension")
        db: SupabaseClient (opcional, pra checar repetição)

    Returns:
        Caminho completo do arquivo MP3, ou None se não encontrou.
    """
    folder = SUBNICHO_FOLDER.get(subnicho)
    if not folder:
        logger.warning(f"Subnicho '{subnicho}' sem pasta de música mapeada")
        return None

    category_path = os.path.join(MUSIC_BASE, folder, "music", music_category)
    if not os.path.exists(category_path):
        logger.warning(f"Categoria '{music_category}' não existe em {folder}")
        # Fallback: pegar qualquer categoria disponível
        music_dir = os.path.join(MUSIC_BASE, folder, "music")
        available = [d for d in os.listdir(music_dir)
                     if os.path.isdir(os.path.join(music_dir, d)) and d != "shared"]
        if not available:
            return None
        music_category = random.choice(available)
        category_path = os.path.join(MUSIC_BASE, folder, "music", music_category)
        logger.info(f"Fallback categoria: {music_category}")

    # Listar todas as tracks disponíveis
    all_tracks = sorted(glob.glob(os.path.join(category_path, "*.mp3")))
    if not all_tracks:
        logger.warning(f"Nenhuma track em {category_path}")
        return None

    # Checar quais já foram usadas nesse canal (via Supabase)
    used_tracks = set()
    if db:
        try:
            result = db.supabase.table("shorts_production").select("music_track").eq("canal", canal).order("created_at", desc=True).limit(50).execute()
            used_tracks = {r["music_track"] for r in result.data if r.get("music_track")}
        except Exception as e:
            logger.warning(f"Erro ao checar tracks usadas: {e}")

    # Filtrar: tracks não usadas nesse canal
    track_names = {os.path.basename(t): t for t in all_tracks}
    available = {name: path for name, path in track_names.items() if name not in used_tracks}

    if not available:
        # Esgotou — volta pro início (todas disponíveis)
        available = track_names
        logger.info(f"Canal '{canal}' esgotou tracks de '{music_category}', reiniciando ciclo")

    # Escolher aleatório
    chosen_name = random.choice(list(available.keys()))
    chosen_path = available[chosen_name]

    logger.info(f"Música selecionada: {music_category}/{chosen_name}")
    return chosen_path
