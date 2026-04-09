# Shorts Factory — Memoria Completa

> Ultima atualizacao: 2026-04-06

---

## Status Atual

- **Pipeline E2E funcionando via Dashboard** (~19 min do zero ao video no Drive)
- **14 cenas × 5s** (Kling 2.5) — ~60s de video
- **Playwright** (zero coordenadas, imune a zoom/scroll)
- **Narracao 1.1x** como padrao
- **Musica de fundo** com selecao por categoria, fade in 1s / fade out 2s
- **Crossfade 0.5s** entre clips
- **Drive upload automatico** (substitui se re-renderizar)
- **Diretor otimizado**: storyboard thinking, coerencia visual total, animacoes unicas por cena

---

## 1. Fluxo Completo

```
[Criacao] Seleciona subnicho >> canal >> tema >> "Gerar Producao"
    |
    | Claude Opus (script 14 paragrafos, 800-900 chars, music_category)
    | Claude Sonnet (14 prompts img + 14 anim, storyboard thinking)
    | Salva producao.json + INSERT Supabase (status: producao)
    |
[Producao] "Produzir Tudo" (1 clique = Freepik + Remotion + Drive)
    |
    | Playwright: limpa >> cola 14+14+narracao >> voz >> "Iniciar a partir daqui"
    | Espera ~10 min + 4 min seguranca >> baixa ZIPs >> organiza (ID numerico)
    | UPDATE status = "edicao"
    |
[Edicao] Card migra automaticamente, detecta Remotion rodando
    |
    | ffmpeg 1.1x >> Musica (categoria + canal) >> Whisper >> Remotion render
    | Crossfade 0.5s entre clips + musica fade in 1s / out 2s
    | Drive upload >> UPDATE status = "pronto" + drive_url
    |
[Prontos] Botao "Drive" abre pasta no Google Drive
```

### Tempos (16 cenas, Kling 2.5)
| Passo | Tempo |
|-------|-------|
| Script + Prompts | ~94s |
| Freepik (16 imgs + 16 vids + nar) | ~15 min |
| Remotion + Drive | ~2.5 min |
| **TOTAL** | **~19 min** |

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
6. **Download**: `page.expect_download()` + `download.save_as()`
7. **Ordenacao clips**: por ID numerico do Freepik (sequencial)
8. **Esperar 4 min** apos 14 videos antes de baixar (Kling 2.5 demora mais)
9. **Tolerancia**: aceita 13+ imagens/clips

### Vozes por Lingua
| Lingua | Voz |
|--------|-----|
| Portugues | Lucas Moreira |
| Ingles | Caleb Morgan |
| Espanhol | Diego Marin |
| Frances | Diego Marin |
| Italiano | Giulio Ferrante |
| Russo | Leo Garnier |
| Japones | Giulio Ferrante |
| Coreano | Ji-Hoon |
| Turco | Can Ozkan |
| Polones | Diego Marin |
| Alemao | Lukas Schneider |

### Selecao de Voz (Playwright)
- Encontra botao de voz pela proximidade com "ElevenLabs" na toolbar
- Abre seletor >> troca filtro de lingua (dropdown mostra linguas em PORTUGUES, nao no idioma nativo)
- Seleciona voz alvo na lista filtrada
- LINGUA_FILTRO usa nomes em portugues (Alemao, Espanhol, Frances, etc.)
- Testado e validado com TODAS as 11 linguas

---

## 3. Remotion Editor

1. **ffmpeg atempo=1.1** >> narracao_fast.mp3
2. **Musica de fundo** >> selecionada por categoria, volume 0.5, fade in 1s / out 2s
3. **Whisper medium** >> captions.json (word timestamps)
4. **Clip timings** >> duracao baseada nos paragrafos (busca ultima palavra no Whisper)
5. **Crossfade 0.5s** entre clips (fade in opacity)
6. **Remotion render** >> video_final.mp4 (1080x1920, 30fps, calculateMetadata)
7. **playbackRate**: 5/clipDuration (clips de 5s do Kling 2.5)
8. **Drive upload** >> Service Account, substitui se ja existe

### Cores de Highlight
| Subnicho | Hex |
|----------|-----|
| Reis Perversos / Historias Sombrias / Culturas Macabras | `#9B30FF` |
| Relatos de Guerra / Frentes de Guerra | `#00CC44` |
| Guerras e Civilizacoes | `#FF8C00` |
| Monetizados | `#E51A1A` |

---

## 4. Director (director.py) — Regras Chave

- **Storyboard thinking**: pensa ACAO primeiro, depois constroi imagem como frame inicial
- **Coerencia visual total**: mesmo periodo, mesmo estilo, mesma paleta, nada fora do contexto
- **14 animacoes UNICAS**: nunca repetir tipo de movimento entre cenas
- **Animacao pro Kling 2.5**: 30-40 palavras, so movimento, nunca descrever a imagem
- **Anima qualquer elemento**: pessoa, objeto, ambiente — o que fizer sentido
- **Dinamico mas real**: sem efeitos fake, sem alucinacoes, sem exageros
- **Variedade**: enquadramento, tipo de cena, iluminacao, tudo diferente entre as 16

---

## 5. Scriptwriter (scriptwriter.py)

- **14 paragrafos**, 800-900 chars, ~60s de video
- **Filosofia**: cada frase cria imagem mental, empurra narrativa, carrega tensao
- **Gancho**: abre loop que fecha no final. Congruente com energia do tema (brutalidade = gancho perturbador, nao curiosidade famosa)
- **Tipos de gancho**: cena impossivel, promessa de choque, pergunta com gap, segredo revelado, contraste extremo
- **Corpo**: tensao escala, ritmo variado (curta/longa/curta), contexto sempre com tensao
- **Climax**: UM MOMENTO especifico (cena, nao resumo)
- **Fechamento**: loop fechado, twist, reflexao, ou CTA natural (as vezes)
- **Tom**: conversacional, como contar pra um amigo. Nao formal nem academico
- **TTS**: numeros por extenso, anos completos ("mil novecentos e quarenta e dois"), "antes de Cristo" nao "a.C."
- **music_category**: escolhe categoria de musica baseado no tom

---

## 6. Endpoints (shorts_endpoints.py)

| Endpoint | O que faz |
|----------|-----------|
| `POST /gerar` | Gera script + prompts (background) |
| `POST /produzir/{id}` | Pipeline completo: Freepik >> Remotion >> Drive (via fila) |
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

## 7. Fila de Producao (production_queue.py)

- **In-memory queue** + worker thread unico (1 por vez no Freepik)
- Clicar "Produzir Tudo" em multiplos cards: primeiro executa, resto mostra "Na fila (X)"
- Quando um termina, proximo comeca automaticamente
- **Cancelar**: remove da fila se ainda nao comecou
- **Endpoints**: `GET /fila-producao`, `DELETE /fila-producao/{id}`
- **Frontend**: polling 5s atualiza posicao, transicao automatica queued >> running
- **Servidor reinicia = fila zera** (aceitavel pra uso local)

---

## 8. Drive Upload

- **Service Account**: `n8n-imagen-service@gen-lang-client-0170628359.iam.gserviceaccount.com`
- **Pasta raiz**: `1_TiJ5NO_I-8E2_ocEiwWiJTXkl8NPWyb`
- **Estrutura**: SHORTS/{subnicho}/{canal}/{titulo}/
- **Arquivos**: video_final.mp4, producao.json, copy.txt, narracao.mp3
- **Substitui** ao re-renderizar (nao duplica)
- **Credenciais**: no .env (GOOGLE_SERVICE_ACCOUNT_JSON)

---

## 9. Ordenacao de Clips

- Clips ordenados por **ID numerico do Freepik** no filename (ex: `_65802.mp4`)
- IDs sao sequenciais pq colamos prompts na ordem 1-14
- Menor ID = cena 1, maior ID = cena 14
- Imagens sao backup, ordem nao importa
- Implementado em `organizar_downloads()` no `freepik_automation.py`

---

## 10. Musica de Fundo

| Pasta | Subnichos |
|-------|-----------|
| Musicas 02 | Guerras e Civilizacoes |
| Musicas 03 | Relatos de Guerra, Frentes de Guerra |
| Musicas 05 | Reis Perversos, Historias Sombrias, Culturas Macabras |
| Musicas 06 | Monetizados (Mansoes) |

- Scriptwriter escolhe `music_category` baseado no tom do script
- Categorias com descricoes (nao engessadas, sao referencia)
- Controle de repeticao por canal via Supabase (`music_track`)
- Volume: 0.5 | Fade in: 1s | Fade out: 2s
- Base: `C:\Users\PC\Downloads\SHORTS\MUSICAS-SHORTS`

---

## 11. Supabase — shorts_production

| Campo | Tipo |
|-------|------|
| id | serial |
| canal, canal_id | text, int |
| subnicho, lingua | text |
| titulo, estrutura | text |
| producao_json | jsonb (script + 14 cenas) |
| drive_link | text (caminho local) |
| drive_url | text (URL Google Drive) |
| music_track | text (nome do arquivo mp3) |
| status | text (producao / edicao / pronto) |
| created_at, updated_at | timestamptz |

---

## 12. Erros Que Podem Voltar

| Erro | Causa | Solucao |
|------|-------|---------|
| Prompts incompletos | Freepik perde foco | Retry com wait 600ms |
| Videos incompletos | Baixou cedo (Kling demora mais) | Esperar 4 min |
| Musica nao selecionada | dotenv nao carregado | load_dotenv() antes do SupabaseClient |
| Cenas fora do contexto | Diretor misturou estilos | Regra coerencia visual total |

---

## 13. YouTube Upload

- Upload via `YouTubeUploader.upload_to_youtube()` existente
- **Shorts**: `skip_playlist=True, privacy_status="public"` (publico, sem playlist)
- **Videos longos**: parametros padrao `skip_playlist=False, privacy_status="private"` (inalterado)
- Busca `channel_id` em `yt_channels` pelo `channel_name`
- Marca como `containsSyntheticMedia: True` (IA)
- Apos upload: salva `youtube_video_id` + status "publicado" no Supabase
- **Endpoint**: `POST /api/shorts/upload-youtube/{id}`
- **Dashboard**: aba Upload com cards por canal, historico, canais sem OAuth

---

## 14. Analytics

- **Aba Analytics** no dashboard: subnichos accordion (mesmo estilo Tabela), canais, shorts
- **Metricas por short**: views, likes, comments (do videos_historico), subs_gained (do shorts_subs)
- **Coleta de subs**: YouTube Analytics API (`channel==MINE`), tabela `shorts_subs` (video_id, date, subs_gained, subs_lost)
- **Endpoint coleta**: `POST /api/shorts/collect-subs` (background task)
- **Endpoint dados**: `GET /api/shorts/analytics` (batch query, rapido)
- views/likes/comments: coleta diaria existente (videos_historico) — nao mexer
- subs_gained: coleta separada via Analytics API
- API so retorna videos com 1+ inscrito atribuido

---

## 15. Proximos Passos

### Futuro
- [ ] Tunnel/Deploy (acesso externo)
- [ ] Script de setup pra outros PCs
- [ ] Integrar coleta de subs na rotina diaria
