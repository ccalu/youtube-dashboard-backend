# FRONTEND COMPONENTS - MONETIZATION TAB

## ✅ COMPONENTES CRIADOS (3/7)

### 1. **MonetizationTab.tsx** ✅ (Principal Container)
**Linhas:** 249
**Responsabilidades:**
- Container principal da aba de monetização
- Gerencia estado global dos filtros
- Faz fetch paralelo de todos os endpoints
- Orquestra renderização de todos os subcomponentes
- Loading state e error handling

**Estrutura:**
```
<MonetizationTab>
  ├── <FilterBar />
  ├── <MonetizationCards />
  └── Grid 2 colunas
      ├── <ChannelsList /> (2/3 width)
      └── Right Column (1/3 width)
          ├── <AnalyticsCard />
          └── <TopPerformersCard />
```

**API Calls:**
- GET /api/monetization/summary
- GET /api/monetization/channels
- GET /api/monetization/analytics
- GET /api/monetization/top-performers

---

### 2. **FilterBar.tsx** ✅
**Linhas:** 226
**Responsabilidades:**
- Filtros globais (período, idioma, subnicho, tipo)
- Fetch dinâmico de subnichos disponíveis
- Resumo de filtros ativos
- Botão "Limpar filtros"

**Filtros:**
- **Período:** 24h | 3d | 7d | 15d | 30d | Total
- **Idioma:** Todos | PT 🇧🇷 | ES 🇪🇸 | EN 🇺🇸 | DE 🇩🇪 | FR 🇫🇷
- **Subnicho:** Dropdown dinâmico (busca do /config)
- **Tipo:** Toggle Real + Estimativa | Somente Real

**API Calls:**
- GET /api/monetization/config (para buscar subnichos)

---

### 3. **MonetizationCards.tsx** ✅
**Linhas:** 159
**Responsabilidades:**
- 4 cards superiores com métricas principais
- Formatação de valores (currency, numbers)
- Ícones e cores por tipo de métrica
- Loading skeleton

**Cards:**
1. **Canais Monetizados** (azul) - Total de canais ativos
2. **Média Diária** (verde) - Revenue médio + taxa crescimento
3. **RPM Médio** (amarelo) - Revenue por 1.000 views
4. **Total Revenue** (roxo) - Revenue do período

**Features:**
- Trend indicators (↑ verde / ↓ vermelho)
- Formatação inteligente (1.2K, 1.5M)
- Tooltips informativos

---

## ⏳ COMPONENTES PENDENTES (4/7)

### 4. **ChannelsList.tsx** (PRÓXIMO)
**Responsabilidades:**
- Lista de canais agrupados por subnicho
- Últimos 3 dias visíveis para cada canal
- Badges de status (🟡 estimate | 🟢 real)
- Botão "Ver Histórico" → abre modal
- Layout responsivo (grid/list)

**Estrutura:**
```tsx
interface ChannelsListProps {
  data: {
    [subnicho: string]: Array<{
      channel_id: string;
      channel_name: string;
      subnicho: string;
      language: string;
      last_3_days: Array<{
        date: string;
        views: number;
        revenue: number;
        rpm: number;
        is_estimate: boolean;
      }>;
    }>;
  };
  loading: boolean;
  typeFilter: 'real_estimate' | 'real_only';
}
```

**Features Necessárias:**
- Agrupamento por subnicho (collapsible sections)
- Badge de idioma (🇧🇷 🇪🇸 🇺🇸)
- Tabela mini com D-1, D-2, D-3
- Indicadores de status
- Botão "Ver Histórico Completo"

---

### 5. **ChannelHistoryModal.tsx**
**Responsabilidades:**
- Modal fullscreen com histórico completo
- Gráfico de linha (revenue ao longo do tempo)
- Tabela paginada (15 dias iniciais + "Carregar Mais")
- Stats resumo (Total Revenue, Avg RPM, Total Days)

**API Call:**
- GET /api/monetization/channel/{channel_id}/history

**Estrutura:**
```tsx
interface ChannelHistoryModalProps {
  channelId: string;
  channelName: string;
  open: boolean;
  onClose: () => void;
}
```

**Features Necessárias:**
- Recharts ou similar para gráfico
- Tabela com sorting
- Pagination (15 em 15)
- Download CSV (bonus)
- Toggle estimativas no gráfico

---

### 6. **AnalyticsCard.tsx**
**Responsabilidades:**
- Projeções (7d, 15d, 30d)
- Melhores/Piores dias (revenue)
- Retention e CTR médios
- Análise por dia da semana

**Estrutura:**
```tsx
interface AnalyticsCardProps {
  data: {
    projections: {
      days_7: number;
      days_15: number;
      days_30: number;
    };
    best_day: { date: string; revenue: number };
    worst_day: { date: string; revenue: number };
    avg_retention_pct: number;
    avg_ctr: number;
    day_of_week_analysis: Array<{
      day_name: string;
      avg_revenue: number;
    }>;
  };
  loading: boolean;
}
```

**Features Necessárias:**
- Mini chart para projeções
- Day-of-week heatmap (visual)
- Progress bars para retention/CTR

---

### 7. **TopPerformersCard.tsx**
**Responsabilidades:**
- Top 3 canais por RPM (podium style 🥇🥈🥉)
- Top 3 canais por Revenue
- Visual destacado para #1

**Estrutura:**
```tsx
interface TopPerformersCardProps {
  data: {
    top_rpm: Array<{
      channel_id: string;
      channel_name: string;
      avg_rpm: number;
      total_revenue: number;
    }>;
    top_revenue: Array<{
      channel_id: string;
      channel_name: string;
      total_revenue: number;
      avg_rpm: number;
    }>;
  };
  loading: boolean;
}
```

**Features Necessárias:**
- Podium visual (boxes com altura diferente)
- Medal icons (🥇🥈🥉)
- Tabs: "Por RPM" | "Por Revenue"

---

## 📦 DEPENDÊNCIAS NECESSÁRIAS (Lovable)

### UI Components (shadcn/ui):
```tsx
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
```

### Icons (lucide-react):
```tsx
import {
  Loader2,
  Calendar,
  Globe,
  Tag,
  Filter,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Users,
  Zap,
  ExternalLink,
  Download,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
```

### Charts (recharts):
```tsx
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
```

### Utils:
```tsx
import { cn } from '@/lib/utils';
```

---

## 🎨 DESIGN SYSTEM

### Cores:
- **Azul** (`text-blue-600`, `bg-blue-500/10`) - Canais
- **Verde** (`text-green-600`, `bg-green-500/10`) - Revenue, Real
- **Amarelo** (`text-yellow-600`, `bg-yellow-500/10`) - RPM, Estimativa
- **Roxo** (`text-purple-600`, `bg-purple-500/10`) - Total
- **Vermelho** (`text-red-600`) - Perdas, Erros

### Badges:
- 🟢 **Real** (verde) - `is_estimate: false`
- 🟡 **Estimativa** (amarelo) - `is_estimate: true`

### Bandeiras:
- 🇧🇷 Português (pt)
- 🇪🇸 Espanhol (es)
- 🇺🇸 Inglês (en)
- 🇩🇪 Alemão (de)
- 🇫🇷 Francês (fr)

---

## 🚀 INTEGRAÇÃO LOVABLE

### PASSO 1: Adicionar Tab no Dashboard

**Arquivo:** `src/pages/Index.tsx` (ou similar)

```tsx
import { MonetizationTab } from '@/components/monetization/MonetizationTab';

// Dentro do Tabs component:
<TabsList>
  <TabsTrigger value="minerados">Canais Minerados</TabsTrigger>
  <TabsTrigger value="tabela">Tabela</TabsTrigger>
  <TabsTrigger value="monetizacao">💰 Monetização</TabsTrigger>
</TabsList>

<TabsContent value="monetizacao">
  <MonetizationTab />
</TabsContent>
```

### PASSO 2: Estrutura de Pastas

```
src/
├── components/
│   └── monetization/
│       ├── MonetizationTab.tsx          ✅
│       ├── FilterBar.tsx                ✅
│       ├── MonetizationCards.tsx        ✅
│       ├── ChannelsList.tsx             ⏳
│       ├── ChannelHistoryModal.tsx      ⏳
│       ├── AnalyticsCard.tsx            ⏳
│       └── TopPerformersCard.tsx        ⏳
```

### PASSO 3: Configurar API_BASE

**Opção 1:** Environment Variable (Recomendado)
```tsx
// .env
VITE_API_BASE_URL=https://youtube-dashboard-backend-production.up.railway.app

// Componentes
const API_BASE = import.meta.env.VITE_API_BASE_URL;
```

**Opção 2:** Config File
```tsx
// src/config/api.ts
export const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

// Componentes
import { API_BASE } from '@/config/api';
```

---

## 📊 FLUXO DE DADOS

### 1. Load Inicial:
```
MonetizationTab (mount)
  ↓
fetchAllData()
  ↓
Promise.all([
  GET /api/monetization/summary?period=total&type_filter=real_estimate
  GET /api/monetization/channels?period=total&type_filter=real_estimate
  GET /api/monetization/analytics?period=total&type_filter=real_estimate
  GET /api/monetization/top-performers?period=total&type_filter=real_estimate
])
  ↓
Set States → Render Components
```

### 2. Mudança de Filtro:
```
User changes filter (ex: period = "7d")
  ↓
FilterBar.onFilterChange({ period: "7d" })
  ↓
MonetizationTab.setFilters({ ...prev, period: "7d" })
  ↓
useEffect [filters] triggered
  ↓
fetchAllData() with new params
  ↓
Update all components
```

### 3. Ver Histórico (Modal):
```
User clicks "Ver Histórico" on channel
  ↓
ChannelsList opens ChannelHistoryModal
  ↓
Modal fetches: GET /api/monetization/channel/{id}/history
  ↓
Renders chart + table with pagination
```

---

## ⚙️ PRÓXIMOS PASSOS

### Você (Backend):
1. ✅ Backend 100% implementado
2. ⏳ Executar migration no Supabase
3. ⏳ Rodar snapshot_initial_views.py

### Desenvolvimento (Frontend):
4. ⏳ Criar ChannelsList.tsx (lista de canais)
5. ⏳ Criar ChannelHistoryModal.tsx (modal histórico)
6. ⏳ Criar AnalyticsCard.tsx (analytics)
7. ⏳ Criar TopPerformersCard.tsx (top 3)
8. ⏳ Integrar no Lovable (adicionar tab)
9. ⏳ Testar com dados reais

---

## 🎯 ESTIMATIVA DE TEMPO

### Componentes Restantes:
- **ChannelsList.tsx:** 2-3 horas
- **ChannelHistoryModal.tsx:** 2-3 horas
- **AnalyticsCard.tsx:** 1-2 horas
- **TopPerformersCard.tsx:** 1 hora

**Total:** 6-9 horas de desenvolvimento

### Integração + Testes:
- **Lovable Integration:** 30 min
- **Testes com dados reais:** 1-2 horas
- **Ajustes finais:** 1 hora

**TOTAL GERAL:** 8-12 horas para frontend completo

---

## 📱 RESPONSIVIDADE

Todos os componentes são **mobile-first**:

### Breakpoints:
- **sm:** 640px (mobile landscape)
- **md:** 768px (tablet)
- **lg:** 1024px (desktop)
- **xl:** 1280px (large desktop)

### Grid Layouts:
- **Cards:** `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- **Main Layout:** `grid-cols-1 lg:grid-cols-3`
- **Filters:** `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`

---

## 🔗 LINKS ÚTEIS

### Backend:
- **API Base:** https://youtube-dashboard-backend-production.up.railway.app
- **Swagger Docs:** /docs (FastAPI auto-generated)

### Frontend:
- **shadcn/ui:** https://ui.shadcn.com
- **Lucide Icons:** https://lucide.dev
- **Recharts:** https://recharts.org

### Database:
- **Supabase Dashboard:** https://supabase.com/dashboard
- **SQL Editor:** Project → SQL Editor

---

**STATUS:** ✅ Backend pronto | ⏳ Frontend 43% completo (3/7 componentes)
**DATA:** 10/12/2025
**DESENVOLVIDO POR:** Claude Code
