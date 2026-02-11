"""
Sistema de Calendário Empresarial - Router Principal
Integração com o main.py
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, validator
from typing import Optional, List, Any
from datetime import date
import logging

logger = logging.getLogger(__name__)

# ========================================
# MODELS PYDANTIC
# ========================================

class EventCreate(BaseModel):
    """Model para criar novo evento"""
    title: str
    description: Optional[str] = None
    event_date: date
    created_by: str
    category: Optional[str] = None
    event_type: str = "normal"

    @validator('created_by')
    def validate_author(cls, v):
        # Normalizar entrada (lowercase e remover espaços)
        v = v.lower().strip() if v else v
        valid_authors = ['cellibs', 'arthur', 'lucca', 'joao']
        if v not in valid_authors:
            raise ValueError(f'Autor deve ser um de: {valid_authors}')
        return v

    @validator('category')
    def validate_category(cls, v, values):
        if 'event_type' in values and values['event_type'] in ['monetization', 'demonetization']:
            return None
        # Normalizar entrada se houver valor
        if v:
            v = v.lower().strip()
            if v not in ['geral', 'desenvolvimento', 'financeiro', 'urgente']:
                raise ValueError('Categoria inválida')
        return v

    @validator('event_type')
    def validate_event_type(cls, v):
        # Normalizar entrada
        v = v.lower().strip() if v else 'normal'
        if v not in ['normal', 'monetization', 'demonetization']:
            raise ValueError('Tipo de evento inválido')
        return v

class EventUpdate(BaseModel):
    """Model para atualizar evento"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    category: Optional[str] = None
    event_type: Optional[str] = None

class SearchRequest(BaseModel):
    """Model para busca avançada"""
    text: Optional[str] = None
    authors: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# ========================================
# FUNÇÃO PARA INICIALIZAR ROUTER
# ========================================

def init_calendar_router(db: Any) -> APIRouter:
    """
    Inicializa o router do calendário com acesso ao database
    Segue o padrão do agents_router
    """
    try:
        # Importar o sistema de calendário
        from _features.calendar_system.calendar_system import CalendarSystem

        # Criar instância do sistema
        calendar_system = CalendarSystem(db)

        # Criar router
        router = APIRouter(prefix="/api/calendar", tags=["calendar"])

        # ========================================
        # ENDPOINT 1: Eventos do mês
        # ========================================
        @router.get("/month/{year}/{month}")
        async def get_month_events(
            year: int,
            month: int,
            author: Optional[str] = Query(None)
        ):
            """
            Retorna eventos do mês agrupados por dia
            Formato: {'2026-02-11': [eventos], '2026-02-12': [eventos]}
            """
            try:
                result = await calendar_system.get_month_events(year, month, author)
                return result
            except Exception as e:
                logger.error(f"Erro ao buscar eventos do mês: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 2: Eventos do dia
        # ========================================
        @router.get("/day/{date}")
        async def get_day_events(date: str):
            """
            Retorna eventos de um dia específico
            Data no formato: YYYY-MM-DD
            """
            try:
                result = await calendar_system.get_day_events(date)
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Erro ao buscar eventos do dia: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 3: Criar evento
        # ========================================
        @router.post("/event", status_code=201)
        async def create_event(event: EventCreate):
            """
            Cria novo evento no calendário
            Retorna o evento criado com ID
            """
            try:
                event_data = event.dict()
                # Converter date para string ISO
                if event_data.get('event_date'):
                    event_data['event_date'] = event_data['event_date'].isoformat()

                result = await calendar_system.create_event(event_data)
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Erro ao criar evento: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 4: Ver evento
        # ========================================
        @router.get("/event/{event_id}")
        async def get_event(event_id: int):
            """
            Retorna detalhes completos de um evento
            """
            try:
                result = await calendar_system.get_event(event_id)
                return result
            except Exception as e:
                if "não encontrado" in str(e).lower():
                    raise HTTPException(status_code=404, detail="Evento não encontrado")
                logger.error(f"Erro ao buscar evento: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 5: Atualizar evento
        # ========================================
        @router.patch("/event/{event_id}")
        async def update_event(event_id: int, update: EventUpdate):
            """
            Atualiza evento existente
            Permite atualização parcial
            """
            try:
                update_data = update.dict(exclude_unset=True)
                # Converter date para string ISO se presente
                if update_data.get('event_date'):
                    update_data['event_date'] = update_data['event_date'].isoformat()

                result = await calendar_system.update_event(event_id, update_data)
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                if "não encontrado" in str(e).lower():
                    raise HTTPException(status_code=404, detail="Evento não encontrado")
                logger.error(f"Erro ao atualizar evento: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 6: Deletar evento
        # ========================================
        @router.delete("/event/{event_id}")
        async def delete_event(event_id: int):
            """
            Deleta evento (soft delete - vai para lixeira por 30 dias)
            """
            try:
                result = await calendar_system.delete_event(event_id)
                return result
            except Exception as e:
                if "não encontrado" in str(e).lower():
                    raise HTTPException(status_code=404, detail="Evento não encontrado")
                logger.error(f"Erro ao deletar evento: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT 7: Busca avançada
        # ========================================
        @router.post("/search")
        async def search_events(search: SearchRequest):
            """
            Busca avançada de eventos
            Suporta busca por texto, autor, categoria, tipo e período
            """
            try:
                search_params = search.dict(exclude_none=True)
                result = await calendar_system.search_events(search_params)
                return result
            except Exception as e:
                logger.error(f"Erro na busca: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ========================================
        # ENDPOINT EXTRA: Estatísticas
        # ========================================
        @router.get("/stats")
        async def get_stats():
            """
            Retorna estatísticas do calendário
            Total de eventos, por autor, por categoria, etc.
            """
            try:
                result = await calendar_system.get_stats()
                return result
            except Exception as e:
                logger.error(f"Erro ao buscar estatísticas: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        logger.info("✅ Router do calendário inicializado com sucesso")
        return router

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar router do calendário: {e}")
        raise