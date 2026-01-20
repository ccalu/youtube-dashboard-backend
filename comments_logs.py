"""
Sistema de Logs Detalhado para Coleta de Comentários
Armazena e recupera logs estruturados das coletas
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from database import SupabaseClient
import json

class CommentsLogsManager:
    """Gerenciador de logs de coleta de comentários"""

    def __init__(self):
        self.db = SupabaseClient()

    def save_collection_log(self, log_data: Dict) -> bool:
        """
        Salva log detalhado de uma coleta de comentários

        Estrutura esperada de log_data:
        {
            'collection_id': str,
            'timestamp': datetime,
            'tipo': 'automatic' | 'manual',
            'canais_processados': int,
            'canais_com_sucesso': int,
            'canais_com_erro': int,
            'total_comentarios': int,
            'comentarios_analisados': int,
            'comentarios_nao_analisados': int,
            'detalhes_erros': [
                {
                    'canal_nome': str,
                    'canal_id': str,
                    'tipo_erro': 'sem_videos' | 'sem_comentarios' | 'api_error',
                    'mensagem': str
                }
            ],
            'detalhes_sucesso': [
                {
                    'canal_nome': str,
                    'canal_id': str,
                    'videos_processados': int,
                    'comentarios_coletados': int,
                    'comentarios_analisados_gpt': int
                }
            ],
            'tempo_execucao': float,  # em segundos
            'tokens_usados': int,  # quantidade de tokens GPT usados
            'percentual_limite_diario': float  # % do limite de 1M tokens/dia
        }
        """
        try:
            # Preparar dados para salvar
            record = {
                'id': log_data.get('collection_id'),
                'timestamp': log_data.get('timestamp', datetime.now(timezone.utc)).isoformat(),
                'tipo': log_data.get('tipo', 'manual'),
                'canais_processados': log_data.get('canais_processados', 0),
                'canais_com_sucesso': log_data.get('canais_com_sucesso', 0),
                'canais_com_erro': log_data.get('canais_com_erro', 0),
                'total_comentarios': log_data.get('total_comentarios', 0),
                'comentarios_analisados': log_data.get('comentarios_analisados', 0),
                'comentarios_nao_analisados': log_data.get('comentarios_nao_analisados', 0),
                'detalhes_erros': json.dumps(log_data.get('detalhes_erros', []), ensure_ascii=False),
                'detalhes_sucesso': json.dumps(log_data.get('detalhes_sucesso', []), ensure_ascii=False),
                'tempo_execucao': log_data.get('tempo_execucao', 0),
                'tokens_usados': log_data.get('tokens_usados', 0),
                'percentual_limite_diario': log_data.get('percentual_limite_diario', 0),
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            # Salvar no banco
            response = self.db.supabase.table('comments_collection_logs')\
                .upsert(record)\
                .execute()

            return bool(response.data)

        except Exception as e:
            print(f"Erro ao salvar log de coleta: {e}")
            return False

    def get_latest_logs(self, limit: int = 10) -> List[Dict]:
        """Busca os logs mais recentes de coleta"""
        try:
            response = self.db.supabase.table('comments_collection_logs')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()

            # Parse JSON fields
            for log in response.data:
                if log.get('detalhes_erros'):
                    log['detalhes_erros'] = json.loads(log['detalhes_erros'])
                if log.get('detalhes_sucesso'):
                    log['detalhes_sucesso'] = json.loads(log['detalhes_sucesso'])

            return response.data

        except Exception as e:
            print(f"Erro ao buscar logs: {e}")
            return []

    def get_log_by_id(self, collection_id: str) -> Optional[Dict]:
        """Busca log específico por ID"""
        try:
            response = self.db.supabase.table('comments_collection_logs')\
                .select('*')\
                .eq('id', collection_id)\
                .single()\
                .execute()

            if response.data:
                log = response.data
                if log.get('detalhes_erros'):
                    log['detalhes_erros'] = json.loads(log['detalhes_erros'])
                if log.get('detalhes_sucesso'):
                    log['detalhes_sucesso'] = json.loads(log['detalhes_sucesso'])
                return log

            return None

        except Exception as e:
            print(f"Erro ao buscar log por ID: {e}")
            return None

    def get_logs_summary(self, days: int = 7) -> Dict:
        """
        Retorna resumo dos logs dos últimos N dias
        """
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            response = self.db.supabase.table('comments_collection_logs')\
                .select('*')\
                .gte('timestamp', cutoff_date)\
                .execute()

            if not response.data:
                return {
                    'periodo_dias': days,
                    'total_coletas': 0,
                    'total_comentarios': 0,
                    'total_analisados': 0,
                    'taxa_sucesso_canais': 0,
                    'tokens_totais_usados': 0,
                    'percentual_medio_limite': 0,
                    'tempo_medio_execucao': 0
                }

            # Calcular estatísticas
            total_coletas = len(response.data)
            total_comentarios = sum(log.get('total_comentarios', 0) for log in response.data)
            total_analisados = sum(log.get('comentarios_analisados', 0) for log in response.data)
            total_canais = sum(log.get('canais_processados', 0) for log in response.data)
            total_sucesso = sum(log.get('canais_com_sucesso', 0) for log in response.data)
            tokens_total = sum(log.get('tokens_usados', 0) for log in response.data)
            percentual_total = sum(log.get('percentual_limite_diario', 0) for log in response.data)
            tempo_total = sum(log.get('tempo_execucao', 0) for log in response.data)

            taxa_sucesso = (total_sucesso / total_canais * 100) if total_canais > 0 else 0
            tempo_medio = tempo_total / total_coletas if total_coletas > 0 else 0
            percentual_medio = percentual_total / total_coletas if total_coletas > 0 else 0

            return {
                'periodo_dias': days,
                'total_coletas': total_coletas,
                'total_comentarios': total_comentarios,
                'total_analisados': total_analisados,
                'taxa_sucesso_canais': round(taxa_sucesso, 1),
                'tokens_totais_usados': tokens_total,
                'percentual_medio_limite': round(percentual_medio, 1),
                'tempo_medio_execucao': round(tempo_medio / 60, 1)  # em minutos
            }

        except Exception as e:
            print(f"Erro ao calcular resumo: {e}")
            return {
                'periodo_dias': days,
                'total_coletas': 0,
                'total_comentarios': 0,
                'total_analisados': 0,
                'taxa_sucesso_canais': 0,
                'tokens_totais_usados': 0,
                'percentual_medio_limite': 0,
                'tempo_medio_execucao': 0
            }

    def get_canais_com_mais_erros(self, limit: int = 10) -> List[Dict]:
        """
        Identifica canais com mais erros recorrentes
        """
        try:
            # Buscar logs dos últimos 30 dias
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

            response = self.db.supabase.table('comments_collection_logs')\
                .select('detalhes_erros')\
                .gte('timestamp', cutoff_date)\
                .execute()

            # Contar erros por canal
            erro_counter = {}
            for log in response.data:
                if log.get('detalhes_erros'):
                    erros = json.loads(log['detalhes_erros'])
                    for erro in erros:
                        canal_id = erro.get('canal_id')
                        if canal_id:
                            if canal_id not in erro_counter:
                                erro_counter[canal_id] = {
                                    'canal_nome': erro.get('canal_nome'),
                                    'canal_id': canal_id,
                                    'total_erros': 0,
                                    'tipos_erro': {}
                                }

                            erro_counter[canal_id]['total_erros'] += 1
                            tipo = erro.get('tipo_erro', 'unknown')
                            erro_counter[canal_id]['tipos_erro'][tipo] = \
                                erro_counter[canal_id]['tipos_erro'].get(tipo, 0) + 1

            # Ordenar por quantidade de erros
            canais_ordenados = sorted(
                erro_counter.values(),
                key=lambda x: x['total_erros'],
                reverse=True
            )[:limit]

            return canais_ordenados

        except Exception as e:
            print(f"Erro ao identificar canais problemáticos: {e}")
            return []