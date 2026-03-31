#!/bin/bash
# =============================================================================
# Setup Axiomgraph LTX 2.3 I2V Workflow — Content Factory
# Modelos e nodes EXATOS do workflow axiomgraph_i2v_v1.json
# =============================================================================
set -e

COMFY="/workspace/runpod-slim/ComfyUI"
MODELS="$COMFY/models"
NODES="$COMFY/custom_nodes"

echo "=========================================="
echo " SETUP AXIOMGRAPH I2V — Content Factory"
echo "=========================================="

# =============================================================================
# STEP 1: Custom Nodes
# =============================================================================
echo "[1/3] Instalando Custom Nodes..."
cd $NODES

[ -d "ComfyUI-LTXVideo" ] || git clone -q https://github.com/Lightricks/ComfyUI-LTXVideo.git
[ -d "ComfyUI-VideoHelperSuite" ] || git clone -q https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
[ -d "ComfyUI-KJNodes" ] || git clone -q https://github.com/kijai/ComfyUI-KJNodes.git
[ -d "rgthree-comfy" ] || git clone -q https://github.com/rgthree/rgthree-comfy.git
[ -d "ComfyMath" ] || git clone -q https://github.com/evanspearman/ComfyMath.git
[ -d "comfyui-workflow-to-api-converter-endpoint" ] || git clone -q https://github.com/SethRobinson/comfyui-workflow-to-api-converter-endpoint.git

# Install requirements
for dir in ComfyUI-LTXVideo ComfyUI-VideoHelperSuite ComfyUI-KJNodes; do
    [ -f "$dir/requirements.txt" ] && pip install -q -r "$dir/requirements.txt" 2>/dev/null
done

echo "  Nodes OK"

# =============================================================================
# STEP 2: Modelos (download paralelo)
# =============================================================================
echo "[2/3] Baixando modelos..."

# 1. Transformer distilled FP8 v2 (~20GB) → diffusion_models/
mkdir -p "$MODELS/diffusion_models"
if [ ! -f "$MODELS/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v2.safetensors" ]; then
    echo "  [1/7] Transformer distilled FP8 v2..."
    wget -q "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v2.safetensors" \
        -O "$MODELS/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v2.safetensors" &
    P1=$!
else echo "  [1/7] Transformer — ja existe"; P1=""; fi

# 2. Gemma fp8_scaled (~12GB) → text_encoders/
if [ ! -f "$MODELS/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors" ]; then
    echo "  [2/7] Gemma 3 fp8_scaled..."
    wget -q "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors" \
        -O "$MODELS/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors" &
    P2=$!
else echo "  [2/7] Gemma — ja existe"; P2=""; fi

# 3. Text projection (~2.2GB) → text_encoders/
if [ ! -f "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors" ]; then
    echo "  [3/7] Text projection..."
    wget -q "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/text_encoders/ltx-2.3_text_projection_bf16.safetensors" \
        -O "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors" &
    P3=$!
else echo "  [3/7] Text projection — ja existe"; P3=""; fi

# 4. LoRA abliterated (~500MB) → loras/
if [ ! -f "$MODELS/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors" ]; then
    echo "  [4/7] LoRA abliterated..."
    wget -q "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors" \
        -O "$MODELS/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors" &
    P4=$!
else echo "  [4/7] LoRA — ja existe"; P4=""; fi

# 5. Video VAE Kijai (~2.3GB) → vae/
if [ ! -f "$MODELS/vae/LTX23_video_vae_bf16.safetensors" ]; then
    echo "  [5/7] Video VAE (Kijai)..."
    wget -q "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_video_vae_bf16.safetensors" \
        -O "$MODELS/vae/LTX23_video_vae_bf16.safetensors" &
    P5=$!
else echo "  [5/7] Video VAE — ja existe"; P5=""; fi

# 6. Audio VAE Kijai (~208MB) → vae/
if [ ! -f "$MODELS/vae/LTX23_audio_vae_bf16.safetensors" ]; then
    echo "  [6/7] Audio VAE (Kijai)..."
    wget -q "https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_audio_vae_bf16.safetensors" \
        -O "$MODELS/vae/LTX23_audio_vae_bf16.safetensors" &
    P6=$!
else echo "  [6/7] Audio VAE — ja existe"; P6=""; fi

# 7. Spatial Upscaler v1.1 (~996MB) → latent_upscale_models/
mkdir -p "$MODELS/latent_upscale_models"
if [ ! -f "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors" ]; then
    echo "  [7/7] Spatial Upscaler v1.1..."
    wget -q "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors" \
        -O "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors" &
    P7=$!
else echo "  [7/7] Upscaler — ja existe"; P7=""; fi

echo "  Aguardando downloads..."
[ -n "$P3" ] && wait $P3 && echo "  [3] Text projection DONE"
[ -n "$P4" ] && wait $P4 && echo "  [4] LoRA DONE"
[ -n "$P5" ] && wait $P5 && echo "  [5] Video VAE DONE"
[ -n "$P6" ] && wait $P6 && echo "  [6] Audio VAE DONE"
[ -n "$P7" ] && wait $P7 && echo "  [7] Upscaler DONE"
[ -n "$P2" ] && wait $P2 && echo "  [2] Gemma DONE"
[ -n "$P1" ] && wait $P1 && echo "  [1] Transformer DONE"

# =============================================================================
# STEP 3: Verificacao
# =============================================================================
echo "[3/3] Verificando..."

check() {
    if [ -f "$1" ]; then
        size=$(du -h "$1" | cut -f1)
        echo "  OK  $size  $(basename $1)"
    else
        echo "  FALTA  $(basename $1)"
    fi
}

check "$MODELS/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v2.safetensors"
check "$MODELS/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors"
check "$MODELS/text_encoders/ltx-2.3_text_projection_bf16.safetensors"
check "$MODELS/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors"
check "$MODELS/vae/LTX23_video_vae_bf16.safetensors"
check "$MODELS/vae/LTX23_audio_vae_bf16.safetensors"
check "$MODELS/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors"

echo ""
echo "  Disco:"
df -h /workspace | tail -1
echo ""
echo "=========================================="
echo " SETUP COMPLETO!"
echo "=========================================="
