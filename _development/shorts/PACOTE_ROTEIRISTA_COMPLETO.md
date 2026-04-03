# Pacote Completo — Otimização do Roteirista de Shorts

> **Objetivo**: Melhorar a qualidade dos scripts gerados automaticamente por IA.
> **Entrega**: Me devolve o arquivo `scriptwriter.py` com o prompt otimizado. Eu substituo e pronto.

---

## PARTE 1 — Como Funciona

### Fluxo Simplificado
```
[Usuário escolhe]  tema + canal + subnicho + língua
         ↓
[Claude Opus IA]   recebe o PROMPT → gera título + descrição + script
         ↓
[ElevenLabs TTS]   narra o script em voz (por isso números têm que ser por extenso)
         ↓
[Freepik IA]       gera 14 imagens + 14 vídeos animados baseados no script
         ↓
[Remotion]         monta: vídeo + narração + legendas word-by-word com highlight
         ↓
[Output]           YouTube Short pronto (~60-90 segundos)
```

### O que o script gera
- **14 parágrafos** = 14 cenas visuais (cada parágrafo = 1 cena de ~6s com imagem/vídeo)
- **Título** = o que aparece no YouTube (max 60 chars, tem que fazer clicar)
- **Descrição** = texto + hashtags do YouTube
- **Duração alvo**: ~60-90s de narração (max ~800 caracteres de script)

### Importante
- Cada parágrafo do script vira uma cena visual separada com imagem cinematográfica
- O Diretor de Cinema (outra IA) lê cada parágrafo e cria a imagem/vídeo correspondente
- Então cada parágrafo precisa ter potencial visual claro e ser um "momento" da história

---

## PARTE 2 — Problemas Atuais (O Que Precisa Melhorar)

### Exemplo do primeiro vídeo gerado (Crônicas da Coroa — Reis Perversos):

```
Henrique VIII mandou decapitar duas esposas — e uma delas ensaiou a própria
execução na noite anterior.

Ele casou 6 vezes. Divorciou 2, decapitou 2, uma morreu no parto e uma sobreviveu.

Ana Bolena foi a segunda esposa. Deu a ele uma filha, não um herdeiro homem.

Isso bastou. Henrique a acusou de traição, bruxaria e adultério com 5 homens —
incluindo o próprio irmão dela.

O julgamento durou 3 dias. Todos os acusados foram condenados sem provas concretas.

Em 19 de maio de 1536, Ana caminhou até o cadafalso na Torre de Londres.

Ela pediu um espadachim francês em vez de machado. Henrique concedeu — como um "favor".

Um único golpe. A cabeça caiu. Ninguém tinha preparado um caixão.

O corpo foi enfiado numa caixa de flechas e enterrado sem cerimônia.

11 dias depois, Henrique já estava casado com Jane Seymour.

Catarina Howard, a quinta esposa, tinha apenas 17 anos quando casou com ele.

Quando Henrique descobriu que ela teve casos antes do casamento, trancou-a nos aposentos.

Na noite de 12 de fevereiro de 1542, Catarina pediu o bloco de execução para
ensaiar — para morrer com dignidade.

Se essa história te chocou, comenta qual rei cruel você quer ver no próximo vídeo.
```

### O que deu errado:
1. **Informativo demais** — parecia artigo da Wikipedia, não YouTube Short
2. **Sem arco narrativo** — fatos jogados sem conexão emocional
3. **Sem tensão crescente** — não dava vontade de continuar assistindo
4. **Hook fraco** — resumiu o vídeo inteiro na primeira frase (zero mistério)
5. **Muita informação** — confuso, difícil de acompanhar em 90 segundos
6. **Sem história coesa** — pulou de Ana Bolena pra Catarina Howard sem transição
7. **Números não por extenso** — "6 vezes", "5 homens", "1536" (TTS lê errado)

### O que deveria ter:
- Hook que cria **MISTÉRIO** (não resume tudo logo de cara)
- **Arco narrativo**: início → tensão crescente → clímax → resolução
- Cada frase faz o espectador **querer ouvir a próxima**
- **Menos fatos, mais emoção** e storytelling
- História **coesa** do início ao fim — tem que fazer sentido como narrativa
- Se o espectador pode parar a qualquer momento sem curiosidade, **o script falhou**

---

## PARTE 3 — O Arquivo Para Editar

### `scriptwriter.py` (código completo atual)

```python
"""
Roteirista de Shorts — gera título, descrição, script e estimativa de cenas.

Usa Claude CLI (plano Max) para gerar o script completo.
Output: JSON com titulo, descricao, script, estrutura, total_cenas.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um roteirista de YouTube Shorts. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicação."""


def write_script(topic: str, canal: str, subnicho: str, lingua: str, subnicho_desc: str = "", titulos_ref: str = "") -> dict:
    """
    Gera script completo para um YouTube Short.

    Args:
        topic: Tema do Short
        canal: Nome do canal
        subnicho: Nome do subnicho
        lingua: Língua do canal (ex: "Português", "Inglês")
        subnicho_desc: Descrição do subnicho (do SUBNICHOS.md)
        titulos_ref: Títulos de referência do canal

    Returns:
        Dict com titulo, descricao, script, estrutura, total_cenas
    """
    user_prompt = f"""Crie um script de YouTube Short completo.

Canal: {canal} | Subnicho: {subnicho} | Língua: {lingua} | Tema: {topic}

Contexto: {subnicho_desc}

REGRAS:
- Script na língua "{lingua}". Título e descrição também em "{lingua}".
- Hook matador na primeira frase (fato chocante que cria MISTÉRIO — nunca resuma o vídeo no hook)
- Arco narrativo OBRIGATÓRIO: setup → tensão crescente → clímax → resolução
- Cada frase deve criar curiosidade pra PRÓXIMA — se o espectador pode parar sem querer saber mais, o script falhou
- Priorizar STORYTELLING sobre dados/fatos — conte uma HISTÓRIA, não uma lista de informações
- Menos texto, mais impacto. Cada palavra tem que merecer estar ali
- Pattern interrupts a cada 10-15s
- Máximo ~800 caracteres de script (~80s narração)
- 14 parágrafos = 14 cenas visuais
- Título: max 60 chars, curiosidade extrema
- Descrição: 1-2 frases + 5 hashtags
- CTA variado no final (inscrição, like, comentário — variar)
- NUNCA editorialize, só mostre fatos

REGRA CRÍTICA DE NARRAÇÃO:
- TODOS os números no script devem ser escritos POR EXTENSO (o texto será narrado por TTS)
- "dois" NÃO "2", "oitavo" NÃO "VIII", "mil quinhentos e trinta e seis" NÃO "1536"
- Algarismos romanos SEMPRE por extenso: "Henrique oitavo" NÃO "Henrique VIII"
- No TÍTULO e DESCRIÇÃO pode usar números/romanos normalmente (ex: "Henrique VIII", "2 esposas")
- Esta regra é APENAS para o campo "script" que será narrado em voz

Retorne SOMENTE:

[JSON_START]
{{
  "titulo": "título max 60 chars",
  "descricao": "descrição com #hashtags",
  "script": "texto narrado com paragrafos separados por \\n\\n",
  "estrutura": "E11",
  "total_cenas": 14
}}
[JSON_END]
"""

    logger.info(f"[scriptwriter] Gerando script: {topic} | {canal} | {lingua}")

    raw = call_claude_cli(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model="claude-opus-4-6",
        timeout=300,
    )

    # Extract JSON
    match = re.search(r'\[JSON_START\](.*?)\[JSON_END\]', raw, re.DOTALL)
    if match:
        result = json.loads(match.group(1).strip())
        logger.info(f"[scriptwriter] OK: {result.get('titulo', '?')}")
        return result

    # Fallback: try parsing the whole response as JSON
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.error(f"[scriptwriter] Failed to parse response: {raw[:200]}")
        raise RuntimeError("Scriptwriter: could not parse JSON from response")
```

### O que PODE editar:
- `SYSTEM_PROMPT` (a frase curta no topo) — pode melhorar mas manter CURTO
- Toda a seção `REGRAS:` dentro do `user_prompt` — é aqui que mora a mágica
- Adicionar exemplos de bons scripts se quiser
- Mudar a estrutura das instruções de storytelling

### O que NÃO PODE editar:
- As variáveis Python entre chaves: `{canal}`, `{subnicho}`, `{lingua}`, `{topic}`, `{subnicho_desc}`
- O formato JSON de saída (titulo, descricao, script, estrutura, total_cenas)
- Os markers `[JSON_START]` e `[JSON_END]`
- A regra de 14 parágrafos (14 cenas visuais fixas)
- A regra de números por extenso na narração (TTS lê errado se não for extenso)
- O campo `total_cenas` tem que ser sempre 14
- NADA fora do `user_prompt` (imports, funções, lógica de parsing)

### Formato de entrega:
Me devolve o arquivo `scriptwriter.py` completo com as alterações. Eu substituo o arquivo e testo.

---

## PARTE 4 — Referência: 27 Estruturas de Copy (Micha)

O sistema usa essas estruturas pra variar o estilo narrativo. O campo `estrutura` no JSON indica qual foi usada (ex: "E4", "E11"). Conhecer essas estruturas ajuda a escrever prompts melhores.

### E1 — Progressão Exponencial ("What If Escalation")
- **Hook**: Pergunta hipotética impossível ("E se você nunca parasse de cavar?")
- **Arco**: Escalar números com marcos progressivos (10m, 100m, 1km...)
- **Motor**: Loop de dopamina contínuo via escala numérica + humor
- **Fechamento**: Twist irônico — a maior conquista vira a maior prisão

### E2 — Fatos Bizarros de Ícone ("Weird Facts Escalation")
- **Hook**: Desafio ao ego do viewer ("Coisas bizarras que você nunca soube sobre Einstein")
- **Arco**: Lista curada de fatos escalando em estranheza
- **Motor**: Ataque ao ego + micro-recompensas crescentes
- **Fechamento**: Fato mais emocionalmente impactante

### E3 — Ícone Moderno em Era Antiga ("Historical What-If Comedy")
- **Hook**: Premissa anacrônica ("Tesla ficaria rico vendendo eletricidade na Grécia Antiga?")
- **Arco**: Progressão dia-a-dia (Dia 1, Dia 2... Ano 1)
- **Motor**: Duplo information gap + humor situacional absurdo
- **Fechamento**: Fantasia de poder — protagonista vence sem consequências

### E4 — Estratégia Oculta do Gênio ("Hidden Mastermind Reveal")
- **Hook**: Conexão inesperada entre elementos contraditórios
- **Arco**: Cadeia causal passo-a-passo revelando estratégia brilhante
- **Motor**: Lógica de thriller de xadrez — viewer monta o quebra-cabeça junto
- **Fechamento**: Reframe que recontextualiza toda a narrativa

### E5 — Fato Bizarro com Validação Científica ("Ancient Shock + Modern Proof")
- **Hook**: Superlativo absoluto sobre tema mundano
- **Arco**: Método antigo absurdo → escalar absurdidade → validação científica
- **Motor**: "antigo = ignorante" destruído
- **Fechamento**: Ciência moderna prova que o método funcionava

### E6 — Lenda Militar Imbatível ("The Unstoppable Ghost")
- **Hook**: Afirmação de ameaça suprema
- **Arco**: Mitificação de indivíduo contra força superior
- **Motor**: Fascinação por figuras que desafiam sistemas de poder
- **Fechamento**: Mistério aberto — protagonista nunca é capturado

### E7 — Anedota Histórica com Punch ("The Chad History Move")
- **Hook**: Ícone em posição vulnerável
- **Arco**: Inversão de poder — vítima vira o chefe
- **Motor**: Fascinação com audácia + Chekhov's Gun
- **Fechamento**: Promessa plantada no meio é cumprida brutalmente

### E8 — Compilação de Respostas Épicas ("Legendary Comebacks")
- **Hook**: Tese provocativa
- **Arco**: 3 blocos: ameaça pomposa → resposta devastadora de 1-4 palavras
- **Motor**: Satisfação de padrão + economia como poder
- **Fechamento**: Última resposta É o fechamento

### E9 — O Golpe Genial ("The Slickest Move in History")
- **Hook**: Contraste entre massas e gênio
- **Arco**: Narração passo-a-passo do golpe em tempo real
- **Motor**: Emoção de filme de assalto + "aha moment"
- **Fechamento**: Payoff revelando a escala do lucro

### E10 — Fatos com Narrador Cômico ("Personality-Driven Facts")
- **Hook**: Apresentação apoiada no magnetismo do ícone
- **Arco**: Fatos alternados com comentários humorísticos
- **Motor**: Bonding parassocial com narrador
- **Fechamento**: Fato final

### E11 — Resumo Épico Ultracompacto ("Cinematic Micro-History")
- **Hook**: Tríade de elementos contrastantes
- **Arco**: Compressão máxima de evento complexo em ~30s
- **Motor**: Sensação de GRANDEZA em micro formato
- **Fechamento**: Reframe de perspectiva que força reavaliação

### E12 — De Nada a Tudo ("Rags to Empire")
- **Hook**: Ponto zero absoluto
- **Arco**: Ascensão linear da pobreza ao império via marcos concretos
- **Motor**: Fascinação universal com ascensão
- **Fechamento**: Legado ou contraste irônico com origens

### E13 — O Improvável que Restaurou Tudo ("The Unlikely Restorer")
- **Hook**: Negação do destino ("Ele não nasceu para ser rei")
- **Arco**: Exílio → vitória contra odds impossíveis → reconstrução
- **Motor**: Fascinação com o improvável
- **Fechamento**: Legado de reconstrução que transcende o indivíduo

### E14 — Arco de Queda e Redenção ("Rise-Fall-Rise")
- **Hook**: Origem humilde + primeira escolha moral
- **Arco**: Sobe por escolha, cai por integridade, sobe maior
- **Motor**: Jornada do herói comprimida
- **Fechamento**: Renascimento maior + reconhecimento universal

### E15 — Denúncia Histórica Visceral ("Systemic Injustice Exposé")
- **Hook**: Afirmação de poder absoluto com prova escalante
- **Arco**: Justaposição poderosos vs sofredores, sem comentário editorial
- **Motor**: Indignação universal + viewer recrutado como juiz
- **Fechamento**: Crítica sistêmica que ressoa com os dias atuais

### E16 — Cronologia de Desastre em Tempo Real ("Disaster Countdown")
- **Hook**: Abertura jornalística com data, local, contexto
- **Arco**: Setup paralelo de elementos do desastre
- **Motor**: Ironia dramática + impotência diante do inevitável
- **Fechamento**: Comparação de escala com evento universalmente conhecido

### E17 — A Odisseia de Sobrevivência ("The Impossible Journey")
- **Hook**: Morte coletiva vs recusa individual
- **Arco**: Odisseia geográfica por ambientes letais
- **Motor**: Instinto de sobrevivência primal
- **Fechamento**: Sobrevivência é a vitória + estatísticas da jornada

### E18 — Identidade Oculta ("Mystery Origin Story")
- **Hook**: Início anônimo com detalhes viscerais
- **Arco**: Escada de competência sem revelar o nome
- **Motor**: Mistério da identidade + fascinação com trajetória
- **Fechamento**: Name drop que recontextualiza tudo

### E19 — DEPRECADA

### E20 — A Queda do Invencível ("The Titan's Downfall")
- **Hook**: Paradoxo gênio/erro + consequência revelada
- **Arco**: Pico → erro fatal → descenso passo-a-passo
- **Motor**: Descenso gradual mais devastador que queda instantânea
- **Fechamento**: Desolação poética — sem redenção

### E21 — A Conspiração Exposta ("The Government Betrayal")
- **Hook**: Superlativo de horror + traição institucional
- **Arco**: Revelação de programa secreto
- **Motor**: Medo da relação cidadão-estado — protetor vira predador
- **Fechamento**: Escala do dano + permaneceria escondido

### E22 — O Último Ato do Condenado ("The Final Stand")
- **Hook**: Contraste de escala chocante
- **Arco**: ESCOLHA DELIBERADA de como morrer
- **Motor**: "se soubesse que ia morrer, COMO morreria?"
- **Fechamento**: Protagonista remove insígnias e morre como soldado

### E23 — Arco Completo com Morte Irônica ("Full Arc + Ironic Death")
- **Hook**: Conquista + custo irônico simultaneamente
- **Arco**: Vulnerabilidade → juramento → ascensão → pico → morte anticlimática
- **Motor**: Admirar E lamentar ao mesmo tempo
- **Fechamento**: Morte que não combina com a vida

### E24 — O Reformador Traído ("The Martyred Reformer")
- **Hook**: Resultado + motivo moral revelado
- **Arco**: Reformas → desafio a poderes → traição interna → REVERSÃO TOTAL
- **Motor**: Indignação moral pura
- **Fechamento**: Tudo que construiu foi desfeito

### E25 — O Predador Disfarçado ("The Friendly Predator")
- **Hook**: Máscara revelada antes da história
- **Arco**: Ciclo de manipulação onde destrói FINGINDO cooperar
- **Motor**: Medo universal de ser manipulado
- **Fechamento**: Escala da destruição revelada

### E26 — Texto Sagrado como Thriller ("Sacred Text Retold")
- **Hook**: Questão filosófica universal
- **Arco**: Reconto cinematográfico usando linguagem de thriller
- **Motor**: Desfamiliarização do conhecido
- **Fechamento**: Síntese teológica/filosófica

### E27 — O Herói Contra o Próprio Corpo ("The Defiant Decay")
- **Hook**: Sentença biológica + feito impossível
- **Arco**: Luta em DUAS frentes — inimigos + corpo morrendo
- **Motor**: RECUSA em aceitar limites biológicos
- **Fechamento**: Corpo vence, mas legado transcende

---

## PARTE 5 — Mapeamento Estrutura → Subnicho

### Reis Perversos / Histórias Sombrias / Culturas Macabras
**Estruturas**: E4, E5, E15, E20, E21, E23, E24, E25

### Guerras e Civilizações (antiguidade/medieval)
**Estruturas**: E5, E6, E7, E8, E9, E11, E12, E18, E20, E22

### Frentes de Guerra / Relatos de Guerra (WWII+)
**Estruturas**: E4, E5, E6, E11, E16, E17, E21, E22, E27

### Mansões
**Estruturas**: E4, E11, E12, E15, E16, E20, E23, E25

---

## PARTE 6 — Subnichos (Contexto dos Canais)

### REIS PERVERSOS
Reis, imperadores, tiranos. Crueldade, rituais, torturas, traições na corte, execuções. Fatos históricos reais.

**Ângulos**: o que realmente acontecia dentro de (haréns, palácios, rituais), segredos que a história escondeu, práticas que tentaram apagar.

**Títulos referência**:
- O Que Acontecia de Verdade nos Haréns do Império Otomano — Era Pior Que Qualquer Prisão
- Os Espetáculos de Tortura Pública Mais Horripilantes Que a Europa Medieval Tentou Apagar
- What Was Found Inside the Coffins of Henry VIII's 6 Wives Changes Everything
- Caligula's Darkest Night: The Ceremony That Made Even Roman Senators Look Away

### HISTÓRIAS SOMBRIAS
Lado oculto de figuras famosas e eventos conhecidos. Revelação histórica com tom de documentário sombrio.

**Ângulos**: "os últimos dias de X foram piores do que imagina", "o que fizeram com X antes de Y", "o ritual que tentaram apagar".

### CULTURAS MACABRAS
Rituais e costumes macabros de civilizações antigas/medievais. Tom antropológico sem julgamento moral.

**Ângulos**: "o que X faziam com Y era pior que a morte", "a execução de X foi pior do que imagina".

### RELATOS DE GUERRA
Histórias individuais e momentos da WWII. Soldados, armas, erros fatais, execuções. Tom dramático-militar.

**Ângulos**: "ignoraram X até que Y aconteceu", "o truque estúpido que salvou milhares", contrastes irônicos.

### FRENTES DE GUERRA
Batalhas decisivas e figuras-chave da WWII. Momentos de virada, inovações. Tom cinematográfico.

**Ângulos**: "o momento em que o general soube que perdeu", "o truque estúpido de um cadete".

### GUERRAS E CIVILIZAÇÕES
Batalhas da antiguidade/medieval como épicos. Números impressionantes, estratégias brilhantes. NADA moderno.

**Ângulos**: "como X soldados derrotaram Y mil", "a mentira que você acreditou sobre X".

### MANSÕES / MONETIZADOS
Propriedades históricas, tragédias da riqueza, quedas de dinastias. Mansão é personagem da narrativa.

**Ângulos**: queda de famílias ricas, imóveis abandonados, imigrantes que construíram impérios.

---

## PARTE 7 — Regras Fundamentais de Copy (Micha)

### Hook (Primeiros 3 Segundos)
A primeira frase É o hook. Sem introdução, sem filler.

**NUNCA**: "Você sabia que...", "Neste vídeo...", "Hoje vamos falar sobre..."
**SEMPRE**: Fato chocante, premissa impossível, número absurdo, contraste dramático

**Exemplos que funcionam**:
- "Em mil novecentos e quarenta, um oficial polonês fez algo que ninguém na história teve coragem de fazer."
- "Uma família construiu o primeiro arranha-céu da América Latina. E morreu na miséria enquanto ele virava cortiço."

### Retenção (Meio)
- Pattern interrupts a cada 10-15s: "Mas fica pior...", "E aqui é onde a história muda..."
- Escalar tensão progressivamente
- Alternar frases curtas (impacto) e longas (buildup)
- Números concretos: "quinhentos soldados" não "muitos soldados"

### Fechamento (Final)
- Payoff emocional — entregar o que o hook prometeu
- Conexão com o início (loop)
- Reflexão ou twist irônico
- CTA natural (inscrição, like, comentário — variar)

### Universais
- NUNCA editorialize — mostra os fatos, deixa o viewer tirar conclusões
- Concreto > Abstrato
- Números por extenso para narração
- Vocabulário simples, emoções complexas
- Cada frase deve justificar sua existência

---

## Como Testar (sem rodar código)

Você não precisa instalar nada. Testa direto no chat da IA:

1. Abre o **Claude** (claude.ai) ou **ChatGPT**
2. Cola o `SYSTEM_PROMPT` como instrução do sistema (a frase curta do topo do código)
3. Cola o `user_prompt` substituindo as variáveis por valores reais:

```
Canal: Crônicas da Coroa | Subnicho: Reis Perversos | Língua: Português | Tema: Henrique VIII e suas esposas

Contexto: Histórias chocantes de reis, imperadores, tiranos e figuras de poder.
Crueldade, perversão, rituais, torturas, traições na corte, execuções.
Tudo baseado em fatos históricos reais.
```

4. Vê o script que a IA gera
5. Pergunta: "Ficou cativante? Dá vontade de assistir até o fim? Tem arco narrativo?"
6. Se não → ajusta o prompt → testa de novo
7. Repete até ficar satisfeito

### Variáveis pra testar com outros subnichos:

| Teste | Canal | Subnicho | Tema |
|-------|-------|----------|------|
| 1 | Crônicas da Coroa | Reis Perversos | Calígula e as noites de Roma |
| 2 | Forja Imperial | Guerras e Civilizações | Os 300 de Esparta |
| 3 | Arquivos da WW2 | Relatos de Guerra | O sniper mais letal da WWII |
| 4 | Grandes Mansões | Mansões | A mansão que Eike Batista abandonou |

Testa com pelo menos 2-3 temas diferentes pra garantir que funciona bem em vários contextos.

---

## Resumo da Entrega

1. Leia tudo acima pra entender o contexto
2. Teste o prompt no Claude/ChatGPT com temas de exemplo
3. Itere até os scripts ficarem cativantes
4. Edite o prompt dentro do `scriptwriter.py` (Parte 3)
5. Me devolva o arquivo `scriptwriter.py` completo
6. Eu substituo e pronto

**Foco**: fazer os scripts contarem HISTÓRIAS cativantes, não listas de fatos. O espectador tem que ficar PRESO do início ao fim.
