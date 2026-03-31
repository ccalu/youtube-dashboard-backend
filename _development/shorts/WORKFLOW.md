# WORKFLOW DE PRODUÇÃO DE SHORTS

## Arquitetura

```
PC (Dashboard + Claude Code)     Google Drive (ponte)     MacBook (Coworker)

Dashboard Railway ──────────→   /Shorts Production/   ←── Freepik Spaces
Roteirista (Claude CLI)              Canal X/              gera img, clips, áudio
Diretor (Claude CLI)                   Titulo Do Video/
Remotion + Whisper                       img/
                                         clips/
                                         narracao.mp3
                                         producao.json
                                         copy.txt
                                         PRONTO.txt
```

---

## Fluxo Completo (3 Etapas)

### Etapa 1 — Dashboard (PC, Railway)
Central de controle. Acessível de qualquer lugar.

```
1. Usuário seleciona subnicho → canal
2. Insere tema OU clica "Sugerir 5 temas" (GPT-4 Mini, rápido)
3. Seleciona 1 ou mais temas
4. Clica "Gerar"
5. Roteirista (Claude CLI) → título + descrição + script + CTA
6. Diretor (Claude CLI) → 12 prompts imagem + 12 prompts animação
7. Tudo salvo no Supabase → status: "pendente"
8. producao.json disponível para o Coworker
```

### Etapa 2 — Coworker (MacBook, Freepik Spaces)
Geração de assets. Só lê, nunca escreve no Supabase.

```
1. Lê producao.json (do Supabase ou Drive)
2. Abre Freepik Spaces
3. Cola 12 prompts de imagem (1 por linha, na ordem)
4. Confere gerador de imagem: quantidade = 1 (bug: fazer +1 -1)
5. Cola 12 prompts de animação (1 por linha, na ordem)
6. Cola script no bloco de narração
7. Executa "Todo o fluxo de trabalho"
8. Aguarda geração de imagens + clips + áudio
9. Gera vídeo final manualmente (bug: clicar no bloco VIDEO FINAL)
10. Baixa tudo e organiza no Google Drive:
    - img/ (12 imagens)
    - clips/ (12 clips)
    - narracao.mp3
    - copy.txt (título + descrição + script)
    - producao.json
11. Cria arquivo PRONTO.txt na pasta (sinal pro backend)
12. Limpa o Spaces para próximo vídeo
```

### Etapa 3 — Claude Code + Remotion (PC)
Pós-produção. Edição, legendas, exportação.

```
1. Backend detecta PRONTO.txt no Drive → status: "aguardando_edicao"
2. Usuário diz "veja os novos vídeos e faça a edição" (ou automático)
3. Claude Code para cada pasta aguardando edição:
   a. Baixa: 12 clips + áudio do Drive
   b. Roda Whisper no áudio → timestamps por palavra
   c. Remotion:
      - Ajusta velocidade dos 12 clips para encaixar no tempo do áudio
      - Sincroniza legendas com timestamps do Whisper
      - Monta vídeo final: clips + áudio + legendas
   d. Exporta video_final.mp4
   e. Salva no Drive na mesma pasta
   f. Cria FINALIZADO.txt na pasta
4. Backend detecta FINALIZADO.txt → status: "finalizado"
```

---

## Estrutura de Pastas (Google Drive)

```
Google Drive/
└── Shorts Production/
    ├── Grandes Mansões/
    │   ├── O Imigrante Sem/
    │   │   ├── producao.json
    │   │   ├── narracao.mp3
    │   │   ├── copy.txt
    │   │   ├── video_final.mp4
    │   │   ├── PRONTO.txt
    │   │   ├── FINALIZADO.txt
    │   │   ├── img/
    │   │   │   ├── cena_01.png
    │   │   │   └── ...
    │   │   └── clips/
    │   │       ├── cena_01.mp4
    │   │       └── ...
    │   └── A Mansão Que/
    │       └── ...
    ├── Relatos de Guerra/
    │   └── ...
    └── Reis Perversos/
        └── ...
```

**Nome da pasta**: 3 primeiras palavras do título do vídeo.

---

## JSON de Produção (producao.json)

```json
{
  "titulo": "O Imigrante Sem Dinheiro Que Construiu o Primeiro Arranha-Céu do Brasil",
  "descricao": "Chegou sem um centavo. Ergueu o prédio mais alto da América Latina.\n\n#HistóriaDoBrasil #Mansões #ArquiteturaBrasileira",
  "script": "Giuseppe Martinelli chegou ao Brasil sem um centavo.\n\nNão falava português...",
  "canal": "Grandes Mansões",
  "subnicho": "Mansões",
  "lingua": "portugues",
  "estrutura": "E12",
  "cenas": [
    {
      "cena": 1,
      "prompt_imagem": "Cinematic photorealistic...",
      "prompt_animacao": "Camera slowly tilting..."
    }
  ]
}
```

---

## Supabase — Tabela `shorts_production`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | serial | Auto |
| production_id | uuid | Auto |
| canal | text | Nome do canal |
| subnicho | text | Subnicho |
| lingua | text | Língua do canal |
| titulo | text | Título do vídeo |
| descricao | text | Descrição YouTube |
| script | text | Script narrado |
| estrutura | text | Estrutura usada (E1-E27) |
| producao_json | jsonb | JSON completo com prompts |
| drive_folder | text | Nome da pasta no Drive (3 primeiras palavras) |
| status | text | pendente / em_producao / aguardando_edicao / em_edicao / finalizado |
| created_at | timestamptz | Data de criação |
| updated_at | timestamptz | Última atualização |

### Detecção Automática de Status

O backend NÃO depende do Coworker ou Claude Code para atualizar status:

| Condição | Status |
|----------|--------|
| JSON gerado, pasta no Drive ainda não existe | `pendente` |
| Arquivo `PRONTO.txt` detectado na pasta | `aguardando_edicao` |
| Claude Code iniciou edição | `em_edicao` |
| Arquivo `FINALIZADO.txt` detectado na pasta | `finalizado` |

---

## Dashboard (Railway)

### Funcionalidades

**Criar Produção:**
- Selecionar subnicho → canal
- Inserir tema OU "Sugerir 5 temas" (GPT-4 Mini)
- Selecionar temas → "Gerar" → Roteirista + Diretor

**Fila de Produção:**
- Lista de todas produções com status em tempo real (polling 10-15s)
- Filtrar por canal / subnicho / status
- Ver JSON de cada produção

**Histórico:**
- Tudo que foi produzido, por canal, por data
- Contagem: "Grandes Mansões: 23 shorts finalizados"
- Estruturas mais usadas por subnicho

---

## Quem Faz O Quê

| Componente | Onde roda | O que faz | Escreve no Supabase? |
|------------|-----------|-----------|---------------------|
| Dashboard | Railway | Interface de controle, criar produções | SIM |
| Roteirista | PC (Claude CLI) | Gera script + título + descrição | SIM (via dashboard) |
| Diretor | PC (Claude CLI) | Gera 12 prompts imagem + animação | SIM (via dashboard) |
| GPT-4 Mini | API | Sugere 5 temas rapidamente | NÃO (retorna pro dashboard) |
| Coworker | MacBook | Executa no Spaces, baixa pro Drive | NÃO (só cria PRONTO.txt) |
| Claude Code | PC | Remotion + Whisper, edição final | NÃO (só cria FINALIZADO.txt) |
| Backend | Railway | Monitora Drive, atualiza status | SIM (automático) |
