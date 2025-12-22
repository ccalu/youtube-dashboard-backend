"""
Cadastra canal na tabela yt_channels do Supabase
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

# Dados do canal
canal_data = {
    'channel_id': 'UCbB1WtTqBWYdSk3JE6iRNRw',
    'channel_name': 'Sans Limites',
    'proxy_name': 'proxy_c0008_1',
    'proxy_url': 'socks5://MhVF0OljP2EGqcX:uf2UGXy42gmzcXz@46.202.218.132:46073',
    'lingua': 'fr',
    'subnicho': 'mentalidade_masculina_financas',
    'is_active': True
}

print("\n" + "="*70)
print("📝 CADASTRANDO CANAL NO SUPABASE")
print("="*70)
print(f"\n📌 Canal: {canal_data['channel_name']}")
print(f"📌 Channel ID: {canal_data['channel_id']}")
print(f"📌 Proxy: {canal_data['proxy_name']}")
print(f"📌 Língua: {canal_data['lingua']}")
print(f"📌 Subnicho: {canal_data['subnicho']}\n")

try:
    # Verifica se já existe
    existing = supabase.table('yt_channels')\
        .select('*')\
        .eq('channel_id', canal_data['channel_id'])\
        .execute()

    if existing.data:
        print("⚠️  Canal já existe! Atualizando...")
        result = supabase.table('yt_channels')\
            .update(canal_data)\
            .eq('channel_id', canal_data['channel_id'])\
            .execute()
        print("✅ Canal ATUALIZADO com sucesso!")
    else:
        print("⏳ Inserindo novo canal...")
        result = supabase.table('yt_channels')\
            .insert(canal_data)\
            .execute()
        print("✅ Canal CADASTRADO com sucesso!")

    print("\n" + "="*70)
    print("🎉 CANAL CONFIGURADO!")
    print("="*70)
    print("\n📌 Próximo passo: Executar novamente 'processar_oauth_callback.py'")
    print("   para salvar os tokens OAuth!\n")

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}\n")
    import traceback
    traceback.print_exc()
