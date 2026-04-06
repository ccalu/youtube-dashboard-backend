"""
Remotion Editor — pós-produção de Shorts.

Recebe pasta de produção com clips + narração.
Acelera narração 1.1x, gera captions via Whisper, renderiza vídeo final com legendas.
Copia resultado pro Google Drive.
"""

import json
import os
import glob
import subprocess
import shutil
import logging
import time

logger = logging.getLogger(__name__)

REMOTION_PROJECT = r"C:\Users\PC\Desktop\ContentFactory\shorts-editor"
DRIVE_SHORTS_PATH = r"C:\Users\PC\Downloads\SHORTS"  # Base do Drive sync

NARRATION_SPEED = 1.1  # Velocidade da narração (1.0 = normal, 1.1 = 10% mais rápido)

# Cores de highlight por subnicho
HIGHLIGHT_COLORS = {
    "Reis Perversos": "#9B30FF",
    "Historias Sombrias": "#9B30FF",
    "Culturas Macabras": "#9B30FF",
    "Relatos de Guerra": "#00CC44",
    "Frentes de Guerra": "#00CC44",
    "Guerras e Civilizações": "#FF8C00",
    "Monetizados": "#E51A1A",
}


def edit_short(production_path: str, subnicho: str = "", log_callback=None) -> str:
    """
    Edita um Short: acelera narração → Whisper → Remotion render → copia pro Drive.

    Args:
        production_path: Pasta com clips/, img/, narracao.mp3
        subnicho: Subnicho pra cor da legenda
        log_callback: Função opcional pra logs em tempo real

    Returns:
        Caminho do vídeo final
    """
    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    start_time = time.time()
    log(f"=== EDITANDO: {os.path.basename(production_path)} ===")

    # 1. Verificar assets
    clips = sorted(glob.glob(os.path.join(production_path, "clips", "*.mp4")))
    narracao = os.path.join(production_path, "narracao.mp3")

    if not clips:
        raise RuntimeError(f"Sem clips em {production_path}/clips/")
    if not os.path.exists(narracao):
        raise RuntimeError(f"narracao.mp3 não encontrada em {production_path}")

    log(f"  {len(clips)} clips + narracao encontrados")

    # 2. Acelerar narração pra 1.1x
    narracao_fast = os.path.join(production_path, "narracao_fast.mp3")
    if NARRATION_SPEED != 1.0:
        log(f"  Acelerando narração pra {NARRATION_SPEED}x...")
        _speed_up_audio(narracao, narracao_fast, NARRATION_SPEED)
        dur_orig = _get_audio_duration(narracao)
        dur_fast = _get_audio_duration(narracao_fast)
        log(f"  {dur_orig:.1f}s >> {dur_fast:.1f}s (economizou {dur_orig - dur_fast:.1f}s)")
        narracao_to_use = narracao_fast
    else:
        narracao_to_use = narracao

    # 3. Copiar assets pro Remotion public/
    public_dir = os.path.join(REMOTION_PROJECT, "public")
    os.makedirs(public_dir, exist_ok=True)

    # Limpar public anterior
    for f in glob.glob(os.path.join(public_dir, "*")):
        os.remove(f)

    # Copiar clips
    clip_names = []
    for i, clip in enumerate(clips):
        name = f"clip_{i+1:02d}.mp4"
        shutil.copy2(clip, os.path.join(public_dir, name))
        clip_names.append(name)

    # Copiar narração acelerada
    shutil.copy2(narracao_to_use, os.path.join(public_dir, "narracao.mp3"))

    # Selecionar música de fundo
    music_file = None
    music_track_name = None
    producao_json_path = os.path.join(production_path, "producao.json")
    if os.path.exists(producao_json_path):
        with open(producao_json_path, "r", encoding="utf-8") as _f:
            _prod = json.load(_f)
        music_category = _prod.get("music_category", "tension")
        canal = _prod.get("canal", "")

        try:
            from dotenv import load_dotenv
            load_dotenv()
            from _features.shorts_production.music_selector import select_music
            from database import SupabaseClient
            _db = SupabaseClient()
            music_file = select_music(subnicho, canal, music_category, db=_db)
        except Exception as e:
            log(f"  Musica: erro ao selecionar - {e}")

    if music_file:
        music_track_name = os.path.basename(music_file)
        shutil.copy2(music_file, os.path.join(public_dir, "musica.mp3"))
        log(f"  Musica: {music_track_name}")
    else:
        log(f"  Musica: nenhuma selecionada")

    log(f"  Assets copiados pra Remotion")

    # 4. Transcrever narração acelerada com Whisper
    log("  Transcrevendo narração com Whisper...")
    captions = _transcribe_with_whisper(narracao_to_use)

    captions_path = os.path.join(public_dir, "captions.json")
    with open(captions_path, "w", encoding="utf-8") as f:
        json.dump(captions, f, ensure_ascii=False, indent=2)
    log(f"  {len(captions)} palavras transcritas")

    # 5. Calcular duração de cada parágrafo (clip timing)
    audio_duration = _get_audio_duration(narracao_to_use)
    log(f"  Duração áudio final: {audio_duration:.1f}s")

    producao_json_path = os.path.join(production_path, "producao.json")
    clip_durations = None
    if os.path.exists(producao_json_path):
        with open(producao_json_path, "r", encoding="utf-8") as f:
            prod_data = json.load(f)
        script_text = prod_data.get("script", "")
        clip_durations = _calc_clip_durations(script_text, captions, audio_duration)
        if clip_durations and len(clip_durations) == len(clip_names):
            log(f"  Clip timings: {[f'{d:.1f}s' for d in clip_durations]}")
        else:
            clip_durations = None
            log("  Clip timings: usando distribuicao igual (fallback)")

    # 6. Renderizar com Remotion
    output_path = os.path.join(production_path, "video_final.mp4")
    log("  Renderizando vídeo final...")

    props_dict = {
        "clipPaths": clip_names,
        "audioPaths": ["narracao.mp3"],
        "captionsPath": "captions.json",
        "subnicho": subnicho,
    }
    if clip_durations:
        props_dict["clipDurations"] = clip_durations
    if music_file:
        props_dict["musicPath"] = "musica.mp3"
        props_dict["musicVolume"] = 0.5
    props = json.dumps(props_dict)

    npx_path = r"C:\Program Files\nodejs\npx.cmd"

    cmd = [
        npx_path, "remotion", "render",
        "src/index.ts",
        "ShortsVideo",
        output_path,
        "--props", props,
    ]

    result = subprocess.run(
        cmd,
        cwd=REMOTION_PROJECT,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error(f"Remotion error: {result.stderr[:500]}")
        raise RuntimeError(f"Remotion render falhou: {result.stderr[:200]}")

    render_time = time.time() - start_time
    log(f"  Video final: {output_path}")
    log(f"  Tempo total edicao: {render_time:.0f}s")

    # 7. Upload pro Google Drive
    drive_url = None
    try:
        from _features.shorts_production.drive_uploader import upload_to_drive

        producao_json = os.path.join(production_path, "producao.json")
        if os.path.exists(producao_json):
            import json as _json
            with open(producao_json, "r", encoding="utf-8") as f:
                prod_data = _json.load(f)
            canal = prod_data.get("canal", "")
            titulo = prod_data.get("titulo", os.path.basename(production_path))

            lang_map = {"Português": "PO", "Inglês": "EN", "Espanhol": "ES", "Francês": "FR",
                        "Italiano": "IT", "Russo": "RU", "Japonês": "JP", "Coreano": "KO",
                        "Turco": "TR", "Polonês": "PL", "Alemão": "DE"}
            lingua = prod_data.get("lingua", "Português")
            lang_code = lang_map.get(lingua, "PT")
            canal_folder = f"({lang_code}) {canal}"

            drive_url = upload_to_drive(
                production_path, subnicho, canal_folder, titulo, log_callback=log_callback
            )
            log(f"  Drive: {drive_url}")
        else:
            log("  Drive: producao.json nao encontrado, pulando upload")
    except Exception as e:
        log(f"  Drive: ERRO no upload - {e}")

    log(f"=== EDICAO COMPLETA ===")
    return {"video_path": output_path, "drive_url": drive_url}


def _speed_up_audio(input_path: str, output_path: str, speed: float):
    """Acelera áudio com ffmpeg (atempo)."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", f"atempo={speed}",
        "-vn", output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg speed error: {result.stderr[:200]}")


def _transcribe_with_whisper(audio_path: str) -> list:
    """Transcreve áudio com OpenAI Whisper e retorna captions no formato Remotion."""
    import whisper

    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, word_timestamps=True)

    captions = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            captions.append({
                "text": word["word"],
                "startMs": int(word["start"] * 1000),
                "endMs": int(word["end"] * 1000),
                "timestampMs": int(word["start"] * 1000),
                "confidence": word.get("probability", 1.0),
            })

    return captions


def _calc_clip_durations(script: str, captions: list, total_duration: float) -> list | None:
    """Calcula duração de cada clip buscando a última palavra de cada parágrafo no Whisper.

    Procura a última palavra significativa de cada parágrafo na sequência do Whisper.
    O corte acontece após essa palavra ser falada.
    """
    import re as _re

    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    num_clips = len(paragraphs)
    if num_clips < 2 or not captions or len(captions) < 2:
        return None

    def _normalize(text: str) -> str:
        """Remove pontuação e normaliza pra comparação."""
        s = text.lower().strip()
        s = _re.sub(r"[^a-záàâãéèêíïóôõúüç0-9\s]", "", s)
        return s.strip()

    # Pra cada parágrafo, encontrar onde sua última palavra aparece no Whisper
    whisper_words = [_normalize(c["text"]) for c in captions]
    cut_indices = []  # índice no Whisper onde cada parágrafo termina
    search_from = 0

    for i, para in enumerate(paragraphs):
        para_words = [_normalize(w) for w in para.split() if _normalize(w)]
        if not para_words:
            continue

        # Pegar as últimas 2-3 palavras significativas do parágrafo pra busca
        last_words = para_words[-min(3, len(para_words)):]

        # Buscar sequência no Whisper a partir de search_from
        found = False
        for j in range(search_from, len(whisper_words) - len(last_words) + 1):
            match = True
            for k, lw in enumerate(last_words):
                ww = whisper_words[j + k]
                # Match se uma contém a outra (Whisper pode ter pontuação grudada)
                if lw not in ww and ww not in lw and lw[:4] != ww[:4]:
                    match = False
                    break
            if match:
                cut_idx = j + len(last_words) - 1
                cut_indices.append(cut_idx)
                search_from = cut_idx + 1
                found = True
                break

        if not found:
            # Fallback: avançar pelo número de palavras do parágrafo
            fallback_idx = min(search_from + len(para_words) - 1, len(captions) - 1)
            cut_indices.append(fallback_idx)
            search_from = fallback_idx + 1
            logger.warning(f"Clip timing: paragrafo {i+1} nao encontrado, usando fallback")

    if len(cut_indices) != num_clips:
        return None

    # Montar durações baseadas nos cut points
    durations = []
    prev_time = 0.0

    for i, idx in enumerate(cut_indices):
        end_time = captions[idx]["endMs"] / 1000.0

        if i < len(cut_indices) - 1:
            # Próximo parágrafo começa na próxima palavra
            next_start = captions[min(idx + 1, len(captions) - 1)]["startMs"] / 1000.0
            # Cortar no meio da pausa
            cut_time = (end_time + next_start) / 2.0
        else:
            cut_time = total_duration

        durations.append(cut_time - prev_time)
        prev_time = cut_time

    if any(d <= 0 for d in durations):
        return None

    return durations


def _get_audio_duration(audio_path: str) -> float:
    """Retorna duração do áudio em segundos via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python remotion_editor.py <pasta_producao> [subnicho]")
        sys.exit(1)

    path = sys.argv[1]
    sub = sys.argv[2] if len(sys.argv) > 2 else ""
    edit_short(path, sub)
