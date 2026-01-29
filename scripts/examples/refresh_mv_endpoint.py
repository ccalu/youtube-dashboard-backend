#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoint para refresh manual da Materialized View
Data: 28/01/2026

Este endpoint será adicionado ao main.py para permitir refresh manual
"""

# CÓDIGO A SER ADICIONADO NO main.py:

@app.post("/api/refresh-mv")
async def refresh_materialized_view():
    """
    🔄 Força refresh da Materialized View mv_dashboard_completo.

    Use este endpoint quando:
    - inscritos_diff estiver mostrando 0 para muitos canais
    - Após coleta manual
    - Para garantir dados atualizados
    """
    try:
        logger.info("=" * 60)
        logger.info("🔄 REFRESH MANUAL DA MATERIALIZED VIEW")
        logger.info(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # Tentar método 1: Via RPC (se existir)
        try:
            response = db.supabase.rpc("refresh_all_dashboard_mvs").execute()
            if response.data:
                logger.info("✅ Refresh via RPC executado com sucesso")
                return {
                    "success": True,
                    "method": "rpc",
                    "message": "Materialized View atualizada via RPC",
                    "data": response.data
                }
        except Exception as rpc_error:
            logger.warning(f"RPC não disponível: {rpc_error}")

        # Método 2: SQL direto via Supabase (MAIS CONFIÁVEL)
        try:
            # Executar SQL direto
            sql_query = """
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;
            """

            # Usar postgrest para executar SQL personalizado
            # Nota: Isto requer uma função SQL no Supabase
            response = db.supabase.rpc("execute_refresh_mv").execute()

            logger.info("✅ Refresh via SQL direto executado")
            return {
                "success": True,
                "method": "sql_direct",
                "message": "Materialized View atualizada via SQL direto"
            }

        except Exception as sql_error:
            logger.warning(f"SQL direto falhou: {sql_error}")

        # Método 3: Forçar recálculo dos dados (FALLBACK)
        try:
            # Verificar dados de hoje e ontem
            hoje = datetime.now(timezone.utc).date()
            ontem = hoje - timedelta(days=1)

            # Contar registros disponíveis
            hoje_count = db.supabase.table('dados_canais_historico') \
                .select('id', count='exact') \
                .gte('data_coleta', hoje.isoformat() + 'T00:00:00') \
                .lte('data_coleta', hoje.isoformat() + 'T23:59:59') \
                .execute()

            ontem_count = db.supabase.table('dados_canais_historico') \
                .select('id', count='exact') \
                .gte('data_coleta', ontem.isoformat() + 'T00:00:00') \
                .lte('data_coleta', ontem.isoformat() + 'T23:59:59') \
                .execute()

            logger.info(f"📊 Dados disponíveis - Hoje: {hoje_count.count}, Ontem: {ontem_count.count}")

            # Limpar cache para forçar recálculo
            cache_cleared = clear_all_cache()
            logger.info(f"🧹 Cache limpo: {cache_cleared['entries_cleared']} entradas")

            return {
                "success": True,
                "method": "cache_clear",
                "message": "Cache limpo - dados serão recalculados no próximo acesso",
                "stats": {
                    "dados_hoje": hoje_count.count or 0,
                    "dados_ontem": ontem_count.count or 0,
                    "cache_limpo": cache_cleared['entries_cleared']
                }
            }

        except Exception as fallback_error:
            logger.error(f"Todos os métodos falharam: {fallback_error}")
            return {
                "success": False,
                "error": str(fallback_error),
                "message": "Não foi possível atualizar a MV. Tente novamente ou execute SQL direto no Supabase."
            }

    except Exception as e:
        logger.error(f"❌ Erro crítico no refresh da MV: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erro ao tentar atualizar Materialized View"
        }


# SQL A SER EXECUTADO NO SUPABASE (criar função):
"""
CREATE OR REPLACE FUNCTION execute_refresh_mv()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    start_time timestamp;
    end_time timestamp;
    rows_count integer;
BEGIN
    start_time := clock_timestamp();

    -- Fazer refresh da MV
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;

    end_time := clock_timestamp();

    -- Contar linhas
    SELECT COUNT(*) INTO rows_count FROM mv_dashboard_completo;

    RETURN json_build_object(
        'success', true,
        'rows_affected', rows_count,
        'execution_time', (end_time - start_time),
        'refreshed_at', end_time
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM,
        'refreshed_at', clock_timestamp()
    );
END;
$$;
"""