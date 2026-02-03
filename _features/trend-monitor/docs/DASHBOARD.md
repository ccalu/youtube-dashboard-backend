# Como Usar o Dashboard

## Visao Geral

O dashboard HTML tem 4 abas principais:

```
[ GERAL ] [ DIRECIONADO ] [ RELATORIO ] [ HISTORICO ]
```

---

## ABA GERAL

### O que mostra
**TODOS os trends coletados**, sem filtro de subnicho.

### Organizacao
- Agrupado por **FONTE** (Google Trends, YouTube, Reddit, Hacker News)
- Dentro de cada fonte, agrupado por **PAIS**
- Ordenado por **volume/popularidade**

### Uso
- Visao ampla do que esta em alta globalmente
- Descobrir trends fora dos seus subnichos
- Identificar oportunidades de novos canais

### Exemplo
```
GOOGLE TRENDS
├── US (50 trends)
│   ├── #1 "Super Bowl 2025" - 2.5M buscas
│   ├── #2 "iPhone 17 release" - 1.8M buscas
│   └── ...
├── BR (50 trends)
│   ├── #1 "Carnaval 2025" - 890K buscas
│   └── ...
└── ...

YOUTUBE
├── US (50 videos)
│   ├── #1 "MrBeast New Video" - 45M views
│   └── ...
└── ...
```

---

## ABA DIRECIONADO

### O que mostra
**APENAS trends que matcham seus subnichos**.

### Organizacao
- Agrupado por **SUBNICHO** (Terror, Misterios, etc)
- Cada trend tem **score de relevancia** (0-100)
- Ordenado por score (mais relevantes primeiro)

### Score de Relevancia
```
0-40:   Baixa relevancia (match parcial)
41-70:  Media relevancia (bom match)
71-100: Alta relevancia (match forte) ⭐
```

### Como o score e calculado
- +20 pontos: cada keyword do subnicho encontrada
- +15 pontos: aparece em multiplos paises
- +10 pontos: aparece em multiplas fontes

### Uso
- Encontrar trends relevantes para seus canais
- Priorizar producao de conteudo
- Ver quais subnichos tem mais oportunidades

### Exemplo
```
TERROR (23 trends)
├── "Haunted house documentary" - Score: 95% ⭐
│   └── Fontes: Google, YouTube, Reddit
├── "Demonic possession real footage" - Score: 88%
│   └── Fontes: YouTube, Reddit
└── ...

MISTERIOS (18 trends)
├── "Unsolved disappearances 2025" - Score: 92% ⭐
└── ...
```

---

## ABA RELATORIO

### O que mostra
**Resumo executivo** com insights acionaveis.

### Secoes

1. **Resumo do Dia**
   - Total de trends coletados
   - Trends relevantes encontrados
   - Fontes consultadas
   - Paises monitorados

2. **Top Oportunidades**
   - 10 trends com maior potencial
   - Ordenados por score + volume

3. **Trends Evergreen**
   - Trends que aparecem ha 7+ dias
   - Indicam interesse sustentado
   - Otimos para conteudo "atemporal"

4. **Alertas**
   - Trends virais (volume muito alto)
   - Cross-platform (aparecem em 3+ fontes)
   - Novos no radar (primeira vez detectados)

### Uso
- Visao rapida diaria
- Decisao de pauta
- Identificar urgencias

---

## ABA HISTORICO

### O que mostra
**Calendario dos ultimos 30 dias** com dados coletados.

### Funcionalidades
- Clique em um dia para ver trends daquela data
- Comparativo semana atual vs anterior
- Evolucao de trends ao longo do tempo

### Trends Persistentes
Lista de trends que aparecem em multiplos dias:
- 3-6 dias: "Crescente"
- 7+ dias: "EVERGREEN" (oportunidade!)

### Uso
- Analisar tendencias ao longo do tempo
- Identificar padroes sazonais
- Validar se um trend e passageiro ou duradouro

---

## Filtros Disponiveis

### Filtro por Fonte
Dropdown no topo do dashboard:
- Todas as fontes
- Google Trends
- YouTube
- Reddit
- Hacker News

### Filtro por Pais
Dropdown para selecionar:
- Todos os paises
- US, BR, ES, MX, FR, JP, KR

### Busca
Campo de texto para buscar trends especificos.

---

## Dicas de Uso

### Rotina Diaria Recomendada
1. Abrir **ABA RELATORIO** primeiro
2. Ver "Top Oportunidades" e "Alertas"
3. Se algo interessante, ir para **ABA DIRECIONADO**
4. Verificar score e decidir producao

### Identificar Oportunidades
- Score 80+: Produzir nos proximos 2-3 dias
- Evergreen: Pode produzir a qualquer momento
- Cross-platform: Alta chance de viralizar

### Evitar Armadilhas
- Score baixo (<50): Pode nao ter audiencia
- Trend de 1 dia: Pode ser passageiro
- Muito nichado: Verificar volume real

---

## Atualizacao

O dashboard e gerado:
- **Automaticamente**: Se configurado cron job
- **Manualmente**: `python main.py`

Horario recomendado: 6h UTC (3h Brasilia)
- Dados frescos do dia anterior
- Tempo para planejar producao
