# Plano de Testes — LTX 2.3 I2V (FINAL)

> Data: 2026-03-25
> Status: PRONTO PARA EXECUTAR (aguardando autorizacao)

---

## O que foi preparado

### 3 Workflows adaptados para nossos modelos + vertical (720x1280)

| Arquivo | Base | Modelo | Sampler | Stages |
|---------|------|--------|---------|--------|
| TEST_A_two_stage_vertical.json | Lightricks oficial | DEV FP8 + LoRA 0.5 | euler_ancestral_cfg_pp + euler_cfg_pp | 2 (gera + upscale) |
| TEST_B_single_stage_vertical.json | Lightricks oficial | DEV FP8 + LoRA dual (0.5+0.2) | ClownSampler_Beta | 1 (dual sampler) |
| TEST_C_runexx_vertical.json | RuneXX comunidade | DEV FP8 + LoRA 0.6 | euler_ancestral_cfg_pp | 1 (single pass) |

### Adaptacoes feitas em cada workflow:
- Checkpoint: ltx-2.3-22b-dev.safetensors → ltx-2.3-22b-dev-fp8.safetensors
- Gemma: comfy_gemma_3_12B_it.safetensors → gemma_3_12B_it_heretic_fp8.safetensors
- LoRA path: removido subpasta ltxv/ltx2/
- VAEs: nomes Kijai KJ → nomes LTXV2_comfy
- Resolucao: landscape → vertical (544x960)
- Imagem: example.png → img1.png
- Prompt: tea ceremony → soldados lutando na neve

### Parametros CORRETOS (estudados e confirmados):
- CFG: 1.0 (TODOS os workflows usam 1.0 com LoRA distilled)
- Sampler: euler_ancestral_cfg_pp (NAO euler generico)
- Sigmas: ManualSigmas fixos (NAO LTXVScheduler)
- img_compression: 18
- I2V strength: 0.7
- Frames: 121 (5s @ 24fps)

---

## Modelos necessarios no pod

| Modelo | Tamanho | Path no ComfyUI |
|--------|---------|-----------------|
| ltx-2.3-22b-dev-fp8.safetensors | 28 GB | models/checkpoints/ |
| gemma_3_12B_it_heretic_fp8.safetensors | 12 GB | models/text_encoders/ |
| ltx-2.3_text_projection_bf16.safetensors | ~500 MB | models/text_encoders/ |
| ltx-2.3-22b-distilled-lora-384.safetensors | 7.1 GB | models/loras/ |
| ltx-2.3-spatial-upscaler-x2-1.0.safetensors | 1.1 GB | models/latent_upscale_models/ |
| LTX2_video_vae_bf16.safetensors | 2.3 GB | models/vae/ |
| LTX2_audio_vae_bf16.safetensors | 208 MB | models/vae/ |
| **TOTAL** | **~51 GB** | |

## Nodes necessarios

- ComfyUI-LTXVideo (Lightricks)
- ComfyUI-VideoHelperSuite (VHS)
- RES4LYF (ClownSampler_Beta — para TEST B)
- ComfyUI-KJNodes

---

## Procedimento de execucao

1. Criar pod RTX 5090 ($0.69/hr)
2. Rodar setup_pod_complete.sh (instala tudo, ~10-15 min)
3. Upload imagem img1.png
4. Upload 3 workflows TEST_A/B/C
5. Executar cada workflow via API do ComfyUI
6. Anotar tempo de cada teste
7. Baixar resultados
8. Desligar pod

Tempo estimado total: ~30-40 min
Custo estimado: ~$0.40 (~R$2.20)

---

## Riscos identificados

1. **Gemma heretic FP8 pode nao funcionar com DualCLIPLoader (TEST C)**
   - Mitigacao: se falhar, usar LTXAVTextEncoderLoader no lugar

2. **Resolucao 544x960 pode nao ser suportada**
   - Mitigacao: testar 720x1280 como fallback (ambas divisiveis por 32)

3. **Modelo DEV FP8 pode se comportar diferente do BF16 original**
   - Mitigacao: os workflows originais usam BF16, nos usamos FP8. Diferenca minima segundo docs.

4. **ClownSampler_Beta (TEST B) pode ter bug com audio**
   - Mitigacao: TEST A e C nao usam ClownSampler, servem de controle

---

## Estrutura de arquivos

```
_development/runpod/
├── docs/
│   ├── LTX23_WORKFLOW_STUDY.md          (estudo dos erros anteriores)
│   ├── LTX23_WORKFLOWS_COMPARATIVO.md   (comparativo dos 5 workflows)
│   ├── LTX23_WORKFLOW_FINAL.md          (analise final dos parametros)
│   ├── PLANO_TESTES_FINAL.md            (este documento)
│   └── ... (docs anteriores)
├── scripts/
│   ├── setup_pod_complete.sh            (setup automatico do pod)
│   └── ... (scripts anteriores)
├── workflows/
│   ├── TEST_A_two_stage_vertical.json   (Lightricks Two-Stage adaptado)
│   ├── TEST_B_single_stage_vertical.json (Lightricks Single-Stage adaptado)
│   ├── TEST_C_runexx_vertical.json      (RuneXX adaptado)
│   ├── lightricks_two_stage.json        (original)
│   ├── official_lightricks_single_stage.json (original)
│   ├── runexx_single_pass.json          (original)
│   └── ... (outros originais)
└── test_results/
    └── ... (resultados anteriores)
```
