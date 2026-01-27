# Endpoints da API - Sistema de Comentários

## 📍 Base URL
- **Local:** `http://localhost:8000`
- **Produção:** `https://youtube-dashboard-backend-production.up.railway.app`

---

## 1️⃣ GET /api/comentarios/resumo

**Descrição:** Retorna resumo dos comentários dos canais monetizados

**Localização no código:**
- `main.py` linha 1157
- `database.py` linha 2378 (função `get_comments_summary`)

**Resposta:**
```json
{
  "canais_monetizados": 9,
  "total_comentarios": 3152,
  "novos_hoje": 45,
  "aguardando_resposta": 1854
}
```

**Filtros aplicados:**
- Apenas canais com `tipo="nosso"` e `subnicho="Monetizados"`
- Total de comentários APENAS dos monetizados
- Novos hoje APENAS dos monetizados
- Aguardando resposta APENAS dos monetizados

---

## 2️⃣ GET /api/comentarios/monetizados

**Descrição:** Lista canais monetizados com estatísticas de comentários

**Localização no código:**
- `main.py` linha 1075
- `database.py` linha 2225 (função `get_monetized_channels_with_comments`)

**Resposta:**
```json
[
  {
    "id": 835,
    "nome_canal": "그림자의 왕국",
    "total_comentarios": 355,
    "comentarios_sem_resposta": 200,
    "total_videos": 15,
    "engagement_rate": 0
  }
]
```

**Ordenação:** Por total de comentários (maior primeiro)

---

## 3️⃣ GET /api/canais/{canal_id}/videos-com-comentarios

**Descrição:** Lista vídeos de um canal com contagem de comentários

**Localização no código:**
- `main.py` linha 1092
- `database.py` linha 2268 (função `get_videos_with_comments_count`)

**Parâmetros:**
- `canal_id` (path) - ID do canal

**Resposta:**
```json
[
  {
    "video_id": "abc123",
    "titulo": "Título do Vídeo",
    "data_publicacao": "2025-01-15",
    "total_comentarios": 50,
    "comentarios_sem_resposta": 30,
    "views_atuais": 15000
  }
]
```

---

## 4️⃣ GET /api/videos/{video_id}/comentarios-paginados

**Descrição:** Retorna comentários paginados de um vídeo

**Localização no código:**
- `main.py` linha 1111
- `database.py` linha 2305 (função `get_video_comments_paginated`)

**Parâmetros:**
- `video_id` (path) - ID do vídeo
- `page` (query) - Número da página (default: 1)
- `per_page` (query) - Itens por página (default: 10, max: 50)

**Resposta:**
```json
{
  "comments": [
    {
      "id": "comment123",
      "author_name": "João Silva",
      "comment_text_original": "Great video!",
      "comment_text_pt": "Ótimo vídeo!",
      "suggested_response": "Obrigado pelo feedback!",
      "like_count": 5,
      "published_at": "2025-01-15T10:30:00",
      "is_responded": false,
      "is_translated": true
    }
  ],
  "total": 100,
  "page": 1,
  "total_pages": 10
}
```

**Ordenação:** Por likes (maior primeiro)

---

## 5️⃣ PATCH /api/comentarios/{comment_id}/marcar-respondido

**Descrição:** Marca um comentário como respondido

**Localização no código:**
- `main.py` linha 1132
- `database.py` linha 2356 (função `mark_comment_as_responded`)

**Parâmetros:**
- `comment_id` (path) - ID do comentário

**Body (opcional):**
```json
{
  "actual_response": "Resposta real enviada ao usuário"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Comentário marcado como respondido"
}
```

**Ações:**
- Define `is_responded = true`
- Define `responded_at = now()`
- Salva `actual_response` se fornecido

---

## 6️⃣ POST /api/collect-comments/{canal_id}

**Descrição:** Coleta comentários de um canal específico

**Localização no código:**
- `main.py` linha 1173

**Parâmetros:**
- `canal_id` (path) - ID do canal

**Body (opcional):**
```json
{
  "max_videos": 10,
  "max_comments_per_video": 100
}
```

**Resposta:**
```json
{
  "success": true,
  "videos_processed": 10,
  "total_comments": 250,
  "new_comments": 180,
  "duplicates": 70
}
```

**Processo:**
1. Busca últimos vídeos do canal
2. Coleta comentários de cada vídeo
3. Salva no banco (ignora duplicados)
4. Dispara tradução automática

---

## 🔒 Autenticação

Atualmente sem autenticação. Todos os endpoints são públicos.

## 📊 Limites e Performance

- Paginação máxima: 50 itens por página
- Timeout padrão: 30 segundos
- Cache: Não implementado

## 🐛 Tratamento de Erros

Todos os endpoints retornam:
```json
{
  "error": "Descrição do erro"
}
```

Códigos HTTP:
- `200` - Sucesso
- `400` - Parâmetros inválidos
- `404` - Recurso não encontrado
- `500` - Erro interno do servidor

---

**Última atualização:** 27/01/2025