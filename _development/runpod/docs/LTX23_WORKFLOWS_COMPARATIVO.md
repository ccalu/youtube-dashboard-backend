# LTX 2.3 — Comparativo de Workflows I2V

> Data: 2026-03-25
> Pesquisa completa de workflows funcionais para Image-to-Video

---

## Boa noticia: LTX 2.3 suporta VERTICAL NATIVO

O modelo foi treinado com dados portrait. Nao precisa gerar landscape e croppar.
- Resolucoes verticais validas: 720x1280, 1080x1920
- Largura e altura devem ser divisiveis por 32
- Frame count divisivel por 8 + 1 (ex: 121 = 15x8+1)

---

## 5 Workflows Encontrados

### WF1: VideoFlow (Civitai) — MAIS RAPIDO
- URL: https://civitai.com/models/1815300
- Rating: 5.0/5 (159 reviews, 5498 downloads)
- Modelo: Distilled
- Resolucao: 768x1152 → upscale 1536x2304
- Frames: 81 @ 16fps
- Sampler: dpmpp_sde_gpu
- Steps: 4 (!)
- Tempo: ~12 min (RTX 4080)
- Tipo: Single-stage + upscale pixel

### WF2: Lightricks Two-Stage (GitHub) — MAIOR QUALIDADE
- URL: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/
- Modelo: DEV + LoRA distilled (0.5)
- Resolucao: 960x544 → 2x latent upscale
- Frames: 121 @ 24fps
- Sampler: euler_ancestral_cfg_pp
- Steps: 9 + 4 (two-stage)
- Tipo: Two-stage com LTXVLatentUpsampler
- Requer: RES4LYF (ClownSampler_Beta)

### WF3: Lightricks Single-Stage (GitHub) — OFICIAL REFERENCIA
- URL: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/
- Modelo: DEV + LoRA distilled dual (0.5 + 0.2)
- Resolucao: 960x544
- Frames: 121 @ 24fps
- Sampler: euler_ancestral_cfg_pp + ClownSampler_Beta
- Steps: 9 (distilled path) ou 15 (full quality path)
- CFG: VIDEO=3, AUDIO=7 (via MultimodalGuider)
- Requer: RES4LYF, ComfyUI-KJNodes, rgthree-comfy

### WF4: RuneXX Basic (HuggingFace) — MAIS SIMPLES
- URL: huggingface.co/RuneXX/LTX-2.3-Workflows
- Modelo: Distilled FP8 + LoRA (0.6)
- Resolucao: 704x512 → 1280x736 (upscale 2x)
- Frames: 121 @ 24fps
- Sampler: euler_ancestral_cfg_pp (pass1) + euler_cfg_pp (pass2)
- Steps: 8-9
- CFG: 1.0
- I2V node: LTXVImgToVideoInplace (strength=1.0)
- img_compression: 33
- Tipo: Two-pass (gerar + upscale espacial)
- NAO requer ClownSampler_Beta

### WF5: Ollama DEV/DIST (Civitai) — MAIS FEATURES
- URL: https://civitai.com/models/2318870
- Rating: 5.0/5 (109 reviews)
- Modelo: DEV ou DIST (selecionavel)
- DEV: Steps=20, CFG=3, MultiModalGuider + LTXVScheduler
- DIST: Steps=8, CFG=1, Standard Guider
- Features: Ollama prompt enhancement, RTX VSR upscale
- Tipo: Two-pass

---

## Comparativo Direto

| | VideoFlow | Two-Stage | Single-Stage | RuneXX | Ollama |
|---|---|---|---|---|---|
| Qualidade | Alta | Maxima | Muito Alta | Alta | Configuravel |
| Velocidade | Mais rapido | Lento | Medio | Rapido | Variavel |
| Complexidade | Media | Alta | Alta | Baixa | Media |
| VRAM min | 16GB | 24GB+ | 24GB+ | 12GB | 16GB+ |
| ClownSampler | Nao | Sim | Sim | Nao | Nao |
| Vertical | Sim | Adaptar | Adaptar | Adaptar | Sim |
| Audio | Opcional | Integrado | Integrado | Separado | Integrado |

---

## Os 3 Workflows que vamos testar

### TESTE A: RuneXX Basic (adaptado vertical)
Mais simples, sem ClownSampler. Bom ponto de partida.
- Modelo: Distilled FP8
- I2V: LTXVImgToVideoInplace (strength=1.0)
- img_compression: 33
- Sampler: euler_ancestral_cfg_pp
- Sigmas: 1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0
- CFG: 1.0
- Resolucao: 720x1280 (vertical direto)
- Frames: 121 (5s @ 24fps)
- Pass 2: Spatial upscaler x2

### TESTE B: Lightricks Single-Stage (adaptado vertical)
Oficial, com ClownSampler + dual LoRA + MultimodalGuider.
- Modelo: DEV + LoRA distilled (0.5 + 0.2)
- I2V: LTXVImgToVideoConditionOnly (strength=0.7)
- img_compression: 18
- Sampler: ClownSampler_Beta + SamplerCustomAdvanced dual
- CFG VIDEO: 3, AUDIO: 7
- Resolucao: 544x960 (vertical) ou 720x1280
- Frames: 121 (5s @ 24fps)

### TESTE C: Lightricks Two-Stage (adaptado vertical)
Maximo de qualidade. Gera low-res + upscale latent.
- Stage 1: 544x960, 9 steps
- Stage 2: LTXVLatentUpsampler x2 → 1088x1920, 4 steps
- Modelo: DEV + LoRA
- Tipo: Gera pequeno, upscala com qualidade

---

## Modelos necessarios para os 3 testes

### Ja temos no pod:
- [x] ltx-2.3-22b-dev-fp8.safetensors (28GB)
- [x] gemma_3_12B_it_heretic_fp8.safetensors (12GB)
- [x] LTX2_video_vae_bf16.safetensors (2.3GB)
- [x] LTX2_audio_vae_bf16.safetensors (208MB)

### Falta baixar:
- [ ] ltx-2.3-22b-distilled-lora-384.safetensors (7.1GB) — ja baixamos antes
- [ ] ltx-2.3-spatial-upscaler-x2-1.0.safetensors (~1.1GB)
- [ ] ltx-2.3-temporal-upscaler-x2-1.0.safetensors (~250MB) — opcional

### Nodes necessarios:
- [x] ComfyUI-LTXVideo
- [x] ComfyUI-VideoHelperSuite
- [ ] RES4LYF (ClownSampler_Beta) — pra testes B e C
- [x] ComfyUI-KJNodes
- [x] ComfyUI-Manager

---

## Diferencas CRITICAS entre os nodes de I2V

### LTXVImgToVideo (o que eu usava — ERRADO para DEV)
- Gera conditioning + latent ao mesmo tempo
- Funciona para distilled com KSampler
- NAO eh o node certo para o pipeline avancado

### LTXVImgToVideoInplace (RuneXX usa)
- Injeta a imagem diretamente no latent
- strength=1.0 = imagem domina completamente
- Melhor para manter a imagem original visivel
- Funciona com distilled

### LTXVImgToVideoConditionOnly (Lightricks usa)
- So gera o conditioning, nao mexe no latent
- strength=0.7 = guia suave, mais liberdade de movimento
- Melhor para animacao real (nao fica "congelado")
- Funciona com DEV + dual LoRA

---

## Parametros-chave por workflow

| Parametro | RuneXX | Lightricks Single | Lightricks Two-Stage |
|-----------|--------|-------------------|---------------------|
| img_compression | 33 | 18 | 18 |
| I2V strength | 1.0 | 0.7 | 0.7 |
| CFG | 1.0 | VIDEO=3, AUDIO=7 | 1.0 |
| Sampler | euler_ancestral_cfg_pp | ClownSampler_Beta | euler_ancestral_cfg_pp |
| Steps | 8-9 | 9+refinement | 9+4 |
| Sigmas | Manual (8 valores) | Manual (8 valores) | Manual (8+3 valores) |
| LoRA | 1x (0.6) | 2x (0.5+0.2) | 1x (0.5) |
| Resolution | 704x512→upscale | 960x544 | small→2x upscale |

---

## Fontes

- Lightricks GitHub: github.com/Lightricks/ComfyUI-LTXVideo/
- RuneXX HF: huggingface.co/RuneXX/LTX-2.3-Workflows
- VideoFlow Civitai: civitai.com/models/1815300
- Ollama Civitai: civitai.com/models/2318870
- ComfyUI docs: docs.comfy.org/tutorials/video/ltx/ltx-2-3
- LTX docs: docs.ltx.video/open-source-model/integration-tools/comfy-ui
- LTX model card: huggingface.co/Lightricks/LTX-2.3
