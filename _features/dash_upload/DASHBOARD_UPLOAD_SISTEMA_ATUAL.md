# SISTEMA DE DASHBOARD UPLOAD - DOCUMENTACAO COMPLETA
*Ultima atualizacao: 16/02/2026*

## VISAO GERAL

Sistema completo de automacao de upload para YouTube com dashboard de monitoramento em tempo real. Gerencia 20+ canais dark, com upload automatizado diario, integracao com Google Sheets e sistema de historico completo.

### Status Atual
- **Dashboard v2 integrado no main.py** (Railway) - acesso online sem servidor local
- Dashboard local (legado) na porta 5006
- Upload automatico diario as 5:30 AM
- 20 canais ativos
- Suporte multi-idioma (PT, EN, ES, DE, FR, AR, IT, JP, KR, TR, PL, RU)

---

## DASHBOARD v2 - INTEGRADO NO RAILWAY (PRINCIPAL)

### Acesso Online
- **URL Producao:** `https://youtube-dashboard-backend-production.up.railway.app/dash-upload`
- **Implementado em:** `main.py` (linhas 5994-6741)
- **Cache:** 3 segundos (compartilhado entre usuarios, reduzido de 10s em 16/02/2026)
- **Atualizacao automatica:** A cada 5 segundos via JavaScript

### Vantagens sobre v1 (local)
- Acessa de qualquer lugar (celular, outro PC)
- Socio pode acessar sem rodar nada local
- Sempre atualizado (deploy automatico via Railway)
- Sem necessidade de rodar Flask separado

### Endpoints da v2
| Endpoint | Descricao |
|----------|-----------|
| `GET /dash-upload` | Pagina HTML do dashboard |
| `GET /api/dash-upload/status` | Status canais agrupados por subnicho |
| `GET /api/dash-upload/canais/{id}/historico` | Historico individual do canal |
| `GET /api/dash-upload/historico-completo` | Historico de todos os canais (30 dias) |

### Detalhes Tecnicos da v2
- **Template HTML:** Inline no main.py (~495 linhas HTML/CSS/JS)
- **Cache:** `_dash_cache` com TTL de 3s para evitar queries repetidas
- **Funcao auxiliar:** `_extrair_hora()` para timestamps
- **Ordenacao subnichos:** Mais uploads com sucesso aparecem primeiro
- **URLs relativas:** Funciona tanto local (localhost:8000) quanto Railway

---

## DASHBOARD LOCAL (LEGADO)

### Arquivo Principal
**`dash_upload_final.py`**
- **Porta:** 5006
- **URL:** http://localhost:5006
- **Atualizacao:** A cada 5 segundos (automatico)
- **Backup:** `_features/dash_upload/dash_upload_final_backup_13022026.py`
- **Nota:** Ainda funcional, mas a versao v2 no Railway e a principal

### Funcionalidades

#### 1. Cards de Estatisticas (Clicaveis)
```
Total de Canais | Upload com Sucesso | Sem Video | Com Erro | Historico Completo
```
- **Total de Canais** - Clicavel para resetar filtro (mostra todos)
- **Sucesso/Sem Video/Erro** - Clicavel para filtrar tabela por status
- **Historico Completo** - Abre modal com historico de todos os dias
- **UI:** Hover levanta card (-2px) + sombra, clique compress (scale 0.97)

#### 2. Agrupamento por Subnicho
Cada subnicho tem cor e emoji personalizados:
- Monetizados (verde) - Prioridade maxima
- Relatos de Guerra (dourado)
- Historias Sombrias (roxo)
- Terror (vermelho)
- Desmonetizados (cinza)

#### 3. Tags de Idioma
Sistema detecta automaticamente o idioma via funcao `getSiglaIdioma()`:
- Suporta: PT, EN, ES, DE, FR, AR, IT, JP, KR, TR, PL, RU
- Exibido como badge colorido ao lado do nome do canal

#### 4. Titulos Truncados
Titulos de video com maximo de 7 palavras + reticencias para manter layout limpo.

#### 5. Historico Individual (por canal)
- **Sem limite de data** - Mostra TODOS os registros do canal
- **Paginacao de 10 itens** - Navegacao com botoes Anterior/Proxima
- **Colunas:** Data | Video | Status | Horario
- **Deduplicacao** automatica de registros
- **Ordenacao:** Data mais recente primeiro
- **Estilo unificado:** Background #16213e, headers #0f3460, status com cores inline

#### 6. Historico Completo (todos os canais)
- **Accordion por dia** - Fechado por padrao, clicavel para expandir
- **Resumo no header:** `13/02/2026  Sucesso: 1 | Sem video: 19 | Erro: 0`
- **Seta animada:** Rotacao CSS suave ao expandir/colapsar
- **Colunas:** Canal (idioma) | Video | Status | Horario
- **Total de uploads:** Conta apenas uploads com sucesso
- **Idioma do canal** entre parenteses (PT, EN, etc.)

#### 7. Botoes de Acao por Canal
- **Upload Forcado** - Forca upload do proximo video "done" da planilha
  - Animacao: botao vira ⏳ girando+pulsando ao clicar
  - Sucesso: botao vira ✅ por 15 segundos + tabela atualiza imediatamente
  - Erro: botao vira ❌ por 5 segundos
  - Sem video: alert em ate 12 segundos + botao volta ao normal
- **Historico** - Abre modal de historico individual
- **Sheets** - Link direto para Google Sheets do canal

#### 8. Timestamps
Funcao `extrair_hora()` extrai HH:MM do timestamp sem conversao de timezone (servidor Railway roda em UTC).

---

## UI PROFISSIONAL - ANIMACOES E EFEITOS

### Cards de Estatisticas
- Hover: `translateY(-2px)` + `box-shadow: 0 4px 15px`
- Clique: `scale(0.97)` instantaneo (0.05s)
- Ativo: Borda branca + glow

### Botoes de Acao
- Hover: `opacity 0.9` + `box-shadow: 0 2px 8px`
- Clique: `scale(0.92)` (0.1s)

### Animacao de Upload Forcado (16/02/2026)
- **Uploading (⏳):** `@keyframes upload-spin` (rotacao 2s) + `upload-pulse` (opacity 1.2s)
  - Classe `.btn-icon--uploading` com background roxo suave
  - `pointer-events: none` para evitar cliques duplos
- **Sucesso (✅):** `@keyframes success-pop` (scale 0.5→1.2→1, 0.4s)
  - Classe `.btn-icon--upload-success` com background verde suave
  - Dura 15 segundos, depois restaura botao normal
- **Erro (❌):** Classe `.btn-icon--upload-error` com background vermelho suave
  - Dura 5 segundos
- **Estado preservado:** Variaveis globais `_uploadingChannelId`, `_successChannelId`, `_errorChannelId` mantêm estado entre rebuilds da tabela (que ocorrem a cada 5s)

### Modais
- Abrir: Fade-in 0.2s + slide-down 0.25s (visibility + opacity)
- Fechar: Fade-out 0.2s (clique no X, fora do modal, ou escape)

### Accordion (Dias)
- Expandir/colapsar: `max-height` transition 0.3s
- Seta: Rotacao CSS 90 graus (0.2s) em vez de trocar texto
- Header: Background transition + scale(0.99) no clique

### Tabelas
- Rows: `background transition 0.15s` no hover
- Status success: Animacao pulse (box-shadow 2s infinite)

### Botao Close (X)
- Hover: `scale(1.2)` + cor branca
- Clique: `scale(0.9)`

### Paginacao
- Classe `.btn-pagina` dedicada
- Hover: background transition
- Clique: `scale(0.95)`
- Disabled: `opacity 0.4`

---

## SISTEMA DE UPLOAD AUTOMATIZADO

### Orquestrador Principal
**`daily_uploader.py`** (1025 linhas)

### Fluxo de Upload
```
5:30 AM -> Buscar Canais -> Verificar Planilhas -> Download Drive -> Upload YouTube -> Adicionar Playlist -> Atualizar Status
```

### Prioridades
1. **Monetizados** - Processados primeiro
2. **Canais constantes** - Segunda prioridade
3. **Desmonetizados** - Por ultimo

### Sistema de Retry
- **3 tentativas** por video
- **Intervalo:** 30 segundos entre tentativas
- **Fallback:** Marca como erro apos 3 falhas

---

## INTEGRACAO GOOGLE SHEETS

### Condicoes para Video "Pronto"

| Coluna | Nome | Condicao |
|--------|------|----------|
| A | Name | Preenchido |
| J | Status | "done" |
| K | Post | Vazio |
| L | Published Date | Vazio |
| M | Drive URL | Preenchido |
| O | Upload | Vazio ou "Erro" |

---

## SISTEMA OAUTH

### Escopos Obrigatorios (4)
```python
SCOPES = [
    'youtube.upload',       # Upload de videos
    'youtube',              # Leitura do canal
    'youtube.force-ssl',    # Gerenciar playlists
    'spreadsheets'          # Atualizar planilhas
]
```

---

## ESTRUTURA DO BANCO DE DADOS

### Tabelas Principais (Supabase)

#### `yt_channels`
- Configuracoes dos canais (nome, idioma, subnicho, lingua)
- URLs das planilhas

#### `yt_canal_upload_diario`
- Registro diario de uploads
- Campos: channel_name, data, video_titulo, youtube_video_id, status

#### `yt_canal_upload_historico`
- Historico completo de uploads (sem limite de data)
- Usado como fonte primaria pelo endpoint de historico individual

#### `yt_oauth_tokens`
- Tokens OAuth por canal
- Auto-refresh configurado

---

## ENDPOINTS DO DASHBOARD

### Dashboard v2 (main.py - Railway)

#### GET /dash-upload
Pagina HTML completa do dashboard (retorna HTMLResponse).

#### GET /api/dash-upload/status
Retorna stats gerais + canais agrupados por subnicho.
- Cache de 3 segundos (`_dash_cache`)
- Busca `yt_channels` (ativos + upload_automatico) e `yt_canal_upload_diario` (hoje)
- `upload_map` com prioridade: sucesso > erro > sem_video; quando mesmo status, pega o MAIS RECENTE (created_at)
- Monetizados forcados: 2 channel_ids hardcoded
- Agrupamento inteligente: monetizados separados, guerra agrupada
- Ordenacao: subnichos com mais sucesso primeiro, canais por status

#### GET /api/dash-upload/canais/{channel_id}/historico
Retorna historico completo do canal (sem limite de data).
- Busca de `yt_canal_upload_historico` + fallback para `yt_canal_upload_diario`
- Sort por data desc + hora desc apos merge
- Deduplicacao por (channel_id, data, video_titulo)

#### GET /api/dash-upload/historico-completo
Retorna historico de todos os canais agrupado por dia (30 dias).
- Inclui campo `lingua` via JOIN com `yt_channels`
- Contadores de sucesso/sem_video/erro por dia
- Merge entre tabelas historico e diario com deduplicacao

### Dashboard v1 (dash_upload_final.py - Local/Legado)

#### GET /api/status
Retorna stats gerais + canais agrupados por subnicho (porta 5006).

#### GET /api/canais/{channel_id}/historico-uploads
Historico individual (porta 5006).

#### GET /api/historico-completo
Historico completo (porta 5006).

---

## ARQUIVOS IMPORTANTES

```
youtube-dashboard-backend/
|-- main.py                           # Dashboard v2 integrado (linhas 5994-6741)
|-- dash_upload_final.py              # Dashboard v1 local/legado (porta 5006)
|-- daily_uploader.py                 # Orquestrador de upload
|-- _features/yt_uploader/            # Modulo de upload YouTube
|   |-- uploader.py                   # Logica de upload
|   |-- oauth_manager.py              # Gestao de tokens OAuth
|   |-- sheets.py                     # Integracao Google Sheets
|   |-- database.py                   # Interacoes Supabase
|-- reauth_channel_oauth.py           # Re-autorizacao OAuth de canal existente
|-- _features/dash_upload/            # Documentacao + backup
|   |-- DASHBOARD_UPLOAD_SISTEMA_ATUAL.md (este arquivo)
|   |-- COMANDOS_RAPIDOS.md
|   |-- LAUNCHER_USAGE.md
|   |-- dash_upload_final_backup_13022026.py
```

---

## TROUBLESHOOTING

### Dashboard v2 (Railway) nao carrega
```bash
# Verificar se Railway esta no ar
curl https://youtube-dashboard-backend-production.up.railway.app/health

# Verificar endpoint de status
curl https://youtube-dashboard-backend-production.up.railway.app/api/dash-upload/status
```

### Dashboard local (v1) nao atualiza
```bash
# Verificar se esta rodando
curl http://localhost:5006/api/status

# Reiniciar
python dash_upload_final.py
```

### Upload falhou
1. Verificar token OAuth: `python check_oauth_definitivo.py`
2. Verificar planilha (colunas corretas)
3. Upload manual: `python forcar_upload_manual_fixed.py --canal "Nome do Canal"`
4. Re-autorizar OAuth: `python reauth_channel_oauth.py [channel_id]`

### Token OAuth revogado (invalid_grant)
- Causa: Google revogou refresh token (projeto em testing mode, ou permissao revogada)
- Solucao: `python reauth_channel_oauth.py` para re-autorizar com novos tokens

### Erro 403 ao adicionar playlist
- Canal precisa refazer OAuth com todos os 4 scopes
- Usar wizard v3: `python add_canal_wizard_v3.py`

---

## HISTORICO DE ALTERACOES

### 16/02/2026 - Animacao de Upload Forcado + Correcoes
- Animacao visual completa ao forcar upload (⏳ girando → ✅ check 15s ou ❌ erro 5s)
- CSS: 3 keyframes (upload-spin, upload-pulse, success-pop) + 3 classes de estado
- JS: `forcarUpload()` reescrito com polling inteligente (compara status antes/depois)
- Estado preservado entre rebuilds da tabela via variaveis globais
- `upload_map` com prioridade sucesso > erro > sem_video (multiplos registros/dia)
- Timeout de 12 segundos (4 tentativas x 3s) para sem_video
- Backend retorna `sem_video` imediato se `_find_ready_video` falha
- Cache reduzido de 10s para 3s (`_DASH_CACHE_TTL`)
- Script `reauth_channel_oauth.py` reescrito (aceita channel_id como argumento)
- Correcao OAuth "Cronicas da Coroa" (invalid_grant → re-autorizacao)

### 13/02/2026 - Dashboard v2 Integrado no Railway
- **Dashboard v2 integrado no main.py** (linhas 5994-6741)
- Acesso online: `/dash-upload` no Railway
- 4 novos endpoints: `/dash-upload`, `/api/dash-upload/status`, `/api/dash-upload/canais/{id}/historico`, `/api/dash-upload/historico-completo`
- Template HTML inline (~495 linhas) com design dark profissional
- Cache de 10s para performance
- Subnichos ordenados por quantidade de uploads com sucesso
- URLs relativas (funciona local e Railway)
- Socio pode acessar sem rodar nada local

### 13/02/2026 - Grande Atualizacao de UI e Features
- Titulos truncados (max 7 palavras + reticencias)
- Cards clicaveis para filtro por status
- Historico Individual: sem limite 30 dias, paginacao de 10, colunas reorganizadas
- Historico Completo: accordion por dia, idioma do canal, total = so sucessos
- UI profissional: animacoes em cards, botoes, modais, accordion
- Modais com fade-in/out + slide-down
- Accordion com max-height transition + seta rotacao CSS
- Status success com pulse animation
- Estilo unificado entre historicos (background, cores, padding)
- Correcao de timestamps com extrair_hora()
- Backend: sort apos merge de tabelas no historico individual
- Atualizacao de 1s para 5s + DOM diffing contra flickering

### 10/02/2026 - Suporte Arabe
- Tag de idioma AR adicionada

### Anteriores
- Sistema de upload automatico
- Dashboard com subnichos
- Integracao Google Sheets + OAuth

---

*Documentacao criada por Claude Code para Cellibs*
*Sistema desenvolvido para operacao de canais dark no YouTube*
