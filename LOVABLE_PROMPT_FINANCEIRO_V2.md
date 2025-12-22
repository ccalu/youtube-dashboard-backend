# PROMPT LOVABLE - Sistema Financeiro (V2 CORRIGIDO)

## 🚨 CORREÇÕES SOLICITADAS

Este prompt substitui a versão anterior com as seguintes correções:

1. ✅ Categoria "💰 Empresa" ENTRE "🚀 Navegação" e "🛠️ Ferramentas"
2. ✅ Nova ordem/layout da aba Financeiro
3. ✅ Filtro de período como ícone calendário (abre modal)
4. ✅ Taxa de câmbio minimalista no card Lucro Líquido
5. ✅ Gráfico Receita vs Despesas (SEM Lucro)
6. ✅ Metas ao lado do gráfico
7. ✅ Card Despesas (lista + gráfico pizza abaixo)
8. ✅ Card Lançamentos (todos, com filtros)
9. ✅ Filtro período com "Todo Período" (desde 26/10/2024)
10. ✅ Endpoint corrigido (422 fix)

---

## PASSO 1: ESTRUTURA DO MENU

### ORDEM CORRETA DAS CATEGORIAS:

```
🚀 Navegação ← ABA PADRÃO: "Tabela"
  ├─ Tabela
  ├─ Análise
  └─ Monetização

💰 Empresa ← AQUI! (ENTRE Navegação e Ferramentas)
  └─ Financeiro

🛠️ Ferramentas
  └─ (outras abas)
```

**IMPORTANTE:**
- Categoria "💰 Empresa" fica **ENTRE** "🚀 Navegação" e "🛠️ Ferramentas"
- Aba "Tabela" **CONTINUA sendo a padrão** ao abrir o dashboard
- Cor da categoria Empresa: Verde (#10B981)

---

## PASSO 2: LAYOUT DA ABA FINANCEIRO

### NOVA ESTRUTURA (de cima para baixo):

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
│ Financeiro                          [📅] ← ícone calendário │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ OVERVIEW - 4 CARDS (grid responsivo)                        │
│                                                              │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐      │
│ │ Receita │ │Despesas │ │ Taxas  │ │ Lucro Líquido│      │
│ │  Bruta  │ │ Totais  │ │  (3%)  │ │ R$ 23.731    │      │
│ │R$ 24.4k │ │ R$ 0,00 │ │R$ 733  │ │ ─────────────│      │
│ │ +15.2%  │ │  -5.3%  │ │ +15.2% │ │ USD/BRL 5.52 │      │
│ └─────────┘ └─────────┘ └─────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐ ┌─────────────────────────┐
│ GRÁFICO: Receita vs Despesas │ │ METAS FINANCEIRAS      │
│ (linha, 2 séries)            │ │ ┌────────────────────┐ │
│                              │ │ │ Meta 1             │ │
│ - Receita (verde)            │ │ │ [██████░░░░] 67%  │ │
│ - Despesas (vermelho)        │ │ │ R$ 20k / R$ 30k   │ │
│                              │ │ └────────────────────┘ │
│                              │ │ [+ Adicionar Meta]     │
└──────────────────────────────┘ └─────────────────────────┘

┌──────────────────┐ ┌─────────────────────────────────────┐
│ DESPESAS         │ │ LANÇAMENTOS (Todos)                │
│                  │ │                                     │
│ Lista:           │ │ [+ Adicionar Lançamento]           │
│ ┌──────────────┐ │ │                                     │
│ │ Salários     │ │ │ Filtros:                           │
│ │ R$ 5.000     │ │ │ [Tipo: Todos ▼] [Recorr.: Todos ▼]│
│ └──────────────┘ │ │                                     │
│ ┌──────────────┐ │ │ Lista:                             │
│ │ Ferramentas  │ │ │ ┌─────────────────────────────────┐│
│ │ R$ 500       │ │ │ │ 01/12 - YouTube AdSense         ││
│ └──────────────┘ │ │ │ R$ 20.210,54 [Receita]          ││
│                  │ │ │ [Editar] [Deletar]               ││
│ ─────────────────│ │ └─────────────────────────────────┘│
│ Gráfico Pizza:   │ │ ┌─────────────────────────────────┐│
│ (Por categoria)  │ │ │ 15/12 - Salário Dev             ││
│                  │ │ │ R$ 5.000,00 [Despesa] [Fixa]    ││
│ [Gráfico aqui]   │ │ │ [Editar] [Deletar]               ││
│                  │ │ └─────────────────────────────────┘│
└──────────────────┘ └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ GESTÃO                                                       │
│ [Categorias] [Taxas] [Exportar CSV]                        │
└─────────────────────────────────────────────────────────────┘
```

---

## PASSO 3: COMPONENTES DETALHADOS

### A. HEADER COM FILTRO (Ícone Calendário)

```tsx
<div className="flex items-center justify-between mb-6">
  <h1 className="text-2xl font-bold text-white">Financeiro</h1>

  {/* Ícone calendário - abre modal */}
  <Button
    variant="outline"
    size="icon"
    onClick={() => setModalPeriodoOpen(true)}
  >
    <Calendar className="w-5 h-5" />
  </Button>
</div>

{/* Modal de Período */}
<Dialog open={modalPeriodoOpen} onOpenChange={setModalPeriodoOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Selecionar Período</DialogTitle>
    </DialogHeader>
    <div className="space-y-2">
      <Button
        variant={periodo === '7d' ? 'default' : 'outline'}
        className="w-full"
        onClick={() => { setPeriodo('7d'); setModalPeriodoOpen(false); }}
      >
        Últimos 7 dias
      </Button>
      <Button
        variant={periodo === '15d' ? 'default' : 'outline'}
        className="w-full"
        onClick={() => { setPeriodo('15d'); setModalPeriodoOpen(false); }}
      >
        Últimos 15 dias
      </Button>
      <Button
        variant={periodo === '30d' ? 'default' : 'outline'}
        className="w-full"
        onClick={() => { setPeriodo('30d'); setModalPeriodoOpen(false); }}
      >
        Últimos 30 dias
      </Button>
      <Button
        variant={periodo === 'all' ? 'default' : 'outline'}
        className="w-full"
        onClick={() => { setPeriodo('2024-10-26,' + hoje); setModalPeriodoOpen(false); }}
      >
        Todo o Período (desde 26/10/2024)
      </Button>
      <Button
        variant="outline"
        className="w-full"
        onClick={() => { setModalCustomOpen(true); setModalPeriodoOpen(false); }}
      >
        Período Customizado
      </Button>
    </div>
  </DialogContent>
</Dialog>
```

### B. CARD LUCRO LÍQUIDO (com taxa de câmbio)

```tsx
<Card className="bg-gradient-to-br from-blue-500 to-blue-600">
  <CardHeader>
    <CardTitle className="text-white">Lucro Líquido</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold text-white">
      R$ {formatCurrency(overview.lucro_liquido)}
    </div>
    <div className="flex items-center gap-1 text-white/90 text-sm mt-2">
      {overview.variacao_lucro > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
      {Math.abs(overview.variacao_lucro).toFixed(1)}%
    </div>

    {/* Taxa de câmbio minimalista */}
    <div className="border-t border-white/20 mt-3 pt-3">
      <div className="text-xs text-white/70">USD/BRL</div>
      <div className="text-sm font-semibold text-white">
        R$ {taxa?.taxa?.toFixed(2)}
      </div>
    </div>
  </CardContent>
</Card>
```

### C. GRÁFICO RECEITA VS DESPESAS (sem Lucro)

```tsx
<Card>
  <CardHeader>
    <CardTitle>Receita vs Despesas</CardTitle>
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
      </LineChart>
    </ResponsiveContainer>
  </CardContent>
</Card>
```

### D. METAS (ao lado do gráfico)

```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Metas Financeiras</CardTitle>
    <Button onClick={() => setModalMetaOpen(true)} size="sm">
      <Plus className="w-4 h-4 mr-2" />
      Adicionar
    </Button>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      {metas.map((meta) => (
        <div key={meta.id} className="p-4 rounded-lg bg-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-sm">{meta.nome}</span>
            <span className="text-sm text-muted-foreground">
              {meta.percentual.toFixed(1)}%
            </span>
          </div>
          <Progress value={meta.percentual} className="mb-2 h-2" />
          <div className="text-xs text-muted-foreground">
            R$ {formatCurrency(meta.valor_atual)} / R$ {formatCurrency(meta.valor_objetivo)}
          </div>
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

### E. CARD DESPESAS (Lista + Gráfico Pizza)

```tsx
<Card>
  <CardHeader>
    <CardTitle>Despesas</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Lista de Despesas */}
    <div className="space-y-2 mb-6">
      {despesas.slice(0, 5).map((desp) => (
        <div key={desp.id} className="flex items-center justify-between p-2 rounded bg-slate-800">
          <span className="text-sm">{desp.descricao}</span>
          <span className="text-sm font-semibold text-red-500">
            R$ {formatCurrency(desp.valor)}
          </span>
        </div>
      ))}
    </div>

    {/* Gráfico Pizza - Breakdown por Categoria */}
    <div>
      <h4 className="text-sm font-semibold mb-3">Por Categoria</h4>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={breakdown.por_categoria}
            dataKey="valor"
            nameKey="categoria"
            cx="50%"
            cy="50%"
            outerRadius={70}
            label={({ percentual }) => `${percentual.toFixed(1)}%`}
          >
            {breakdown.por_categoria.map((entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `R$ ${formatCurrency(value)}`} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  </CardContent>
</Card>
```

### F. CARD LANÇAMENTOS (Todos, com Filtros)

```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Lançamentos</CardTitle>
    <Button onClick={() => setModalLancamentoOpen(true)} size="sm">
      <Plus className="w-4 h-4 mr-2" />
      Adicionar
    </Button>
  </CardHeader>
  <CardContent>
    {/* Filtros */}
    <div className="flex gap-2 mb-4">
      <Select value={filtroTipo} onValueChange={setFiltroTipo}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todos</SelectItem>
          <SelectItem value="receita">Receita</SelectItem>
          <SelectItem value="despesa">Despesa</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filtroRecorrencia} onValueChange={setFiltroRecorrencia}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Recorrência" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todos</SelectItem>
          <SelectItem value="fixa">Fixa</SelectItem>
          <SelectItem value="unica">Única</SelectItem>
        </SelectContent>
      </Select>
    </div>

    {/* Lista de Lançamentos */}
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {lancamentosFiltrados.map((lanc) => (
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
                  <Badge variant="outline" className="text-xs">
                    {lanc.recorrencia}
                  </Badge>
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
              <Button variant="ghost" size="icon-sm" onClick={() => editarLancamento(lanc)}>
                <Edit className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="icon-sm" onClick={() => deletarLancamento(lanc.id)}>
                <Trash className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

---

## PASSO 4: INTEGRAÇÃO COM BACKEND

### 4.1 BASE URL:
```typescript
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app';
```

### 4.2 ENDPOINT CRIAR LANÇAMENTO (CORRIGIDO):

**IMPORTANTE:** O endpoint agora aceita JSON body (não query params)

```typescript
async function criarLancamento(dados: {
  categoria_id: number;
  valor: number;
  data: string; // YYYY-MM-DD
  descricao: string;
  tipo: 'receita' | 'despesa';
  recorrencia?: 'fixa' | 'unica' | null;
  usuario?: string;
}) {
  const response = await fetch(`${API_URL}/api/financeiro/lancamentos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(dados)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Erro ao criar lançamento');
  }

  return response.json();
}
```

**Exemplo de uso:**
```typescript
await criarLancamento({
  categoria_id: 5, // ID da categoria "Salários"
  valor: 5000.00,
  data: "2025-12-15",
  descricao: "Salário Dev",
  tipo: "despesa",
  recorrencia: "fixa",
  usuario: "Marcelo"
});
```

### 4.3 OUTROS ENDPOINTS:

```typescript
// Overview (sempre atualizado com revenue real)
GET /api/financeiro/overview?periodo=30d
GET /api/financeiro/overview?periodo=2024-10-26,2025-12-17  // Custom

// Taxa de câmbio
GET /api/financeiro/taxa-cambio

// Gráfico Receita vs Despesas
GET /api/financeiro/graficos/receita-despesas?periodo=30d

// Breakdown Despesas (para gráfico pizza)
GET /api/financeiro/graficos/despesas-breakdown?periodo=30d

// Lançamentos (com filtros)
GET /api/financeiro/lancamentos?periodo=30d&tipo=despesa
GET /api/financeiro/lancamentos?periodo=30d&tipo=receita&recorrencia=fixa

// Metas
GET /api/financeiro/metas/progresso?periodo=30d

// Editar lançamento
PATCH /api/financeiro/lancamentos/{id}
Body: { valor: 5500.00, descricao: "Salário Dev (reajustado)" }

// Deletar lançamento
DELETE /api/financeiro/lancamentos/{id}

// Exportar CSV
GET /api/financeiro/lancamentos/export-csv?periodo=90d
```

---

## PASSO 5: RESPONSIVIDADE

### Grid Responsivo:

**Desktop (> 1024px):**
- Overview: 4 colunas
- Gráfico + Metas: 2 colunas (60% / 40%)
- Despesas + Lançamentos: 2 colunas (40% / 60%)

**Tablet (768px - 1024px):**
- Overview: 2 colunas
- Gráfico + Metas: empilhados
- Despesas + Lançamentos: empilhados

**Mobile (< 768px):**
- Tudo empilhado (1 coluna)
- Gráficos altura reduzida (200px)
- Filtros em modal

---

## PASSO 6: VALIDAÇÕES E CHECKLIST

### ANTES DE ENTREGAR, TESTE:

1. ✅ Categoria "💰 Empresa" aparece ENTRE "🚀 Navegação" e "🛠️ Ferramentas"
2. ✅ Aba "Tabela" continua sendo a padrão ao abrir
3. ✅ Filtro de período é ícone calendário (abre modal)
4. ✅ Modal de período tem: 7d, 15d, 30d, "Todo Período", Custom
5. ✅ Card Lucro Líquido mostra taxa USD/BRL
6. ✅ 4 cards de overview mostram valores corretos
7. ✅ Gráfico mostra APENAS Receita vs Despesas (sem Lucro)
8. ✅ Metas aparecem ao lado do gráfico
9. ✅ Card Despesas mostra lista + gráfico pizza abaixo
10. ✅ Card Lançamentos mostra TODOS (receitas + despesas)
11. ✅ Filtros de lançamento funcionam (tipo, recorrência)
12. ✅ Criar lançamento funciona (JSON body correto)
13. ✅ Editar lançamento funciona
14. ✅ Deletar lançamento funciona
15. ✅ Overview sempre atualizado (consulta yt_daily_metrics)
16. ✅ Taxa de câmbio atualiza corretamente
17. ✅ Responsividade mobile funciona
18. ✅ Cores seguem a paleta (verde, vermelho, azul, slate)
19. ✅ Export CSV funciona
20. ✅ Loading states em todas as requisições

---

## PASSO 7: PALETA DE CORES

```typescript
const colors = {
  receita: '#10B981',     // green-500
  despesa: '#EF4444',     // red-500
  lucro: '#3B82F6',       // blue-500
  empresa: '#10B981',     // green-500 (categoria menu)

  bg: {
    primary: '#0F172A',   // slate-900
    card: '#1E293B',      // slate-800
    hover: '#334155',     // slate-700
  }
};
```

---

## ✅ ENTREGA FINAL

**POR FAVOR:**

1. ✅ Implemente TODA a estrutura acima
2. ✅ Teste TODAS as funcionalidades da checklist
3. ✅ Use o endpoint corrigido (JSON body)
4. ✅ Verifique responsividade
5. ✅ Confirme que a ordem do menu está correta
6. ✅ **ENTREGUE PRONTO PARA USO!**

**Quando estiver tudo funcionando, me avise!**

---
