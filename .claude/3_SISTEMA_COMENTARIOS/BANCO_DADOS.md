# Estrutura do Banco de Dados - Sistema de Comentários

## 📊 Tabela: `video_comments`

### Descrição
Armazena todos os comentários coletados dos vídeos do YouTube, incluindo traduções, análises de sentimento e sugestões de resposta.

### Total de Registros (Atualizado em 02/02/2026)
- **6.264** comentários total
- **6.264** dos nossos canais (100% tipo="nosso")
- **1.937** em canais monetizados
- **100%** traduzidos (is_translated=true)
- **1.860** com sugestões GPT
- **0** pendentes de tradução

## 🔧 Estrutura da Tabela

### Campos de Identificação
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | BIGINT | PK, auto-increment |
| `comment_id` | VARCHAR(255) | ID único do YouTube (UNIQUE) |
| `video_id` | VARCHAR(255) | ID do vídeo no YouTube |
| `canal_id` | BIGINT | FK para canais_monitorados |

### Campos de Conteúdo
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `video_title` | TEXT | Título do vídeo |
| `author_name` | VARCHAR(255) | Nome do autor do comentário |
| `author_channel_id` | VARCHAR(255) | ID do canal do autor |
| `comment_text_original` | TEXT | Texto original do comentário |
| `comment_text_pt` | TEXT | Tradução para português |
| `suggested_response` | TEXT | Resposta sugerida pelo GPT |
| `actual_response` | TEXT | Resposta real enviada |

### Campos de Análise
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sentiment_category` | VARCHAR(50) | Categoria do sentimento |
| `sentiment_score` | DECIMAL(3,2) | Score -1 a 1 |
| `sentiment_confidence` | DECIMAL(3,2) | Confiança 0 a 1 |
| `categories` | JSON | Array de categorias |
| `primary_category` | VARCHAR(50) | Categoria principal |
| `emotional_tone` | VARCHAR(50) | Tom emocional |
| `gpt_analysis` | JSON | Análise completa GPT |

### Campos de Priorização
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `priority_score` | DECIMAL(3,2) | Score de prioridade 0-10 |
| `urgency_level` | VARCHAR(20) | baixo/médio/alto |
| `requires_response` | BOOLEAN | Se precisa resposta |

### Campos de Engajamento
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `like_count` | INTEGER | Número de likes |
| `reply_count` | INTEGER | Número de respostas |
| `is_reply` | BOOLEAN | Se é resposta a outro |
| `parent_comment_id` | VARCHAR(255) | ID do comentário pai |

### Campos de Controle
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `is_translated` | BOOLEAN | Se foi traduzido |
| `is_reviewed` | BOOLEAN | Se foi revisado |
| `is_responded` | BOOLEAN | Se foi respondido |
| `is_resolved` | BOOLEAN | Se foi resolvido |

### Campos de Data
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `published_at` | TIMESTAMP | Data de publicação no YouTube |
| `created_at` | TIMESTAMP | Data de publicação no YouTube (auto Supabase) |
| `collected_at` | TIMESTAMP | **Data quando NÓS coletamos** (NOVO - 29/01/2026) |
| `analyzed_at` | TIMESTAMP | Data da análise |
| `reviewed_at` | TIMESTAMP | Data da revisão |
| `responded_at` | TIMESTAMP | Data da resposta |
| `resolved_at` | TIMESTAMP | Data da resolução |
| `updated_at` | TIMESTAMP | Última atualização |

> **IMPORTANTE (29/01/2026):** Campo `collected_at` adicionado para diferenciar quando o comentário foi publicado no YouTube (`published_at`) de quando foi coletado pelo nosso sistema (`collected_at`). Usado para filtro "novos hoje".

### Campos Adicionais
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `insight_summary` | TEXT | Resumo de insights |
| `actionable_items` | JSON | Itens acionáveis |
| `response_tone` | VARCHAR(50) | Tom da resposta sugerida |

## 🔑 Índices

1. **PRIMARY KEY:** `id`
2. **UNIQUE:** `comment_id`
3. **INDEX:** `video_id`
4. **INDEX:** `canal_id`
5. **INDEX:** `is_responded`
6. **INDEX:** `published_at`
7. **INDEX:** `priority_score`
8. **INDEX:** `collected_at DESC` (NOVO - 29/01/2026)

## 🔗 Relacionamentos

```
video_comments.canal_id → canais_monitorados.id
```

## 📈 Estatísticas Atuais

### Por Status
- **Traduzidos:** 5.756 (99.9%)
- **Com sugestão:** 1.854 (32%)
- **Respondidos:** 0 (0%)
- **Analisados:** ~2.000 (35%)

### Por Canal
- **Canais com comentários:** 44 de 63
- **Maior volume:** Mistérios Arquivados (1.000)
- **Canais monetizados:** 9 com 3.152 comentários

## 🔄 Triggers e Automações

### Auto-update `updated_at`
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_video_comments_updated_at
BEFORE UPDATE ON video_comments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

## 💾 Backup e Manutenção

- **Backup:** Diário via Supabase
- **Retenção:** 30 dias
- **Limpeza:** Não implementada (manter histórico)

## 🚀 Queries Principais

### Comentários dos monetizados sem resposta
```sql
SELECT * FROM video_comments
WHERE canal_id IN (
  SELECT id FROM canais_monitorados
  WHERE tipo = 'nosso'
  AND subnicho = 'Monetizados'
)
AND is_responded = false
AND suggested_response IS NOT NULL
ORDER BY priority_score DESC;
```

### Estatísticas por canal
```sql
SELECT
  canal_id,
  COUNT(*) as total,
  SUM(CASE WHEN is_responded THEN 1 ELSE 0 END) as respondidos,
  AVG(sentiment_score) as sentiment_medio
FROM video_comments
GROUP BY canal_id;
```

---

**Última atualização:** 27/01/2025
**Banco de dados:** Supabase (PostgreSQL)