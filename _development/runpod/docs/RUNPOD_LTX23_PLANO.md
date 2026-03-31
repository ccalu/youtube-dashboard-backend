# Plano de Producao de Shorts com IA — RunPod + LTX 2.3

> Documento para alinhamento entre socios
> Data: 2026-03-23

---

## O Que Estamos Fazendo

Produzir Shorts (~1 min) para os canais do YouTube usando inteligencia artificial para transformar imagens estaticas em video animado (Image-to-Video).

**Exemplo:** Uma imagem de um samurai em campo de batalha → IA gera um video dele lutando, capa balancando, poeira subindo. Nao e efeito de camera — e animacao real gerada por IA.

---

## Stack Tecnico

| Componente | O que e | Custo |
|---|---|---|
| **LTX 2.3** | Modelo de IA que transforma imagem em video (I2V) | Gratis (open-source) |
| **ComfyUI** | Interface para rodar o modelo com workflows visuais | Gratis (open-source) |
| **RunPod** | Aluguel de GPU na nuvem para rodar o modelo | $0.39/hr (RTX 4090) |
| **FFmpeg** | Montagem final dos clips (local, sem GPU) | Gratis |
| **Claude Code** | Orquestra tudo: liga pod, gera clips, monta video, desliga pod | Assinatura existente |

---

## Como Funciona o Processo

### Fase Criativa (Marcelo + Lucca)
```
1. Lucca gera imagens verticais a partir dos videos longos do YouTube
2. Marcelo organiza as imagens em pastas (1 pasta = 1 Short)
3. Marcelo + Claude definem os prompts de animacao para cada imagem
   Ex: "samurai swings katana, dust rises, cape flowing in wind"
```

### Fase de Execucao (Claude Code — 100% autonomo)
```
1. Liga o pod RTX 4090 no RunPod
2. Envia as imagens para o pod
3. Roda o workflow do ComfyUI gerando cada clip via I2V
4. Baixa todos os clips prontos para o PC do Marcelo
5. DESLIGA O POD (fim do custo RunPod)
6. Monta o Short final via FFmpeg (local, custo zero):
   - Junta os clips na sequencia correta
   - Adiciona narracao/audio
   - Adiciona musica de fundo
   - Adiciona legendas
7. Entrega o Short pronto para upload
```

### Fluxo Visual
```
Lucca gera          Marcelo +           Claude Code          Claude Code
imagens         Claude definem      executa no RunPod      monta local
                   prompts

[12 imagens] → [prompts animacao] → [12 clips animados] → [Short pronto]
   |                  |                     |                    |
   v                  v                     v                    v
 Gratis            Gratis              ~R$0.87/short          Gratis
                                      (12 clips x 2min)
```

---

## Estrutura de Pastas

```
shorts_producao/
├── video_01/
│   ├── 01.png  → prompt: "warrior charges forward, sword raised"
│   ├── 02.png  → prompt: "aerial view of battlefield, armies clashing"
│   ├── 03.png  → prompt: "close-up face, eyes fierce, sweat dripping"
│   ├── ...
│   └── 12.png  → prompt: "sunset over battlefield, flags waving"
├── video_02/
│   └── ...
└── video_30/
    └── ...
```

---

## Custos

### Por Short (12 clips)
| Item | Calculo | Custo |
|---|---|---|
| Geracao I2V | 12 clips x ~2 min = 24 min de GPU | ~$0.16 (~R$0.87) |
| Montagem FFmpeg | Local | Gratis |
| **Total por Short** | | **~R$0.87** |

### Producao Diaria (30 Shorts)
| Item | Calculo | Custo |
|---|---|---|
| Total de clips | 30 x 12 = 360 clips | |
| Tempo de GPU | 360 x 2 min = 12 horas | |
| Custo RunPod | 12h x $0.39/hr | **$4.68 (~R$26/dia)** |

### Producao Mensal
| Volume | Custo/mes |
|---|---|
| 30 shorts/dia | ~R$780/mes |
| 15 shorts/dia | ~R$390/mes |
| 50 shorts/dia | ~R$1.300/mes |

### Custo Fixo
| Item | Custo |
|---|---|
| Network Volume RunPod (storage modelos) | ~$7-15/mes (~R$50-80) |

---

## Qualidade

| Parametro | Valor |
|---|---|
| Resolucao minima | 720x1280 (HD vertical) |
| Testar tambem | 1080x1920 (Full HD vertical) |
| Duracao por clip | ~5 segundos |
| Duracao do Short final | ~1 minuto (12 clips) |
| Modelo | LTX 2.3 (distilled, 14 steps) |
| Formato | 9:16 vertical (padrao Shorts/Reels/TikTok) |

**Nota:** A qualidade do video e identica independente da GPU usada. A GPU so muda a velocidade de geracao.

---

## Seguranca e Economia

### Regras de Uso do Pod
| Regra | Detalhe |
|---|---|
| Pod so liga quando tem fila de trabalho | Nunca fica ligado "esperando" |
| Pod desliga IMEDIATAMENTE apos ultima geracao | Antes do FFmpeg (que roda local) |
| Pod ocioso = pod desligado | Se nao tem clip gerando, desliga |
| Checklist de confirmacao | Toda sessao termina com verificacao de pod desligado |
| Script de seguranca | Alerta automatico se pod ficar ligado sem produzir |

### Comparativo de GPU
| | RTX 4090 | H200 |
|---|---|---|
| Custo/hora | $0.39 | $3.59 |
| Tempo/clip (720p) | ~2 min | ~30-45s |
| Custo/clip | R$0.07 | R$0.22 |
| 360 clips (30 shorts) | R$26 em 12h | R$243 em 12h |
| Qualidade | Identica | Identica |

**Decisao: RTX 4090** — 3x mais barata por clip. Se precisar de mais velocidade, escala com 2-3 pods em paralelo (mesmo custo total, metade do tempo).

---

## Fases de Implementacao

### Fase 1: Setup (~5 min)
- [ ] Configurar API Key do RunPod
- [ ] Instalar RunPod CLI + MCP Server no Claude Code
- [ ] Configurar SSH para acesso aos pods
- [ ] Criar scripts de seguranca (auto-desligar)

### Fase 2: Testes (~R$5-10)
- [ ] Subir pod RTX 4090 com ComfyUI
- [ ] Instalar LTX 2.3 (FP8) no pod
- [ ] Testar 1 imagem em 720p — medir tempo real
- [ ] Testar 1 imagem em 1080p — medir tempo real
- [ ] Comparar qualidade 720p vs 1080p
- [ ] Testar 8 steps vs 14 steps vs 20 steps
- [ ] Definir sweet spot (qualidade x velocidade x custo)
- [ ] Desligar pod

### Fase 3: Validacao Pipeline I2V (~R$5)
- [ ] Enviar pasta com 12 imagens de teste
- [ ] Gerar os 12 clips com prompts definidos
- [ ] Validar qualidade dos clips
- [ ] Validar que todos salvaram corretamente
- [ ] Medir tempo total do pipeline
- [ ] Desligar pod

### Fase 4: Montagem FFmpeg
- [ ] Juntar 12 clips em sequencia
- [ ] Adicionar audio/narracao
- [ ] Adicionar legendas
- [ ] Exportar Short final
- [ ] Validar qualidade do resultado

### Fase 5: Producao
- [ ] Primeiro lote real (5-10 shorts)
- [ ] Ajustes finos baseado nos resultados
- [ ] Escalar para volume desejado

---

## Autonomia do Claude Code

| O que Claude faz sozinho | O que precisa do Marcelo |
|---|---|
| Liga/desliga pods | Aprovar o "roda" antes de comecar |
| Instala modelos e dependencias | Fornecer imagens nas pastas |
| Envia imagens pro pod | Definir prompts de animacao (junto com Claude) |
| Gera todos os clips | Avaliar qualidade dos resultados |
| Baixa clips pro PC | Decisoes criativas |
| Monta Short no FFmpeg | |
| Monitora GPU e progresso | |
| Desliga pod apos conclusao | |

---

## Riscos e Mitigacoes

| Risco | Mitigacao |
|---|---|
| Pod esquecido ligado | Script auto-desligar + checklist + alerta |
| Qualidade ruim dos clips | Fase de testes antes de produzir em escala |
| Modelo LTX 2.3 nao atende | Wan 2.2 como backup (mais lento, mesma qualidade ou melhor) |
| RunPod fora do ar | Raro, mas pode trocar de regiao/provedor |
| Custo acima do esperado | Monitoramento por sessao, historico de gastos |

---

## Resumo Executivo

- **Investimento:** R$5-10 para testes iniciais
- **Custo operacional:** ~R$0.87 por Short
- **Producao:** ~30 clips/hora na RTX 4090
- **Autonomia:** Claude Code executa 100% do processo tecnico
- **Qualidade:** HD/Full HD vertical, animacao real por IA
- **Stack:** 100% open-source (exceto aluguel de GPU)
