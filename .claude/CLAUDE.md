# DASHBOARD DE MINERAÇÃO - Backend Python

## 📍 VOCÊ ESTÁ NO: Backend do Dashboard de Mineração
**Localização:** D:\ContentFactory\youtube-dashboard-backend
**Linguagem:** Python (FastAPI)
**Deploy:** Railway

## 🎯 O QUE ESTE BACKEND FAZ:
API REST que gerencia coleta de dados YouTube, notificações e transcrições.

## 📂 ARQUIVOS PRINCIPAIS:
- `main.py` - FastAPI app + endpoints (1122 linhas)
- `collector.py` - YouTube collector + rotação de API keys (727 linhas)
- `notifier.py` - Sistema de notificações inteligente (394 linhas)
- `database.py` - Client Supabase + queries
- `requirements.txt` - Dependências Python

## 🔗 INTEGRAÇÕES:
- **Supabase:** PostgreSQL (credenciais em .env)
- **YouTube API:** 20 keys (KEY_3 a 10 + KEY_21 a 32) - NÃO ESTÃO AQUI! (Railway)
- **Servidor M5:** https://transcription.2growai.com.br

## ⚠️ CREDENCIAIS LOCAIS (.env):
- `SUPABASE_URL` - Configurado ✅
- `SUPABASE_KEY` - Configurado ✅
- `YOUTUBE_API_KEY_X` - NÃO configuradas localmente (só Railway)

**IMPORTANTE:**
- Para testar localmente: precisa configurar pelo menos 1 YouTube API key
- Para produção: usar Railway (já tem tudo configurado)
- Arquivo .env está em .gitignore (não sobe pro GitHub)

## 🚀 RODAR LOCALMENTE:
```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Rodar servidor
python main.py
```

**Porta:** 8000 (local) ou PORT env var (Railway)

## 📊 ENDPOINTS PRINCIPAIS:

### Canais & Vídeos:
- `GET /api/canais` - Lista canais minerados (com filtros)
- `GET /api/canais-tabela` - **NOVO!** Nossos canais agrupados por subnicho (para aba Tabela)
- `GET /api/videos` - Lista vídeos (com filtros)
- `POST /api/canais` - Adiciona novo canal

### Notificações:
- `GET /api/notificacoes` - Lista notificações (com filtros)
- `POST /api/force-notifier` - Força disparo manual de notificações
- `PATCH /api/notificacoes/{id}/vista` - Marca notificação como vista
- `POST /api/notificacoes/marcar-todas-vistas` - Marca todas como vistas

### Análise:
- `GET /api/subniche-trends` - Tendências por subnicho
- `GET /api/system-stats` - Estatísticas do sistema

Ver documentação completa em: D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md

## 🔧 PARA CLAUDE CODE:
- Você pode ler/editar código Python
- Testar conexão Supabase (tem credenciais)
- NÃO pode testar coleta YouTube (faltam API keys locais)
- Pode criar novos endpoints
- Pode melhorar lógica existente
- SEMPRE fazer backup antes de mudanças grandes

## 🆕 ATUALIZAÇÕES RECENTES (02/12/2025):

### 1. Nova Feature: Aba "Tabela" (Nossos Canais)
**Endpoint:** `GET /api/canais-tabela`
- Retorna canais `tipo="nosso"` agrupados por subnicho
- Ordenação por desempenho: **melhor → menor → zero → nulo**
- Response inclui: `inscritos`, `inscritos_diff` (ganho ontem→hoje), `ultima_coleta`
- Frontend pronto: `frontend-code/TabelaCanais.tsx` (366 linhas, mobile-first)
- Documentação: `INTEGRACAO_ABA_TABELA.md`

**Lógica de Ordenação:**
- Categoria 0: Positivos (+35, +10, +2...) - Melhor no topo
- Categoria 1: Negativos (-5, -10...) - Perdas
- Categoria 2: Zero (0) - Sem mudança
- Categoria 3: Null (--) - Sem dados, sempre no final
- Tiebreaker: Maior número de inscritos

### 2. Sistema de Notificações - Bugs Corrigidos
**Arquivo:** `notifier.py`
- ✅ Query SQL otimizada (dados em uma query só)
- ✅ Filtro de subnicho case-insensitive
- ✅ Permite re-notificação para milestones maiores
- **Status:** 100% funcional (69 notificações criadas no teste)

### 3. Expansão de API Keys
**Arquivo:** `collector.py`
- ✅ Adicionadas 8 novas chaves (KEY_25 a KEY_32)
- ✅ Total: 20 chaves (antes: 12)
- ✅ Capacidade +67% (~2M requisições/dia)
- **Configuração:** Railway (variáveis de ambiente)

### 4. Arquivos de Referência Criados:
- `frontend-code/TabelaCanais.tsx` - Componente React completo
- `INTEGRACAO_ABA_TABELA.md` - Guia de integração Lovable
- `FIX_ORDENACAO_TABELA.md` - Documentação técnica do sorting
- `VALIDACAO_API_KEYS.md` - Validação das 8 novas chaves

## 🎯 INTEGRAÇÃO FUTURA:
Este backend será integrado com o Sistema Musical (D:\ContentFactory\music_queue_system)

Para documentação completa do Dashboard, consulte:
`D:\ContentFactory\.claude\DASHBOARD_MINERACAO.md`
