"""
Verifica logs de coleta - investigar duplicação às 5 AM
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("=" * 80)
print("INVESTIGACAO - DUPLICACAO DE COLETA")
print("=" * 80)

# Verificar coletas de hoje
today = datetime.now().date()
print(f"\nData: {today}")

# Buscar logs de coleta (tabela yt_collection_logs ou similar)
# Primeiro vamos ver que tabelas de log existem
print("\n[1] Verificando tabelas de log...")

# Tentar yt_collection_logs
try:
    result = supabase.table("yt_collection_logs")\
        .select("*")\
        .gte("created_at", str(today))\
        .order("created_at", desc=False)\
        .execute()

    if result.data:
        print(f"\n✓ yt_collection_logs: {len(result.data)} registros hoje")

        for log in result.data:
            created_at = log.get('created_at', '')
            status = log.get('status', '')
            channel_id = log.get('channel_id', '')
            message = log.get('message', '')

            # Formatar timestamp
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = created_at

            print(f"  {time_str} - {status} - {channel_id[:20]} - {message[:50]}")
except Exception as e:
    print(f"  Erro ao acessar yt_collection_logs: {e}")

# Verificar também coleta_logs (tabela geral de coletas)
print("\n[2] Verificando coleta_logs (coletas gerais)...")

try:
    result = supabase.table("coleta_logs")\
        .select("*")\
        .gte("inicio", str(today))\
        .order("inicio", desc=False)\
        .execute()

    if result.data:
        print(f"\n✓ coleta_logs: {len(result.data)} coletas hoje\n")

        for log in result.data:
            inicio = log.get('inicio', '')
            fim = log.get('fim', '')
            status = log.get('status', '')
            canais_sucesso = log.get('canais_sucesso', 0)
            canais_erro = log.get('canais_erro', 0)

            # Formatar timestamps
            try:
                dt_inicio = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
                time_inicio = dt_inicio.strftime('%H:%M:%S')
            except:
                time_inicio = inicio

            try:
                if fim:
                    dt_fim = datetime.fromisoformat(fim.replace('Z', '+00:00'))
                    time_fim = dt_fim.strftime('%H:%M:%S')
                else:
                    time_fim = "Em execução"
            except:
                time_fim = fim or "?"

            print(f"Coleta ID {log.get('id')}:")
            print(f"  Início: {time_inicio}")
            print(f"  Fim: {time_fim}")
            print(f"  Status: {status}")
            print(f"  Sucesso: {canais_sucesso} | Erros: {canais_erro}")
            print(f"  Total canais: {log.get('total_canais', 0)}")
            print()
    else:
        print("  Nenhuma coleta registrada hoje")

except Exception as e:
    print(f"  Erro ao acessar coleta_logs: {e}")

# Verificar últimos 3 dias para ver padrão
print("\n[3] Histórico últimos 3 dias...")

three_days_ago = today - timedelta(days=3)

try:
    result = supabase.table("coleta_logs")\
        .select("inicio, status, canais_sucesso")\
        .gte("inicio", str(three_days_ago))\
        .order("inicio", desc=False)\
        .execute()

    if result.data:
        print(f"\nTotal de coletas (últimos 3 dias): {len(result.data)}\n")

        # Agrupar por dia
        by_day = {}
        for log in result.data:
            inicio = log.get('inicio', '')
            try:
                dt = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
                day = dt.date()
                hour = dt.hour

                if day not in by_day:
                    by_day[day] = []
                by_day[day].append({'hour': hour, 'time': dt.strftime('%H:%M')})
            except:
                pass

        for day, coletas in sorted(by_day.items()):
            print(f"{day}:")
            print(f"  Total: {len(coletas)} coletas")
            print(f"  Horários: {', '.join(c['time'] for c in coletas)}")

            if len(coletas) > 1:
                print(f"  ⚠️ DUPLICAÇÃO DETECTADA!")
            print()

except Exception as e:
    print(f"  Erro: {e}")

print("=" * 80)
