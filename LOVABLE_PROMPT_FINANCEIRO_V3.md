# PROMPT LOVABLE - Sistema Financeiro (V3 FINAL)

## 🚨 VERSÃO FINAL COM TODAS AS CORREÇÕES

Este é o prompt definitivo com TODAS as correções solicitadas:

### Mudanças V2 → V3:
1. ✅ Header: **💲 Financeiro** (DESTACADO) + ícones [📅] [⚖️] [📁]
2. ✅ Período: 7d, 15d, 30d, **"Todo Período"** (SEM parênteses), Custom (REMOVIDO 60d/90d)
3. ✅ **Card Taxas:** Gradiente LARANJA
4. ✅ Card Lucro: "Lucro Líquido **(USD/BRL R$ 5,52)**" inline (não em box separado)
5. ✅ **REMOVIDO Card Lançamentos** (YouTube é única receita)
6. ✅ Card Despesas: **50% Pizza (ESQUERDA) | 50% Lista (DIREITA)**
7. ✅ Botão [+] para adicionar despesa DENTRO do card (só ícone, minimalista)
8. ✅ **Criar categoria INLINE** no modal de adicionar despesa
9. ✅ Categorias iniciais: **Ferramentas/Software, Salários, Infraestrutura, Contabilidade**
10. ✅ **NOVO:** Card Projeção do Mês (com novos endpoints)
11. ✅ **NOVO:** Card Comparação Mês a Mês (tabela)
12. ✅ **REMOVIDO:** Ícones repetidos embaixo (taxas/csv só no topo)

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

### ESTRUTURA FINAL (de cima para baixo):

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
│ 💲 Financeiro (DESTACADO)            [📅] [⚖️] [📁]         │
│                                      cal tax csv            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ OVERVIEW - 4 CARDS (tamanho uniforme)                       │
│                                                              │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │
│ │ Receita │ │Despesas │ │ Taxas  │ │ Lucro Líquido    │  │
│ │  Bruta  │ │ Totais  │ │ (3%)   │ │ R$ 23.731        │  │
│ │R$ 24.4k │ │ R$ 0,00 │ │R$ 733  │ │ (USD/BRL R$ 5.52)│  │
│ │ +15.2%  │ │  -5.3%  │ │ +15.2% │ │ +18.5%           │  │
│ └─────────┘ └─────────┘ └─────────┘ └──────────────────┘  │
│             CARD LARANJA ↑                                   │
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

┌──────────────────────────────┐ ┌─────────────────────────┐
│ PROJEÇÃO DO MÊS              │ │ COMPARAÇÃO MÊS A MÊS   │
│                              │ │                         │
│ Dezembro 2025                │ │ [Tabela últimos 6]     │
│ ─────────────────────────    │ │                         │
│ Total até hoje: R$ 20.173,93 │ │ Mês    | Receita | Var │
│ Média diária: R$ 1.186,70    │ │ ────────────────────────│
│ Dias restantes: 14           │ │ Out/25 | R$ 398  | -   │
│                              │ │ Nov/25 | R$ 3.8k |+865%│
│ PROJEÇÃO FIM DO MÊS:         │ │ Dez/25 | R$ 20k  |+424%│
│ R$ 36.787,75                 │ │                         │
│                              │ │                         │
└──────────────────────────────┘ └─────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ DESPESAS                                            [+]   │
│                                                            │
│ ┌──────────────────┐ ┌─────────────────────────────────┐ │
│ │  PIZZA (50%)     │ │  LISTA (50%)                   │ │
│ │                  │ │  ┌───────────────────────────┐ │ │
│ │  [Gráfico Pizza] │ │  │ Salários - R$ 5.000       │ │ │
│ │                  │ │  │ [edit] [delete]           │ │ │
│ │                  │ │  └───────────────────────────┘ │ │
│ │  Por Categoria   │ │  ┌───────────────────────────┐ │ │
│ │                  │ │  │ Ferramentas - R$ 500      │ │ │
│ │                  │ │  │ [edit] [delete]           │ │ │
│ │                  │ │  └───────────────────────────┘ │ │
│ └──────────────────┘ └─────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

**IMPORTANTE:**
- NÃO repetir ícones embaixo
- Taxas e CSV só aparecem NO TOPO ao lado do calendário
- Card Despesas: Pizza 50% ESQUERDA | Lista 50% DIREITA
- Botão [+] DENTRO do card Despesas (só ícone)

---

## PASSO 3: COMPONENTES DETALHADOS

### A. HEADER COM ÍCONES (CORRIGIDO)

```tsx
<div className="flex items-center justify-between mb-6">
  {/* Título com destaque */}
  <h1 className="text-3xl font-bold text-white flex items-center gap-2">
    <span className="text-4xl">💲</span>
    <span>Financeiro</span>
  </h1>

  {/* Ícones: Calendário, Taxas, CSV */}
  <div className="flex items-center gap-2">
    {/* Calendário - abre modal período */}
    <Button
      variant="outline"
      size="icon"
      onClick={() => setModalPeriodoOpen(true)}
      title="Período"
    >
      <Calendar className="w-5 h-5" />
    </Button>

    {/* Taxas - abre modal taxas */}
    <Button
      variant="outline"
      size="icon"
      onClick={() => setModalTaxasOpen(true)}
      title="Gerenciar Taxas"
    >
      <Scale className="w-5 h-5" />
    </Button>

    {/* Exportar CSV */}
    <Button
      variant="outline"
      size="icon"
      onClick={exportarCSV}
      title="Exportar CSV"
    >
      <FolderOpen className="w-5 h-5" />
    </Button>
  </div>
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
        onClick={() => {
          setPeriodo('2024-10-26,' + hoje);
          setModalPeriodoOpen(false);
        }}
      >
        Todo Período
      </Button>
      <Button
        variant="outline"
        className="w-full"
        onClick={() => {
          setModalCustomOpen(true);
          setModalPeriodoOpen(false);
        }}
      >
        Período Customizado
      </Button>
    </div>
  </DialogContent>
</Dialog>
```

**IMPORTANTE:**
- Título 💲 Financeiro com destaque (text-3xl ou text-4xl)
- Ícones na ordem: 📅 (Calendar) → ⚖️ (Scale) → 📁 (FolderOpen)
- REMOVIDO 60d e 90d
- "Todo Período" SEM parênteses na UI

### B. CARD TAXAS (LARANJA)

```tsx
<Card className="bg-gradient-to-br from-orange-500 to-orange-600">
  <CardHeader>
    <CardTitle className="text-white">Taxas (3%)</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold text-white">
      R$ {formatCurrency(overview.taxas_totais)}
    </div>
    <div className="flex items-center gap-1 text-white/90 text-sm mt-2">
      {overview.variacao_taxas > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
      {Math.abs(overview.variacao_taxas).toFixed(1)}%
    </div>
  </CardContent>
</Card>
```

### C. CARD LUCRO LÍQUIDO (Taxa inline)

```tsx
<Card className="bg-gradient-to-br from-blue-500 to-blue-600">
  <CardHeader>
    <CardTitle className="text-white">Lucro Líquido</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold text-white">
      R$ {formatCurrency(overview.lucro_liquido)}
    </div>

    {/* Taxa de câmbio INLINE (na mesma linha da variação) */}
    <div className="flex items-center justify-between mt-2">
      <div className="flex items-center gap-1 text-white/90 text-sm">
        {overview.variacao_lucro > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        {Math.abs(overview.variacao_lucro).toFixed(1)}%
      </div>
      <div className="text-xs text-white/70">
        USD/BRL R$ {taxa?.taxa?.toFixed(2)}
      </div>
    </div>
  </CardContent>
</Card>
```

**IMPORTANTE:**
- Taxa de câmbio fica inline, não em box separado
- Mantém tamanho original do card (compacto)

### D. CARD DESPESAS (50% Pizza | 50% Lista)

```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Despesas</CardTitle>
    {/* Botão + DENTRO do card (só ícone) */}
    <Button
      variant="outline"
      size="icon"
      onClick={() => setModalDespesaOpen(true)}
      title="Adicionar Despesa"
    >
      <Plus className="w-4 h-4" />
    </Button>
  </CardHeader>
  <CardContent>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* PIZZA (50% - ESQUERDA) */}
      <div>
        <h4 className="text-sm font-semibold mb-3">Por Categoria</h4>
        <ResponsiveContainer width="100%" height={250}>
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
      </div>

      {/* LISTA (50% - DIREITA) */}
      <div>
        <h4 className="text-sm font-semibold mb-3">Últimas Despesas</h4>
        <div className="space-y-2">
          {despesas.slice(0, 6).map((desp) => (
            <div key={desp.id} className="flex items-center justify-between p-2 rounded bg-slate-800">
              <div className="flex-1">
                <span className="text-sm">{desp.descricao}</span>
                <div className="text-xs text-muted-foreground">
                  {desp.categoria_nome} • {formatDate(desp.data)}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-sm font-semibold text-red-500">
                  R$ {formatCurrency(desp.valor)}
                </span>
                <Button variant="ghost" size="icon-sm" onClick={() => editarDespesa(desp)}>
                  <Edit className="w-3 h-3" />
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={() => deletarDespesa(desp.id)}>
                  <Trash className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </CardContent>
</Card>
```

**IMPORTANTE:**
- Pizza 50% ESQUERDA | Lista 50% DIREITA
- Botão [+] DENTRO do header (só ícone)
- No mobile: empilha (Pizza em cima, Lista embaixo)

### E. MODAL ADICIONAR DESPESA (Com criar categoria inline)

```tsx
<Dialog open={modalDespesaOpen} onOpenChange={setModalDespesaOpen}>
  <DialogContent className="max-w-md">
    <DialogHeader>
      <DialogTitle>Adicionar Despesa</DialogTitle>
    </DialogHeader>
    <div className="space-y-4">
      {/* Categoria - com opção de criar */}
      <div>
        <Label>Categoria</Label>
        <div className="flex gap-2">
          <Select value={formData.categoria_id} onValueChange={(v) => setFormData({...formData, categoria_id: v})}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              {categorias.map((cat) => (
                <SelectItem key={cat.id} value={cat.id.toString()}>
                  {cat.nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Botão criar categoria */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => setModalNovaCategoriaOpen(true)}
            title="Nova Categoria"
          >
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Valor */}
      <div>
        <Label>Valor (R$)</Label>
        <Input
          type="number"
          step="0.01"
          value={formData.valor}
          onChange={(e) => setFormData({...formData, valor: e.target.value})}
          placeholder="0,00"
        />
      </div>

      {/* Data */}
      <div>
        <Label>Data</Label>
        <Input
          type="date"
          value={formData.data}
          onChange={(e) => setFormData({...formData, data: e.target.value})}
        />
      </div>

      {/* Descrição */}
      <div>
        <Label>Descrição</Label>
        <Input
          value={formData.descricao}
          onChange={(e) => setFormData({...formData, descricao: e.target.value})}
          placeholder="Ex: Assinatura Lovable"
        />
      </div>

      {/* Recorrência */}
      <div>
        <Label>Recorrência</Label>
        <Select value={formData.recorrencia} onValueChange={(v) => setFormData({...formData, recorrencia: v})}>
          <SelectTrigger>
            <SelectValue placeholder="Selecione..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="unica">Única</SelectItem>
            <SelectItem value="fixa">Fixa (mensal)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Botões */}
      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={() => setModalDespesaOpen(false)}>
          Cancelar
        </Button>
        <Button onClick={salvarDespesa}>
          Salvar
        </Button>
      </div>
    </div>
  </DialogContent>
</Dialog>

{/* Modal Nova Categoria (inline) */}
<Dialog open={modalNovaCategoriaOpen} onOpenChange={setModalNovaCategoriaOpen}>
  <DialogContent className="max-w-sm">
    <DialogHeader>
      <DialogTitle>Nova Categoria</DialogTitle>
    </DialogHeader>
    <div className="space-y-4">
      <div>
        <Label>Nome</Label>
        <Input
          value={novaCategoria.nome}
          onChange={(e) => setNovaCategoria({...novaCategoria, nome: e.target.value})}
          placeholder="Ex: Marketing"
        />
      </div>
      <div>
        <Label>Cor</Label>
        <Input
          type="color"
          value={novaCategoria.cor}
          onChange={(e) => setNovaCategoria({...novaCategoria, cor: e.target.value})}
        />
      </div>
      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={() => setModalNovaCategoriaOpen(false)}>
          Cancelar
        </Button>
        <Button onClick={criarCategoria}>
          Criar
        </Button>
      </div>
    </div>
  </DialogContent>
</Dialog>
```

**IMPORTANTE:**
- Criar categoria DENTRO do modal de despesa (botão [+] ao lado do select)
- Categorias iniciais: Ferramentas/Software, Salários, Infraestrutura, Contabilidade

### F. CARD PROJEÇÃO DO MÊS (NOVO)

```tsx
<Card>
  <CardHeader>
    <CardTitle>Projeção do Mês</CardTitle>
  </CardHeader>
  <CardContent>
    {projecao ? (
      <div className="space-y-3">
        <div>
          <div className="text-sm text-muted-foreground">
            {projecao.mes_nome}
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            R$ {formatCurrency(projecao.total_ate_hoje)}
          </div>
          <div className="text-xs text-muted-foreground">
            Total até hoje
          </div>
        </div>

        <div className="border-t border-slate-700 pt-3">
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <div className="text-xs text-muted-foreground">Média diária</div>
              <div className="text-sm font-semibold">
                R$ {formatCurrency(projecao.media_diaria)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Dias restantes</div>
              <div className="text-sm font-semibold">
                {projecao.dias_restantes} de {projecao.dias_total}
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-500/20 to-green-600/20 p-3 rounded-lg">
            <div className="text-xs text-green-300 mb-1">
              PROJEÇÃO FIM DO MÊS
            </div>
            <div className="text-3xl font-bold text-green-400">
              R$ {formatCurrency(projecao.projecao_mes)}
            </div>
          </div>
        </div>
      </div>
    ) : (
      <div className="text-center py-8 text-muted-foreground">
        Carregando projeção...
      </div>
    )}
  </CardContent>
</Card>
```

### G. CARD COMPARAÇÃO MÊS A MÊS (NOVO)

```tsx
<Card>
  <CardHeader>
    <CardTitle>Comparação Mês a Mês</CardTitle>
  </CardHeader>
  <CardContent>
    {comparacao && comparacao.meses ? (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-2">Mês</th>
              <th className="text-right py-2">Receita</th>
              <th className="text-right py-2">Despesas</th>
              <th className="text-right py-2">Lucro</th>
              <th className="text-right py-2">Var.</th>
            </tr>
          </thead>
          <tbody>
            {comparacao.meses.map((m, idx) => (
              <tr key={idx} className="border-b border-slate-800">
                <td className="py-2">{m.mes_nome}</td>
                <td className="text-right text-green-400">
                  R$ {formatCurrency(m.receita)}
                </td>
                <td className="text-right text-red-400">
                  R$ {formatCurrency(m.despesas)}
                </td>
                <td className="text-right text-blue-400">
                  R$ {formatCurrency(m.lucro)}
                </td>
                <td className="text-right">
                  {m.variacao !== null ? (
                    <span className={m.variacao >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {m.variacao >= 0 ? '+' : ''}{m.variacao.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="text-center py-8 text-muted-foreground">
        Carregando comparação...
      </div>
    )}
  </CardContent>
</Card>
```

---

## PASSO 4: INTEGRAÇÃO COM BACKEND

### 4.1 BASE URL:
```typescript
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app';
```

### 4.2 CATEGORIAS INICIAIS:

Ao carregar a aba pela primeira vez, o setup já criou 4 categorias de despesa:

1. **Ferramentas/Software** (🔧)
2. **Salários** (👥)
3. **Infraestrutura** (🖥️)
4. **Contabilidade** (🧮)

### 4.3 ENDPOINTS PRINCIPAIS:

#### Overview (sempre atualizado com revenue real)
```typescript
GET /api/financeiro/overview?periodo=30d
GET /api/financeiro/overview?periodo=2024-10-26,2025-12-17  // Custom

Response:
{
  "receita_bruta": 24450.32,
  "despesas_totais": 5500.00,
  "despesas_fixas": 5000.00,
  "despesas_unicas": 500.00,
  "taxas_totais": 733.51,    // 3% da receita
  "lucro_liquido": 18216.81,
  "variacao_receita": 15.2,
  "variacao_despesas": -5.3,
  "variacao_taxas": 15.2,
  "variacao_lucro": 18.5
}
```

#### Taxa de Câmbio
```typescript
GET /api/financeiro/taxa-cambio

Response:
{
  "taxa": 5.52,
  "moeda_origem": "USD",
  "moeda_destino": "BRL",
  "timestamp": "2025-12-17T10:30:00"
}
```

#### **NOVO:** Projeção do Mês
```typescript
GET /api/financeiro/projecao-mes

Response:
{
  "mes": "2025-12",
  "mes_nome": "December 2025",
  "total_ate_hoje": 20173.93,
  "projecao_mes": 36787.75,
  "media_diaria": 1186.70,
  "dias_decorridos": 17,
  "dias_restantes": 14,
  "dias_total": 31,
  "taxa_cambio": 5.52
}
```

#### **NOVO:** Comparação Mensal
```typescript
GET /api/financeiro/comparacao-mensal?meses=6  // Default: 6 meses

Response:
{
  "meses": [
    {
      "mes": "2025-10",
      "mes_nome": "Oct/2025",
      "receita": 398.59,
      "despesas": 0.00,
      "taxas": 11.96,
      "lucro": 386.63,
      "variacao": null
    },
    {
      "mes": "2025-11",
      "mes_nome": "Nov/2025",
      "receita": 3848.18,
      "despesas": 0.00,
      "taxas": 115.44,
      "lucro": 3732.74,
      "variacao": 865.5  // +865.5% vs Oct
    },
    {
      "mes": "2025-12",
      "mes_nome": "Dec/2025",
      "receita": 20173.93,
      "despesas": 0.00,
      "taxas": 605.22,
      "lucro": 19568.71,
      "variacao": 424.1  // +424.1% vs Nov
    }
  ]
}
```

#### Gráfico Receita vs Despesas
```typescript
GET /api/financeiro/graficos/receita-despesas?periodo=30d

Response:
{
  "dados": [
    {"mes": "Out/25", "receita": 398.59, "despesas": 0.00},
    {"mes": "Nov/25", "receita": 3848.18, "despesas": 0.00},
    {"mes": "Dez/25", "receita": 20173.93, "despesas": 5500.00}
  ]
}
```

#### Breakdown Despesas (para gráfico pizza)
```typescript
GET /api/financeiro/graficos/despesas-breakdown?periodo=30d

Response:
{
  "por_categoria": [
    {"categoria": "Salários", "valor": 5000.00, "percentual": 90.9, "cor": "#CC0000"},
    {"categoria": "Ferramentas/Software", "valor": 500.00, "percentual": 9.1, "cor": "#FF0000"}
  ],
  "por_recorrencia": [
    {"recorrencia": "Fixa", "valor": 5000.00, "percentual": 90.9},
    {"recorrencia": "Única", "valor": 500.00, "percentual": 9.1}
  ]
}
```

#### Metas
```typescript
GET /api/financeiro/metas/progresso?periodo=30d

Response:
{
  "metas": [
    {
      "id": 1,
      "nome": "Receita R$ 30k",
      "tipo": "receita",
      "valor_objetivo": 30000.00,
      "valor_atual": 20173.93,
      "percentual": 67.2,
      "periodo_inicio": "2025-12-01",
      "periodo_fim": "2025-12-31"
    }
  ]
}

POST /api/financeiro/metas
Body: {
  "nome": "Receita R$ 30k",
  "tipo": "receita",  // ou "lucro_liquido"
  "valor_objetivo": 30000.00,
  "periodo_inicio": "2025-12-01",
  "periodo_fim": "2025-12-31"
}
```

#### Criar Lançamento (CORRIGIDO - JSON body)
```typescript
POST /api/financeiro/lancamentos
Headers: { 'Content-Type': 'application/json' }
Body: {
  "categoria_id": 5,
  "valor": 5000.00,
  "data": "2025-12-15",
  "descricao": "Salário Dev",
  "tipo": "despesa",
  "recorrencia": "fixa",  // ou "unica" ou null
  "usuario": "Marcelo"
}

Response:
{
  "id": 7,
  "categoria_id": 5,
  "categoria_nome": "Salários",
  "valor": 5000.00,
  "data": "2025-12-15",
  "descricao": "Salário Dev",
  "tipo": "despesa",
  "recorrencia": "fixa",
  "usuario": "Marcelo",
  "created_at": "2025-12-17T10:30:00"
}
```

#### Criar Categoria
```typescript
POST /api/financeiro/categorias
Headers: { 'Content-Type': 'application/json' }
Body: {
  "nome": "Marketing",
  "tipo": "despesa",
  "cor": "#FF5733",
  "icon": "megaphone"
}

Response:
{
  "id": 6,
  "nome": "Marketing",
  "tipo": "despesa",
  "cor": "#FF5733",
  "icon": "megaphone"
}
```

#### Listar Categorias
```typescript
GET /api/financeiro/categorias?tipo=despesa

Response:
{
  "categorias": [
    {"id": 2, "nome": "Ferramentas/Software", "tipo": "despesa", "cor": "#FF0000", "icon": "tools"},
    {"id": 3, "nome": "Salários", "tipo": "despesa", "cor": "#CC0000", "icon": "users"},
    {"id": 4, "nome": "Infraestrutura", "tipo": "despesa", "cor": "#DD0000", "icon": "server"},
    {"id": 5, "nome": "Contabilidade", "tipo": "despesa", "cor": "#AA0000", "icon": "calculator"}
  ]
}
```

#### Editar/Deletar Lançamento
```typescript
PATCH /api/financeiro/lancamentos/{id}
Body: { "valor": 5500.00, "descricao": "Salário Dev (reajustado)" }

DELETE /api/financeiro/lancamentos/{id}
```

#### Exportar CSV
```typescript
GET /api/financeiro/lancamentos/export-csv?periodo=90d

Response: Arquivo CSV com todos os lançamentos
```

---

## PASSO 5: RESPONSIVIDADE

### Grid Responsivo:

**Desktop (> 1024px):**
- Overview: 4 colunas
- Gráfico + Metas: 2 colunas (60% / 40%)
- Projeção + Comparação: 2 colunas (50% / 50%)
- Despesas: Pizza 50% esquerda | Lista 50% direita

**Tablet (768px - 1024px):**
- Overview: 2 colunas
- Todos os grids de 2 colunas: empilhados

**Mobile (< 768px):**
- Tudo empilhado (1 coluna)
- Gráficos altura reduzida (200px)
- Tabela comparação com scroll horizontal

```tsx
// Exemplo de grid responsivo
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* 4 cards overview */}
</div>

<div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
  <div className="lg:col-span-2">
    {/* Gráfico Receita vs Despesas (60%) */}
  </div>
  <div>
    {/* Metas (40%) */}
  </div>
</div>

<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
  {/* Projeção + Comparação (50/50) */}
</div>

<div>
  <Card>
    {/* Despesas - interno tem grid 50/50 */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Pizza | Lista */}
    </div>
  </Card>
</div>
```

---

## PASSO 6: VALIDAÇÕES E CHECKLIST

### ANTES DE ENTREGAR, TESTE:

1. ✅ Categoria "💰 Empresa" aparece ENTRE "🚀 Navegação" e "🛠️ Ferramentas"
2. ✅ Aba "Tabela" continua sendo a padrão ao abrir
3. ✅ Header: **💲 Financeiro** DESTACADO + ícones [📅] [⚖️] [📁]
4. ✅ Modal de período: 7d, 15d, 30d, "Todo Período", Custom (SEM 60d/90d)
5. ✅ Card Taxas com gradiente LARANJA
6. ✅ Card Lucro com taxa USD/BRL inline (não em box)
7. ✅ 4 cards overview uniformes e compactos
8. ✅ Gráfico mostra APENAS Receita vs Despesas (sem Lucro)
9. ✅ Metas aparecem ao lado do gráfico
10. ✅ **NOVO:** Card Projeção do Mês funciona
11. ✅ **NOVO:** Card Comparação Mês a Mês funciona (tabela)
12. ✅ Card Despesas: 50% Pizza (ESQUERDA) | 50% Lista (DIREITA)
13. ✅ Botão [+] DENTRO do card Despesas (só ícone)
14. ✅ Criar categoria INLINE no modal de despesa
15. ✅ Categorias iniciais: Ferramentas/Software, Salários, Infraestrutura, Contabilidade
16. ✅ **REMOVIDO:** Card Lançamentos separado
17. ✅ **REMOVIDO:** Ícones repetidos embaixo (taxas/csv só no topo)
18. ✅ Criar despesa funciona (JSON body correto)
19. ✅ Editar despesa funciona
20. ✅ Deletar despesa funciona
21. ✅ Overview sempre atualizado (consulta yt_daily_metrics)
22. ✅ Taxa de câmbio atualiza corretamente
23. ✅ Projeção calcula corretamente (média diária × dias do mês)
24. ✅ Comparação mostra últimos 6 meses com variação %
25. ✅ Responsividade mobile funciona
26. ✅ Cores seguem a paleta (verde, vermelho, azul, laranja, slate)
27. ✅ Export CSV funciona
28. ✅ Loading states em todas as requisições

---

## PASSO 7: PALETA DE CORES

```typescript
const colors = {
  receita: '#10B981',     // green-500
  despesa: '#EF4444',     // red-500
  lucro: '#3B82F6',       // blue-500
  taxas: '#F97316',       // orange-500 (NOVO)
  empresa: '#10B981',     // green-500 (categoria menu)

  bg: {
    primary: '#0F172A',   // slate-900
    card: '#1E293B',      // slate-800
    hover: '#334155',     // slate-700
  },

  gradients: {
    receita: 'from-green-500 to-green-600',
    despesa: 'from-red-500 to-red-600',
    lucro: 'from-blue-500 to-blue-600',
    taxas: 'from-orange-500 to-orange-600',  // NOVO
  }
};
```

---

## ✅ ENTREGA FINAL

**POR FAVOR:**

1. ✅ Implemente TODA a estrutura acima
2. ✅ Siga TODAS as correções V3 (header, taxas laranja, despesas 50/50, etc)
3. ✅ Use os novos endpoints (projecao-mes, comparacao-mensal)
4. ✅ Remova card Lançamentos e ícones repetidos
5. ✅ Teste TODAS as funcionalidades da checklist
6. ✅ Verifique responsividade
7. ✅ Confirme que a ordem do menu está correta
8. ✅ **ENTREGUE PRONTO PARA USO!**

**Quando estiver tudo funcionando, me avise!**

---
