"""
Script SIMPLIFICADO para cadastrar canal no Supabase
Proxy_name serve apenas como identificador/organização
"""

from supabase import create_client
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*70)
print("📝 CADASTRAR CANAL NO SISTEMA DE UPLOAD")
print("="*70)
print("\n⚠️  IMPORTANTE: Execute 'autorizar_canal_oauth.py' ANTES deste script!")
print("   (para gerar os tokens OAuth)\n")

# Entrada de dados
print("=" * 70)
print("DADOS DO CANAL:")
print("=" * 70 + "\n")

channel_id = input("Channel ID (UCxxxxxxxxx): ").strip()
channel_name = input("Nome do Canal: ").strip()
proxy_name = input("Proxy Name (ex: proxy_c0008_1) [identificador]: ").strip()
lingua = input("Língua (pt, en, es, fr, etc): ").strip()
subnicho = input("Subnicho: ").strip()

# Validação básica
if not channel_id or not channel_id.startswith('UC'):
    print("\n❌ ERRO: Channel ID inválido!")
    exit(1)

if not channel_name or not lingua or not subnicho:
    print("\n❌ ERRO: Preencha todos os campos obrigatórios!")
    exit(1)

# Dados do canal (SEM proxy_url - não usa SOCKS5)
canal_data = {
    'channel_id': channel_id,
    'channel_name': channel_name,
    'proxy_name': proxy_name if proxy_name else None,  # Opcional
    'lingua': lingua,
    'subnicho': subnicho,
    'is_active': True
}

print("\n" + "="*70)
print("RESUMO:")
print("="*70)
print(f"\n📌 Canal: {canal_data['channel_name']}")
print(f"📌 Channel ID: {canal_data['channel_id']}")
print(f"📌 Proxy: {canal_data['proxy_name'] or '(sem grupo)'}")
print(f"📌 Língua: {canal_data['lingua']}")
print(f"📌 Subnicho: {canal_data['subnicho']}\n")

confirma = input("Confirma cadastro? (s/n): ").strip().lower()

if confirma != 's':
    print("\n❌ Cadastro cancelado!")
    exit(0)

try:
    # Verifica se já existe
    existing = supabase.table('yt_channels')\
        .select('*')\
        .eq('channel_id', canal_data['channel_id'])\
        .execute()

    if existing.data:
        print("\n⚠️  Canal já existe! Atualizando...")
        result = supabase.table('yt_channels')\
            .update(canal_data)\
            .eq('channel_id', canal_data['channel_id'])\
            .execute()
        print("✅ Canal ATUALIZADO com sucesso!")
    else:
        print("\n⏳ Inserindo novo canal...")
        result = supabase.table('yt_channels')\
            .insert(canal_data)\
            .execute()
        print("✅ Canal CADASTRADO com sucesso!")

    print("\n" + "="*70)
    print("🎉 CANAL CONFIGURADO!")
    print("="*70)
    print("\n📌 Sistema pronto para upload!")
    print("📌 Teste editando célula na planilha Google Sheets\n")

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}\n")
    import traceback
    traceback.print_exc()
