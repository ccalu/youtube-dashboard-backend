import os
import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
import logging
from supabase import create_client, Client
import json

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

        # Client principal (anon key) - para tabelas normais
        self.supabase: Client = create_client(url, key)

        # Client service_role (OPCIONAL) - para tabelas OAuth protegidas com RLS
        # Usado para acessar: yt_oauth_tokens, yt_proxy_credentials, yt_channel_credentials
        if service_role_key:
            self.supabase_service: Client = create_client(url, service_role_key)
            logger.info("Supabase clients initialized (anon + service_role)")
        else:
            self.supabase_service = None
            logger.info("Supabase client initialized (anon only - service_role not configured)")

    async def test_connection(self):
        try:
            response = self.supabase.table("canais_monitorados").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    async def fetch_all_records(self, table: str, select_fields: str = "*", filters: Optional[Dict] = None, batch_size: int = 1000) -> List[Dict]:
        """
        Busca TODOS os registros de uma tabela com paginação automática.
        Garante que não há limite de 1000 registros do Supabase.

        Args:
            table: Nome da tabela
            select_fields: Campos a selecionar (default: "*")
            filters: Dicionário de filtros {campo: valor}
            batch_size: Tamanho do lote para paginação (default: 1000)

        Returns:
            Lista com TODOS os registros, sem limite de 1000
        """
        all_records = []
        offset = 0

        while True:
            try:
                # Criar query com paginação
                query = self.supabase.table(table).select(select_fields).range(offset, offset + batch_size - 1)

                # Aplicar filtros se fornecidos
                if filters:
                    for field, value in filters.items():
                        if value is not None:
                            query = query.eq(field, value)

                response = query.execute()

                if not response.data:
                    break

                all_records.extend(response.data)

                # Log de warning se atingiu exatamente o limite
                if len(response.data) == batch_size:
                    logger.warning(f"⚠️ Tabela '{table}' retornou {batch_size} registros - usando paginação automática (offset: {offset})")

                # Se retornou menos que batch_size, acabou
                if len(response.data) < batch_size:
                    break

                offset += batch_size

            except Exception as e:
                logger.error(f"Erro ao buscar registros da tabela {table}: {e}")
                raise

        logger.info(f"✅ Busca completa na tabela '{table}': {len(all_records)} registros totais")
        return all_records

    async def upsert_canal(self, canal_data: Dict[str, Any]) -> Dict:
        try:
            response = self.supabase.table("canais_monitorados").upsert({
                "nome_canal": canal_data.get("nome_canal"),
                "url_canal": canal_data.get("url_canal"),
                "nicho": canal_data.get("nicho", ""),
                "subnicho": canal_data.get("subnicho"),
                "lingua": canal_data.get("lingua", "English"),
                "tipo": canal_data.get("tipo", "minerado"),
                "status": canal_data.get("status", "ativo")
            }).execute()
            
            logger.info(f"Canal upserted: {canal_data.get('nome_canal')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting canal: {e}")
            raise

    async def get_canais_for_collection(self) -> List[Dict]:
        """
        Busca TODOS os canais ativos para coleta com paginação automática.
        CRÍTICO: Garante que todos os canais sejam coletados mesmo com >1000 canais.
        """
        try:
            # Usar paginação automática para garantir todos os canais
            canais = await self.fetch_all_records(
                table="canais_monitorados",
                select_fields="*",
                filters={"status": "ativo"}
            )
            logger.info(f"Found {len(canais)} canais needing collection (com paginação)")
            return canais
        except Exception as e:
            logger.error(f"Error getting canais for collection: {e}")
            raise

    async def save_canal_data(self, canal_id: int, data: Dict[str, Any]):
        try:
            data_coleta = datetime.now(timezone.utc).date().isoformat()

            # 🔧 CORREÇÃO: Voltei a checar views_60d (não gasta API, é só validação!)
            views_60d = data.get("views_60d", 0)
            views_30d = data.get("views_30d", 0)
            views_15d = data.get("views_15d", 0)
            views_7d = data.get("views_7d", 0)

            # Check if at least one view metric is > 0
            if views_60d == 0 and views_30d == 0 and views_15d == 0 and views_7d == 0:
                logger.warning(f"Skipping save for canal_id {canal_id} - all views zero")
                return None

            # 🆕 CALCULAR INSCRITOS_DIFF NO MOMENTO DA COLETA
            # Buscar inscritos de ontem para calcular diferença
            inscritos_diff = None
            inscritos_atual = data.get("inscritos")

            if inscritos_atual is not None:
                # Verificar se o canal é tipo="nosso" para calcular inscritos_diff
                canal_info = self.supabase.table("canais_monitorados").select("tipo").eq("id", canal_id).execute()

                if canal_info.data and canal_info.data[0].get("tipo") == "nosso":
                    # Buscar dados de ontem
                    data_ontem = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
                    ontem_result = self.supabase.table("dados_canais_historico").select("inscritos").eq("canal_id", canal_id).eq("data_coleta", data_ontem).execute()

                    if ontem_result.data and ontem_result.data[0].get("inscritos") is not None:
                        inscritos_ontem = ontem_result.data[0]["inscritos"]
                        inscritos_diff = inscritos_atual - inscritos_ontem
                        logger.info(f"📊 Canal {canal_id}: inscritos_diff = {inscritos_diff} (hoje: {inscritos_atual}, ontem: {inscritos_ontem})")
                    else:
                        # Primeira coleta ou sem dados de ontem - assume 0
                        inscritos_diff = 0
                        logger.info(f"📊 Canal {canal_id}: inscritos_diff = 0 (sem dados de ontem)")

            existing = self.supabase.table("dados_canais_historico").select("*").eq("canal_id", canal_id).eq("data_coleta", data_coleta).execute()

            canal_data = {
                "canal_id": canal_id,
                "data_coleta": data_coleta,
                "views_30d": data.get("views_30d"),
                "views_15d": data.get("views_15d"),
                "views_7d": data.get("views_7d"),
                "inscritos": data.get("inscritos"),
                "videos_publicados_7d": data.get("videos_publicados_7d", 0),
                "engagement_rate": data.get("engagement_rate", 0.0),
                "inscritos_diff": inscritos_diff  # 🆕 SALVAR DIFERENÇA CALCULADA
            }

            if existing.data:
                response = self.supabase.table("dados_canais_historico").update(canal_data).eq("canal_id", canal_id).eq("data_coleta", data_coleta).execute()
            else:
                response = self.supabase.table("dados_canais_historico").insert(canal_data).execute()

            return response.data
        except Exception as e:
            logger.error(f"Error saving canal data: {e}")
            raise

    async def save_videos_data(self, canal_id: int, videos: List[Dict[str, Any]]):
        try:
            if not videos:
                return []
                
            current_date = datetime.now(timezone.utc).date().isoformat()
            
            saved_videos = []
            for video in videos:
                try:
                    video_data = {
                        "canal_id": canal_id,
                        "video_id": video.get("video_id"),
                        "titulo": video.get("titulo"),
                        "url_video": video.get("url_video"),
                        "data_publicacao": video.get("data_publicacao"),
                        "data_coleta": current_date,
                        "views_atuais": video.get("views_atuais"),
                        "likes": video.get("likes"),
                        "comentarios": video.get("comentarios"),
                        "duracao": video.get("duracao")
                    }
                    
                    existing = self.supabase.table("videos_historico").select("id").eq("video_id", video_data["video_id"]).eq("data_coleta", current_date).execute()
                    
                    if existing.data:
                        response = self.supabase.table("videos_historico").update(video_data).eq("video_id", video_data["video_id"]).eq("data_coleta", current_date).execute()
                    else:
                        response = self.supabase.table("videos_historico").insert(video_data).execute()
                    
                    if response.data:
                        saved_videos.extend(response.data)
                        
                except Exception as video_error:
                    logger.warning(f"Error saving individual video {video.get('video_id')}: {video_error}")
                    continue
            
            logger.info(f"Saved {len(saved_videos)} videos for canal {canal_id}")
            return saved_videos
            
        except Exception as e:
            logger.error(f"Error saving videos data: {e}")
            raise

    async def update_last_collection(self, canal_id: int):
        try:
            response = self.supabase.table("canais_monitorados").update({
                "ultima_coleta": datetime.now(timezone.utc).isoformat()
            }).eq("id", canal_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error updating last collection: {e}")
            raise

    async def create_coleta_log(self, canais_total: int) -> int:
        try:
            response = self.supabase.table("coletas_historico").insert({
                "data_inicio": datetime.now(timezone.utc).isoformat(),
                "status": "em_progresso",
                "canais_total": canais_total,
                "canais_sucesso": 0,
                "canais_erro": 0,
                "videos_coletados": 0,
                "requisicoes_usadas": 0
            }).execute()
            
            coleta_id = response.data[0]["id"]
            return coleta_id
        except Exception as e:
            logger.error(f"Error creating coleta log: {e}")
            raise

    async def update_coleta_log(self, coleta_id: int, status: str, canais_sucesso: int, canais_erro: int, videos_coletados: int, requisicoes_usadas: int = 0, mensagem_erro: Optional[str] = None):
        try:
            data_inicio_response = self.supabase.table("coletas_historico").select("data_inicio").eq("id", coleta_id).execute()
            
            if data_inicio_response.data:
                data_inicio = datetime.fromisoformat(data_inicio_response.data[0]["data_inicio"].replace('Z', '+00:00'))
                data_fim = datetime.now(timezone.utc)
                duracao = int((data_fim - data_inicio).total_seconds())
            else:
                duracao = 0
            
            update_data = {
                "data_fim": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "canais_sucesso": canais_sucesso,
                "canais_erro": canais_erro,
                "videos_coletados": videos_coletados,
                "duracao_segundos": duracao,
                "requisicoes_usadas": requisicoes_usadas
            }
            
            if mensagem_erro:
                update_data["mensagem_erro"] = mensagem_erro
            
            response = self.supabase.table("coletas_historico").update(update_data).eq("id", coleta_id).execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error updating coleta log: {e}")
            raise

    async def get_coletas_historico(self, limit: int = 20) -> List[Dict]:
        try:
            response = self.supabase.table("coletas_historico").select("*").order("data_inicio", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching coletas historico: {e}")
            raise

    async def cleanup_stuck_collections(self) -> int:
        try:
            # Aumentado de 1h para 2h - coletas demoram 60-80min para 263 canais
            duas_horas_atras = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

            response = self.supabase.table("coletas_historico").update({
                "status": "erro",
                "mensagem_erro": "Coleta travada - marcada como erro automaticamente (timeout 2h)"
            }).eq("status", "em_progresso").lt("data_inicio", duas_horas_atras).execute()

            count = len(response.data) if response.data else 0
            if count > 0:
                logger.info(f"Cleaned up {count} stuck collections (timeout: 2 hours)")

            return count
        except Exception as e:
            logger.error(f"Error cleaning up stuck collections: {e}")
            return 0

    async def delete_coleta(self, coleta_id: int):
        try:
            response = self.supabase.table("coletas_historico").delete().eq("id", coleta_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error deleting coleta: {e}")
            raise

    async def get_quota_diaria_usada(self) -> int:
        try:
            hoje = datetime.now(timezone.utc).date().isoformat()
            
            response = self.supabase.table("coletas_historico").select("requisicoes_usadas").gte("data_inicio", hoje).execute()
            
            total = sum(coleta.get("requisicoes_usadas", 0) for coleta in response.data)
            
            return total
        except Exception as e:
            logger.error(f"Error getting daily quota: {e}")
            return 0

    async def get_canais_with_filters(self, nicho: Optional[str] = None, subnicho: Optional[str] = None, lingua: Optional[str] = None, tipo: Optional[str] = None, views_30d_min: Optional[int] = None, views_15d_min: Optional[int] = None, views_7d_min: Optional[int] = None, score_min: Optional[float] = None, growth_min: Optional[float] = None, limit: int = 500, offset: int = 0) -> List[Dict]:
        try:
            # 🔧 ATUALIZAÇÃO: Buscar histórico de 35 dias para calcular growth_30d
            # Precisamos de dados de ~30 dias atrás para comparar com hoje
            trinta_e_cinco_dias_atras = (datetime.now(timezone.utc) - timedelta(days=35)).date().isoformat()

            logger.info(f"📊 Buscando histórico a partir de: {trinta_e_cinco_dias_atras}")
            
            query = self.supabase.table("canais_monitorados").select("*").eq("status", "ativo")
            
            if nicho:
                query = query.eq("nicho", nicho)
            if subnicho:
                query = query.eq("subnicho", subnicho)
            if lingua:
                query = query.eq("lingua", lingua)
            if tipo:
                query = query.eq("tipo", tipo)
            
            canais_response = query.execute()
            
            # 🔧 BUSCAR HISTÓRICO DOS ÚLTIMOS 35 DIAS (para calcular growth_7d e growth_30d)
            # FIX: Paginação completa para evitar limite de 1000 registros do Supabase
            all_historico = []
            page_size = 1000
            pagination_offset = 0  # Renomeado para não colidir com parâmetro 'offset' da função

            while True:
                response = self.supabase.table("dados_canais_historico")\
                    .select("*")\
                    .gte("data_coleta", trinta_e_cinco_dias_atras)\
                    .range(pagination_offset, pagination_offset + page_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_historico.extend(response.data)

                if len(response.data) < page_size:
                    break

                pagination_offset += page_size
                logger.info(f"📊 Paginando histórico... {len(all_historico)} registros carregados")

            # Criar objeto compatível com código existente
            historico_response = type('obj', (object,), {'data': all_historico})()

            logger.info(f"📊 Histórico carregado: {len(historico_response.data)} linhas (com paginação completa)")

            # 🔧 Organizar histórico por canal_id e data (para calcular diferença)
            historico_por_canal = {}
            for h in historico_response.data:
                canal_id = h["canal_id"]
                data_coleta = h.get("data_coleta", "")

                if canal_id not in historico_por_canal:
                    historico_por_canal[canal_id] = {}

                historico_por_canal[canal_id][data_coleta] = h

            logger.info(f"📊 Canais com histórico: {len(historico_por_canal)}")

            # 🚀 OTIMIZAÇÃO: Buscar stats de vídeos de TODOS os canais em 1 query
            logger.info("📊 Calculando stats de vídeos para todos os canais...")
            all_video_stats = await self.get_all_canais_video_stats()
            logger.info(f"✅ Stats calculadas para {len(all_video_stats)} canais")

            canais = []
            for item in canais_response.data:
                canal = {
                    "id": item["id"],
                    "nome_canal": item["nome_canal"],
                    "url_canal": item["url_canal"],
                    "nicho": item["nicho"],
                    "subnicho": item["subnicho"],
                    "lingua": item.get("lingua", "N/A"),
                    "tipo": item.get("tipo", "minerado"),
                    "status": item["status"],
                    "ultima_coleta": item.get("ultima_coleta"),
                    "views_30d": 0,
                    "views_15d": 0,
                    "views_7d": 0,
                    "inscritos": 0,
                    "inscritos_diff": None,
                    "engagement_rate": 0.0,
                    "videos_publicados_7d": 0,
                    "score_calculado": 0,
                    "growth_30d": 0,
                    "growth_7d": 0,
                    # 🆕 Novos campos de crescimento percentual
                    "views_growth_7d": None,   # % crescimento views 7d vs 7d anteriores
                    "views_growth_30d": None,  # % crescimento views 30d vs 30d anteriores
                    # 🆕 Novos campos de diferença absoluta
                    "views_diff_7d": None,     # diferença absoluta views 7d vs 7d anteriores
                    "views_diff_30d": None,     # diferença absoluta views 30d vs 30d anteriores
                    # 🆕 Novos campos de estatísticas de vídeos
                    "total_videos": 0,          # quantidade total de vídeos únicos
                    "total_views": 0            # soma das views de todos os vídeos
                }

                # 🔧 Se tem histórico recente, usa ele
                if item["id"] in historico_por_canal:
                    datas_disponiveis = sorted(historico_por_canal[item["id"]].keys(), reverse=True)

                    if len(datas_disponiveis) > 0:
                        # Dados mais recentes (hoje)
                        h_hoje = historico_por_canal[item["id"]][datas_disponiveis[0]]

                        canal["views_30d"] = h_hoje.get("views_30d") or 0
                        canal["views_15d"] = h_hoje.get("views_15d") or 0
                        canal["views_7d"] = h_hoje.get("views_7d") or 0
                        canal["inscritos"] = h_hoje.get("inscritos") or 0
                        canal["engagement_rate"] = h_hoje.get("engagement_rate") or 0.0
                        canal["videos_publicados_7d"] = h_hoje.get("videos_publicados_7d") or 0

                        # 🆕 USAR O VALOR SALVO DO inscritos_diff (não calcular mais on-the-fly!)
                        # O valor agora é calculado e salvo durante a coleta, garantindo consistência
                        if item.get("tipo") == "nosso":
                            # Buscar o valor salvo do banco (já calculado durante a coleta)
                            canal["inscritos_diff"] = h_hoje.get("inscritos_diff")

                            # Se for None (campo ainda não existe no registro), usa 0
                            if canal["inscritos_diff"] is None:
                                canal["inscritos_diff"] = 0
                                logger.debug(f"Canal {item['nome_canal']}: inscritos_diff não encontrado no banco, usando 0")

                        # 🆕 NOVO: Calcular views_growth_7d (comparar com ~7 dias atrás)
                        hoje_date = datetime.now(timezone.utc).date()
                        data_7d_atras = (hoje_date - timedelta(days=7)).isoformat()
                        data_30d_atras = (hoje_date - timedelta(days=30)).isoformat()

                        # Encontrar registro mais próximo de 7 dias atrás
                        h_7d_atras = None
                        for data in datas_disponiveis:
                            if data <= data_7d_atras:
                                h_7d_atras = historico_por_canal[item["id"]][data]
                                break

                        # Encontrar registro mais próximo de 30 dias atrás
                        h_30d_atras = None
                        for data in datas_disponiveis:
                            if data <= data_30d_atras:
                                h_30d_atras = historico_por_canal[item["id"]][data]
                                break

                        # Calcular views_growth_7d
                        if h_7d_atras:
                            views_7d_anterior = h_7d_atras.get("views_7d")
                            if views_7d_anterior is not None and views_7d_anterior > 0:
                                growth_7d = ((canal["views_7d"] - views_7d_anterior) / views_7d_anterior) * 100
                                canal["views_growth_7d"] = round(growth_7d, 1)

                        # Calcular views_growth_30d
                        if h_30d_atras:
                            views_30d_anterior = h_30d_atras.get("views_30d")
                            if views_30d_anterior is not None and views_30d_anterior > 0:
                                growth_30d = ((canal["views_30d"] - views_30d_anterior) / views_30d_anterior) * 100
                                canal["views_growth_30d"] = round(growth_30d, 1)

                        # 🆕 Calcular views_diff_7d (diferença absoluta)
                        if h_7d_atras:
                            views_7d_anterior = h_7d_atras.get("views_7d")
                            if views_7d_anterior is not None:
                                canal["views_diff_7d"] = canal["views_7d"] - views_7d_anterior

                        # 🆕 Calcular views_diff_30d (diferença absoluta)
                        if h_30d_atras:
                            views_30d_anterior = h_30d_atras.get("views_30d")
                            if views_30d_anterior is not None:
                                canal["views_diff_30d"] = canal["views_30d"] - views_30d_anterior

                    # Calcular score
                    if canal["inscritos"] > 0:
                        score = ((canal["views_30d"] / canal["inscritos"]) * 0.7) + ((canal["views_7d"] / canal["inscritos"]) * 0.3)
                        canal["score_calculado"] = round(score, 2)

                    # Calcular growth 7d (método antigo - mantido para compatibilidade)
                    if canal["views_7d"] > 0 and canal["views_15d"] > 0:
                        views_anterior_7d = canal["views_15d"] - canal["views_7d"]
                        if views_anterior_7d > 0:
                            growth = ((canal["views_7d"] - views_anterior_7d) / views_anterior_7d) * 100
                            canal["growth_7d"] = round(growth, 2)

                # 🆕 Pegar stats de vídeos do dict pré-calculado (OTIMIZADO!)
                video_stats = all_video_stats.get(item["id"], {"total_videos": 0, "total_views": 0})
                canal["total_videos"] = video_stats["total_videos"]
                canal["total_views"] = video_stats["total_views"]

                canais.append(canal)
            
            # Aplicar filtros numéricos
            if views_30d_min:
                canais = [c for c in canais if c.get("views_30d", 0) >= views_30d_min]
            if views_15d_min:
                canais = [c for c in canais if c.get("views_15d", 0) >= views_15d_min]
            if views_7d_min:
                canais = [c for c in canais if c.get("views_7d", 0) >= views_7d_min]
            if score_min:
                canais = [c for c in canais if c.get("score_calculado", 0) >= score_min]
            if growth_min:
                canais = [c for c in canais if c.get("growth_7d", 0) >= growth_min]
            
            # Ordenar por score
            canais.sort(key=lambda x: x.get("score_calculado", 0), reverse=True)
            
            logger.info(f"✅ Retornando {len(canais)} canais filtrados")
            
            return canais[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error fetching canais with filters: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    async def get_videos_with_filters(self, nicho: Optional[str] = None, subnicho: Optional[str] = None, lingua: Optional[str] = None, canal: Optional[str] = None, periodo_publicacao: str = "30d", views_min: Optional[int] = None, growth_min: Optional[float] = None, order_by: str = "views_atuais", limit: int = 500, offset: int = 0) -> List[Dict]:
        try:
            days_map = {"30d": 30, "15d": 15, "7d": 7}
            days = days_map.get(periodo_publicacao, 30)
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            # PAGINAÇÃO: Buscar TODOS os vídeos (pode ter >1000 nos últimos 30 dias)
            all_videos = []
            batch_size = 1000
            offset_count = 0

            while True:
                response = self.supabase.table("videos_historico")\
                    .select("*")\
                    .gte("data_publicacao", cutoff_date)\
                    .range(offset_count, offset_count + batch_size - 1)\
                    .execute()

                if not response.data:
                    break

                all_videos.extend(response.data)

                if len(response.data) < batch_size:
                    break

                offset_count += batch_size

            logger.info(f"✅ Busca de vídeos completa: {len(all_videos)} vídeos dos últimos {days} dias")
            
            videos_dict = {}
            for video in all_videos:
                video_id = video["video_id"]
                data_coleta = video.get("data_coleta", "")
                
                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video
            
            videos = list(videos_dict.values())
            
            if views_min:
                videos = [v for v in videos if v.get("views_atuais", 0) >= views_min]
            
            if videos:
                canal_ids = list(set(v["canal_id"] for v in videos))
                canais_response = self.supabase.table("canais_monitorados").select("*").in_("id", canal_ids).execute()
                canais_dict = {c["id"]: c for c in canais_response.data}
                
                for video in videos:
                    canal_info = canais_dict.get(video["canal_id"], {})
                    video["nome_canal"] = canal_info.get("nome_canal", "Unknown")
                    video["nicho"] = canal_info.get("nicho", "Unknown")
                    video["subnicho"] = canal_info.get("subnicho", "Unknown")
                    video["lingua"] = canal_info.get("lingua", "N/A")
                
                if nicho:
                    videos = [v for v in videos if v.get("nicho") == nicho]
                if subnicho:
                    videos = [v for v in videos if v.get("subnicho") == subnicho]
                if lingua:
                    videos = [v for v in videos if v.get("lingua") == lingua]
                if canal:
                    videos = [v for v in videos if v.get("nome_canal") == canal]
            
            return videos
        except Exception as e:
            logger.error(f"Error fetching videos with filters: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    async def get_videos_by_canal(self, canal_id: int, limit: int = 20) -> List[Dict]:
        """
        Busca os vídeos mais recentes de um canal específico.

        Args:
            canal_id: ID do canal
            limit: Quantidade de vídeos a retornar (padrão: 20, None = todos)

        Returns:
            Lista de vídeos ordenados por data de publicação (mais recente primeiro)
        """
        try:
            # Tratamento de limit
            if limit is None:
                query_limit = 10000  # Limite prático do Supabase
            else:
                query_limit = limit * 2  # Margem para deduplicação

            # Buscar vídeos mais recentes deste canal
            response = self.supabase.table("videos_historico")\
                .select("*")\
                .eq("canal_id", canal_id)\
                .order("data_publicacao", desc=True)\
                .limit(query_limit)\
                .execute()

            if not response.data:
                logger.info(f"Nenhum vídeo encontrado para canal {canal_id}")
                return []

            # Deduplicar por video_id (pegar o registro mais recente)
            videos_dict = {}
            for video in response.data:
                video_id = video.get("video_id")
                if not video_id:
                    continue

                data_coleta = video.get("data_coleta", "")

                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video

            videos = list(videos_dict.values())

            # Ordenar por data de publicação (mais recente primeiro)
            videos.sort(key=lambda x: x.get("data_publicacao", ""), reverse=True)

            # Aplicar limit final
            if limit is None:
                result = videos  # Retornar todos
            else:
                result = videos[:limit]  # Aplicar limite

            logger.info(f"✅ Encontrados {len(result)} vídeos únicos para canal {canal_id}")
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar vídeos do canal {canal_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def get_top_videos_by_canal(self, canal_id: int, limit: int = 5) -> List[Dict]:
        """
        Busca os top N vídeos de um canal ordenados por views.
        Retorna apenas a coleta mais recente de cada vídeo.

        Args:
            canal_id: ID do canal
            limit: Quantidade de vídeos (padrão: 5)

        Returns:
            Lista de vídeos ordenados por views_atuais DESC
        """
        try:
            # CORREÇÃO: Buscar TODOS os vídeos do canal sem limite inicial
            # Isso garante que pegaremos todos os vídeos únicos
            all_videos = []
            offset = 0
            batch_size = 1000

            # Paginar para buscar TODOS os registros
            while True:
                response = self.supabase.table("videos_historico")\
                    .select("*")\
                    .eq("canal_id", canal_id)\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if response.data:
                    all_videos.extend(response.data)
                    if len(response.data) < batch_size:
                        break
                    offset += batch_size
                else:
                    break

            if not all_videos:
                logger.info(f"Nenhum vídeo encontrado para canal {canal_id}")
                return []

            logger.info(f"📊 Canal {canal_id}: {len(all_videos)} registros totais encontrados")

            # Deduplicar: pegar coleta mais recente de cada video_id
            videos_dict = {}
            for video in all_videos:
                video_id = video.get("video_id")
                if not video_id:
                    continue

                data_coleta = video.get("data_coleta", "")

                # Se não existe ou se a data_coleta é mais recente
                if video_id not in videos_dict:
                    videos_dict[video_id] = video
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = video

            # Converter para lista e reordenar por views
            videos = list(videos_dict.values())
            videos.sort(key=lambda x: x.get("views_atuais", 0), reverse=True)

            logger.info(f"📹 Canal {canal_id}: {len(videos)} vídeos únicos após deduplicação")

            # Adicionar url_thumbnail calculada
            for video in videos:
                video_id = video.get("video_id", "")
                video["url_thumbnail"] = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

            # Retornar top N vídeos
            result = videos[:limit]
            logger.info(f"✅ Retornando top {len(result)} vídeos do canal {canal_id} (solicitado: {limit})")
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar top vídeos do canal {canal_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def get_canal_video_stats(self, canal_id: int) -> Dict[str, int]:
        """
        Calcula total_videos e total_views de um canal.
        Usa apenas a coleta mais recente de cada vídeo.

        Args:
            canal_id: ID do canal

        Returns:
            {
                "total_videos": int,
                "total_views": int
            }
        """
        try:
            # Buscar todos os vídeos deste canal (campos mínimos para performance)
            response = self.supabase.table("videos_historico")\
                .select("video_id, views_atuais, data_coleta")\
                .eq("canal_id", canal_id)\
                .execute()

            if not response.data:
                return {"total_videos": 0, "total_views": 0}

            # Deduplicar: pegar coleta mais recente de cada video_id
            videos_dict = {}
            for record in response.data:
                video_id = record.get("video_id")
                data_coleta = record.get("data_coleta", "")

                if video_id not in videos_dict:
                    videos_dict[video_id] = record
                elif data_coleta > videos_dict[video_id].get("data_coleta", ""):
                    videos_dict[video_id] = record

            # Calcular métricas
            total_videos = len(videos_dict)
            total_views = sum(v.get("views_atuais", 0) for v in videos_dict.values())

            logger.debug(f"Canal {canal_id}: {total_videos} vídeos, {total_views:,} views totais")

            return {
                "total_videos": total_videos,
                "total_views": total_views
            }

        except Exception as e:
            logger.error(f"Erro ao calcular stats de vídeos do canal {canal_id}: {e}")
            return {"total_videos": 0, "total_views": 0}

    async def get_all_canais_video_stats(self) -> Dict[int, Dict[str, int]]:
        """
        Calcula total_videos e total_views para TODOS os canais em UMA query.

        OTIMIZAÇÃO v2.0:
        - Usa Materialized View (< 100ms) quando disponível
        - Fallback para método antigo se MV não existir
        - Performance: 950x mais rápido (95s → 100ms)

        Returns:
            Dict mapeando canal_id -> {"total_videos": int, "total_views": int}
        """
        try:
            # ========================================
            # MÉTODO 1: MATERIALIZED VIEW (ULTRA-RÁPIDO!)
            # ========================================
            try:
                logger.info("📊 Tentando buscar stats da Materialized View...")

                # Query direto na Materialized View (< 100ms)
                response = self.supabase.table("mv_canal_video_stats")\
                    .select("canal_id, total_videos, total_views")\
                    .execute()

                if response.data:
                    result = {}
                    for row in response.data:
                        result[row["canal_id"]] = {
                            "total_videos": row["total_videos"],
                            "total_views": row["total_views"]
                        }

                    logger.info(f"⚡ Stats carregadas em < 100ms para {len(result)} canais (Materialized View)")
                    return result
                else:
                    logger.warning("Materialized View vazia, tentando RPC...")

            except Exception as mv_error:
                logger.warning(f"Materialized View não disponível: {mv_error}")

            # ========================================
            # FALLBACK: Retornar vazio (melhor que mentir com dados falsos)
            # ========================================
            # Se MV não está disponível e RPC falhar, retornar vazio
            # A coleta futura preencherá os dados reais
            logger.warning("⚠️ MV e RPC não disponíveis - retornando vazio (sem dados fictícios)")

            # ========================================
            # MÉTODO 2: RPC QUERY SQL (Railway)
            # ========================================
            try:
                query = """
                WITH latest_videos AS (
                    SELECT DISTINCT ON (canal_id, video_id)
                        canal_id,
                        video_id,
                        views_atuais
                    FROM videos_historico
                    ORDER BY canal_id, video_id, data_coleta DESC
                )
                SELECT
                    canal_id,
                    COUNT(DISTINCT video_id) as total_videos,
                    COALESCE(SUM(views_atuais), 0) as total_views
                FROM latest_videos
                GROUP BY canal_id
                """

                response = self.supabase.rpc("execute_sql", {"query": query}).execute()

                # Processar resultado da query SQL
                result = {}
                for row in response.data:
                    result[row["canal_id"]] = {
                        "total_videos": row["total_videos"],
                        "total_views": row["total_views"]
                    }

                logger.info(f"✅ Stats calculadas para {len(result)} canais em 1 query SQL")
                return result

            except Exception as rpc_error:
                # ========================================
                # MÉTODO 3: FALLBACK - PAGINAÇÃO PYTHON (lento, mas funciona)
                # ========================================
                logger.warning("RPC não disponível, usando fallback method (paginação)")
                logger.warning("⚠️ ATENÇÃO: Este método é LENTO (~95s). Execute o SQL em create_materialized_view.sql no Supabase!")

                # Buscar TODOS os vídeos com paginação
                all_records = []
                pagination_offset = 0
                limit = 1000
                start_time = datetime.now()

                logger.info("🔄 Buscando todos os vídeos com paginação (isso pode demorar)...")

                while True:
                    response = self.supabase.table("videos_historico")\
                        .select("canal_id, video_id, views_atuais, data_coleta")\
                        .range(pagination_offset, pagination_offset + limit - 1)\
                        .execute()

                    if response.data:
                        all_records.extend(response.data)

                        # Log a cada 10 páginas para não poluir
                        if (pagination_offset // limit + 1) % 10 == 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            logger.info(f"  📊 {len(all_records)} registros carregados... ({elapsed:.1f}s)")

                        if len(response.data) < limit:
                            # Última página
                            break
                        pagination_offset += limit
                    else:
                        break

                elapsed_total = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Total: {len(all_records)} registros em {elapsed_total:.1f}s")

                if not all_records:
                    return {}

                # Processar em Python (deduplicar e agregar)
                videos_by_canal = {}
                for record in all_records:
                    canal_id = record.get("canal_id")
                    video_id = record.get("video_id")
                    data_coleta = record.get("data_coleta", "")

                    if canal_id not in videos_by_canal:
                        videos_by_canal[canal_id] = {}

                    if video_id not in videos_by_canal[canal_id]:
                        videos_by_canal[canal_id][video_id] = record
                    elif data_coleta > videos_by_canal[canal_id][video_id].get("data_coleta", ""):
                        videos_by_canal[canal_id][video_id] = record

                # Calcular stats
                result = {}
                for canal_id, videos in videos_by_canal.items():
                    total_videos = len(videos)
                    total_views = sum(v.get("views_atuais", 0) for v in videos.values())
                    result[canal_id] = {
                        "total_videos": total_videos,
                        "total_views": total_views
                    }

                logger.warning(f"⚠️ Stats calculadas em {elapsed_total:.1f}s (FALLBACK LENTO)")
                logger.warning("💡 Para melhorar performance, execute create_materialized_view.sql no Supabase")
                return result

        except Exception as e:
            logger.error(f"Erro ao calcular stats de todos os canais: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    async def refresh_mv_canal_video_stats(self) -> bool:
        """
        Atualiza a Materialized View mv_canal_video_stats.
        Deve ser chamado após cada coleta para manter dados frescos.

        Performance: ~2-5 segundos para 300 canais
        Non-blocking: Se falhar, apenas registra warning

        Returns:
            bool: True se sucesso, False se falhou
        """
        try:
            logger.info("=" * 60)
            logger.info("🔄 ATUALIZANDO MATERIALIZED VIEW")
            logger.info("=" * 60)

            start_time = datetime.now()

            # Chamar função SQL de refresh
            # CONCURRENTLY = não bloqueia leituras durante refresh
            self.supabase.rpc("refresh_mv_canal_video_stats").execute()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Materialized View atualizada com sucesso!")
            logger.info(f"⏱️  Tempo de refresh: {elapsed:.1f} segundos")
            logger.info("=" * 60)

            return True

        except Exception as e:
            # NÃO é crítico - apenas registra erro e continua
            # Dashboard continua funcionando com dados anteriores
            logger.warning("=" * 60)
            logger.warning("⚠️ Erro ao atualizar Materialized View")
            logger.warning(f"Erro: {e}")
            logger.warning("Dashboard continuará com dados anteriores")
            logger.warning("Próxima tentativa na próxima coleta")
            logger.warning("=" * 60)
            return False

    async def refresh_all_dashboard_mvs(self) -> dict:
        """
        Atualiza TODAS as Materialized Views do dashboard.
        Chamado após coleta diária às 5h AM.

        Returns:
            Dicionário com estatísticas do refresh
        """
        try:
            logger.info("=" * 60)
            logger.info("🔄 REFRESH DE TODAS AS MATERIALIZED VIEWS")
            logger.info("=" * 60)

            start_time = datetime.now()
            results = {}

            # Chamar função SQL que faz refresh de TODAS as MVs
            response = self.supabase.rpc("refresh_all_dashboard_mvs").execute()

            if response.data:
                for mv in response.data:
                    mv_name = mv.get('mv_name', 'unknown')
                    status = mv.get('status', 'UNKNOWN')
                    rows = mv.get('rows_affected', 0)
                    exec_time = mv.get('execution_time', '0')

                    results[mv_name] = {
                        'status': status,
                        'rows': rows,
                        'time': exec_time
                    }

                    if status == 'SUCCESS':
                        logger.info(f"✅ {mv_name}: {rows} linhas, tempo: {exec_time}")
                    else:
                        logger.warning(f"⚠️ {mv_name}: {status}")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️  Tempo total de refresh: {elapsed:.1f} segundos")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar MVs: {e}")
            return {'error': str(e)}

    async def get_dashboard_from_mv(self, tipo: str = None, subnicho: str = None,
                                   lingua: str = None, limit: int = 100,
                                   offset: int = 0) -> List[Dict]:
        """
        Busca dados do dashboard direto da Materialized View.
        Ultra-rápido: < 100ms ao invés de 3000ms!

        Args:
            tipo: Filtrar por tipo (nosso/minerado)
            subnicho: Filtrar por subnicho
            lingua: Filtrar por língua
            limit: Quantidade máxima de resultados
            offset: Offset para paginação

        Returns:
            Lista de canais com todas as métricas pré-calculadas
        """
        try:
            # Tentar buscar da MV otimizada
            logger.info("⚡ Buscando dados da Materialized View mv_dashboard_completo...")
            start_time = time.time()

            # Construir query base
            query = self.supabase.table("mv_dashboard_completo")\
                .select("*")\
                .order("inscritos", desc=True)\
                .limit(limit)\
                .offset(offset)

            # Aplicar filtros opcionais
            if tipo:
                query = query.eq("tipo", tipo)
            if subnicho:
                query = query.eq("subnicho", subnicho)
            if lingua:
                query = query.eq("lingua", lingua)

            # Executar query
            response = query.execute()

            if response.data:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(f"✅ MV retornou {len(response.data)} canais em {elapsed_ms}ms")

                # Formatar resposta para manter compatibilidade
                result = []
                for canal in response.data:
                    # Converter campos para formato esperado
                    formatted = {
                        'id': canal.get('canal_id'),
                        'nome_canal': canal.get('nome_canal'),
                        'canal_handle': canal.get('canal_handle'),
                        'tipo': canal.get('tipo'),
                        'subnicho': canal.get('subnicho'),
                        'lingua': canal.get('lingua'),
                        'pais': canal.get('pais'),
                        'status': canal.get('status'),
                        'url_canal': canal.get('url_canal'),
                        'thumbnail_url': canal.get('thumbnail_url'),
                        'descricao': canal.get('descricao'),
                        'data_adicao': canal.get('data_adicao'),
                        'ultima_verificacao': canal.get('ultima_verificacao'),
                        'coleta_ativa': canal.get('coleta_ativa'),
                        'notificacoes_ativas': canal.get('notificacoes_ativas'),
                        'limite_notificacao': canal.get('limite_notificacao'),
                        'dias_notificacao': canal.get('dias_notificacao'),
                        'views_referencia': canal.get('views_referencia'),

                        # Métricas atuais
                        'inscritos': canal.get('inscritos', 0),
                        'views_totais': canal.get('views_totais', 0),
                        'videos_publicados': canal.get('videos_publicados', 0),
                        'ultima_coleta': canal.get('ultima_coleta'),

                        # Métricas de views por período (CORRIGIDO - estavam faltando!)
                        'views_60d': canal.get('views_60d', 0),
                        'views_30d': canal.get('views_30d', 0),
                        'views_15d': canal.get('views_15d', 0),
                        'views_7d': canal.get('views_7d', 0),
                        'videos_publicados_7d': canal.get('videos_publicados_7d', 0),
                        'videos_30d': canal.get('videos_30d', 0),
                        'engagement_rate': canal.get('engagement_rate', 0.0),

                        # Growth metrics
                        'inscritos_diff': canal.get('inscritos_diff'),  # FIX: Remove default 0 to preserve None
                        'views_diff_24h': canal.get('views_diff_24h', 0),
                        'views_diff_7d': canal.get('views_diff_7d', 0),
                        'views_diff_30d': canal.get('views_diff_30d', 0),
                        'views_growth_7d': canal.get('views_growth_7d', 0),
                        'views_growth_30d': canal.get('views_growth_30d', 0),

                        # Video stats
                        'total_videos': canal.get('total_videos', 0),
                        'total_video_views': canal.get('total_video_views', 0),

                        # Dados históricos (compatibilidade)
                        'inscritos_7d_atras': canal.get('inscritos_7d_atras', 0),
                        'views_7d_atras': canal.get('views_7d_atras', 0),
                        'inscritos_30d_atras': canal.get('inscritos_30d_atras', 0),
                        'views_30d_atras': canal.get('views_30d_atras', 0)
                    }
                    result.append(formatted)

                return result

            else:
                logger.warning("⚠️ MV vazia ou não existe, usando fallback...")
                # Fallback para método antigo se MV não existir
                return await self.get_canais_with_filters(
                    tipo=tipo, subnicho=subnicho, lingua=lingua,
                    limit=limit, offset=offset
                )

        except Exception as e:
            logger.error(f"❌ Erro ao buscar da MV: {e}")
            logger.info("📊 Usando método tradicional como fallback...")

            # Fallback para método antigo em caso de erro
            return await self.get_canais_with_filters(
                tipo=tipo, subnicho=subnicho, lingua=lingua,
                limit=limit, offset=offset
            )

    async def get_filter_options(self) -> Dict[str, List]:
        try:
            nichos_response = self.supabase.table("canais_monitorados").select("nicho").execute()
            nichos = list(set(item["nicho"] for item in nichos_response.data if item["nicho"]))
            
            subnichos_response = self.supabase.table("canais_monitorados").select("subnicho").execute()
            subnichos = list(set(item["subnicho"] for item in subnichos_response.data if item["subnicho"]))
            
            linguas_response = self.supabase.table("canais_monitorados").select("lingua").execute()
            linguas = list(set(item["lingua"] for item in linguas_response.data if item.get("lingua")))
            
            canais_response = self.supabase.table("canais_monitorados").select("nome_canal").eq("status", "ativo").execute()
            canais = [item["nome_canal"] for item in canais_response.data]
            
            return {
                "nichos": sorted(nichos),
                "subnichos": sorted(subnichos),
                "linguas": sorted(linguas),
                "canais": sorted(canais)
            }
        except Exception as e:
            logger.error(f"Error fetching filter options: {e}")
            raise

    async def get_system_stats(self) -> Dict[str, Any]:
        try:
            canais_response = self.supabase.table("canais_monitorados").select("id", count="exact").execute()
            total_canais = canais_response.count
            
            videos_response = self.supabase.table("videos_historico").select("id", count="exact").execute()
            total_videos = videos_response.count
            
            last_collection_response = self.supabase.table("canais_monitorados").select("ultima_coleta").order("ultima_coleta", desc=True).limit(1).execute()
            last_collection = last_collection_response.data[0]["ultima_coleta"] if last_collection_response.data else None
            
            return {
                "total_canais": total_canais,
                "total_videos": total_videos,
                "last_collection": last_collection,
                "system_status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error fetching system stats: {e}")
            raise

    async def cleanup_old_data(self):
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).date().isoformat()
            
            canal_response = self.supabase.table("dados_canais_historico").delete().lt("data_coleta", cutoff_date).execute()
            video_response = self.supabase.table("videos_historico").delete().lt("data_coleta", cutoff_date).execute()
            
            logger.info(f"Cleaned up old data before {cutoff_date}")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise

    async def add_favorito(self, tipo: str, item_id: int) -> Dict:
        try:
            existing = self.supabase.table("favoritos").select("*").eq("tipo", tipo).eq("item_id", item_id).execute()
            
            if existing.data:
                return existing.data[0]
            
            response = self.supabase.table("favoritos").insert({
                "tipo": tipo,
                "item_id": item_id
            }).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error adding favorito: {e}")
            raise

    async def remove_favorito(self, tipo: str, item_id: int):
        try:
            response = self.supabase.table("favoritos").delete().eq("tipo", tipo).eq("item_id", item_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error removing favorito: {e}")
            raise

    async def get_favoritos_canais(self) -> List[Dict]:
        try:
            favoritos_response = self.supabase.table("favoritos").select("item_id").eq("tipo", "canal").execute()
            
            if not favoritos_response.data:
                return []
            
            canal_ids = [fav["item_id"] for fav in favoritos_response.data]
            canais = await self.get_canais_with_filters(limit=1000)
            canais_favoritos = [c for c in canais if c["id"] in canal_ids]
            
            return canais_favoritos
        except Exception as e:
            logger.error(f"Error fetching favoritos canais: {e}")
            raise

    async def get_favoritos_videos(self) -> List[Dict]:
        try:
            favoritos_response = self.supabase.table("favoritos").select("item_id").eq("tipo", "video").execute()
            
            if not favoritos_response.data:
                return []
            
            video_ids = [fav["item_id"] for fav in favoritos_response.data]
            videos_response = self.supabase.table("videos_historico").select("*").in_("id", video_ids).execute()
            videos = videos_response.data
            
            if videos:
                canal_ids = list(set(v["canal_id"] for v in videos))
                canais_response = self.supabase.table("canais_monitorados").select("*").in_("id", canal_ids).execute()
                canais_dict = {c["id"]: c for c in canais_response.data}
                
                for video in videos:
                    canal_info = canais_dict.get(video["canal_id"], {})
                    video["nome_canal"] = canal_info.get("nome_canal", "Unknown")
                    video["nicho"] = canal_info.get("nicho", "Unknown")
                    video["subnicho"] = canal_info.get("subnicho", "Unknown")
                    video["lingua"] = canal_info.get("lingua", "N/A")
            
            return videos
        except Exception as e:
            logger.error(f"Error fetching favoritos videos: {e}")
            raise

    async def delete_canal_permanently(self, canal_id: int):
        try:
            # Primeiro buscar todos os video_ids do canal
            videos_result = self.supabase.table("videos_historico").select("video_id").eq("canal_id", canal_id).execute()

            # Deletar comentários de todos os vídeos do canal
            if videos_result.data:
                video_ids = [video['video_id'] for video in videos_result.data]
                # Deletar em lotes de 100 para evitar timeout
                for i in range(0, len(video_ids), 100):
                    batch = video_ids[i:i+100]
                    self.supabase.table("video_comments").delete().in_("video_id", batch).execute()

            # Ordem de deleção (respeitar foreign keys)
            self.supabase.table("videos_historico").delete().eq("canal_id", canal_id).execute()
            self.supabase.table("dados_canais_historico").delete().eq("canal_id", canal_id).execute()
            self.supabase.table("notificacoes").delete().eq("canal_id", canal_id).execute()  # Adicionado!
            self.supabase.table("favoritos").delete().eq("tipo", "canal").eq("item_id", canal_id).execute()
            self.supabase.table("canais_monitorados").delete().eq("id", canal_id).execute()

            return True
        except Exception as e:
            logger.error(f"Error deleting canal permanently: {e}")
            raise

    async def get_notificacoes_all(self, limit: int = 500, offset: int = 0, vista_filter: Optional[bool] = None, dias: Optional[int] = 30, lingua: Optional[str] = None, tipo_canal: Optional[str] = None) -> List[Dict]:
        try:
            query = self.supabase.table("notificacoes").select(
                "*, canais_monitorados(subnicho, lingua, tipo)"
            )

            if dias is not None:
                data_limite = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
                query = query.gte("data_disparo", data_limite)

            if vista_filter is not None:
                query = query.eq("vista", vista_filter)

            response = query.order("data_disparo", desc=True).range(offset, offset + limit - 1).execute()

            if not response.data:
                return []

            notificacoes = response.data

            video_ids = [n["video_id"] for n in notificacoes if n.get("video_id")]

            if video_ids:
                videos_response = self.supabase.table("videos_historico").select(
                    "video_id, data_publicacao"
                ).in_("video_id", video_ids).execute()

                videos_dict = {v["video_id"]: v["data_publicacao"] for v in videos_response.data}

                for notif in notificacoes:
                    video_id = notif.get("video_id")
                    if video_id and video_id in videos_dict:
                        notif["data_publicacao"] = videos_dict[video_id]
                    else:
                        notif["data_publicacao"] = None

            for notif in notificacoes:
                if notif.get("canais_monitorados"):
                    notif["subnicho"] = notif["canais_monitorados"].get("subnicho")
                    notif["lingua"] = notif["canais_monitorados"].get("lingua")
                    notif["tipo_canal"] = notif["canais_monitorados"].get("tipo")
                else:
                    notif["subnicho"] = None
                    notif["lingua"] = None
                    notif["tipo_canal"] = None
                notif.pop("canais_monitorados", None)

            # Filtrar por lingua se especificado
            if lingua is not None:
                notificacoes = [n for n in notificacoes if n.get("lingua") == lingua]

            # Filtrar por tipo_canal se especificado
            if tipo_canal is not None:
                notificacoes = [n for n in notificacoes if n.get("tipo_canal") == tipo_canal]

            return notificacoes
        except Exception as e:
            logger.error(f"Erro ao buscar notificacoes: {e}")
            return []
    
    async def marcar_notificacao_vista(self, notif_id: int) -> bool:
        """
        Marca uma notificação como vista.
        """
        try:
            response = self.supabase.table("notificacoes").update({
                "vista": True,
                "data_vista": datetime.now(timezone.utc).isoformat()
            }).eq("id", notif_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao marcar notificacao como vista: {e}")
            return False
    
    async def desmarcar_notificacao_vista(self, notif_id: int) -> bool:
        """
        Desmarca uma notificação como vista (volta para não vista).
        Útil quando usuário marca por engano.
        
        Args:
            notif_id: ID da notificação
            
        Returns:
            bool: True se sucesso, False se notificação não encontrada
        """
        try:
            response = self.supabase.table("notificacoes").update({
                "vista": False,
                "data_vista": None
            }).eq("id", notif_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao desmarcar notificacao como vista: {e}")
            return False
    
    async def marcar_todas_notificacoes_vistas(
        self,
        lingua: Optional[str] = None,
        subnicho: Optional[str] = None,
        tipo_canal: Optional[str] = None,
        periodo_dias: Optional[int] = None
    ) -> int:
        """
        Marca todas as notificações não vistas como vistas (com filtros opcionais).

        Args:
            lingua: Filtrar por língua do canal
            subnicho: Filtrar por subnicho do canal
            tipo_canal: Filtrar por tipo (nosso/minerado)
            periodo_dias: Filtrar por período da regra

        Returns:
            Quantidade de notificações marcadas
        """
        try:
            # Se não tem filtros, marcar todas direto (comportamento original)
            if not lingua and not subnicho and not tipo_canal and not periodo_dias:
                response = self.supabase.table("notificacoes").update({
                    "vista": True,
                    "data_vista": datetime.now(timezone.utc).isoformat()
                }).eq("vista", False).execute()

                return len(response.data) if response.data else 0

            # Com filtros: buscar IDs primeiro (JOIN com canais_monitorados)
            query = self.supabase.table("notificacoes")\
                .select("id, canal_id, periodo_dias, canais_monitorados!inner(lingua, subnicho, tipo)")\
                .eq("vista", False)

            # Aplicar filtros
            if lingua:
                query = query.eq("canais_monitorados.lingua", lingua)
            if subnicho:
                query = query.eq("canais_monitorados.subnicho", subnicho)
            if tipo_canal:
                query = query.eq("canais_monitorados.tipo", tipo_canal)
            if periodo_dias:
                query = query.eq("periodo_dias", periodo_dias)

            ids_response = query.execute()

            if not ids_response.data or len(ids_response.data) == 0:
                logger.info("Nenhuma notificação encontrada com os filtros aplicados")
                return 0

            # Extrair IDs
            ids = [item["id"] for item in ids_response.data]

            # Marcar todas de uma vez
            update_response = self.supabase.table("notificacoes").update({
                "vista": True,
                "data_vista": datetime.now(timezone.utc).isoformat()
            }).in_("id", ids).execute()

            marked_count = len(ids)
            logger.info(f"✅ {marked_count} notificações marcadas como vistas (filtros aplicados)")

            return marked_count

        except Exception as e:
            logger.error(f"Erro ao marcar todas notificacoes como vistas: {e}")
            return 0
    
    async def get_notificacao_stats(self) -> Dict:
        try:
            total_response = self.supabase.table("notificacoes").select("id", count="exact").execute()
            total = total_response.count if total_response.count else 0
            
            nao_vistas_response = self.supabase.table("notificacoes").select("id", count="exact").eq("vista", False).execute()
            nao_vistas = nao_vistas_response.count if nao_vistas_response.count else 0
            
            vistas = total - nao_vistas
            
            hoje = datetime.now(timezone.utc).date().isoformat()
            hoje_response = self.supabase.table("notificacoes").select("id", count="exact").gte("data_disparo", hoje).execute()
            hoje_count = hoje_response.count if hoje_response.count else 0
            
            semana_atras = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            semana_response = self.supabase.table("notificacoes").select("id", count="exact").gte("data_disparo", semana_atras).execute()
            semana_count = semana_response.count if semana_response.count else 0
            
            return {
                "total": total,
                "nao_vistas": nao_vistas,
                "vistas": vistas,
                "hoje": hoje_count,
                "esta_semana": semana_count
            }
        except Exception as e:
            logger.error(f"Erro ao buscar estatisticas de notificacoes: {e}")
            return {
                "total": 0,
                "nao_vistas": 0,
                "vistas": 0,
                "hoje": 0,
                "esta_semana": 0
            }
            
    async def get_regras_notificacoes(self) -> List[Dict]:
        try:
            response = self.supabase.table("regras_notificacoes").select("*").order("views_minimas", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar regras de notificacoes: {e}")
            return []
    
    async def create_regra_notificacao(self, regra_data: Dict) -> Optional[Dict]:
        try:
            if 'subnichos' in regra_data:
                if regra_data['subnichos'] is None or (isinstance(regra_data['subnichos'], list) and len(regra_data['subnichos']) == 0):
                    regra_data['subnichos'] = None
                elif isinstance(regra_data['subnichos'], str):
                    regra_data['subnichos'] = [regra_data['subnichos']]
            
            response = self.supabase.table("regras_notificacoes").insert(regra_data).execute()
            
            if response.data:
                logger.info(f"✅ Regra criada: {regra_data.get('nome_regra')} com {len(regra_data.get('subnichos', [])) if regra_data.get('subnichos') else 'todos os'} subnicho(s)")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erro ao criar regra de notificacao: {e}")
            return None
    
    async def update_regra_notificacao(self, regra_id: int, regra_data: Dict) -> Optional[Dict]:
        try:
            if 'subnichos' in regra_data:
                if regra_data['subnichos'] is None or (isinstance(regra_data['subnichos'], list) and len(regra_data['subnichos']) == 0):
                    regra_data['subnichos'] = None
                elif isinstance(regra_data['subnichos'], str):
                    regra_data['subnichos'] = [regra_data['subnichos']]
            
            response = self.supabase.table("regras_notificacoes").update(regra_data).eq("id", regra_id).execute()
            
            if response.data:
                logger.info(f"✅ Regra atualizada: ID {regra_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar regra de notificacao: {e}")
            return None
    
    async def delete_regra_notificacao(self, regra_id: int) -> bool:
        try:
            response = self.supabase.table("regras_notificacoes").delete().eq("id", regra_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar regra de notificacao: {e}")
            return False
    
    async def toggle_regra_notificacao(self, regra_id: int) -> Optional[Dict]:
        try:
            current = self.supabase.table("regras_notificacoes").select("ativa").eq("id", regra_id).execute()

            if not current.data:
                return None

            nova_ativa = not current.data[0]["ativa"]

            response = self.supabase.table("regras_notificacoes").update({
                "ativa": nova_ativa
            }).eq("id", regra_id).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao toggle regra de notificacao: {e}")
            return None

    async def update_canal_analytics_fields(self, canal_id: int, analytics_data: Dict[str, Any]) -> bool:
        """
        Atualiza campos de analytics do canal (publishedAt, customUrl, etc)

        Args:
            canal_id: ID do canal
            analytics_data: Dados coletados incluindo publishedAt, customUrl, etc

        Returns:
            True se atualizado com sucesso
        """
        try:
            # Preparar dados para atualização
            update_data = {}

            # Adicionar campos se existirem
            if analytics_data.get('published_at'):
                update_data['published_at'] = analytics_data['published_at']

            if analytics_data.get('custom_url'):
                update_data['custom_url'] = analytics_data['custom_url']

            if analytics_data.get('video_count'):
                # Podemos calcular frequência semanal se tivermos published_at
                if analytics_data.get('published_at'):
                    # Calcular semanas desde criação
                    created = datetime.fromisoformat(analytics_data['published_at'].replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    weeks = (now - created).days / 7
                    if weeks > 0:
                        update_data['frequencia_semanal'] = round(analytics_data['video_count'] / weeks, 2)

            # Só atualizar se houver dados novos
            if update_data:
                response = self.supabase.table("canais_monitorados")\
                    .update(update_data)\
                    .eq("id", canal_id)\
                    .execute()

                logger.info(f"✅ Analytics fields updated for canal {canal_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao atualizar campos de analytics: {e}")
            return False

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """
        Deleta notificações não vistas com mais de X dias.

        Args:
            days: Número de dias (padrão: 30)

        Returns:
            Quantidade de notificações deletadas
        """
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            logger.info(f"🧹 Iniciando limpeza de notificações antigas (>{days} dias)...")

            # Deletar notificações não vistas com data_disparo < cutoff_date
            response = self.supabase.table("notificacoes")\
                .delete()\
                .eq("vista", False)\
                .lt("data_disparo", cutoff_date)\
                .execute()

            deleted_count = len(response.data) if response.data else 0

            logger.info(f"✅ {deleted_count} notificações antigas deletadas (>{days} dias)")

            return deleted_count

        except Exception as e:
            logger.error(f"Erro ao limpar notificações antigas: {e}")
            return 0

    async def get_cached_transcription(self, video_id: str):
        try:
            response = self.supabase.table("transcriptions").select("*").eq("video_id", video_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Cache hit for video: {video_id}")
                return response.data[0]["transcription"]
            
            logger.info(f"❌ Cache miss for video: {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching cached transcription: {e}")
            return None
    
    async def save_transcription_cache(self, video_id: str, transcription: str):
        try:
            data = {
                "video_id": video_id,
                "transcription": transcription,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("transcriptions").upsert(data).execute()
            
            logger.info(f"💾 Transcription cached for video: {video_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error saving transcription cache: {e}")
            return None

    # =========================================================================
    # ANALYSIS TAB - New Functions
    # Added by Claude Code - 2024-11-05
    # =========================================================================

    async def get_keyword_analysis(self, period_days: int = 30) -> List[Dict]:
        """Busca análise de keywords mais recente"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            response = self.supabase.table("keyword_analysis")\
                .select("*")\
                .eq("period_days", period_days)\
                .eq("analyzed_date", today)\
                .order("frequency", desc=True)\
                .limit(20)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar keyword analysis: {e}")
            return []

    async def get_title_patterns(self, subniche: str, period_days: int = 30) -> List[Dict]:
        """Busca padrões de título por subniche"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            response = self.supabase.table("title_patterns")\
                .select("*")\
                .eq("subniche", subniche)\
                .eq("period_days", period_days)\
                .eq("analyzed_date", today)\
                .order("avg_views", desc=True)\
                .limit(5)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar title patterns: {e}")
            return []

    async def get_top_channels_snapshot(self, subniche: str) -> List[Dict]:
        """Busca top 5 canais por subniche (snapshot mais recente)"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            response = self.supabase.table("top_channels_snapshot")\
                .select("*, canais_monitorados!inner(nome_canal, url_canal)")\
                .eq("subniche", subniche)\
                .eq("snapshot_date", today)\
                .order("rank_position", desc=False)\
                .limit(5)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar top channels: {e}")
            return []

    async def get_gap_analysis(self, subniche: str = None) -> List[Dict]:
        """Busca gap analysis mais recente"""
        try:
            week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
            
            query = self.supabase.table("gap_analysis")\
                .select("*")\
                .eq("analyzed_week_start", week_start)
            
            if subniche:
                query = query.eq("subniche", subniche)
            
            response = query.order("avg_views", desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar gap analysis: {e}")
            return []

    async def get_weekly_report_latest(self) -> Optional[Dict]:
        """Busca o relatório semanal mais recente"""
        try:
            response = self.supabase.table("weekly_reports")\
                .select("*")\
                .order("week_start", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                import json
                report = response.data[0]
                report['report_data'] = json.loads(report['report_data'])
                return report
            
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar weekly report: {e}")
            return None

    async def get_all_subniches(self) -> List[str]:
        """Busca lista de todos os subniches ativos"""
        try:
            response = self.supabase.table("canais_monitorados")\
                .select("subnicho")\
                .eq("status", "ativo")\
                .execute()

            if response.data:
                subniches = list(set([c['subnicho'] for c in response.data]))
                return sorted(subniches)

            return []
        except Exception as e:
            logger.error(f"Erro ao buscar subniches: {e}")
            return []

    # =========================================================================
    # SUBNICHE TRENDS SNAPSHOT - New Functions
    # Added by Claude Code - 2025-01-07
    # =========================================================================

    async def save_subniche_trends_snapshot(self, trends_data: List[Dict]) -> bool:
        """
        Salva snapshot de tendências por subniche.

        Args:
            trends_data: Lista de dicts com dados de tendências
                Formato: {
                    'subnicho': str,
                    'period_days': int,
                    'total_videos': int,
                    'avg_views': int,
                    'engagement_rate': float,
                    'trend_percent': float,
                    'analyzed_date': str (YYYY-MM-DD)
                }

        Returns:
            bool: True se sucesso, False se erro
        """
        try:
            if not trends_data:
                logger.warning("Nenhum dado de trends para salvar")
                return False

            today = datetime.now().strftime("%Y-%m-%d")

            # Preparar dados para insert/upsert
            records = []
            for trend in trends_data:
                records.append({
                    "subnicho": trend['subnicho'],
                    "period_days": trend['period_days'],
                    "total_videos": trend.get('total_videos', 0),
                    "avg_views": trend.get('avg_views', 0),
                    "engagement_rate": trend.get('engagement_rate', 0.0),
                    "trend_percent": trend.get('trend_percent', 0.0),
                    "snapshot_date": today,
                    "analyzed_date": trend.get('analyzed_date', today)
                })

            # Upsert: cria novo ou atualiza se já existe (baseado em UNIQUE constraint)
            response = self.supabase.table("subniche_trends_snapshot").upsert(records).execute()

            logger.info(f"✅ Salvos {len(records)} registros de subniche trends")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar subniche trends snapshot: {e}")
            return False

    async def get_subniche_trends_snapshot(self, period_days: int) -> List[Dict]:
        """
        Busca snapshot mais recente de tendências por subniche.

        Args:
            period_days: Período (7, 15 ou 30 dias)

        Returns:
            Lista de dicts com dados das tendências
        """
        try:
            # Buscar a data mais recente disponível para este período
            latest_date_response = self.supabase.table("subniche_trends_snapshot")\
                .select("analyzed_date")\
                .eq("period_days", period_days)\
                .order("analyzed_date", desc=True)\
                .limit(1)\
                .execute()

            if not latest_date_response.data:
                logger.warning(f"Nenhum snapshot encontrado para {period_days}d")
                return []

            latest_date = latest_date_response.data[0]["analyzed_date"]

            # Buscar todos os dados dessa data mais recente
            response = self.supabase.table("subniche_trends_snapshot")\
                .select("*")\
                .eq("period_days", period_days)\
                .eq("analyzed_date", latest_date)\
                .order("subnicho", desc=False)\
                .execute()

            if response.data:
                logger.info(f"📊 Subniche trends ({period_days}d): {len(response.data)} registros (data: {latest_date})")
                return response.data

            return []

        except Exception as e:
            logger.error(f"Erro ao buscar subniche trends snapshot: {e}")
            return []

    async def get_all_subniche_trends(self) -> Dict[str, List[Dict]]:
        """
        Busca todos os snapshots (7d, 15d, 30d) de uma vez.
        Útil para frontend carregar tudo em uma request.

        Returns:
            Dict com chaves '7d', '15d', '30d' contendo listas de trends
        """
        try:
            trends_7d = await self.get_subniche_trends_snapshot(7)
            trends_15d = await self.get_subniche_trends_snapshot(15)
            trends_30d = await self.get_subniche_trends_snapshot(30)

            return {
                "7d": trends_7d,
                "15d": trends_15d,
                "30d": trends_30d
            }
        except Exception as e:
            logger.error(f"Erro ao buscar all subniche trends: {e}")
            return {"7d": [], "15d": [], "30d": []}

    # =========================================================================
    # TRACKING DE COLETAS - Funções para rastrear falhas
    # Added by Claude Code - 2026-01-17
    # =========================================================================

    async def marcar_coleta_sucesso(self, canal_id: int):
        """
        Marca canal como coletado com sucesso.
        Reseta contador de falhas e atualiza timestamp de último sucesso.
        """
        try:
            self.supabase.table("canais_monitorados").update({
                "coleta_falhas_consecutivas": 0,
                "coleta_ultimo_sucesso": datetime.now(timezone.utc).isoformat(),
                "coleta_ultimo_erro": None
            }).eq("id", canal_id).execute()
        except Exception as e:
            logger.warning(f"Erro ao marcar coleta como sucesso para canal {canal_id}: {e}")

    async def marcar_coleta_falha(self, canal_id: int, erro: str):
        """
        Incrementa contador de falhas consecutivas e salva mensagem de erro.

        Args:
            canal_id: ID do canal
            erro: Mensagem de erro a salvar
        """
        try:
            # Buscar valor atual de falhas
            atual = self.supabase.table("canais_monitorados")\
                .select("coleta_falhas_consecutivas")\
                .eq("id", canal_id)\
                .execute()

            falhas_atuais = 0
            if atual.data and len(atual.data) > 0:
                falhas_atuais = atual.data[0].get("coleta_falhas_consecutivas") or 0

            # Incrementar e salvar
            self.supabase.table("canais_monitorados").update({
                "coleta_falhas_consecutivas": falhas_atuais + 1,
                "coleta_ultimo_erro": erro[:500] if erro else None  # Limitar tamanho do erro
            }).eq("id", canal_id).execute()

            logger.warning(f"Canal {canal_id}: falha #{falhas_atuais + 1} - {erro[:100]}...")
        except Exception as e:
            logger.error(f"Erro ao marcar coleta como falha para canal {canal_id}: {e}")

    async def update_canal_ultimo_comentario(self, canal_id: int, timestamp: str):
        """
        Atualiza o timestamp do último comentário coletado para um canal.
        Usado para implementar coleta incremental de comentários.
        """
        try:
            self.supabase.table("canais_monitorados").update({
                "ultimo_comentario_coletado": timestamp,
                "total_comentarios_coletados": self.supabase.table("canais_monitorados")
                    .select("total_comentarios_coletados")
                    .eq("id", canal_id)
                    .execute()
                    .data[0].get("total_comentarios_coletados", 0) + 1
            }).eq("id", canal_id).execute()

            logger.debug(f"Timestamp de comentário atualizado para canal {canal_id}: {timestamp}")
        except Exception as e:
            logger.error(f"Erro ao atualizar timestamp de comentário para canal {canal_id}: {e}")

    async def get_canais_problematicos(self) -> List[Dict]:
        """
        Retorna lista de canais com falhas de coleta.
        Ordenados por quantidade de falhas consecutivas (mais problemáticos primeiro).

        Returns:
            Lista de dicts com info dos canais problemáticos
        """
        try:
            response = self.supabase.table("canais_monitorados")\
                .select("id, nome_canal, url_canal, subnicho, tipo, lingua, coleta_falhas_consecutivas, coleta_ultimo_erro, coleta_ultimo_sucesso, ultima_coleta")\
                .gt("coleta_falhas_consecutivas", 0)\
                .order("coleta_falhas_consecutivas", desc=True)\
                .execute()

            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar canais problemáticos: {e}")
            return []

    async def get_canais_sem_coleta_recente(self, dias: int = 3) -> List[Dict]:
        """
        Retorna canais que não tiveram coleta bem-sucedida nos últimos X dias.

        Args:
            dias: Número de dias para considerar "sem coleta recente"

        Returns:
            Lista de canais sem coleta recente
        """
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()

            response = self.supabase.table("canais_monitorados")\
                .select("id, nome_canal, url_canal, subnicho, tipo, ultima_coleta, coleta_falhas_consecutivas, coleta_ultimo_erro")\
                .eq("status", "ativo")\
                .or_(f"ultima_coleta.is.null,ultima_coleta.lt.{cutoff}")\
                .execute()

            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar canais sem coleta recente: {e}")
            return []

    # =========================================================================
    # SISTEMA DE COMENTÁRIOS - Funções para análise de engajamento
    # Added by Claude Code - 2026-01-19
    # =========================================================================

    async def save_video_comments(self, video_id: str, canal_id: int, comments: List[Dict], canal_lingua: str = None) -> bool:
        """
        Salva comentários analisados no banco de dados
        Se o canal for em português, marca automaticamente como traduzido
        """
        try:
            if not comments:
                return True

            # Verificar se canal é em português
            is_portuguese = False
            if canal_lingua:
                lingua_lower = canal_lingua.lower()
                is_portuguese = 'portug' in lingua_lower or lingua_lower in ['portuguese', 'português', 'pt', 'pt-br']

            # Preparar dados para inserção
            records = []
            for comment in comments[:100]:  # Limitar a 100 comentários por vídeo
                # Se canal é português, copiar original para PT e marcar como traduzido
                if is_portuguese:
                    comment_text_pt = comment.get('comment_text_original', '')
                    is_translated = True
                else:
                    comment_text_pt = comment.get('comment_text_pt', '')
                    is_translated = comment.get('is_translated', False)

                record = {
                    'comment_id': comment.get('comment_id'),
                    'video_id': video_id,
                    'video_title': comment.get('video_title', ''),
                    'canal_id': canal_id,
                    'author_name': comment.get('author_name', 'Anônimo'),
                    'author_channel_id': comment.get('author_channel_id', ''),
                    'comment_text_original': comment.get('comment_text_original', ''),
                    'comment_text_pt': comment_text_pt,
                    'original_language': comment.get('original_language', 'unknown'),
                    'is_translated': is_translated,
                    'like_count': comment.get('like_count', 0),
                    'reply_count': comment.get('reply_count', 0),
                    'is_reply': comment.get('is_reply', False),
                    'parent_comment_id': comment.get('parent_comment_id'),
                    'sentiment_score': comment.get('sentiment_score', 0),
                    'sentiment_category': comment.get('sentiment_category', 'neutral'),
                    'has_problem': comment.get('has_problem', False),
                    'problem_type': comment.get('problem_type'),
                    'problem_description': comment.get('problem_description'),
                    'has_praise': comment.get('has_praise', False),
                    'praise_type': comment.get('praise_type'),
                    'insight_text': comment.get('insight_text', ''),
                    'action_required': comment.get('action_required', False),
                    'suggested_action': comment.get('suggested_action', ''),
                    'published_at': comment.get('published_at'),
                    'created_at': comment.get('published_at'),  # Data real do comentário no YouTube
                    'collected_at': datetime.now(timezone.utc).isoformat(),  # Data de coleta no banco (NOVO)
                    'updated_at': datetime.now(timezone.utc).isoformat()  # Data de atualização no banco
                }
                records.append(record)

            # Inserir em lote (upsert para evitar duplicatas)
            response = self.supabase.table('video_comments').upsert(records).execute()

            logger.info(f"✅ {len(records)} comentários salvos para vídeo {video_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao salvar comentários: {e}")
            return False

    async def update_video_comments_summary(self, video_id: str, canal_id: int, summary: Dict) -> bool:
        """
        Atualiza resumo de comentários de um vídeo
        """
        try:
            data = {
                'video_id': video_id,
                'canal_id': canal_id,
                'total_comments': summary.get('total_comments', 0),
                'positive_count': summary['sentiment_distribution'].get('positive', 0),
                'negative_count': summary['sentiment_distribution'].get('negative', 0),
                'neutral_count': summary['sentiment_distribution'].get('neutral', 0),
                'positive_percentage': summary['sentiment_distribution'].get('positive_pct', 0),
                'negative_percentage': summary['sentiment_distribution'].get('negative_pct', 0),
                'problems_count': len(summary.get('problems_found', [])),
                'praise_count': len(summary.get('praises_found', [])),
                'actionable_count': len(summary.get('actionable_items', [])),
                'problem_categories': {p['type']: 1 for p in summary.get('problems_found', [])},
                'praise_categories': {p['type']: 1 for p in summary.get('praises_found', [])},
                'last_analyzed_at': datetime.now(timezone.utc).isoformat()
            }

            response = self.supabase.table('video_comments_summary').upsert(data).execute()

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao salvar resumo de comentários: {e}")
            return False

    async def get_canal_engagement_data(self, canal_id: int) -> Dict[str, Any]:
        """
        Busca dados de engajamento completos de um canal DIRETO dos comentários
        """
        try:
            # Buscar TODOS os comentários do canal
            all_comments_response = self.supabase.table('video_comments')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .execute()

            all_comments = all_comments_response.data if all_comments_response.data else []

            # Calcular métricas gerais
            total_comments = len(all_comments)
            positive_count = len([c for c in all_comments if c.get('sentiment_category') == 'positive'])
            negative_count = len([c for c in all_comments if c.get('sentiment_category') == 'negative'])
            problem_count = len([c for c in all_comments if c.get('sentiment_category') == 'problem'])

            # Agrupar comentários por vídeo
            videos_data = {}
            for comment in all_comments:
                video_id = comment.get('video_id')
                if video_id not in videos_data:
                    videos_data[video_id] = {
                        'video_id': video_id,
                        'video_title': comment.get('video_title', ''),
                        'total_comments': 0,
                        'positive_count': 0,
                        'negative_count': 0,
                        'neutral_count': 0,
                        'problem_count': 0,
                        'comments': []
                    }

                videos_data[video_id]['total_comments'] += 1
                videos_data[video_id]['comments'].append(comment)

                sentiment = comment.get('sentiment_category', 'neutral')
                if sentiment == 'positive':
                    videos_data[video_id]['positive_count'] += 1
                elif sentiment == 'negative':
                    videos_data[video_id]['negative_count'] += 1
                elif sentiment == 'problem':
                    videos_data[video_id]['problem_count'] += 1
                else:
                    videos_data[video_id]['neutral_count'] += 1

            # Converter para lista e ordenar por total de comentários
            videos_list = list(videos_data.values())
            videos_list.sort(key=lambda x: x['total_comments'], reverse=True)

            # Buscar comentários positivos e negativos para destaque
            positive_comments = [c for c in all_comments if c.get('sentiment_category') == 'positive']
            negative_comments = [c for c in all_comments if c.get('sentiment_category') == 'negative']
            problem_comments = [c for c in all_comments if c.get('sentiment_category') == 'problem']

            # Ordenar por like_count se existir
            positive_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)
            negative_comments.sort(key=lambda x: x.get('like_count', 0), reverse=True)

            return {
                'summary': {
                    'total_comments': total_comments,
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'positive_pct': round(positive_count / total_comments * 100, 1) if total_comments > 0 else 0,
                    'negative_pct': round(negative_count / total_comments * 100, 1) if total_comments > 0 else 0,
                    'actionable_count': problem_count,  # problemas são acionáveis
                    'problems_count': problem_count
                },
                'videos_summary': videos_list,  # TODOS os vídeos com comentários
                'problem_comments': problem_comments,  # TODOS os problemas (sem limite)
                'positive_comments': positive_comments,  # TODOS os positivos (sem limite)
                'negative_comments': negative_comments,  # TODOS os negativos (sem limite)
                'actionable_comments': problem_comments  # TODOS os problemas são acionáveis (sem limite)
            }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados de engajamento: {e}")
            return {
                'summary': {'total_comments': 0},
                'videos_summary': [],
                'problem_comments': [],
                'positive_comments': [],
                'actionable_comments': []
            }

    async def mark_comment_resolved(self, comment_id: str) -> bool:
        """
        Marca um comentário como resolvido
        """
        try:
            response = self.supabase.table('video_comments')\
                .update({
                    'is_resolved': True,
                    'resolved_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq('comment_id', comment_id)\
                .execute()

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao marcar comentário como resolvido: {e}")
            return False

    async def get_comments_by_video(self, video_id: str, limit: int = 100) -> List[Dict]:
        """
        Busca comentários de um vídeo específico
        """
        try:
            response = self.supabase.table('video_comments')\
                .select('*')\
                .eq('video_id', video_id)\
                .order('like_count', desc=True)\
                .limit(limit)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar comentários do vídeo: {e}")
            return []

    # ==================== NOVAS FUNÇÕES PARA ABA COMENTÁRIOS ====================

    def get_monetized_channels_with_comments(self) -> List[Dict]:
        """
        Retorna canais monetizados com contagem de comentários
        """
        try:
            # Buscar canais monetizados
            canais = self.supabase.table('canais_monitorados').select(
                'id, nome_canal, subnicho, lingua, url_canal'
            ).eq('tipo', 'nosso').eq('subnicho', 'Monetizados').execute()

            result = []
            for canal in canais.data:
                # Contar total de comentários do canal
                total = self.supabase.table('video_comments').select(
                    'id', count='exact'
                ).eq('canal_id', canal['id']).execute()

                # Contar comentários com resposta sugerida (aguardando resposta)
                com_resposta = self.supabase.table('video_comments').select(
                    'id', count='exact'
                ).eq('canal_id', canal['id']).not_.is_('suggested_response', 'null').eq('is_responded', False).execute()

                # Buscar último comentário
                ultimo = self.supabase.table('video_comments').select(
                    'published_at'
                ).eq('canal_id', canal['id']).order('published_at', desc=True).limit(1).execute()

                # Contar vídeos únicos com comentários
                videos_query = self.supabase.table('video_comments').select(
                    'video_id'
                ).eq('canal_id', canal['id']).execute()
                total_videos = len(set([v['video_id'] for v in videos_query.data])) if videos_query.data else 0

                result.append({
                    'id': canal['id'],
                    'nome_canal': canal['nome_canal'],
                    'subnicho': canal['subnicho'],
                    'lingua': canal['lingua'],
                    'url_canal': canal['url_canal'],
                    'total_comentarios': total.count,
                    'total_videos': total_videos,  # Novo campo adicionado
                    'comentarios_pendentes': com_resposta.count,
                    'ultimo_comentario': self._safe_date_format(ultimo.data[0]['published_at']) if ultimo.data else None
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching monetized channels: {e}")
            return []

    def get_videos_with_comments_count(self, canal_id: int, limit: int = 10) -> List[Dict]:
        """
        Retorna TOP vídeos de um canal com contagem de comentários
        Nova abordagem: busca diretamente dos comentários para evitar duplicatas
        """
        try:
            # 1. Buscar TODOS os comentários do canal
            comments_data = self.supabase.table('video_comments').select(
                'video_id, video_title'
            ).eq('canal_id', canal_id).execute()

            if not comments_data.data:
                return []

            # 2. Agrupar por video_id e contar comentários
            from collections import Counter
            video_counts = Counter([c['video_id'] for c in comments_data.data])

            # 3. Criar dict com títulos únicos
            video_titles = {}
            for comment in comments_data.data:
                if comment['video_id'] not in video_titles:
                    video_titles[comment['video_id']] = comment.get('video_title', 'Sem título')

            # 4. Ordenar por quantidade de comentários (TOP 10 ou limit)
            top_videos = video_counts.most_common(limit)

            # 5. Buscar dados adicionais dos vídeos e montar resultado
            result = []
            for video_id, comment_count in top_videos:
                # Buscar views e título mais recentes do videos_historico
                video_data = self.supabase.table('videos_historico').select(
                    'views_atuais, data_publicacao, titulo'
                ).eq('video_id', video_id).order('data_coleta', desc=True).limit(1).execute()

                # Obter dados do vídeo
                if video_data.data:
                    views = video_data.data[0].get('views_atuais', 0)
                    data_pub = video_data.data[0].get('data_publicacao')
                    # Priorizar título do videos_historico se disponível
                    titulo_hist = video_data.data[0].get('titulo')
                else:
                    views = 0
                    data_pub = None
                    titulo_hist = None

                # Usar título do video_comments se não tiver no historico
                titulo_final = titulo_hist or video_titles.get(video_id)

                # Se ainda não tiver título, buscar via API do YouTube ou usar fallback
                if not titulo_final or titulo_final == 'None':
                    titulo_final = f"Vídeo {video_id}"

                # Contar comentários pendentes
                pendentes = self.supabase.table('video_comments').select(
                    'id', count='exact'
                ).eq('video_id', video_id).not_.is_('suggested_response', 'null').eq('is_responded', False).execute()

                result.append({
                    'video_id': video_id,
                    'titulo': titulo_final,
                    'views': views,
                    'data_publicacao': self._safe_date_format(data_pub) if data_pub else None,
                    'total_comentarios': comment_count,
                    'comentarios_pendentes': pendentes.count,
                    'thumbnail': f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
                })

            logger.info(f"Retornando {len(result)} vídeos únicos com comentários para canal {canal_id}")
            return result
        except Exception as e:
            logger.error(f"Error fetching videos with comments: {e}")
            return []

    def _safe_date_format(self, date_str):
        """
        Helper function to safely format dates and avoid RangeError in frontend
        Garantir formato ISO 8601 sempre válido
        """
        if not date_str or date_str == '':
            return datetime.now(timezone.utc).isoformat()

        try:
            date_str = str(date_str)

            # Adicionar 'T' se não tiver
            if 'T' not in date_str:
                date_str = date_str.replace(' ', 'T')

            # Verificar se tem timezone
            has_tz = False
            if date_str.endswith('Z'):
                has_tz = True
            elif '+' in date_str.split('T')[-1]:  # Apenas após o T
                has_tz = True
            elif len(date_str) > 19 and date_str[-6] in ['+', '-'] and ':' in date_str[-6:]:
                has_tz = True

            # Se não tem timezone, adicionar
            if not has_tz:
                # Tratar microsegundos com muitos dígitos (ex: .98135 -> .981350)
                if '.' in date_str:
                    parts = date_str.split('.')
                    # Garantir 6 dígitos para microsegundos
                    microseconds = parts[1][:6].ljust(6, '0')
                    date_str = f"{parts[0]}.{microseconds}"
                date_str = date_str + '+00:00'

            # Parsear e reformatar
            if date_str.endswith('Z'):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)

            # Retornar sempre com timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.isoformat()

        except Exception as e:
            logger.warning(f"Date parsing error for '{date_str}': {e}")
            return datetime.now(timezone.utc).isoformat()

    def get_video_comments_paginated(self, video_id: str, page: int = 1, limit: int = 10) -> Dict:
        """
        Retorna comentários de um vídeo com paginação (TOP 10 primeiro)
        """
        try:
            offset = (page - 1) * limit

            # Buscar comentários ordenados por likes (mais relevantes primeiro)
            comments = self.supabase.table('video_comments').select(
                'id, comment_id, author_name, comment_text_original, comment_text_pt, '
                'is_translated, like_count, suggested_response, is_responded, published_at, collected_at'
            ).eq('video_id', video_id).order('like_count', desc=True).range(offset, offset + limit - 1).execute()

            # Contar total de comentários
            total = self.supabase.table('video_comments').select(
                'id', count='exact'
            ).eq('video_id', video_id).execute()

            # Processar comentários
            processed_comments = []
            for comment in comments.data:
                # Usar tradução se existir, senão usar original
                text_to_show = comment['comment_text_pt'] if comment['comment_text_pt'] else comment['comment_text_original']

                # Usar _safe_date_format para garantir datas válidas e evitar RangeError
                published_date = self._safe_date_format(
                    comment.get('published_at') or comment.get('collected_at')
                )
                collected_date = self._safe_date_format(
                    comment.get('collected_at') or comment.get('published_at')
                )

                processed_comments.append({
                    'id': comment['id'],
                    'comment_id': comment['comment_id'],
                    'author_name': comment['author_name'],
                    'comment_text': text_to_show,
                    'comment_text_original': comment['comment_text_original'],
                    'comment_text_pt': comment['comment_text_pt'],
                    'is_translated': comment['is_translated'],
                    'like_count': comment['like_count'],
                    'suggested_response': comment['suggested_response'],
                    'is_responded': comment['is_responded'],
                    'published_at': published_date,
                    'collected_at': collected_date
                })

            return {
                'comments': processed_comments,  # Mudado de 'comentarios' para 'comments'
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total.count,
                    'total_pages': (total.count + limit - 1) // limit
                }
            }
        except Exception as e:
            logger.error(f"Error fetching video comments: {e}")
            return {'comments': [], 'pagination': {}}

    def mark_comment_as_responded(self, comment_id: str, actual_response: str = None) -> bool:
        """
        Marca um comentário como respondido
        """
        try:
            update_data = {
                'is_responded': True,
                'responded_at': datetime.utcnow().isoformat()
            }

            if actual_response:
                update_data['actual_response'] = actual_response

            self.supabase.table('video_comments').update(
                update_data
            ).eq('comment_id', comment_id).execute()

            return True
        except Exception as e:
            logger.error(f"Error marking comment as responded: {e}")
            return False

    def get_comments_summary(self) -> Dict:
        """
        Retorna resumo geral dos comentários para o dashboard
        APENAS para canais monetizados (monetizado=True)
        """
        try:
            # Total de canais monetizados
            monetizados = self.supabase.table('canais_monitorados').select(
                'id', count='exact'
            ).eq('tipo', 'nosso').eq('monetizado', True).execute()

            # Buscar IDs dos canais monetizados para filtrar comentários
            canal_ids_result = self.supabase.table('canais_monitorados').select(
                'id'
            ).eq('tipo', 'nosso').eq('monetizado', True).execute()

            canal_ids = [c['id'] for c in (canal_ids_result.data or [])]

            if not canal_ids:
                # Se não há canais monetizados, retorna zeros
                return {
                    'canais_monetizados': 0,
                    'total_comentarios': 0,
                    'novos_hoje': 0,
                    'aguardando_resposta': 0
                }

            # Total de comentários dos últimos 30 dias APENAS dos canais monetizados
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            total_comments = self.supabase.table('video_comments').select(
                'id', count='exact'
            ).in_('canal_id', canal_ids).gte('collected_at', cutoff_date.isoformat()).execute()

            # Comentários novos hoje APENAS dos canais monetizados
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            novos_hoje = self.supabase.table('video_comments').select(
                'id', count='exact'
            ).in_('canal_id', canal_ids).gte('collected_at', today.isoformat()).execute()

            # Comentários aguardando resposta APENAS dos canais monetizados
            aguardando = self.supabase.table('video_comments').select(
                'id', count='exact'
            ).in_('canal_id', canal_ids).not_.is_('suggested_response', 'null').eq('is_responded', False).execute()

            return {
                'canais_monetizados': monetizados.count,
                'total_comentarios': total_comments.count if total_comments.count else 0,
                'novos_hoje': novos_hoje.count if novos_hoje.count else 0,
                'aguardando_resposta': aguardando.count if aguardando.count else 0
            }
        except Exception as e:
            logger.error(f"Error getting comments summary: {e}")
            return {
                'canais_monetizados': 0,
                'total_comentarios': 0,
                'novos_hoje': 0,
                'aguardando_resposta': 0
            }
