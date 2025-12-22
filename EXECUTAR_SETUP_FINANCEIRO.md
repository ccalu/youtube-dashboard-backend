# Setup do Sistema Financeiro

## 📋 Passo a Passo

### 1️⃣ Criar Tabelas no Supabase

**Acesse:** https://supabase.com/dashboard/project/prvkmzstyedepvlbppyo/editor/sql

**Cole e execute o SQL:**
```
Arquivo: create_financial_tables.sql
```

Copie TODO o conteúdo do arquivo `create_financial_tables.sql` e execute no SQL Editor do Supabase.

**Resultado esperado:**
- 4 tabelas criadas: `financeiro_categorias`, `financeiro_lancamentos`, `financeiro_taxas`, `financeiro_metas`
- Índices criados
- Triggers de `updated_at` funcionando

---

### 2️⃣ Rodar Setup (Dados Iniciais)

**No terminal:**
```powershell
cd D:\ContentFactory\youtube-dashboard-backend
python setup_financeiro.py
```

**O que o script faz:**
- ✅ Cria 8 categorias padrão (YouTube AdSense, Ferramentas, Salários, etc)
- ✅ Cria taxa padrão de 3% (Imposto)
- ✅ Sincroniza receita YouTube dos últimos 90 dias
- ✅ Mostra overview financeiro

**Resultado esperado:**
```
==============================================================
SETUP FINANCEIRO - Dados Iniciais
==============================================================

1. Criando categorias padrão...
   ✓ YouTube AdSense criada
   ✓ Patrocínios criada
   ✓ Ferramentas/Software criada
   ✓ Salários criada
   ...

2. Criando taxa padrão...
   ✓ Taxa 'Imposto' (3%) criada

3. Sincronizando receita YouTube (últimos 90 dias)...
   ✓ 3 meses sincronizados
   ✓ Total de 3 meses processados

==============================================================
RESUMO FINAL
==============================================================
✓ Categorias criadas: 8
✓ Taxas ativas: 1
✓ Lançamentos (90d): 3

OVERVIEW (últimos 30 dias):
  Receita Bruta: R$ 15.250,00
  Despesas: R$ 0,00
  Taxas: R$ 457,50
  Lucro Líquido: R$ 14.792,50

==============================================================
SETUP CONCLUÍDO!
==============================================================
```

---

### 3️⃣ Testar API

**Rodar servidor local:**
```powershell
python main.py
```

**Testar endpoints:**

1. **Listar categorias:**
   ```
   GET http://localhost:8000/api/financeiro/categorias
   ```

2. **Ver overview:**
   ```
   GET http://localhost:8000/api/financeiro/overview?periodo=30d
   ```

3. **Criar despesa fixa:**
   ```
   POST http://localhost:8000/api/financeiro/lancamentos
   Body: {
     "categoria_id": 5,
     "valor": 8000.00,
     "data": "2024-12-01",
     "descricao": "Pagamento Time",
     "tipo": "despesa",
     "recorrencia": "fixa"
   }
   ```

4. **Ver lançamentos:**
   ```
   GET http://localhost:8000/api/financeiro/lancamentos?periodo=30d
   ```

5. **Ver gráficos:**
   ```
   GET http://localhost:8000/api/financeiro/graficos/receita-despesas?periodo=30d
   GET http://localhost:8000/api/financeiro/graficos/despesas-breakdown?periodo=30d
   ```

---

### 4️⃣ Deploy no Railway

**Quando estiver tudo testado:**

```powershell
git add .
git commit -m "feat: Adicionar sistema financeiro completo

- Tabelas: categorias, lançamentos, taxas, metas
- Lógica: cálculos, overview, gráficos
- Endpoints: CRUD completo + overview + gráficos
- Integração YouTube automática
- Despesas fixas vs únicas
- Export CSV
- Taxa de 3% (Imposto)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

Railway vai fazer auto-deploy e a API estará disponível em produção!

---

## 🎯 Endpoints Disponíveis

### Categorias
- `GET /api/financeiro/categorias` - Listar
- `POST /api/financeiro/categorias` - Criar
- `PATCH /api/financeiro/categorias/{id}` - Editar
- `DELETE /api/financeiro/categorias/{id}` - Deletar

### Lançamentos
- `GET /api/financeiro/lancamentos?periodo=30d&tipo=despesa&recorrencia=fixa` - Listar com filtros
- `POST /api/financeiro/lancamentos` - Criar
- `PATCH /api/financeiro/lancamentos/{id}` - Editar
- `DELETE /api/financeiro/lancamentos/{id}` - Deletar
- `GET /api/financeiro/lancamentos/export-csv?periodo=30d` - Exportar CSV

### Taxas
- `GET /api/financeiro/taxas` - Listar
- `POST /api/financeiro/taxas` - Criar
- `PATCH /api/financeiro/taxas/{id}` - Editar
- `DELETE /api/financeiro/taxas/{id}` - Deletar

### Metas
- `GET /api/financeiro/metas` - Listar
- `GET /api/financeiro/metas/progresso` - Ver progresso
- `POST /api/financeiro/metas` - Criar
- `PATCH /api/financeiro/metas/{id}` - Editar
- `DELETE /api/financeiro/metas/{id}` - Deletar

### Dashboard/Overview
- `GET /api/financeiro/overview?periodo=30d` - Cards principais
- `GET /api/financeiro/graficos/receita-despesas?periodo=30d` - Gráfico linha
- `GET /api/financeiro/graficos/despesas-breakdown?periodo=30d` - Gráfico pizza

### Integração YouTube
- `GET /api/financeiro/youtube-revenue?periodo=30d` - Consultar receita
- `POST /api/financeiro/sync-youtube?periodo=90d` - Sincronizar lançamentos

---

## 🔄 Próximos Passos

Após o backend estar funcionando:
1. Testar todos os endpoints
2. Ajustar lógica se necessário
3. Deploy no Railway
4. Começar desenvolvimento do frontend (você monta do seu jeito!)
