# REMOTION — Estilo de Legendas para Shorts

## Visão Geral

O Claude Code usa Remotion + Whisper para a pós-produção dos Shorts:
1. Whisper no áudio → timestamps por palavra
2. Remotion monta: clips ajustados + áudio + legendas animadas word-by-word
3. Exporta video_final.mp4

---

## Estilo de Legenda: Word-by-Word com Highlight

Estilo TikTok/Shorts clássico — texto aparece conforme a fala, com destaque na palavra sendo falada.

### Fonte

- **Fonte**: Montserrat ExtraBold (Google Font, gratuita)
- **Peso**: 800 (ExtraBold)
- **Tamanho**: 70px (em canvas 1080px de largura)
- **Caixa**: TUDO EM MAIÚSCULAS (text-transform: uppercase)
- **Espaçamento entre letras**: -1px (levemente apertado)
- **Altura da linha**: 1.1
- **Alinhamento**: Centro
- **Máximo por linha**: 3-4 palavras, 1-2 linhas visíveis

### Posição na Tela (9:16 — 1080x1920)

```
Posição Y do centro do texto: 1200px (62.5% do topo)
```

Isso coloca a legenda **levemente abaixo do centro** — a posição clássica para mobile que:
- Não cobre o conteúdo visual principal (terço superior)
- Fica acima dos botões do YouTube/TikTok (terço inferior)
- Está na zona natural de leitura do mobile

```
┌─────────────┐
│             │  0-15%    UI da plataforma
│   IMAGEM    │  15-50%   Conteúdo visual principal
│             │
│  ─ ─ ─ ─ ─ │  50%      Centro
│             │
│  LEGENDAS   │  60-66%   ← AQUI (Y=1200px)
│             │
│             │  85-100%  Botões da plataforma
└─────────────┘
```

### Cores Base (todos os subnichos)

| Elemento | Cor |
|----------|-----|
| Texto padrão | Branco `#FFFFFF` |
| Contorno do texto (stroke) | Preto `#000000`, 4px |
| Sombra | Preto, 0px 4px 6px, opacidade 80% |
| **Palavra ativa — texto** | Preto `#000000` (texto fica preto sobre o box) |
| Box highlight | Cantos arredondados 8px, padding 6px |

### Cor do Highlight por Subnicho

| Subnicho | Cor do Box | Hex |
|----------|-----------|-----|
| Reis Perversos | Roxo | `#9B30FF` |
| Histórias Sombrias | Roxo | `#9B30FF` |
| Culturas Macabras | Roxo | `#9B30FF` |
| Relatos de Guerra | Verde | `#00CC44` |
| Frentes de Guerra | Verde | `#00CC44` |
| Guerras e Civilizações | Laranja | `#FF8C00` |
| Mansões | Vermelho | `#E51A1A` |

Assim cada grupo de subnichos tem identidade visual própria nas legendas.

### Como Funciona a Animação

```
Exemplo de frase: "Giuseppe Martinelli chegou ao Brasil"

Segundo 0.0: "GIUSEPPE" (highlight amarelo) "MARTINELLI CHEGOU AO BRASIL"
Segundo 0.4: "GIUSEPPE" "MARTINELLI" (highlight) "CHEGOU AO BRASIL"
Segundo 0.8: "GIUSEPPE MARTINELLI" "CHEGOU" (highlight) "AO BRASIL"
Segundo 1.0: "GIUSEPPE MARTINELLI CHEGOU" "AO" (highlight) "BRASIL"
Segundo 1.1: "GIUSEPPE MARTINELLI CHEGOU AO" "BRASIL" (highlight)
```

- Cada palavra recebe o highlight pelo tempo que é falada (timestamps do Whisper)
- Transição: **snap instantâneo** (sem fade, sem animação suave)
- Grupos de 3-5 palavras aparecem juntos na tela
- Quando o grupo termina, próximo grupo aparece (snap)

### Parâmetros para Remotion

```typescript
// Configuração base
const captionStyle = {
  fontFamily: 'Montserrat',
  fontWeight: 800,
  fontSize: 70,
  textTransform: 'uppercase',
  letterSpacing: -1,
  lineHeight: 1.1,
  textAlign: 'center',
  color: '#FFFFFF',
  WebkitTextStroke: '4px #000000',
  textShadow: '0px 4px 6px rgba(0, 0, 0, 0.8)',
  position: 'absolute',
  top: '62.5%',  // Y = 1200px em 1920px
  left: '50%',
  transform: 'translate(-50%, -50%)',
  maxWidth: '90%',
  wordSpacing: '4px',
};

// Highlight da palavra ativa
const highlightStyle = {
  backgroundColor: '#FFE500',
  color: '#000000',
  borderRadius: '8px',
  padding: '2px 6px',
  WebkitTextStroke: '0px',  // remove stroke no highlight
};
```

---

## Pipeline Completo do Claude Code

```
1. Detectar pasta com status "edicao" no Supabase
2. Baixar do Drive: 12 clips + narracao.mp3
3. Rodar Whisper na narracao.mp3 → timestamps por palavra
4. Remotion:
   a. Calcular duração do áudio
   b. Distribuir 12 clips no tempo (ajustar velocidade de cada um)
   c. Sobrepor áudio
   d. Renderizar legendas word-by-word com timestamps do Whisper
   e. Exportar video_final.mp4 (1080x1920, 9:16)
5. Upload video_final.mp4 pro Drive (mesma pasta)
6. Marcar como "pronto" no dashboard (clicar botão ou API)
```

---

## Repos Necessários

- **Remotion Skills**: `C:\Users\PC\Desktop\ContentFactory\remotion-skills\`
- **UI/UX Pro Max Skill**: `C:\Users\PC\Desktop\ContentFactory\ui-ux-pro-max-skill\`
