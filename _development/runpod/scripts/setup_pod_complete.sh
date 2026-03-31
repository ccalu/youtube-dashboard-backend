#!/bin/bash
# =============================================================================
# LTX 2.3 DEV — Setup Completo para RunPod (RTX 5090)
# Versao FINAL com todos os modelos necessarios para 3 workflows
# =============================================================================
set -e

echo "=========================================="
echo " LTX 2.3 SETUP COMPLETO — Content Factory"
echo "=========================================="

COMFY="/workspace/runpod-slim/ComfyUI"
MODELS="$COMFY/models"
NODES="$COMFY/custom_nodes"

# =============================================================================
# STEP 1: Custom Nodes
# =============================================================================
echo ""
echo "[1/4] Instalando Custom Nodes..."
cd $NODES

# ComfyUI-LTXVideo (oficial Lightricks)
[ -d "ComfyUI-LTXVideo" ] || git clone -q https://github.com/Lightricks/ComfyUI-LTXVideo.git
cd ComfyUI-LTXVideo && git pull -q 2>/dev/null && cd ..
pip install -q -r ComfyUI-LTXVideo/requirements.txt 2>/dev/null

# VideoHelperSuite (VHS_VideoCombine)
[ -d "ComfyUI-VideoHelperSuite" ] || git clone -q https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
pip install -q -r ComfyUI-VideoHelperSuite/requirements.txt 2>/dev/null

# RES4LYF (ClownSampler_Beta - necessario pro workflow Single-Stage)
[ -d "RES4LYF" ] || git clone -q https://github.com/ClownsharkBatwing/RES4LYF.git
pip install -q -r RES4LYF/requirements.txt 2>/dev/null

# KJNodes (utility nodes)
[ -d "ComfyUI-KJNodes" ] || git clone -q https://github.com/kijai/ComfyUI-KJNodes.git
pip install -q -r ComfyUI-KJNodes/requirements.txt 2>/dev/null

# Workflow Converter (converte frontend JSON → API format)
[ -d "comfyui-workflow-to-api-converter-endpoint" ] || git clone -q https://github.com/SethRobinson/comfyui-workflow-to-api-converter-endpoint.git

echo "  Nodes OK"

# =============================================================================
# STEP 2: Modelos — Download paralelo
# =============================================================================
echo ""
echo "[2/4] Baixando modelos..."

# --- Checkpoint DEV FP8 (28GB) ---
if [ ! -f "$MODELS/checkpoints/ltx-2.3-22b-dev-fp8.safetensors" ]; then
    echo "  [1] Checkpoint DEV FP8 (28GB)..."
    wget -q "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors" \
        -O "$MODELS/checkpoints/ltx-2.3-22b-dev-fp8.safetensors" &
    PID_CKPT=$!
else
    echo "  [1] Checkpoint DEV FP8 — ja existe"
    PID_CKPT=""
fi

# --- Gemma Text Encoder V2 FP8 (12GB) --- MUST be V2 (has vision weights)
if [ ! -f "$MODELS/text_encoders/gemma_3_12B_it_heretic_v2_fp8.safetensors" ]; then
    echo "  [2] Gemma 3 V2 FP8 (12GB)..."
    wget -q "https://huggingface.co/DreamFast/gemma-3-12b-it-heretic-v2/resolve/main/comfyui/gemma_3_12B_it_heretic_v2_fp8_e4m3fn.safetensors" \
        -O "$MODELS/text_encoders/gemma_3_12B_it_heretic_v2_fp8.safetensors" &
    PID_GEMMA=$!
else
    echo "  [2] Gemma 3 V2 FP8 — ja existe"
    PID_GEMMA=""
fi

# --- Text Projection (necessario para DualCLIPLoader no RuneXX) ---
if [ ! -f "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors" ]; then
    echo "  [3] Text Projection (necessario RuneXX)..."
    wget -q "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/text_encoders/ltx-2.3_text_projection_bf16.safetensors" \
        -O "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors" &
    PID_PROJ=$!
else
    echo "  [3] Text Projection — ja existe"
    PID_PROJ=""
fi

# --- LoRA Distilled (7.1GB) ---
if [ ! -f "$MODELS/loras/ltx-2.3-22b-distilled-lora-384.safetensors" ]; then
    echo "  [4] LoRA Distilled (7.1GB)..."
    wget -q "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors" \
        -O "$MODELS/loras/ltx-2.3-22b-distilled-lora-384.safetensors" &
    PID_LORA=$!
else
    echo "  [4] LoRA Distilled — ja existe"
    PID_LORA=""
fi

# --- Spatial Upscaler x2 (1.1GB) ---
mkdir -p "$MODELS/latent_upscale_models"
if [ ! -f "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.0.safetensors" ]; then
    echo "  [5] Spatial Upscaler x2 (1.1GB)..."
    wget -q "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.0.safetensors" \
        -O "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.0.safetensors" &
    PID_UP=$!
else
    echo "  [5] Spatial Upscaler — ja existe"
    PID_UP=""
fi

# --- Video VAE (2.3GB) ---
if [ ! -f "$MODELS/vae/LTX2_video_vae_bf16.safetensors" ]; then
    echo "  [6] Video VAE (2.3GB)..."
    wget -q "https://huggingface.co/Kijai/LTXV2_comfy/resolve/main/VAE/LTX2_video_vae_bf16.safetensors" \
        -O "$MODELS/vae/LTX2_video_vae_bf16.safetensors" &
    PID_VVAE=$!
else
    echo "  [6] Video VAE — ja existe"
    PID_VVAE=""
fi

# --- Audio VAE (208MB) ---
if [ ! -f "$MODELS/vae/LTX2_audio_vae_bf16.safetensors" ]; then
    echo "  [7] Audio VAE (208MB)..."
    wget -q "https://huggingface.co/Kijai/LTXV2_comfy/resolve/main/VAE/LTX2_audio_vae_bf16.safetensors" \
        -O "$MODELS/vae/LTX2_audio_vae_bf16.safetensors" &
    PID_AVAE=$!
else
    echo "  [7] Audio VAE — ja existe"
    PID_AVAE=""
fi

# Esperar downloads
echo ""
echo "  Aguardando downloads..."
[ -n "$PID_GEMMA" ] && wait $PID_GEMMA && echo "  [2] Gemma DONE" || true
[ -n "$PID_PROJ" ] && wait $PID_PROJ && echo "  [3] Text Projection DONE" || true
[ -n "$PID_LORA" ] && wait $PID_LORA && echo "  [4] LoRA DONE" || true
[ -n "$PID_UP" ] && wait $PID_UP && echo "  [5] Upscaler DONE" || true
[ -n "$PID_VVAE" ] && wait $PID_VVAE && echo "  [6] Video VAE DONE" || true
[ -n "$PID_AVAE" ] && wait $PID_AVAE && echo "  [7] Audio VAE DONE" || true
[ -n "$PID_CKPT" ] && wait $PID_CKPT && echo "  [1] Checkpoint DONE" || true

# =============================================================================
# STEP 3: Verificacao
# =============================================================================
echo ""
echo "[3/4] Verificando..."

check() {
    if [ -f "$1" ]; then
        size=$(du -h "$1" | cut -f1)
        echo "  OK  $size  $(basename $1)"
    else
        echo "  FALTA     $1"
    fi
}

echo "  -- Checkpoints --"
check "$MODELS/checkpoints/ltx-2.3-22b-dev-fp8.safetensors"
echo "  -- Text Encoders --"
check "$MODELS/text_encoders/gemma_3_12B_it_heretic_v2_fp8.safetensors"
check "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors"
echo "  -- LoRAs --"
check "$MODELS/loras/ltx-2.3-22b-distilled-lora-384.safetensors"
echo "  -- VAE --"
check "$MODELS/vae/LTX2_video_vae_bf16.safetensors"
check "$MODELS/vae/LTX2_audio_vae_bf16.safetensors"
echo "  -- Upscalers --"
check "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.0.safetensors"
echo "  -- Nodes --"
for node in ComfyUI-LTXVideo ComfyUI-VideoHelperSuite RES4LYF ComfyUI-KJNodes; do
    [ -d "$NODES/$node" ] && echo "  OK  $node" || echo "  FALTA  $node"
done

echo ""
echo "  Disco:"
df -h /workspace | tail -1

# =============================================================================
# STEP 4: Iniciar ComfyUI
# =============================================================================
echo ""
echo "[4/4] Iniciando ComfyUI na porta 3000..."
killall -9 python3 2>/dev/null || true
sleep 3
cd $COMFY
nohup python3 main.py --listen 0.0.0.0 --port 3000 --disable-auto-launch > /tmp/comfyui.log 2>&1 &
echo "  PID: $!"
echo "  Aguardando startup (30s)..."
sleep 30

# Verificar nodes
echo "  Verificando nodes..."
for node in VHS_VideoCombine ClownSampler_Beta LTXVImgToVideoInplace LTXVImgToVideoConditionOnly LTXVPreprocess LTXVScheduler LTXVConditioning LTXVConcatAVLatent LTXVSeparateAVLatent LTXVLatentUpsampler EmptyLTXVLatentVideo LTXVEmptyLatentAudio LTXVAudioVAEDecode LTXVAudioVAELoader CFGGuider KSamplerSelect SamplerCustomAdvanced ManualSigmas RandomNoise; do
    result=$(curl -s "http://localhost:3000/object_info/$node" 2>/dev/null)
    if echo "$result" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        echo "    OK  $node"
    else
        echo "    FALTA  $node"
    fi
done

echo ""
echo "=========================================="
echo " SETUP COMPLETO!"
echo "=========================================="
