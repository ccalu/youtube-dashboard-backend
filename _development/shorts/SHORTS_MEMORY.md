# Shorts Factory — Memoria Completa

> Ultima atualizacao: 2026-04-02

---

## Status Atual

- **Pipeline E2E funcionando via Dashboard** (~13 min do zero ao video no Drive)
- **Playwright** (zero coordenadas, imune a zoom/scroll)
- **Narracao 1.1x** como padrao
- **Drive upload automatico** (substitui se re-renderizar)
- **Scriptwriter otimizado** (Joao + estrutura 4 atos)

---

## 1. Fluxo Completo

```
[Criacao] Seleciona subnicho >> canal >> tema >> "Gerar Producao"
    |
    | Claude Opus (script 14 paragrafos) + Claude Sonnet (14 prompts img + 14 anim)
    | Salva producao.json + INSERT Supabase (status: producao)
    |
[Producao] "Produzir Tudo" (1 clique = Freepik + Remotion + Drive)
    |
    | Playwright: limpa >> cola 14+14+narracao >> voz >> "Iniciar a partir daqui"
    | Espera ~9 min + 90s >> baixa ZIPs >> organiza (reverse, dedup, rename)
    | UPDATE status = "edicao"
    |
[Edicao] Card migra automaticamente, detecta Remotion rodando
    |
    | ffmpeg 1.1x >> Whisper >> Remotion render >> Drive upload
    | UPDATE status = "pronto" + drive_url
    |
[Prontos] Botao "Drive" abre pasta no Google Drive
```

### Tempos
| Passo | Tempo |
|-------|-------|
| Script + Prompts | ~97s |
| Freepik | ~9 min |
| Remotion + Drive | ~2 min |
| **TOTAL** | **~13 min** |

---

## 2. Freepik Spaces — IDs e Regras

### IDs dos Blocos (data-id)
| Bloco | ID |
|-------|----|
| PROMPTS_IMAGEM | `c4861991-3c27-4026-ad32-8fe46c43e360` |
| PROMPTS_ANIMACAO | `1ce52b31-1c46-4460-b4c2-a01778b76c6d` |
| NARRACAO_TEXTO | `1d28d411-54eb-4d66-83eb-f414971cb89a` |
| LISTA_IMAGENS | `8072ef08-819b-495a-8411-68e921856e9c` |
| LISTA_VIDEOS | `f9217fab-bdfe-4a96-965a-2665e0dda2e2` |
| WRAPPER_NARRACAO | `68ea5e5a-f898-4f35-83b6-cd69a760dd76` |

### Regras Criticas
1. **ZERO coordenadas** — tudo via data-id + dispatchEvent + element.click() + focus()
2. **Limpar lista**: right-click via dispatchEvent no ID INTERNO (nao wrapper)
3. **Colar prompts**: dispatchEvent "Adicionar texto" >> focus tiptap >> insert_text + Enter
4. **Verificacao**: checa count apos colar, re-tenta com wait 600ms se < 14
5. **Executar**: SEMPRE "Iniciar a partir daqui" (NUNCA "Todo o fluxo")
6. **Download**: `page.expect_download()` + `download.save_as()` (CDP nao salva em artifacts)
7. **Ordem reversa**: sorted(reverse=True) + nomes tmp_XX (evita conflito Windows)
8. **Esperar 90s** apos 14 videos antes de baixar
9. **Tolerancia**: aceita 13+ imagens/clips

### Vozes por Lingua
| Lingua | Voz |
|--------|-----|
| Portugues | Lucas Moreira |
| Ingles | Caleb Morgan |
| Espanhol | Diego Marin |
| Frances | Diego Marin |
| Italiano | Giulio Ferrante |
| Russo | Leo Gamier |
| Japones | Giulio Ferrante |
| Coreano | Ji-Hoon |
| Turco | Can Ozkan |
| Polones | Diego Marin |
| Alemao | Lukas Schneider |

---

## 3. Remotion Editor

1. **ffmpeg atempo=1.1** >> narracao_fast.mp3
2. **Musica de fundo** >> selecionada por categoria (music_selector.py), volume 0.6
3. **Whisper medium** >> captions.json (word timestamps)
4. **Clip timings** >> duracao de cada clip baseada nos paragrafos do script (busca ultima palavra de cada paragrafo no Whisper, corta no meio da pausa)
5. **Remotion render** >> video_final.mp4 (1080x1920, 30fps, calculateMetadata)
6. **Drive upload** >> Service Account, substitui se ja existe
7. Retorna `{video_path, drive_url}` >> backend salva no Supabase

### Cores de Highlight
| Subnicho | Hex |
|----------|-----|
| Reis Perversos / Historias Sombrias / Culturas Macabras | `#9B30FF` |
| Relatos de Guerra / Frentes de Guerra | `#00CC44` |
| Guerras e Civilizacoes | `#FF8C00` |
| Monetizados | `#E51A1A` |

---

## 4. Endpoints (shorts_endpoints.py)

| Endpoint | O que faz |
|----------|-----------|
| `POST /gerar` | Gera script + prompts (background) |
| `POST /produzir/{id}` | Pipeline completo: Freepik >> Remotion >> Drive |
| `POST /executar-freepik/{id}` | So Freepik (fallback) |
| `POST /editar/{id}` | So Remotion + Drive (fallback) |
| `POST /sugerir-temas` | GPT-4 Mini sugere 5 temas |
| `GET /logs/{id}?after=N` | Logs em tempo real |
| `POST /pausar/{id}` | Pausa producao |
| `PATCH /producoes/{id}/status` | Muda status manual |
| `DELETE /producoes/{id}` | Exclui do Supabase |
| `GET /producoes` | Lista (filtro por status) |
| `GET /browser-status` | Chrome conectado? |
| `POST /inicializar-browser` | Abre Chrome + Freepik |
| `GET /fila-producao` | Estado da fila (current + queue) |
| `DELETE /fila-producao/{id}` | Remove da fila |

Todos prefixados com `/api/shorts/`

---

## 5. Supabase — shorts_production

| Campo | Tipo |
|-------|------|
| id | serial |
| canal, canal_id | text, int |
| subnicho, lingua | text |
| titulo, estrutura | text |
| producao_json | jsonb (script + 14 cenas) |
| drive_link | text (caminho local) |
| drive_url | text (URL Google Drive) |
| status | text (producao / edicao / pronto) |
| created_at, updated_at | timestamptz |

---

## 6. Scriptwriter — Estrutura do Prompt

- **6 tipos de hook**: Dilema, Claim Chocante, Superlativo, Did You Know, Pergunta, Listicle
- **4 atos obrigatorios**: HOOK (1-2) >> BUILD (3-9) >> CLIMAX (10-12) >> PAYOFF (13-14)
- **Regra de ouro**: Payoff reconecta com o Hook (loop fechado)
- **Retencao natural**: sem frases template, tensao vem do storytelling
- **Finalizacao**: Open Loop ou Twist Final (NUNCA CTA explicito)
- **TTS**: numeros por extenso no script, normais no titulo/descricao
- **Max**: 800 chars, 14 paragrafos

---

## 7. Drive Upload

- **Service Account**: `n8n-imagen-service@gen-lang-client-0170628359.iam.gserviceaccount.com`
- **Pasta raiz**: `1_TiJ5NO_I-8E2_ocEiwWiJTXkl8NPWyb`
- **Estrutura**: SHORTS/{subnicho}/{canal}/{titulo}/
- **Arquivos**: video_final.mp4, producao.json, copy.txt, narracao.mp3
- **Substitui** ao re-renderizar (nao duplica)

---

## 8. Erros Que Podem Voltar

| Erro | Causa | Solucao |
|------|-------|---------|
| Prompts incompletos (< 14) | Freepik perde foco | Retry automatico com wait 600ms |
| "Execution context destroyed" | Pagina recarregou | Retry 3x + wait_for_selector |
| Videos incompletos ao baixar | Baixou cedo demais | Esperar 90s extra |
| Imagens duplicadas | "Todo o fluxo" em vez de "Iniciar a partir daqui" | NUNCA usar "Todo o fluxo" |
| CDP nao salva downloads | Playwright via CDP | Usar expect_download + save_as |

---

## 9. Fila de Producao (production_queue.py)

- **In-memory queue** + worker thread unico (1 por vez no Freepik)
- Clicar "Produzir Tudo" em multiplos cards: primeiro executa, resto mostra "Na fila (X)"
- Quando um termina, proximo comeca automaticamente
- **Cancelar**: remove da fila se ainda nao comecou
- **Endpoints**: `GET /fila-producao`, `DELETE /fila-producao/{id}`
- **Frontend**: polling 5s atualiza posicao, transicao automatica queued >> running
- **Servidor reinicia = fila zera** (aceitavel pra uso local)

---

## 10. Ordenacao de Clips

- Clips ordenados por **ID numerico do Freepik** no filename (ex: `_65802.mp4`)
- IDs sao sequenciais pq colamos prompts na ordem 1-14
- Menor ID = cena 1, maior ID = cena 14
- Imagens sao backup, ordem nao importa
- Implementado em `organizar_downloads()` no `freepik_automation.py`

---

## 11. Musica de Fundo

### Pastas
| Pasta | Subnichos |
|-------|-----------|
| Musicas 02 | Guerras e Civilizacoes |
| Musicas 03 | Relatos de Guerra, Frentes de Guerra |
| Musicas 05 | Reis Perversos, Historias Sombrias, Culturas Macabras |
| Musicas 06 | Monetizados (Mansoes) |

### Categorias (variam por subnicho)
battle, cinematic, documentary, emotional, military, suspense, tension, court, dramatic, ecclesiastical, horror, decay, grandeur

### Como funciona
- **Scriptwriter** escolhe `music_category` baseado no tom do script
- **music_selector.py** pega track aleatoria dessa categoria
- **Controle de repeticao por canal** via Supabase (campo `music_track`)
- Quando esgota todas do canal, reinicia ciclo
- Delete do Supabase libera a track
- **Volume**: 0.5 (testado no celular e fone)
- Musica no Remotion: `<Audio src={musicPath} volume={0.5} />`

### Base: `C:\Users\PC\Downloads\SHORTS\MUSICAS-SHORTS`

---

## 12. Script (scriptwriter.py)

- **Chars**: 850-1100 (obrigatorio)
- **music_category**: scriptwriter escolhe com base no tom do script
- Categorias com descricoes pra orientar (nao engessadas)

---

## 13. Proximos Passos

### Aguardando Joao
- [ ] Prompts visuais otimizados (director.py) — pacote enviado: PACOTE_DIRETOR_COMPLETO.md
- [ ] Possivel troca de modelo de video no Freepik

### Futuro
- [ ] Upload pro YouTube via API
- [ ] Tunnel/Deploy (quando precisar acesso externo)
- [ ] Script de setup pra outros PCs
- [ ] Legendas com numeros formatados
