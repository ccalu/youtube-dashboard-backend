# Incertezas Resolvidas — LTX 2.3

> Data: 2026-03-25

---

## 1. Gemma Heretic FP8 — COMPATIVEL? ✅ SIM

**Resposta definitiva:** gemma_3_12B_it_heretic_fp8 funciona como drop-in replacement.

**POREM:** Estamos usando v1 do heretic. Existe v2 que eh melhor:
- v1: pode faltar vision weights
- v2: inclui vision weights, mais compativel

**Acao:** Baixar v2 ao inves de v1
- URL: https://huggingface.co/DreamFast/gemma-3-12b-it-heretic-v2
- Arquivo: comfyui/gemma_3_12B_it_heretic_v2_fp8_e4m3fn.safetensors

**Fonte:** DreamFast confirma que o formato ComfyUI FP8 funciona com LTXAVTextEncoderLoader

---

## 2. Vertical 544x960 — FUNCIONA? ✅ SIM

**Resposta definitiva:** LTX 2.3 suporta vertical nativo (treinado com dados portrait)

**Resolucoes validas (divisiveis por 32):**
- 544x960 ✅ (544/32=17, 960/32=30)
- 736x1280 ✅ (736/32=23, 1280/32=40) — MELHOR opcao para 720p
- 720x1280 ⚠️ (720/32=22.5 — NAO divisivel! pode dar problema!)
- 1088x1920 ✅ (1088/32=34, 1920/32=60) — para 1080p

**DESCOBERTA CRITICA:** 720 NAO eh divisivel por 32!
- 720/32 = 22.5 → pode causar artefatos ou erro
- Usar **736x1280** ao inves de 720x1280

**EmptyLTXVLatentVideo:** width=736, height=1280 (width primeiro)

**Sem perda de qualidade** vs landscape — na verdade, LTX 2.3 foi especificamente melhorado para portrait

---

## 3. Conversao Frontend→API — COMO? ✅ RESOLVIDO

**Resposta definitiva:** O /prompt API NAO aceita formato frontend. Precisa converter.

**Solucao:** Instalar o custom node conversor de Seth Robinson:
```bash
cd custom_nodes
git clone https://github.com/SethRobinson/comfyui-workflow-to-api-converter-endpoint.git
```

Isso cria um endpoint POST /workflow/convert que converte frontend→API automaticamente usando o registro de nodes do proprio ComfyUI. Sem erros de conversao manual.

**Pipeline de execucao:**
1. POST workflow frontend JSON para /workflow/convert → recebe API format
2. POST API format para /prompt → executa
3. GET /history/{id} → resultado

---

## Mudancas no setup

### Modelo Gemma: trocar v1 por v2
- ANTES: gemma_3_12B_it_heretic_fp8_e4m3fn.safetensors (v1)
- AGORA: gemma_3_12B_it_heretic_v2_fp8_e4m3fn.safetensors (v2)

### Resolucao: trocar 720 por 736
- ANTES: 720x1280
- AGORA: 736x1280 (divisivel por 32)

### Node extra: workflow converter
- Instalar: comfyui-workflow-to-api-converter-endpoint
- Permite converter e executar workflows sem erro

### Workflows adaptados: atualizar resolucao
- Trocar 544x960 para 736x1280 nos 3 workflows
- Ou manter 544x960 para stage 1 do Two-Stage (depois upscale)
