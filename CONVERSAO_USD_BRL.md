# Conversão USD → BRL - Receita YouTube

## 🎯 O QUE FOI IMPLEMENTADO

Sistema automático de conversão de receita YouTube de USD para BRL usando taxa de câmbio em tempo real.

---

## 📊 RESULTADOS

### Antes (USD):
- Total 90 dias: $663,21 USD
- Receita mensal (30d): $663,21 USD

### Depois (BRL com taxa R$ 5,52):
- Total 90 dias: **R$ 20.210,54**
- Receita mensal (30d): **R$ 20.210,54**
- Taxas (3%): R$ 606,32
- Lucro líquido: **R$ 19.604,22**

---

## 🔧 MODIFICAÇÕES

### 1. `financeiro.py`

#### Nova função `get_usd_brl_rate()`:
```python
async def get_usd_brl_rate() -> Dict:
    """
    Retorna taxa de câmbio USD-BRL atualizada da AwesomeAPI

    Returns:
        Dict com:
        - taxa: float (ex: 5.52)
        - atualizado_em: str (ex: "2025-12-17 15:35:03")
    """
```

**Fonte:** `https://economia.awesomeapi.com.br/last/USD-BRL`
**Taxa atual (17/12/2025):** R$ 5,52

#### Modificações em `sync_youtube_revenue()`:
- Busca taxa de câmbio atual antes de processar
- Agrupa receitas por mês em USD
- **CONVERTE USD → BRL** antes de salvar lançamentos
- Retorna taxa de câmbio usada

#### Modificações em `get_youtube_revenue()`:
- Soma valores em USD
- **CONVERTE para BRL** usando taxa atual
- Retorna total em BRL

### 2. `main.py`

#### Novo endpoint:
```python
GET /api/financeiro/taxa-cambio
```

**Resposta:**
```json
{
  "taxa": 5.52,
  "atualizado_em": "2025-12-17 15:35:03"
}
```

### 3. Scripts

#### `limpar_lancamentos_youtube.py`
- Deleta lançamentos YouTube antigos (em USD)
- Prepara para re-sincronização com valores em BRL

**Uso:**
```bash
python limpar_lancamentos_youtube.py
```

---

## 🚀 COMO USAR

### 1. Consultar taxa atual:
```bash
GET https://youtube-dashboard-backend-production.up.railway.app/api/financeiro/taxa-cambio
```

### 2. Overview financeiro (já em BRL):
```bash
GET https://youtube-dashboard-backend-production.up.railway.app/api/financeiro/overview?periodo=30d
```

### 3. Sincronizar receita YouTube:
```bash
POST https://youtube-dashboard-backend-production.up.railway.app/api/financeiro/sync-youtube
Body: {"periodo": "90d"}
```

**Resposta:**
```json
{
  "sincronizados": 3,
  "periodo": "90d",
  "meses": 3,
  "taxa_cambio": 5.52,
  "taxa_atualizada_em": "2025-12-17 15:35:03"
}
```

---

## ⚙️ CONFIGURAÇÃO

### Railway (Produção)
✅ Deploy automático via GitHub
✅ Taxa de câmbio atualizada em tempo real
✅ Todos os valores financeiros em BRL

### Local (Desenvolvimento)
1. Limpar lançamentos USD antigos:
   ```bash
   python limpar_lancamentos_youtube.py
   ```

2. Re-sincronizar com BRL:
   ```bash
   python setup_simples.py
   ```

---

## 📈 API FINANCEIRA - ENDPOINTS

### Categorias (8 endpoints):
- `GET /api/financeiro/categorias`
- `POST /api/financeiro/categorias`
- `PATCH /api/financeiro/categorias/{id}`
- `DELETE /api/financeiro/categorias/{id}`

### Lançamentos (5 endpoints):
- `GET /api/financeiro/lancamentos` (filtros: periodo, tipo, recorrencia)
- `POST /api/financeiro/lancamentos`
- `PATCH /api/financeiro/lancamentos/{id}`
- `DELETE /api/financeiro/lancamentos/{id}`
- `GET /api/financeiro/lancamentos/export-csv`

### Taxas (4 endpoints):
- `GET /api/financeiro/taxas`
- `POST /api/financeiro/taxas`
- `PATCH /api/financeiro/taxas/{id}`
- `DELETE /api/financeiro/taxas/{id}`

### Metas (5 endpoints):
- `GET /api/financeiro/metas`
- `GET /api/financeiro/metas/progresso`
- `POST /api/financeiro/metas`
- `PATCH /api/financeiro/metas/{id}`
- `DELETE /api/financeiro/metas/{id}`

### Overview & Gráficos (4 endpoints):
- `GET /api/financeiro/overview`
- `GET /api/financeiro/graficos/receita-despesas`
- `GET /api/financeiro/graficos/despesas-breakdown`
- **`GET /api/financeiro/taxa-cambio`** ← NOVO!

### YouTube (2 endpoints):
- `GET /api/financeiro/youtube-revenue?periodo=30d`
- `POST /api/financeiro/sync-youtube` (body: `{"periodo": "90d"}`)

**Total:** 28 endpoints REST

---

## 🔍 DETALHES TÉCNICOS

### Taxa de Câmbio:
- **API:** AwesomeAPI (https://economia.awesomeapi.com.br)
- **Atualização:** Tempo real (a cada sincronização)
- **Valor usado:** Bid (compra)
- **Fallback:** R$ 5,50 (se API falhar)

### Conversão:
```python
# Antes (USD)
total_usd = 663.21

# Depois (BRL)
taxa = 5.52
total_brl = total_usd * taxa  # R$ 3.661,13
```

### Filtros de Receita:
```python
.eq("is_estimate", False)  # Apenas valores REAIS (confirmados)
```

---

## 📌 IMPORTANTE

1. **Todos os valores financeiros estão em BRL**
2. **Taxa de câmbio atualizada automaticamente**
3. **Apenas receitas reais (não estimadas)**
4. **Sincronização mensal (1 lançamento por mês)**
5. **Taxa de 3% aplicada sobre receita bruta**

---

## 📝 CHANGELOG

### v1.1.0 (17/12/2025)
- ✅ Conversão automática USD → BRL
- ✅ Endpoint `/api/financeiro/taxa-cambio`
- ✅ Script de limpeza `limpar_lancamentos_youtube.py`
- ✅ Integração com AwesomeAPI
- ✅ Overview atualizado com valores em BRL

### v1.0.0 (15/12/2025)
- ✅ Sistema financeiro completo (28 endpoints)
- ✅ Categorias, Lançamentos, Taxas, Metas
- ✅ Overview e Gráficos
- ✅ Integração YouTube (USD)

---

## 🎨 PRÓXIMO PASSO

Construir frontend personalizado consumindo os 28 endpoints REST!
