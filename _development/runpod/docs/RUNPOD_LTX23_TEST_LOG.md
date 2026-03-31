# LTX 2.3 I2V — Log Completo de Setup e Testes

> Data: 2026-03-24
> Pod: RTX A6000 48GB VRAM | $0.33/hr | Canadá (CA)
> Tempo total de pod ligado: ~1.7 horas (~$0.56)

---

## 1. Setup Realizado

### Infraestrutura
- **CLI (runpodctl):** Instalado em `~/.runpod/runpodctl.exe`
- **API Key:** Configurada no CLI e `.env`
- **SSH Key:** `~/.runpod/ssh/RunPod-Key-Go` (RSA, gerada pelo CLI)
- **MCP Server:** Configurado em `.claude/mcp.json` (ativa na proxima sessao)
- **Network Volume:** `content_factory_ltx` 150GB em US-IL-1 (ID: ma18aq88u0)

### Modelos Instalados no Pod (disco local 150GB)
| Modelo | Tamanho | Path |
|--------|---------|------|
| ltx-2.3-22b-distilled-fp8.safetensors | 28 GB | models/checkpoints/ |
| gemma_3_12B_it_heretic_fp8.safetensors | 12 GB | models/text_encoders/ |
| gemma_3_12B_it_heretic.safetensors | 21 GB | models/text_encoders/ (NAO USAR - incompativel) |
| ltx-2.3-22b-distilled-lora-384.safetensors | 7.1 GB | models/loras/ |
| LTX2_video_vae_bf16.safetensors | 2.3 GB | models/vae/ |
| LTX2_audio_vae_bf16.safetensors | 208 MB | models/vae/ |
| ltx-2.3-spatial-upscaler-x1.5-1.0.safetensors | 1.1 GB | models/latent_upscale_models/ |
| ltx-2.3-temporal-upscaler-x2-1.0.safetensors | 250 MB | models/latent_upscale_models/ |
| **Total** | **~60 GB** | |

### Custom Nodes Instalados
- ComfyUI-LTXVideo (Lightricks oficial)
- ComfyUI-VideoHelperSuite (VHS_VideoCombine)
- ComfyUI-Manager
- ComfyUI-KJNodes
- RES4LYF (ClownSampler_Beta — necessario para workflow oficial)

### Dependencias pip instaladas
- diffusers, timm, ninja, imageio-ffmpeg, pywavelets

---

## 2. Troubleshooting — Erros Encontrados e Solucoes

### ERRO 1: Gemma BF16 (21GB) incompativel
- **Arquivo:** `gemma_3_12B_it_heretic.safetensors` (21GB, BF16)
- **Erro:** `buffer length (67692993 bytes) after offset (0 bytes) must be a multiple of element size (2)`
- **Causa:** O formato BF16 do DreamFast heretic nao e compativel com LTXAVTextEncoderLoader
- **Solucao:** Usar a versao FP8 `gemma_3_12B_it_heretic_fp8_e4m3fn.safetensors` (12GB)
- **REGRA:** Sempre usar gemma FP8, nunca BF16 do DreamFast

### ERRO 2: Gemma oficial do Google eh gated
- **Repo:** `google/gemma-3-12b-it-qat-q4_0-unquantized`
- **Erro:** 401 Unauthorized — requer aceitar termos no HuggingFace
- **Solucao:** Usar DreamFast/gemma-3-12b-it-heretic (ungated) versao FP8
- **REGRA:** Se precisar do Gemma oficial, criar conta HF e aceitar termos primeiro

### ERRO 3: VHS_VideoCombine falta parametro pingpong
- **Erro:** `Required input is missing: pingpong`
- **Causa:** Versao mais nova do VideoHelperSuite exige `pingpong` no workflow
- **Solucao:** Adicionar `"pingpong": False` nos inputs do VHS_VideoCombine
- **REGRA:** Sempre incluir pingpong no workflow

### ERRO 4: ClownSampler_Beta nao encontrado
- **Causa:** Node faz parte do pacote RES4LYF, nao vem com ComfyUI
- **Solucao:** `git clone https://github.com/ClownsharkBatwing/RES4LYF.git` em custom_nodes
- **REGRA:** Instalar RES4LYF junto com os outros custom nodes

### ERRO 5: Porta 8188 ja em uso
- **Causa:** Template ComfyUI do RunPod inicia ComfyUI automaticamente
- **Solucao:** `fuser -k 8188/tcp` antes de iniciar manualmente
- **REGRA:** Sempre matar processo existente antes de reiniciar ComfyUI

### ERRO 6: SSH timeout em scripts longos
- **Causa:** Scripts Python que demoram >2 min perdem conexao SSH
- **Solucao:** Usar `nohup python3 script.py > log.log 2>&1 &` e monitorar separadamente
- **REGRA:** Sempre rodar scripts de geracao com nohup

### ERRO 7: 4090 indisponivel globalmente
- **Causa:** Alta demanda por 4090 na Community Cloud
- **Solucao:** Usar RTX A6000 ($0.33/hr, 48GB VRAM) como alternativa
- **REGRA:** Ter fallback para A6000 ou 5090 quando 4090 nao disponivel

### ERRO 8: Network Volume nao aceita criacao em US-CA-2
- **Causa:** Datacenter US-CA-2 nao permite novos volumes (possivelmente cheio)
- **Solucao:** Criar em US-IL-1 que aceitou
- **REGRA:** Testar criacao de volume antes de assumir que funciona

---

## 3. Resultados dos Testes

### img1 — Dois soldados lutando na neve (cor)
| Teste | Tempo | Arquivo |
|-------|-------|---------|
| 8 steps, 720x1280 | **75s (1.3 min)** | img1_8steps_720p_00001.mp4 |
| 14 steps, 720x1280 | **102s (1.7 min)** | img1_14steps_720p_00001.mp4 |
| 20 steps, 720x1280 | **~140s (2.3 min)** | img1_20steps_720p_00001.mp4 |
| 14 steps, 1080x1920 | **~277s (4.6 min)** | img1_14steps_1080p_00001.mp4 |

### img2 — Lider militar com tropa (P&B)
| Teste | Tempo | Arquivo |
|-------|-------|---------|
| 8 steps, 720x1280 | **66s (1.1 min)** | img2_8steps_720p_00001.mp4 |
| 14 steps, 720x1280 | **102s (1.7 min)** | img2_14steps_720p_00001.mp4 |
| 20 steps, 720x1280 | **141s (2.4 min)** | img2_20steps_720p_00001.mp4 |
| 14 steps, 1080x1920 | **279s (4.7 min)** | img2_14steps_1080p_00001.mp4 |

### Resumo de Tempos (RTX A6000 48GB)
| Config | Tempo medio |
|--------|-------------|
| **720p, 8 steps** | **~70s (1.2 min)** |
| **720p, 14 steps** | **~102s (1.7 min)** |
| **720p, 20 steps** | **~140s (2.3 min)** |
| **1080p, 14 steps** | **~278s (4.6 min)** |

### Observacoes
- GPU: RTX A6000 (48GB) — NAO eh a 4090 (24GB) do plano original
- A 4090 deve ser ~10-20% mais rapida por ter arquitetura mais moderna
- Mas a 4090 pode ter problemas de VRAM em 1080p (24GB vs 48GB)
- 1080p demora ~2.7x mais que 720p
- Diferenca de 8 para 14 steps: ~45% mais tempo, qualidade TBD (avaliar videos)
- Diferenca de 14 para 20 steps: ~37% mais tempo

---

## 4. Workflow API Utilizado

### Nodes do pipeline I2V:
```
CheckpointLoaderSimple (ltx-2.3-22b-distilled-fp8)
    |
LTXAVTextEncoderLoader (gemma_3_12B_it_heretic_fp8)
    |
CLIPTextEncode (positive + negative prompts)
    |
LoadImage (imagem de entrada)
    |
LTXVImgToVideo (width, height, length=81 frames, strength=0.85)
    |
KSampler (steps, cfg=3.0, euler_ancestral, seed=42)
    |
VAEDecodeTiled (tile_size=512)
    |
VHS_VideoCombine (25fps, h264-mp4, crf=19)
```

### Parametros chave:
- **strength:** 0.85 (quanto a imagem original influencia)
- **cfg:** 3.0 (guidance scale)
- **sampler:** euler_ancestral
- **length:** 81 frames (~3.2s a 25fps)
- **crf:** 19 (qualidade do h264)

---

## 5. Custos Reais

| Item | Custo |
|------|-------|
| Pod A6000 (~1.7 hrs) | ~$0.56 |
| Network Volume IL-1 (150GB, mensal) | $10.50/mes |
| Volume Japao deletado | -$21/mes economia |
| **Total gasto hoje** | **~$0.56 (~R$3)** |

---

## 6. Proximos Passos

- [ ] Avaliar qualidade dos 8 videos gerados
- [ ] Definir sweet spot (steps x resolucao)
- [ ] Quando 4090 disponivel: testar com Network Volume
- [ ] Testar prompts mais detalhados / diferentes estilos
- [ ] Pipeline completo: pasta com 12 imagens → 12 clips → FFmpeg → Short

---

## 7. Comandos Uteis

### Ligar pod
```bash
runpodctl pod start 8ab8rcboikc4sv
```

### Desligar pod
```bash
runpodctl pod stop 8ab8rcboikc4sv
```

### SSH no pod
```bash
ssh -i ~/.runpod/ssh/RunPod-Key-Go root@<IP> -p <PORT>
# Ou verificar porta: runpodctl ssh info 8ab8rcboikc4sv
```

### Iniciar ComfyUI
```bash
fuser -k 8188/tcp; sleep 2
cd /workspace/runpod-slim/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch
```

### Rodar geracao com nohup
```bash
nohup python3 /workspace/script.py > /workspace/results.log 2>&1 &
```
