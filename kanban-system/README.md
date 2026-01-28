# Sistema Kanban - Dashboard de Mineração YouTube

## 📊 Visão Geral

Sistema de Kanban para gerenciar o status e estratégias dos **63 canais próprios** (tipo="nosso") do projeto Dark YouTube Channels. Permite organizar canais por status, documentar decisões e acompanhar a evolução de cada canal.

## 🎯 Objetivo

Resolver o problema de falta de visibilidade sobre o status de cada canal em uma operação com 50+ canais em 8 idiomas, criando um sistema visual para:
- Ver o status atual de cada canal
- Documentar estratégias e testes
- Acompanhar evolução temporal
- Facilitar tomada de decisões

## 📁 Estrutura do Projeto

```
kanban-system/
├── database/          # Scripts SQL para Supabase
├── backend/           # Código Python para API
├── frontend/          # Componentes React para Lovable
├── docs/              # Documentação adicional
└── examples/          # Exemplos de uso
```

## 🚀 Status do Canal

### Para Canais NÃO Monetizados:
- 🟡 **Em Teste Inicial** - Canal testando micro-nichos pela primeira vez
- 🟢 **Demonstrando Tração** - Sinais positivos, vídeos viralizando
- 🟠 **Em Andamento p/ Monetizar** - Caminhando para 1K subs e 4K horas
- 🔵 **Monetizado** - Atingiu requisitos de monetização

### Para Canais Monetizados:
- 🟢 **Em Crescimento** - Canal saudável e escalando
- 🟡 **Em Testes Novos** - Perdeu tração, testando novas estratégias
- 🔵 **Canal Constante** - Estável, performance previsível

## 💾 Banco de Dados

### Tabelas Criadas:
1. **Campos em `canais_monitorados`:**
   - `kanban_status` - Status atual do canal
   - `kanban_status_since` - Desde quando está no status

2. **`kanban_notes`** - Notas e documentação de estratégias
   - Suporta múltiplas cores para organização
   - Permite reordenação (drag & drop)

3. **`kanban_history`** - Histórico de todas as ações
   - Soft delete (pode remover itens)
   - Registra mudanças de status e notas

## 🔌 API Endpoints

### Estrutura Principal
- `GET /api/kanban/structure` - Retorna cards, subnichos e canais

### Kanban Individual
- `GET /api/kanban/canal/{id}/board` - Dados do kanban do canal
- `PATCH /api/kanban/canal/{id}/move-status` - Mudar status

### Notas
- `POST /api/kanban/canal/{id}/note` - Criar nota
- `PATCH /api/kanban/note/{id}` - Editar nota
- `DELETE /api/kanban/note/{id}` - Deletar nota
- `PATCH /api/kanban/canal/{id}/reorder-notes` - Reordenar

### Histórico
- `GET /api/kanban/canal/{id}/history` - Ver histórico
- `DELETE /api/kanban/history/{id}` - Remover item do histórico

## 🎨 Frontend (Lovable)

### Localização:
- Nova aba "**Kanban**" em **Ferramentas** (abaixo de "Histórico de Coletas")

### Layout:
1. **Dois cards principais:** Monetizados e Não Monetizados (com contadores)
2. **Expansível por subnicho:** Clique expande mostrando subnichos
3. **Lista de canais:** Mesmo layout da aba Tabela com tags de status
4. **Kanban individual:** Modal com colunas, notas e histórico

## 📦 Instalação

### 1. Banco de Dados (Supabase):
```sql
-- Execute na ordem:
1. database/01_add_columns.sql
2. database/02_create_tables.sql
3. database/03_test_data.sql (opcional)
```

### 2. Backend (Python):
```python
# Adicione o código de backend/kanban_endpoints.py ao main.py
# Importe as funções necessárias
```

### 3. Frontend (Lovable):
```jsx
// Copie os componentes de frontend/ para o Lovable
// Siga o guia em docs/LOVABLE_INTEGRATION.md
```

## 🧪 Testes

```bash
# Testar estrutura
curl http://localhost:8000/api/kanban/structure

# Testar kanban individual
curl http://localhost:8000/api/kanban/canal/1/board

# Mudar status
curl -X PATCH http://localhost:8000/api/kanban/canal/1/move-status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "demonstrando_tracao"}'
```

## 📝 Notas Importantes

- Sistema exclusivo para canais **tipo="nosso"** (63 canais)
- Não inclui canais minerados de referência
- Sem campos de autor (ferramenta específica do Micha)
- Histórico com soft delete (pode remover registros)
- Preparado para futuros alertas (dados timestamped)

## 🔄 Próximos Passos

1. ✅ Backend 100% implementado e testado
2. ⏳ Implementar frontend no Lovable
3. 🔜 Sistema de alertas configuráveis (futuro)

## 📞 Suporte

- **Cellibs:** Implementação e manutenção
- **Micha:** Usuário principal do sistema
- **Arthur:** Feedback e melhorias

---

**Última atualização:** 28/01/2025
**Versão:** 1.0.0