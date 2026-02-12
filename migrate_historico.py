#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Migração de Dados Históricos
---------------------------------------
Copia registros com status 'sem_video' e 'erro' da tabela diária
para a tabela histórico, preservando dados completos.

Autor: Claude
Data: 11/02/2026
"""

import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Usar service role para bypass RLS
)

def migrar_dados_historicos():
    """Migra dados faltantes da tabela diária para o histórico"""

    try:
        logger.info("=== INICIANDO MIGRAÇÃO DE DADOS HISTÓRICOS ===")

        # Definir período (últimos 60 dias para garantir)
        hoje = datetime.now(timezone.utc).date()
        data_inicio = hoje - timedelta(days=60)

        logger.info(f"Período: {data_inicio} até {hoje}")

        # Buscar TODOS os registros da tabela diária
        logger.info("Buscando dados da tabela yt_canal_upload_diario...")
        response_diario = supabase.table('yt_canal_upload_diario')\
            .select('*')\
            .gte('data', data_inicio.isoformat())\
            .in_('status', ['sem_video', 'erro'])\
            .execute()

        if not response_diario.data:
            logger.warning("Nenhum registro de 'sem_video' ou 'erro' encontrado na tabela diária")
            return

        logger.info(f"Encontrados {len(response_diario.data)} registros para migrar")

        # Buscar registros já existentes no histórico para evitar duplicação
        logger.info("Verificando registros existentes no histórico...")
        response_historico = supabase.table('yt_canal_upload_historico')\
            .select('channel_id,data,status')\
            .gte('data', data_inicio.isoformat())\
            .execute()

        # Criar set de chaves únicas para verificação rápida
        historico_keys = {
            (item['channel_id'], item['data'], item['status'])
            for item in response_historico.data
        } if response_historico.data else set()

        logger.info(f"Registros já existentes no histórico: {len(historico_keys)}")

        # Processar cada registro da tabela diária
        registros_inseridos = 0
        registros_pulados = 0

        for item_diario in response_diario.data:
            # Criar chave única
            key = (item_diario['channel_id'], item_diario['data'], item_diario['status'])

            # Verificar se já existe
            if key in historico_keys:
                registros_pulados += 1
                continue

            # Preparar dados para inserção (removendo campos que não existem no histórico)
            historico_data = {
                'channel_id': item_diario['channel_id'],
                'channel_name': item_diario.get('channel_name'),
                'data': item_diario['data'],
                'status': item_diario['status'],
                'video_titulo': item_diario.get('video_titulo'),
                'video_url': item_diario.get('video_url'),
                'youtube_video_id': item_diario.get('youtube_video_id'),
                'hora_processamento': item_diario.get('hora_processamento'),
                'erro_mensagem': item_diario.get('erro_mensagem'),
                'tentativa_numero': item_diario.get('tentativa_numero', 1)
                # Removido: upload_realizado não existe na tabela de histórico
            }

            # Inserir no histórico
            try:
                supabase.table('yt_canal_upload_historico')\
                    .insert(historico_data)\
                    .execute()

                registros_inseridos += 1

                if registros_inseridos % 10 == 0:
                    logger.info(f"Progresso: {registros_inseridos} registros inseridos...")

            except Exception as e:
                logger.error(f"Erro ao inserir registro {key}: {e}")
                continue

        # Relatório final
        logger.info("=== MIGRAÇÃO CONCLUÍDA ===")
        logger.info(f"✅ Registros inseridos: {registros_inseridos}")
        logger.info(f"⏭️  Registros pulados (já existentes): {registros_pulados}")
        logger.info(f"📊 Total processado: {registros_inseridos + registros_pulados}")

        # Verificar resultado
        if registros_inseridos > 0:
            logger.info("\n🎉 SUCESSO! Dados históricos migrados com sucesso!")
            logger.info("Os contadores do dashboard agora mostrarão valores corretos para todas as datas.")
        else:
            logger.info("\nNenhum novo registro foi necessário. Histórico já está completo.")

    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        raise

def verificar_resultado():
    """Verifica e exibe estatísticas após migração"""

    logger.info("\n=== VERIFICANDO RESULTADO ===")

    # Contar registros por status
    hoje = datetime.now(timezone.utc).date()
    data_inicio = hoje - timedelta(days=30)

    response = supabase.table('yt_canal_upload_historico')\
        .select('data,status', count='exact')\
        .gte('data', data_inicio.isoformat())\
        .execute()

    if response.data:
        # Agrupar por data e status
        stats = {}
        for item in response.data:
            data = item['data']
            status = item['status']

            if data not in stats:
                stats[data] = {'sucesso': 0, 'erro': 0, 'sem_video': 0}

            stats[data][status] = stats[data].get(status, 0) + 1

        # Exibir estatísticas
        logger.info("\nEstatísticas por data (últimos 5 dias):")
        for data in sorted(stats.keys(), reverse=True)[:5]:
            s = stats[data]
            logger.info(f"  {data}: ✅ {s['sucesso']} | ⚠️ {s['sem_video']} | ❌ {s['erro']}")

if __name__ == "__main__":
    try:
        # Executar migração
        migrar_dados_historicos()

        # Verificar resultado
        verificar_resultado()

    except KeyboardInterrupt:
        logger.info("\n⚠️ Migração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro fatal: {e}")