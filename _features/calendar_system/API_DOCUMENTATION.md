# 📡 API Documentation - Sistema de Calendário

## 🔗 Base URL

**Local:** `http://localhost:8000/api/calendar`
**Produção:** `https://youtube-dashboard-backend-production.up.railway.app/api/calendar`

## 🔑 Autenticação

Atualmente não requer autenticação (será implementado futuramente)

## 📋 Endpoints

### 1. GET /month/{year}/{month}

Retorna todos os eventos de um mês agrupados por dia.

**Parâmetros:**
- `year` (int) - Ano (ex: 2026)
- `month` (int) - Mês (1-12)
- `author` (query, opcional) - Filtrar por autor

**Response (200):**
```json
{
  "2026-02-11": [
    {
      "id": 1,
      "title": "Reunião de Planejamento",
      "description": "Discussão sobre novos canais",
      "event_date": "2026-02-11",
      "created_by": "cellibs",
      "author_name": "Cellibs",
      "author_emoji": "🎯",
      "category": "desenvolvimento",
      "category_color": "🔵",
      "event_type": "normal",
      "created_at": "2026-02-11T14:30:00Z"
    }
  ],
  "2026-02-15": [...]
}
```

---

### 2. GET /day/{date}

Retorna eventos de um dia específico.

**Parâmetros:**
- `date` (string) - Data no formato YYYY-MM-DD

**Response (200):**
```json
{
  "date": "2026-02-11",
  "day_name": "Tuesday",
  "total": 3,
  "events": [
    {
      "id": 1,
      "title": "Deploy Sistema",
      "created_by": "cellibs",
      "author_emoji": "🎯",
      "category": "desenvolvimento"
    }
  ]
}
```

**Errors:**
- `400` - Data em formato inválido

---

### 3. POST /event

Cria um novo evento.

**Request Body:**
```json
{
  "title": "Novo Canal Monetizado",
  "description": "Canal X atingiu 1000 inscritos",
  "event_date": "2026-02-11",
  "created_by": "arthur",
  "category": "geral",  // Opcional para normal, NULL para monetization
  "event_type": "monetization"  // normal | monetization | demonetization
}
```

**Validações:**
- `title`: Obrigatório, max 500 caracteres
- `event_date`: Obrigatório, formato YYYY-MM-DD
- `created_by`: Deve ser: cellibs, arthur, lucca ou joao
- `category`: Apenas para type="normal" (geral, desenvolvimento, financeiro, urgente)
- `event_type`: Aceita PT/EN (monetizacao→monetization)

**Response (201):**
```json
{
  "id": 10,
  "title": "Novo Canal Monetizado",
  "created_by": "arthur",
  "author_emoji": "📝",
  "special_indicator": "💰",
  "created_at": "2026-02-11T20:30:00Z"
}
```

**Errors:**
- `422` - Validação falhou (autor inválido, categoria inválida, etc)
- `400` - Dados mal formatados

---

### 4. GET /event/{id}

Retorna detalhes completos de um evento.

**Parâmetros:**
- `id` (int) - ID do evento

**Response (200):**
```json
{
  "id": 10,
  "title": "Reunião Financeira",
  "description": "Análise de receitas do mês",
  "event_date": "2026-02-20",
  "created_by": "joao",
  "author_name": "João",
  "author_emoji": "🎨",
  "category": "financeiro",
  "category_color": "🟣",
  "event_type": "normal",
  "is_deleted": false,
  "created_at": "2026-02-11T15:00:00Z",
  "updated_at": "2026-02-11T15:00:00Z"
}
```

**Errors:**
- `404` - Evento não encontrado
- `500` - Erro interno

---

### 5. PATCH /event/{id}

Atualiza um evento existente (atualização parcial).

**Parâmetros:**
- `id` (int) - ID do evento

**Request Body (apenas campos a atualizar):**
```json
{
  "title": "Reunião Adiada",
  "event_date": "2026-02-22"
}
```

**Response (200):**
```json
{
  "id": 10,
  "title": "Reunião Adiada",
  "event_date": "2026-02-22",
  "updated_at": "2026-02-11T21:00:00Z"
}
```

**Errors:**
- `404` - Evento não encontrado
- `400` - Validação falhou
- `422` - Dados inválidos

---

### 6. DELETE /event/{id}

Deleta um evento (soft delete - vai para lixeira por 30 dias).

**Parâmetros:**
- `id` (int) - ID do evento

**Response (200):**
```json
{
  "success": true,
  "message": "Evento movido para lixeira (30 dias)"
}
```

**Errors:**
- `404` - Evento não encontrado
- `500` - Erro ao deletar

---

### 7. POST /search

Busca avançada com múltiplos filtros.

**Request Body:**
```json
{
  "text": "reunião",  // Busca em título e descrição
  "authors": ["cellibs", "arthur"],
  "categories": ["desenvolvimento", "urgente"],
  "event_types": ["normal", "monetization"],
  "date_from": "2026-02-01",
  "date_to": "2026-02-28"
}
```

**Response (200):**
```json
{
  "total": 15,
  "search_params": {...},
  "events": [
    {
      "id": 1,
      "title": "Reunião de Desenvolvimento",
      "event_date": "2026-02-05",
      "created_by": "cellibs",
      "category": "desenvolvimento"
    }
  ]
}
```

**Notas:**
- Todos os parâmetros são opcionais
- Busca por texto é case-insensitive
- Resultados ordenados por data (mais recente primeiro)

---

### 8. GET /stats

Retorna estatísticas gerais do calendário.

**Response (200):**
```json
{
  "total_events": 156,
  "by_author": {
    "cellibs": 45,
    "arthur": 38,
    "lucca": 40,
    "joao": 33
  },
  "by_category": {
    "geral": 50,
    "desenvolvimento": 35,
    "financeiro": 20,
    "urgente": 15
  },
  "monetizations": 25,
  "demonetizations": 3,
  "recent_events": [
    {
      "id": 156,
      "title": "Evento mais recente",
      "created_at": "2026-02-11T20:00:00Z"
    }
  ],
  "socios_config": {
    "cellibs": {"name": "Cellibs", "emoji": "🎯"},
    "arthur": {"name": "Arthur", "emoji": "📝"},
    "lucca": {"name": "Lucca", "emoji": "🎬"},
    "joao": {"name": "João", "emoji": "🎨"}
  },
  "categorias_config": {
    "geral": "🟡",
    "desenvolvimento": "🔵",
    "financeiro": "🟣",
    "urgente": "🔴"
  }
}
```

## 🔍 Códigos de Status

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 400 | Bad Request - Dados inválidos |
| 404 | Não encontrado |
| 422 | Entidade não processável - Validação falhou |
| 500 | Erro interno do servidor |

## 📝 Notas de Validação

### Campos Obrigatórios
- `title` - Sempre obrigatório
- `event_date` - Sempre obrigatório
- `created_by` - Sempre obrigatório

### Valores Aceitos

**created_by:**
- cellibs
- arthur
- lucca
- joao

**category** (apenas para event_type="normal"):
- geral
- desenvolvimento
- financeiro
- urgente

**event_type:**
- normal
- monetization / monetizacao / monetização
- demonetization / desmonetizacao / desmonetização

### Regras de Negócio
1. **Monetização/Desmonetização** nunca têm categoria (sempre NULL)
2. **Soft Delete** - Eventos deletados ficam 30 dias na lixeira
3. **Tradução Automática** - Aceita PT e converte para EN
4. **Normalização** - Inputs em lowercase e sem espaços

## 🧪 Exemplos de Teste

### Criar evento normal:
```bash
curl -X POST http://localhost:8000/api/calendar/event \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Reunião Semanal",
    "event_date": "2026-02-15",
    "created_by": "cellibs",
    "category": "geral",
    "event_type": "normal"
  }'
```

### Criar monetização:
```bash
curl -X POST http://localhost:8000/api/calendar/event \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Canal Dark Stories Monetizado!",
    "event_date": "2026-02-11",
    "created_by": "lucca",
    "event_type": "monetizacao"
  }'
```

### Buscar eventos do mês:
```bash
curl http://localhost:8000/api/calendar/month/2026/2
```

### Busca avançada:
```bash
curl -X POST http://localhost:8000/api/calendar/search \
  -H "Content-Type: application/json" \
  -d '{
    "authors": ["cellibs", "arthur"],
    "date_from": "2026-02-01",
    "date_to": "2026-02-28"
  }'
```

## 📊 Performance

- **Cache:** Não implementado (considerar para futuro)
- **Índices:** Otimizados para event_date, created_by, event_type
- **Paginação:** Não implementada (eventos limitados naturalmente por mês)
- **Rate Limiting:** Não implementado

---

**Última atualização:** 11/02/2026
**Versão:** 1.0.0
**Status:** ✅ Produção