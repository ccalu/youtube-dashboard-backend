# LTX 2.3 — Estudo Definitivo para Cinema Quality

> Data: 2026-03-25
> Baseado em: docs oficiais Lightricks, Civitai, HuggingFace, Reddit, blogs tecnicos
> Objetivo: resolver os problemas de qualidade (corpos fundindo, visual emborrachado, ghosting)

---

## DIAGNOSTICO DOS PROBLEMAS

### Problema 1: Corpos se fundindo na luta
- CAUSA: Poucos steps (8 com distilled LoRA) + falta de controle estrutural
- SOLUCAO: IC-LoRA Union Control (depth + canny) para forcar separacao dos corpos

### Problema 2: Visual emborrachado/plastico
- CAUSA: motion_weight alto demais + falta de termos de textura no prompt
- SOLUCAO: motion_weight 0.4-0.6 + prompt com texturas de alta frequencia + film grain pos-VAE

### Problema 3: Ghosting e flicker no fundo
- CAUSA: Poucos steps + modelo distilled tentando gerar cena complexa
- SOLUCAO: Modelo DEV completo com mais steps (25-50) ou Two-Stage com upscale latent

### Problema 4: Range dinamico chapado
- CAUSA: VAE ou falta de prompt de iluminacao
- SOLUCAO: Prompt com volumetric lighting + usar spatial upscaler v1.1 (nao v1.0)

---

## PIPELINE DEFINITIVO — TWO-STAGE COM IC-LORA

Baseado no workflow oficial Lightricks + IC-LoRA + melhorias da comunidade:

```
STAGE 1 — Geracao Base (544x960 vertical)
  ├── CheckpointLoaderSimple → ltx-2.3-22b-dev-fp8.safetensors
  ├── LoraLoaderModelOnly → distilled-lora-384 (strength 0.5)
  ├── LTXICLoRALoaderModelOnly → union-control-ref0.5 (strength 1.0)
  ├── LTXAVTextEncoderLoader → gemma heretic v2 fp8
  ├── CLIPTextEncode → prompt positivo (camera → acao → textura)
  ├── CLIPTextEncode → prompt negativo
  ├── LoadImage → img1.png
  ├── LTXVPreprocess → img_compression=18
  ├── LTXVImgToVideoConditionOnly → strength=0.7
  ├── DepthAnythingV2Preprocessor → extrai mapa de profundidade
  ├── LTXAddVideoICLoRAGuide → aplica controle estrutural (strength=1.0)
  ├── EmptyLTXVLatentVideo → 544x960, 121 frames
  ├── LTXVEmptyLatentAudio → 121 frames, 24fps
  ├── LTXVConcatAVLatent → junta audio+video
  ├── LTXVConditioning → fps=24
  ├── CFGGuider → cfg=1.0 (com LoRA distilled)
  ├── KSamplerSelect → euler_ancestral_cfg_pp
  ├── ManualSigmas → "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
  ├── RandomNoise → seed=42
  └── SamplerCustomAdvanced → gera video base

STAGE 2 — Upscale + Refinamento
  ├── LTXVSeparateAVLatent → separa video de audio
  ├── LatentUpscaleModelLoader → spatial-upscaler-x2-1.1 (USAR v1.1!)
  ├── LTXVLatentUpsampler → 2x resolucao no espaco latent
  ├── LTXVImgToVideoConditionOnly → recondiciona (strength=1.0)
  ├── LTXVConcatAVLatent → rejunta audio+video
  ├── CFGGuider → cfg=1.0
  ├── KSamplerSelect → euler_cfg_pp (nota: sem _ancestral no stage 2)
  ├── ManualSigmas → "0.85, 0.7250, 0.4219, 0.0" (3 steps refinamento)
  ├── RandomNoise → seed=43
  └── SamplerCustomAdvanced → refina detalhes

DECODE + POS-PROCESSAMENTO
  ├── LTXVSeparateAVLatent → separa
  ├── VAEDecodeTiled → tile_size=512, overlap=64
  ├── LTXVAudioVAEDecode → decodifica audio
  ├── (opcional) LTXVFilmGrain → adiciona grao de filme
  ├── CreateVideo → fps=24
  └── SaveVideo
```

---

## MODELOS NECESSARIOS (ATUALIZADO)

### O que ja temos:
- [x] ltx-2.3-22b-dev-fp8.safetensors (28GB) — checkpoint
- [x] gemma-3-12b-it-heretic-v2_fp8.safetensors (13GB) — text encoder
- [x] ltx-2.3-22b-distilled-lora-384.safetensors (7.1GB) — LoRA
- [x] LTX2_video_vae_bf16.safetensors (2.3GB) — video VAE
- [x] LTX2_audio_vae_bf16.safetensors (208MB) — audio VAE
- [x] ltx-2.3-spatial-upscaler-x2-1.0.safetensors (1.1GB) — upscaler

### O que FALTA baixar:
- [ ] ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors (~654MB) — IC-LoRA
- [ ] ltx-2.3-spatial-upscaler-x2-1.1.safetensors (996MB) — upscaler ATUALIZADO (v1.1 hotfix)

### Opcional (futuro):
- [ ] ltx-2.3-temporal-upscaler-x2-1.0.safetensors (262MB) — dobra framerate
- [ ] Camera LoRAs (static, dolly-in, etc.) — controle de camera
- [ ] IC-LoRA Motion Track (~327MB) — tracking de movimento

---

## PARAMETROS DEFINITIVOS

### Com LoRA Distilled (modo rapido, 8 steps):
| Parametro | Valor | Fonte |
|-----------|-------|-------|
| CFG | 1.0 | Lightricks oficial (LoRA embute guidance) |
| Sampler | euler_ancestral_cfg_pp | Todos os workflows oficiais |
| Sigmas Stage 1 | "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0" | Lightricks |
| Sigmas Stage 2 | "0.85, 0.7250, 0.4219, 0.0" | Lightricks |
| img_compression | 18 | Lightricks + RuneXX |
| I2V strength | 0.7 | Lightricks |
| IC-LoRA strength | 1.0 (nunca menor!) | Lightricks docs |
| LoRA distilled | 0.5 | Lightricks |
| Frames | 121 (5s @ 24fps) | Todos |
| Resolucao Stage 1 | 544x960 (vertical) | Divisivel por 32 |

### Sem LoRA Distilled (modo qualidade maxima, 25-50 steps):
| Parametro | Valor | Fonte |
|-----------|-------|-------|
| CFG | 3.0-3.5 (sweet spot) | CrePal, LTX docs |
| Sampler | euler_ancestral_cfg_pp ou dpmpp_2m | CrePal, NVIDIA guide |
| Scheduler | LTXVScheduler (25-50 steps) | LTX docs |
| motion_weight | 0.5-0.6 | CrePal (acima de 0.75 = emborrachado!) |
| Cross-modal | 1.5-2.0 | CrePal (acima de 2.0 = artefatos) |

---

## PROMPT STRUCTURE (Hierarquia Gemma 3)

O Gemma 3 12B le o prompt como ROTEIRO, nao como tags.
Ordem: CAMERA → ACAO → TEXTURA → ATMOSFERA

### Prompt Positivo (img1 — soldados lutando):
```
Handheld 35mm film cinematography, shaky close-up tracking shot.
Two soldiers locked in brutal hand-to-hand combat, grappling
intensely in deep snow. The soldier on the left throws a heavy
right hook connecting with the other's jaw. The second soldier
blocks and counters with a knee strike. Their bodies strain with
realistic weight and physical impact, boots kicking up snow.
Thick black smoke billows from burning ruins behind them, embers
drifting through the air. Tank turret slowly rotating in the
background. High-frequency detail on weathered wool uniforms,
scratched metal helmets, frost on fabric. Cinematic volumetric
lighting, overcast winter sky, deep shadows in the snow. Raw
Kodak film stock, heavy grain, natural motion blur,
photorealistic, hyper-detailed textures.
```

### Prompt Negativo:
```
smooth skin, plastic, synthetic, cartoon, anime, CGI, 3D render,
airbrushed, soft focus, low detail, blurry, watermark, text,
logo, worst quality, compression artifacts
```

---

## WORKFLOWS VALIDADOS (TOP 3)

### 1. Lightricks Two-Stage + IC-LoRA (RECOMENDADO)
- Fonte: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/
- Tipo: Two-Stage com upscale latent
- Qualidade: Maxima
- IC-LoRA: Union Control para separacao de corpos
- Status: Workflow oficial + IC-LoRA workflow oficial

### 2. VideoFlow (Civitai)
- URL: civitai.com/models/1815300
- Rating: 5.0/5 (159 reviews)
- Diferencial: Color correction integrada (resolve o visual plastico)
- Tipo: Single-stage + pixel upscale

### 3. MrXin Eros (Civitai)
- URL: civitai.com/models/2488266
- Diferencial: 3-step optimizado para 12GB VRAM
- Tipo: 3-pass (elimina o visual emborrachado)

---

## CUSTOM NODES ESSENCIAIS

### Obrigatorios:
- ComfyUI-LTXVideo — nodes LTX oficiais + IC-LoRA
- ComfyUI-VideoHelperSuite — VHS_VideoCombine
- ComfyUI-KJNodes — utilities
- comfyui-workflow-to-api-converter-endpoint — conversao de workflows

### Para IC-LoRA:
- ComfyUI-DepthAnythingV2 — gera mapas de profundidade automaticamente
- Nao precisa de node extra — IC-LoRA nodes vem com ComfyUI-LTXVideo

### Para pos-processamento:
- LTXVFilmGrain (vem com ComfyUI-LTXVideo) — grao de filme
- Color correction node — correcao de cor

### Opcionais (pra qualidade maxima):
- RES4LYF (ClownSampler_Beta) — sampler avancado

---

## UPSCALERS — DETALHES

| Modelo | Versao | Tamanho | Uso |
|--------|--------|---------|-----|
| spatial-upscaler-x2-1.0 | v1.0 (DEPRECATED) | 996MB | NAO USAR |
| spatial-upscaler-x2-1.1 | v1.1 (HOTFIX) | 996MB | USAR ESTE |
| spatial-upscaler-x1.5-1.0 | v1.0 | 1.09GB | Alternativa menor |
| temporal-upscaler-x2-1.0 | v1.0 | 262MB | Dobra FPS (aplicar DEPOIS do spatial) |

IMPORTANTE: Usar v1.1 do spatial upscaler. v1.0 tem bug documentado.
Ordem: spatial PRIMEIRO, temporal DEPOIS.

---

## IC-LORA — COMO FUNCIONA

### O que resolve:
- Corpos se fundindo → Depth IC-LoRA mantem volumes separados
- Anatomia quebrando → Pose IC-LoRA preserva esqueleto
- Bordas sumindo → Canny IC-LoRA preserva contornos

### Union IC-LoRA (recomendado):
- Combina Depth + Canny + Pose num modelo so
- Menor VRAM que usar 3 separados
- Strength SEMPRE 1.0 (menor causa bleed-through)

### Pipeline com IC-LoRA:
1. LoadImage → DepthAnythingV2Preprocessor → extrai profundidade
2. LTXICLoRALoaderModelOnly → carrega IC-LoRA
3. LTXAddVideoICLoRAGuide → aplica controle (strength=1.0)
4. Prompt foca em APARENCIA (IC-LoRA cuida da estrutura)

### Regras:
- IC-LoRA + Distilled LoRA juntas: SIM, funciona
- Ordem: carregar Distilled LoRA PRIMEIRO, IC-LoRA DEPOIS
- Usar UM tipo de controle por vez (Depth OU Canny OU Pose)
- VRAM adicional: +2-3 GB

---

## FONTES PRIMARIAS

### Documentacao Oficial:
- LTX 2.3 Model Card: huggingface.co/Lightricks/LTX-2.3
- ComfyUI Workflow Guide: ltx.io/model/model-blog/comfyui-workflow-guide
- IC-LoRA Guide: ltx.io/model/model-blog/how-to-use-ic-lora-in-ltx-2
- LTX Docs: docs.ltx.video/open-source-model/usage-guides/ic-lo-ra

### Comunidade:
- CrePal Best Settings: crepal.ai/blog/aivideo/blog-ltx-2-best-settings-comfyui-2026/
- CrePal Full vs Distilled: crepal.ai/blog/aivideo/blog-ltx-2-full-vs-distilled-model/
- WaveSpeed LTX 2.3: wavespeed.ai/blog/posts/ltx-2-3-whats-new-2026/
- Awesome LTX-2: github.com/wildminder/awesome-ltx2

### Workflows:
- Lightricks GitHub: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/
- VideoFlow Civitai: civitai.com/models/1815300
- MrXin Eros Civitai: civitai.com/models/2488266
- IC-LoRA Workflow: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/LTX-2.3_ICLoRA_Union_Control_Distilled.json

### Modelos:
- IC-LoRA Union: huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control
- Kijai LTX2.3: huggingface.co/Kijai/LTX2.3_comfy
- Upscalers: huggingface.co/Lightricks/LTX-2.3 (pasta do repo)
