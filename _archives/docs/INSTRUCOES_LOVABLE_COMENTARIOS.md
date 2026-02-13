# INSTRUCOES PARA ATUALIZAR LOVABLE - ABA COMENTARIOS

## CONTEXTO (Atualizado 13/02/2026)

Coleta historica COMPLETA e traducao 100% FINALIZADA para todos os 43 canais.

**Numeros atuais:**
- 15.074 comentarios totais no banco
- 43 canais tipo="nosso" com comentarios coletados
- 100% traduzidos para portugues (15.074/15.074)
- Coleta historica de TODOS os videos de TODOS os canais (sem limite)
- Novo endpoint de geracao de resposta por GPT on-demand

## MUDANCAS NO BACKEND (13/02/2026)

1. **Coleta historica completa**: TODOS os videos de TODOS os 43 canais coletados (antes era top 20)
2. **Traducao 100%**: Todos os 15.074 comentarios traduzidos para PT-BR via GPT-4o-mini
3. **Canais PT**: 12 canais em portugues tem texto original copiado (sem traduzir por GPT)
4. **Novo endpoint**: `POST /api/comentarios/{id}/gerar-resposta` - gera resposta por GPT on-demand
5. **Campo collected_at**: Diferencia data de publicacao no YouTube vs data de coleta no banco

## ENDPOINTS DISPONIVEIS (6 TOTAL)

### 1. Resumo Geral
```
GET /api/comentarios/resumo
```
Retorna:
```json
{
  "total_comentarios": 15074,
  "novos_hoje": 42,
  "aguardando_resposta": 14500,
  "respondidos": 0
}
```

### 2. Lista de Canais com Comentarios
```
GET /api/comentarios/monetizados
```
Retorna TODOS os 43 canais (nao so monetizados). Agrupavel por subnicho.
```json
{
  "canais": [
    {
      "id": 891,
      "nome_canal": "Grandes Mansoes",
      "subnicho": "Monetizados",
      "lingua": "portuguese",
      "url_canal": "https://youtube.com/@...",
      "total_comentarios": 327,
      "total_videos": 19,
      "comentarios_pendentes": 11,
      "ultimo_comentario": "2026-02-13T10:30:00+00:00"
    }
  ]
}
```

### 3. Videos de um Canal com Comentarios
```
GET /api/canais/{canal_id}/videos-com-comentarios
```
Retorna TOP 10 videos por quantidade de comentarios.
```json
{
  "videos": [
    {
      "video_id": "abc123",
      "titulo": "Titulo do Video",
      "views": 12500,
      "data_publicacao": "2025-12-15T00:00:00Z",
      "total_comentarios": 45,
      "comentarios_sem_resposta": 12,
      "thumbnail": "https://i.ytimg.com/vi/abc123/mqdefault.jpg"
    }
  ]
}
```

### 4. Comentarios Paginados de um Video
```
GET /api/videos/{video_id}/comentarios-paginados?page=1&limit=10
```
Retorna comentarios com traducao e info do autor.
```json
{
  "comments": [
    {
      "id": 123,
      "comment_id": "xyz",
      "author_name": "Joao",
      "comment_text": "Texto em portugues (traduzido)",
      "comment_text_original": "Original text in English",
      "comment_text_pt": "Texto em portugues (traduzido)",
      "is_translated": true,
      "like_count": 5,
      "suggested_response": "Resposta sugerida por GPT (se existir)",
      "is_responded": false,
      "published_at": "2025-12-27T20:23:37Z",
      "collected_at": "2026-01-21T15:59:27Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 283,
    "total_pages": 29
  }
}
```

### 5. Gerar Resposta por GPT (NOVO!)
```
POST /api/comentarios/{comment_id}/gerar-resposta
```
Gera resposta inteligente via GPT-4o-mini no idioma original do comentario.
```json
{
  "success": true,
  "response": "Thanks for your comment! That's a great observation about...",
  "response_generated_at": "2026-02-13T15:30:00+00:00"
}
```

### 6. Marcar como Respondido
```
PATCH /api/comentarios/{comment_id}/marcar-respondido
```
Body: `{ "actual_response": "Resposta que foi enviada" }`

## O QUE FAZER NO LOVABLE

### Nenhuma mudanca na URL da API necessaria!
O endpoint `/api/comentarios/monetizados` ja retorna TODOS os 43 canais automaticamente.

### Sugestoes de melhorias visuais:

#### 1. Cards de Resumo (topo da pagina)
Usar dados de `/api/comentarios/resumo`:
- Total de Comentarios: 15.074
- Novos Hoje: X
- Aguardando Resposta: Y
- Respondidos: Z

#### 2. Agrupar Canais por Subnicho
```typescript
// Agrupar canais por subnicho (igual a aba Tabela)
const canaisPorSubnicho = canais.reduce((acc, canal) => {
  if (!acc[canal.subnicho]) {
    acc[canal.subnicho] = [];
  }
  acc[canal.subnicho].push(canal);
  return acc;
}, {} as Record<string, typeof canais>);
```

#### 3. Cores dos Subnichos (mesmas da aba Tabela)
```typescript
const SUBNICHE_COLORS: Record<string, string> = {
  'Monetizados': '#10B981',
  'Desmonetizados': '#EF4444',
  'Relatos de Guerra': '#059669',
  'Historias Sombrias': '#7C3AED',
  'Terror': '#DC2626',
};
```

#### 4. Botao "Gerar Resposta" nos Comentarios
Quando usuario clica num comentario:
```typescript
// Gerar resposta por GPT
const gerarResposta = async (commentId: number) => {
  const response = await fetch(
    `${API_URL}/api/comentarios/${commentId}/gerar-resposta`,
    { method: 'POST' }
  );
  const data = await response.json();
  // data.response contem a resposta gerada
};
```

#### 5. Mostrar Traducao + Original
Cada comentario tem:
- `comment_text_pt` - Traducao em portugues (SEMPRE disponivel, 100%)
- `comment_text_original` - Texto original no idioma do autor
- Toggle para ver original vs traduzido

#### 6. Marcar como Respondido
```typescript
const marcarRespondido = async (commentId: number, resposta: string) => {
  await fetch(
    `${API_URL}/api/comentarios/${commentId}/marcar-respondido`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actual_response: resposta })
    }
  );
};
```

## FLUXO DO USUARIO

1. Abre aba Comentarios -> ve resumo geral (4 cards)
2. Ve lista de canais agrupados por subnicho
3. Clica num canal -> ve TOP 10 videos com mais comentarios
4. Clica num video -> ve comentarios paginados (10 por pagina)
5. Cada comentario mostra: autor, texto traduzido, likes, data
6. Botao "Gerar Resposta" -> GPT sugere resposta no idioma do comentario
7. Botao "Marcar Respondido" -> salva resposta enviada

## TESTE RAPIDO

1. Acesse a aba Comentarios
2. Deve mostrar TODOS os 43 canais (nao so 2)
3. Canais agrupados por subnicho
4. Total deve mostrar ~15.074 comentarios
5. Todos comentarios devem ter traducao em PT
6. Botao de gerar resposta deve funcionar

## CAMPOS IMPORTANTES DO COMENTARIO

| Campo | Tipo | Descricao |
|-------|------|-----------|
| comment_text_pt | string | Texto traduzido PT-BR (100% preenchido) |
| comment_text_original | string | Texto no idioma original |
| is_translated | boolean | Sempre true (100% traduzido) |
| is_responded | boolean | Se ja foi respondido |
| suggested_response | string/null | Resposta sugerida por GPT |
| actual_response | string/null | Resposta real enviada |
| like_count | number | Curtidas no comentario |
| published_at | datetime | Quando publicado no YouTube |
| collected_at | datetime | Quando coletado pelo sistema |
| author_name | string | Nome do autor |

---

**Atualizado em:** 13/02/2026
**Por:** Claude Code para Cellibs
**Status:** Backend 100% pronto - Coleta historica completa + Traducao 100% finalizada
