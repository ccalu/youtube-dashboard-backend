"""
Verifica duplicação de coletas na tabela coletas_historico
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
print(f"\nData: {today}\n")

# Buscar coletas dos últimos 3 dias
three_days_ago = today - timedelta(days=3)

result = supabase.table("coletas_historico")\
    .select("*")\
    .gte("data_inicio", str(three_days_ago))\
    .order("data_inicio", desc=False)\
    .execute()

if not result.data:
    print("Nenhuma coleta encontrada")
else:
    print(f"Total de coletas (últimos 3 dias): {len(result.data)}\n")
    print("=" * 80)

    # Agrupar por dia
    by_day = {}

    for coleta in result.data:
        coleta_id = coleta.get('id')
        data_inicio = coleta.get('data_inicio')
        data_fim = coleta.get('data_fim')
        status = coleta.get('status')
        canais_sucesso = coleta.get('canais_sucesso', 0)
        canais_erro = coleta.get('canais_erro', 0)
        canais_total = coleta.get('canais_total', 0)

        # Parsear data
        try:
            dt_inicio = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
            day = dt_inicio.date()
            time_inicio = dt_inicio.strftime('%H:%M:%S')

            if data_fim:
                dt_fim = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
                time_fim = dt_fim.strftime('%H:%M:%S')
                duracao = (dt_fim - dt_inicio).total_seconds() / 60
            else:
                time_fim = "Em andamento"
                duracao = None

            if day not in by_day:
                by_day[day] = []

            by_day[day].append({
                'id': coleta_id,
                'time': time_inicio,
                'time_fim': time_fim,
                'duracao': duracao,
                'status': status,
                'sucesso': canais_sucesso,
                'erro': canais_erro,
                'total': canais_total,
                'dt_completo': dt_inicio
            })

        except Exception as e:
            print(f"Erro ao parsear data {data_inicio}: {e}")

    # Exibir por dia
    for day, coletas in sorted(by_day.items()):
        print(f"\n[{day}] - {len(coletas)} coleta(s)")
        print("-" * 80)

        for i, c in enumerate(coletas, 1):
            print(f"\nColeta #{i} (ID: {c['id']})")
            print(f"  Início: {c['time']}")
            print(f"  Fim: {c['time_fim']}")
            if c['duracao']:
                print(f"  Duração: {c['duracao']:.1f} minutos")
            print(f"  Status: {c['status']}")
            print(f"  Resultado: {c['sucesso']} sucesso / {c['erro']} erros (total: {c['total']})")

        # Detectar duplicação
        if len(coletas) > 1:
            print(f"\n⚠️ DUPLICAÇÃO DETECTADA!")
            print(f"   {len(coletas)} coletas no mesmo dia!")

            # Verificar se são próximas
            if len(coletas) >= 2:
                diff_minutos = (coletas[1]['dt_completo'] - coletas[0]['dt_completo']).total_seconds() / 60
                print(f"   Diferença entre 1ª e 2ª: {diff_minutos:.0f} minutos")

                if diff_minutos < 5:
                    print(f"   🚨 COLETAS QUASE SIMULTÂNEAS!")
                elif diff_minutos < 60:
                    print(f"   ⚠️ Coletas no mesmo horário")

    print("\n" + "=" * 80)

# Verificar especificamente hoje
print("\nFOCO: COLETAS DE HOJE")
print("=" * 80)

today_coletas = supabase.table("coletas_historico")\
    .select("*")\
    .gte("data_inicio", str(today))\
    .order("data_inicio", desc=False)\
    .execute()

if today_coletas.data:
    print(f"\nTotal hoje: {len(today_coletas.data)} coleta(s)\n")

    for coleta in today_coletas.data:
        data_inicio = coleta.get('data_inicio')
        dt = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))

        print(f"ID {coleta['id']}: {dt.strftime('%H:%M:%S')}")
        print(f"  Status: {coleta['status']}")
        print(f"  Canais: {coleta['canais_sucesso']}/{coleta['canais_total']}")
        print()

else:
    print("\nNenhuma coleta hoje")

print("=" * 80)
