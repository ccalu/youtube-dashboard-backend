import os
import asyncio
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
            
            existing = self.supabase.table("dados_canais_historico").select("*").eq("canal_id", canal_id).eq("data_coleta", data_coleta).execute()
            
            canal_data = {
                "canal_id": canal_id,
                "data_coleta": data_coleta,
                "views_30d": data.get("views_30d"),
                "views_15d": data.get("views_15d"),
                "views_7d": data.get("views_7d"),
                "inscritos": data.get("inscritos"),
                "videos_publicados_7d": data.get("videos_publicados_7d", 0),
                "engagement_rate": data.get("engagement_rate", 0.0)
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
            historico_response = self.supabase.table("dados_canais_historico")\
                .select("*")\
                .gte("data_coleta", trinta_e_cinco_dias_atras)\
                .execute()
            
            logger.info(f"📊 Histórico carregado: {len(historico_response.data)} linhas (otimizado)")

            # 🔧 Organizar histórico por canal_id e data (para calcular diferença)
            historico_por_canal = {}
            for h in historico_response.data:
                canal_id = h["canal_id"]
                data_coleta = h.get("data_coleta", "")

                if canal_id not in historico_por_canal:
                    historico_por_canal[canal_id] = {}

                historico_por_canal[canal_id][data_coleta] = h

            logger.info(f"📊 Canais com histórico: {len(historico_por_canal)}")
            
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
                    "views_growth_30d": None   # % crescimento views 30d vs 30d anteriores
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

                        # 🆕 Calcular diferença de inscritos (hoje vs ontem)
                        if len(datas_disponiveis) >= 2:
                            h_ontem = historico_por_canal[item["id"]][datas_disponiveis[1]]
                            inscritos_hoje = h_hoje.get("inscritos") or 0
                            inscritos_ontem = h_ontem.get("inscritos") or 0
                            canal["inscritos_diff"] = inscritos_hoje - inscritos_ontem

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
                            views_7d_anterior = h_7d_atras.get("views_7d") or 0
                            if views_7d_anterior > 0:
                                growth_7d = ((canal["views_7d"] - views_7d_anterior) / views_7d_anterior) * 100
                                canal["views_growth_7d"] = round(growth_7d, 1)

                        # Calcular views_growth_30d
                        if h_30d_atras:
                            views_30d_anterior = h_30d_atras.get("views_30d") or 0
                            if views_30d_anterior > 0:
                                growth_30d = ((canal["views_30d"] - views_30d_anterior) / views_30d_anterior) * 100
                                canal["views_growth_30d"] = round(growth_30d, 1)

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
            limit: Quantidade de vídeos a retornar (padrão: 20)

        Returns:
            Lista de vídeos ordenados por data de publicação (mais recente primeiro)
        """
        try:
            # Buscar vídeos mais recentes deste canal
            response = self.supabase.table("videos_historico")\
                .select("*")\
                .eq("canal_id", canal_id)\
                .order("data_publicacao", desc=True)\
                .limit(limit * 2)\
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

            logger.info(f"✅ Encontrados {len(videos)} vídeos únicos para canal {canal_id}")
            return videos[:limit]

        except Exception as e:
            logger.error(f"Erro ao buscar vídeos do canal {canal_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

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

    async def save_video_comments(self, video_id: str, canal_id: int, comments: List[Dict]) -> bool:
        """
        Salva comentários analisados no banco de dados
        """
        try:
            if not comments:
                return True

            # Preparar dados para inserção
            records = []
            for comment in comments:
                record = {
                    'comment_id': comment.get('comment_id'),
                    'video_id': video_id,
                    'video_title': comment.get('video_title', ''),
                    'canal_id': canal_id,
                    'author_name': comment.get('author_name', 'Anônimo'),
                    'author_channel_id': comment.get('author_channel_id', ''),
                    'comment_text_original': comment.get('comment_text_original', ''),
                    'comment_text_pt': comment.get('comment_text_pt', ''),
                    'original_language': comment.get('original_language', 'unknown'),
                    'is_translated': comment.get('is_translated', False),
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
                    'published_at': comment.get('published_at')
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
        Busca dados de engajamento completos de um canal
        """
        try:
            # Buscar resumo geral
            summary_response = self.supabase.table('video_comments_summary')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .order('last_analyzed_at', desc=True)\
                .execute()

            # Buscar comentários com problemas
            problems_response = self.supabase.table('video_comments')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .eq('has_problem', True)\
                .order('published_at', desc=True)\
                .limit(20)\
                .execute()

            # Buscar comentários positivos
            positive_response = self.supabase.table('video_comments')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .eq('sentiment_category', 'positive')\
                .eq('has_praise', True)\
                .order('like_count', desc=True)\
                .limit(20)\
                .execute()

            # Buscar comentários acionáveis
            actionable_response = self.supabase.table('video_comments')\
                .select('*')\
                .eq('canal_id', canal_id)\
                .eq('action_required', True)\
                .eq('is_resolved', False)\
                .order('published_at', desc=True)\
                .limit(20)\
                .execute()

            # Calcular métricas gerais
            total_comments = sum(s.get('total_comments', 0) for s in summary_response.data) if summary_response.data else 0
            total_positive = sum(s.get('positive_count', 0) for s in summary_response.data) if summary_response.data else 0
            total_negative = sum(s.get('negative_count', 0) for s in summary_response.data) if summary_response.data else 0

            return {
                'summary': {
                    'total_comments': total_comments,
                    'positive_count': total_positive,
                    'negative_count': total_negative,
                    'positive_pct': round(total_positive / total_comments * 100, 1) if total_comments > 0 else 0,
                    'negative_pct': round(total_negative / total_comments * 100, 1) if total_comments > 0 else 0,
                    'actionable_count': len(actionable_response.data) if actionable_response.data else 0,
                    'problems_count': len(problems_response.data) if problems_response.data else 0
                },
                'videos_summary': summary_response.data[:10] if summary_response.data else [],
                'problem_comments': problems_response.data if problems_response.data else [],
                'positive_comments': positive_response.data if positive_response.data else [],
                'actionable_comments': actionable_response.data if actionable_response.data else []
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
