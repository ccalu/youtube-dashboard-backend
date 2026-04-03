# Pacote Completo — Otimizacao do Diretor de Cinema

> **Objetivo**: Melhorar os prompts visuais (imagem + animacao) e testar modelos alternativos.
> **Entrega**: Me devolve o arquivo `director.py` com os prompts otimizados. Eu substituo e pronto.

---

## PARTE 1 — Como Funciona

### Fluxo
```
[Roteirista gera script com 14 paragrafos]
         |
[Diretor recebe script + subnicho + canal]
         |
[Claude Sonnet gera 14 cenas: prompt_imagem + prompt_animacao]
         |
[Freepik Spaces executa: imagem (Z-Image/NanoBanana) + video (MiniMax Hailuo)]
         |
[Remotion monta: clips + narracao + legendas + musica]
```

### O que cada prompt faz
- **prompt_imagem**: Gera a IMAGEM estática (frame inicial da cena). Modelo: NanoBanana 2 / Z-Image no Freepik
- **prompt_animacao**: Anima a imagem gerada (6s de video). Modelo: MiniMax Hailuo 2.3 Fast no Freepik

### Importante
- Cada paragrafo do script = 1 cena visual
- O clip dura o tempo do paragrafo na narracao (nao e fixo 6s pra todos)
- Formato: 9:16 vertical (768x1344)
- A imagem e o frame INICIAL do video — o prompt de animacao so descreve o MOVIMENTO

---

## PARTE 2 — Problemas Atuais

1. **Imagens repetitivas** — muitas cenas com o mesmo tipo de composicao (retrato centralizado)
2. **Animacoes genericas** — "camera slowly pushing in" em quase todas as cenas
3. **Falta de variedade** — poucas mudancas de angulo, iluminacao, tipo de cena
4. **Modelo de video** — MiniMax Hailuo 2.3 Fast pode nao ser o melhor disponivel no Freepik

---

## PARTE 3 — O Arquivo Para Editar

### `director.py` (codigo completo atual)

```python
"""
Diretor de Cinema — gera prompts de imagem e animacao para cada cena.

Recebe o script do Roteirista e gera 14 cenas com prompt de imagem
e prompt de animacao pensados JUNTOS.
"""

import json
import re
import logging
from claude_llm_client import call_claude_cli

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Voce e um diretor de cinema para YouTube Shorts. Responda SOMENTE com JSON entre [JSON_START] e [JSON_END]. Sem markdown, sem explicacao."""


def generate_scenes(script: str, canal: str, subnicho: str, lingua: str, estilo_visual: str = "", total_cenas: int = 14) -> list:
    user_prompt = f"""Crie {total_cenas} cenas visuais para este script de YouTube Short.

Canal: {canal} | Estilo: {estilo_visual}

Script:
{script}

REGRAS IMAGEM (NanoBanana 2, formato 9:16 vertical, 768x1344):
- Prompts em INGLES, 80-150 palavras
- OBRIGATORIO incluir "9:16 vertical format" ou "vertical portrait format 9:16" no prompt
- Estrutura: estilo+plano, sujeito detalhado, ambiente, iluminacao, color grade, "9:16 vertical portrait composition, no text, no watermark"
- VARIAR angulo/plano/iluminacao entre cenas (nunca repetir consecutivo)
- Cada imagem interessante SOZINHA
- COMPLIANCE: sem violencia grafica explicita, sem nudez, sem gore. Usar eufemismos e atmosfera em vez de violencia direta

REGRAS ANIMACAO (MiniMax Hailuo 2.3, 6s):
- Prompts em INGLES, 30-60 palavras
- NUNCA descrever a imagem, SO movimento
- Estrutura: camera movement > subject movement > atmospheric > mood
- PROIBIDO: "8K", "masterpiece", quality boosters
- Frases narrativas fluidas, verbos presente continuo

Cena 1 = HOOK VISUAL (mais impactante). Pensar imagem+animacao JUNTOS.

Retorne SOMENTE:

[JSON_START]
{{
  "cenas": [
    {{"cena": 1, "prompt_imagem": "Cinematic...", "prompt_animacao": "Slow..."}},
    ...exatamente {total_cenas} cenas
  ]
}}
[JSON_END]
"""

    logger.info(f"[director] Gerando {total_cenas} cenas para: {canal}")

    raw = call_claude_cli(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model="claude-sonnet-4-6",
        timeout=300,
    )

    match = re.search(r'\[JSON_START\](.*?)\[JSON_END\]', raw, re.DOTALL)
    if match:
        result = json.loads(match.group(1).strip())
        cenas = result.get('cenas', [])
        logger.info(f"[director] OK: {len(cenas)} cenas geradas")
        return cenas

    try:
        result = json.loads(raw.strip())
        return result.get('cenas', [])
    except json.JSONDecodeError:
        logger.error(f"[director] Failed to parse response: {raw[:200]}")
        raise RuntimeError("Director: could not parse JSON from response")
```

### O que PODE editar:
- `SYSTEM_PROMPT` — pode melhorar mas manter CURTO
- Toda a secao de REGRAS dentro do `user_prompt` — prompts de imagem e animacao
- Adicionar exemplos de bons prompts
- Mudar nomes de modelos se testar outros no Freepik
- Mudar tamanho/estrutura dos prompts

### O que NAO PODE editar:
- As variaveis Python entre chaves: `{canal}`, `{script}`, `{estilo_visual}`, `{total_cenas}`
- O formato JSON de saida (cenas com prompt_imagem + prompt_animacao)
- Os markers `[JSON_START]` e `[JSON_END]`
- O numero de cenas tem que ser {total_cenas} (14)
- NADA fora do `user_prompt` (imports, funcoes, logica de parsing)

---

## PARTE 4 — Modelos Disponiveis no Freepik Spaces

### Geracao de Imagem
- **NanoBanana 2** (atual) — bom pra fotorealismo e pintura
- **Z-Image** — alternativa, testa e compara
- **Outros no Freepik** — se encontrar melhor, testa

### Geracao de Video (Image-to-Video)
- **MiniMax Hailuo 2.3 Fast** (atual) — 6s, 768p, 9:16
- **Outros modelos no Freepik** — se tiver algo melhor, testa

### Se trocar o modelo:
- Muda o nome no comentario do prompt (ex: "REGRAS IMAGEM (NovoModelo)")
- Ajusta as regras de prompt pro novo modelo (tamanho, estilo, limitacoes)
- Me avisa qual modelo escolheu pra eu atualizar no Freepik Spaces

---

## PARTE 5 — Estilos Visuais por Subnicho

### Guerras e Civilizacoes
- Cinematografico epico, hiper-realista
- Paletas: dourado (gloria), dessaturado (derrota), azul-cinza (tensao)
- Cenas: panoramicas de batalha, close de olhos em elmos, formacoes militares

### Relatos/Frentes de Guerra (WWII)
- Fotografia documental anos 1940 (NAO Hollywood)
- 5 estilos: P&B alto contraste, P&B grao suave, sepia, colorizado, cor muda
- Constraints: sem HDR, sem foco ultra-sharp, sem poses heroicas

### Reis Perversos / Culturas Macabras / Historias Sombrias
- Pintura a oleo renascentista + iluminacao barroca (Caravaggio, Rembrandt)
- Chiaroscuro, tenebrismo, sfumato
- Paleta: dourado, carmesim, azul profundo, ambar de velas

### Mansoes
- Fotografia documental cinematografica por era
- Mansao como personagem central
- Estilos arquitetonicos especificos

---

## PARTE 6 — Regras de Animacao (MiniMax Hailuo)

### Regra principal: NUNCA descrever a imagem, SO movimento

### Estrutura:
1. Movimento de camera (primeiro)
2. Movimento do sujeito
3. Movimento atmosferico (vento, fumaca, particulas)
4. Mood/atmosfera (ultimo)

### 30-60 palavras, ingles, verbos presente continuo

### Variar intensidade:
- Sutil: momentos contemplativos
- Moderado: narrativa normal
- Intenso: acao, climax
- Dramatico: morte, revelacao

---

## PARTE 7 — Como Testar

1. Abre o **Claude** (claude.ai)
2. Cola o `SYSTEM_PROMPT`
3. Cola o `user_prompt` substituindo:
   - `{canal}` > "Cronicas da Coroa"
   - `{estilo_visual}` > "Renaissance oil painting with dramatic Baroque lighting"
   - `{total_cenas}` > 14
   - `{script}` > (cola um script de teste)
4. Ve os prompts gerados
5. Testa os prompts no Freepik Spaces (cola direto)
6. Ajusta o prompt e repete

### Script de teste (usar pra gerar prompts):
```
O que encontraram no rosto de Elizabeth I chocou toda a corte.

Ela era a rainha mais poderosa do mundo.

Mas escondia um segredo sob a maquiagem.

Aos vinte e nove anos, a variola destruiu seu rosto.

Ela passou a cobrir a pele com chumbo branco.

Camada sobre camada, todos os dias.

O veneno corroia lentamente sua carne.

Seus dentes apodreceram e cairam um a um.

Ela proibiu todos os espelhos do palacio.

Nos ultimos anos, mal conseguia comer.

Recusava medicos e ficava dias deitada no chao.

Seu corpo ja estava destruido pelo chumbo.

Morreu aos sessenta e nove anos, sozinha e desfigurada.

Siga para mais historias que a escola nunca contou.
```

---

## Resumo da Entrega

1. Leia tudo acima
2. Teste prompts no Claude + Freepik Spaces
3. Itere ate ficar satisfeito com a qualidade visual
4. Edite o `director.py` com os novos prompts
5. Me devolva o arquivo completo
6. Me diga qual modelo de imagem/video escolheu (se mudou)
