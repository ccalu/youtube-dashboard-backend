# API Reference - Sistema Kanban

## Base URL
```
Local: http://localhost:8000
Railway: https://youtube-dashboard-backend-production.up.railway.app
```

## Endpoints

### 1. Estrutura Principal

#### GET `/api/kanban/structure`
Retorna a estrutura completa do Kanban com cards, subnichos e canais.

**Response:**
```json
{
  "monetizados": {
    "total": 9,
    "subnichos": {
      "Terror": {
        "nome": "Terror",
        "total": 3,
        "canais": [
          {
            "id": 1,
            "nome": "Dark Terror BR",
            "subnicho": "Terror",
            "lingua": "portuguese",
            "kanban_status": "em_crescimento",
            "status_label": "Em Crescimento",
            "status_color": "green",
            "dias_no_status": 15,
            "total_notas": 3
          }
        ]
      }
    }
  },
  "nao_monetizados": {
    "total": 54,
    "subnichos": {...}
  }
}
```

### 2. Kanban Individual

#### GET `/api/kanban/canal/{canal_id}/board`
Retorna o quadro Kanban individual de um canal.

**Parameters:**
- `canal_id` (path): ID do canal

**Response:**
```json
{
  "canal": {
    "id": 1,
    "nome": "Dark Terror BR",
    "subnicho": "Terror",
    "monetizado": false,
    "status_atual": "em_teste_inicial",
    "status_since": "2025-01-28T12:00:00Z",
    "dias_no_status": 0
  },
  "colunas": [
    {
      "id": "em_teste_inicial",
      "label": "Em Teste Inicial",
      "emoji": "🟡",
      "descricao": "Canal testando micro-nichos pela primeira vez",
      "is_current": true
    }
  ],
  "notas": [
    {
      "id": 1,
      "canal_id": 1,
      "note_text": "Testando micro-nicho Bizâncio",
      "note_color": "yellow",
      "position": 1,
      "created_at": "2025-01-28T14:35:00Z"
    }
  ],
  "historico": []
}
```

### 3. Mudança de Status

#### PATCH `/api/kanban/canal/{canal_id}/move-status`
Move um canal para outro status no Kanban.

**Request Body:**
```json
{
  "new_status": "demonstrando_tracao"
}
```

**Status Válidos:**

Para **Não Monetizados:**
- `em_teste_inicial`
- `demonstrando_tracao`
- `em_andamento`
- `monetizado`

Para **Monetizados:**
- `em_crescimento`
- `em_testes_novos`
- `canal_constante`

**Response:**
```json
{
  "success": true,
  "message": "Status atualizado com sucesso"
}
```

### 4. Gestão de Notas

#### POST `/api/kanban/canal/{canal_id}/note`
Cria uma nova nota para o canal.

**Request Body:**
```json
{
  "note_text": "Testando micro-nicho de Império Bizantino",
  "note_color": "yellow",
  "coluna_id": "em_teste_inicial"  // opcional - define coluna específica
}
```

**Cores Válidas:**
- `yellow` (padrão)
- `green`
- `blue`
- `purple`
- `red`
- `orange`

**Response:**
```json
{
  "id": 1,
  "canal_id": 1,
  "note_text": "Testando micro-nicho de Império Bizantino",
  "note_color": "yellow",
  "position": 1,
  "created_at": "2025-01-28T14:35:00Z"
}
```

#### PATCH `/api/kanban/note/{note_id}`
Atualiza uma nota existente.

**Request Body:**
```json
{
  "note_text": "Texto atualizado",
  "note_color": "green"
}
```

#### DELETE `/api/kanban/note/{note_id}`
Deleta uma nota.

**Response:**
```json
{
  "success": true,
  "message": "Nota deletada com sucesso"
}
```

#### PATCH `/api/kanban/note/{note_id}/move`
Move uma nota para outra coluna (drag & drop entre colunas).

**Request Body:**
```json
{
  "stage_id": "demonstrando_tracao"  // ou "coluna_id" - aceita ambos
}
```

**Response:**
```json
{
  "success": true,
  "message": "Nota movida com sucesso",
  "data": {
    "id": 1,
    "canal_id": 1,
    "note_text": "Texto da nota",
    "note_color": "yellow",
    "coluna_id": "demonstrando_tracao",
    "position": 1
  }
}
```

#### PATCH `/api/kanban/canal/{canal_id}/reorder-notes`
Reordena as notas de um canal (drag & drop).

**Request Body:**
```json
{
  "note_positions": [
    {"note_id": 3, "position": 1},
    {"note_id": 1, "position": 2},
    {"note_id": 2, "position": 3}
  ]
}
```

### 5. Histórico

#### GET `/api/kanban/canal/{canal_id}/history`
Retorna o histórico de ações do canal.

**Query Parameters:**
- `limit` (opcional): Número máximo de registros (1-100, padrão: 50)

**Response:**
```json
[
  {
    "id": 1,
    "canal_id": 1,
    "action_type": "status_change",
    "description": "Status mudou de em_teste_inicial para demonstrando_tracao",
    "details": {
      "from_status": "em_teste_inicial",
      "to_status": "demonstrando_tracao"
    },
    "performed_at": "2025-01-28T15:00:00Z",
    "is_deleted": false
  }
]
```

#### DELETE `/api/kanban/history/{history_id}`
Remove um item do histórico (soft delete).

**Response:**
```json
{
  "success": true,
  "message": "Item removido do histórico"
}
```

## Tipos de Ação no Histórico

- `status_change` - Mudança de status do canal
- `note_added` - Nota adicionada
- `note_edited` - Nota editada
- `note_deleted` - Nota removida
- `note_moved` - Nota movida entre colunas
- `note_reordered` - Notas reordenadas
- `canal_created` - Canal criado no sistema

## Códigos de Erro

- `404` - Canal, nota ou item não encontrado
- `400` - Dados inválidos na requisição
- `500` - Erro interno do servidor

## Exemplos de Uso

### Buscar estrutura completa:
```bash
curl http://localhost:8000/api/kanban/structure
```

### Mover canal para novo status:
```bash
curl -X PATCH http://localhost:8000/api/kanban/canal/1/move-status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "demonstrando_tracao"}'
```

### Criar nova nota:
```bash
curl -X POST http://localhost:8000/api/kanban/canal/1/note \
  -H "Content-Type: application/json" \
  -d '{"note_text": "Teste de micro-nicho", "note_color": "green"}'
```

## Observações

- Todos os endpoints filtram automaticamente por `tipo="nosso"`
- Timestamps são sempre em UTC com timezone
- Soft delete é usado no histórico (registros não são fisicamente removidos)
- Drag & drop de notas requer enviar todas as posições atualizadas