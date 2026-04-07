# Setup Completo — Shorts Factory

> Guia para configurar o sistema completo de producao de YouTube Shorts em um novo PC.
> Enviar este documento + `setup_shorts.py` para o Claude Code no novo PC.

---

## Pre-requisitos (instalar manualmente se nao tiver)

### 1. Python 3.10+
- Download: https://www.python.org/downloads/
- Marcar "Add Python to PATH" na instalacao
- Verificar: `python --version`

### 2. Node.js 18+
- Download: https://nodejs.org/
- Verificar: `node --version` e `npm --version`

### 3. Git
- Download: https://git-scm.com/downloads
- Verificar: `git --version`

### 4. ffmpeg
- Download: https://ffmpeg.org/download.html
- Adicionar ao PATH
- Verificar: `ffmpeg -version`

### 5. Google Chrome
- Download: https://www.google.com/chrome/
- Verificar: instalado em `C:\Program Files\Google\Chrome\Application\chrome.exe`

---

## Setup Automatizado

Depois de instalar os pre-requisitos acima, rodar:

```bash
python setup_shorts.py
```

Este script faz:
1. Clona os repositorios (backend, shorts-editor, dashboard)
2. Instala dependencias Python (pip install)
3. Instala dependencias Node (npm install)
4. Configura .env (pede as chaves interativamente)
5. Cria pastas necessarias (SHORTS, MUSICAS-SHORTS)
6. Configura Chrome com debug port
7. Faz build do dashboard
8. Testa conexoes (Supabase, Freepik)

---

## Configuracao Manual (apos script)

### 1. Login no Freepik Spaces (unica vez)

1. Abrir Chrome com debug port:
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\SEU_USUARIO\chrome-debug-profile
```

2. Navegar para: https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce

3. Fazer login na conta do Freepik

4. Verificar que o workspace "PRODUCTION SHORTS" esta aberto

5. Fechar o Chrome

Pronto! O perfil fica salvo. Proximas vezes o login ja esta feito.

### 2. Musicas de Fundo

Copiar a pasta `MUSICAS-SHORTS` para:
```
C:\Users\SEU_USUARIO\Downloads\SHORTS\MUSICAS-SHORTS\
```

Estrutura necessaria:
```
MUSICAS-SHORTS/
  Musicas 02/music/  (Guerras e Civilizacoes)
  Musicas 03/music/  (Relatos/Frentes de Guerra)
  Musicas 05/music/  (Reis Perversos/Sombrias/Macabras)
  Musicas 06/music/  (Monetizados)
```

---

## Variaveis de Ambiente (.env)

O script `setup_shorts.py` cria o .env automaticamente. Chaves necessarias:

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...  (anon key)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...  (service role key)

# OpenAI (para theme_suggester)
OPENAI_API_KEY=sk-...

# Google Drive Service Account
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":...}

# JWT (gerado automaticamente se nao definir)
JWT_SECRET_KEY=...

# Shorts
SHORTS_LOCAL_PATH=C:\Users\SEU_USUARIO\Downloads\SHORTS
```

---

## Estrutura de Pastas

```
C:\Users\SEU_USUARIO\
  Desktop\
    ContentFactory\
      youtube-dashboard-backend\     (backend principal)
      shorts-editor\                 (Remotion)
      shorts-factory-dashboard\      (dashboard React)
  Downloads\
    SHORTS\                          (producoes locais)
      MUSICAS-SHORTS\                (musicas de fundo)
      Reis Perversos\
      Relatos de Guerra\
      ...
  chrome-debug-profile\              (perfil Chrome pra Freepik)
```

---

## Como Iniciar (dia a dia)

### Opcao 1: Atalho (INICIAR_SHORTS_FACTORY.bat)
- Duplo clique no atalho do Desktop
- Abre backend + dashboard + Chrome com Freepik

### Opcao 2: Manual
```bash
# Terminal 1 — Backend
cd youtube-dashboard-backend
python run_shorts_server.py

# Terminal 2 — Dashboard (dev mode)
cd shorts-factory-dashboard
npm run dev

# Terminal 3 — Chrome com Freepik
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\SEU_USUARIO\chrome-debug-profile https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce
```

### Acessar
- Dashboard: http://localhost:5173
- Backend API: http://localhost:8000
- Freepik status: http://localhost:8000/api/shorts/browser-status

---

## Verificacao

Depois de tudo configurado, verificar:

1. Dashboard abre em localhost:5173
2. "Freepik Conectado" aparece verde
3. Criar uma producao de teste
4. Clicar "Produzir Tudo" e verificar se:
   - Freepik limpa, cola prompts, executa
   - Remotion renderiza
   - Drive upload funciona
   - Video aparece em "Prontos"

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| `playwright` nao conecta | Chrome nao esta com --remote-debugging-port=9222 |
| Whisper lento | Normal em CPU (~18s). GPU acelera mas nao e necessario |
| Upload Drive falha | Verificar GOOGLE_SERVICE_ACCOUNT_JSON no .env |
| Freepik nao cola prompts | Verificar se workspace PRODUCTION SHORTS esta aberto |
| gdown nao encontrado | `pip install gdown` |
| Musica nao selecionada | Verificar pasta MUSICAS-SHORTS no caminho correto |
