# -*- coding: utf-8 -*-
"""
Script de Integração do Sistema de Upload Diário com main.py

Este arquivo contém o código necessário para integrar o sistema
de upload diário ao arquivo main.py existente.
"""

# ============================================================
# INSTRUÇÕES DE INTEGRAÇÃO
# ============================================================

"""
ADICIONAR NO main.py:

1. NO INÍCIO DO ARQUIVO (junto com os outros imports):
----------------------------------------
import asyncio
from daily_uploader import schedule_daily_uploader

2. ADICIONAR VARIÁVEL DE CONTROLE (após os imports):
----------------------------------------
# Sistema de Upload Diário
DAILY_UPLOAD_ENABLED = os.getenv("DAILY_UPLOAD_ENABLED", "false").lower() == "true"

3. NO FINAL DO ARQUIVO, ANTES DE app.run() ou uvicorn.run():
----------------------------------------
# Inicia sistema de upload diário se habilitado
if DAILY_UPLOAD_ENABLED:
    async def start_daily_uploader():
        logger.info("📤 Iniciando sistema de upload diário automático")
        await schedule_daily_uploader()

    # Cria task em background
    asyncio.create_task(start_daily_uploader())
    logger.info("✅ Sistema de upload diário ATIVADO")
else:
    logger.info("📤 Sistema de upload diário DESABILITADO")

4. SE MAIN.PY USA FASTAPI, ADICIONAR EVENTOS DE STARTUP:
----------------------------------------
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if DAILY_UPLOAD_ENABLED:
        asyncio.create_task(schedule_daily_uploader())
        logger.info("✅ Sistema de upload diário iniciado")

    yield  # App está rodando

    # Shutdown
    logger.info("Sistema sendo desligado...")

app = FastAPI(lifespan=lifespan)

5. ADICIONAR ENDPOINTS DA API (opcional mas recomendado):
----------------------------------------
@app.post("/api/daily-upload/manual-trigger")
async def trigger_daily_upload_manual():
    '''Dispara upload diário manualmente'''
    from daily_uploader import DailyUploader

    uploader = DailyUploader()
    result = await uploader.execute_daily_upload(retry_attempt=1)

    return {
        "success": True,
        "stats": {
            "sucesso": len(result.get("sucesso", [])),
            "erro": len(result.get("erro", [])),
            "sem_video": len(result.get("sem_video", [])),
            "pulado": len(result.get("pulado", []))
        }
    }

@app.get("/api/daily-upload/status")
async def get_daily_upload_status():
    '''Retorna status do upload diário de hoje'''
    from datetime import datetime

    hoje = datetime.now().date().isoformat()

    # Busca logs de hoje
    logs_result = supabase.table('yt_upload_daily_logs')\
        .select('*')\
        .eq('data', hoje)\
        .order('tentativa_numero', desc=True)\
        .limit(1)\
        .execute()

    if logs_result.data:
        log = logs_result.data[0]
        return {
            "data": hoje,
            "ultima_execucao": log.get("hora_inicio"),
            "tentativa": log.get("tentativa_numero"),
            "stats": {
                "total": log.get("total_canais", 0),
                "sucesso": log.get("total_sucesso", 0),
                "erro": log.get("total_erro", 0),
                "sem_video": log.get("total_sem_video", 0),
                "pulado": log.get("total_pulado", 0)
            },
            "canais_com_erro": log.get("canais_com_erro", []),
            "canais_sem_video": log.get("canais_sem_video", [])
        }

    return {
        "data": hoje,
        "message": "Nenhuma execução hoje ainda"
    }

"""

# ============================================================
# CONFIGURAÇÕES DO RAILWAY
# ============================================================

"""
ADICIONAR NO RAILWAY (Variáveis de Ambiente):

1. Para ATIVAR o sistema:
-------------------------
DAILY_UPLOAD_ENABLED=true

2. Para DESATIVAR o sistema antigo (opcional):
---------------------------------------------
UPLOAD_WORKER_ENABLED=false
SCANNER_ENABLED=false

3. Credenciais Google Sheets (já deve existir):
----------------------------------------------
GOOGLE_SHEETS_CREDENTIALS_2={"type":"service_account",...}

"""

# ============================================================
# CÓDIGO AUXILIAR PARA INTEGRAÇÃO MANUAL
# ============================================================

def add_to_main_startup():
    """
    Código para adicionar ao startup do main.py
    """
    startup_code = """
# Sistema de Upload Diário Automático
async def initialize_daily_uploader():
    '''Inicializa sistema de upload diário em background'''
    if os.getenv("DAILY_UPLOAD_ENABLED", "false").lower() == "true":
        try:
            from daily_uploader import schedule_daily_uploader
            asyncio.create_task(schedule_daily_uploader())
            logger.info("✅ Sistema de upload diário ATIVADO e rodando")
            logger.info("   - Execução principal: Após coleta (~5:30-6:00)")
            logger.info("   - Retry 1: 6:30 AM")
            logger.info("   - Retry 2: 7:00 AM")
            logger.info("   - Dashboard: http://localhost:5002")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar upload diário: {e}")
    else:
        logger.info("📤 Sistema de upload diário DESABILITADO (DAILY_UPLOAD_ENABLED=false)")

# Chamar durante inicialização
asyncio.create_task(initialize_daily_uploader())
"""
    return startup_code


# ============================================================
# VERIFICAÇÃO DE INTEGRAÇÃO
# ============================================================

def verificar_integracao():
    """
    Verifica se o sistema está corretamente integrado
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    print("\n" + "=" * 60)
    print("🔍 VERIFICAÇÃO DE INTEGRAÇÃO")
    print("=" * 60)

    checks = []

    # 1. Verifica variável de ambiente
    daily_enabled = os.getenv("DAILY_UPLOAD_ENABLED", "false").lower() == "true"
    checks.append({
        "item": "DAILY_UPLOAD_ENABLED",
        "status": "✅" if daily_enabled else "❌",
        "valor": str(daily_enabled),
        "recomendacao": "Defina DAILY_UPLOAD_ENABLED=true no Railway" if not daily_enabled else None
    })

    # 2. Verifica credenciais Google Sheets
    sheets_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_2")
    checks.append({
        "item": "GOOGLE_SHEETS_CREDENTIALS_2",
        "status": "✅" if sheets_creds else "❌",
        "valor": "Configurado" if sheets_creds else "Não configurado",
        "recomendacao": "Configure as credenciais no Railway" if not sheets_creds else None
    })

    # 3. Verifica Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    checks.append({
        "item": "SUPABASE_URL",
        "status": "✅" if supabase_url else "❌",
        "valor": "Configurado" if supabase_url else "Não configurado",
        "recomendacao": "Configure SUPABASE_URL no .env" if not supabase_url else None
    })
    checks.append({
        "item": "SUPABASE_KEY",
        "status": "✅" if supabase_key else "❌",
        "valor": "Configurado" if supabase_key else "Não configurado",
        "recomendacao": "Configure SUPABASE_KEY no .env" if not supabase_key else None
    })

    # 4. Verifica se tabelas foram criadas
    try:
        from supabase import create_client
        if supabase_url and supabase_key:
            client = create_client(supabase_url, supabase_key)

            # Verifica coluna upload_automatico
            result = client.table('yt_channels').select('upload_automatico').limit(1).execute()
            checks.append({
                "item": "Coluna upload_automatico",
                "status": "✅",
                "valor": "Existe",
                "recomendacao": None
            })
    except Exception as e:
        checks.append({
            "item": "Coluna upload_automatico",
            "status": "❌",
            "valor": "Não existe",
            "recomendacao": "Execute o SQL em scripts/database/001_add_upload_automatico.sql"
        })

    # Mostra resultados
    print("\nRESULTADOS:")
    print("-" * 60)
    for check in checks:
        print(f"{check['status']} {check['item']}: {check['valor']}")
        if check.get('recomendacao'):
            print(f"   → {check['recomendacao']}")

    # Resumo
    todos_ok = all(c['status'] == "✅" for c in checks)
    print("\n" + "=" * 60)
    if todos_ok:
        print("✅ SISTEMA PRONTO PARA USO!")
        print("\nPróximos passos:")
        print("1. Integre o código no main.py")
        print("2. Faça deploy no Railway")
        print("3. Adicione canais com scripts-temp/add_canal_wizard_v2.py")
        print("4. Acompanhe pelo dashboard: python dashboard_daily_uploads.py")
    else:
        print("⚠️ CORREÇÕES NECESSÁRIAS")
        print("\nResolva os problemas acima antes de continuar.")

    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📋 INTEGRAÇÃO DO SISTEMA DE UPLOAD DIÁRIO")
    print("=" * 60)
    print("\nEste arquivo contém instruções para integrar o sistema")
    print("de upload diário ao main.py existente.")
    print("\n1. Leia as instruções no código")
    print("2. Execute verificar_integracao() para validar")

    verificar = input("\nDeseja verificar a integração agora? (s/n): ").strip().lower()
    if verificar == 's':
        verificar_integracao()