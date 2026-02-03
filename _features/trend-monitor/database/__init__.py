# =============================================================================
# DATABASE - Modulos de Banco de Dados
# =============================================================================
# sqlite.py          - Cliente SQLite (local)
# supabase_client.py - Cliente Supabase (nuvem)
# =============================================================================

from .sqlite import TrendDatabase

__all__ = ["TrendDatabase"]
