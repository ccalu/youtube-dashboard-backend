# Scripts de Análise - Sistema de Comentários

Pasta com scripts para análise e validação do sistema de comentários dos canais monetizados.

---

## 📊 Scripts Disponíveis

### 1. `check_monetizados.py`
**O que faz:** Analisa canais monetizados e estima impacto das correções

**Quando usar:**
- Verificar quantos canais monetizados existem
- Ver estatísticas atuais de comentários
- Estimar impacto de mudanças no sistema

**Como executar:**
```bash
cd D:\ContentFactory\youtube-dashboard-backend
python _development/scripts/analysis/check_monetizados.py
```

**Output esperado:**
- Lista de canais monetizados
- Comentários totais e por período
- Estimativas conservadora/realista/otimista
- Média diária/semanal/mensal

---

### 2. `validar_correcao_amanha.py`
**O que faz:** Valida se as correções implementadas funcionaram após a coleta

**Quando usar:**
- DEPOIS da coleta diária (após 05:00 AM)
- Para comparar resultado vs baseline (7 comentários/dia)
- Verificar se atingiu meta de 15-25 comentários/dia

**Como executar:**
```bash
cd D:\ContentFactory\youtube-dashboard-backend
python _development/scripts/analysis/validar_correcao_amanha.py
```

**Output esperado:**
- Comentários coletados hoje (por canal)
- Comparação com baseline
- Status: ✅ Funcionou / ⚠️ Parcial / ❌ Problema
- Tendência dos últimos 3 dias

---

## 🎯 Workflow Recomendado

### 1. ANTES das Correções (feito em 12/02/2026):
```bash
python _development/scripts/analysis/check_monetizados.py
```
- ✅ 5 canais monetizados identificados
- ✅ Baseline: 7 comentários/dia
- ✅ Estimativa: 21 comentários/dia após correção

### 2. DEPOIS da Coleta (13/02/2026 às 06:00 AM+):
```bash
python _development/scripts/analysis/validar_correcao_amanha.py
```
- Verifica se atingiu 15-25 comentários
- Compara com baseline (7/dia)
- Confirma se correção foi efetiva

### 3. Monitoramento Contínuo (próximos 7 dias):
```bash
# Executar diariamente após coleta
python _development/scripts/analysis/validar_correcao_amanha.py
```
- Confirma consistência da melhoria
- Identifica anomalias (fins de semana, feriados)
- Ajusta estimativas com dados reais

---

## 📋 Correções Implementadas (12/02/2026)

### ANTES:
- ❌ TOP 20 vídeos por VIEWS (vídeos antigos)
- ❌ ~7 comentários/dia

### DEPOIS:
- ✅ TOP 50 vídeos por DATA (vídeos recentes)
- ✅ Ordem cronológica reversa (newest first)
- ✅ Estimativa: ~21 comentários/dia (+200%)

**Arquivos modificados:**
- `collector.py` (linhas 960-975)

---

## 📈 Resultados Esperados

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Vídeos cobertos/canal | 20 | 50 | +150% |
| Comentários/dia | 7 | 21 | +200% |
| Comentários/semana | 49 | 150 | +206% |
| Comentários/mês | 212 | 643 | +203% |

---

## ⚠️ Notas Importantes

### Dependências:
- `.env` configurado (SUPABASE_URL, SUPABASE_KEY)
- Python 3.10+
- Bibliotecas: python-dotenv, supabase-py

### Encoding:
- Scripts usam `sys.stdout.reconfigure(encoding='utf-8')`
- Compatível com Windows (PowerShell/CMD)
- Funciona com nomes de canais em caracteres especiais (FR, JP, PT)

### Canais Monetizados Atuais (12/02/2026):
1. Archives de Guerre (Francês)
2. Mistérios da Realeza (Português)
3. Mistérios Arquivados (Português)
4. Archived Mysteries (Inglês)
5. 王の影 (Japonês)

---

**Última atualização:** 12/02/2026
**Autor:** Sistema automatizado via Claude Code
