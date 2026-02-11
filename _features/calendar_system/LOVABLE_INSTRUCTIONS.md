# 📅 INSTRUÇÕES PARA IMPLEMENTAR SISTEMA DE CALENDÁRIO NO DASHBOARD

## ✅ **STATUS DO BACKEND: 100% PRONTO E FUNCIONANDO!**

### 🎉 Backend Completo em Produção
- **8 endpoints REST API** funcionando perfeitamente
- **Banco de dados Supabase** com tabelas criadas
- **Validações robustas** implementadas
- **Todos os bugs corrigidos** e testados

### 🔗 URL da API
```
Produção: https://youtube-dashboard-backend-production.up.railway.app/api/calendar
Local: http://localhost:8000/api/calendar
```

### ✅ Bugs Já Resolvidos (não se preocupe com eles)
1. **Erro 500** - Acesso ao Supabase corrigido
2. **Erro 422** - Validações melhoradas
3. **Tradução PT→EN** - Aceita "monetizacao" e converte para "monetization"
4. **Category NULL** - Monetização/Desmonetização sempre salvam sem categoria

---

## 🎯 **A IDEIA PRINCIPAL**

Quero criar uma **nova aba chamada "Calendário"** dentro da seção **"Ferramentas"** do nosso dashboard. Será um **calendário empresarial estilo Google Calendar** onde os 4 sócios da empresa (Cellibs, Arthur, Lucca e João) podem registrar eventos, atividades e marcos importantes do negócio.

### **Por que precisamos disso:**
- Para ter visibilidade de todas as atividades da empresa
- Registrar quando canais são monetizados/desmonetizados
- Cada sócio pode adicionar suas atividades
- Buscar eventos passados facilmente
- Organização visual por cores e categorias

---

## 📍 **ONDE VAI FICAR**

```
Dashboard (seu dashboard existente)
└── Seção: Ferramentas
    ├── Aba: Kanban (já existe - NÃO MEXER)
    ├── Aba: Calendário (CRIAR ESTA NOVA) ← AQUI
    └── Outras abas... (NÃO MEXER)
```

**IMPORTANTE:**
- ✅ Adicione APENAS a nova aba "Calendário"
- ❌ NÃO modifique nenhuma outra parte do dashboard
- ✅ Use os MESMOS componentes UI que já existem (Card, Button, Dialog, etc)
- ✅ Mantenha o MESMO padrão visual do dashboard

---

## 👥 **OS 4 SÓCIOS DA EMPRESA**

Cada sócio tem um emoji único para identificação visual:

| Emoji | Nome | Função |
|-------|------|---------|
| 🎯 | Cellibs | Sistemas e Automação |
| 📝 | Arthur | Copywriter e Títulos |
| 🎬 | Lucca | Produção de Vídeos |
| 🎨 | João | Designer de Thumbnails |

---

## 🎨 **SISTEMA DE CATEGORIAS E CORES**

Os eventos podem ter 4 categorias com cores específicas:

| Emoji | Categoria | Uso |
|-------|-----------|-----|
| 🟡 | Geral | Reuniões, ideias, notas gerais |
| 🔵 | Desenvolvimento | Código, sistemas, features |
| 🟣 | Financeiro | Pagamentos, contratos |
| 🔴 | Urgente | Bugs críticos, problemas |

**Eventos especiais (sem categoria):**
- 💰 **Canal Monetizado** - Quando um canal é aprovado no YouTube
- ❌ **Canal Desmonetizado** - Quando um canal perde monetização

---

## 🖥️ **LAYOUT VISUAL DO CALENDÁRIO**

### **1. TELA PRINCIPAL - Calendário Mensal:**

Crie um grid de calendário similar ao Google Calendar:

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Calendário Empresarial                                 │
│                                                             │
│  [Dropdown: Mês ▼] [Dropdown: Ano ▼]                      │
│                                   [+ Novo Evento] [🔍 Buscar]│
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Dom   Seg   Ter   Qua   Qui   Sex   Sáb            │ │
│  ├──────┬──────┬──────┬──────┬──────┬──────┬──────────┤ │
│  │  2   │  3   │  4   │  5   │  6   │  7   │  8        │ │
│  │      │ 🎯   │ 🎬   │      │ 💰   │ 🎨   │          │ │
│  │      │ •2   │ •1   │      │      │ •1   │          │ │
│  ├──────┼──────┼──────┼──────┼──────┼──────┼──────────┤ │
│  │  9   │ 10   │ 11   │ 12   │ 13   │ 14   │ 15       │ │
│  │ 🎬   │ 🎯   │ 📝   │ ❌   │      │ 🎬🎨 │          │ │
│  │ •1   │ •2   │ •4   │      │      │ •3   │          │ │
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Cada célula do dia deve mostrar:**
- Número do dia no canto superior esquerdo
- Emojis dos sócios que criaram eventos (máximo 4 emojis)
- 💰 se houve monetização neste dia
- ❌ se houve desmonetização neste dia
- Quantidade de eventos (•1, •2, •3, etc) ou pontos (•••)
- Ao clicar em qualquer dia → Abre modal com eventos do dia
- Dias do mês atual com fundo branco, outros meses com fundo cinza claro
- Dia de hoje com borda azul destacada

---

### **2. MODAL: CRIAR NOVO EVENTO**

Quando clicar em "+ Novo Evento", abrir este modal overlay:

```
┌─────────────────────────────────────────────────────────────┐
│  ➕ Novo Evento                                        [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Quem está criando este evento? *                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  ( ) 🎯 Cellibs        ( ) 📝 Arthur                  │ │
│  │  ( ) 🎬 Lucca          ( ) 🎨 João                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Data do evento:                                           │
│  [Campo de seleção de data]                               │
│                                                             │
│  Título do evento: *                                       │
│  [_______________________________________________________] │
│                                                             │
│  Descrição/Detalhes:                                      │
│  [_______________________________________________________] │
│  [_______________________________________________________] │
│  [_______________________________________________________] │
│                                                             │
│  Tipo de evento:                                           │
│  ( ) Evento Normal                                         │
│  ( ) 💰 Canal foi Monetizado                              │
│  ( ) ❌ Canal foi Desmonetizado                           │
│                                                             │
│  SE "Evento Normal" selecionado, mostrar:                  │
│  Categoria do evento:                                      │
│  ( ) 🟡 Geral     ( ) 🔵 Desenvolvimento                  │
│  ( ) 🟣 Financeiro ( ) 🔴 Urgente                         │
│                                                             │
│                         [Cancelar] [💾 Salvar Evento]      │
└─────────────────────────────────────────────────────────────┘
```

**Regras importantes:**
- Se selecionar "💰 Monetizado" ou "❌ Desmonetizado" → NÃO mostrar opções de categoria
- Campos obrigatórios: Quem criou + Título
- NÃO precisa de campo de horário (apenas data)
- Modal com overlay escuro e transição suave (fade in/out)

---

### **3. MODAL: VISUALIZAR DIA**

Quando clicar em um dia do calendário:

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Terça, 11 de Fevereiro de 2026                    [X] │
├─────────────────────────────────────────────────────────────┤
│                                        [+ Adicionar Evento]│
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🎯 Cellibs                                          │  │
│  │ 🔵 Deploy do sistema de comentários                 │  │
│  │ ─────────────────────────────────────               │  │
│  │ Sistema agora coleta e analisa comentários          │  │
│  │ automaticamente de todos os canais                  │  │
│  │                                [Editar] [Deletar]   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📝 Arthur                                           │  │
│  │ 💰 Canal "Terror Histórico BR" monetizado!         │  │
│  │ ─────────────────────────────────────               │  │
│  │ Alcançamos 1.247 inscritos e 4.500 horas           │  │
│  │ assistidas. Canal aprovado no programa!             │  │
│  │                                [Editar] [Deletar]   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📝 Arthur                                           │  │
│  │ 🟡 Análise: 5 vídeos viralizaram essa semana       │  │
│  │ ─────────────────────────────────────               │  │
│  │ Padrão identificado - thumbnails com tons          │  │
│  │ vermelhos performam 3x melhor                       │  │
│  │                                [Editar] [Deletar]   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🎬 Lucca                                           │  │
│  │ 🟢 Produção finalizada: 15 vídeos                  │  │
│  │ ─────────────────────────────────────               │  │
│  │ Batch de vídeos renderizado e pronto               │  │
│  │ para upload nos próximos dias                       │  │
│  │                                [Editar] [Deletar]   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Cada card de evento mostra:**
- Emoji e nome do sócio que criou
- Emoji da categoria (🟡🔵🟣🔴) ou indicador especial (💰❌)
- Título em destaque
- Descrição completa
- Botões de ação (Editar/Deletar) no canto inferior direito

---

### **4. MODAL: BUSCA AVANÇADA**

Quando clicar em "🔍 Buscar":

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Buscar Eventos                                    [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Buscar por texto:                                         │
│  [_______________________________________________________] │
│                                                             │
│  Filtrar por autor:                                        │
│  ☐ 🎯 Cellibs  ☐ 📝 Arthur  ☐ 🎬 Lucca  ☐ 🎨 João       │
│                                                             │
│  Filtrar por categoria:                                    │
│  ☐ 🟡 Geral           ☐ 🔵 Desenvolvimento               │
│  ☐ 🟣 Financeiro      ☐ 🔴 Urgente                       │
│  ☐ 💰 Monetizações    ☐ ❌ Desmonetizações               │
│                                                             │
│  Período:                                                  │
│  De: [___/___/____]  Até: [___/___/____]                  │
│                                                             │
│                              [Limpar] [Buscar]             │
├─────────────────────────────────────────────────────────────┤
│  Resultados encontrados: 3                                 │
│                                                             │
│  • 11/02/2026 - 🎯 Cellibs                                │
│    🔵 Deploy do sistema de comentários                    │
│    Sistema 100% funcional...                [Ver mais]    │
│                                                             │
│  • 06/02/2026 - 📝 Arthur                                 │
│    💰 Canal "Terror BR" monetizado                        │
│    Alcançamos os requisitos...              [Ver mais]    │
│                                                             │
│  • 03/02/2026 - 🎯 Cellibs                                │
│    🔵 Correção bug OAuth                                  │
│    Bug de permissões resolvido...           [Ver mais]    │
└─────────────────────────────────────────────────────────────┘
```

**Funcionalidades da busca:**
- Busca em títulos e descrições (case insensitive)
- Múltiplos filtros podem ser selecionados
- Resultados ordenados por data (mais recente primeiro)
- Clicar em "Ver mais" abre o modal do dia

---

## 🔌 **ENDPOINTS DA API (JÁ PRONTOS NO BACKEND)**

O backend já está funcionando com estes endpoints:

```javascript
// Base URL da API (use a mesma variável do dashboard)
const API_URL = import.meta.env.VITE_API_URL

// Endpoints disponíveis:
GET    ${API_URL}/api/calendar/month/{year}/{month}  // Lista eventos do mês
GET    ${API_URL}/api/calendar/day/{date}           // Lista eventos de um dia
POST   ${API_URL}/api/calendar/event                // Criar novo evento
GET    ${API_URL}/api/calendar/event/{id}           // Ver detalhes do evento
PATCH  ${API_URL}/api/calendar/event/{id}           // Editar evento
DELETE ${API_URL}/api/calendar/event/{id}           // Deletar evento
POST   ${API_URL}/api/calendar/search               // Busca avançada
GET    ${API_URL}/api/calendar/stats                // Estatísticas (opcional)
```

### **Exemplo de request para criar evento:**
```javascript
POST /api/calendar/event
{
  "title": "Deploy sistema de comentários",
  "description": "Sistema 100% funcional em produção",
  "event_date": "2026-02-11",
  "created_by": "cellibs",      // cellibs|arthur|lucca|joao
  "category": "desenvolvimento", // geral|desenvolvimento|financeiro|urgente
  "event_type": "normal"         // normal|monetization|demonetization
}
```

### **Exemplo de response do GET month:**
```javascript
{
  "2026-02-11": [
    {
      "id": 1,
      "title": "Deploy sistema",
      "description": "...",
      "event_date": "2026-02-11",
      "created_by": "cellibs",
      "author_name": "Cellibs",
      "author_emoji": "🎯",
      "category": "desenvolvimento",
      "category_color": "🔵",
      "event_type": "normal"
    },
    {
      "id": 2,
      "title": "Terror Histórico BR",
      "description": "Canal monetizado!",
      "event_date": "2026-02-11",
      "created_by": "arthur",
      "author_name": "Arthur",
      "author_emoji": "📝",
      "event_type": "monetization",
      "special_indicator": "💰"
    }
  ],
  "2026-02-12": [...]
}
```

---

## ⚙️ **CONFIGURAÇÕES TÉCNICAS**

```javascript
// Configuração dos 4 sócios
const SOCIOS = {
  cellibs: { name: 'Cellibs', emoji: '🎯' },
  arthur: { name: 'Arthur', emoji: '📝' },
  lucca: { name: 'Lucca', emoji: '🎬' },
  joao: { name: 'João', emoji: '🎨' }
}

// Configuração das categorias
const CATEGORIAS = {
  geral: { name: 'Geral', emoji: '🟡' },
  desenvolvimento: { name: 'Desenvolvimento', emoji: '🔵' },
  financeiro: { name: 'Financeiro', emoji: '🟣' },
  urgente: { name: 'Urgente', emoji: '🔴' }
}

// Meses em português
const MONTHS = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

// Dias da semana
const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
```

---

## ✅ **CHECKLIST DE IMPLEMENTAÇÃO**

- [ ] Criar nova aba "Calendário" na seção Ferramentas
- [ ] Implementar grid do calendário mensal (7 dias x 6 semanas)
- [ ] Adicionar dropdowns para navegação mês/ano
- [ ] Implementar modal de criar evento com validações
- [ ] Implementar modal de visualizar dia com lista de eventos
- [ ] Implementar modal de busca com filtros
- [ ] Conectar com os 8 endpoints da API
- [ ] Adicionar funcionalidade de editar evento (modal pré-preenchido)
- [ ] Adicionar funcionalidade de deletar evento (confirmação)
- [ ] Garantir responsividade (mobile)
- [ ] Usar componentes UI existentes do dashboard
- [ ] Manter padrão visual consistente
- [ ] Adicionar loading states durante requests
- [ ] Adicionar tratamento de erros
- [ ] Adicionar toasts de feedback (sucesso/erro)
- [ ] Testar todas as funcionalidades

---

## ⚠️ **PONTOS DE ATENÇÃO**

1. **NÃO adicione campo de horário** - apenas datas
2. **NÃO modifique** outras partes do dashboard
3. **USE os componentes UI existentes** (Card, Button, Dialog, etc)
4. **Quando for monetização/desmonetização**, não mostrar opções de categoria
5. **Soft delete** - eventos deletados vão para lixeira por 30 dias (backend cuida disso)
6. **Mantenha o padrão visual** do dashboard existente
7. **Dropdown de navegação** para mês e ano (não setas)
8. **Modal overlay** com fundo escuro e transições suaves
9. **Responsivo** - deve funcionar bem em mobile
10. **Validações** - campos obrigatórios devem ser validados antes de enviar

---

## 🎯 **RESULTADO ESPERADO**

Uma aba de calendário profissional e funcional que:
- Permite os 4 sócios registrarem suas atividades
- Mostra visualmente quem fez o quê (emojis)
- Destaca eventos importantes (monetização com 💰)
- Tem busca poderosa para encontrar eventos passados
- Segue 100% o padrão visual do dashboard
- Funciona perfeitamente em desktop e mobile
- Tem feedback visual claro (loading, toasts)
- É intuitiva e fácil de usar

---

## 📱 **COMPORTAMENTO RESPONSIVO**

### Desktop (tela grande):
- Grid completo 7x6
- Modais com largura fixa (600px)
- Todos os controles visíveis

### Tablet (tela média):
- Grid adaptado
- Modais com 80% da largura
- Controles mantidos

### Mobile (tela pequena):
- Grid pode virar lista vertical por semana
- Modais fullscreen
- Botões adaptados para toque

---

## 🚀 **FLUXOS DE USUÁRIO**

### Criar evento:
1. Clicar em "+ Novo Evento"
2. Selecionar qual sócio está criando
3. Escolher data (ou já vem preenchida se clicou em um dia)
4. Digitar título e descrição
5. Escolher tipo (normal/monetização/desmonetização)
6. Se normal, escolher categoria
7. Salvar → Toast de sucesso → Atualiza calendário

### Visualizar eventos:
1. Clicar em qualquer dia
2. Modal abre com lista de eventos
3. Pode editar ou deletar cada evento
4. Pode adicionar novo evento para aquele dia

### Buscar eventos:
1. Clicar em "🔍 Buscar"
2. Digitar texto e/ou selecionar filtros
3. Clicar em "Buscar"
4. Ver resultados
5. Clicar em resultado para ver detalhes

---

**Implemente seguindo estas instruções detalhadas para criar uma experiência consistente e profissional!** 🚀

**Qualquer dúvida, me avise antes de implementar para esclarecermos.**