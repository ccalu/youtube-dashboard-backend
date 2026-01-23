# CORREÇÕES PARA ABA ENGAJAMENTO - LOVABLE
**Data: 23/01/2025**
**Documento de Instruções de Implementação**

---

## 1️⃣ ENDPOINT CORRIGIDO - AGORA FUNCIONANDO

### ✅ O QUE FOI CORRIGIDO NO BACKEND:
O endpoint `/api/canais/{canal_id}/engagement` estava retornando 0 comentários porque buscava de uma tabela desnecessária. Agora busca **direto da tabela de comentários** e está 100% funcional.

### COMO USAR:
```javascript
// Endpoint com paginação
GET /api/canais/{canal_id}/engagement?page=1&limit=10

// Parâmetros:
// page: número da página (padrão: 1)
// limit: vídeos por página (padrão: 10)
```

### RESPOSTA DO ENDPOINT:
```json
{
  "summary": {
    "total_comments": 301,      // Total geral de comentários
    "positive_count": 35,        // Total de positivos
    "negative_count": 72,        // Total de negativos
    "positive_pct": 11.6,        // Percentual positivos
    "negative_pct": 23.9,        // Percentual negativos
    "actionable_count": 2,       // Ação necessária
    "problems_count": 2          // Problemas reportados
  },
  "videos": [
    {
      "video_id": "ygfBtqvfNBE",
      "video_title": "Título do vídeo",
      "total_comments": 37,
      "positive_count": 8,
      "negative_count": 5,
      "sentiment_score": 21.6,
      "positive_comments": [...],  // Array com comentários positivos
      "negative_comments": [...]   // Array com comentários negativos
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_videos": 23,
    "total_pages": 3
  }
}
```

### IMPORTANTE:
- ✅ **Agora retorna TODOS os vídeos que têm comentários** (23 vídeos no teste)
- ✅ **301 comentários** processados corretamente
- ✅ **Análise GPT** já está em cada comentário
- ✅ **Paginação funcionando** - dividido em páginas de 10 vídeos

---

## 2️⃣ SISTEMA DE CORES POR PERFORMANCE DOS VÍDEOS

### ADICIONAR NOS CARDS DE VÍDEO:

Baseado no número de **views** do vídeo, aplicar cor no card:

| Faixa de Views | Classificação | Cor do Card | Código Hex |
|----------------|---------------|-------------|------------|
| **20.000 ou mais** | Excelente | Verde Escuro | `#0d9488` |
| **10.000 a 19.999** | Bom | Verde | `#10b981` |
| **5.000 a 9.999** | Regular | Amarelo | `#eab308` |
| **Menos de 5.000** | Em Desenvolvimento | Laranja | `#fb923c` |

### CÓDIGO PARA IMPLEMENTAR:

```javascript
// Função para determinar a cor baseada nas views
function getPerformanceColor(views) {
  if (!views || views < 5000) return '#fb923c';  // Laranja
  if (views < 10000) return '#eab308';            // Amarelo
  if (views < 20000) return '#10b981';            // Verde
  return '#0d9488';                               // Verde Escuro
}

// Função para o label
function getPerformanceLabel(views) {
  if (!views || views < 5000) return 'Em Desenvolvimento';
  if (views < 10000) return 'Regular';
  if (views < 20000) return 'Bom';
  return 'Excelente';
}

// Aplicar no card do vídeo (exemplo):
<div
  className="video-card"
  style={{ borderLeftColor: getPerformanceColor(video.views) }}
>
  <span className="performance-badge">
    {getPerformanceLabel(video.views)}
  </span>
  {/* resto do conteúdo do card */}
</div>
```

### ONDE APLICAR:
- Na lista de vídeos da aba Engajamento
- Adicionar uma borda colorida ou badge indicando o nível
- Mostrar o label (Excelente, Bom, Regular, Em Desenvolvimento)

---

## 3️⃣ REMOVER ABA "PADRÕES"

### AÇÃO NECESSÁRIA:
Remover completamente a aba "Padrões" do dashboard.

```javascript
// ANTES (procurar no código)
const tabs = ['Canais', 'Vídeos', 'Notificações', 'Padrões', 'Engajamento'];

// DEPOIS (alterar para)
const tabs = ['Canais', 'Vídeos', 'Notificações', 'Engajamento'];
```

Remover também:
- Componente da aba Padrões
- Rota/navegação para essa aba
- Qualquer referência a "Padrões" no código

---

## 📋 CHECKLIST SIMPLES

- [ ] Atualizar chamada do endpoint engagement com paginação
- [ ] Adicionar sistema de cores nos cards de vídeo baseado em views
- [ ] Adicionar label de performance (Excelente/Bom/Regular/Em Desenvolvimento)
- [ ] Remover aba "Padrões" completamente
- [ ] Testar com canal ID 835 (tem 301 comentários)

---

## ⚠️ OBSERVAÇÕES FINAIS

1. **NÃO ALTERAR** o layout existente da aba Engajamento - apenas adicionar as cores
2. **O endpoint já está funcionando** - só precisa usar com paginação
3. **Campo views** pode não existir em alguns vídeos - tratar como 0
4. **Manter todo o resto** como está funcionando atualmente

---

**FIM DO DOCUMENTO**