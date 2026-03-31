# Setup Final — Workflow Axiomgraph I2V

> Workflow: LTX 2.3 Image To Video V1 (axiomgraph)
> Fonte: github.com/axiomgraph/ComfyUIWorkflow
> Video tutorial: YouTube @AxiomGraph

---

## 7 Modelos necessarios

| # | Arquivo | Pasta ComfyUI | URL Download | Tamanho est. |
|---|---------|---------------|-------------|-------------|
| 1 | ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v2.safetensors | models/diffusion_models/ | huggingface.co/Kijai/LTX2.3_comfy | ~20GB |
| 2 | gemma_3_12B_it_fp8_scaled.safetensors | models/text_encoders/ | huggingface.co/Comfy-Org/ltx-2/split_files/text_encoders/ | ~12GB |
| 3 | ltx-2.3_text_projection_bf16.safetensors | models/text_encoders/ | huggingface.co/Kijai/LTX2.3_comfy/text_encoders/ | ~2.2GB |
| 4 | gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors | models/loras/ | huggingface.co/Comfy-Org/ltx-2/split_files/loras/ | ~500MB |
| 5 | LTX23_video_vae_bf16.safetensors | models/vae/ | huggingface.co/Kijai/LTX2.3_comfy/vae/ | ~2.3GB |
| 6 | LTX23_audio_vae_bf16.safetensors | models/vae/ | huggingface.co/Kijai/LTX2.3_comfy/vae/ | ~208MB |
| 7 | ltx-2.3-spatial-upscaler-x2-1.1.safetensors | models/latent_upscale_models/ | huggingface.co/Lightricks/LTX-2.3/ | ~996MB |

Total estimado: ~38GB

---

## Custom Nodes necessarios

| Node | Pacote | Pra que |
|------|--------|---------|
| VAELoaderKJ | ComfyUI-KJNodes | Carrega VAEs do Kijai (nativo nao funciona!) |
| ImageResizeKJv2 | ComfyUI-KJNodes | Resize com divisible_by=32 |
| LTXVImgToVideoInplace | ComfyUI-LTXVideo | I2V core |
| LTXVPreprocess | ComfyUI-LTXVideo | Preprocessamento da imagem |
| LTXVLatentUpsampler | ComfyUI-LTXVideo | Upscale latent stage 2 |
| TextGenerateLTX2Prompt | ComfyUI-LTXVideo | Prompt enhancement (opcional) |
| CreateVideo/SaveVideo | ComfyUI-LTXVideo | Output |
| Fast Groups Muter | rgthree-comfy | Muta/ativa grupos (util) |
| ComfyMathExpression | ComfyMath | Calculo de dimensoes |
| ComfySwitchNode | ComfyUI-Easy-Use ou similar | Switch censura/enhance |
| PreviewAny | ?? | Preview de texto |

### Instalar:
```bash
cd custom_nodes
git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
git clone https://github.com/kijai/ComfyUI-KJNodes.git
git clone https://github.com/rgthree/rgthree-comfy.git
git clone https://github.com/evanspearman/ComfyMath.git
git clone https://github.com/SethRobinson/comfyui-workflow-to-api-converter-endpoint.git
```

---

## Parametros do workflow (NAO MEXER)

| Parametro | Valor | Node |
|-----------|-------|------|
| CFG Stage 1 | 1 | CFGGuider [316] |
| CFG Stage 2 | 1 | CFGGuider [286] |
| Sampler Stage 1 | euler_ancestral_cfg_pp | KSamplerSelect [294] |
| Sampler Stage 2 | euler_cfg_pp | KSamplerSelect [284] |
| Sigmas Stage 1 | 1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0 | ManualSigmas [308] |
| Sigmas Stage 2 | 0.85, 0.7250, 0.4219, 0.0 | ManualSigmas [285] |
| img_compression | 18 | LTXVPreprocess [292] |
| I2V strength | 1.0 | LTXVImgToVideoInplace [299] |
| I2V strength stage 2 | 1.0 | LTXVImgToVideoInplace [291] |
| Resolucao base | 768x512 → upscale 2x | EmptyLTXVLatentVideo [298] |
| Frames | 241 (10s) ou 97 (4s) | PrimitiveInt [303] |
| FPS | 24 | PrimitiveInt [302] |
| Width input | 1280 | PrimitiveInt [314] |
| Height input | 720 | PrimitiveInt [301] |
| Seed stage 1 | random | RandomNoise [282] |
| Seed stage 2 | 42, fixed | RandomNoise [281] |
| VAE decode | 256/64/592/4 | VAEDecodeTiled [321] |
| LoRA abliterated | strength 1.0 | LoraLoader [343] |

---

## O que MUDAR pra nosso teste

| O que | De | Para |
|-------|-----|------|
| Imagem | z-image-turbo_00056_.png | img1.png |
| Prompt | two persons fighting in stadium | Nosso prompt de soldados |
| Negative | (ja esta no workflow) | Manter |
| Width | 1280 | **720** (vertical) |
| Height | 720 | **1280** (vertical) |
| Frames | 241 | **121** (5s, pra teste rapido) |
| Enhance prompt | True | **False** (pra teste rapido, é lento) |

NAO mudar: CFG, samplers, sigmas, strength, modelos, VAE settings.

---

## Procedimento de execucao

1. Criar pod RTX 5090
2. Instalar custom nodes
3. Baixar 7 modelos nas pastas corretas
4. Iniciar ComfyUI
5. Usar converter endpoint pra executar workflow via API
6. OU carregar workflow na interface web
7. Trocar imagem + prompt
8. Rodar
9. Baixar resultado
10. Desligar pod
