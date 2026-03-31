# GUIA COMPLETO DO COWORKER — Produção de Shorts

## O Que Você Faz

Você pega os scripts e prompts do dashboard e executa a produção no Freepik Spaces. Seu trabalho:

1. Ver o que precisa ser produzido (dashboard)
2. Executar no Freepik Spaces (gerar imagens, clips e narração)
3. Baixar tudo e organizar no Google Drive
4. Marcar como concluído (dashboard)

---

## ETAPA 1 — Dashboard

### Aba "Produção"

Abrir o dashboard no browser. Ir na aba **Produção**.

Cada card mostra:
- Título do vídeo
- Canal, subnicho e língua
- Botões: [Ver Script] [Ver Prompts] [Copiar JSON] [Abrir Drive]
- Botões de status: [Iniciar] [Concluído]

### Pegar um Short

1. Clicar **[Iniciar]** no card que vai produzir
2. Clicar **[Copiar JSON]** para acessar o conteúdo
3. Anotar a **língua** do canal (define a voz da narração)

### O que você precisa do JSON

```json
{
  "titulo": "Título do vídeo",
  "script": "Texto completo da narração...",
  "lingua": "portugues",
  "cenas": [
    {
      "cena": 1,
      "prompt_imagem": "Cinematic photorealistic...",
      "prompt_animacao": "Slow camera push..."
    },
    ...12 cenas
  ]
}
```

Você vai usar:
- Cada `cenas[].prompt_imagem` → bloco PROMPT IMAGEM do Spaces
- Cada `cenas[].prompt_animacao` → bloco PROMPT ANIMAÇÃO do Spaces
- `script` → bloco NARRAÇÃO do Spaces

---

## ETAPA 2 — Freepik Spaces

O workflow já existe e é SEMPRE o mesmo. Nunca criar um novo.

### Passo 1: Colar Prompts de Imagem

1. Clicar no bloco **PROMPT IMAGEM**
2. Colar o prompt da cena 1
3. Pressionar **Enter**
4. Colar o prompt da cena 2
5. Repetir até colar os 12 prompts, **sempre na ordem** (cena 1 primeiro, cena 12 por último)

### Passo 2: Verificar Gerador de Imagem

**OBRIGATÓRIO — BUG CONHECIDO**

1. Clicar no bloco **GERADOR IMAGEM** → clicar na **engrenagem**
2. Verificar que a quantidade está em **1**
3. **Para garantir**: adicionar 1 (fica 2), depois remover 1 (volta pra 1). Isso força o reset.
4. Se não fizer isso, pode gerar o DOBRO das imagens

Configuração correta:
- Modelo: **Z-Image**
- Resolução: **768 x 1344**
- Aspecto: **9:16**
- Quantidade: **1**

### Passo 3: Colar Prompts de Animação

1. Clicar no bloco **PROMPT ANIMAÇÃO**
2. Colar um por linha, na ordem
3. Prompt 1 de animação corresponde à imagem 1, prompt 2 à imagem 2, etc.
4. Total deve ser **12** (igual ao de prompts de imagem)

### Passo 4: Executar o Workflow (Imagens + Vídeos)

1. Clicar no bloco **PROMPT IMAGEM**
2. Clicar na **seta roxa para baixo** (canto superior do bloco)
3. Selecionar **"Todo o fluxo de trabalho"**
4. Clicar no **ícone de play** ao lado da seta
5. Vai pedir confirmação — **confirmar** para iniciar
6. Aguardar: imagens → vídeos (pode demorar alguns minutos)

**Nota**: Este workflow gera as imagens e os vídeos, mas NÃO gera a narração. A narração é feita separadamente no próximo passo.

### Passo 5: Gerar Narração (separado)

1. Clicar no bloco **NARRAÇÃO**
2. Colar o texto completo do script (campo `script` do JSON)
3. Selecionar a **voz correta** para a língua do canal:

| Língua | Voz |
|--------|-----|
| Português (PT-BR) | Lucas Moreira |
| Inglês (EN) | Caleb Morgan |
| Espanhol (ES) | Diego Marín |
| Francês (FR) | Diego Marín |
| Italiano (IT) | Giulio Ferrante |
| Russo (RU) | Léo Gamier |
| Japonês (JP) | Giulio Ferrante |
| Coreano (KO) | Ji-Hoon |
| Turco (TR) | Can Özkan |
| Polonês (PL) | Diego Marín |
| Alemão (DE) | Lukas Schneider |

Modelo é SEMPRE **ElevenLabs v2**.

4. Clicar no botão de gerar (ícone circular rosa no canto inferior direito do bloco)
5. Aguardar a narração ser gerada

### Passo 6: Verificar Resultado

Antes de baixar, conferir:
- **LISTA IMAGEM** tem exatamente 12 imagens (se tem mais, o bug do gerador aconteceu — limpar e refazer)
- **LISTA DE VÍDEOS** tem exatamente 12 vídeos
- **NARRAÇÃO** tem áudio gerado

---

## ETAPA 3 — Baixar e Organizar no Drive

### Baixar

Clicar em cada bloco e baixar pelo ícone de download:

| Bloco | O que baixar |
|-------|-------------|
| LISTA IMAGEM | Todas as 12 imagens |
| LISTA DE VÍDEOS | Todos os 12 clips |
| NARRAÇÃO | Áudio narrado (.mp3) |

### Organizar no Google Drive

1. Clicar no botão **[Abrir Drive]** do card no dashboard (leva direto pra pasta do canal)
2. Dentro da pasta do canal, criar uma pasta com as **3 primeiras palavras do título**
3. Dentro dessa pasta, criar duas subpastas: **img/** e **clips/**
4. Organizar:

```
{3 Primeiras Palavras do Título}/
├── narracao.mp3
├── img/
│   ├── cena_01.png
│   ├── cena_02.png
│   └── ... (12 imagens)
└── clips/
    ├── cena_01.mp4
    ├── cena_02.mp4
    └── ... (12 clips)
```

### Nomear arquivos

- Imagens: cena_01.png, cena_02.png, ..., cena_12.png (na ordem em que foram geradas)
- Clips: cena_01.mp4, cena_02.mp4, ..., cena_12.mp4 (na ordem)
- A ordem é importante — cena_01 corresponde ao primeiro prompt, cena_12 ao último

---

## ETAPA 4 — Finalizar no Dashboard

1. Voltar ao dashboard, aba **Produção**
2. Encontrar o card do short que produziu
3. Clicar **[Concluído]**
4. O card sai de Produção e vai para a aba **Edição**

---

## ETAPA 5 — Limpar o Spaces para o Próximo

1. Bloco **PROMPT IMAGEM** → 3 pontinhos → **Limpar lista**
2. Bloco **PROMPT ANIMAÇÃO** → 3 pontinhos → **Limpar lista**
3. Bloco **LISTA IMAGEM** → 3 pontinhos → **Limpar lista**
4. Bloco **LISTA DE VÍDEOS** → 3 pontinhos → **Limpar lista**
5. Bloco **NARRAÇÃO** → **excluir** o áudio/texto antigo

Depois de limpo, voltar à **ETAPA 1** e pegar o próximo card.

---

## Resumo Rápido

```
Dashboard: pegar card → [Iniciar]
    ↓
Spaces: colar 12 prompts imagem → conferir gerador (qtd=1) →
        colar 12 prompts animação → executar workflow (play + confirmar)
    ↓
Spaces: colar script na narração → selecionar voz → gerar narração
    ↓
Verificar: 12 imagens + 12 vídeos + 1 narração
    ↓
Drive: baixar tudo → organizar na pasta do canal (img/ + clips/ + narracao.mp3)
    ↓
Dashboard: [Concluído] → limpar Spaces → próximo card
```

---

## Erros Comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| Dobro de imagens geradas | Quantidade no gerador não estava em 1 | Limpar lista, fazer +1 -1 no gerador, refazer |
| Prompts fora de ordem | Colou errado | Limpar lista, colar novamente na ordem correta |
| Voz errada na narração | Não trocou a voz pro idioma | Verificar tabela de vozes, trocar antes de gerar |
| Narração não gerou com o workflow | Normal, narração é feita separadamente | Gerar manualmente no bloco NARRAÇÃO |
