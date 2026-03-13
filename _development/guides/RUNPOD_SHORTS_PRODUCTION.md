# RunPod + ComfyUI — Producao de Shorts em Escala

> Estudo completo realizado em 2026-03-13
> Decisoes tomadas pelo Marcelo nesta sessao

---

## Decisoes Finais

- **Plataforma GPU:** RunPod Serverless (confiavel, templates prontos, SaladCloud descartado por pouca economia vs complexidade)
- **Modelo:** Wan 2.2 (melhor qualidade I2V open-source atual)
- **Metodo:** I2V ONLY (imagem-para-video, para consistencia visual)
- **Imagens:** NanoBanana/Flux (custo ZERO)
- **Comprar maquina:** NAO — RunPod e mais barato que eletricidade de maquina propria com otimizacoes
- **Audio:** Wan gera video MUDO — narracao vem separada (TTS ou gravada)

---

## Modelos I2V Disponiveis no ComfyUI (Ranking)

| # | Modelo | Qualidade | VRAM Min | Velocidade (4090, 5s clip) | Veredicto |
|---|--------|-----------|----------|---------------------------|-----------|
| 1 | **Wan 2.2 I2V 14B** | 10/10 | 12GB (GGUF) | ~4-5 min (c/ otimizacoes) | Melhor qualidade |
| 2 | **Wan 2.2 TI2V 5B** | 8.5/10 | 6GB (GGUF) | ~5-6 min | Melhor custo-beneficio |
| 3 | **FramePack** (Wan-based) | 9/10 | 6GB | ~4 min (5s) | Videos longos, VRAM baixa |
| 4 | **HunyuanVideo 1.5 I2V** | 9/10 | 8GB (GGUF) | ~75s (distilled) | Rapido com distilled |
| 5 | **LTX-Video 2.3** | 8.5/10 | 8GB | ~2-3 min | Mais rapido, suporta 4K |
| 6 | **CogVideoX 1.5 I2V** | 8/10 | 12GB | ~15 min | Lento, so 8fps |
| 7 | **SkyReels V2** | 8.5/10 | 15GB | Novo | Promissor, nao maduro |
| 8 | **SVD XT** | 6.5/10 | 8GB | ~2-3 min | Ultrapassado |
| 9 | **AnimateDiff** | 6/10 | 8GB | ~30-60s | 512px, qualidade baixa |

---

## Otimizacoes — O Que e SEGURO vs PERIGOSO

### SEGURO para producao (usar):

| Otimizacao | Config Segura | Speedup | Perda de Qualidade |
|------------|--------------|---------|-------------------|
| **Distilled LoRA (CausVid V2)** | 8-14 steps | ~6x | Negligivel a 8 steps, zero a 14 |
| **TeaCache** | threshold 0.3 (Retention Mode) | ~2x | Negligivel |
| **480p + Latent Upscaler** | Wan 2.2 5B upscaler | ~3x geracao | Aceitavel para Shorts mobile |

### NAO usar:

| Otimizacao | Problema |
|------------|---------|
| **SageAttention** | So 10% mais rapido, degradacao sutil + bugs em GPUs |
| **TeaCache > 0.5** | Artefatos visiveis em maos/dedos |
| **TeaCache + LoRA distilled JUNTOS** | Fica embasado! Competem pela mesma margem |
| **Menos de 6 steps** | Perda significativa |
| **Modelo base (sem LoRA) abaixo de 20 steps** | Perda severa |

### O que e Distilled LoRA:
Wan 2.2 = motor principal. Distilled LoRA (CausVid V2) = arquivo de ~200MB que "ensina" o Wan a fazer em 8 steps o que normalmente precisa de 50. Qualidade ~95-98% do original. E o MESMO modelo Wan, so roda mais rapido.

### Opcoes de steps:
- **14 steps:** ~98% qualidade, 3.5x mais rapido — MAIS SEGURO
- **8 steps:** ~95% qualidade, 6x mais rapido — BOM para Shorts mobile
- **Recomendacao:** Testar ambos, comparar visualmente

---

## I2V com Imagens Flux (NanoBanana)

- Imagens de alta qualidade MELHORAM o resultado do I2V
- "Noise in, noise out" — imagem limpa = video melhor
- POREM: I2V produz ~18% menos movimento que T2V (modelo "respeita demais" a imagem)
- Solucao: enfatizar acao desejada nos prompts de video
- Paisagens/ambientes ficam excelentes com I2V
- Acao intensa pode ficar mais estatica

---

## Pipeline Definitivo

```
NanoBanana (gratis)          RunPod Serverless ($0.39/hr)         Montagem (gratis)
+----------------+          +--------------------------+         +----------------+
| 12 imagens     |          | ComfyUI + Wan 2.2        |         | FFmpeg monta   |
| Flux HD por    |-- S3 --> | I2V 480p (8-14 steps)    |-- S3 -->| 12 clips       |
| short          |          | + CausVid V2 LoRA        |         | + narracao     |
+----------------+          | Latent Upscale --> 720p   |         | + musica       |
                            +--------------------------+         | --> YouTube    |
                                                                 +----------------+
```

### Etapas detalhadas:

1. **Roteiro** (gratis) — Claude gera 10-12 descricoes de cena por short
2. **Narracao** (TTS ou gravada) — ElevenLabs (~$0.30/min), Fish Audio (~$0.10/min), Edge TTS (gratis)
3. **Keyframes** (gratis) — NanoBanana gera 12 imagens Flux HD por short
4. **I2V no RunPod** ($0.39/hr) — ComfyUI Serverless, Wan 2.2 + LoRA, 480p --> 720p
5. **Montagem** (gratis) — FFmpeg junta clips + narracao + musica + legendas
6. **Upload** — daily_uploader.py existente --> YouTube

---

## Custos Calculados (So RunPod — Imagens Gratis)

### Tempo por clip (RTX 4090, Distilled LoRA):

| Etapa | Tempo |
|-------|-------|
| I2V geracao 480p (8 steps) | ~40-60s |
| Latent upscale 720p | ~15-20s |
| **Total por clip** | **~60-80s** |

### 30 shorts/dia:

| Item | Calculo |
|------|---------|
| Clips total | 30 x 12 = 360 clips |
| Tempo GPU total | 360 x 70s = 25.200s = **7 horas** |
| Custo RunPod | 7h x $0.39 = **$2.73/dia** |
| **Custo mensal** | **$82 (~R$450/mes)** |
| **Custo por short** | **~R$15** |

### 50 shorts/dia:

| Item | Calculo |
|------|---------|
| Clips total | 50 x 12 = 600 clips |
| Tempo GPU total | 600 x 70s = 42.000s = **11.7 horas** |
| Custo RunPod | 11.7h x $0.39 = **$4.56/dia** |
| **Custo mensal** | **$137 (~R$750/mes)** |
| **Custo por short** | **~R$15** |

---

## RunPod — Detalhes Tecnicos

### Precos GPU (Community Cloud):

| GPU | VRAM | On-Demand/hr | Spot/hr |
|-----|------|-------------|---------|
| RTX 3090 | 24GB | $0.22-0.30 | $0.15-0.20 |
| RTX 4090 | 24GB | $0.39-0.44 | $0.25-0.34 |
| A6000 | 48GB | $0.33-0.40 | $0.22-0.28 |
| A100 80GB | 80GB | $1.64-1.89 | $1.10-1.33 |
| H100 80GB | 80GB | $2.39-2.99 | $1.70-2.17 |

### Serverless:
- Billing por segundo
- Escala automatica (0 a N workers)
- Cold start: <2 segundos com FlashBoot
- Transfer in/out: GRATIS
- Storage: $0.07/GB/mes (Network Volume)

### Setup no RunPod:
1. Template ComfyUI pronto (1-click)
2. Ou Docker custom com worker-comfyui (`github.com/runpod-workers/worker-comfyui`)
3. API: enviar workflow JSON via REST
4. Output: S3 bucket ou base64

---

## SaladCloud — Por Que Foi Descartado

| Aspecto | RunPod | SaladCloud |
|---------|--------|------------|
| Preco 4090/hr | $0.39 | $0.18-0.20 |
| SLA/Uptime | Bom | NENHUM |
| Cold start | 2-5 seg | 5-15 MINUTOS |
| No cai no meio? | Raro | 5-10% chance |
| Template Wan 2.2 | 1-click | Nao tem |
| Economia 30 shorts/dia | — | ~R$115/mes |

**Economia de R$115/mes NAO justifica a complexidade.** SaladCloud so faz sentido a 200+ videos/dia.

---

## Comprar Maquina — Por Que Foi Descartado

Com otimizacoes (Distilled LoRA), o RunPod custa ~R$450/mes para 30 shorts.
Eletricidade de uma RTX 3090 rodando 20hr/dia = ~R$236/mes.
Eletricidade de uma RTX 5090 rodando 20hr/dia = ~R$346/mes.

A economia e minima e nao justifica o investimento upfront ($1.480-$3.860).
So faria sentido a 100+ shorts/dia ou com outros workloads (LoRAs, imagens, etc).

---

## Componentes no ComfyUI (o que carregar):

| Componente | O que e | Tamanho |
|------------|---------|---------|
| Wan 2.2 I2V 14B (ou 5B) | Modelo principal de video | ~28GB (14B) ou ~10GB (5B) |
| CausVid V2 LoRA | Otimizacao de steps (50-->8) | ~200MB |
| Wan 2.2 Latent Upscaler 5B | Upscale 480p-->720p | ~10GB |

---

## Proximo Passo: Teste de Qualidade (~R$30)

1. Subir Pod RTX 4090 no RunPod (template Wan 2.2, $0.39/hr)
2. Pegar 1 imagem do NanoBanana
3. Rodar I2V com CausVid V2 LoRA:
   - Teste A: 8 steps
   - Teste B: 14 steps
4. Latent upscale ambos para 720p
5. Comparar qualidade
6. Aprovar config final

### Depois do teste aprovado:
- Montar Docker image para Serverless
- Criar script de orquestracao (Python)
- Integrar com backend FastAPI existente
- Automatizar pipeline completo

---

## Opcoes de TTS para Narracao

| Metodo | Custo | Qualidade |
|--------|-------|-----------|
| ElevenLabs | ~$0.30/min | Excelente, vozes realistas |
| Fish Audio | ~$0.10/min | Muito boa, mais barato |
| Edge TTS (Microsoft) | Gratis | Boa, vozes pt-BR disponiveis |
| Gravar voces | Gratis | Autentica |

---

## Links Uteis

- RunPod: https://www.runpod.io
- worker-comfyui: https://github.com/runpod-workers/worker-comfyui
- Wan 2.2: https://github.com/Wan-Video/Wan2.2
- CausVid V2 LoRA: https://huggingface.co/blog/MonsterMMORPG/causvid-lora-v2-of-wan-21-brings-massive-quality
- FramePack: https://github.com/lllyasviel/FramePack
- ComfyUI TeaCache: https://github.com/welltop-cn/ComfyUI-TeaCache
- Wan 2.2 GGUF: https://huggingface.co/QuantStack/Wan2.2-I2V-A14B-GGUF
- ComfyUI GGUF: https://github.com/city96/ComfyUI-GGUF
