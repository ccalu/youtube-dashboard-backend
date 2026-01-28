"""
Endpoints do Sistema Kanban para o Dashboard de Mineração
Data: 28/01/2025
Autor: Cellibs

IMPORTANTE: Adicione este código ao arquivo main.py
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

# =====================================================
# MODELS (Adicionar no início do main.py)
# =====================================================

class KanbanMoveStatusRequest(BaseModel):
    new_status: str

class KanbanNoteRequest(BaseModel):
    note_text: str
    note_color: str = "yellow"

class KanbanNoteUpdateRequest(BaseModel):
    note_text: Optional[str] = None
    note_color: Optional[str] = None

class KanbanReorderNotesRequest(BaseModel):
    note_positions: List[Dict[str, int]]

# =====================================================
# FUNÇÕES DO KANBAN (Adicionar após as outras funções)
# =====================================================

async def get_kanban_structure(db_client):
    """
    Retorna a estrutura completa do Kanban com cards, subnichos e canais.
    Apenas canais tipo='nosso'.
    """
    try:
        # Buscar todos os canais nossos
        canais = db_client.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("tipo", "nosso")\
            .order("subnicho", desc=False)\
            .order("nome_canal", desc=False)\
            .execute()

        # Separar monetizados e não monetizados
        monetizados = []
        nao_monetizados = []

        for canal in canais.data:
            # Calcular dias no status
            if canal.get("kanban_status_since"):
                try:
                    # Tentar vários formatos de data
                    date_str = canal["kanban_status_since"]
                    if "Z" in date_str:
                        date_str = date_str.replace("Z", "+00:00")

                    # Adicionar zeros se necessário para microsegundos
                    if "." in date_str:
                        parts = date_str.split(".")
                        microsec_part = parts[1].split("+")[0]
                        # Garantir 6 dígitos nos microsegundos
                        if len(microsec_part) < 6:
                            microsec_part = microsec_part.ljust(6, '0')
                        date_str = f"{parts[0]}.{microsec_part}+00:00"

                    status_date = datetime.fromisoformat(date_str)
                    dias_no_status = (datetime.now(timezone.utc) - status_date).days
                except Exception as e:
                    logger.warning(f"Erro ao processar data: {e}")
                    dias_no_status = 0
            else:
                dias_no_status = 0

            # Mapear status para label e cor
            status_map = {
                # Não monetizados
                "em_teste_inicial": ("Em Teste Inicial", "yellow"),
                "demonstrando_tracao": ("Demonstrando Tração", "green"),
                "em_andamento": ("Em Andamento p/ Monetizar", "orange"),
                "monetizado": ("Monetizado", "blue"),
                # Monetizados
                "em_crescimento": ("Em Crescimento", "green"),
                "em_testes_novos": ("Em Testes Novos", "yellow"),
                "canal_constante": ("Canal Constante", "blue"),
            }

            status_info = status_map.get(canal.get("kanban_status"), ("Sem Status", "gray"))

            # Buscar total de notas do canal
            notas = db_client.supabase.table("kanban_notes")\
                .select("id")\
                .eq("canal_id", canal["id"])\
                .execute()

            canal_info = {
                "id": canal["id"],
                "nome": canal["nome_canal"],
                "subnicho": canal["subnicho"],
                "lingua": canal.get("lingua", ""),
                "url_canal": canal.get("url_canal", ""),
                "kanban_status": canal.get("kanban_status"),
                "status_label": status_info[0],
                "status_color": status_info[1],
                "status_since": canal.get("kanban_status_since"),
                "dias_no_status": dias_no_status,
                "total_notas": len(notas.data) if notas.data else 0
            }

            if canal.get("monetizado"):
                monetizados.append(canal_info)
            else:
                nao_monetizados.append(canal_info)

        # Agrupar por subnicho
        def agrupar_por_subnicho(canais_list):
            subnichos = {}
            for canal in canais_list:
                subnicho = canal["subnicho"] or "Sem Subnicho"
                if subnicho not in subnichos:
                    subnichos[subnicho] = {
                        "nome": subnicho,
                        "total": 0,
                        "canais": []
                    }
                subnichos[subnicho]["canais"].append(canal)
                subnichos[subnicho]["total"] += 1
            return subnichos

        return {
            "monetizados": {
                "total": len(monetizados),
                "subnichos": agrupar_por_subnicho(monetizados)
            },
            "nao_monetizados": {
                "total": len(nao_monetizados),
                "subnichos": agrupar_por_subnicho(nao_monetizados)
            }
        }

    except Exception as e:
        logging.error(f"Erro ao buscar estrutura Kanban: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_kanban_board(db_client, canal_id: int):
    """
    Retorna o quadro Kanban individual de um canal.
    """
    try:
        # Buscar dados do canal
        canal = db_client.supabase.table("canais_monitorados")\
            .select("*")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Calcular dias no status
        dias_no_status = 0
        if canal.data.get("kanban_status_since"):
            try:
                # Tentar vários formatos de data
                date_str = canal.data["kanban_status_since"]
                if "Z" in date_str:
                    date_str = date_str.replace("Z", "+00:00")

                # Adicionar zeros se necessário para microsegundos
                if "." in date_str:
                    parts = date_str.split(".")
                    microsec_part = parts[1].split("+")[0]
                    # Garantir 6 dígitos nos microsegundos
                    if len(microsec_part) < 6:
                        microsec_part = microsec_part.ljust(6, '0')
                    date_str = f"{parts[0]}.{microsec_part}+00:00"

                status_date = datetime.fromisoformat(date_str)
                dias_no_status = (datetime.now(timezone.utc) - status_date).days
            except Exception as e:
                logger.warning(f"Erro ao processar data: {e}")
                dias_no_status = 0

        # Definir colunas baseado se é monetizado ou não
        if canal.data.get("monetizado"):
            colunas = [
                {
                    "id": "em_crescimento",
                    "label": "Em Crescimento",
                    "emoji": "🟢",
                    "descricao": "Canal saudável e escalando",
                    "is_current": canal.data.get("kanban_status") == "em_crescimento"
                },
                {
                    "id": "em_testes_novos",
                    "label": "Em Testes Novos",
                    "emoji": "🟡",
                    "descricao": "Perdeu tração, testando novas estratégias",
                    "is_current": canal.data.get("kanban_status") == "em_testes_novos"
                },
                {
                    "id": "canal_constante",
                    "label": "Canal Constante",
                    "emoji": "🔵",
                    "descricao": "Estável, performance previsível",
                    "is_current": canal.data.get("kanban_status") == "canal_constante"
                }
            ]
        else:
            colunas = [
                {
                    "id": "em_teste_inicial",
                    "label": "Em Teste Inicial",
                    "emoji": "🟡",
                    "descricao": "Canal testando micro-nichos pela primeira vez",
                    "is_current": canal.data.get("kanban_status") == "em_teste_inicial"
                },
                {
                    "id": "demonstrando_tracao",
                    "label": "Demonstrando Tração",
                    "emoji": "🟢",
                    "descricao": "Sinais positivos, vídeos viralizando",
                    "is_current": canal.data.get("kanban_status") == "demonstrando_tracao"
                },
                {
                    "id": "em_andamento",
                    "label": "Em Andamento p/ Monetizar",
                    "emoji": "🟠",
                    "descricao": "Caminhando para 1K subs e 4K horas",
                    "is_current": canal.data.get("kanban_status") == "em_andamento"
                },
                {
                    "id": "monetizado",
                    "label": "Monetizado",
                    "emoji": "🔵",
                    "descricao": "Atingiu requisitos de monetização",
                    "is_current": canal.data.get("kanban_status") == "monetizado"
                }
            ]

        # Buscar notas do canal
        notas = db_client.supabase.table("kanban_notes")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .order("position", desc=False)\
            .execute()

        # Buscar histórico (últimos 20 registros não deletados)
        historico = db_client.supabase.table("kanban_history")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .eq("is_deleted", False)\
            .order("performed_at", desc=True)\
            .limit(20)\
            .execute()

        return {
            "canal": {
                "id": canal.data["id"],
                "nome": canal.data["nome_canal"],
                "subnicho": canal.data["subnicho"],
                "monetizado": canal.data.get("monetizado", False),
                "status_atual": canal.data.get("kanban_status"),
                "status_since": canal.data.get("kanban_status_since"),
                "dias_no_status": dias_no_status
            },
            "colunas": colunas,
            "notas": notas.data if notas.data else [],
            "historico": historico.data if historico.data else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao buscar kanban board: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def move_kanban_status(db_client, canal_id: int, new_status: str):
    """
    Move um canal para um novo status no Kanban.
    """
    try:
        # Verificar se o canal existe e é nosso
        canal = db_client.supabase.table("canais_monitorados")\
            .select("id, nome_canal, kanban_status")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        old_status = canal.data.get("kanban_status")

        # Atualizar status
        result = db_client.supabase.table("canais_monitorados")\
            .update({
                "kanban_status": new_status,
                "kanban_status_since": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", canal_id)\
            .execute()

        # Registrar no histórico
        db_client.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "status_change",
            "description": f"Status mudou de {old_status or 'indefinido'} para {new_status}",
            "details": {
                "from_status": old_status,
                "to_status": new_status
            }
        }).execute()

        return {"success": True, "message": "Status atualizado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao mover status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_kanban_note(db_client, canal_id: int, note_text: str, note_color: str = "yellow"):
    """
    Cria uma nova nota para um canal.
    """
    try:
        # Verificar se o canal existe e é nosso
        canal = db_client.supabase.table("canais_monitorados")\
            .select("id, nome_canal")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Buscar última posição
        last_note = db_client.supabase.table("kanban_notes")\
            .select("position")\
            .eq("canal_id", canal_id)\
            .order("position", desc=True)\
            .limit(1)\
            .execute()

        next_position = 1
        if last_note.data:
            next_position = last_note.data[0]["position"] + 1

        # Criar nota
        nota = db_client.supabase.table("kanban_notes").insert({
            "canal_id": canal_id,
            "note_text": note_text,
            "note_color": note_color,
            "position": next_position
        }).execute()

        # Registrar no histórico
        db_client.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "note_added",
            "description": f"Nota {note_color} adicionada",
            "details": {
                "note_id": nota.data[0]["id"],
                "color": note_color
            }
        }).execute()

        return nota.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao criar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_kanban_note(db_client, note_id: int, note_text: Optional[str] = None, note_color: Optional[str] = None):
    """
    Atualiza uma nota existente.
    """
    try:
        # Buscar nota atual
        nota_atual = db_client.supabase.table("kanban_notes")\
            .select("*")\
            .eq("id", note_id)\
            .single()\
            .execute()

        if not nota_atual.data:
            raise HTTPException(status_code=404, detail="Nota não encontrada")

        # Preparar campos para atualizar
        update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if note_text is not None:
            update_fields["note_text"] = note_text
        if note_color is not None:
            update_fields["note_color"] = note_color

        # Atualizar nota
        result = db_client.supabase.table("kanban_notes")\
            .update(update_fields)\
            .eq("id", note_id)\
            .execute()

        # Registrar no histórico
        db_client.supabase.table("kanban_history").insert({
            "canal_id": nota_atual.data["canal_id"],
            "action_type": "note_edited",
            "description": f"Nota editada",
            "details": {
                "note_id": note_id,
                "old_color": nota_atual.data["note_color"],
                "new_color": note_color or nota_atual.data["note_color"]
            }
        }).execute()

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao atualizar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_kanban_note(db_client, note_id: int):
    """
    Deleta uma nota.
    """
    try:
        # Buscar nota antes de deletar
        nota = db_client.supabase.table("kanban_notes")\
            .select("canal_id, note_color")\
            .eq("id", note_id)\
            .single()\
            .execute()

        if not nota.data:
            raise HTTPException(status_code=404, detail="Nota não encontrada")

        # Deletar nota
        db_client.supabase.table("kanban_notes")\
            .delete()\
            .eq("id", note_id)\
            .execute()

        # Registrar no histórico
        db_client.supabase.table("kanban_history").insert({
            "canal_id": nota.data["canal_id"],
            "action_type": "note_deleted",
            "description": f"Nota {nota.data['note_color']} removida",
            "details": {
                "note_id": note_id,
                "color": nota.data["note_color"]
            }
        }).execute()

        return {"success": True, "message": "Nota deletada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao deletar nota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def reorder_kanban_notes(db_client, canal_id: int, note_positions: List[Dict[str, int]]):
    """
    Reordena as notas de um canal.
    """
    try:
        # Verificar se o canal existe
        canal = db_client.supabase.table("canais_monitorados")\
            .select("id")\
            .eq("id", canal_id)\
            .eq("tipo", "nosso")\
            .single()\
            .execute()

        if not canal.data:
            raise HTTPException(status_code=404, detail="Canal não encontrado")

        # Atualizar posições
        for item in note_positions:
            db_client.supabase.table("kanban_notes")\
                .update({"position": item["position"]})\
                .eq("id", item["note_id"])\
                .eq("canal_id", canal_id)\
                .execute()

        # Registrar no histórico
        db_client.supabase.table("kanban_history").insert({
            "canal_id": canal_id,
            "action_type": "note_reordered",
            "description": "Notas reordenadas",
            "details": {"positions": note_positions}
        }).execute()

        return {"success": True, "message": "Notas reordenadas com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao reordenar notas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_kanban_history(db_client, canal_id: int, limit: int = 50):
    """
    Retorna o histórico de ações de um canal.
    """
    try:
        historico = db_client.supabase.table("kanban_history")\
            .select("*")\
            .eq("canal_id", canal_id)\
            .eq("is_deleted", False)\
            .order("performed_at", desc=True)\
            .limit(limit)\
            .execute()

        return historico.data if historico.data else []

    except Exception as e:
        logging.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_history_item(db_client, history_id: int):
    """
    Remove um item do histórico (soft delete).
    """
    try:
        result = db_client.supabase.table("kanban_history")\
            .update({"is_deleted": True})\
            .eq("id", history_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Item de histórico não encontrado")

        return {"success": True, "message": "Item removido do histórico"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao deletar item do histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# ROTAS (Adicionar no final do main.py, antes de app.mount)
# =====================================================

# KANBAN ENDPOINTS
@app.get("/api/kanban/structure")
async def kanban_structure_endpoint():
    """Retorna a estrutura completa do Kanban"""
    return await get_kanban_structure(db_client)

@app.get("/api/kanban/canal/{canal_id}/board")
async def kanban_board_endpoint(canal_id: int):
    """Retorna o quadro Kanban de um canal específico"""
    return await get_kanban_board(db_client, canal_id)

@app.patch("/api/kanban/canal/{canal_id}/move-status")
async def kanban_move_status_endpoint(canal_id: int, request: KanbanMoveStatusRequest):
    """Move um canal para outro status"""
    return await move_kanban_status(db_client, canal_id, request.new_status)

@app.post("/api/kanban/canal/{canal_id}/note")
async def kanban_create_note_endpoint(canal_id: int, request: KanbanNoteRequest):
    """Cria uma nova nota para o canal"""
    return await create_kanban_note(db_client, canal_id, request.note_text, request.note_color)

@app.patch("/api/kanban/note/{note_id}")
async def kanban_update_note_endpoint(note_id: int, request: KanbanNoteUpdateRequest):
    """Atualiza uma nota existente"""
    return await update_kanban_note(db_client, note_id, request.note_text, request.note_color)

@app.delete("/api/kanban/note/{note_id}")
async def kanban_delete_note_endpoint(note_id: int):
    """Deleta uma nota"""
    return await delete_kanban_note(db_client, note_id)

@app.patch("/api/kanban/canal/{canal_id}/reorder-notes")
async def kanban_reorder_notes_endpoint(canal_id: int, request: KanbanReorderNotesRequest):
    """Reordena as notas de um canal"""
    return await reorder_kanban_notes(db_client, canal_id, request.note_positions)

@app.get("/api/kanban/canal/{canal_id}/history")
async def kanban_history_endpoint(canal_id: int, limit: int = Query(50, ge=1, le=100)):
    """Retorna o histórico de ações do canal"""
    return await get_kanban_history(db_client, canal_id, limit)

@app.delete("/api/kanban/history/{history_id}")
async def kanban_delete_history_endpoint(history_id: int):
    """Remove um item do histórico (soft delete)"""
    return await delete_history_item(db_client, history_id)

# =====================================================
# FIM DOS ENDPOINTS KANBAN
# =====================================================