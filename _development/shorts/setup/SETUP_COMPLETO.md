# Setup Completo — Shorts Factory (Atualizado 2026-04-11)

> Guia para configurar o sistema completo de producao de YouTube Shorts em um novo PC.
> Enviar esta pasta (`setup/`) com `setup_shorts.py` para o novo PC.
> O script faz quase tudo automaticamente.

---

## Pre-requisitos (instalar manualmente)

### 1. Python 3.10+
- Download: https://www.python.org/downloads/
- **IMPORTANTE:** Marcar "Add Python to PATH" na instalacao
- Verificar: `python --version`

### 2. Node.js 18+
- Download: https://nodejs.org/ (LTS)
- Verificar: `node --version` e `npm --version`

### 3. Git
- Download: https://git-scm.com/downloads
- Verificar: `git --version`

### 4. ffmpeg
- Download: https://github.com/BtbN/FFmpeg-Builds/releases (ffmpeg-master-latest-win64-gpl.zip)
- Extrair e adicionar a pasta `bin/` ao PATH do Windows
- Verificar: `ffmpeg -version`

### 5. Google Chrome
- Download: https://www.google.com/chrome/
- Verificar: instalado em `C:\Program Files\Google\Chrome\Application\chrome.exe`

### 6. Claude Code CLI
- Instalar: `npm install -g @anthropic-ai/claude-code`
- Fazer login: `claude login` (precisa de conta Max)
- Verificar: `claude --version`

---

## Setup Automatizado

Depois de instalar os pre-requisitos, copiar esta pasta para o novo PC e rodar:

```bash
python setup_shorts.py
```

O script faz automaticamente:
1. Clona os repositorios (backend, shorts-editor, shorts-factory-dashboard)
2. Instala dependencias Python (`pip install -r requirements.txt` + extras)
3. Instala dependencias Node (shorts-editor + dashboard)
4. Instala Playwright
5. Configura `.env` (pede as chaves interativamente)
6. Copia arquivos de credenciais (service account)
7. Cria pastas necessarias (SHORTS, MUSICAS-SHORTS)
8. Cria profile do Chrome pra debug
9. Faz build do dashboard
10. Testa conexoes (Supabase, Drive, Sheets)
11. Cria arquivo `.bat` de inicializacao rapida

---

## Credenciais Necessarias

Antes de rodar o setup, ter em maos:

| Credencial | Onde pegar |
|---|---|
| SUPABASE_URL | Supabase Dashboard > Settings > API |
| SUPABASE_KEY (anon) | Supabase Dashboard > Settings > API |
| SUPABASE_SERVICE_ROLE_KEY | Supabase Dashboard > Settings > API |
| OPENAI_API_KEY | https://platform.openai.com/api-keys |
| GOOGLE_SERVICE_ACCOUNT_JSON | Copiar do PC principal (.env) |
| GOOGLE_SHEETS_CREDENTIALS_2 | Copiar do PC principal (.env) |
| Service Account JSON (arquivo) | Copiar `service-account-492821-*.json` do PC principal |

**DICA:** A forma mais facil e copiar o `.env` completo do PC principal pro novo PC.

---

## Estrutura Final

Apos o setup, a estrutura fica:

```
C:\Users\<usuario>\Desktop\ContentFactory\
├── youtube-dashboard-backend\    # Backend (API + endpoints)
│   ├── .env                      # Credenciais
│   ├── main.py                   # Servidor principal
│   ├── shorts_endpoints.py       # Endpoints de shorts
│   └── _features\shorts_production\  # Pipeline de producao
├── shorts-editor\                # Remotion (renderizacao de video)
└── shorts-factory-dashboard\     # Frontend React (dash)

C:\Users\<usuario>\Downloads\SHORTS\
├── MUSICAS-SHORTS\               # Musicas de fundo
│   ├── Musicas 02\               # Guerras e Civilizacoes
│   ├── Musicas 03\               # Relatos/Frentes de Guerra
│   ├── Musicas 05\               # Reis Perversos/Sombrias/Macabras
│   └── Musicas 06\               # Monetizados
├── Guerras e Civilizacoes\       # Producoes por subnicho
├── Frentes de Guerra\
├── Relatos de Guerra\
├── Reis Perversos\
├── Historias Sombrias\
├── Culturas Macabras\
└── Monetizados\

C:\Users\<usuario>\chrome-debug-profile\  # Chrome profile pra Freepik
```

---

## Musicas

As pastas de musica precisam ser copiadas manualmente do PC principal:
```
C:\Users\PC\Downloads\SHORTS\MUSICAS-SHORTS\ → copiar toda a pasta
```

Sem as musicas, o Remotion nao adiciona trilha sonora nos videos.

---

## Freepik — Login Manual

Apos o setup, abrir o Chrome com debug port (o `.bat` faz isso automaticamente) e:
1. Abrir https://br.freepik.com/
2. Fazer login com a conta do Freepik
3. Acessar o workspace: https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce
4. Confirmar que o workspace carrega (deve mostrar os blocos de imagem, animacao, narracao)

**IMPORTANTE:** O Chrome deve estar em **fullscreen** pra selecao de voz funcionar corretamente.

---

## Iniciar o Sistema

Duplo clique no arquivo criado na area de trabalho:
```
INICIAR_SHORTS_FACTORY.bat
```

Isso inicia:
1. Backend (porta 8000)
2. Chrome com debug port (porta 9222) + Freepik
3. Dashboard frontend (porta 5173)

---

## Operacao com 2 PCs

Para rodar producao em 2 PCs simultaneamente:

**PC 1 (principal):** Produz Leva 1 (18 canais)
- Reis Perversos (9) + Guerras e Civilizacoes (5) + Frentes de Guerra (4)

**PC 2 (producao):** Produz Leva 2 (17 canais)
- Relatos de Guerra (5) + Monetizados (5) + Culturas Macabras (4) + Historias Sombrias (3)

Ambos usam o mesmo Supabase, Sheets e Drive. O dash em qualquer PC mostra tudo junto.

**Regra:** Nunca produzir o mesmo short nos 2 PCs. Usar o filtro por Leva no modal de Produzir.

---

## Portas

| Servico | Porta |
|---|---|
| Backend API | 8000 |
| Chrome CDP | 9222 |
| Dashboard Dev | 5173 |
| Remotion Studio | 3000 |

---

## Troubleshooting

| Problema | Solucao |
|---|---|
| Freepik nao conecta | Verificar Chrome com `--remote-debugging-port=9222` |
| Voz errada no Freepik | Chrome em fullscreen |
| Claude CLI timeout | Verificar login: `claude login` |
| Supabase erro RLS | Usar SUPABASE_SERVICE_ROLE_KEY pra OAuth |
| Sheets 429 rate limit | Espera automatica 60s (retry built-in) |
| Download 0 bytes | Verificar internet, Freepik logado |
