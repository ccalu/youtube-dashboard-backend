# 02. Pipeline de Produção - Overview

## 🎯 Propósito deste Documento

Este documento explica **como a Content Factory cria vídeos** - o pipeline de produção automatizado de 17 passos que gera 100-130 vídeos por dia.

**Por que isso importa para o Dashboard?**
- O Dashboard **integra com o pipeline** (upload de vídeos)
- Entender a produção ajuda a entender o contexto dos dados coletados
- O Dashboard monitora **resultados** da produção (views, engagement, receita)

---

## 🏭 VISÃO GERAL DO PIPELINE

### O Que É

Um sistema totalmente automatizado que transforma **ideia → vídeo publicado no YouTube** sem intervenção humana.

### Números

| Métrica | Valor |
|---------|-------|
| **Passos automatizados** | 17 steps |
| **Agentes AI** | 8 agents |
| **Máquinas de produção** | 5 (M1-M5) |
| **Capacidade diária** | 100-130 vídeos |
| **Tempo por vídeo** | ~15-30 minutos |
| **Idiomas suportados** | 10+ línguas |
| **Formatos** | Múltiplos (AI images, avatars) |

---

## 🔄 OS 17 PASSOS DO PIPELINE

### **Fase 1: Ideação e Roteiro (Passos 1-3)**

#### **1. Topic Generator Agent**
- **Input:** Subnicho, idioma, histórico de tópicos usados
- **Output:** Tópico novo e único para o vídeo
- **Função:** Garante não repetir temas

#### **2. Script Writer Agent**
- **Input:** Tópico escolhido, tom do canal, duração target
- **Output:** Roteiro completo do vídeo (narração)
- **Função:** Cria narrativa envolvente

#### **3. Screenplay Agent**
- **Input:** Roteiro completo
- **Output:** Roteiro segmentado (scene breakdown)
- **Função:** Divide roteiro em cenas com timings

---

### **Fase 2: Assets Visuais (Passos 4-6)**

#### **4. Prompt Generator Agent**
- **Input:** Roteiro segmentado
- **Output:** Prompts otimizados para geração de imagens
- **Função:** Cria descrições visuais para cada cena
- **🆕 Melhoria planejada:** Adicionar instruções de variação (lighting, color palette, art style)

#### **5. Image Generation**
- **Input:** Prompts do passo 4
- **Output:** Imagens AI para cada cena
- **Tecnologia Primária:** Google Gemini API
  - $300 créditos grátis por conta nova
  - Estratégia: Criar múltiplas contas (CPFs/emails disponíveis)
- **Tecnologia Fallback:** ComfyUI (local)
  - Backup se Gemini indisponível
  - Usa checkpoints treinados localmente

#### **6. Image Processing**
- **Input:** Imagens geradas
- **Output:** Imagens otimizadas (resolução, aspect ratio, etc)
- **Função:** Prepara imagens para edição de vídeo

---

### **Fase 3: Assets de Áudio (Passos 7-9)**

#### **7. TTS Polish Agent**
- **Input:** Roteiro original
- **Output:** Roteiro otimizado para Text-to-Speech
- **Função:** Ajusta pontuação, respiração, ênfase para narração natural
- **Por idioma:** Um agent por língua

#### **8. Text-to-Speech Generation**
- **Input:** Roteiro polido
- **Output:** Arquivo de áudio da narração
- **Tecnologia:** AllTalk (local)
- **Idiomas:** 10+ vozes (uma por idioma target)
- **Qualidade:** Natural, sem sotaque robótico

#### **9. Transcription (WhisperX)**
- **Input:** Áudio gerado no passo 8
- **Output:** Transcrição com timestamps precisos
- **Tecnologia:** WhisperX (local)
- **Função:** Gera legendas sincronizadas
- **🆕 Melhoria planejada:** Subtitle Polish Agent para corrigir erros de transcrição

---

### **Fase 4: Edição de Vídeo (Passos 10-13)**

#### **10. Ken Burns Animations**
- **Input:** Imagens estáticas + duração de cada cena
- **Output:** Imagens com movimento de câmera (zoom, pan)
- **Efeitos:** Zoom-in, zoom-out, pan-left, pan-right, diagonal
- **🆕 Melhoria planejada:** 20 templates de alta qualidade com easing curves

#### **11. FFmpeg Transitions**
- **Input:** Cenas com animações
- **Output:** Cenas conectadas com transições suaves
- **Efeitos:** Fade, dissolve, crossfade, wipe, slide, zoom-through
- **🆕 Melhoria planejada:** Implementar biblioteca de transições profissionais
- **Timing:** Transições em pausas naturais da fala (não mid-word)

#### **12. Subtitle Overlay**
- **Input:** Vídeo + transcrição com timestamps
- **Output:** Vídeo com legendas
- **Templates:** 10 estilos diferentes de legenda por conta
- **Rotação:** Evita mesmo estilo em todos os vídeos

#### **13. Add Music (Background)**
- **Input:** Vídeo completo
- **Output:** Vídeo com música de fundo
- **Biblioteca:** 25-38 tracks royalty-free por conta
- **Rotação:** Música diferente em cada vídeo
- **Volume:** Ajustado para não competir com narração

---

### **Fase 5: Polish e Assets Extras (Passos 14-15)**

#### **14. Add Overlay**
- **Input:** Vídeo quase final
- **Output:** Vídeo com overlay gráfico (bordas, frames, elements)
- **Biblioteca:** 8 overlays diferentes por conta
- **Rotação:** Overlay diferente em cada vídeo
- **🆕 Melhoria planejada:** Expandir biblioteca de overlays

#### **15. Sound Effects System** 🆕
- **Input:** Vídeo + transcrição com timestamps
- **Output:** Vídeo com sound effects em momentos chave
- **Status:** **NÃO IMPLEMENTADO** (planejado para Semana 1)
- **Implementação (3 fases):**
  1. **Curadoria:** 50 SFX versáteis por conta
  2. **SFX Placement Agent:** LLM identifica momentos ideais
  3. **FFmpeg Integration:** Mix de áudio em timestamps precisos

---

### **Fase 6: Formatos Especiais (Novo)**

#### **16. HeyGen Avatar Integration** 🆕
- **Input:** Roteiro (primeiro minuto)
- **Output:** Vídeo de avatar narrando introdução
- **Status:** **EM DESENVOLVIMENTO** (Semana 2)
- **Formato:** Avatar (1min) + AI Images (resto)
- **Personas:** 10 characters por canal
- **Propósito:** Humanizar conteúdo ("automated" → "person telling story")
- **Tecnologia:** HeyGen API
- **Economia:** $99/mês (Pro) ou 10 contas grátis (10 créditos/mês cada)

---

### **Fase 7: Finalização e Upload (Passo 17)**

#### **17. Video Export & Quality Check**
- **Input:** Vídeo completo
- **Output:** Vídeo final renderizado
- **Codec:** H.264, MP4
- **Resolução:** 1080p (Full HD)
- **Quality Check:** Validação automática (duração, áudio sync, corruption)
- **Próximo passo:** Adicionar na fila de upload (`upload_queue`)

---

## 🖥️ INFRAESTRUTURA: 5 Máquinas

### Distribuição

| Máquina | Função | Capacidade |
|---------|--------|-----------|
| **M1** | Produção | 20-26 vídeos/dia |
| **M2** | Produção | 20-26 vídeos/dia |
| **M3** | Produção | 20-26 vídeos/dia |
| **M4** | Produção + Dev | 20-26 vídeos/dia |
| **M5** | Produção | 20-26 vídeos/dia |

**Total:** 100-130 vídeos/dia

### Setup de Cada Máquina

- **Sistema Operacional:** Windows (todas)
- **Python:** 3.10+
- **ComfyUI:** Instalado (fallback para imagens)
- **AllTalk:** TTS local
- **WhisperX:** Transcrição local
- **FFmpeg:** Edição de vídeo
- **MoviePy:** Python video editing
- **Credenciais:** Gemini API keys, YouTube OAuth por canal

---

## 🔄 SISTEMA DE ROTAÇÃO (Anti-Detecção)

### Por Que Rotação?

YouTube detecta **padrões de produção em massa**. Se todos os vídeos de um canal têm:
- Mesma música
- Mesmas transições
- Mesmo overlay
- Mesma sequência de animações

→ Canal é flagged como "factory" e desmonetizado.

### Elementos Rotacionados

| Elemento | Status Atual | Quantidade | Status |
|----------|--------------|-----------|--------|
| **1. Música** | ✅ OK | 25-38 tracks/conta | Implementado |
| **2. Overlays** | ⚠️ Limitado | 8/conta | Precisa expandir |
| **3. MoviePy Animations** | ⚠️ Baixa qualidade | 10 templates | Precisa melhorar |
| **4. Subtitle Templates** | ⚠️ Pouca diferença | 10 estilos | Precisa mais variação |
| **5. FFmpeg Transitions** | ❌ Poucos | Quase nenhum | **Precisa implementar** |
| **6. Sound Effects** | ❌ Não existe | 0 | **Precisa implementar** |

### Estratégia de Rotação

**Por canal (não por conta):**
- Cada canal tem seu próprio conjunto de assets
- Vídeo 1: Música A, Overlay A, Transition Set A
- Vídeo 2: Música B, Overlay B, Transition Set B
- Vídeo 3: Música C, Overlay C, Transition Set C
- ...
- Vídeo 26: Música A novamente (ciclo completo)

**Objetivo:** Nenhum vídeo parece idêntico aos outros.

---

## 🎨 TECH STACK DETALHADO

### Geração de Conteúdo

| Componente | Tecnologia | Custo | Notas |
|------------|-----------|-------|-------|
| **Ideação/Roteiro** | LLMs (Claude, GPT) | API credits | Agents via prompts |
| **Imagens AI** | Google Gemini | $0 (free credits) | $300/conta nova |
| **Imagens Fallback** | ComfyUI (local) | $0 | Stable Diffusion local |
| **TTS** | AllTalk | $0 | Open source, local |
| **Transcrição** | WhisperX | $0 | Open source, local |

### Edição de Vídeo

| Componente | Tecnologia | Custo | Notas |
|------------|-----------|-------|-------|
| **Animações** | MoviePy | $0 | Python library |
| **Transitions** | FFmpeg | $0 | Command-line tool |
| **Rendering** | FFmpeg | $0 | Final export |
| **Legendas** | FFmpeg + SRT | $0 | Subtitle overlay |

### Novos Formatos

| Componente | Tecnologia | Custo | Notas |
|------------|-----------|-------|-------|
| **Avatares** | HeyGen | $99/mês | Pro plan, ou 10 contas grátis |
| **Character Photos** | Gemini | $0 | Gera rostos para avatares |

### Assets

| Tipo | Fonte | Custo | Notas |
|------|-------|-------|-------|
| **Música** | Royalty-free libraries | $0-baixo | Curadoria manual |
| **Sound Effects** | Freesound, etc | $0 | Planejado |
| **Overlays** | Custom design | $0 | João Gabriel cria |

---

## 🔗 INTEGRAÇÃO COM DASHBOARD

### Como o Pipeline se Conecta ao Dashboard

#### **1. Upload de Vídeos**
```
[M1-M5 Produção]
    → Vídeo finalizado
    → Adicionado na `upload_queue` (Supabase)
    → [Dashboard Backend] pega da fila
    → [YouTube Uploader] faz upload
    → Atualiza Google Sheets
    → Marca como completed no DB
```

**Arquivo responsável:** `yt_uploader/uploader.py`
**Ver:** `11_YOUTUBE_UPLOADER.md`

#### **2. Monitoramento de Desempenho**
```
[YouTube] Vídeo publicado
    → 24h depois
    → [Dashboard Collector] coleta views/likes
    → [Notification Checker] verifica marcos
    → Se atingiu 10k views → Cria notificação
    → Arthur vê no dashboard
```

**Arquivo responsável:** `collector.py`, `notifier.py`
**Ver:** `06_YOUTUBE_COLLECTOR.md`, `07_NOTIFICACOES_INTELIGENTES.md`

#### **3. Coleta de Receita**
```
[YouTube] Receita gerada
    → Diariamente
    → [Monetization Collector] coleta via OAuth
    → Armazena em `monetization_history`
    → Dashboard financeiro mostra evolução
```

**Arquivo responsável:** `monetization_collector.py`
**Ver:** `09_MONETIZACAO_SISTEMA.md`

---

## 🆕 MELHORIAS PLANEJADAS (Semana 1-2)

### **Semana 1: Hardening do Pipeline**

#### **1. Refinar Prompts de Geração** (Segunda)
- Remover instruções de "consistência visual"
- Adicionar instruções de variação (lighting, colors, style, atmosphere)
- "Cada vídeo é único, priorize coerência narrativa sobre consistência cross-video"
- Lista dinâmica de estilos para agent escolher

#### **2. Subtitle Polish Agent** (Segunda) 🆕
- **Problema:** WhisperX comete erros de transcrição
- **Solução:** Agent corrige erros mantendo timestamps
- **Input:** (1) Texto original enviado para AllTalk, (2) Transcrição WhisperX
- **Output:** Texto corrigido com timestamps originais
- **Um agent por idioma**

#### **3. Ken Burns + FFmpeg Transitions** (Terça) 🆕
- **Goal:** 20 templates de alta qualidade combinados
- Consertar presets "congelados" atuais
- Substituir easing linear por ease-in-out, ease-out curves
- Variações: zoom-in, zoom-out, pan-left, pan-right, diagonal, combos
- Implementar transições FFmpeg: fade, dissolve, crossfade, wipe, slide, zoom-through
- Templates integrados: animação + transição que funcionam juntas

#### **4. Sync Precision** (Quarta)
- Melhorar cálculos de duração de imagem
- Garantir transições em pausas naturais da fala, não mid-word
- Buffer de 0.1s: transição começa após frase terminar
- Ajustar Screenplay Agent para agrupar segmentos respeitando pausas naturais

#### **5. Sound Effects System** (Quarta-Sexta) 🆕

**Fase 1 - Curar SFX por Conta:**
- Coletar 100 amostras de scripts por conta
- Usar LLM para identificar 50 sound effects úteis e versáteis
- Baixar/criar biblioteca royalty-free de SFX
- Armazenar em `/accounts/XXX/resources/sfx/`
- Criar mapping: nome → arquivo → descrição de uso

**Fase 2 - SFX Placement Agent:**
- **Input:** Transcrição WhisperX com timestamps + lista SFX disponíveis
- **Output:** Lista de (sfx_name, timestamp_start, volume)
- **System prompt:** "Identifique momentos ideais para sound effects. Seja sutil. Max X effects/minuto."
- **Regras:** Não sobrepor narração importante, preferir pausas/transições

**Fase 3 - FFmpeg Integration:**
- Criar função `mix_sfx(video, sfx_list) → video_with_sfx`
- Usar FFmpeg amix/adelay para posicionamento preciso de timestamp
- Ajustar volume de SFX para não competir com narração
- Integrar após Add Music (passo 13)

#### **6. Padronização M1-M5** (Qui-Sex)
- Atualizar pipeline em todas as 5 máquinas
- Testar todas as features novas
- Garantir consistência de ambiente

---

### **Semana 2: Novos Formatos**

#### **HeyGen Avatars + Visual Narrative**

**Contexto:**
- Nicho "Family Stories / First-Person Narratives" está vazio (demonetizações)
- Antes: Milhões de inscritos, formato simples
- Agora: Oportunidade de first-mover
- Problema: Formato antigo (imagens estáticas + narração) é exatamente o que YouTube penaliza

**Solução:** Upgrade format com HeyGen

**Estrutura Proposta:**
- **Primeiro minuto:** Avatar HeyGen introduzindo história (humanização)
- **Resto do vídeo:** Imagens AI ilustrando narrativa (pipeline existente)

**Por Que Funciona:**
- Avatar no primeiro minuto muda percepção completamente
- De "conteúdo automatizado" → "pessoa contando história"
- Resto do vídeo (imagens AI) contextualizado como "ilustração da narrativa", não conteúdo principal
- Constrói familiaridade através de personas consistentes

**Sistema de Personagens:**
- 10 personas por canal
- Fotos geradas em Gemini (variadas: idade, gênero, etnia)
- Criar avatares no HeyGen com fotos de referência
- Mesma "face" aparece em múltiplos vídeos
- Cada vídeo = 1 personagem narrando história em primeira pessoa

**Economia HeyGen:**
- **Free tier:** 10 créditos/mês (10 minutos = 10 vídeos com intro 1min)
- **Pro plan:** $99/mês para 100 créditos (100 minutos = ~3 vídeos/dia com intros)
- **Estratégia multi-conta:** 10 contas grátis = 100 minutos/mês ($0)
- **Viabilidade:** $99/mês < 1 dia de receita atual

**Implementação:**

**Fase 1 - Setup Inicial:**
- Criar conta HeyGen, explorar interface/API
- Gerar 10 fotos de personagens em Gemini
- Criar 10 avatares no HeyGen com fotos de referência
- Testar geração de 1 minuto com cada avatar
- Validar qualidade: lipsync, naturalidade, expressões

**Fase 2 - Pipeline Integration:**
- Definir estrutura de script: intro (avatar) + body (imagens)
- Criar processo para geração de vídeo HeyGen (API ou manual)
- Integrar vídeo avatar como primeiro clip antes do pipeline atual
- Ajustar concatenação FFmpeg para juntar avatar + main video
- Testar vídeo completo: transição avatar → imagens

**Fase 3 - Validação & Scale:**
- Produzir 5-10 vídeos de teste em formato completo
- Upload para canal de teste e monitorar métricas
- Validar: retention, CTR, feedback de audiência
- Se positivo: escalar para produção regular
- Decidir: múltiplas contas grátis ou Pro plan

**Timeline Semana 2:**
- **Segunda + Terça:** Criação de personagens + integração de pipeline
- **Quarta + Quinta:** Produção de vídeos de teste + validação
- **Sexta + Fim de semana:** Fechar Section 4 + Começar exploração Section 5

---

## 📊 MÉTRICAS DE QUALIDADE

### KPIs do Pipeline

| Métrica | Target | Atual |
|---------|--------|-------|
| **Vídeos/dia** | 100-130 | ✅ 100-130 |
| **Taxa de erro** | <5% | ⚠️ ~10% |
| **Tempo/vídeo** | <30min | ✅ 15-30min |
| **Sync áudio/vídeo** | Perfect | ⚠️ 90% |
| **Qualidade TTS** | Natural | ✅ Natural |
| **Variação visual** | Alto | ⚠️ Médio |
| **Detecção como factory** | 0% | ❌ ~14% (7/50) |

**Meta pós-hardening:** <5% taxa de detecção como factory

### Indicadores de Sucesso

**Técnicos:**
- ✅ Zero elementos repetidos detectáveis
- ✅ Transições suaves em pausas naturais
- ✅ Sound effects sutis e profissionais
- ✅ Animações com easing curves de qualidade

**De Negócio:**
- ✅ Taxa de retenção de monetização >90% após 6 meses
- ✅ Novos canais monetizados em <30 dias
- ✅ Vídeos indistinguíveis de produção manual
- ✅ Capacidade de abrir novos nichos rapidamente

---

## 🎓 DECISÕES ESTRATÉGICAS

### Redução de Volume: 3 → 1 Vídeo/Dia

**Antes:** 3 vídeos/dia por canal
**Agora:** 1 vídeo/dia por canal

**Por quê?**
- Alto volume virou fingerprint de detecção
- Canais concorrentes com 1 vídeo/dia permaneceram monetizados
- Foco em qualidade + variação > quantidade

**Impacto:**
- Capacidade total: 100-130 vídeos/dia serve 100-130 canais (vs 33-43 antes)
- Permite escalar para mais canais mantendo qualidade
- Reduz detecção como "mass production"

### Foco em Diversificação vs Otimização

**Estratégia Antiga:** Otimizar canais existentes, maximizar output por canal
**Estratégia Nova:** Diversificar subnichos/idiomas, conquistar novos territórios

**Implicação para Pipeline:**
- Pipeline precisa ser **flexível** (adaptar novos formatos rapidamente)
- **Não apenas eficiente** (produzir muito do mesmo)
- HeyGen avatars = exemplo de flexibilidade

---

## 🔮 EXPLORAÇÃO FUTURA (Não Imediato)

### Capability 1: Web Scraping for Images

**Problema:**
Nichos bloqueados que requerem fotos reais, atuais:
- **Tecnologia:** Fotos de iPhones, laptops específicos
- **Luxo:** Imagens de Ferraris, Rolex
- **Notícias:** Imagens de eventos atuais
- **Esportes:** Fotos de atletas reais, jogos, eventos

**Limitação Atual:**
- Stock images (Pexels, Pixabay) faltam conteúdo atual/específico
- Imagens AI não podem replicar pessoas/produtos reais com precisão
- Requer fotografias reais de assuntos atuais

**Questão Legal Não Resolvida:**
- Uso de imagens de celebridades, atletas, produtos de marca - onde está a linha?
- Fair use jornalístico? Press kits oficiais? Screenshots?
- **Precisa clareza legal antes de investir em pipeline**

**Status:** 🟡 Exploração futura - não imediato

### Capability 2: Trending System

**Conceito:** Identificar automaticamente o que está trending online e criar conteúdo sobre isso.

**Mudança de Paradigma:**
- De "produzir conteúdo evergreen" → "surfar ondas de demanda"

**Opções de Velocidade (Indefinido):**
- **Daily news:** Ciclo 24-48h - Requer produção muito rápida, quase real-time
- **Weekly trends:** Ciclo 7-30 dias - Mais viável com pipeline atual
- **Ondas maiores:** Identificar trends antes de saturação - Requer análise preditiva

**Componentes Necessários (Conceitual):**
1. **Discovery:** Monitorar fontes (Google Trends, Twitter/X, Reddit, YouTube Trending)
2. **Filter:** Identificar trends relevantes para nichos Content Factory
3. **Generation:** Auto-criar scripts sobre tópicos trending
4. **Assets:** Obter imagens/vídeos relacionados (volta ao problema webscraping)
5. **Velocity:** Pipeline precisa ser mais rápido que normal

**Status:** 🟡 Sem clareza - deixado para explorar depois

---

## 🔗 RELACIONAMENTOS COM OUTROS DOCUMENTOS

### Leia Depois:
- **Como vídeos são enviados:** `11_YOUTUBE_UPLOADER.md`
- **Como receita é coletada:** `09_MONETIZACAO_SISTEMA.md`
- **Como oportunidades são identificadas:** `07_NOTIFICACOES_INTELIGENTES.md`

### Contexto de Negócio:
- **Por que produzimos:** `01_CONTENT_FACTORY_VISAO_GERAL.md`
- **Como Dashboard ajuda:** `03_DASHBOARD_PROPOSTA_VALOR.md`

---

## 📝 SOBRE ESTE DOCUMENTO

- **Autor:** Cellibs (Marcelo) via Claude Code
- **Data:** Janeiro 2025
- **Versão:** 1.0
- **Fonte:** Baseado no PRD v3 Content Factory (Section 3-5)
- **Propósito:** Contexto de produção para entender integração com Dashboard
- **Audiência:** Claude Code em qualquer máquina

---

**Documento Anterior:** [01. Content Factory - Visão Geral](./01_CONTENT_FACTORY_VISAO_GERAL.md)
**Próximo Documento:** [03. Dashboard - Proposta de Valor](./03_DASHBOARD_PROPOSTA_VALOR.md)
