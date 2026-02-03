# Subnichos Monitorados

## Subnichos Ativos (7)

### 1. Relatos de Guerra
**Foco:** Historias pessoais de soldados, veteranos, sobreviventes.

| Idioma | Keywords |
|--------|----------|
| EN | war story, soldier story, veteran tale, combat experience, battlefield, survivor, troops, front line, military |
| PT | historia de guerra, soldado, veterano, combate, sobrevivente, tropas, front, militar |
| ES | historia de guerra, soldado, veterano, combate, sobreviviente, tropas, frente, militar |

---

### 2. Guerras e Civilizacoes
**Foco:** Historia de imperios, batalhas antigas, civilizacoes.

| Idioma | Keywords |
|--------|----------|
| EN | war, battle, empire, civilization, ancient, roman, greek, mongol, conquest, invasion, dynasty, kingdom |
| PT | guerra, batalha, imperio, civilizacao, antigo, romano, grego, mongol, conquista, invasao, dinastia |
| ES | guerra, batalla, imperio, civilizacion, antiguo, romano, griego, mongol, conquista, invasion, dinastia |

---

### 3. Empreendedorismo
**Foco:** Negocios, startups, historias de sucesso, CEOs.

| Idioma | Keywords |
|--------|----------|
| EN | entrepreneur, startup, business, success, millionaire, billionaire, ceo, founder, company, wealth |
| PT | empreendedor, startup, negocio, sucesso, milionario, bilionario, ceo, fundador, empresa, riqueza |
| ES | emprendedor, startup, negocio, exito, millonario, ceo, fundador, empresa, riqueza |

---

### 4. Terror
**Foco:** Horror, sobrenatural, historias assustadoras.

| Idioma | Keywords |
|--------|----------|
| EN | horror, scary, creepy, haunted, ghost, paranormal, demon, possessed, nightmare, terrifying |
| PT | terror, assustador, macabro, assombrado, fantasma, paranormal, demonio, possuido, pesadelo |
| ES | terror, miedo, escalofriante, embrujado, fantasma, paranormal, demonio, poseido, pesadilla |

---

### 5. Misterios
**Foco:** Casos nao resolvidos, conspiracias, enigmas.

| Idioma | Keywords |
|--------|----------|
| EN | mystery, unexplained, unsolved, strange, bizarre, conspiracy, secret, hidden, unknown, enigma |
| PT | misterio, inexplicavel, nao resolvido, estranho, bizarro, conspiracao, secreto, oculto, enigma |
| ES | misterio, inexplicable, sin resolver, extrano, bizarro, conspiracion, secreto, oculto, enigma |

---

### 6. Psicologia e Mindset
**Foco:** Comportamento humano, mente, habitos, manipulacao.

| Idioma | Keywords |
|--------|----------|
| EN | psychology, mind, brain, behavior, habit, bias, mental, cognitive, manipulation, influence |
| PT | psicologia, mente, cerebro, comportamento, habito, vies, mental, cognitivo, manipulacao |
| ES | psicologia, mente, cerebro, comportamiento, habito, sesgo, mental, cognitivo, manipulacion |

---

### 7. Historias Sombrias
**Foco:** Historia obscura, tiranos, mitologia, eventos macabros.

| Idioma | Keywords |
|--------|----------|
| EN | dark history, evil king, queen, mythology, legend, tyrant, cruel, brutal, twisted, macabre |
| PT | historia sombria, rei malvado, rainha, mitologia, lenda, tirano, cruel, brutal, macabro |
| ES | historia oscura, rey malvado, reina, mitologia, leyenda, tirano, cruel, brutal, macabro |

---

## Como Adicionar Novo Subnicho

### 1. Editar config.py

```python
SUBNICHOS = {
    # ... subnichos existentes ...

    "novo_subnicho": {
        "nome": "Nome do Subnicho",
        "ativo": True,
        "keywords": {
            "en": ["keyword1", "keyword2", "keyword3"],
            "pt": ["palavra1", "palavra2", "palavra3"],
            "es": ["palabra1", "palabra2", "palabra3"]
        }
    }
}
```

### 2. Definir Keywords Efetivas

**Boas keywords:**
- Especificas do tema
- Usadas em titulos de videos
- Termos de busca comuns

**Keywords a evitar:**
- Muito genericas ("video", "story")
- Muito especificas (nomes proprios)
- Palavras comuns ("the", "a", "is")

### 3. Testar

```bash
python main.py --mock
```

Verificar se trends estao sendo capturados na aba DIRECIONADO.

---

## Subnichos Candidatos (Inativos)

### Finance/Economia
```python
"finance": {
    "nome": "Financas",
    "ativo": False,  # Ativar quando quiser
    "keywords": {
        "en": ["economy", "market", "crash", "bank", "inflation", "recession"],
        "pt": ["economia", "mercado", "crise", "banco", "inflacao", "recessao"],
        "es": ["economia", "mercado", "crisis", "banco", "inflacion", "recesion"]
    }
}
```

### Geopolitica
```python
"geopolitics": {
    "nome": "Geopolitica",
    "ativo": False,
    "keywords": {
        "en": ["geopolitics", "china", "russia", "usa", "conflict", "nato"],
        "pt": ["geopolitica", "china", "russia", "eua", "conflito", "otan"],
        "es": ["geopolitica", "china", "rusia", "eeuu", "conflicto", "otan"]
    }
}
```

### Espaco
```python
"space": {
    "nome": "Espaco",
    "ativo": False,
    "keywords": {
        "en": ["nasa", "spacex", "mars", "moon", "asteroid", "universe"],
        "pt": ["nasa", "spacex", "marte", "lua", "asteroide", "universo"],
        "es": ["nasa", "spacex", "marte", "luna", "asteroide", "universo"]
    }
}
```

---

## Metricas por Subnicho

Apos algumas semanas de coleta, voce tera dados como:

| Subnicho | Trends/Dia | Avg Score | Evergreen |
|----------|------------|-----------|-----------|
| Terror | 15-25 | 72% | 3 |
| Misterios | 10-18 | 68% | 5 |
| Guerras | 8-15 | 75% | 7 |
| Psicologia | 12-20 | 65% | 4 |
| ... | ... | ... | ... |

Esses dados ajudam a priorizar producao.
