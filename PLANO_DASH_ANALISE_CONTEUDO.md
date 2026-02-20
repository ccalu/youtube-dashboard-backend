# Dashboard de Analise de Conteudo - Plano

## A Ideia

Um dashboard web (mesmo estilo do dash de uploads) que gera relatorios periodicos dos nossos videos que bateram metas definidas por nos. Ele cruza as metricas do banco de dados (views, likes, crescimento) com as planilhas de producao (titulo, copy/script) e usa uma LLM pra analisar o QUE fez aquele video dar certo.

**O objetivo:** Entender quais estruturas de titulo e estilos de copy funcionam melhor, por canal e por subnicho. E no futuro, sugerir novos titulos baseados nesses padroes.

---

## O Que Ja Temos Pronto

- **Banco de dados completo** - views, likes, comentarios de todos os videos, com snapshots diarios (da pra ver crescimento dia a dia)
- **43 canais monitorados** com coleta automatica
- **Google Sheets API** funcionando (acesso a qualquer planilha)
- **Infraestrutura** (Railway, Supabase, deploy automatico)
- **Dashboard de uploads como modelo** (replicamos a mesma arquitetura)

## O Que NAO Temos Ainda

- **CTR e Retencao** - precisa ativar YouTube Analytics API nos canais (re-autorizar OAuth de cada canal com novo escopo). Codigo ja existe, so precisa ativar.
- **Conexao com planilhas de copy** - precisa mapear quais planilhas, formato, e como cruzar com os videos do banco

---

## Fases

### Fase 1 - MVP: Relatorio de Performance
Usando SOMENTE dados que ja temos no banco + planilhas.

**O que entrega:**
- Dashboard web no Railway (acesso via link, qualquer um abre)
- Lista dos videos que bateram os criterios definidos (ex: +7 dias, +10k views)
- Metricas de cada video: views, likes, crescimento diario, engagement
- Titulo e copy puxados da planilha de producao
- Agrupado por canal/subnicho
- Atualiza automaticamente conforme novos videos batem as metas

**Metricas disponiveis HOJE:**
- Views totais e crescimento por dia
- Likes e comentarios
- Engagement rate (likes+comentarios / views)
- Duracao do video
- Data de publicacao + idade do video

### Fase 2 - CTR e Retencao (Analytics API)
Ativar YouTube Analytics API nos 43 canais.

**Setup necessario:**
- Adicionar escopo `yt-analytics.readonly` no OAuth (1 linha de codigo)
- Re-autorizar cada canal (rodar script, ~2min por canal)
- Coletor de analytics ja existe, so adaptar

**Metricas novas:**
- **CTR** - % de quem viu a thumb/titulo e clicou (indica se titulo funcionou)
- **Retencao media** - % do video que as pessoas assistem (indica se copy funcionou)
- **Impressoes** - quantas vezes o YouTube mostrou o video
- **Watch time** - tempo total assistido
- **Fontes de trafego** - de onde vieram as views

**Por que importa:**
- CTR alto = titulo bom (mais ligado ao titulo que a thumb)
- Retencao alta = copy boa (conteudo prendeu)

### Fase 3 - Analise LLM
LLM analisa os videos vencedores e identifica padroes.

**O que faz:**
- Analisa estrutura do titulo (formato, gatilhos, palavras-chave)
- Analisa modelo/formato da copy (narrativa, ganchos, ritmo)
- Identifica padroes por canal e subnicho
- Compara videos que deram certo vs videos que nao deram
- Gera insights tipo: "Titulos com 'Segredo' performam 2.3x melhor neste canal"

**Precisa dos fundamentos do Micha** - criterios de analise, estilos de copy, regras de titulo. Isso alimenta o prompt da LLM pra ela saber O QUE analisar.

### Fase 4 - Sugestoes de Titulos (Futuro)
LLM sugere novos titulos baseados nos padroes identificados.

- Sugestoes ranqueadas por probabilidade de sucesso
- Explicacao do racional de cada sugestao
- Botao no dash: "Gerar copy pra este titulo" → dispara agente escritor do Micha
- Fecha o loop: analise → sugestao → producao → upload → analise

---

## Decisoes do Micha

Pra comecar a Fase 1, preciso que o Micha defina:

1. **Criterios do relatorio:**
   - Quantos dias minimo desde a publicacao? (sugestao: 7-10 dias)
   - Quantas views minimas pra considerar sucesso? (sugestao: 10k)
   - Frequencia do relatorio? (a cada 7 ou 10 dias)
   - Algum outro criterio? (engagement minimo, etc.)

2. **Planilhas de producao:**
   - Formato das planilhas (colunas, abas)
   - Onde esta o titulo e a copy de cada video
   - IDs das planilhas pra acessar via API

3. **Pra Fase 3 (futuro):**
   - Como ele analisa copy/titulo hoje (criterios, fundamentos)
   - Exemplos de analises que ele ja faz manualmente
   - O que ele quer que a LLM identifique especificamente

---

## Resumo

| Fase | O que | Depende de |
|------|-------|------------|
| 1 - MVP | Relatorio com metricas + titulo/copy da planilha | Criterios do Micha + mapeamento planilhas |
| 2 - Analytics | CTR + retencao por video | Re-autorizar OAuth dos 43 canais |
| 3 - LLM | Analise de padroes de titulo e copy | Fundamentos do Micha + dados da Fase 2 |
| 4 - Sugestoes | Titulos sugeridos + botao gerar copy | Fase 3 madura + integracao com agente |

**Comecamos pela Fase 1, validamos, e vamos crescendo.**

---

*19/02/2026 - Marcelo + Micha*
