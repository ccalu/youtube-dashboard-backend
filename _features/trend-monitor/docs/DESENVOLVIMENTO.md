# Guia de Desenvolvimento

## Ambiente de Desenvolvimento

### Setup Inicial

```bash
# Clonar projeto
git clone <repo>
cd trend-monitor

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env
# Editar .env
```

### Executar em Modo Dev

```bash
# Usar dados mock (nao consome APIs)
python main.py --mock

# Apenas coleta (debug de APIs)
python main.py --collect-only

# Apenas gera dashboard (debug de HTML)
python main.py --generate-only
```

---

## Estrutura do Codigo

### main.py - Orquestrador

```python
class TrendMonitor:
    def __init__(self, use_mock=False)
    def collect_all() -> Dict        # Fase 1: Coleta
    def filter_and_score() -> Dict   # Fase 2: Filtragem
    def generate_dashboard() -> str   # Fase 3: Geracao
    def run() -> Dict                 # Executa tudo
```

### collectors/ - Coletores

Cada coletor implementa:
```python
class XxxCollector:
    def __init__(self)
    def collect_country(country: str) -> List[Dict]
    def collect_all_countries() -> Dict[str, List]
```

### filters/ - Filtros

```python
class RelevanceFilter:
    def calculate_score(trend: Dict, subnicho: str) -> int
    def filter_by_subnicho(trends: List) -> Dict
    def filter_all_trends(data: Dict) -> Dict
```

### generators/ - Geradores

```python
class HTMLReportGenerator:
    def __init__(self)
    def generate(data: Dict, output_path: str) -> str
```

---

## Adicionar Novo Coletor

### 1. Criar arquivo

`collectors/nova_fonte.py`:
```python
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class NovaFonteCollector:
    def __init__(self):
        # Inicializar cliente da API
        pass

    def collect_all(self) -> Dict[str, List[Dict]]:
        """Coleta dados da nova fonte"""
        results = {}

        # Implementar coleta
        trends = self._fetch_trends()

        for trend in trends:
            results.setdefault("global", []).append({
                "title": trend["title"],
                "url": trend["url"],
                "volume": trend.get("score", 0),
                "source": "nova_fonte"
            })

        return results

    def _fetch_trends(self) -> List[Dict]:
        # Chamar API
        pass


def get_mock_nova_fonte_data() -> Dict:
    """Dados mock para testes"""
    return {
        "global": [
            {"title": "Mock Trend 1", "url": "https://...", "volume": 100},
            {"title": "Mock Trend 2", "url": "https://...", "volume": 80},
        ]
    }
```

### 2. Registrar em __init__.py

`collectors/__init__.py`:
```python
from .nova_fonte import NovaFonteCollector
```

### 3. Integrar no main.py

```python
from collectors import NovaFonteCollector

class TrendMonitor:
    def __init__(self):
        # ...
        self.nova_fonte_collector = NovaFonteCollector()

    def collect_all(self):
        # ...
        data["nova_fonte"] = self.nova_fonte_collector.collect_all()
```

---

## Modificar Score de Relevancia

### Arquivo: filters/relevance.py

```python
def calculate_score(self, trend: Dict, keywords: List[str]) -> int:
    score = 0
    title = trend.get("title", "").lower()

    # Match de keywords
    for keyword in keywords:
        if keyword.lower() in title:
            score += 20  # Ajustar peso aqui

    # Bonus por volume
    volume = trend.get("volume", 0)
    if volume > 100000:
        score += 10
    if volume > 500000:
        score += 10

    # Bonus cross-platform (implementar se necessario)

    return min(score, 100)
```

---

## Modificar Template HTML

### Arquivo: templates/dashboard.html

Template usa Jinja2:
```html
{% for source, countries in trends_by_source.items() %}
    <div class="source-section">
        <h2>{{ source | upper }}</h2>
        {% for country, trends in countries.items() %}
            <h3>{{ country }}</h3>
            {% for trend in trends %}
                <div class="trend-card">
                    {{ trend.title }}
                </div>
            {% endfor %}
        {% endfor %}
    </div>
{% endfor %}
```

### Variaveis Disponiveis

```python
{
    "trends_by_source": {...},      # Aba GERAL
    "trends_by_subnicho": {...},    # Aba DIRECIONADO
    "stats": {...},                 # Estatisticas
    "evergreen_trends": [...],      # Trends persistentes
    "metadata": {...}               # Data, timestamp, etc
}
```

---

## Testes

### Rodar Testes (se existirem)

```bash
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/test_collectors.py  # Arquivo especifico
```

### Criar Teste para Novo Coletor

`tests/test_nova_fonte.py`:
```python
import pytest
from collectors.nova_fonte import NovaFonteCollector, get_mock_nova_fonte_data

def test_mock_data():
    data = get_mock_nova_fonte_data()
    assert "global" in data
    assert len(data["global"]) > 0

def test_collector_init():
    collector = NovaFonteCollector()
    assert collector is not None
```

---

## Deploy

### Railway (Recomendado)

1. Criar projeto no Railway
2. Conectar repositorio GitHub
3. Configurar variaveis de ambiente
4. Deploy automatico em push

### Cron Job Local

```bash
# Editar crontab
crontab -e

# Adicionar (roda todo dia as 6h)
0 6 * * * cd /path/to/trend-monitor && /path/to/venv/bin/python main.py >> /var/log/trend-monitor.log 2>&1
```

### GitHub Actions

`.github/workflows/collect.yml`:
```yaml
name: Collect Trends
on:
  schedule:
    - cron: '0 6 * * *'  # 6h UTC
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

---

## Debug

### Logs

```bash
# Ver logs em tempo real
python main.py 2>&1 | tee debug.log

# Nivel de log (editar main.py)
logging.basicConfig(level=logging.DEBUG)
```

### Verificar APIs

```python
# Teste rapido de API
python -c "
from collectors.youtube import YouTubeCollector
yt = YouTubeCollector()
print(yt.collect_country('BR')[:3])
"
```

### Verificar Banco

```bash
# SQLite
sqlite3 data/trends.db "SELECT COUNT(*) FROM trends"

# Supabase
# Ver no dashboard web
```

---

## Contribuindo

1. Criar branch: `git checkout -b feature/nova-funcionalidade`
2. Fazer alteracoes
3. Testar: `python main.py --mock`
4. Commit: `git commit -m "Add: nova funcionalidade"`
5. Push: `git push origin feature/nova-funcionalidade`
6. Abrir Pull Request
