# 07 - Sistema de Notificações Inteligentes

**Arquivo:** `D:\ContentFactory\youtube-dashboard-backend\notifier.py` (449 linhas)
**Classe Principal:** `NotificationChecker`
**Propósito:** Sistema anti-duplicação para notificar vídeos que atingiram marcos de views (10k/24h, 50k/7d, etc)

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Lógica de Notificação](#lógica-de-notificação)
3. [NotificationChecker Class](#notificationchecker-class)
4. [Sistema Anti-Duplicação](#sistema-anti-duplicação)
5. [Regras de Notificação](#regras-de-notificação)
6. [Workflow do Arthur](#workflow-do-arthur)
7. [Integração com main.py](#integração-com-mainpy)
8. [Configuração de Regras](#configuração-de-regras)
9. [Troubleshooting](#troubleshooting)

---

## Visão Geral

O `NotificationChecker` é executado **automaticamente após cada coleta** para identificar vídeos que atingiram marcos de performance (ex: 10k views em 24h).

### Problema que Resolve

**Antes do sistema:**
- Arthur tinha que revisar TODOS os vídeos coletados manualmente
- Perdia vídeos virais (10k+ views)
- Não havia filtro por subnicho/língua

**Depois do sistema:**
- Sistema notifica apenas vídeos que atingiram marcos
- Anti-duplicação: vídeo só notifica UMA VEZ por marco
- Elevação: notificação 10k → 50k → 100k (atualiza, não duplica)
- Filtros: subnicho, língua, tipo de canal

### Quando Executa

```python
# Automaticamente após coleta (main.py)
async def run_collection_job():
    # 1. Coletar dados dos canais
    # ...

    # 2. EXECUTAR NOTIFIER
    await notifier.check_and_create_notifications()

    # 3. Finalizar coleta
```

### Localização no Sistema

```
D:\ContentFactory\youtube-dashboard-backend\
├── notifier.py           ← Você está aqui
├── main.py               ← Chama o notifier após coleta
├── database.py           ← Queries de notificações
└── .env                  ← Configurações
```

---

## Lógica de Notificação

### Fluxo Simplificado

```
1. Buscar regras ativas (ex: 10k/24h, 50k/7d)
2. Para cada regra:
   a. Buscar vídeos que atingiram o marco
   b. Verificar se já existe notificação não vista
   c. Se existe:
      - Nova regra maior? → ATUALIZAR notificação
      - Senão? → PULAR
   d. Se não existe:
      - Já foi visto em marco maior/igual? → PULAR
      - Senão? → CRIAR notificação
```

### Exemplo Prático

**Vídeo X atingiu 10,000 views em 24h:**
```
Dia 1: 10,000 views → ✅ CRIAR notificação "10k/24h"
Arthur vê: ❌ (não viu ainda)
```

**Dia 2: Vídeo X atingiu 50,000 views em 7 dias:**
```
Já tem notificação não vista de 10k?
→ Sim! E 50k > 10k? → ✅ ATUALIZAR para "50k/7d"
Arthur vê: ❌ (ainda não viu)
```

**Dia 3: Arthur marca como vista**
```
Arthur clica em "Marcar vista"
Status: vista = true
```

**Dia 4: Vídeo X atingiu 100,000 views em 30 dias:**
```
Já tem notificação não vista?
→ Não (foi vista)
Já foi visto em marco maior/igual?
→ Sim, foi visto em 50k
→ 100k > 50k? → ✅ CRIAR nova notificação "100k/30d"
```

### Regras de Elevação

```python
# Hierarquia de marcos (menor → maior)
10k/24h < 15k/3d < 50k/7d < 100k/30d

# Regra de elevação:
# - Se notificação NÃO VISTA: pode atualizar para marco maior
# - Se notificação VISTA: pode criar nova para marco maior
# - Nunca notifica marco menor após maior
```

---

## NotificationChecker Class

**Linhas:** 16-449
**Propósito:** Verificar vídeos e criar/atualizar notificações

### Inicialização (__init__)

**Linhas:** 22-30

```python
def __init__(self, db: Client):
    """
    Inicializa o NotificationChecker.

    Args:
        db: Cliente do Supabase para acesso ao banco de dados
    """
    self.db = db
    logger.info("NotificationChecker inicializado")
```

### Método Principal: check_and_create_notifications()

**Linhas:** 33-127

```python
async def check_and_create_notifications(self):
    """
    Função principal que verifica e cria notificações.

    Fluxo com anti-duplicação:
    1. Busca regras ativas ordenadas por hierarquia
    2. Para cada video que atinge marco:
       - Se já tem notificação NÃO VISTA e nova regra é maior: ATUALIZA
       - Se já foi visto alguma vez: PULA
       - Se não tem notificação: CRIA
    """
    try:
        logger.info("=" * 80)
        logger.info("INICIANDO VERIFICACAO DE NOTIFICACOES")
        logger.info("=" * 80)

        # 1. Buscar regras ativas ORDENADAS por views_minimas (hierarquia)
        regras = await self.get_regras_ativas_ordenadas()

        if not regras:
            logger.info("Nenhuma regra ativa encontrada. Pulando verificacao.")
            return

        logger.info(f"Encontradas {len(regras)} regras ativas")

        total_criadas = 0
        total_atualizadas = 0
        total_puladas = 0

        # 2. Processar cada regra (da menor para maior)
        for regra in regras:
            logger.info("-" * 80)
            logger.info(f"Processando regra: {regra['nome_regra']}")
            logger.info(f"Marco: {regra['views_minimas']} views em {regra['periodo_dias']} dia(s)")

            # Log de subnichos da regra
            if regra.get('subnichos'):
                logger.info(f"Subnichos: {', '.join(regra['subnichos'])}")
            else:
                logger.info("Subnichos: TODOS")

            # 3. Buscar videos que atingiram o marco
            videos = await self.get_videos_that_hit_milestone(regra)

            if not videos:
                logger.info("Nenhum video atingiu este marco")
                continue

            logger.info(f"{len(videos)} video(s) atingiram este marco")

            # 4. Processar cada video
            for video in videos:
                # Limpar duplicatas antigas antes de processar
                await self.cleanup_duplicate_notifications(video['video_id'])

                # Verificar se video ja tem notificacao NAO VISTA
                notificacao_existente = await self.get_unread_notification(video['video_id'])

                if notificacao_existente:
                    # Comparar hierarquia de regras
                    regra_anterior = await self.get_regra_by_periodo(notificacao_existente['periodo_dias'])

                    if regra_anterior and regra['views_minimas'] > regra_anterior['views_minimas']:
                        # Nova regra é maior - ATUALIZAR notificação
                        await self.update_notification(notificacao_existente['id'], video, regra)
                        total_atualizadas += 1
                        logger.info(f"✅ NOTIFICACAO ATUALIZADA: '{video['titulo'][:50]}...' ({regra_anterior['nome_regra']} → {regra['nome_regra']})")
                    else:
                        total_puladas += 1
                        logger.info(f"⭕ Video '{video['titulo'][:50]}...' ja tem notificacao igual ou maior - PULANDO")
                else:
                    # Verificar se já foi visto em marco maior ou igual
                    ja_visto = await self.video_already_seen(video['video_id'], regra)

                    if ja_visto:
                        total_puladas += 1
                        logger.info(f"👁️ Video '{video['titulo'][:50]}...' ja foi visto em marco maior/igual - PULANDO")
                        continue

                    # Criar nova notificacao
                    await self.create_notification(video, regra)
                    total_criadas += 1
                    logger.info(f"🆕 NOTIFICACAO CRIADA: '{video['titulo'][:50]}...'")

        logger.info("=" * 80)
        logger.info(f"✅ VERIFICACAO COMPLETA")
        logger.info(f"   Criadas: {total_criadas}")
        logger.info(f"   Atualizadas: {total_atualizadas}")
        logger.info(f"   Puladas: {total_puladas}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Erro ao verificar notificacoes: {e}")
        import traceback
        logger.error(traceback.format_exc())
```

---

## Sistema Anti-Duplicação

### Problema que Resolve

**Sem anti-duplicação:**
```
Vídeo X: 10k views → Notifica
Vídeo X: 12k views → Notifica (duplicata!)
Vídeo X: 50k views → Notifica (triplicata!)
```

**Com anti-duplicação:**
```
Vídeo X: 10k views → Notifica (cria)
Vídeo X: 12k views → Pula (já notificou 10k)
Vídeo X: 50k views → Atualiza notificação 10k → 50k (sem duplicar!)
```

### Métodos de Anti-Duplicação

#### 1. get_unread_notification()

**Linhas:** 147-167

```python
async def get_unread_notification(self, video_id: str) -> Optional[Dict]:
    """
    Busca notificação NÃO VISTA do vídeo.
    Retorna apenas a primeira (mais recente).
    """
    try:
        response = self.db.table("notificacoes")\
            .select("*")\
            .eq("video_id", video_id)\
            .eq("vista", False)\
            .order("created_at.desc")\
            .limit(1)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    except Exception as e:
        logger.error(f"Erro ao buscar notificacao nao vista: {e}")
        return None
```

#### 2. video_already_seen()

**Linhas:** 189-226

```python
async def video_already_seen(self, video_id: str, regra_atual: Dict) -> bool:
    """
    Verifica se video ja teve notificacao VISTA para um marco MAIOR OU IGUAL.
    Permite notificar novamente se atingir marcos maiores.

    Exemplo:
    - Video atingiu 10k → notificou → viu ✓
    - Video atingiu 50k → pode notificar novamente ✓
    - Video atingiu 100k → pode notificar novamente ✓
    """
    try:
        # Buscar notificações vistas deste vídeo
        response = self.db.table("notificacoes")\
            .select("periodo_dias, views_atingidas")\
            .eq("video_id", video_id)\
            .eq("vista", True)\
            .execute()

        if not response.data:
            return False  # Nunca foi visto

        # Verificar se já viu um marco maior ou igual
        for notif in response.data:
            # Buscar regra anterior
            regra_anterior = await self.get_regra_by_periodo(notif['periodo_dias'])

            if regra_anterior:
                # Se regra anterior é maior ou igual, não notificar
                if regra_anterior['views_minimas'] >= regra_atual['views_minimas']:
                    logger.debug(f"Video '{video_id}' ja visto em marco maior/igual: {regra_anterior['views_minimas']} >= {regra_atual['views_minimas']}")
                    return True

        # Se chegou aqui, todas as notificações vistas são de marcos menores
        return False

    except Exception as e:
        logger.error(f"Erro ao verificar se video ja foi visto: {e}")
        return False
```

#### 3. cleanup_duplicate_notifications()

**Linhas:** 229-253

```python
async def cleanup_duplicate_notifications(self, video_id: str):
    """
    Remove notificações duplicadas não vistas do mesmo vídeo.
    Mantém apenas a mais recente.

    Executado ANTES de processar cada vídeo.
    """
    try:
        # Buscar todas notificações não vistas do vídeo
        response = self.db.table("notificacoes")\
            .select("id, created_at")\
            .eq("video_id", video_id)\
            .eq("vista", False)\
            .order("created_at.desc")\
            .execute()

        if response.data and len(response.data) > 1:
            # Manter apenas a mais recente, deletar as outras
            ids_to_delete = [n['id'] for n in response.data[1:]]

            for notif_id in ids_to_delete:
                self.db.table("notificacoes").delete().eq("id", notif_id).execute()

            logger.info(f"🧹 Removidas {len(ids_to_delete)} notificações duplicadas do vídeo")

    except Exception as e:
        logger.error(f"Erro ao limpar notificações duplicadas: {e}")
```

### Fluxo Visual

```
┌─────────────────────────────────────────────────────────────┐
│ VIDEO_ID = "abc123"                                         │
│                                                             │
│ Notificações no banco:                                     │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ ID  │ MARCO  │ VISTA │ CREATED_AT                   │   │
│ ├─────┼────────┼───────┼─────────────────────────────┤   │
│ │ 1   │ 10k/24h│ True  │ 2025-01-01 10:00            │   │
│ │ 2   │ 50k/7d │ False │ 2025-01-05 15:00            │   │
│ │ 3   │ 50k/7d │ False │ 2025-01-05 16:00 (duplicata)│   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ Processamento:                                              │
│ 1. cleanup_duplicate_notifications("abc123")                │
│    → Remove ID 3 (duplicata de ID 2)                        │
│                                                             │
│ 2. get_unread_notification("abc123")                        │
│    → Retorna ID 2 (50k/7d, não vista)                       │
│                                                             │
│ 3. Nova regra: 100k/30d                                     │
│    - 100k > 50k? → SIM                                      │
│    - Ação: UPDATE ID 2 para 100k/30d                        │
│                                                             │
│ 4. video_already_seen("abc123", regra_10k)                  │
│    - Tem notificação vista? → SIM (ID 1: 10k)              │
│    - 10k >= 100k? → NÃO                                     │
│    - Retorno: False (pode notificar marco maior)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Regras de Notificação

### Tabela: regras_notificacoes

**Schema:**
```sql
CREATE TABLE regras_notificacoes (
    id SERIAL PRIMARY KEY,
    nome_regra VARCHAR(255) NOT NULL,          -- Ex: "10k em 24h"
    views_minimas INT NOT NULL,                -- Ex: 10000
    periodo_dias INT NOT NULL,                 -- Ex: 1 (24h)
    tipo_canal VARCHAR(50) DEFAULT 'ambos',    -- 'nosso', 'minerado', 'ambos'
    subnichos TEXT[],                          -- Array de subnichos (opcional)
    ativa BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Buscar Regras Ativas

**Linhas:** 130-144

```python
async def get_regras_ativas_ordenadas(self) -> List[Dict]:
    """
    Busca regras ativas ORDENADAS por views_minimas (hierarquia).
    Menor para maior: 15k → 50k → 100k → 150k

    Importante: Ordem é CRUCIAL para lógica de elevação funcionar!
    """
    try:
        response = self.db.table("regras_notificacoes")\
            .select("*")\
            .eq("ativa", True)\
            .order("views_minimas")\
            .execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Erro ao buscar regras ativas: {e}")
        return []
```

### Regras Padrão (Exemplo)

```python
# Inserir via endpoint POST /api/regras-notificacoes
regras_exemplo = [
    {
        "nome_regra": "10k em 24 horas",
        "views_minimas": 10000,
        "periodo_dias": 1,
        "tipo_canal": "ambos",
        "subnichos": None,  # Todos os subnichos
        "ativa": True
    },
    {
        "nome_regra": "50k em 7 dias",
        "views_minimas": 50000,
        "periodo_dias": 7,
        "tipo_canal": "ambos",
        "subnichos": None,
        "ativa": True
    },
    {
        "nome_regra": "100k em 30 dias - Terror",
        "views_minimas": 100000,
        "periodo_dias": 30,
        "tipo_canal": "minerado",
        "subnichos": ["Terror", "Histórias Sombrias"],  # Apenas esses subnichos
        "ativa": True
    }
]
```

### Buscar Vídeos que Atingiram Marco

**Linhas:** 297-381

```python
async def get_videos_that_hit_milestone(self, regra: Dict) -> List[Dict]:
    """
    Busca videos que atingiram o marco especificado na regra.

    Otimizado:
    - Usa apenas entrada mais recente de cada vídeo (evita duplicatas)
    - Suporta filtro por múltiplos subnichos
    - Filtro case-insensitive

    Passos:
    1. Buscar TODOS os dados de uma vez (query JOIN com canais)
    2. Agrupar por video_id e pegar apenas entrada mais recente
    3. Filtrar por subnichos (se especificado na regra)
    """
    try:
        logger.info(f"🔍 Buscando videos para regra: {regra['nome_regra']} ({regra['views_minimas']} views em {regra['periodo_dias']}d)")

        # Calcular data de corte
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=regra['periodo_dias'])).isoformat()
        logger.info(f"📅 Data de corte: {cutoff_date[:10]}")

        # PASSO 1: Buscar TODOS os dados de uma vez (mais eficiente)
        # JOIN com canais_monitorados para ter subnicho/lingua
        query = self.db.table("videos_historico").select(
            "video_id, titulo, views_atuais, data_publicacao, data_coleta, canal_id, canais_monitorados!inner(tipo, nome_canal, subnicho)"
        ).gte("data_publicacao", cutoff_date).gte("views_atuais", regra['views_minimas'])

        # Filtrar por tipo de canal se necessario
        tipo_canal = regra.get('tipo_canal', 'ambos')
        if tipo_canal != 'ambos':
            query = query.eq("canais_monitorados.tipo", tipo_canal)

        response = query.execute()
        logger.info(f"📊 Total de entradas encontradas (pode ter duplicatas): {len(response.data) if response.data else 0}")

        if not response.data:
            logger.info("❌ Nenhum video encontrado na query inicial")
            return []

        # PASSO 2: Agrupar por video_id e pegar apenas a entrada mais recente
        videos_map = {}  # {video_id: entrada_completa_mais_recente}

        for item in response.data:
            video_id = item['video_id']
            data_coleta = item['data_coleta']

            # Se video_id já existe, comparar datas
            if video_id in videos_map:
                if data_coleta > videos_map[video_id]['data_coleta']:
                    videos_map[video_id] = item  # Substituir por mais recente
            else:
                videos_map[video_id] = item

        logger.info(f"🔢 Videos unicos (apos agrupar por mais recente): {len(videos_map)}")

        # PASSO 3: Filtrar por subnichos (views ja foi filtrado na query)
        videos = []
        videos_filtrados_subnicho = 0

        for video_id, item in videos_map.items():
            canal_info = item.get('canais_monitorados', {})
            video_subnicho = canal_info.get('subnicho', '').strip()

            # Filtrar por subnichos da regra (normalizado e case-insensitive)
            if regra.get('subnichos'):
                # Normalizar subnichos da regra
                regra_subnichos_normalized = [s.strip() for s in regra['subnichos']]

                # Verificar se subnicho do video esta na lista (case-insensitive)
                if not any(video_subnicho.lower() == rs.lower() for rs in regra_subnichos_normalized):
                    videos_filtrados_subnicho += 1
                    logger.debug(f"⏭️ Video '{item['titulo'][:40]}...' filtrado por subnicho: '{video_subnicho}' não está em {regra['subnichos']}")
                    continue

            videos.append({
                'video_id': item['video_id'],
                'titulo': item['titulo'],
                'canal_id': item['canal_id'],
                'nome_canal': canal_info.get('nome_canal', 'Unknown'),
                'tipo_canal': canal_info.get('tipo', 'minerado'),
                'views_atuais': item['views_atuais'],
                'data_publicacao': item['data_publicacao']
            })

        logger.info(f"✅ Videos que passaram filtros: {len(videos)}")
        logger.info(f"📉 Filtrados por subnicho: {videos_filtrados_subnicho}")

        return videos

    except Exception as e:
        logger.error(f"Erro ao buscar videos que atingiram marco: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
```

---

## Workflow do Arthur

### 1. Notificação Criada

```
Sistema → Banco de dados:
INSERT INTO notificacoes (
    video_id,
    nome_video,
    nome_canal,
    views_atingidas,
    periodo_dias,
    tipo_alerta,
    mensagem,
    vista
) VALUES (
    'dQw4w9WgXcQ',
    'How to Make Pizza',
    'Cooking Channel',
    10500,
    1,
    '10k_1d',
    'O video "How to Make Pizza" do canal Cooking Channel atingiu 10.5k views nas ultimas 24 horas',
    false
);
```

### 2. Arthur Acessa Dashboard

```
GET /api/notificacoes
```

**Response:**
```json
{
  "notificacoes": [
    {
      "id": 123,
      "video_id": "dQw4w9WgXcQ",
      "nome_video": "How to Make Pizza",
      "nome_canal": "Cooking Channel",
      "views_atingidas": 10500,
      "periodo_dias": 1,
      "tipo_alerta": "10k_1d",
      "mensagem": "O video 'How to Make Pizza' do canal Cooking Channel atingiu 10.5k views nas ultimas 24 horas",
      "vista": false,
      "tipo_canal": "minerado",
      "data_disparo": "2025-01-12T10:30:00Z"
    }
  ],
  "total": 1
}
```

### 3. Arthur Analisa Vídeo

```
1. Acessar link do vídeo (youtube.com/watch?v=dQw4w9WgXcQ)
2. Verificar título, thumbnail, descrição
3. Decidir se vale adaptar para nossos canais
4. Se sim: anotar ideia para produção
```

### 4. Arthur Marca como Vista

```
PUT /api/notificacoes/123/marcar-vista
```

**Response:**
```json
{
  "message": "Notificação marcada como vista",
  "notif_id": 123
}
```

### 5. Banco de Dados Atualizado

```sql
UPDATE notificacoes
SET vista = true
WHERE id = 123;
```

---

## Integração com main.py

### Importação

**main.py, linhas 21-22:**
```python
from notifier import NotificationChecker

notifier = NotificationChecker(db.supabase)
```

### Execução Automática

**main.py, função run_collection_job():**
```python
async def run_collection_job():
    try:
        # 1. Criar registro de coleta
        coleta_id = await db.create_coleta_record()

        # 2. Coletar dados dos canais
        collector.reset_for_new_collection()
        canais = await db.get_active_canais()

        for canal in canais:
            canal_data = await collector.get_canal_data(canal['url_canal'], canal['nome_canal'])
            if canal_data:
                await db.save_canal_stats(canal['id'], canal_data)

        # 3. Coletar vídeos
        for canal in canais:
            videos = await collector.get_videos_data(canal['url_canal'], canal['nome_canal'])
            if videos:
                await db.save_videos(canal['id'], videos)

        # 4. ✅ EXECUTAR NOTIFIER (AQUI!)
        logger.info("🔔 Executando notifier...")
        await notifier.check_and_create_notifications()

        # 5. Finalizar coleta
        await db.complete_coleta_record(coleta_id)

    except Exception as e:
        logger.error(f"❌ Erro na coleta: {e}")
```

### Endpoint Manual

**main.py, linhas 713-739:**
```python
@app.post("/api/force-notifier")
async def force_notifier():
    """
    Força execução do notifier manualmente.
    Útil para: testes, debug, ou recuperar notificações perdidas.
    """
    try:
        logger.info("🔔 FORÇANDO EXECUÇÃO DO NOTIFIER (manual)")

        # Importar e executar o notifier
        from notifier import NotificationChecker

        checker = NotificationChecker(db.supabase)
        await checker.check_and_create_notifications()

        logger.info("✅ Notifier executado com sucesso!")

        return {
            "status": "success",
            "message": "Notificador executado com sucesso! Verifique as notificações."
        }

    except Exception as e:
        logger.error(f"❌ Erro ao executar notifier: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Configuração de Regras

### Criar Regra (via API)

```bash
POST /api/regras-notificacoes
Content-Type: application/json

{
  "nome_regra": "15k em 3 dias - Terror",
  "views_minimas": 15000,
  "periodo_dias": 3,
  "tipo_canal": "minerado",
  "subnichos": ["Terror", "Histórias Sombrias"],
  "ativa": true
}
```

### Listar Regras

```bash
GET /api/regras-notificacoes
```

**Response:**
```json
{
  "regras": [
    {
      "id": 1,
      "nome_regra": "10k em 24 horas",
      "views_minimas": 10000,
      "periodo_dias": 1,
      "tipo_canal": "ambos",
      "subnichos": null,
      "ativa": true,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "nome_regra": "50k em 7 dias",
      "views_minimas": 50000,
      "periodo_dias": 7,
      "tipo_canal": "ambos",
      "subnichos": null,
      "ativa": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

### Atualizar Regra

```bash
PUT /api/regras-notificacoes/2
Content-Type: application/json

{
  "nome_regra": "50k em 7 dias - ATUALIZADA",
  "views_minimas": 45000,
  "periodo_dias": 7,
  "tipo_canal": "minerado",
  "subnichos": ["Terror"],
  "ativa": true
}
```

### Deletar Regra

```bash
DELETE /api/regras-notificacoes/2
```

---

## Troubleshooting

### Problema 1: Notificações duplicadas

**Sintoma:**
```
Mesmo vídeo aparece múltiplas vezes nas notificações não vistas
```

**Causa:**
- Bug no cleanup_duplicate_notifications
- Múltiplas execuções simultâneas do notifier

**Solução:**
```python
# 1. Limpar manualmente via SQL:
DELETE FROM notificacoes
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY video_id, vista ORDER BY created_at DESC) as rn
        FROM notificacoes
    ) t
    WHERE rn > 1 AND vista = false
);

# 2. Forçar cleanup:
POST /api/force-notifier
```

### Problema 2: Vídeo não notificou

**Sintoma:**
```
Vídeo atingiu 10k views mas não apareceu nas notificações
```

**Causas possíveis:**
1. Regra inativa
2. Subnicho filtrado
3. Tipo de canal errado
4. Vídeo já foi visto em marco maior

**Debug:**
```python
# 1. Verificar regras ativas:
GET /api/regras-notificacoes

# 2. Buscar vídeo no histórico:
SELECT vh.*, cm.subnicho, cm.tipo
FROM videos_historico vh
JOIN canais_monitorados cm ON vh.canal_id = cm.id
WHERE vh.video_id = 'VIDEO_ID_AQUI'
ORDER BY vh.data_coleta DESC
LIMIT 1;

# 3. Verificar se já tem notificação:
SELECT * FROM notificacoes WHERE video_id = 'VIDEO_ID_AQUI';

# 4. Forçar notifier manualmente:
POST /api/force-notifier
```

### Problema 3: Notificação não atualiza

**Sintoma:**
```
Vídeo atingiu 50k mas notificação continua mostrando 10k
```

**Causa:**
- Notificação foi marcada como vista
- Bug na lógica de elevação

**Solução:**
```python
# 1. Verificar status da notificação:
SELECT * FROM notificacoes WHERE video_id = 'VIDEO_ID_AQUI';

# Se vista = true:
# - Sistema não atualiza notificações vistas
# - Arthur já viu a notificação de 10k
# - Quando atingir 50k, criará NOVA notificação

# Se vista = false:
# - Deveria ter atualizado
# - Forçar notifier novamente:
POST /api/force-notifier
```

### Problema 4: Muitas notificações

**Sintoma:**
```
100+ notificações não vistas acumuladas
```

**Causa:**
- Arthur não está marcando como vista
- Regras muito abrangentes (ex: 1k views)

**Solução:**
```bash
# 1. Marcar todas como vistas (por filtro):
POST /api/notificacoes/marcar-todas?lingua=português&subnicho=Terror

# 2. Ajustar regras (aumentar threshold):
PUT /api/regras-notificacoes/1
{
  "views_minimas": 20000,  # Em vez de 10000
  ...
}

# 3. Adicionar filtro de subnicho:
PUT /api/regras-notificacoes/1
{
  "subnichos": ["Terror", "Histórias Sombrias"],  # Apenas esses
  ...
}
```

### Problema 5: Notifier não executa

**Sintoma:**
```
Coleta termina mas notifier não roda
```

**Causa:**
- Erro na coleta (interrompe antes do notifier)
- Exception no notifier

**Debug:**
```bash
# 1. Ver logs da coleta:
GET /api/coletas/historico

# 2. Executar notifier manualmente:
POST /api/force-notifier

# 3. Ver logs do servidor:
# Railway > Deploy > Logs
# Procurar por:
# - "🔔 Executando notifier..."
# - "INICIANDO VERIFICACAO DE NOTIFICACOES"
# - Erros/exceptions
```

---

## Exemplo Completo

### Setup Inicial

```python
# 1. Criar regras via API
import requests

regras = [
    {
        "nome_regra": "10k em 24 horas",
        "views_minimas": 10000,
        "periodo_dias": 1,
        "tipo_canal": "ambos",
        "subnichos": None,
        "ativa": True
    },
    {
        "nome_regra": "50k em 7 dias",
        "views_minimas": 50000,
        "periodo_dias": 7,
        "tipo_canal": "ambos",
        "subnichos": None,
        "ativa": True
    }
]

for regra in regras:
    response = requests.post(
        "https://youtube-dashboard.railway.app/api/regras-notificacoes",
        json=regra
    )
    print(response.json())
```

### Workflow Completo

```python
# 1. Coletar dados
POST /api/collect-data
# → Sistema coleta canais + vídeos
# → Executa notifier automaticamente

# 2. Arthur verifica notificações
GET /api/notificacoes
# → Lista todas não vistas

# 3. Arthur marca como vista
PUT /api/notificacoes/123/marcar-vista

# 4. Próxima coleta
# → Mesmo vídeo atinge 50k
# → Sistema cria NOVA notificação (10k foi visto)
```

---

## Referências

**Arquivos relacionados:**
- `D:\ContentFactory\youtube-dashboard-backend\main.py` - Integração
- `D:\ContentFactory\youtube-dashboard-backend\database.py` - Queries
- `D:\ContentFactory\youtube-dashboard-backend\collector.py` - Coleta os vídeos

**Tabelas do banco:**
- `regras_notificacoes` - Configuração de regras
- `notificacoes` - Notificações criadas
- `videos_historico` - Dados dos vídeos
- `canais_monitorados` - Metadados dos canais

**Ver também:**
- `05_DATABASE_SCHEMA.md` - Schema completo
- `06_YOUTUBE_COLLECTOR.md` - Como vídeos são coletados
- `08_API_ENDPOINTS_COMPLETA.md` - Todos os endpoints

---

**Última atualização:** 12/01/2026
**Versão notifier.py:** 449 linhas (sistema anti-duplicação completo)
