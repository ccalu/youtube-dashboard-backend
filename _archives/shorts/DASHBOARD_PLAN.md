# SHORTS FACTORY — Dashboard Plan

## Design System (matching YouTube Dashboard v2)

### Cores
- Background: `hsl(230, 25%, 5%)` (#0a0f1a)
- Cards: `bg-white/[0.04] backdrop-blur-[16px] border border-white/[0.08]`
- Primary: `#8B5CF6` (purple)
- CTA/Success: `#22C55E` (green)
- Danger: `#EF4444` (red)
- Amber: `#FBBF24`
- Text: `#F0F3F9`
- Muted: `#8899BB`

### Glass Effects
- Cards: `bg-white/4 backdrop-blur-[16px] border-white/8`
- Hover: `border-white/12 shadow-glass-hover`
- Glow: `shadow-[0_0_24px_-4px_rgba(139,92,246,0.3)]`

### Typography
- Font: Inter (matching existing dash)
- Headings: Semi-bold/Bold
- Body: Regular 16px

### Stack
- React + TypeScript + Vite
- Tailwind CSS
- shadcn/ui
- Lucide icons (NO emojis)

---

## Estrutura: 4 Abas

### Tab 1: CRIAÇÃO
Onde o usuário cria novas produções.

**Componentes:**
- Dropdown: Selecionar Subnicho
- Dropdown: Selecionar Canal (filtra por subnicho)
- Input: Inserir tema OU botão "Sugerir 5 Temas"
- Cards: Temas sugeridos com checkbox pra selecionar
- Botão: "Gerar" (aciona Roteirista + Diretor)
- Mini resumo: contagem por status (produção, edição, prontos)

**Fluxo:**
1. Seleciona subnicho → filtra canais
2. Seleciona canal
3. Insere tema ou clica "Sugerir 5 Temas"
4. Seleciona 1 ou mais temas
5. Clica "Gerar" → Roteirista + Diretor rodam → produção criada
6. Card vai pra aba Produção automaticamente

### Tab 2: PRODUÇÃO
Fila do dev-browser/Coworker. O que precisa ser executado no Freepik Spaces.

**Componentes:**
- Cards de produção pendente, cada um com:
  - Título do vídeo
  - Canal + subnicho + língua
  - Botões: [Ver Script] [Ver Prompts] [Copiar JSON] [Abrir Drive]
  - Toggle: [Iniciar] (visual indica que está sendo feito)
  - Botão: [Concluído] → move pra Edição
  - Botão: [Excluir] (com confirmação)

### Tab 3: EDIÇÃO
O que já foi gerado no Spaces e aguarda pós-produção (Remotion).

**Componentes:**
- Cards de edição pendente:
  - Título do vídeo
  - Canal
  - Info: 12 clips + narração prontos
  - Link: Pasta no Drive/Local
  - Botão: [Concluído] → move pra Prontos

### Tab 4: PRONTOS
Histórico de tudo que foi finalizado.

**Componentes:**
- Filtros: Subnicho, Canal, Mês
- Cards finalizados:
  - Título
  - Canal + data
  - [Ver Copy] [Abrir Pasta]
- Contagem total por subnicho/canal

---

## API Endpoints (Backend FastAPI)

```
GET  /api/shorts/subnichos          → lista subnichos
GET  /api/shorts/canais?subnicho=X  → lista canais do subnicho
POST /api/shorts/sugerir-temas      → GPT-4 Mini sugere 5 temas
POST /api/shorts/gerar              → Roteirista + Diretor geram tudo
GET  /api/shorts/producoes          → lista todas produções
GET  /api/shorts/producoes?status=X → filtra por status
PATCH /api/shorts/producoes/:id     → atualiza status (producao→edicao→pronto)
DELETE /api/shorts/producoes/:id    → exclui produção
GET  /api/shorts/producoes/:id/json → retorna JSON completo
```

---

## Supabase: Tabela `shorts_production`

Já criada:
- id, production_id, canal_id, canal, subnicho, lingua
- titulo, estrutura, producao_json, drive_link
- status (producao / edicao / pronto)
- created_at, updated_at

---

## Wireframes

### Criação
```
┌─────────────────────────────────────────────────────┐
│  SHORTS FACTORY                                      │
├──────────┬───────────┬──────────┬───────────────────┤
│ Criação  │ Produção  │  Edição  │  Prontos          │
├──────────┴───────────┴──────────┴───────────────────┤
│                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ 3       │ │ 5       │ │ 2       │ │ 47       │  │
│  │Produção │ │ Edição  │ │ Pronto  │ │ Total    │  │
│  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │
│                                                      │
│  ── Nova Produção ────────────────────────────────── │
│                                                      │
│  Subnicho  [Reis Perversos          ▼]               │
│  Canal     [(PT) Crônicas da Coroa  ▼]               │
│                                                      │
│  [Inserir tema________________] [Sugerir 5 Temas]    │
│                                                      │
│  ☐ A Queda de Nero — E20                            │
│  ☐ Os Venenos dos Médici — E21                      │
│  ☐ Vlad e a Floresta — E25                          │
│                                                      │
│           [Gerar Selecionados]                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Produção
```
┌─────────────────────────────────────────────────────┐
│  ┌─── Card ──────────────────────────────────────┐  │
│  │ O Sniper Mais Letal da Finlândia              │  │
│  │ (PT) Crônicas da Guerra · Frentes de Guerra   │  │
│  │                                                │  │
│  │ [Ver Script] [Ver Prompts] [JSON] [Drive]     │  │
│  │                                                │  │
│  │      [● Iniciar]           [✓ Concluído]      │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── Card ──────────────────────────────────────┐  │
│  │ 어둠의 왕의 최후                                │  │
│  │ (KO) 어둠의 왕국들 · Reis Perversos            │  │
│  │ ...                                            │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Projeto Separado

```
shorts-factory-dashboard/
├── package.json
├── vite.config.ts
├── tailwind.config.ts     ← copiar paleta do YouTube dash v2
├── src/
│   ├── App.tsx
│   ├── index.css          ← copiar glass effects do YouTube dash v2
│   ├── components/
│   │   ├── ui/            ← shadcn components
│   │   ├── tabs/
│   │   │   ├── CriacaoTab.tsx
│   │   │   ├── ProducaoTab.tsx
│   │   │   ├── EdicaoTab.tsx
│   │   │   └── ProntosTab.tsx
│   │   ├── ProductionCard.tsx
│   │   ├── ThemeSuggestions.tsx
│   │   └── StatusBadge.tsx
│   ├── lib/
│   │   ├── api.ts         ← chamadas ao backend
│   │   └── supabase.ts    ← client Supabase direto
│   └── types/
│       └── shorts.ts      ← tipos TypeScript
├── Dockerfile             ← deploy Railway
└── railway.json
```
