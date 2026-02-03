"""
TREND MONITOR - Configuracao Central
=====================================
Arquivo de configuracao com todos os parametros do sistema.
Modifique aqui para adicionar novos paises, subnichos ou keywords.
"""

import os
from datetime import datetime

# Carregar variaveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar .env do diretorio do projeto (onde config.py esta)
    import pathlib
    env_path = pathlib.Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv nao instalado, usar variaveis do sistema

# =============================================================================
# CONFIGURACAO SUPABASE (Banco de dados na nuvem)
# =============================================================================

SUPABASE_CONFIG = {
    "url": os.getenv("SUPABASE_URL"),
    "key": os.getenv("SUPABASE_KEY"),
    "enabled": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
}

# =============================================================================
# CONFIGURAÇÃO DE PAÍSES E IDIOMAS
# =============================================================================

COUNTRIES = {
    "US": {
        "name": "Estados Unidos",
        "flag": "🇺🇸",
        "language": "en",
        "google_geo": "US",
        "youtube_region": "US",
        "reddit_subs": ["all", "videos", "Documentaries", "todayilearned"],
        "timezone": "America/New_York"
    },
    "BR": {
        "name": "Brasil",
        "flag": "🇧🇷",
        "language": "pt",
        "google_geo": "BR",
        "youtube_region": "BR",
        "reddit_subs": ["brasil", "portugal", "desabafos", "eu_nvr"],
        "timezone": "America/Sao_Paulo"
    },
    "ES": {
        "name": "Espanha",
        "flag": "🇪🇸",
        "language": "es",
        "google_geo": "ES",
        "youtube_region": "ES",
        "reddit_subs": ["spain", "mexico", "argentina", "espanol"],
        "timezone": "Europe/Madrid"
    },
    "FR": {
        "name": "França",
        "flag": "🇫🇷",
        "language": "fr",
        "google_geo": "FR",
        "youtube_region": "FR",
        "reddit_subs": ["france", "Quebec", "rance"],
        "timezone": "Europe/Paris"
    },
    "KR": {
        "name": "Coreia do Sul",
        "flag": "🇰🇷",
        "language": "ko",
        "google_geo": "KR",
        "youtube_region": "KR",
        "reddit_subs": ["korea", "hanguk", "kpop"],
        "timezone": "Asia/Seoul"
    },
    "JP": {
        "name": "Japão",
        "flag": "🇯🇵",
        "language": "ja",
        "google_geo": "JP",
        "youtube_region": "JP",
        "reddit_subs": ["japan", "newsokur", "japanlife"],
        "timezone": "Asia/Tokyo"
    },
    "IT": {
        "name": "Itália",
        "flag": "🇮🇹",
        "language": "it",
        "google_geo": "IT",
        "youtube_region": "IT",
        "reddit_subs": ["italy", "Italia"],
        "timezone": "Europe/Rome"
    }
}

# =============================================================================
# SUBNICHOS E KEYWORDS PARA FILTRAGEM
# =============================================================================

SUBNICHO_CONFIG = {
    # === SUBNICHOS ATUAIS (7) - Produção ativa ===
    "relatos_guerra": {
        "name": "Relatos de Guerra",
        "icon": "⚔️",
        "description": "Histórias de soldados, veteranos e sobreviventes de guerra",
        "active": True,
        "keywords": {
            "en": ["war story", "soldier", "veteran", "combat", "battlefield",
                   "wwii story", "military tale", "war survivor", "troop",
                   "front line", "war hero", "battle story", "military history",
                   "war documentary", "war memoir"],
            "pt": ["história de guerra", "soldado", "veterano", "combate",
                   "campo de batalha", "sobrevivente", "militar", "guerra mundial",
                   "herói de guerra", "batalha"],
            "es": ["historia de guerra", "soldado", "veterano", "combate",
                   "batalla", "superviviente", "militar", "héroe"],
            "fr": ["histoire de guerre", "soldat", "vétéran", "combat",
                   "bataille", "survivant", "militaire", "héros"],
            "ko": ["전쟁 이야기", "군인", "참전용사", "전투", "전쟁"],
            "ja": ["戦争物語", "兵士", "退役軍人", "戦闘", "戦争"],
            "it": ["storia di guerra", "soldato", "veterano", "combattimento",
                   "battaglia", "sopravvissuto", "militare", "eroe"]
        }
    },

    "guerras_civilizacoes": {
        "name": "Guerras e Civilizações",
        "icon": "🏛️",
        "description": "Impérios, batalhas históricas e civilizações antigas",
        "active": True,
        "keywords": {
            "en": ["war", "battle", "empire", "civilization", "ancient", "roman",
                   "greek", "mongol", "conquest", "invasion", "dynasty", "kingdom",
                   "emperor", "fall of rome", "ancient egypt", "ottoman", "viking",
                   "medieval", "crusade", "alexander the great"],
            "pt": ["guerra", "batalha", "império", "civilização", "antigo", "romano",
                   "grego", "mongol", "conquista", "invasão", "dinastia", "reino",
                   "imperador", "egito antigo", "medieval", "cruzada"],
            "es": ["guerra", "batalla", "imperio", "civilización", "antiguo",
                   "romano", "griego", "conquista", "invasión", "dinastía", "reino"],
            "fr": ["guerre", "bataille", "empire", "civilisation", "ancien",
                   "romain", "grec", "conquête", "invasion", "dynastie", "royaume"],
            "ko": ["전쟁", "전투", "제국", "문명", "고대", "로마", "정복"],
            "ja": ["戦争", "戦い", "帝国", "文明", "古代", "ローマ", "征服"],
            "it": ["guerra", "battaglia", "impero", "civiltà", "antico",
                   "romano", "greco", "conquista", "invasione", "dinastia"]
        }
    },

    "empreendedorismo": {
        "name": "Empreendedorismo",
        "icon": "💼",
        "description": "Startups, negócios, histórias de sucesso empresarial",
        "active": True,
        "keywords": {
            "en": ["entrepreneur", "startup", "business", "success", "millionaire",
                   "ceo", "founder", "company", "hustle", "wealth", "rich",
                   "billionaire", "self-made", "business story", "how he built",
                   "from zero to", "rags to riches", "net worth"],
            "pt": ["empreendedor", "startup", "negócio", "sucesso", "milionário",
                   "fundador", "empresa", "riqueza", "bilionário", "história de sucesso"],
            "es": ["emprendedor", "startup", "negocio", "éxito", "millonario",
                   "fundador", "empresa", "riqueza", "billonario"],
            "fr": ["entrepreneur", "startup", "entreprise", "succès", "millionnaire",
                   "fondateur", "richesse", "milliardaire"],
            "ko": ["기업가", "스타트업", "사업", "성공", "백만장자", "창업자"],
            "ja": ["起業家", "スタートアップ", "ビジネス", "成功", "億万長者", "創業者"],
            "it": ["imprenditore", "startup", "business", "successo", "milionario",
                   "fondatore", "azienda", "ricchezza", "miliardario"]
        }
    },

    "terror": {
        "name": "Terror",
        "icon": "👻",
        "description": "Horror, paranormal, histórias assustadoras",
        "active": True,
        "keywords": {
            "en": ["horror", "scary", "creepy", "haunted", "ghost", "paranormal",
                   "demon", "possessed", "nightmare", "terrifying", "sinister",
                   "supernatural", "evil spirit", "poltergeist", "exorcism",
                   "haunted house", "true horror", "real ghost"],
            "pt": ["terror", "assustador", "assombrado", "fantasma", "paranormal",
                   "demônio", "possuído", "pesadelo", "sobrenatural", "espírito",
                   "exorcismo", "casa assombrada", "história real de terror"],
            "es": ["terror", "miedo", "embrujado", "fantasma", "paranormal",
                   "demonio", "poseído", "pesadilla", "sobrenatural"],
            "fr": ["horreur", "effrayant", "hanté", "fantôme", "paranormal",
                   "démon", "possédé", "cauchemar", "surnaturel"],
            "ko": ["공포", "무서운", "귀신", "유령", "악마", "초자연적"],
            "ja": ["ホラー", "怖い", "幽霊", "お化け", "悪魔", "超自然"],
            "it": ["horror", "spaventoso", "infestato", "fantasma", "paranormale",
                   "demone", "posseduto", "incubo", "soprannaturale"]
        }
    },

    "misterios": {
        "name": "Mistérios",
        "icon": "🔍",
        "description": "Casos não resolvidos, enigmas, conspiracções",
        "active": True,
        "keywords": {
            "en": ["mystery", "unexplained", "unsolved", "strange", "bizarre",
                   "conspiracy", "secret", "hidden", "unknown", "enigma", "puzzle",
                   "cold case", "disappearance", "true crime", "investigation",
                   "unsolved mystery", "what happened to", "mysterious death"],
            "pt": ["mistério", "inexplicável", "não resolvido", "estranho",
                   "conspiração", "secreto", "oculto", "desconhecido", "enigma",
                   "caso não resolvido", "desaparecimento", "crime real"],
            "es": ["misterio", "inexplicable", "sin resolver", "extraño",
                   "conspiración", "secreto", "oculto", "enigma"],
            "fr": ["mystère", "inexpliqué", "non résolu", "étrange",
                   "conspiration", "secret", "caché", "énigme"],
            "ko": ["미스터리", "설명할 수 없는", "미해결", "이상한", "음모"],
            "ja": ["ミステリー", "未解決", "謎", "不思議", "陰謀"],
            "it": ["mistero", "inspiegabile", "irrisolto", "strano",
                   "cospirazione", "segreto", "nascosto", "enigma"]
        }
    },

    "psicologia_mindset": {
        "name": "Psicologia e Mindset",
        "icon": "🧠",
        "description": "Comportamento humano, manipulação, vieses cognitivos",
        "active": True,
        "keywords": {
            "en": ["psychology", "mind", "brain", "behavior", "habit", "bias",
                   "mental", "cognitive", "manipulation", "influence", "emotion",
                   "personality", "narcissist", "psychopath", "dark psychology",
                   "how to read people", "body language", "mindset"],
            "pt": ["psicologia", "mente", "cérebro", "comportamento", "hábito",
                   "viés", "mental", "cognitivo", "manipulação", "influência",
                   "emoção", "narcisista", "psicopata", "linguagem corporal"],
            "es": ["psicología", "mente", "cerebro", "comportamiento", "hábito",
                   "sesgo", "mental", "cognitivo", "manipulación", "influencia"],
            "fr": ["psychologie", "esprit", "cerveau", "comportement", "habitude",
                   "biais", "mental", "cognitif", "manipulation", "influence"],
            "ko": ["심리학", "마음", "뇌", "행동", "습관", "편견", "조작"],
            "ja": ["心理学", "心", "脳", "行動", "習慣", "バイアス", "操作"],
            "it": ["psicologia", "mente", "cervello", "comportamento", "abitudine",
                   "pregiudizio", "mentale", "cognitivo", "manipolazione"]
        }
    },

    "historias_sombrias": {
        "name": "Histórias Sombrias",
        "icon": "💀",
        "description": "Reis cruéis, mitologia sombria, história perversa",
        "active": True,
        "keywords": {
            "en": ["dark history", "evil", "king", "queen", "mythology", "myth",
                   "legend", "tyrant", "cruel", "brutal", "twisted", "sinister",
                   "macabre", "torture", "execution", "mad king", "bloody",
                   "ruthless", "villain", "dark ages"],
            "pt": ["história sombria", "mal", "rei", "rainha", "mitologia", "mito",
                   "lenda", "tirano", "cruel", "brutal", "macabro", "tortura",
                   "execução", "rei louco", "sangrento", "vilão"],
            "es": ["historia oscura", "mal", "rey", "reina", "mitología", "mito",
                   "leyenda", "tirano", "cruel", "brutal", "macabro"],
            "fr": ["histoire sombre", "mal", "roi", "reine", "mythologie", "mythe",
                   "légende", "tyran", "cruel", "brutal", "macabre"],
            "ko": ["어두운 역사", "악", "왕", "왕비", "신화", "전설", "폭군"],
            "ja": ["暗い歴史", "悪", "王", "女王", "神話", "伝説", "暴君"],
            "it": ["storia oscura", "male", "re", "regina", "mitologia", "mito",
                   "leggenda", "tiranno", "crudele", "brutale", "macabro"]
        }
    },

    # === SUBNICHOS NOVOS (Candidatos) - Em análise ===
    "finance": {
        "name": "Finanças",
        "icon": "💰",
        "description": "Economia, mercados, crises financeiras",
        "active": False,  # Candidato - não ativo ainda
        "keywords": {
            "en": ["economy", "market", "crash", "bank", "inflation", "recession",
                   "money", "debt", "crisis", "stock", "bitcoin", "currency",
                   "financial collapse", "wall street", "federal reserve"],
            "pt": ["economia", "mercado", "crash", "banco", "inflação", "recessão",
                   "dinheiro", "dívida", "crise", "bolsa", "bitcoin"],
            "es": ["economía", "mercado", "crash", "banco", "inflación", "recesión"],
            "fr": ["économie", "marché", "crash", "banque", "inflation", "récession"],
            "ko": ["경제", "시장", "붕괴", "은행", "인플레이션", "불황"],
            "ja": ["経済", "市場", "暴落", "銀行", "インフレ", "不況"],
            "it": ["economia", "mercato", "crash", "banca", "inflazione", "recessione"]
        }
    },

    "geopolitics": {
        "name": "Geopolítica",
        "icon": "🌍",
        "description": "Conflitos internacionais, poder global",
        "active": False,
        "keywords": {
            "en": ["geopolitics", "china", "russia", "usa", "conflict", "sanction",
                   "nato", "alliance", "superpower", "territory", "diplomacy",
                   "cold war", "world war", "nuclear", "military power"],
            "pt": ["geopolítica", "china", "rússia", "eua", "conflito", "sanção",
                   "otan", "aliança", "superpotência", "território", "diplomacia"],
            "es": ["geopolítica", "china", "rusia", "eeuu", "conflicto", "sanción"],
            "fr": ["géopolitique", "chine", "russie", "usa", "conflit", "sanction"],
            "ko": ["지정학", "중국", "러시아", "미국", "분쟁", "제재"],
            "ja": ["地政学", "中国", "ロシア", "アメリカ", "紛争", "制裁"],
            "it": ["geopolitica", "cina", "russia", "usa", "conflitto", "sanzione"]
        }
    },

    "space": {
        "name": "Espaço",
        "icon": "🚀",
        "description": "NASA, SpaceX, astronomia, cosmos",
        "active": False,
        "keywords": {
            "en": ["nasa", "spacex", "mars", "moon", "asteroid", "planet",
                   "universe", "galaxy", "black hole", "alien", "cosmic",
                   "telescope", "space exploration", "astronaut", "rocket"],
            "pt": ["nasa", "spacex", "marte", "lua", "asteróide", "planeta",
                   "universo", "galáxia", "buraco negro", "alienígena", "cósmico"],
            "es": ["nasa", "spacex", "marte", "luna", "asteroide", "planeta"],
            "fr": ["nasa", "spacex", "mars", "lune", "astéroïde", "planète"],
            "ko": ["나사", "스페이스x", "화성", "달", "소행성", "행성"],
            "ja": ["nasa", "スペースx", "火星", "月", "小惑星", "惑星"],
            "it": ["nasa", "spacex", "marte", "luna", "asteroide", "pianeta"]
        }
    }
}

# =============================================================================
# CONFIGURAÇÃO DE COLETA
# =============================================================================

COLLECTION_CONFIG = {
    "trends_per_country": 50,           # Número de trends por país (Google Trends)
    "reddit_posts_per_sub": 30,         # Posts por subreddit
    "youtube_videos_per_country": 200,  # Vídeos por país (4 páginas × 50)
    "hackernews_stories": 500,          # Stories do Hacker News
    "max_trends_display": 30,           # Máximo para exibir no dashboard
    "history_days": 30,                 # Dias de histórico a manter
    "time_periods": ["24h", "7d", "15d", "30d"],  # Períodos de análise
}

# =============================================================================
# FILTROS DE QUALIDADE (por fonte)
# =============================================================================

QUALITY_FILTERS = {
    "youtube": {
        "min_duration": 180,           # >= 3 minutos
        "max_duration": 3600,          # <= 60 minutos
        "min_views": 10000,            # >= 10K views
        "min_engagement": 0.02,        # >= 2% likes/views
        "exclude_categories": [
            "10",  # Music
            "17",  # Sports
            "20",  # Gaming
        ],
        "exclude_keywords": [
            "music video", "official video", "lyric", "lyrics",
            "highlights", "goals", "match", "vs",
            "gameplay", "walkthrough", "let's play", "gaming"
        ]
    },
    "google_trends": {
        "min_volume": 10000,           # >= 10K buscas
        "exclude_keywords": [
            # Celebridades/fofoca
            "kardashian", "celebrity", "divorce", "wedding", "dating",
            # Esportes
            "score", "game", "match", "vs", "fifa", "nfl", "nba",
            # Entretenimento genérico
            "movie release", "netflix", "premiere", "trailer"
        ],
        "prefer_keywords": [
            # Relevantes para subnichos
            "history", "mystery", "documentary", "story",
            "explained", "what happened", "truth about"
        ]
    },
    "hackernews": {
        "min_score": 50,               # >= 50 pontos
        "min_comments": 10,            # >= 10 comentários
        "exclude_domains": [
            "youtube.com",             # Já coletamos direto do YouTube
        ],
        "prefer_topics": [
            "ai", "startup", "founder", "business",
            "psychology", "history", "science",
            "documentary", "investigation"
        ],
        "exclude_topics": [
            # Dev muito técnico (não relevante para os canais)
            "rust", "golang", "typescript", "kubernetes",
            "docker", "aws", "azure", "terraform"
        ]
    }
}

# =============================================================================
# REGRAS DE EXIBIÇÃO DO DASHBOARD
# =============================================================================

DISPLAY_RULES = {
    # Top por Subnicho
    "subnicho_top": 10,           # Top 10 por subnicho (colapsável)
    "subnicho_min_score": 60,     # Score mínimo para aparecer

    # Top por Língua
    "language_top": 10,           # Top 10 por língua (colapsável)
    "language_min_score": 50,     # Score mínimo

    # Bombando (evergreen)
    "bombando_min_days": 3,       # Mínimo 3 dias ativos
    "bombando_per_page": 10,      # 10 por página

    # Lista Geral
    "general_per_page": 20,       # 20 por página
    "general_min_score": 50,      # Score mínimo para aparecer

    # Ordenação padrão
    "default_order": "quality_score DESC, volume DESC"
}

# =============================================================================
# CONFIGURAÇÃO DE APIs
# =============================================================================

API_CONFIG = {
    "youtube": {
        "api_key": os.environ.get("YOUTUBE_API_KEY", ""),
        "quota_daily": 10000,
        "requests_per_second": 1
    },
    "reddit": {
        "client_id": os.environ.get("REDDIT_CLIENT_ID", ""),
        "client_secret": os.environ.get("REDDIT_CLIENT_SECRET", ""),
        "user_agent": "TrendMonitor/1.0 (Content Factory Research Bot)"
    },
    "google_trends": {
        "requests_per_hour": 100,
        "timeout": 30
    }
}

# =============================================================================
# CONFIGURAÇÃO DE PATHS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Criar diretórios se não existirem
for dir_path in [DATA_DIR, TEMPLATES_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_active_subnichos():
    """Retorna apenas subnichos ativos (em produção)"""
    return {k: v for k, v in SUBNICHO_CONFIG.items() if v.get("active", False)}

def get_all_keywords_flat(language="en"):
    """Retorna todas as keywords de todos os subnichos em um único set"""
    keywords = set()
    for subnicho in SUBNICHO_CONFIG.values():
        if language in subnicho.get("keywords", {}):
            keywords.update(subnicho["keywords"][language])
    return keywords

def get_country_list():
    """Retorna lista de códigos de países"""
    return list(COUNTRIES.keys())

def get_today_filename():
    """Retorna nome do arquivo de dados para hoje"""
    return f"trends_{datetime.now().strftime('%Y-%m-%d')}.json"


# =============================================================================
# CONFIGURAÇÃO DO DASHBOARD
# =============================================================================

DASHBOARD_CONFIG = {
    "title": "TREND MONITOR // CONTENT FACTORY",
    "subtitle": "Pesquisa de Mercado Automática",
    "theme": {
        "bg_primary": "#0a0a0f",
        "bg_secondary": "#12121a",
        "bg_card": "#1a1a24",
        "accent": "#00d4aa",
        "accent_hover": "#00f5c4",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0b0",
        "text_muted": "#606070",
        "border": "#2a2a3a",
        "success": "#00d4aa",
        "warning": "#ffd700",
        "danger": "#ff4757"
    },
    "font_family": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif"
}


if __name__ == "__main__":
    # Teste de configuração
    print("=== TREND MONITOR - Config Test ===\n")

    print(f"Países configurados: {len(COUNTRIES)}")
    for code, info in COUNTRIES.items():
        print(f"  {info['flag']} {code}: {info['name']} ({info['language']})")

    print(f"\nSubnichos ativos: {len(get_active_subnichos())}")
    for key, info in get_active_subnichos().items():
        print(f"  {info['icon']} {info['name']}")

    print(f"\nSubnichos candidatos: {len(SUBNICHO_CONFIG) - len(get_active_subnichos())}")
    for key, info in SUBNICHO_CONFIG.items():
        if not info.get("active", False):
            print(f"  {info['icon']} {info['name']} (inativo)")

    print(f"\nDiretórios:")
    print(f"  Data: {DATA_DIR}")
    print(f"  Templates: {TEMPLATES_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
