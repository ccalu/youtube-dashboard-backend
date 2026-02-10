"""
Script para FORÇAR upload manual de canais específicos
VERSÃO CORRIGIDA - Agora salva no banco de dados corretamente
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
import pytz
from dotenv import load_dotenv
from supabase import create_client

# Adicionar diretório ao path para importar daily_uploader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis
load_dotenv()

# Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Importar o uploader
try:
    from daily_uploader import DailyUploader
    print("[OK] daily_uploader.py importado com sucesso")
except ImportError as e:
    print(f"[ERRO] Não foi possível importar daily_uploader: {e}")
    sys.exit(1)

async def forcar_upload_canal(uploader, canal_nome=None, canal_id=None):
    """Força upload de um canal específico e SALVA NO BANCO"""

    br_tz = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(br_tz).strftime('%Y-%m-%d')

    # Criar cliente Supabase com SERVICE_KEY para bypass RLS
    supabase = create_client(SUPABASE_URL, SERVICE_KEY)

    print(f"\n{'='*60}")
    print(f"  FORÇANDO UPLOAD - {canal_nome or canal_id}")
    print(f"{'='*60}\n")

    try:
        # Buscar informações do canal
        if canal_nome:
            canal_result = uploader.supabase.table('yt_channels')\
                .select('*')\
                .eq('channel_name', canal_nome)\
                .eq('is_active', True)\
                .execute()
        elif canal_id:
            canal_result = uploader.supabase.table('yt_channels')\
                .select('*')\
                .eq('id', canal_id)\
                .eq('is_active', True)\
                .execute()
        else:
            print("[ERRO] Especifique nome ou ID do canal")
            return False

        if not canal_result.data:
            print(f"[ERRO] Canal '{canal_nome or canal_id}' não encontrado ou não está ativo")
            return False

        canal = canal_result.data[0]
        print(f"[INFO] Canal encontrado: {canal['channel_name']}")
        print(f"       ID: {canal['id']}")
        print(f"       Channel ID: {canal['channel_id']}")
        print(f"       Spreadsheet: {canal.get('spreadsheet_id', 'N/A')[:30]}...")

        # Verificar se existe registro para hoje
        existing = supabase.table('yt_canal_upload_diario').select('*')\
            .eq('channel_id', canal['channel_id'])\
            .eq('data', hoje)\
            .execute()

        if not existing.data:
            # Criar registro inicial
            print(f"\n[INFO] Criando registro para hoje...")
            supabase.table('yt_canal_upload_diario').insert({
                'channel_id': canal['channel_id'],
                'channel_name': canal['channel_name'],
                'data': hoje,
                'status': 'pendente',
                'upload_realizado': False,
                'hora_processamento': datetime.now(br_tz).isoformat()
            }).execute()

        # Processar upload
        print(f"\n[INFO] Processando upload...")
        resultado = await uploader._process_canal_upload(canal, hoje, retry_attempt=0)

        if resultado:
            status = resultado.get('status', 'erro')

            # ATUALIZAR BANCO DE DADOS COM O RESULTADO
            update_data = {
                'status': status,
                'hora_processamento': datetime.now(br_tz).isoformat()
            }

            if status == 'sucesso':
                update_data['upload_realizado'] = True
                update_data['video_titulo'] = resultado.get('video_title', '')
                update_data['youtube_video_id'] = resultado.get('youtube_video_id', '')

                # Construir URL do vídeo
                video_id = resultado.get('youtube_video_id', '')
                if video_id:
                    update_data['video_url'] = f"https://youtube.com/watch?v={video_id}"

                # Atualizar no banco
                supabase.table('yt_canal_upload_diario').update(update_data)\
                    .eq('channel_id', canal['channel_id'])\
                    .eq('data', hoje)\
                    .execute()

                print(f"[SUCESSO] Upload realizado e SALVO no banco!")
                print(f"          Vídeo: {resultado.get('video_title', 'N/A')}")
                print(f"          YouTube ID: {resultado.get('youtube_video_id', 'N/A')}")
                print(f"          Status no banco: sucesso")
                return True

            elif status == 'sem_video':
                update_data['upload_realizado'] = False

                # Atualizar no banco
                supabase.table('yt_canal_upload_diario').update(update_data)\
                    .eq('channel_id', canal['channel_id'])\
                    .eq('data', hoje)\
                    .execute()

                print(f"[AVISO] Nenhum vídeo pronto encontrado na planilha")
                print(f"        Status no banco: sem_video")
                print(f"        Verifique se há vídeos com:")
                print(f"        - Status = 'done' (minúsculo)")
                print(f"        - Post = vazio")
                print(f"        - Published Date = vazio")
                print(f"        - Drive URL = preenchido")
                return False

            elif status == 'erro':
                update_data['upload_realizado'] = False
                update_data['erro_detalhes'] = resultado.get('erro', 'Erro desconhecido')

                # Atualizar no banco
                supabase.table('yt_canal_upload_diario').update(update_data)\
                    .eq('channel_id', canal['channel_id'])\
                    .eq('data', hoje)\
                    .execute()

                print(f"[ERRO] Falha no upload: {resultado.get('erro', 'Erro desconhecido')}")
                print(f"       Status no banco: erro")
                return False

            else:
                print(f"[INFO] Status: {status}")
                print(f"       Detalhes: {resultado}")
                return False
        else:
            # Atualizar como erro se não houver resultado
            supabase.table('yt_canal_upload_diario').update({
                'status': 'erro',
                'upload_realizado': False,
                'hora_processamento': datetime.now(br_tz).isoformat(),
                'erro_detalhes': 'Nenhum resultado retornado do processamento'
            }).eq('channel_id', canal['channel_id']).eq('data', hoje).execute()

            print(f"[ERRO] Nenhum resultado retornado")
            return False

    except Exception as e:
        print(f"[ERRO] Erro ao processar: {str(e)}")

        # Tentar atualizar banco como erro
        try:
            if canal:
                supabase.table('yt_canal_upload_diario').update({
                    'status': 'erro',
                    'upload_realizado': False,
                    'hora_processamento': datetime.now(br_tz).isoformat(),
                    'erro_detalhes': str(e)
                }).eq('channel_id', canal['channel_id']).eq('data', hoje).execute()
        except:
            pass

        return False

async def main():
    parser = argparse.ArgumentParser(description='Forçar upload manual de canais')
    parser.add_argument('--canal', type=str, help='Nome do canal')
    parser.add_argument('--id', type=int, help='ID do canal')
    parser.add_argument('--todos', action='store_true', help='Processar todos os canais sem upload')

    args = parser.parse_args()

    # Criar instância do uploader
    uploader = DailyUploader()

    if args.todos:
        # Processar todos os canais sem upload
        br_tz = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.now(br_tz).strftime('%Y-%m-%d')

        # Buscar canais ativos
        canais = uploader.supabase.table('yt_channels')\
            .select('*')\
            .eq('is_active', True)\
            .eq('upload_automatico', True)\
            .execute()

        print(f"[INFO] Total de canais ativos: {len(canais.data)}")

        # Buscar uploads de hoje
        uploads_hoje = uploader.supabase.table('yt_canal_upload_diario')\
            .select('channel_id')\
            .eq('data', hoje)\
            .eq('status', 'sucesso')\
            .execute()

        canais_com_upload = {u['channel_id'] for u in uploads_hoje.data}

        # Processar canais sem upload
        processados = 0
        sucesso = 0

        for canal in canais.data:
            if canal['channel_id'] not in canais_com_upload:
                print(f"\n[INFO] Processando: {canal['channel_name']}")
                resultado = await forcar_upload_canal(uploader, canal_nome=canal['channel_name'])
                processados += 1
                if resultado:
                    sucesso += 1

        print(f"\n[RESUMO] Processados: {processados} | Sucesso: {sucesso}")

    elif args.canal or args.id:
        # Processar canal específico
        await forcar_upload_canal(uploader, canal_nome=args.canal, canal_id=args.id)
    else:
        print("[ERRO] Especifique --canal, --id ou --todos")
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())