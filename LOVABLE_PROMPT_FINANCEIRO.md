# PROMPT LOVABLE - Sistema Financeiro Completo

## 📍 CONTEXTO ATUAL DO DASHBOARD

Atualmente existem duas **categorias** no menu lateral:
1. **🚀 Navegação** (contém: Tabela, Análise, Monetização)
2. **🛠️ Ferramentas** (contém: outras funcionalidades)

**Aba padrão ao abrir:** Tabela (primeira aba de Navegação)

---

## 🎯 NOVA CATEGORIA A CRIAR

### Estrutura do Menu:
```
💰 Empresa  ← NOVA (cor verde, posicionada ACIMA de Navegação)
  └─ Financeiro

🚀 Navegação
  ├─ Tabela ← CONTINUA SENDO A ABA PADRÃO AO ABRIR
  ├─ Análise
  └─ Monetização

🛠️ Ferramentas
  └─ (outras abas)
```

**IMPORTANTE:**
- Categoria "💰 Empresa" deve ficar **ACIMA** de "🚀 Navegação"
- Aba "Tabela" **CONTINUA sendo a padrão** ao abrir o dashboard
- Cor da categoria Empresa: **Verde (#10B981 ou similar)**

---

## 🎨 DESIGN DA ABA FINANCEIRO

### Layout Geral:
- **Mobile-first** (responsivo)
- **Tema escuro** (dark mode)
- **Cards com gradiente verde** para receitas
- **Cards com gradiente vermelho** para despesas
- **Gráficos interativos** (recharts ou similar)

### Estrutura da Página:

```
┌─────────────────────────────────────────────────────────┐
│  FILTRO DE PERÍODO                                      │
│  [7d] [15d] [30d] [60d] [90d] [Custom]                 │
│  Taxa USD-BRL: R$ 5,52 (atualizada em: 17/12 15:52)   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  OVERVIEW FINANCEIRO (4 cards lado a lado)              │
│                                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ Receita │ │Despesas │ │ Taxas  │ │  Lucro  │      │
│  │  Bruta  │ │ Totais  │ │  (3%)  │ │ Líquido │      │
│  │         │ │         │ │        │ │         │      │
│  │R$ 24.4k │ │ R$ 0,00 │ │R$ 733  │ │R$ 23.7k │      │
│  │ +15.2%  │ │  -5.3%  │ │ +15.2% │ │ +16.8%  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  GRÁFICO: RECEITA VS DESPESAS VS LUCRO                  │
│  (Gráfico de linha, 3 séries, por mês)                 │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐ ┌─────────────────────────────────┐
│ BREAKDOWN        │ │ LANÇAMENTOS                     │
│ DESPESAS         │ │                                 │
│                  │ │ [+ Adicionar Lançamento]        │
│ (Gráfico Pizza)  │ │                                 │
│                  │ │ Filtros: [Receita] [Despesa]    │
│ - Por Categoria  │ │          [Fixa] [Única]         │
│ - Por Recorrência│ │                                 │
│                  │ │ Lista de lançamentos:           │
│                  │ │ ┌──────────────────────────┐    │
│                  │ │ │ 01/12 - YouTube AdSense  │    │
│                  │ │ │ R$ 20.210,54            │    │
│                  │ │ │ [Editar] [Deletar]       │    │
│                  │ │ └──────────────────────────┘    │
└──────────────────┘ └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  METAS FINANCEIRAS                                      │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │ Meta: Receita R$ 30k (Dez/2024)           │         │
│  │ Progresso: 67% (R$ 20.210 / R$ 30.000)   │         │
│  │ [████████████░░░░░░░]                     │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  [+ Adicionar Meta]                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  GESTÃO                                                  │
│                                                          │
│  [Categorias] [Taxas] [Exportar CSV]                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 INTEGRAÇÃO COM BACKEND

### Base URL:
```
https://youtube-dashboard-backend-production.up.railway.app
```

### Endpoints Principais:

#### 1. Overview (Card principal)
```typescript
GET /api/financeiro/overview?periodo=30d

Response: {
  receita_bruta: 24465.03,
  despesas_totais: 0.00,
  despesas_fixas: 0.00,
  despesas_unicas: 0.00,
  taxas_totais: 733.95,
  lucro_liquido: 23731.08,
  periodo: "30d",
  variacao_receita: 15.2,
  variacao_despesas: -5.3,
  variacao_lucro: 16.8
}
```

#### 2. Taxa de Câmbio
```typescript
GET /api/financeiro/taxa-cambio

Response: {
  taxa: 5.52,
  atualizado_em: "2025-12-17 15:52:09"
}
```

#### 3. Gráfico Receita vs Despesas
```typescript
GET /api/financeiro/graficos/receita-despesas?periodo=90d

Response: {
  dados: [
    { mes: "2025-10", receita: 399.32, despesas: 0.00, lucro: 387.93 },
    { mes: "2025-11", receita: 3855.17, despesas: 0.00, lucro: 3739.51 },
    { mes: "2025-12", receita: 20210.54, despesas: 0.00, lucro: 19604.22 }
  ]
}
```

#### 4. Breakdown Despesas
```typescript
GET /api/financeiro/graficos/despesas-breakdown?periodo=30d

Response: {
  por_categoria: [
    { categoria: "Salários", valor: 5000.00, percentual: 55.5 },
    { categoria: "Ferramentas", valor: 3000.00, percentual: 33.3 },
    { categoria: "Marketing", valor: 1000.00, percentual: 11.1 }
  ],
  por_recorrencia: [
    { tipo: "Fixas", valor: 8000.00, percentual: 88.9 },
    { tipo: "Únicas", valor: 1000.00, percentual: 11.1 }
  ],
  total: 9000.00
}
```

#### 5. Listar Lançamentos
```typescript
GET /api/financeiro/lancamentos?periodo=30d&tipo=receita&recorrencia=fixa

Response: [
  {
    id: 1,
    categoria_id: 1,
    categoria_nome: "YouTube AdSense",
    valor: 20210.54,
    data: "2025-12-01",
    descricao: "Receita YouTube AdSense - 12/2025",
    tipo: "receita",
    recorrencia: null,
    usuario: "sistema",
    created_at: "2025-12-17T18:00:00Z"
  }
]
```

#### 6. Criar Lançamento
```typescript
POST /api/financeiro/lancamentos
Body: {
  categoria_id: 4,
  valor: 500.00,
  data: "2025-12-15",
  descricao: "Licença software XYZ",
  tipo: "despesa",
  recorrencia: "fixa",
  usuario: "Marcelo"
}
```

#### 7. Listar Categorias
```typescript
GET /api/financeiro/categorias

Response: [
  { id: 1, nome: "YouTube AdSense", tipo: "receita", cor: "#00FF00", icon: "youtube" },
  { id: 2, nome: "Patrocínios", tipo: "receita", cor: "#00CC00", icon: "handshake" },
  { id: 4, nome: "Ferramentas/Software", tipo: "despesa", cor: "#FF0000", icon: "tools" },
  { id: 5, nome: "Salários", tipo: "despesa", cor: "#CC0000", icon: "users" }
]
```

#### 8. Listar Taxas
```typescript
GET /api/financeiro/taxas

Response: [
  { id: 1, nome: "Imposto", percentual: 3.0, aplica_sobre: "receita_bruta", ativo: true }
]
```

#### 9. Metas
```typescript
GET /api/financeiro/metas/progresso?periodo=30d

Response: [
  {
    id: 1,
    nome: "Receita R$ 30k Dezembro",
    tipo: "receita",
    valor_objetivo: 30000.00,
    valor_atual: 20210.54,
    percentual: 67.37,
    periodo_inicio: "2025-12-01",
    periodo_fim: "2025-12-31",
    atingida: false
  }
]
```

#### 10. Exportar CSV
```typescript
GET /api/financeiro/lancamentos/export-csv?periodo=90d

Response: (arquivo CSV)
```

---

## 🎨 COMPONENTES A CRIAR

### 1. `FinanceiroTab.tsx` (Componente Principal)
- Gerencia estado do período selecionado
- Faz fetch de todos os dados
- Organiza layout geral

### 2. `FinanceiroFiltroPeriodo.tsx`
- Botões: 7d, 15d, 30d, 60d, 90d, Custom
- Mostra taxa USD-BRL atualizada
- Emite evento onChange

### 3. `FinanceiroOverviewCards.tsx`
- 4 cards: Receita Bruta, Despesas, Taxas, Lucro Líquido
- Mostra variação com período anterior (% + seta)
- Cores: verde (positivo), vermelho (negativo)

### 4. `FinanceiroGraficoReceitaDespesas.tsx`
- Gráfico de linha (recharts)
- 3 séries: Receita (verde), Despesas (vermelho), Lucro (azul)
- Responsivo

### 5. `FinanceiroBreakdownDespesas.tsx`
- Gráfico de pizza (recharts)
- 2 gráficos: Por categoria + Por recorrência
- Tooltip com valores e percentuais

### 6. `FinanceiroLancamentosList.tsx`
- Lista de lançamentos
- Filtros: tipo, recorrência
- Botão "Adicionar"
- Cards clicáveis com editar/deletar

### 7. `FinanceiroLancamentoModal.tsx`
- Modal para criar/editar lançamento
- Form: categoria, valor, data, descrição, tipo, recorrência
- Validação

### 8. `FinanceiroMetas.tsx`
- Lista de metas com barra de progresso
- Botão "Adicionar Meta"
- Modal para criar/editar

### 9. `FinanceiroCategorias.tsx`
- Gestão de categorias (criar, editar, deletar)
- Modal com form

### 10. `FinanceiroTaxas.tsx`
- Gestão de taxas
- Modal com form

---

## 📱 COMPORTAMENTO MOBILE

- Cards empilhados verticalmente
- Gráficos responsivos (altura ajustável)
- Filtros em dropdown/select
- Botões de ação flutuantes (FAB)
- Lista de lançamentos scrollável

---

## 🎨 PALETA DE CORES

### Receitas (Verde):
- Primary: `#10B981` (green-500)
- Light: `#34D399` (green-400)
- Dark: `#059669` (green-600)
- Gradient: `from-green-500 to-emerald-600`

### Despesas (Vermelho):
- Primary: `#EF4444` (red-500)
- Light: `#F87171` (red-400)
- Dark: `#DC2626` (red-600)
- Gradient: `from-red-500 to-rose-600`

### Lucro (Azul):
- Primary: `#3B82F6` (blue-500)
- Light: `#60A5FA` (blue-400)
- Dark: `#2563EB` (blue-600)

### Background (Dark):
- Background: `#0F172A` (slate-900)
- Card: `#1E293B` (slate-800)
- Border: `#334155` (slate-700)

---

## ⚙️ FUNCIONALIDADES ESPECIAIS

### 1. Auto-refresh Taxa de Câmbio:
```typescript
// Atualizar taxa a cada 5 minutos
useEffect(() => {
  const interval = setInterval(fetchTaxaCambio, 300000);
  return () => clearInterval(interval);
}, []);
```

### 2. Sincronização YouTube:
```typescript
// Botão para forçar sincronização manual
const syncYoutube = async () => {
  await fetch('/api/financeiro/sync-youtube', {
    method: 'POST',
    body: JSON.stringify({ periodo: '90d' })
  });
};
```

### 3. Export CSV:
```typescript
const exportCSV = () => {
  window.open(
    `${API_URL}/api/financeiro/lancamentos/export-csv?periodo=${periodo}`,
    '_blank'
  );
};
```

### 4. Validações:
- Valor > 0
- Data válida
- Categoria selecionada
- Tipo selecionado (receita/despesa)

---

## 🚀 IMPLEMENTAÇÃO COMPLETA

### INSTRUÇÕES PARA IMPLEMENTAÇÃO:

Por favor, implemente o sistema financeiro completo seguindo TODAS as especificações deste documento. Abaixo está um guia passo a passo do que precisa ser feito:

---

## PASSO 1: ESTRUTURA DO MENU

**CONTEXTO ATUAL:**
O dashboard possui duas categorias no menu lateral:
- 🚀 Navegação (contém: Tabela, Análise, Monetização)
- 🛠️ Ferramentas (outras funcionalidades)

**ABA PADRÃO ATUAL:** "Tabela" (primeira aba de Navegação)

**O QUE CRIAR:**

1. **Nova Categoria "💰 Empresa"**
   - Cor: Verde (#10B981 ou green-500)
   - Posição: **ACIMA** de "🚀 Navegação" no menu
   - Contém: Aba "Financeiro"

2. **Manter aba "Tabela" como padrão**
   - Quando o usuário abre o dashboard, deve abrir na aba "Tabela"
   - A categoria "💰 Empresa" fica visível no menu, mas não é a padrão

**Estrutura final do menu:**
```
💰 Empresa
  └─ Financeiro

🚀 Navegação  ← ABA PADRÃO: "Tabela"
  ├─ Tabela
  ├─ Análise
  └─ Monetização

🛠️ Ferramentas
  └─ (outras)
```

---

## PASSO 2: LAYOUT DA ABA FINANCEIRO

### 2.1 CONFIGURAÇÃO GERAL:
- Tema: Dark mode
- Responsividade: Mobile-first
- Biblioteca de gráficos: Recharts (ou similar)
- Animações: Suaves (framer-motion ou similar)
- Ícones: Lucide React

### 2.2 ESTRUTURA DA PÁGINA (de cima para baixo):

**A. HEADER COM FILTRO DE PERÍODO**
```tsx
<div className="flex items-center justify-between mb-6">
  <h1 className="text-2xl font-bold">Financeiro</h1>

  <div className="flex gap-2">
    <Button variant={periodo === '7d' ? 'default' : 'outline'}>7d</Button>
    <Button variant={periodo === '15d' ? 'default' : 'outline'}>15d</Button>
    <Button variant={periodo === '30d' ? 'default' : 'outline'}>30d</Button>
    <Button variant={periodo === '60d' ? 'default' : 'outline'}>60d</Button>
    <Button variant={periodo === '90d' ? 'default' : 'outline'}>90d</Button>
    <Button variant="outline">Custom</Button>
  </div>
</div>

<div className="text-sm text-muted-foreground mb-4">
  Taxa USD-BRL: R$ {taxa.toFixed(2)} (atualizada em: {dataAtualizacao})
</div>
```

**B. OVERVIEW - 4 CARDS (grid responsivo)**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
  {/* Card 1: Receita Bruta (verde) */}
  <Card className="bg-gradient-to-br from-green-500 to-emerald-600">
    <CardHeader>
      <CardTitle className="text-white">Receita Bruta</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold text-white">
        R$ {formatCurrency(overview.receita_bruta)}
      </div>
      <div className="flex items-center gap-1 text-white/90 text-sm mt-2">
        {overview.variacao_receita > 0 ? <TrendingUp /> : <TrendingDown />}
        {overview.variacao_receita.toFixed(1)}%
      </div>
    </CardContent>
  </Card>

  {/* Card 2: Despesas (vermelho) */}
  <Card className="bg-gradient-to-br from-red-500 to-rose-600">
    <CardHeader>
      <CardTitle className="text-white">Despesas Totais</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold text-white">
        R$ {formatCurrency(overview.despesas_totais)}
      </div>
      <div className="flex items-center gap-1 text-white/90 text-sm mt-2">
        {overview.variacao_despesas > 0 ? <TrendingUp /> : <TrendingDown />}
        {overview.variacao_despesas.toFixed(1)}%
      </div>
    </CardContent>
  </Card>

  {/* Card 3: Taxas (cinza) */}
  <Card className="bg-gradient-to-br from-slate-600 to-slate-700">
    <CardHeader>
      <CardTitle className="text-white">Taxas (3%)</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold text-white">
        R$ {formatCurrency(overview.taxas_totais)}
      </div>
      <div className="text-white/90 text-sm mt-2">
        Sobre receita bruta
      </div>
    </CardContent>
  </Card>

  {/* Card 4: Lucro Líquido (azul) */}
  <Card className="bg-gradient-to-br from-blue-500 to-blue-600">
    <CardHeader>
      <CardTitle className="text-white">Lucro Líquido</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold text-white">
        R$ {formatCurrency(overview.lucro_liquido)}
      </div>
      <div className="flex items-center gap-1 text-white/90 text-sm mt-2">
        {overview.variacao_lucro > 0 ? <TrendingUp /> : <TrendingDown />}
        {overview.variacao_lucro.toFixed(1)}%
      </div>
    </CardContent>
  </Card>
</div>
```

**C. GRÁFICO RECEITA VS DESPESAS (linha)**
```tsx
<Card className="mb-6">
  <CardHeader>
    <CardTitle>Receita vs Despesas vs Lucro</CardTitle>
  </CardHeader>
  <CardContent>
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={dadosGrafico}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="mes" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
          formatter={(value) => `R$ ${formatCurrency(value)}`}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="receita"
          stroke="#10B981"
          strokeWidth={2}
          name="Receita"
        />
        <Line
          type="monotone"
          dataKey="despesas"
          stroke="#EF4444"
          strokeWidth={2}
          name="Despesas"
        />
        <Line
          type="monotone"
          dataKey="lucro"
          stroke="#3B82F6"
          strokeWidth={2}
          name="Lucro"
        />
      </LineChart>
    </ResponsiveContainer>
  </CardContent>
</Card>
```

**D. GRID 2 COLUNAS: Breakdown + Lançamentos**
```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
  {/* COLUNA ESQUERDA: Breakdown Despesas */}
  <Card>
    <CardHeader>
      <CardTitle>Breakdown de Despesas</CardTitle>
    </CardHeader>
    <CardContent>
      {/* Gráfico Pizza - Por Categoria */}
      <h3 className="text-sm font-semibold mb-2">Por Categoria</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={breakdown.por_categoria}
            dataKey="valor"
            nameKey="categoria"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ percentual }) => `${percentual.toFixed(1)}%`}
          >
            {breakdown.por_categoria.map((entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `R$ ${formatCurrency(value)}`} />
        </PieChart>
      </ResponsiveContainer>

      {/* Gráfico Pizza - Por Recorrência */}
      <h3 className="text-sm font-semibold mb-2 mt-4">Por Recorrência</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={breakdown.por_recorrencia}
            dataKey="valor"
            nameKey="tipo"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ percentual }) => `${percentual.toFixed(1)}%`}
          >
            <Cell fill="#10B981" /> {/* Fixas */}
            <Cell fill="#EF4444" /> {/* Únicas */}
          </Pie>
          <Tooltip formatter={(value) => `R$ ${formatCurrency(value)}`} />
        </PieChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>

  {/* COLUNA DIREITA: Lançamentos */}
  <Card>
    <CardHeader className="flex flex-row items-center justify-between">
      <CardTitle>Lançamentos</CardTitle>
      <Button onClick={() => setModalOpen(true)} size="sm">
        <Plus className="w-4 h-4 mr-2" />
        Adicionar
      </Button>
    </CardHeader>
    <CardContent>
      {/* Filtros */}
      <div className="flex gap-2 mb-4">
        <Select value={filtroTipo} onValueChange={setFiltroTipo}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Tipo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="receita">Receita</SelectItem>
            <SelectItem value="despesa">Despesa</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filtroRecorrencia} onValueChange={setFiltroRecorrencia}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Recorrência" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="fixa">Fixa</SelectItem>
            <SelectItem value="unica">Única</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Lista */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {lancamentos.map((lanc) => (
          <div
            key={lanc.id}
            className="p-3 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{lanc.descricao}</span>
                  <Badge variant={lanc.tipo === 'receita' ? 'success' : 'destructive'}>
                    {lanc.tipo}
                  </Badge>
                  {lanc.recorrencia && (
                    <Badge variant="outline">{lanc.recorrencia}</Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {formatDate(lanc.data)} • {lanc.categoria_nome}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-bold ${
                  lanc.tipo === 'receita' ? 'text-green-500' : 'text-red-500'
                }`}>
                  R$ {formatCurrency(lanc.valor)}
                </span>
                <Button variant="ghost" size="sm">
                  <Edit className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
</div>
```

**E. METAS FINANCEIRAS**
```tsx
<Card className="mb-6">
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Metas Financeiras</CardTitle>
    <Button onClick={() => setModalMetaOpen(true)} size="sm">
      <Plus className="w-4 h-4 mr-2" />
      Adicionar Meta
    </Button>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      {metas.map((meta) => (
        <div key={meta.id} className="p-4 rounded-lg bg-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{meta.nome}</span>
            <span className="text-sm text-muted-foreground">
              {meta.percentual.toFixed(1)}%
            </span>
          </div>
          <Progress value={meta.percentual} className="mb-2" />
          <div className="text-sm text-muted-foreground">
            R$ {formatCurrency(meta.valor_atual)} / R$ {formatCurrency(meta.valor_objetivo)}
          </div>
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

**F. BOTÕES DE GESTÃO**
```tsx
<div className="flex gap-2">
  <Button variant="outline" onClick={() => setModalCategoriasOpen(true)}>
    <Tag className="w-4 h-4 mr-2" />
    Categorias
  </Button>
  <Button variant="outline" onClick={() => setModalTaxasOpen(true)}>
    <Percent className="w-4 h-4 mr-2" />
    Taxas
  </Button>
  <Button variant="outline" onClick={exportarCSV}>
    <Download className="w-4 h-4 mr-2" />
    Exportar CSV
  </Button>
</div>
```

---

## PASSO 3: INTEGRAÇÃO COM BACKEND

### 3.1 CONFIGURAÇÃO DA API:

```typescript
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app';

const api = {
  // Overview
  async getOverview(periodo: string) {
    const res = await fetch(`${API_URL}/api/financeiro/overview?periodo=${periodo}`);
    return res.json();
  },

  // Taxa de câmbio
  async getTaxaCambio() {
    const res = await fetch(`${API_URL}/api/financeiro/taxa-cambio`);
    return res.json();
  },

  // Gráfico receita vs despesas
  async getGraficoReceitaDespesas(periodo: string) {
    const res = await fetch(`${API_URL}/api/financeiro/graficos/receita-despesas?periodo=${periodo}`);
    return res.json();
  },

  // Breakdown despesas
  async getBreakdownDespesas(periodo: string) {
    const res = await fetch(`${API_URL}/api/financeiro/graficos/despesas-breakdown?periodo=${periodo}`);
    return res.json();
  },

  // Lançamentos
  async getLancamentos(periodo: string, tipo?: string, recorrencia?: string) {
    let url = `${API_URL}/api/financeiro/lancamentos?periodo=${periodo}`;
    if (tipo && tipo !== 'todos') url += `&tipo=${tipo}`;
    if (recorrencia && recorrencia !== 'todos') url += `&recorrencia=${recorrencia}`;
    const res = await fetch(url);
    return res.json();
  },

  async criarLancamento(data: any) {
    const res = await fetch(`${API_URL}/api/financeiro/lancamentos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async editarLancamento(id: number, data: any) {
    const res = await fetch(`${API_URL}/api/financeiro/lancamentos/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async deletarLancamento(id: number) {
    await fetch(`${API_URL}/api/financeiro/lancamentos/${id}`, {
      method: 'DELETE'
    });
  },

  // Categorias
  async getCategorias() {
    const res = await fetch(`${API_URL}/api/financeiro/categorias`);
    return res.json();
  },

  // Metas
  async getMetasProgresso(periodo: string) {
    const res = await fetch(`${API_URL}/api/financeiro/metas/progresso?periodo=${periodo}`);
    return res.json();
  },

  // Export CSV
  exportarCSV(periodo: string) {
    window.open(`${API_URL}/api/financeiro/lancamentos/export-csv?periodo=${periodo}`, '_blank');
  }
};
```

### 3.2 HOOKS CUSTOMIZADOS:

```typescript
// useFinanceiro.ts
function useFinanceiro(periodo: string) {
  const [overview, setOverview] = useState(null);
  const [taxa, setTaxa] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [overviewData, taxaData] = await Promise.all([
          api.getOverview(periodo),
          api.getTaxaCambio()
        ]);
        setOverview(overviewData);
        setTaxa(taxaData);
      } catch (error) {
        console.error('Erro ao buscar dados:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Auto-refresh taxa a cada 5 minutos
    const interval = setInterval(() => {
      api.getTaxaCambio().then(setTaxa);
    }, 300000);

    return () => clearInterval(interval);
  }, [periodo]);

  return { overview, taxa, loading };
}
```

---

## PASSO 4: MODAIS

### 4.1 Modal Adicionar/Editar Lançamento:

```tsx
<Dialog open={modalOpen} onOpenChange={setModalOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>
        {editando ? 'Editar Lançamento' : 'Novo Lançamento'}
      </DialogTitle>
    </DialogHeader>
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <Label>Categoria</Label>
          <Select name="categoria_id" required>
            <SelectTrigger>
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              {categorias.map(cat => (
                <SelectItem key={cat.id} value={cat.id.toString()}>
                  {cat.nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Valor (R$)</Label>
          <Input
            type="number"
            step="0.01"
            name="valor"
            placeholder="0,00"
            required
          />
        </div>

        <div>
          <Label>Data</Label>
          <Input type="date" name="data" required />
        </div>

        <div>
          <Label>Descrição</Label>
          <Textarea name="descricao" placeholder="Descrição do lançamento" />
        </div>

        <div>
          <Label>Tipo</Label>
          <Select name="tipo" required>
            <SelectTrigger>
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="receita">Receita</SelectItem>
              <SelectItem value="despesa">Despesa</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Recorrência</Label>
          <Select name="recorrencia">
            <SelectTrigger>
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fixa">Fixa (mensal)</SelectItem>
              <SelectItem value="unica">Única</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <DialogFooter className="mt-4">
        <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
          Cancelar
        </Button>
        <Button type="submit">
          {editando ? 'Salvar' : 'Criar'}
        </Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

---

## PASSO 5: RESPONSIVIDADE

### Breakpoints:
- Mobile: < 768px
  - Cards empilhados (1 coluna)
  - Filtros em select/dropdown
  - Gráficos altura reduzida (200px)

- Tablet: 768px - 1024px
  - Overview: 2 colunas
  - Breakdown + Lançamentos: empilhados

- Desktop: > 1024px
  - Overview: 4 colunas
  - Breakdown + Lançamentos: 2 colunas lado a lado

---

## PASSO 6: VALIDAÇÕES E TESTES

### Checklist de Validação:

**ANTES DE ENTREGAR, TESTE:**

1. ✅ Categoria "💰 Empresa" aparece ACIMA de "🚀 Navegação"
2. ✅ Aba "Tabela" continua sendo a padrão ao abrir
3. ✅ Filtro de período funciona (7d, 15d, 30d, 60d, 90d)
4. ✅ Taxa USD-BRL atualiza corretamente
5. ✅ 4 cards de overview mostram valores corretos
6. ✅ Variações (%) aparecem com seta up/down
7. ✅ Gráfico de linha mostra 3 séries (receita, despesas, lucro)
8. ✅ Gráfico pizza mostra breakdown por categoria
9. ✅ Gráfico pizza mostra breakdown por recorrência
10. ✅ Lista de lançamentos carrega corretamente
11. ✅ Filtros de lançamento funcionam (tipo, recorrência)
12. ✅ Modal de criar lançamento funciona
13. ✅ Modal de editar lançamento funciona
14. ✅ Deletar lançamento funciona
15. ✅ Metas aparecem com barra de progresso
16. ✅ Export CSV funciona
17. ✅ Responsividade mobile funciona
18. ✅ Cores seguem a paleta definida
19. ✅ Animações são suaves
20. ✅ Loading states funcionam

---

## PASSO 7: PALETA DE CORES FINAL

```typescript
const colors = {
  // Receitas
  receita: {
    primary: '#10B981',   // green-500
    light: '#34D399',     // green-400
    dark: '#059669',      // green-600
    gradient: 'from-green-500 to-emerald-600'
  },

  // Despesas
  despesa: {
    primary: '#EF4444',   // red-500
    light: '#F87171',     // red-400
    dark: '#DC2626',      // red-600
    gradient: 'from-red-500 to-rose-600'
  },

  // Lucro
  lucro: {
    primary: '#3B82F6',   // blue-500
    light: '#60A5FA',     // blue-400
    dark: '#2563EB',      // blue-600
  },

  // Background
  bg: {
    primary: '#0F172A',   // slate-900
    card: '#1E293B',      // slate-800
    hover: '#334155',     // slate-700
    border: '#475569',    // slate-600
  },

  // Categoria Empresa (menu)
  empresa: '#10B981'      // green-500
};
```

---

## ✅ ENTREGA FINAL

**POR FAVOR, IMPLEMENTE TUDO CONFORME ESPECIFICADO ACIMA E:**

1. ✅ Teste TODAS as funcionalidades da checklist
2. ✅ Verifique se a responsividade está funcionando
3. ✅ Confirme que todos os endpoints estão conectados
4. ✅ Valide que as cores estão corretas
5. ✅ Teste no mobile e desktop
6. ✅ **ENTREGUE PRONTO PARA USO!**

**Quando estiver tudo funcionando perfeitamente, me avise que está pronto!**

---

