"""
Módulo de Gestão Financeira
Gerencia categorias, lançamentos, taxas e metas financeiras
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import logging
import aiohttp

logger = logging.getLogger(__name__)


def parse_periodo(periodo: str) -> Tuple[datetime, datetime]:
    """
    Converte string de período em datas início/fim
    Formatos: '7d', '15d', '30d', '60d', '90d', 'YYYY-MM-DD,YYYY-MM-DD'
    """
    hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if ',' in periodo:
        # Custom: '2024-01-01,2024-03-31'
        inicio_str, fim_str = periodo.split(',')
        data_inicio = datetime.fromisoformat(inicio_str).replace(tzinfo=timezone.utc)
        data_fim = datetime.fromisoformat(fim_str).replace(tzinfo=timezone.utc)
    elif periodo.endswith('d'):
        # Dias: '30d'
        dias = int(periodo[:-1])
        data_fim = hoje
        data_inicio = hoje - timedelta(days=dias)
    else:
        # Default: 30 dias
        data_fim = hoje
        data_inicio = hoje - timedelta(days=30)

    return data_inicio, data_fim


def calcular_periodo_anterior(periodo: str) -> Tuple[datetime, datetime]:
    """
    Calcula período anterior equivalente para comparação
    """
    data_inicio, data_fim = parse_periodo(periodo)
    duracao = (data_fim - data_inicio).days

    data_fim_anterior = data_inicio - timedelta(days=1)
    data_inicio_anterior = data_fim_anterior - timedelta(days=duracao)

    return data_inicio_anterior, data_fim_anterior


async def get_usd_brl_rate() -> Dict:
    """
    Retorna taxa de câmbio USD-BRL atualizada da AwesomeAPI

    Returns:
        Dict com:
        - taxa: float (ex: 5.52)
        - atualizado_em: str (ex: "2025-12-17 15:35:03")
    """
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    usdbrl = data.get("USDBRL", {})

                    # Usa o valor "bid" (compra) como padrão
                    taxa = float(usdbrl.get("bid", 5.50))
                    atualizado_em = usdbrl.get("create_date", "")

                    logger.info(f"Taxa USD-BRL atualizada: R$ {taxa:.2f} ({atualizado_em})")

                    return {
                        "taxa": round(taxa, 2),
                        "atualizado_em": atualizado_em
                    }
                else:
                    logger.warning(f"Erro ao buscar taxa USD-BRL: HTTP {response.status}")
                    # Fallback: taxa padrão
                    return {"taxa": 5.50, "atualizado_em": "fallback"}

    except Exception as e:
        logger.error(f"Erro ao consultar taxa USD-BRL: {e}")
        # Fallback: taxa padrão
        return {"taxa": 5.50, "atualizado_em": "fallback"}


def calcular_variacao(valor_atual: float, valor_anterior: float) -> float:
    """
    Calcula variação percentual entre dois valores
    """
    if valor_anterior == 0:
        return 100.0 if valor_atual > 0 else 0.0

    return round(((valor_atual - valor_anterior) / abs(valor_anterior)) * 100, 1)


class FinanceiroService:
    """
    Serviço de gestão financeira
    """

    def __init__(self, db):
        self.db = db
        self.supabase = db.supabase

    # ========== CATEGORIAS ==========

    async def listar_categorias(self, ativo: bool = None) -> List[Dict]:
        """Lista todas as categorias"""
        try:
            query = self.supabase.table("financeiro_categorias").select("*")

            if ativo is not None:
                query = query.eq("ativo", ativo)

            response = query.order("tipo", desc=False).order("nome", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao listar categorias: {e}")
            raise

    async def criar_categoria(
        self,
        nome: str,
        tipo: str,
        cor: str = None,
        icon: str = None
    ) -> Dict:
        """Cria nova categoria"""
        try:
            response = self.supabase.table("financeiro_categorias").insert({
                "nome": nome,
                "tipo": tipo,
                "cor": cor,
                "icon": icon,
                "ativo": True
            }).execute()

            logger.info(f"Categoria criada: {nome} ({tipo})")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao criar categoria: {e}")
            raise

    async def editar_categoria(self, categoria_id: int, dados: Dict) -> Dict:
        """Edita categoria existente"""
        try:
            response = self.supabase.table("financeiro_categorias")\
                .update(dados)\
                .eq("id", categoria_id)\
                .execute()

            logger.info(f"Categoria {categoria_id} editada")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao editar categoria: {e}")
            raise

    async def deletar_categoria(self, categoria_id: int) -> bool:
        """Deleta categoria (soft delete)"""
        try:
            response = self.supabase.table("financeiro_categorias")\
                .update({"ativo": False})\
                .eq("id", categoria_id)\
                .execute()

            logger.info(f"Categoria {categoria_id} deletada")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar categoria: {e}")
            raise

    # ========== LANÇAMENTOS ==========

    async def listar_lancamentos(
        self,
        periodo: str = "30d",
        tipo: str = None,
        recorrencia: str = None
    ) -> List[Dict]:
        """Lista lançamentos com filtros"""
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            query = self.supabase.table("financeiro_lancamentos")\
                .select("*, financeiro_categorias(nome, cor)")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())

            if tipo:
                query = query.eq("tipo", tipo)

            if recorrencia:
                query = query.eq("recorrencia", recorrencia)

            response = query.order("data", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao listar lançamentos: {e}")
            raise

    async def criar_lancamento(
        self,
        categoria_id: int,
        valor: float,
        data: str,
        descricao: str,
        tipo: str,
        recorrencia: str = None,
        usuario: str = None
    ) -> Dict:
        """Cria novo lançamento"""
        try:
            # Validação: recorrencia só para despesas
            if tipo == "receita" and recorrencia:
                recorrencia = None

            response = self.supabase.table("financeiro_lancamentos").insert({
                "categoria_id": categoria_id,
                "valor": valor,
                "data": data,
                "descricao": descricao,
                "tipo": tipo,
                "recorrencia": recorrencia,
                "usuario": usuario
            }).execute()

            logger.info(f"Lançamento criado: {tipo} R$ {valor} ({descricao})")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao criar lançamento: {e}")
            raise

    async def editar_lancamento(self, lancamento_id: int, dados: Dict) -> Dict:
        """Edita lançamento existente"""
        try:
            response = self.supabase.table("financeiro_lancamentos")\
                .update(dados)\
                .eq("id", lancamento_id)\
                .execute()

            logger.info(f"Lançamento {lancamento_id} editado")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao editar lançamento: {e}")
            raise

    async def deletar_lancamento(self, lancamento_id: int) -> bool:
        """Deleta lançamento"""
        try:
            response = self.supabase.table("financeiro_lancamentos")\
                .delete()\
                .eq("id", lancamento_id)\
                .execute()

            logger.info(f"Lançamento {lancamento_id} deletado")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar lançamento: {e}")
            raise

    # ========== TAXAS ==========

    async def listar_taxas(self, ativo: bool = None) -> List[Dict]:
        """Lista todas as taxas"""
        try:
            query = self.supabase.table("financeiro_taxas").select("*")

            if ativo is not None:
                query = query.eq("ativo", ativo)

            response = query.order("nome", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao listar taxas: {e}")
            raise

    async def criar_taxa(
        self,
        nome: str,
        percentual: float,
        aplica_sobre: str = "receita_bruta"
    ) -> Dict:
        """Cria nova taxa"""
        try:
            response = self.supabase.table("financeiro_taxas").insert({
                "nome": nome,
                "percentual": percentual,
                "aplica_sobre": aplica_sobre,
                "ativo": True
            }).execute()

            logger.info(f"Taxa criada: {nome} ({percentual}%)")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao criar taxa: {e}")
            raise

    async def editar_taxa(self, taxa_id: int, dados: Dict) -> Dict:
        """Edita taxa existente"""
        try:
            response = self.supabase.table("financeiro_taxas")\
                .update(dados)\
                .eq("id", taxa_id)\
                .execute()

            logger.info(f"Taxa {taxa_id} editada")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao editar taxa: {e}")
            raise

    async def deletar_taxa(self, taxa_id: int) -> bool:
        """Deleta taxa (soft delete)"""
        try:
            response = self.supabase.table("financeiro_taxas")\
                .update({"ativo": False})\
                .eq("id", taxa_id)\
                .execute()

            logger.info(f"Taxa {taxa_id} deletada")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar taxa: {e}")
            raise

    async def calcular_taxas_totais(self, receita_bruta: float) -> float:
        """Calcula total de taxas sobre receita bruta"""
        try:
            taxas = await self.listar_taxas(ativo=True)
            total_taxas = 0.0

            for taxa in taxas:
                if taxa['aplica_sobre'] == 'receita_bruta':
                    valor_taxa = receita_bruta * (taxa['percentual'] / 100)
                    total_taxas += valor_taxa

            return round(total_taxas, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular taxas: {e}")
            return 0.0

    # ========== METAS ==========

    async def listar_metas(self, ativo: bool = None) -> List[Dict]:
        """Lista todas as metas"""
        try:
            query = self.supabase.table("financeiro_metas").select("*")

            if ativo is not None:
                query = query.eq("ativo", ativo)

            response = query.order("periodo_inicio", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao listar metas: {e}")
            raise

    async def criar_meta(
        self,
        nome: str,
        tipo: str,
        valor_objetivo: float,
        periodo_inicio: str,
        periodo_fim: str
    ) -> Dict:
        """Cria nova meta"""
        try:
            response = self.supabase.table("financeiro_metas").insert({
                "nome": nome,
                "tipo": tipo,
                "valor_objetivo": valor_objetivo,
                "periodo_inicio": periodo_inicio,
                "periodo_fim": periodo_fim,
                "ativo": True
            }).execute()

            logger.info(f"Meta criada: {nome} ({tipo}) - R$ {valor_objetivo}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao criar meta: {e}")
            raise

    async def editar_meta(self, meta_id: int, dados: Dict) -> Dict:
        """Edita meta existente"""
        try:
            response = self.supabase.table("financeiro_metas")\
                .update(dados)\
                .eq("id", meta_id)\
                .execute()

            logger.info(f"Meta {meta_id} editada")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao editar meta: {e}")
            raise

    async def deletar_meta(self, meta_id: int) -> bool:
        """Deleta meta (soft delete)"""
        try:
            response = self.supabase.table("financeiro_metas")\
                .update({"ativo": False})\
                .eq("id", meta_id)\
                .execute()

            logger.info(f"Meta {meta_id} deletada")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar meta: {e}")
            raise

    async def calcular_progresso_metas(self) -> List[Dict]:
        """Calcula progresso de todas as metas ativas"""
        try:
            metas = await self.listar_metas(ativo=True)
            resultado = []

            for meta in metas:
                # Período da meta
                periodo_custom = f"{meta['periodo_inicio']},{meta['periodo_fim']}"

                # Calcular valor atual
                if meta['tipo'] == 'receita':
                    valor_atual = await self.get_receita_bruta(periodo_custom)
                elif meta['tipo'] == 'lucro_liquido':
                    valor_atual = await self.get_lucro_liquido(periodo_custom)
                else:
                    valor_atual = 0.0

                # Calcular progresso
                valor_objetivo = float(meta['valor_objetivo'])
                progresso_pct = (valor_atual / valor_objetivo * 100) if valor_objetivo > 0 else 0
                faltam = valor_objetivo - valor_atual

                resultado.append({
                    **meta,
                    "valor_atual": round(valor_atual, 2),
                    "progresso_percentual": round(progresso_pct, 1),
                    "valor_faltante": round(faltam, 2),
                    "atingida": valor_atual >= valor_objetivo
                })

            return resultado
        except Exception as e:
            logger.error(f"Erro ao calcular progresso metas: {e}")
            raise

    # ========== CÁLCULOS ==========

    async def get_receita_bruta(self, periodo: str) -> float:
        """Calcula receita bruta total no período"""
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            response = self.supabase.table("financeiro_lancamentos")\
                .select("valor")\
                .eq("tipo", "receita")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())\
                .execute()

            total = sum(float(item['valor']) for item in (response.data or []))
            return round(total, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular receita bruta: {e}")
            return 0.0

    async def get_despesas_totais(self, periodo: str) -> float:
        """Calcula despesas totais no período"""
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            response = self.supabase.table("financeiro_lancamentos")\
                .select("valor")\
                .eq("tipo", "despesa")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())\
                .execute()

            total = sum(float(item['valor']) for item in (response.data or []))
            return round(total, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular despesas: {e}")
            return 0.0

    async def get_despesas_por_tipo(self, periodo: str) -> Dict[str, float]:
        """Calcula despesas separadas por fixas/únicas"""
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            response = self.supabase.table("financeiro_lancamentos")\
                .select("valor, recorrencia")\
                .eq("tipo", "despesa")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())\
                .execute()

            fixas = 0.0
            unicas = 0.0

            for item in (response.data or []):
                valor = float(item['valor'])
                if item['recorrencia'] == 'fixa':
                    fixas += valor
                elif item['recorrencia'] == 'unica':
                    unicas += valor
                # Se recorrencia é null, considera como única
                else:
                    unicas += valor

            total = fixas + unicas

            return {
                "fixas": round(fixas, 2),
                "unicas": round(unicas, 2),
                "total": round(total, 2),
                "fixas_pct": round((fixas / total * 100) if total > 0 else 0, 1),
                "unicas_pct": round((unicas / total * 100) if total > 0 else 0, 1)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular despesas por tipo: {e}")
            return {"fixas": 0.0, "unicas": 0.0, "total": 0.0, "fixas_pct": 0.0, "unicas_pct": 0.0}

    async def get_lucro_liquido(self, periodo: str) -> float:
        """Calcula lucro líquido no período"""
        try:
            receita_bruta = await self.get_receita_bruta(periodo)
            despesas_totais = await self.get_despesas_totais(periodo)
            taxas_totais = await self.calcular_taxas_totais(receita_bruta)

            lucro = receita_bruta - despesas_totais - taxas_totais
            return round(lucro, 2)
        except Exception as e:
            logger.error(f"Erro ao calcular lucro líquido: {e}")
            return 0.0

    # ========== OVERVIEW ==========

    async def get_overview(self, periodo: str = "30d") -> Dict:
        """
        Retorna overview completo do período:
        - Receita bruta
        - Despesas (total + breakdown fixas/únicas)
        - Taxas totais
        - Lucro líquido
        - Variações vs período anterior
        """
        try:
            # Período atual
            receita_bruta = await self.get_receita_bruta(periodo)
            despesas = await self.get_despesas_por_tipo(periodo)
            taxas_totais = await self.calcular_taxas_totais(receita_bruta)
            lucro_liquido = await self.get_lucro_liquido(periodo)

            # Período anterior (para comparação)
            inicio_ant, fim_ant = calcular_periodo_anterior(periodo)
            periodo_anterior = f"{inicio_ant.date()},{fim_ant.date()}"

            receita_anterior = await self.get_receita_bruta(periodo_anterior)
            despesas_anterior = await self.get_despesas_totais(periodo_anterior)
            lucro_anterior = await self.get_lucro_liquido(periodo_anterior)

            # Variações
            receita_variacao = calcular_variacao(receita_bruta, receita_anterior)
            despesas_variacao = calcular_variacao(despesas['total'], despesas_anterior)
            lucro_variacao = calcular_variacao(lucro_liquido, lucro_anterior)

            return {
                "receita_bruta": receita_bruta,
                "receita_variacao": receita_variacao,
                "despesas_totais": despesas['total'],
                "despesas_fixas": despesas['fixas'],
                "despesas_unicas": despesas['unicas'],
                "despesas_fixas_pct": despesas['fixas_pct'],
                "despesas_unicas_pct": despesas['unicas_pct'],
                "despesas_variacao": despesas_variacao,
                "taxas_totais": taxas_totais,
                "lucro_liquido": lucro_liquido,
                "lucro_variacao": lucro_variacao,
                "periodo": periodo
            }
        except Exception as e:
            logger.error(f"Erro ao gerar overview: {e}")
            raise

    # ========== GRÁFICOS ==========

    async def get_grafico_receita_despesas(self, periodo: str = "30d") -> List[Dict]:
        """
        Dados para gráfico de linha temporal: receita vs despesas vs lucro
        Retorna array com dados diários/semanais
        """
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            # Buscar todos os lançamentos do período
            response = self.supabase.table("financeiro_lancamentos")\
                .select("data, tipo, valor")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())\
                .execute()

            # Agrupar por data
            dados_por_data = {}

            for item in (response.data or []):
                data = item['data']
                if data not in dados_por_data:
                    dados_por_data[data] = {"receita": 0.0, "despesas": 0.0}

                if item['tipo'] == 'receita':
                    dados_por_data[data]['receita'] += float(item['valor'])
                elif item['tipo'] == 'despesa':
                    dados_por_data[data]['despesas'] += float(item['valor'])

            # Converter para lista ordenada
            resultado = []
            for data in sorted(dados_por_data.keys()):
                receita = dados_por_data[data]['receita']
                despesas = dados_por_data[data]['despesas']

                # Calcular taxas proporcionais
                taxas = await self.calcular_taxas_totais(receita)
                lucro = receita - despesas - taxas

                resultado.append({
                    "data": data,
                    "receita": round(receita, 2),
                    "despesas": round(despesas, 2),
                    "taxas": round(taxas, 2),
                    "lucro": round(lucro, 2)
                })

            return resultado
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico receita/despesas: {e}")
            return []

    async def get_grafico_despesas_breakdown(self, periodo: str = "30d") -> Dict:
        """
        Dados para gráfico pizza: breakdown de despesas
        - Por categoria
        - Fixas vs Únicas
        """
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            # Buscar despesas com categorias
            response = self.supabase.table("financeiro_lancamentos")\
                .select("valor, recorrencia, financeiro_categorias(nome, cor)")\
                .eq("tipo", "despesa")\
                .gte("data", data_inicio.date())\
                .lte("data", data_fim.date())\
                .execute()

            # Agrupar por categoria
            por_categoria = {}
            fixas_total = 0.0
            unicas_total = 0.0

            for item in (response.data or []):
                valor = float(item['valor'])
                categoria = item['financeiro_categorias']['nome'] if item.get('financeiro_categorias') else 'Sem categoria'
                cor = item['financeiro_categorias'].get('cor') if item.get('financeiro_categorias') else '#999999'

                # Por categoria
                if categoria not in por_categoria:
                    por_categoria[categoria] = {"valor": 0.0, "cor": cor}
                por_categoria[categoria]['valor'] += valor

                # Fixas vs Únicas
                if item['recorrencia'] == 'fixa':
                    fixas_total += valor
                else:
                    unicas_total += valor

            # Converter para arrays
            total_despesas = fixas_total + unicas_total

            categorias = [
                {
                    "nome": cat,
                    "valor": round(dados['valor'], 2),
                    "percentual": round((dados['valor'] / total_despesas * 100) if total_despesas > 0 else 0, 1),
                    "cor": dados['cor']
                }
                for cat, dados in sorted(por_categoria.items(), key=lambda x: x[1]['valor'], reverse=True)
            ]

            recorrencia = [
                {
                    "tipo": "Fixas",
                    "valor": round(fixas_total, 2),
                    "percentual": round((fixas_total / total_despesas * 100) if total_despesas > 0 else 0, 1),
                    "cor": "#FF6B6B"
                },
                {
                    "tipo": "Únicas",
                    "valor": round(unicas_total, 2),
                    "percentual": round((unicas_total / total_despesas * 100) if total_despesas > 0 else 0, 1),
                    "cor": "#4ECDC4"
                }
            ]

            return {
                "por_categoria": categorias,
                "por_recorrencia": recorrencia,
                "total": round(total_despesas, 2)
            }
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico breakdown despesas: {e}")
            return {"por_categoria": [], "por_recorrencia": [], "total": 0.0}

    # ========== INTEGRAÇÃO YOUTUBE ==========

    async def get_youtube_revenue(self, periodo: str = "30d") -> float:
        """Consulta receita YouTube do período (apenas valores reais) em BRL"""
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            # Buscar taxa de câmbio
            taxa_cambio = await get_usd_brl_rate()
            taxa = taxa_cambio['taxa']

            response = self.supabase.table("yt_daily_metrics")\
                .select("revenue")\
                .eq("is_estimate", False)\
                .gte("date", data_inicio.date())\
                .lte("date", data_fim.date())\
                .execute()

            # Soma em USD
            total_usd = sum(float(item['revenue'] or 0) for item in (response.data or []))

            # Converter para BRL
            total_brl = total_usd * taxa

            return round(total_brl, 2)
        except Exception as e:
            logger.error(f"Erro ao consultar receita YouTube: {e}")
            return 0.0

    async def sync_youtube_revenue(self, periodo: str = "90d") -> Dict:
        """
        Sincroniza receita YouTube criando lançamentos automáticos
        Agrupa por mês e cria um lançamento por mês (apenas valores reais)
        CONVERTE USD -> BRL usando taxa atual
        """
        try:
            data_inicio, data_fim = parse_periodo(periodo)

            # Buscar taxa de câmbio atual
            taxa_cambio = await get_usd_brl_rate()
            taxa = taxa_cambio['taxa']
            logger.info(f"Usando taxa de câmbio: R$ {taxa:.2f}")

            # Buscar receita YouTube por mês (apenas valores reais, em USD)
            response = self.supabase.table("yt_daily_metrics")\
                .select("date, revenue")\
                .eq("is_estimate", False)\
                .gte("date", data_inicio.date())\
                .lte("date", data_fim.date())\
                .execute()

            # Agrupar por mês (em USD)
            por_mes_usd = {}
            for item in (response.data or []):
                data = datetime.fromisoformat(item['date'])
                mes_key = data.strftime("%Y-%m")

                if mes_key not in por_mes_usd:
                    por_mes_usd[mes_key] = 0.0

                por_mes_usd[mes_key] += float(item['revenue'] or 0)

            # Converter para BRL
            por_mes = {}
            for mes_key, valor_usd in por_mes_usd.items():
                por_mes[mes_key] = valor_usd * taxa

            # Buscar categoria "YouTube AdSense"
            cat_response = self.supabase.table("financeiro_categorias")\
                .select("id")\
                .eq("nome", "YouTube AdSense")\
                .execute()

            if not cat_response.data:
                # Criar categoria se não existir
                cat = await self.criar_categoria("YouTube AdSense", "receita", "#00FF00", "youtube")
                categoria_id = cat['id']
            else:
                categoria_id = cat_response.data[0]['id']

            # Criar lançamentos
            criados = 0
            for mes_key, valor in por_mes.items():
                if valor <= 0:
                    continue

                # Verificar se já existe lançamento para este mês
                ano, mes = mes_key.split('-')
                data_lancamento = f"{ano}-{mes}-01"
                descricao = f"Receita YouTube AdSense - {mes}/{ano}"

                existente = self.supabase.table("financeiro_lancamentos")\
                    .select("id")\
                    .eq("categoria_id", categoria_id)\
                    .eq("data", data_lancamento)\
                    .execute()

                if existente.data:
                    logger.info(f"Lançamento já existe para {mes_key}")
                    continue

                # Criar lançamento
                await self.criar_lancamento(
                    categoria_id=categoria_id,
                    valor=round(valor, 2),
                    data=data_lancamento,
                    descricao=descricao,
                    tipo="receita",
                    usuario="sistema"
                )
                criados += 1

            return {
                "sincronizados": criados,
                "periodo": periodo,
                "meses": len(por_mes),
                "taxa_cambio": taxa,
                "taxa_atualizada_em": taxa_cambio['atualizado_em']
            }
        except Exception as e:
            logger.error(f"Erro ao sincronizar receita YouTube: {e}")
            raise
