#!/bin/bash
# =============================================================================
# LTX 2.3 + ComfyUI — Setup Completo para RunPod
# Content Factory — Producao de Shorts
# =============================================================================
# Este script instala TUDO necessario para rodar LTX 2.3 I2V no ComfyUI.
# Rodar DENTRO do pod RunPod (via SSH).
# Tempo estimado: ~20-30 min (download dos modelos)
# =============================================================================

set -e

echo "=========================================="
echo " LTX 2.3 Setup — Content Factory"
echo "=========================================="

# Paths
WORKSPACE="/workspace"
COMFYUI_DIR="$WORKSPACE/ComfyUI"
MODELS_DIR="$COMFYUI_DIR/models"
CUSTOM_NODES="$COMFYUI_DIR/custom_nodes"

# =============================================================================
# STEP 1: ComfyUI
# =============================================================================
echo ""
echo "[1/6] Verificando ComfyUI..."

if [ -d "$COMFYUI_DIR" ]; then
    echo "  ComfyUI ja existe. Atualizando..."
    cd "$COMFYUI_DIR"
    git pull 2>/dev/null || echo "  (git pull falhou, continuando...)"
else
    echo "  Instalando ComfyUI..."
    cd "$WORKSPACE"
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd "$COMFYUI_DIR"
    pip install -r requirements.txt
fi

# =============================================================================
# STEP 2: Custom Nodes
# =============================================================================
echo ""
echo "[2/6] Instalando Custom Nodes..."

cd "$CUSTOM_NODES"

# ComfyUI-LTXVideo (oficial Lightricks — OBRIGATORIO para LTX 2.3)
if [ -d "ComfyUI-LTXVideo" ]; then
    echo "  ComfyUI-LTXVideo ja existe. Atualizando..."
    cd ComfyUI-LTXVideo && git pull && cd ..
else
    echo "  Clonando ComfyUI-LTXVideo..."
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
fi
if [ -f "ComfyUI-LTXVideo/requirements.txt" ]; then
    pip install -r ComfyUI-LTXVideo/requirements.txt 2>/dev/null || true
fi

# ComfyUI-VideoHelperSuite (output de video — VHS_VideoCombine)
if [ -d "ComfyUI-VideoHelperSuite" ]; then
    echo "  VideoHelperSuite ja existe. Atualizando..."
    cd ComfyUI-VideoHelperSuite && git pull && cd ..
else
    echo "  Clonando ComfyUI-VideoHelperSuite..."
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
fi
if [ -f "ComfyUI-VideoHelperSuite/requirements.txt" ]; then
    pip install -r ComfyUI-VideoHelperSuite/requirements.txt 2>/dev/null || true
fi

# ComfyUI-Manager (gerenciamento de nodes)
if [ -d "ComfyUI-Manager" ]; then
    echo "  ComfyUI-Manager ja existe. Atualizando..."
    cd ComfyUI-Manager && git pull && cd ..
else
    echo "  Clonando ComfyUI-Manager..."
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git
fi

# ComfyUI-KJNodes (utility nodes)
if [ -d "ComfyUI-KJNodes" ]; then
    echo "  KJNodes ja existe. Atualizando..."
    cd ComfyUI-KJNodes && git pull && cd ..
else
    echo "  Clonando ComfyUI-KJNodes..."
    git clone https://github.com/kijai/ComfyUI-KJNodes.git
fi
if [ -f "ComfyUI-KJNodes/requirements.txt" ]; then
    pip install -r ComfyUI-KJNodes/requirements.txt 2>/dev/null || true
fi

echo "  Custom nodes instalados."

# =============================================================================
# STEP 3: LTX 2.3 FP8 Checkpoint (~20GB)
# =============================================================================
echo ""
echo "[3/6] Baixando LTX 2.3 FP8 checkpoint (~20GB)..."

mkdir -p "$MODELS_DIR/checkpoints"

if [ -f "$MODELS_DIR/checkpoints/ltx-2.3-fp8.safetensors" ]; then
    echo "  Checkpoint ja existe. Pulando."
else
    echo "  Baixando de HuggingFace..."
    cd "$MODELS_DIR/checkpoints"
    wget -q --show-progress \
        "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-fp8.safetensors" \
        -O ltx-2.3-fp8.safetensors
    echo "  Checkpoint baixado."
fi

# =============================================================================
# STEP 4: Text Encoder — Gemma 3 12B
# =============================================================================
echo ""
echo "[4/6] Baixando Gemma 3 12B text encoder (~9.5GB)..."

mkdir -p "$MODELS_DIR/text_encoders"

if [ -f "$MODELS_DIR/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors" ]; then
    echo "  Gemma 3 ja existe. Pulando."
else
    echo "  Baixando de HuggingFace (Kijai)..."
    cd "$MODELS_DIR/text_encoders"
    wget -q --show-progress \
        "https://huggingface.co/Kijai/LTXV2_comfy/resolve/main/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors" \
        -O gemma_3_12B_it_fp4_mixed.safetensors
    echo "  Gemma 3 baixado."
fi

# Embeddings Connector
echo "  Baixando embeddings connector (~2.9GB)..."

if [ -f "$MODELS_DIR/text_encoders/ltx-2.3-embeddings_connector_bf16.safetensors" ]; then
    echo "  Embeddings connector ja existe. Pulando."
else
    cd "$MODELS_DIR/text_encoders"
    wget -q --show-progress \
        "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-embeddings_connector_bf16.safetensors" \
        -O ltx-2.3-embeddings_connector_bf16.safetensors
    echo "  Embeddings connector baixado."
fi

# =============================================================================
# STEP 5: VAEs (Video + Audio)
# =============================================================================
echo ""
echo "[5/6] Baixando VAEs..."

mkdir -p "$MODELS_DIR/vae"

# Video VAE
if [ -f "$MODELS_DIR/vae/ltx_2_video_vae_bf16.safetensors" ]; then
    echo "  Video VAE ja existe. Pulando."
else
    echo "  Baixando Video VAE (~2.5GB)..."
    cd "$MODELS_DIR/vae"
    wget -q --show-progress \
        "https://huggingface.co/Kijai/LTXV2_comfy/resolve/main/VAE/ltx_2_video_vae_bf16.safetensors" \
        -O ltx_2_video_vae_bf16.safetensors
    echo "  Video VAE baixado."
fi

# Audio VAE
if [ -f "$MODELS_DIR/vae/LTX2_audio_vae_bf16.safetensors" ]; then
    echo "  Audio VAE ja existe. Pulando."
else
    echo "  Baixando Audio VAE (~218MB)..."
    cd "$MODELS_DIR/vae"
    wget -q --show-progress \
        "https://huggingface.co/Kijai/LTXV2_comfy/resolve/main/VAE/LTX2_audio_vae_bf16.safetensors" \
        -O LTX2_audio_vae_bf16.safetensors
    echo "  Audio VAE baixado."
fi

# =============================================================================
# STEP 6: Verificacao Final
# =============================================================================
echo ""
echo "[6/6] Verificacao final..."
echo ""
echo "  Arquivos instalados:"
echo "  ───────────────────────────────────────────────────"

check_file() {
    if [ -f "$1" ]; then
        size=$(du -h "$1" | cut -f1)
        echo "  OK  $size  $(basename $1)"
    else
        echo "  FALTA     $(basename $1)"
    fi
}

check_file "$MODELS_DIR/checkpoints/ltx-2.3-fp8.safetensors"
check_file "$MODELS_DIR/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"
check_file "$MODELS_DIR/text_encoders/ltx-2.3-embeddings_connector_bf16.safetensors"
check_file "$MODELS_DIR/vae/ltx_2_video_vae_bf16.safetensors"
check_file "$MODELS_DIR/vae/LTX2_audio_vae_bf16.safetensors"

echo ""
echo "  Custom Nodes:"
for node in ComfyUI-LTXVideo ComfyUI-VideoHelperSuite ComfyUI-Manager ComfyUI-KJNodes; do
    if [ -d "$CUSTOM_NODES/$node" ]; then
        echo "  OK  $node"
    else
        echo "  FALTA  $node"
    fi
done

echo ""
echo "  Espaco usado no volume:"
du -sh "$WORKSPACE"/* 2>/dev/null | head -10

echo ""
echo "=========================================="
echo " SETUP COMPLETO!"
echo " Espaco total usado no /workspace:"
du -sh "$WORKSPACE" 2>/dev/null
echo "=========================================="
echo ""
echo " Para iniciar o ComfyUI:"
echo "   cd $COMFYUI_DIR && python main.py --listen 0.0.0.0 --port 8188"
echo ""
