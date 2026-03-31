# LTX 2.3 DEV — Estudo Completo do Workflow Oficial

> Data: 2026-03-25
> Baseado no workflow oficial: LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json
> Fonte: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/

---

## Pipeline Oficial Completo (44 nodes)

O workflow oficial da Lightricks eh MUITO mais complexo do que eu estava fazendo.
Ele usa um sistema de DUAL SAMPLER com audio+video separados.

### Estrutura Real do Pipeline

```
ENTRADA:
  LoadImage → ResizeImageMaskNode (scale longer dimension, 1536, lanczos)
      ↓
  LTXVPreprocess (img_compression=18, NAO 35!)
      ↓
  LTXVImgToVideoConditionOnly (strength=0.7, bypass=False)

MODELOS:
  CheckpointLoaderSimple (ltx-2.3-22b-dev.safetensors)
      ↓
  LoraLoaderModelOnly x2 (distilled-lora-384 at 0.5 e 0.2)
      ↓
  LTXAVTextEncoderLoader (comfy_gemma_3_12B_it + checkpoint)

TEXTO:
  CLIPTextEncode (positive prompt)
  CLIPTextEncode (negative: "pc game, console game, video game, cartoon, childish, ugly")

LATENTS:
  EmptyLTXVLatentVideo (960x544, 121 frames)
  LTXVEmptyLatentAudio (97 tokens, 25fps)
  LTXVConcatAVLatent (junta audio+video latents)

CONDITIONING:
  LTXVConditioning (fps=24)

SAMPLING - SISTEMA DUAL:
  Passo 1 (ClownSampler_Beta - "fast preview"):
    KSamplerSelect: euler_ancestral_cfg_pp
    ManualSigmas: "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0" (8 steps)
    GuiderParameters AUDIO: cfg=7, cfg_start=1, perp_neg=True, neg_scale=0.7
    GuiderParameters VIDEO: cfg=3, cfg_start=1, perp_neg=True, neg_scale=0.9
    MultimodalGuider: steps=28
    ClownSampler_Beta: eta=0.25, noise_type=exponential/res_2s, seed=94
    → SamplerCustomAdvanced

  Passo 2 (CFGGuider - "full quality"):
    CFGGuider: cfg=1
    RandomNoise: seed=43
    KSamplerSelect: euler_ancestral_cfg_pp
    → SamplerCustomAdvanced

DECODE:
  LTXVSeparateAVLatent (separa audio e video)
  VAEDecodeTiled (tile_size=512, overlap=64)
  LTXVAudioVAEDecode
  CreateVideo (fps=30)
  SaveVideo
```

---

## ERROS CRITICOS QUE EU ESTAVA COMETENDO

### 1. Nao usava LoRA distilled
O workflow oficial carrega a LoRA distilled DUAS VEZES:
- Primeiro com strength 0.5
- Depois com strength 0.2
Isso eh ESSENCIAL para qualidade. Sem a LoRA, o DEV model gera lixo.

### 2. img_compression errado
- Eu usava: 35 (default do node)
- Oficial usa: 18
- Valor alto demais = degrada a imagem de entrada = fantasmas/dispersao

### 3. Nao usava LTXVImgToVideoConditionOnly
- Eu usava: LTXVImgToVideo (node errado!)
- Oficial usa: LTXVImgToVideoConditionOnly (strength=0.7)
- Sao nodes DIFERENTES. O ConditionOnly so gera o conditioning, nao o latent

### 4. Nao usava EmptyLTXVLatentVideo + LTXVConcatAVLatent
- Eu deixava o LTXVImgToVideo gerar o latent
- Oficial: cria latent vazio + audio vazio, concatena, e usa como base
- Isso eh FUNDAMENTAL para o pipeline dual funcionar

### 5. Nao usava MultimodalGuider
- Eu usava: CFGGuider simples
- Oficial usa: MultimodalGuider com GuiderParameters separados pra audio e video
- VIDEO cfg=3, AUDIO cfg=7

### 6. Nao usava ClownSampler_Beta
- Eu usava: KSampler generico ou SamplerCustomAdvanced direto
- Oficial usa: ClownSampler_Beta como primeiro passo
- Com eta=0.25, noise_type=exponential/res_2s

### 7. Sistema de DUAL SAMPLING
- O workflow tem DOIS SamplerCustomAdvanced em sequencia
- Primeiro: ClownSampler_Beta + MultimodalGuider (gera base)
- Segundo: CFGGuider cfg=1 (refina)
- Eu so usava UM sampler

### 8. Resolucao errada
- Eu usava: 720x1280 direto
- Oficial usa: 960x544 (resolucao menor, nao vertical!)
- Com resize da imagem para 1536 no lado mais longo
- Depois upscale se necessario

### 9. Frame count
- Eu usava: 161 frames
- Oficial usa: 121 frames (~5s a 24fps)

### 10. Negative prompt
- Eu usava: lista longa de termos
- Oficial usa: "pc game, console game, video game, cartoon, childish, ugly"
- Mais curto e especifico

---

## PARAMETROS CORRETOS PARA DEV I2V

| Parametro | Valor Oficial | O que eu usava (ERRADO) |
|-----------|---------------|------------------------|
| img_compression | 18 | 35 |
| I2V node | LTXVImgToVideoConditionOnly | LTXVImgToVideo |
| I2V strength | 0.7 | 0.55-0.75 |
| Resolucao | 960x544 | 720x1280 |
| Frames | 121 | 161 |
| Sampler | ClownSampler_Beta + SamplerCustomAdvanced dual | KSampler |
| CFG video | 3 (via GuiderParameters) | 3.0-5.0 (via CFGGuider) |
| CFG audio | 7 (via GuiderParameters) | nenhum |
| LoRA | distilled-lora-384 (0.5 + 0.2) | nenhuma |
| Scheduler | ManualSigmas (8 valores) | LTXVScheduler |
| Sampler name | euler_ancestral_cfg_pp | euler / euler_ancestral |
| Negative | "pc game, console game, video game, cartoon, childish, ugly" | lista longa |

---

## PROBLEMA: Workflow usa nodes que requerem ClownSampler_Beta

O ClownSampler_Beta vem do pacote RES4LYF. Precisa instalar:
```bash
cd custom_nodes
git clone https://github.com/ClownsharkBatwing/RES4LYF.git
pip install -r RES4LYF/requirements.txt
```

## PROBLEMA: Workflow usa LoRA distilled no modelo DEV

Isso parece contradditorio mas faz sentido:
- O modelo DEV eh o base (full quality)
- A LoRA distilled eh aplicada em CIMA do DEV para acelerar
- Com LoRA 0.5 + 0.2, voce tem ~70% da aceleracao do distilled
- Mas mantem a qualidade do DEV como base

## PROBLEMA: Resolucao 960x544 nao eh vertical

O workflow oficial gera em LANDSCAPE (960x544). Para Shorts verticais
precisamos adaptar para portrait. Opcoes:
- Inverter: 544x960 (mas pode nao ser suportado)
- Usar 720x1280 mas com os parametros corretos
- Gerar em landscape e croppar (perde qualidade)

Preciso testar se 720x1280 funciona com os parametros corretos.

---

## PROXIMOS PASSOS

1. Montar workflow API que replica EXATAMENTE o oficial
2. Instalar RES4LYF + LoRA distilled
3. Testar primeiro em 960x544 (landscape) pra validar que funciona
4. Depois testar em resolucao vertical
5. Ajustar CFG e steps para sweet spot

---

## FONTES

- Workflow oficial: github.com/Lightricks/ComfyUI-LTXVideo/example_workflows/2.3/
- RuneXX workflows: huggingface.co/RuneXX/LTX-2.3-Workflows
- LTX docs: docs.ltx.video/open-source-model/integration-tools/comfy-ui
- ComfyUI docs: docs.comfy.org/tutorials/video/ltx/ltx-2-3
