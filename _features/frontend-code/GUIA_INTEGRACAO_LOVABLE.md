# GUIA DE INTEGRAÇÃO - LOVABLE

## ✅ STATUS: TODOS OS COMPONENTES PRONTOS (7/7)

---

## 📦 COMPONENTES CRIADOS

### 1. MonetizationTab.tsx (249 linhas) ✅
- Container principal
- Fetch paralelo de 4 endpoints
- Gerenciamento de filtros
- Loading/error states

### 2. FilterBar.tsx (226 linhas) ✅
- Período, Idioma, Subnicho, Tipo
- Fetch dinâmico de subnichos
- Resumo de filtros ativos

### 3. MonetizationCards.tsx (159 linhas) ✅
- 4 cards superiores
- Formatação currency/numbers
- Trend indicators

### 4. ChannelsList.tsx (313 linhas) ✅
- Lista agrupada por subnicho
- Últimos 3 dias visíveis
- Badges Real/Estimativa
- Botão "Ver Histórico"

### 5. ChannelHistoryModal.tsx (286 linhas) ✅
- Modal fullscreen com histórico completo
- Gráfico Recharts (revenue/RPM)
- Tabela paginada (15 + carregar mais)
- Download CSV

### 6. AnalyticsCard.tsx (212 linhas) ✅
- Projeções 7d/15d/30d
- Melhores/Piores dias
- Retention/CTR médios
- Chart por dia da semana

### 7. TopPerformersCard.tsx (206 linhas) ✅
- Top 3 RPM (podium 🥇🥈🥉)
- Top 3 Revenue
- Tabs para alternar
- Fun fact comparativo

**Total:** ~1,650 linhas de código React/TypeScript

---

## 🚀 PASSO A PASSO: INTEGRAR NO LOVABLE

### PASSO 1: Criar Estrutura de Pastas

No Lovable, crie a estrutura:
```
src/
└── components/
    └── monetization/
        ├── MonetizationTab.tsx
        ├── FilterBar.tsx
        ├── MonetizationCards.tsx
        ├── ChannelsList.tsx
        ├── ChannelHistoryModal.tsx
        ├── AnalyticsCard.tsx
        └── TopPerformersCard.tsx
```

---

### PASSO 2: Copiar Componentes

Copie cada arquivo de `D:\ContentFactory\youtube-dashboard-backend\frontend-code\` para a pasta `src/components/monetization/` no Lovable.

**Arquivos:**
1. MonetizationTab.tsx
2. FilterBar.tsx
3. MonetizationCards.tsx
4. ChannelsList.tsx
5. ChannelHistoryModal.tsx
6. AnalyticsCard.tsx
7. TopPerformersCard.tsx

---

### PASSO 3: Verificar Dependências

Todos os componentes usam shadcn/ui. Certifique-se de que você tem:

**UI Components:**
```typescript
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
```

**Icons:**
```typescript
import { Loader2, Calendar, Globe, ... } from 'lucide-react';
```

**Charts (instalar se não tiver):**
```bash
npm install recharts
```

**Utils:**
```typescript
import { cn } from '@/lib/utils';
```

---

### PASSO 4: Configurar API_BASE

**Opção A: Environment Variable (Recomendado)**

Crie `.env` no Lovable:
```bash
VITE_API_BASE_URL=https://youtube-dashboard-backend-production.up.railway.app
```

Em todos os componentes, substitua:
```typescript
// Antes:
const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

// Depois:
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://youtube-dashboard-backend-production.up.railway.app';
```

**Opção B: Config File**

Crie `src/config/api.ts`:
```typescript
export const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';
```

Em todos os componentes:
```typescript
import { API_BASE } from '@/config/api';
```

---

### PASSO 5: Adicionar Tab no Dashboard

No arquivo principal do dashboard (ex: `src/pages/Index.tsx`):

```typescript
import { MonetizationTab } from '@/components/monetization/MonetizationTab';

// ...

<Tabs defaultValue="minerados">
  <TabsList>
    <TabsTrigger value="minerados">Canais Minerados</TabsTrigger>
    <TabsTrigger value="tabela">Tabela</TabsTrigger>
    <TabsTrigger value="monetizacao">
      💰 Monetização
    </TabsTrigger>
  </TabsList>

  <TabsContent value="minerados">
    {/* Conteúdo existente */}
  </TabsContent>

  <TabsContent value="tabela">
    {/* Conteúdo existente */}
  </TabsContent>

  <TabsContent value="monetizacao">
    <MonetizationTab />
  </TabsContent>
</Tabs>
```

---

### PASSO 6: Testar Localmente (se possível)

```bash
npm run dev
```

Verifique:
1. ✅ Tab "Monetização" aparece
2. ✅ Filtros funcionam
3. ✅ Cards aparecem com dados
4. ✅ Lista de canais carrega
5. ✅ Modal histórico abre
6. ✅ Charts renderizam
7. ✅ Mobile responsivo funciona

---

## 🔧 TROUBLESHOOTING

### Erro: "Module not found"
**Solução:** Instale dependências faltantes
```bash
npm install recharts
```

### Erro: "Cannot find '@/components/ui/...'"
**Solução:** shadcn/ui não está instalado. Siga docs do Lovable.

### Erro: "API fetch failed"
**Solução:** Verifique se Railway está online e API_BASE está correto.

### Componente não renderiza
**Solução:** Verifique console do navegador para erros TypeScript.

### Mobile quebrado
**Solução:** Todos os componentes são mobile-first. Se quebrar, verifique CSS customizado.

---

## 📊 ENDPOINTS USADOS

Os componentes fazem fetch de:

1. **GET /api/monetization/summary**
   - Usado por: MonetizationCards
   - Retorna: total_channels, daily_avg, growth_rate, rpm_avg, total_revenue

2. **GET /api/monetization/channels**
   - Usado por: ChannelsList
   - Retorna: canais agrupados por subnicho com últimos 3 dias

3. **GET /api/monetization/analytics**
   - Usado por: AnalyticsCard
   - Retorna: projections, best/worst days, retention, ctr, day_of_week

4. **GET /api/monetization/top-performers**
   - Usado por: TopPerformersCard
   - Retorna: top_rpm (top 3), top_revenue (top 3)

5. **GET /api/monetization/channel/{id}/history**
   - Usado por: ChannelHistoryModal
   - Retorna: histórico completo do canal

6. **GET /api/monetization/config**
   - Usado por: FilterBar
   - Retorna: lista de canais monetizados (para subnichos)

---

## 🎨 CUSTOMIZAÇÃO

### Mudar Cores

Em cada componente, as cores estão definidas com Tailwind:

```typescript
// Verde (Revenue)
className="text-green-600 bg-green-500/10"

// Amarelo (RPM/Estimativa)
className="text-yellow-600 bg-yellow-500/10"

// Azul (Canais)
className="text-blue-600 bg-blue-500/10"

// Roxo (Total)
className="text-purple-600 bg-purple-500/10"
```

### Mudar Período Padrão

Em `MonetizationTab.tsx`:
```typescript
const [filters, setFilters] = useState<FilterState>({
  period: 'total',  // Mudar aqui: '24h' | '3d' | '7d' | '15d' | '30d' | 'total'
  language: 'all',
  subnicho: null,
  typeFilter: 'real_estimate',
});
```

### Adicionar Bandeira de País

Em `ChannelsList.tsx`:
```typescript
const LANGUAGE_FLAGS: { [key: string]: string } = {
  pt: '🇧🇷',
  es: '🇪🇸',
  en: '🇺🇸',
  de: '🇩🇪',
  fr: '🇫🇷',
  it: '🇮🇹',  // Adicione aqui
};
```

---

## 📱 RESPONSIVIDADE

Todos os componentes são **mobile-first**:

### Breakpoints:
- `sm:` 640px (mobile landscape)
- `md:` 768px (tablet)
- `lg:` 1024px (desktop)
- `xl:` 1280px (large desktop)

### Comportamento Mobile:
- **MonetizationCards:** 1 coluna → 2 colunas (md) → 4 colunas (lg)
- **Main Grid:** 1 coluna → 3 colunas (lg) [2+1]
- **FilterBar:** 1 coluna → 2 colunas (md) → 4 colunas (lg)
- **Charts:** ResponsiveContainer (100% width)
- **Tables:** overflow-x-auto (scroll horizontal)

---

## ✅ CHECKLIST FINAL

Antes de publicar, verifique:

### Backend:
- [ ] Migration executada no Supabase
- [ ] Snapshot inicial rodado
- [ ] Railway deployado (commit já foi feito ✅)
- [ ] Endpoints funcionando (teste com Postman/curl)

### Frontend:
- [ ] 7 componentes copiados para Lovable
- [ ] API_BASE configurado
- [ ] Dependências instaladas (recharts)
- [ ] Tab adicionada no dashboard
- [ ] Testado em dev mode
- [ ] Testado em mobile

### Testes:
- [ ] Filtros funcionam
- [ ] Dados carregam corretamente
- [ ] Modal histórico abre
- [ ] Charts renderizam
- [ ] Download CSV funciona
- [ ] Badges Real/Estimativa aparecem
- [ ] Mobile responsivo

---

## 🎯 PRÓXIMOS PASSOS

1. **Você:** Execute migration no Supabase (2 min)
   - Arquivo: `EXECUTAR_MIGRATION_AGORA.md`

2. **Você:** Configure API keys localmente OU rode snapshot no Railway
   - Local: Adicione YOUTUBE_API_KEY_3 no .env
   - Railway: SSH para o container e rode `python snapshot_initial_views.py`

3. **Lovable:** Copie os 7 componentes
   - Use este guia como referência

4. **Teste:** Abra o dashboard e teste tudo
   - Use os filtros
   - Abra o modal de histórico
   - Verifique mobile

5. **Deploy:** Publique no Lovable
   - Build + Deploy

---

## 📚 DOCUMENTAÇÃO COMPLETA

Consulte também:
- `MONETIZATION_SYSTEM_STATUS.md` - Status completo do sistema
- `RESUMO_IMPLEMENTACAO_MONETIZACAO.md` - Resumo executivo backend
- `FRONTEND_COMPONENTS_README.md` - Detalhes de cada componente
- `EXECUTAR_MIGRATION_AGORA.md` - Instruções da migration

---

## 🆘 SUPORTE

**Backend funcionando?**
Teste: https://youtube-dashboard-backend-production.up.railway.app/health

**API funcionando?**
Teste: https://youtube-dashboard-backend-production.up.railway.app/api/monetization/config

**Dúvidas?**
Consulte a documentação completa nos arquivos `.md`

---

**STATUS:** ✅ Componentes 100% prontos para integração
**DATA:** 10/12/2025
**DESENVOLVIDO POR:** Claude Code
