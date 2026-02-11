"""
Sistema de Calendário Empresarial
Classe principal com toda lógica de negócio
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class CalendarSystem:
    """Sistema de calendário empresarial para o dashboard"""

    # Configuração dos sócios
    SOCIOS = {
        "cellibs": {"name": "Cellibs", "emoji": "🎯"},
        "arthur": {"name": "Arthur", "emoji": "📝"},
        "lucca": {"name": "Lucca", "emoji": "🎬"},
        "joao": {"name": "João", "emoji": "🎨"}
    }

    # Categorias e cores
    CATEGORIAS = {
        "geral": "🟡",
        "desenvolvimento": "🔵",
        "financeiro": "🟣",
        "urgente": "🔴"
    }

    def __init__(self, db):
        """Inicializa com conexão ao banco"""
        self.db = db
        logger.info("Sistema de Calendário inicializado")

    async def get_month_events(self, year: int, month: int, author: Optional[str] = None):
        """Retorna eventos do mês agrupados por dia"""
        try:
            # Calcular início e fim do mês
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            # Query base
            query = self.db.supabase.table('calendar_events').select('*')\
                .gte('event_date', start_date.isoformat())\
                .lte('event_date', end_date.isoformat())\
                .eq('is_deleted', False)\
                .order('event_date')

            # Filtro por autor se especificado
            if author and author in self.SOCIOS:
                query = query.eq('created_by', author)

            response = query.execute()
            events = response.data if response.data else []

            # Enriquecer e agrupar
            return self._group_events_by_day(events)

        except Exception as e:
            logger.error(f"Erro ao buscar eventos do mês: {e}")
            raise

    async def get_day_events(self, date_str: str):
        """Retorna eventos de um dia específico"""
        try:
            # Validar data
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Data inválida. Use formato: YYYY-MM-DD")

            # Buscar eventos
            response = self.db.supabase.table('calendar_events').select('*')\
                .eq('event_date', event_date.isoformat())\
                .eq('is_deleted', False)\
                .order('created_at')\
                .execute()

            events = [self._enrich_event(e) for e in (response.data or [])]

            return {
                "date": date_str,
                "day_name": event_date.strftime("%A"),
                "total": len(events),
                "events": events
            }

        except Exception as e:
            logger.error(f"Erro ao buscar eventos do dia: {e}")
            raise

    async def create_event(self, event_data: dict):
        """Cria novo evento"""
        try:
            # Validar autor
            if event_data.get('created_by') not in self.SOCIOS:
                raise ValueError(f"Autor inválido: {event_data.get('created_by')}")

            # Validar categoria se for evento normal
            if event_data.get('event_type') == 'normal':
                if event_data.get('category') not in self.CATEGORIAS:
                    raise ValueError(f"Categoria inválida: {event_data.get('category')}")

            # Se for monetização/desmonetização, remove categoria
            if event_data.get('event_type') in ['monetization', 'demonetization']:
                event_data['category'] = None

            # Validar campos obrigatórios
            if not event_data.get('title'):
                raise ValueError("Título é obrigatório")

            if not event_data.get('event_date'):
                raise ValueError("Data é obrigatória")

            # Inserir no banco
            response = self.db.supabase.table('calendar_events').insert(event_data).execute()

            if response.data:
                created_event = self._enrich_event(response.data[0])
                logger.info(f"Evento criado: {created_event['id']} - {created_event['title']}")
                return created_event

            raise Exception("Erro ao criar evento")

        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            raise

    async def get_event(self, event_id: int):
        """Retorna detalhes de um evento"""
        try:
            response = self.db.supabase.table('calendar_events').select('*')\
                .eq('id', event_id)\
                .eq('is_deleted', False)\
                .execute()

            if response.data and len(response.data) > 0:
                return self._enrich_event(response.data[0])

            raise Exception("Evento não encontrado")

        except Exception as e:
            logger.error(f"Erro ao buscar evento {event_id}: {e}")
            raise

    async def update_event(self, event_id: int, update_data: dict):
        """Atualiza evento existente"""
        try:
            # Verificar se evento existe
            check = self.db.supabase.table('calendar_events').select('id')\
                .eq('id', event_id)\
                .eq('is_deleted', False)\
                .execute()

            if not check.data:
                raise Exception("Evento não encontrado")

            # Validações
            if 'created_by' in update_data and update_data['created_by'] not in self.SOCIOS:
                raise ValueError(f"Autor inválido: {update_data['created_by']}")

            if 'category' in update_data and update_data['category']:
                if update_data['category'] not in self.CATEGORIAS:
                    raise ValueError(f"Categoria inválida: {update_data['category']}")

            # Se mudou para monetização/desmonetização, limpa categoria
            if update_data.get('event_type') in ['monetization', 'demonetization']:
                update_data['category'] = None

            # Atualizar
            response = self.db.supabase.table('calendar_events')\
                .update(update_data)\
                .eq('id', event_id)\
                .execute()

            if response.data:
                updated_event = self._enrich_event(response.data[0])
                logger.info(f"Evento atualizado: {event_id}")
                return updated_event

            raise Exception("Erro ao atualizar evento")

        except Exception as e:
            logger.error(f"Erro ao atualizar evento {event_id}: {e}")
            raise

    async def delete_event(self, event_id: int):
        """Soft delete - move para lixeira"""
        try:
            # Verificar se evento existe
            check = self.db.supabase.table('calendar_events').select('id')\
                .eq('id', event_id)\
                .eq('is_deleted', False)\
                .execute()

            if not check.data:
                raise Exception("Evento não encontrado")

            # Soft delete
            response = self.db.supabase.table('calendar_events')\
                .update({
                    'is_deleted': True,
                    'deleted_at': datetime.now().isoformat()
                })\
                .eq('id', event_id)\
                .execute()

            if response.data:
                logger.info(f"Evento movido para lixeira: {event_id}")
                return {"success": True, "message": "Evento movido para lixeira (30 dias)"}

            raise Exception("Erro ao deletar evento")

        except Exception as e:
            logger.error(f"Erro ao deletar evento {event_id}: {e}")
            raise

    async def search_events(self, search_params: dict):
        """Busca avançada com múltiplos filtros"""
        try:
            query = self.db.supabase.table('calendar_events').select('*')\
                .eq('is_deleted', False)

            # Busca por texto (título ou descrição)
            if search_params.get('text'):
                # Busca case insensitive
                text = f"%{search_params['text'].lower()}%"
                # Nota: Supabase tem limitações com OR, então fazemos 2 queries
                query1 = self.db.supabase.table('calendar_events').select('*')\
                    .eq('is_deleted', False)\
                    .ilike('title', text)\
                    .execute()

                query2 = self.db.supabase.table('calendar_events').select('*')\
                    .eq('is_deleted', False)\
                    .ilike('description', text)\
                    .execute()

                # Combinar resultados únicos
                events_dict = {}
                for event in (query1.data or []) + (query2.data or []):
                    events_dict[event['id']] = event
                events = list(events_dict.values())
            else:
                # Sem busca por texto, usar query normal
                # Filtro por autores
                if search_params.get('authors'):
                    valid_authors = [a for a in search_params['authors'] if a in self.SOCIOS]
                    if valid_authors:
                        query = query.in_('created_by', valid_authors)

                # Filtro por categorias
                if search_params.get('categories'):
                    valid_cats = [c for c in search_params['categories'] if c in self.CATEGORIAS]
                    if valid_cats:
                        query = query.in_('category', valid_cats)

                # Filtro por tipo de evento
                if search_params.get('event_types'):
                    query = query.in_('event_type', search_params['event_types'])

                # Filtro por período
                if search_params.get('date_from'):
                    query = query.gte('event_date', search_params['date_from'])
                if search_params.get('date_to'):
                    query = query.lte('event_date', search_params['date_to'])

                response = query.order('event_date', desc=True).execute()
                events = response.data or []

            # Se teve busca por texto e outros filtros, aplicar filtros adicionais
            if search_params.get('text') and any([
                search_params.get('authors'),
                search_params.get('categories'),
                search_params.get('date_from'),
                search_params.get('date_to')
            ]):
                if search_params.get('authors'):
                    events = [e for e in events if e.get('created_by') in search_params['authors']]
                if search_params.get('categories'):
                    events = [e for e in events if e.get('category') in search_params['categories']]
                if search_params.get('date_from'):
                    events = [e for e in events if e.get('event_date') >= search_params['date_from']]
                if search_params.get('date_to'):
                    events = [e for e in events if e.get('event_date') <= search_params['date_to']]

            # Enriquecer eventos
            events = [self._enrich_event(e) for e in events]

            # Ordenar por data (mais recente primeiro)
            events.sort(key=lambda x: x.get('event_date', ''), reverse=True)

            return {
                "total": len(events),
                "search_params": search_params,
                "events": events
            }

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            raise

    async def get_stats(self):
        """Retorna estatísticas do calendário"""
        try:
            stats = {
                "total_events": 0,
                "by_author": {},
                "by_category": {},
                "monetizations": 0,
                "demonetizations": 0,
                "recent_events": []
            }

            # Total geral
            total = self.db.supabase.table('calendar_events').select('id', count='exact')\
                .eq('is_deleted', False).execute()
            stats['total_events'] = total.count if hasattr(total, 'count') else 0

            # Por autor
            for socio_key in self.SOCIOS:
                count = self.db.supabase.table('calendar_events').select('id', count='exact')\
                    .eq('is_deleted', False)\
                    .eq('created_by', socio_key).execute()
                stats['by_author'][socio_key] = count.count if hasattr(count, 'count') else 0

            # Por categoria
            for cat in self.CATEGORIAS:
                count = self.db.supabase.table('calendar_events').select('id', count='exact')\
                    .eq('is_deleted', False)\
                    .eq('category', cat).execute()
                stats['by_category'][cat] = count.count if hasattr(count, 'count') else 0

            # Monetizações
            mon = self.db.supabase.table('calendar_events').select('id', count='exact')\
                .eq('is_deleted', False)\
                .eq('event_type', 'monetization').execute()
            stats['monetizations'] = mon.count if hasattr(mon, 'count') else 0

            # Desmonetizações
            demon = self.db.supabase.table('calendar_events').select('id', count='exact')\
                .eq('is_deleted', False)\
                .eq('event_type', 'demonetization').execute()
            stats['demonetizations'] = demon.count if hasattr(demon, 'count') else 0

            # Eventos recentes (últimos 5)
            recent = self.db.supabase.table('calendar_events').select('*')\
                .eq('is_deleted', False)\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()

            if recent.data:
                stats['recent_events'] = [self._enrich_event(e) for e in recent.data]

            # Adicionar configuração dos sócios
            stats['socios_config'] = self.SOCIOS
            stats['categorias_config'] = self.CATEGORIAS

            return stats

        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            raise

    def _enrich_event(self, event: dict) -> dict:
        """Adiciona emojis e cores ao evento"""
        if not event:
            return event

        # Emoji e nome do autor
        if event.get('created_by') in self.SOCIOS:
            event['author_emoji'] = self.SOCIOS[event['created_by']]['emoji']
            event['author_name'] = self.SOCIOS[event['created_by']]['name']

        # Cor da categoria
        if event.get('category') in self.CATEGORIAS:
            event['category_color'] = self.CATEGORIAS[event['category']]

        # Indicadores especiais
        if event.get('event_type') == 'monetization':
            event['special_indicator'] = '💰'
        elif event.get('event_type') == 'demonetization':
            event['special_indicator'] = '❌'

        return event

    def _group_events_by_day(self, events: List[dict]) -> Dict[str, List[dict]]:
        """Agrupa eventos por dia"""
        grouped = {}
        for event in events:
            event = self._enrich_event(event)
            # Extrair apenas a data (YYYY-MM-DD)
            date_str = str(event.get('event_date', ''))[:10]

            if date_str not in grouped:
                grouped[date_str] = []
            grouped[date_str].append(event)

        return grouped