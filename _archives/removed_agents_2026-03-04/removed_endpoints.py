# --- Endpoints individuais de micronichos (Agente 3) ---

@app.post("/api/analise-micronichos/{channel_id}")
async def trigger_micronicho_analysis(channel_id: str):
    """Roda Agente 3 (Micronichos) para um canal."""
    try:
        result = micro_run_analysis(channel_id)
        return result
    except Exception as e:
        logger.error(f"Erro agente micronichos {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analise-micronichos/run-all")
async def run_micronicho_analysis_all():
    """Roda Agente 3 para TODOS os canais ativos. 1 por vez em fila."""
    try:
        channels = micro_get_channels()
        if not channels:
            return {"success": False, "error": "Nenhum canal ativo encontrado"}

        results = []
        success_count = 0
        error_count = 0

        for ch in channels:
            ch_id = ch["channel_id"]
            ch_name = ch.get("channel_name", "")
            logger.info(f"Micronichos: processando {ch_name} ({ch_id})")

            try:
                res = micro_run_analysis(ch_id)
                results.append({
                    "channel_id": ch_id,
                    "channel_name": ch_name,
                    "success": res.get("success", False),
                    "micronicho_count": res.get("micronicho_count"),
                    "error": res.get("error") if not res.get("success") else None
                })
                if res.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                results.append({
                    "channel_id": ch_id,
                    "channel_name": ch_name,
                    "success": False,
                    "error": str(e)
                })
                error_count += 1

        return {
            "success": True,
            "total_channels": len(channels),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Erro run-all micronichos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-micronichos/{channel_id}/latest")
async def get_latest_micronicho_analysis(channel_id: str):
    """Retorna a analise de micronichos mais recente."""
    try:
        result = micro_get_latest(channel_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Nenhuma analise de micronichos para {channel_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro buscar micronichos {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-micronichos/{channel_id}/historico")
async def get_micronicho_analysis_history(channel_id: str, limit: int = 20, offset: int = 0):
    """Retorna historico de analises de micronichos."""
    try:
        limit = min(limit, 100)
        offset = max(offset, 0)
        return micro_get_history(channel_id, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Erro historico micronichos {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-micronichos/{channel_id}/run/{run_id}")
async def get_micronicho_analysis_run(channel_id: str, run_id: int):
    """Retorna relatorio de um run especifico por ID."""
    try:
        resp = db.supabase.table('micronicho_analysis_runs').select('id,channel_id,run_date,report_text,micronicho_count,total_videos_analyzed').eq('id', run_id).eq('channel_id', channel_id).limit(1).execute()
        if resp.data:
            return resp.data[0]
        raise HTTPException(status_code=404, detail="Run nao encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro run micronichos {channel_id}/{run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoints individuais de estruturas de titulo (Agente 4) ---

@app.post("/api/analise-titulo/{channel_id}")
async def trigger_title_structure_analysis(channel_id: str):
    """Roda Agente 4 (Estruturas de Titulo) para 1 canal."""
    try:
        result = title_run_analysis(channel_id)
        return result
    except Exception as e:
        logger.error(f"Erro analise titulo {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analise-titulo/run-all")
async def run_title_structure_analysis_all():
    """Roda Agente 4 para TODOS os canais. Processa 1 por vez."""
    try:
        channels = micro_get_channels()
        if not channels:
            return {"success": False, "error": "Nenhum canal encontrado"}

        results = []
        success_count = 0
        error_count = 0

        for ch in channels:
            ch_id = ch["channel_id"]
            ch_name = ch.get("channel_name", "")
            logger.info(f"Analise titulo: processando {ch_name} ({ch_id})")

            try:
                res = title_run_analysis(ch_id)
                results.append({
                    "channel_id": ch_id,
                    "channel_name": ch_name,
                    "success": res.get("success", False),
                    "structure_count": res.get("structure_count"),
                    "total_videos": res.get("total_videos"),
                    "has_ctr_data": res.get("has_ctr_data"),
                    "error": res.get("error") if not res.get("success") else None
                })
                if res.get("success"):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                results.append({
                    "channel_id": ch_id,
                    "channel_name": ch_name,
                    "success": False,
                    "error": str(e)
                })
                error_count += 1

        return {
            "success": True,
            "total_channels": len(channels),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Erro run-all titulo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-titulo/{channel_id}/latest")
async def get_latest_title_analysis(channel_id: str):
    """Retorna a analise de titulo mais recente."""
    try:
        result = title_get_latest(channel_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Nenhuma analise de titulo para {channel_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro buscar titulo {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-titulo/{channel_id}/historico")
async def get_title_analysis_history(channel_id: str, limit: int = 20, offset: int = 0):
    """Retorna historico de analises de titulo."""
    try:
        limit = min(limit, 100)
        offset = max(offset, 0)
        return title_get_history(channel_id, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Erro historico titulo {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analise-titulo/{channel_id}/run/{run_id}")
async def get_title_analysis_run(channel_id: str, run_id: int):
    """Retorna relatorio de um run especifico por ID."""
    try:
        resp = db.supabase.table('title_structure_analysis_runs').select('id,channel_id,run_date,report_text,structure_count,total_videos_analyzed').eq('id', run_id).eq('channel_id', channel_id).limit(1).execute()
        if resp.data:
            return resp.data[0]
        raise HTTPException(status_code=404, detail="Run nao encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro run titulo {channel_id}/{run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

