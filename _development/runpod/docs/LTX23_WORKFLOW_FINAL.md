# LTX 2.3 — Analise Final dos Workflows I2V

> Data: 2026-03-25
> Analise detalhada dos workflows oficiais e comunidade

---

## DESCOBERTA CRITICA

Todos os 3 workflows (Lightricks oficial, RuneXX, Two-Stage) usam:
- **CFG = 1.0** (NAO 3.0 ou 4.0 como eu estava usando!)
- **ManualSigmas** (NAO LTXVScheduler!)
- **euler_ancestral_cfg_pp** (NAO euler!)
- **LoRA distilled** aplicada mesmo no modelo DEV

O CFG=1.0 eh o padrao porque a LoRA distilled ja "embute" o guidance.
Quando eu usava CFG=3.0-5.0 estava DUPLICANDO o guidance = psicodelico.

---

## Os 3 Workflows para Teste

### TESTE A — Lightricks Two-Stage (maior qualidade)

```
Pipeline:
  LoadImage → Resize(1536 longer edge, lanczos)
  → LTXVPreprocess(img_compression=18)
  → LTXVImgToVideoConditionOnly(strength=0.7)

  CheckpointLoaderSimple(ltx-2.3-22b-dev-fp8)
  → LoraLoaderModelOnly(distilled-lora-384, strength=0.5)
  → LTXAVTextEncoderLoader(gemma + checkpoint)

  CLIPTextEncode(positive) + CLIPTextEncode(negative)

  EmptyLTXVLatentVideo(960x544, 121 frames)
  LTXVEmptyLatentAudio(97, 25fps)
  → LTXVConcatAVLatent
  → LTXVConditioning(fps=24)

  STAGE 1 — Geracao base:
    CFGGuider(cfg=1)
    KSamplerSelect(euler_ancestral_cfg_pp)
    ManualSigmas("1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0")
    RandomNoise(seed=42)
    → SamplerCustomAdvanced

  STAGE 2 — Upscale latent:
    LTXVSeparateAVLatent (separa video de audio)
    LatentUpscaleModelLoader(spatial-upscaler-x2)
    LTXVLatentUpsampler
    LTXVImgToVideoConditionOnly(strength=1.0) ← recondiciona na resolucao alta
    LTXVConcatAVLatent (rejunta)
    CFGGuider(cfg=1)
    KSamplerSelect(euler_cfg_pp) ← nota: euler_cfg_pp no stage 2, nao ancestral
    ManualSigmas("0.85, 0.7250, 0.4219, 0.0") ← so 3 steps no refinamento
    RandomNoise(seed=43)
    → SamplerCustomAdvanced

  DECODE:
    LTXVSeparateAVLatent
    VAEDecodeTiled(512, 64, 512, 4)
    LTXVAudioVAEDecode
    CreateVideo(fps=30)
    SaveVideo
```

Modelos necessarios:
- ltx-2.3-22b-dev-fp8.safetensors (checkpoint)
- comfy_gemma ou gemma heretic fp8 (text encoder)
- ltx-2.3-22b-distilled-lora-384.safetensors (LoRA)
- ltx-2.3-spatial-upscaler-x2-1.0.safetensors (upscaler)
- Video VAE + Audio VAE

Nodes necessarios:
- Todos nativos do ComfyUI + ComfyUI-LTXVideo
- NAO precisa de ClownSampler/RES4LYF!
- NAO precisa de KJNodes extras

### TESTE B — RuneXX Single Pass (mais simples)

```
Pipeline:
  LoadImage → ImageResizeKJv2(736x1280, nearest-exact, divisible by 32)
  → LTXVPreprocess(img_compression=18)
  → LTXVImgToVideoInplace(strength=0.7)

  UNETLoader(distilled_fp8_scaled) ou CheckpointLoaderSimple
  DualCLIPLoader(gemma + text_projection, type=ltxv)

  CLIPTextEncode(positive) + CLIPTextEncode(negative)

  EmptyLTXVLatentVideo(704x512, 121 frames)
  LTXVEmptyLatentAudio(121, 24fps)
  → LTXVConcatAVLatent
  → LTXVConditioning(fps=24)

  SINGLE PASS:
    CFGGuider(cfg=1)
    KSamplerSelect(euler_ancestral_cfg_pp)
    ManualSigmas("1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0")
    RandomNoise(seed=43)
    → SamplerCustomAdvanced

  DECODE:
    LTXVSeparateAVLatent
    VAEDecodeTiled(512, 64)
    LTXVAudioVAEDecode
    VHS_VideoCombine(24fps, h264-mp4)
```

Modelos necessarios:
- ltx-2.3-22b-distilled_transformer_only_fp8 ou checkpoint distilled
- gemma_3_12B_it_fpmixed + ltx-2.3_text_projection_bf16 (DualCLIPLoader)
- Video VAE + Audio VAE

### TESTE C — Lightricks Single-Stage (oficial completo)

Mesmo que ja analisei antes — usa ClownSampler_Beta + MultimodalGuider.
Este eh o mais complexo e requer RES4LYF.
Vou tentar carregar o JSON direto no ComfyUI ao inves de recriar via API.

---

## PARAMETROS CORRETOS CONFIRMADOS

| Parametro | Valor CORRETO | O que eu usava (ERRADO) | Fonte |
|-----------|--------------|------------------------|-------|
| CFG | **1.0** | 3.0-5.0 | Todos os workflows |
| Sampler | **euler_ancestral_cfg_pp** | euler, euler_ancestral | Todos os workflows |
| Sigmas | **Manual 8 valores** | LTXVScheduler | Todos os workflows |
| img_compression | **18** | 35 | Lightricks + RuneXX |
| I2V strength | **0.7** | 0.55-0.85 | Lightricks + RuneXX |
| LoRA | **distilled-lora (0.5)** | nenhuma ou dupla | Two-Stage |
| Frames | **121** | 81 ou 161 | Todos |
| Seed | **42 ou 43** | 42 | Padrao |

### Sigmas (9 valores = 8 steps):
```
1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0
```

### Sigmas Stage 2 upscale (4 valores = 3 steps):
```
0.85, 0.7250, 0.4219, 0.0
```

---

## ADAPTACAO PARA VERTICAL (720x1280)

LTX 2.3 suporta vertical nativo. Mudancas:
- EmptyLTXVLatentVideo: width=720, height=1280 (ao inves de 960x544)
- Resize image: ajustar para 1280 no lado mais longo
- Frames: manter 121 (5s @ 24fps)
- Tudo mais fica igual

Para Two-Stage:
- Stage 1: 544x960 (vertical pequeno) ou 720x1280 direto
- Stage 2: upscale x2 se necessario

---

## POR QUE MEUS TESTES ANTERIORES FALHARAM

1. **CFG 3.0-5.0** → devia ser 1.0 (com LoRA distilled, CFG ja esta embutido)
2. **Sem LoRA distilled** → essencial ate no modelo DEV
3. **LTXVScheduler** → devia usar ManualSigmas com valores fixos
4. **euler** → devia ser euler_ancestral_cfg_pp
5. **KSampler generico** → devia ser SamplerCustomAdvanced + CFGGuider
6. **img_compression=35** → devia ser 18
7. **Sem LTXVConditioning** → node que define o fps do video
8. **Sem audio latent** → precisa de EmptyLatentAudio + ConcatAVLatent
9. **161 frames** → padrao eh 121 (5s)
10. **Sem resize da imagem** → precisa resize antes do preprocess

---

## PLANO DE TESTES (quando Marcelo autorizar)

Todos os testes com a MESMA imagem (img1.png), MESMO prompt, 720x1280, 121 frames.

| Teste | Workflow | Modelo | Estimativa tempo |
|-------|----------|--------|-----------------|
| A | Two-Stage | DEV + LoRA | ~5-8 min |
| B | Single Pass | Distilled FP8 | ~2-3 min |
| C | Single-Stage oficial | DEV + LoRA + ClownSampler | ~4-6 min |

Resultado esperado: videos de ~5s com animacao REAL, sem fantasmas, sem psicodelico.
