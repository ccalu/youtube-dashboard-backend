# 10 - Sistema Financeiro

**Gestão financeira completa: receitas, despesas, taxas, metas e integração com YouTube**

---

## Índice

1. [Visão Geral](#visão-geral)
2. [FinanceiroService Class](#financeiroservice-class)
3. [Categorias](#categorias)
4. [Lançamentos](#lançamentos)
5. [Taxas](#taxas)
6. [Metas](#metas)
7. [Integração YouTube](#integração-youtube)
8. [Conversão USD→BRL](#conversão-usdbrl)

---

## Visão Geral

**Arquivo:** `D:\ContentFactory\youtube-dashboard-backend\financeiro.py` (994 linhas)

**Objetivo:** Centralizar gestão financeira do negócio

**Features:**
- Lançamentos manuais (receitas/despesas)
- Categorias personalizadas
- Taxas automáticas (impostos, etc)
- Metas financeiras
- Integração automática com YouTube revenue
- Conversão USD→BRL em tempo real
- Projeções de receita
- Comparação mensal
- Gráficos de performance

---

## FinanceiroService Class

### 1. Inicialização

```python
class FinanceiroService:
    """Serviço de gestão financeira"""

    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase
```

**Uso:**
```python
from database import SupabaseClient
from financeiro import FinanceiroService

db = SupabaseClient()
financeiro = FinanceiroService(db)

# Buscar overview
overview = await financeiro.get_overview(periodo="30d")
```

---

### 2. Parse de Períodos

```python
def parse_periodo(periodo: str) -> Tuple[datetime, datetime]:
    """
    Converte string de período em datas início/fim

    Formatos aceitos:
    - '7d', '15d', '30d', '60d', '90d'
    - 'YYYY-MM-DD,YYYY-MM-DD' (custom)
    """
    hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if ',' in periodo:
        # Custom: '2024-01-01,2024-03-31'
        inicio_str, fim_str = periodo.split(',')
        data_inicio = datetime.fromisoformat(inicio_str).replace(tzinfo=timezone.utc)
        data_fim = datetime.fromisoformat(fim_str).replace(tzinfo=timezone.utc)
    elif periodo.endswith('d'):
        # Dias: '30d'
        dias = int(periodo[:-1])
        data_fim = hoje
        data_inicio = hoje - timedelta(days=dias)
    else:
        # Default: 30 dias
        data_fim = hoje
        data_inicio = hoje - timedelta(days=30)

    return data_inicio, data_fim
```

**Exemplos:**
```python
# Últimos 30 dias
parse_periodo("30d")
# → (2023-12-11, 2024-01-10)

# Período custom
parse_periodo("2024-01-01,2024-01-31")
# → (2024-01-01, 2024-01-31)
```

---

## Categorias

### 1. Tabela: financeiro_categorias

```sql
CREATE TABLE financeiro_categorias (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL UNIQUE,
  tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
  cor TEXT,           -- HEX color (ex: "#00FF00")
  icon TEXT,          -- Icon name (ex: "youtube", "dollar")
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Categorias padrão:**
```sql
INSERT INTO financeiro_categorias (nome, tipo, cor, icon) VALUES
  ('YouTube AdSense', 'receita', '#00FF00', 'youtube'),
  ('Parcerias', 'receita', '#4CAF50', 'handshake'),
  ('Hospedagem', 'despesa', '#FF6B6B', 'server'),
  ('API Keys', 'despesa', '#FFA500', 'key'),
  ('Ferramentas', 'despesa', '#9C27B0', 'wrench'),
  ('Marketing', 'despesa', '#2196F3', 'megaphone');
```

---

### 2. Listar Categorias

**Endpoint:** `GET /api/financeiro/categorias`

**Código:**
```python
async def listar_categorias(self, ativo: bool = None) -> List[Dict]:
    """Lista todas as categorias"""
    query = self.supabase.table("financeiro_categorias").select("*")

    if ativo is not None:
        query = query.eq("ativo", ativo)

    response = query.order("tipo", desc=False).order("nome", desc=False).execute()
    return response.data if response.data else []
```

**Response:**
```json
{
  "categorias": [
    {
      "id": 1,
      "nome": "YouTube AdSense",
      "tipo": "receita",
      "cor": "#00FF00",
      "icon": "youtube",
      "ativo": true
    }
  ]
}
```

---

### 3. Criar Categoria

**Endpoint:** `POST /api/financeiro/categorias`

**Request:**
```json
{
  "nome": "Freelancing",
  "tipo": "receita",
  "cor": "#4CAF50",
  "icon": "dollar"
}
```

**Código:**
```python
async def criar_categoria(
    self,
    nome: str,
    tipo: str,
    cor: str = None,
    icon: str = None
) -> Dict:
    """Cria nova categoria"""
    response = self.supabase.table("financeiro_categorias").insert({
        "nome": nome,
        "tipo": tipo,
        "cor": cor,
        "icon": icon,
        "ativo": True
    }).execute()

    logger.info(f"Categoria criada: {nome} ({tipo})")
    return response.data[0]
```

---

### 4. Soft Delete

**Endpoint:** `DELETE /api/financeiro/categorias/{categoria_id}`

```python
async def deletar_categoria(self, categoria_id: int) -> bool:
    """Deleta categoria (soft delete)"""
    response = self.supabase.table("financeiro_categorias")\
        .update({"ativo": False})\
        .eq("id", categoria_id)\
        .execute()

    logger.info(f"Categoria {categoria_id} deletada")
    return True
```

**Nota:** Soft delete preserva histórico de lançamentos

---

## Lançamentos

### 1. Tabela: financeiro_lancamentos

```sql
CREATE TABLE financeiro_lancamentos (
  id SERIAL PRIMARY KEY,
  categoria_id INTEGER REFERENCES financeiro_categorias(id),
  valor DECIMAL(10,2) NOT NULL,
  data DATE NOT NULL,
  descricao TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
  recorrencia TEXT CHECK (recorrencia IN ('fixa', 'unica')),  -- Apenas para despesas
  usuario TEXT,  -- Quem criou (ex: "Cellibs", "Arthur", "sistema")
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lancamentos_data ON financeiro_lancamentos(data);
CREATE INDEX idx_lancamentos_tipo ON financeiro_lancamentos(tipo);
```

---

### 2. Listar Lançamentos

**Endpoint:** `GET /api/financeiro/lancamentos`

**Query Parameters:**
```typescript
{
  periodo?: string           // "30d" (padrão) | "7d" | "YYYY-MM-DD,YYYY-MM-DD"
  tipo?: "receita" | "despesa"
  recorrencia?: "fixa" | "unica"
}
```

**Código:**
```python
async def listar_lancamentos(
    self,
    periodo: str = "30d",
    tipo: str = None,
    recorrencia: str = None
) -> List[Dict]:
    """Lista lançamentos com filtros"""
    data_inicio, data_fim = parse_periodo(periodo)

    query = self.supabase.table("financeiro_lancamentos")\
        .select("*, financeiro_categorias(nome, cor)")\
        .gte("data", data_inicio.date())\
        .lte("data", data_fim.date())

    if tipo:
        query = query.eq("tipo", tipo)

    if recorrencia:
        query = query.eq("recorrencia", recorrencia)

    response = query.order("data", desc=True).execute()
    return response.data if response.data else []
```

**Response:**
```json
{
  "lancamentos": [
    {
      "id": 123,
      "categoria_id": 1,
      "valor": 450.00,
      "data": "2024-01-10",
      "descricao": "Publicidade Instagram",
      "tipo": "despesa",
      "recorrencia": "unica",
      "usuario": "Cellibs",
      "financeiro_categorias": {
        "nome": "Marketing",
        "cor": "#2196F3"
      }
    }
  ]
}
```

---

### 3. Criar Lançamento

**Endpoint:** `POST /api/financeiro/lancamentos`

**Request:**
```json
{
  "categoria_id": 3,
  "valor": 89.90,
  "data": "2024-01-10",
  "descricao": "Railway - Hospedagem mensal",
  "tipo": "despesa",
  "recorrencia": "fixa",
  "usuario": "Cellibs"
}
```

**Código:**
```python
async def criar_lancamento(
    self,
    categoria_id: int,
    valor: float,
    data: str,
    descricao: str,
    tipo: str,
    recorrencia: str = None,
    usuario: str = None
) -> Dict:
    """Cria novo lançamento"""

    # Validação: recorrencia só para despesas
    if tipo == "receita" and recorrencia:
        recorrencia = None

    response = self.supabase.table("financeiro_lancamentos").insert({
        "categoria_id": categoria_id,
        "valor": valor,
        "data": data,
        "descricao": descricao,
        "tipo": tipo,
        "recorrencia": recorrencia,
        "usuario": usuario
    }).execute()

    logger.info(f"Lançamento criado: {tipo} R$ {valor} ({descricao})")
    return response.data[0]
```

**Validações:**
- Receitas nunca têm `recorrencia` (sempre `null`)
- Despesas podem ser `"fixa"` ou `"unica"`

---

### 4. Editar Lançamento

**Endpoint:** `PATCH /api/financeiro/lancamentos/{lancamento_id}`

**Request:**
```json
{
  "valor": 99.90,
  "descricao": "Railway - Hospedagem mensal (atualizado)"
}
```

---

### 5. Deletar Lançamento

**Endpoint:** `DELETE /api/financeiro/lancamentos/{lancamento_id}`

**Nota:** Hard delete (remove permanentemente)

---

## Taxas

### 1. Tabela: financeiro_taxas

```sql
CREATE TABLE financeiro_taxas (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  percentual DECIMAL(5,2) NOT NULL,  -- Ex: 3.00 (= 3%)
  aplica_sobre TEXT DEFAULT 'receita_bruta',
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Taxas padrão:**
```sql
INSERT INTO financeiro_taxas (nome, percentual, aplica_sobre) VALUES
  ('Simples Nacional', 6.00, 'receita_bruta'),
  ('ISS', 2.00, 'receita_bruta');
```

---

### 2. Listar Taxas

**Endpoint:** `GET /api/financeiro/taxas`

```python
async def listar_taxas(self, ativo: bool = None) -> List[Dict]:
    """Lista todas as taxas"""
    query = self.supabase.table("financeiro_taxas").select("*")

    if ativo is not None:
        query = query.eq("ativo", ativo)

    response = query.order("nome", desc=False).execute()
    return response.data
```

---

### 3. Calcular Taxas Totais

```python
async def calcular_taxas_totais(self, receita_bruta: float) -> float:
    """Calcula total de taxas sobre receita bruta"""
    taxas = await self.listar_taxas(ativo=True)
    total_taxas = 0.0

    for taxa in taxas:
        if taxa['aplica_sobre'] == 'receita_bruta':
            valor_taxa = receita_bruta * (taxa['percentual'] / 100)
            total_taxas += valor_taxa

    return round(total_taxas, 2)
```

**Exemplo:**
```
Receita bruta: R$ 15,000.00
Simples Nacional (6%): R$ 900.00
ISS (2%): R$ 300.00
Total de taxas: R$ 1,200.00
```

---

## Metas

### 1. Tabela: financeiro_metas

```sql
CREATE TABLE financeiro_metas (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'lucro_liquido')),
  valor_objetivo DECIMAL(10,2) NOT NULL,
  periodo_inicio DATE NOT NULL,
  periodo_fim DATE NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2. Criar Meta

**Endpoint:** `POST /api/financeiro/metas`

**Request:**
```json
{
  "nome": "Meta Q1 2024 - Receita",
  "tipo": "receita",
  "valor_objetivo": 50000.00,
  "periodo_inicio": "2024-01-01",
  "periodo_fim": "2024-03-31"
}
```

---

### 3. Calcular Progresso

**Endpoint:** `GET /api/financeiro/metas/progresso`

```python
async def calcular_progresso_metas(self) -> List[Dict]:
    """Calcula progresso de todas as metas ativas"""
    metas = await self.listar_metas(ativo=True)
    resultado = []

    for meta in metas:
        # Período da meta
        periodo_custom = f"{meta['periodo_inicio']},{meta['periodo_fim']}"

        # Calcular valor atual
        if meta['tipo'] == 'receita':
            valor_atual = await self.get_receita_bruta(periodo_custom)
        elif meta['tipo'] == 'lucro_liquido':
            valor_atual = await self.get_lucro_liquido(periodo_custom)
        else:
            valor_atual = 0.0

        # Calcular progresso
        valor_objetivo = float(meta['valor_objetivo'])
        progresso_pct = (valor_atual / valor_objetivo * 100) if valor_objetivo > 0 else 0
        faltam = valor_objetivo - valor_atual

        resultado.append({
            **meta,
            "valor_atual": round(valor_atual, 2),
            "progresso_percentual": round(progresso_pct, 1),
            "valor_faltante": round(faltam, 2),
            "atingida": valor_atual >= valor_objetivo
        })

    return resultado
```

**Response:**
```json
{
  "metas": [
    {
      "id": 1,
      "nome": "Meta Q1 2024 - Receita",
      "tipo": "receita",
      "valor_objetivo": 50000.00,
      "periodo_inicio": "2024-01-01",
      "periodo_fim": "2024-03-31",
      "valor_atual": 35420.00,
      "progresso_percentual": 70.8,
      "valor_faltante": 14580.00,
      "atingida": false
    }
  ]
}
```

---

## Integração YouTube

### 1. Receita YouTube (Dados Reais)

**Endpoint:** `GET /api/financeiro/youtube-revenue`

```python
async def get_youtube_revenue(self, periodo: str = "30d") -> float:
    """Consulta receita YouTube do período (apenas valores reais) em BRL"""

    data_inicio, data_fim = parse_periodo(periodo)

    # Buscar taxa de câmbio
    taxa_cambio = await get_usd_brl_rate()
    taxa = taxa_cambio['taxa']

    # Buscar revenue em USD (apenas dados reais, não estimativas)
    response = self.supabase.table("yt_daily_metrics")\
        .select("revenue")\
        .eq("is_estimate", False)\
        .gte("date", data_inicio.date())\
        .lte("date", data_fim.date())\
        .execute()

    # Soma em USD
    total_usd = sum(float(item['revenue'] or 0) for item in response.data)

    # Converter para BRL
    total_brl = total_usd * taxa

    return round(total_brl, 2)
```

**Exemplo:**
```
Revenue YouTube (30 dias): $2,254.55 USD
Taxa de câmbio: R$ 5.52
Receita em BRL: R$ 12,445.12
```

---

### 2. Sincronizar Receita YouTube

**Endpoint:** `POST /api/financeiro/sync-youtube`

**Objetivo:** Criar lançamentos automáticos de receita YouTube

**Lógica:**
1. Busca revenue dos últimos 90 dias (apenas dados reais)
2. Agrupa por mês
3. Converte USD → BRL (taxa atual)
4. Cria lançamento na categoria "YouTube AdSense"
5. Evita duplicação

**Código:**
```python
async def sync_youtube_revenue(self, periodo: str = "90d") -> Dict:
    """
    Sincroniza receita YouTube criando lançamentos automáticos
    Agrupa por mês e cria um lançamento por mês (apenas valores reais)
    CONVERTE USD -> BRL usando taxa atual
    """
    data_inicio, data_fim = parse_periodo(periodo)

    # Buscar taxa de câmbio atual
    taxa_cambio = await get_usd_brl_rate()
    taxa = taxa_cambio['taxa']

    # Buscar receita YouTube por mês (apenas valores reais, em USD)
    response = self.supabase.table("yt_daily_metrics")\
        .select("date, revenue")\
        .eq("is_estimate", False)\
        .gte("date", data_inicio.date())\
        .lte("date", data_fim.date())\
        .execute()

    # Agrupar por mês (em USD)
    por_mes_usd = {}
    for item in response.data:
        data = datetime.fromisoformat(item['date'])
        mes_key = data.strftime("%Y-%m")

        if mes_key not in por_mes_usd:
            por_mes_usd[mes_key] = 0.0

        por_mes_usd[mes_key] += float(item['revenue'] or 0)

    # Converter para BRL
    por_mes = {mes: valor_usd * taxa for mes, valor_usd in por_mes_usd.items()}

    # Buscar categoria "YouTube AdSense"
    cat_response = self.supabase.table("financeiro_categorias")\
        .select("id")\
        .eq("nome", "YouTube AdSense")\
        .execute()

    if not cat_response.data:
        # Criar categoria se não existir
        cat = await self.criar_categoria("YouTube AdSense", "receita", "#00FF00", "youtube")
        categoria_id = cat['id']
    else:
        categoria_id = cat_response.data[0]['id']

    # Criar lançamentos
    criados = 0
    for mes_key, valor in por_mes.items():
        if valor <= 0:
            continue

        # Verificar se já existe lançamento para este mês
        ano, mes = mes_key.split('-')
        data_lancamento = f"{ano}-{mes}-01"
        descricao = f"Receita YouTube AdSense - {mes}/{ano}"

        existente = self.supabase.table("financeiro_lancamentos")\
            .select("id")\
            .eq("categoria_id", categoria_id)\
            .eq("data", data_lancamento)\
            .execute()

        if existente.data:
            logger.info(f"Lançamento já existe para {mes_key}")
            continue

        # Criar lançamento
        await self.criar_lancamento(
            categoria_id=categoria_id,
            valor=round(valor, 2),
            data=data_lancamento,
            descricao=descricao,
            tipo="receita",
            usuario="sistema"
        )
        criados += 1

    return {
        "sincronizados": criados,
        "periodo": periodo,
        "meses": len(por_mes),
        "taxa_cambio": taxa,
        "taxa_atualizada_em": taxa_cambio['atualizado_em']
    }
```

**Response:**
```json
{
  "sincronizados": 3,
  "periodo": "90d",
  "meses": 3,
  "taxa_cambio": 5.52,
  "taxa_atualizada_em": "2024-01-10 15:35:03"
}
```

---

### 3. Projeção do Mês

**Endpoint:** `GET /api/financeiro/projecao-mes`

```python
async def get_projecao_mes(self) -> Dict:
    """
    Calcula projeção de receita para o mês atual
    Baseado na média diária de revenue até agora
    """
    hoje = datetime.now(timezone.utc).date()

    # Primeiro e último dia do mês atual
    primeiro_dia = date(hoje.year, hoje.month, 1)
    ultimo_dia = ...  # Calcular último dia do mês

    # Dias do mês
    dias_total_mes = ultimo_dia.day
    dias_decorridos = hoje.day
    dias_restantes = dias_total_mes - dias_decorridos

    # Buscar revenue do mês até hoje (em USD)
    response = self.supabase.table("yt_daily_metrics")\
        .select("revenue")\
        .eq("is_estimate", False)\
        .gte("date", primeiro_dia)\
        .lte("date", hoje)\
        .execute()

    total_usd = sum(float(item['revenue'] or 0) for item in response.data)

    # Taxa de câmbio atual
    taxa_cambio = await get_usd_brl_rate()
    taxa = taxa_cambio['taxa']

    # Converter para BRL
    total_brl = total_usd * taxa

    # Média diária
    media_diaria = total_brl / dias_decorridos if dias_decorridos > 0 else 0

    # Projeção até fim do mês
    projecao = media_diaria * dias_total_mes

    return {
        "mes": hoje.strftime("%Y-%m"),
        "mes_nome": hoje.strftime("%B %Y"),
        "total_ate_hoje": round(total_brl, 2),
        "projecao_mes": round(projecao, 2),
        "media_diaria": round(media_diaria, 2),
        "dias_decorridos": dias_decorridos,
        "dias_restantes": dias_restantes,
        "dias_total": dias_total_mes,
        "taxa_cambio": taxa
    }
```

**Response:**
```json
{
  "mes": "2024-01",
  "mes_nome": "January 2024",
  "total_ate_hoje": 4532.00,
  "projecao_mes": 14050.20,
  "media_diaria": 453.20,
  "dias_decorridos": 10,
  "dias_restantes": 21,
  "dias_total": 31,
  "taxa_cambio": 5.52
}
```

---

## Conversão USD→BRL

### 1. Taxa de Câmbio em Tempo Real

**API:** AwesomeAPI (Brasil)

**Endpoint:** `GET /api/financeiro/taxa-cambio`

```python
async def get_usd_brl_rate() -> Dict:
    """
    Retorna taxa de câmbio USD-BRL atualizada da AwesomeAPI

    Returns:
        Dict com:
        - taxa: float (ex: 5.52)
        - atualizado_em: str (ex: "2024-01-10 15:35:03")
    """
    url = "https://economia.awesomeapi.com.br/last/USD-BRL"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                usdbrl = data.get("USDBRL", {})

                # Usa o valor "bid" (compra) como padrão
                taxa = float(usdbrl.get("bid", 5.50))
                atualizado_em = usdbrl.get("create_date", "")

                return {
                    "taxa": round(taxa, 2),
                    "atualizado_em": atualizado_em
                }

    # Fallback: taxa padrão
    return {"taxa": 5.50, "atualizado_em": "fallback"}
```

**Response AwesomeAPI:**
```json
{
  "USDBRL": {
    "code": "USD",
    "codein": "BRL",
    "name": "Dólar Americano/Real Brasileiro",
    "high": "5.5432",
    "low": "5.4987",
    "varBid": "0.0123",
    "pctChange": "0.22",
    "bid": "5.5234",
    "ask": "5.5298",
    "timestamp": "1704902103",
    "create_date": "2024-01-10 15:35:03"
  }
}
```

---

### 2. Overview Completo

**Endpoint:** `GET /api/financeiro/overview`

```python
async def get_overview(self, periodo: str = "30d") -> Dict:
    """
    Retorna overview completo do período:
    - Receita bruta (YouTube + outras receitas)
    - Despesas (total + breakdown fixas/únicas)
    - Taxas totais
    - Lucro líquido
    - Variações vs período anterior
    """

    # Período atual
    receita_bruta = await self.get_receita_bruta(periodo)
    despesas = await self.get_despesas_por_tipo(periodo)
    taxas_totais = await self.calcular_taxas_totais(receita_bruta)
    lucro_liquido = await self.get_lucro_liquido(periodo)

    # Período anterior (para comparação)
    inicio_ant, fim_ant = calcular_periodo_anterior(periodo)
    periodo_anterior = f"{inicio_ant.date()},{fim_ant.date()}"

    receita_anterior = await self.get_receita_bruta(periodo_anterior)
    despesas_anterior = await self.get_despesas_totais(periodo_anterior)
    lucro_anterior = await self.get_lucro_liquido(periodo_anterior)

    # Variações
    receita_variacao = calcular_variacao(receita_bruta, receita_anterior)
    despesas_variacao = calcular_variacao(despesas['total'], despesas_anterior)
    lucro_variacao = calcular_variacao(lucro_liquido, lucro_anterior)

    return {
        "receita_bruta": receita_bruta,
        "receita_variacao": receita_variacao,
        "despesas_totais": despesas['total'],
        "despesas_fixas": despesas['fixas'],
        "despesas_unicas": despesas['unicas'],
        "despesas_fixas_pct": despesas['fixas_pct'],
        "despesas_unicas_pct": despesas['unicas_pct'],
        "despesas_variacao": despesas_variacao,
        "taxas_totais": taxas_totais,
        "lucro_liquido": lucro_liquido,
        "lucro_variacao": lucro_variacao,
        "periodo": periodo
    }
```

**Response:**
```json
{
  "receita_bruta": 15432.50,
  "receita_variacao": 12.5,
  "despesas_totais": 4200.00,
  "despesas_fixas": 3500.00,
  "despesas_unicas": 700.00,
  "despesas_fixas_pct": 83.3,
  "despesas_unicas_pct": 16.7,
  "despesas_variacao": -5.2,
  "taxas_totais": 462.98,
  "lucro_liquido": 10769.52,
  "lucro_variacao": 18.7,
  "periodo": "30d"
}
```

---

## Cálculos Financeiros

### 1. Receita Bruta

```python
async def get_receita_bruta(self, periodo: str) -> float:
    """
    Calcula receita bruta total no período
    Combina receita YouTube (dados diários) + outras receitas manuais
    """

    # 1. Receita YouTube (dados diários de yt_daily_metrics)
    receita_youtube = await self.get_youtube_revenue(periodo)

    # 2. Outras receitas manuais (excluindo YouTube para evitar duplicação)
    data_inicio, data_fim = parse_periodo(periodo)

    response = self.supabase.table("financeiro_lancamentos")\
        .select("valor")\
        .eq("tipo", "receita")\
        .not_.like("descricao", "Receita YouTube%")\
        .gte("data", data_inicio.date())\
        .lte("data", data_fim.date())\
        .execute()

    outras_receitas = sum(float(item['valor']) for item in response.data)

    # Total = YouTube (diário) + Outras (manuais)
    total = receita_youtube + outras_receitas
    return round(total, 2)
```

---

### 2. Lucro Líquido

```python
async def get_lucro_liquido(self, periodo: str) -> float:
    """Calcula lucro líquido no período"""
    receita_bruta = await self.get_receita_bruta(periodo)
    despesas_totais = await self.get_despesas_totais(periodo)
    taxas_totais = await self.calcular_taxas_totais(receita_bruta)

    lucro = receita_bruta - despesas_totais - taxas_totais
    return round(lucro, 2)
```

**Fórmula:**
```
Lucro Líquido = Receita Bruta - Despesas - Taxas
```

---

### 3. Despesas por Tipo

```python
async def get_despesas_por_tipo(self, periodo: str) -> Dict[str, float]:
    """Calcula despesas separadas por fixas/únicas"""

    data_inicio, data_fim = parse_periodo(periodo)

    response = self.supabase.table("financeiro_lancamentos")\
        .select("valor, recorrencia")\
        .eq("tipo", "despesa")\
        .gte("data", data_inicio.date())\
        .lte("data", data_fim.date())\
        .execute()

    fixas = 0.0
    unicas = 0.0

    for item in response.data:
        valor = float(item['valor'])
        if item['recorrencia'] == 'fixa':
            fixas += valor
        else:
            unicas += valor

    total = fixas + unicas

    return {
        "fixas": round(fixas, 2),
        "unicas": round(unicas, 2),
        "total": round(total, 2),
        "fixas_pct": round((fixas / total * 100) if total > 0 else 0, 1),
        "unicas_pct": round((unicas / total * 100) if total > 0 else 0, 1)
    }
```

---

## Workflow Típico

### 1. Setup Inicial

```bash
# 1. Criar categorias
POST /api/financeiro/categorias
{
  "nome": "YouTube AdSense",
  "tipo": "receita",
  "cor": "#00FF00"
}

# 2. Criar taxas
POST /api/financeiro/taxas
{
  "nome": "Simples Nacional",
  "percentual": 6.00
}

# 3. Sincronizar receita YouTube (últimos 90 dias)
POST /api/financeiro/sync-youtube?periodo=90d
```

---

### 2. Lançamentos Manuais

```bash
# Despesa fixa mensal
POST /api/financeiro/lancamentos
{
  "categoria_id": 3,
  "valor": 89.90,
  "data": "2024-01-10",
  "descricao": "Railway - Hospedagem",
  "tipo": "despesa",
  "recorrencia": "fixa"
}

# Despesa única
POST /api/financeiro/lancamentos
{
  "categoria_id": 4,
  "valor": 450.00,
  "data": "2024-01-10",
  "descricao": "Publicidade Instagram",
  "tipo": "despesa",
  "recorrencia": "unica"
}
```

---

### 3. Monitoramento

```bash
# Overview do mês
GET /api/financeiro/overview?periodo=30d

# Projeção do mês atual
GET /api/financeiro/projecao-mes

# Progresso de metas
GET /api/financeiro/metas/progresso
```

---

**Referências:**
- Código: `D:\ContentFactory\youtube-dashboard-backend\financeiro.py`
- AwesomeAPI: https://docs.awesomeapi.com.br/api-de-moedas

---

**Última atualização:** 2024-01-12
