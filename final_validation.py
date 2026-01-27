"""
VALIDAÇÃO FINAL DO SISTEMA DE COMENTÁRIOS
Data: 27/01/2026

Verificação completa sem emojis (compatível com Windows)
"""

import asyncio
from datetime import datetime
from database import SupabaseClient
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

async def validate_system():
    """Validação completa do sistema"""

    print("\n" + "="*60)
    print("VALIDACAO FINAL DO SISTEMA DE COMENTARIOS")
    print("="*60 + "\n")

    db = SupabaseClient()

    # 1. VERIFICAR COMENTÁRIOS TOTAIS
    print("[1] VERIFICANDO COMENTARIOS...")

    # Total de comentários
    total = db.supabase.table('video_comments').select('*', count='exact', head=True).execute()
    print(f"   Total de comentarios: {total.count}")

    # Comentários vazios
    vazios = db.supabase.table('video_comments').select(
        '*', count='exact', head=True
    ).or_('comment_text_original.is.null,comment_text_original.eq.').execute()
    print(f"   Comentarios vazios: {vazios.count}")

    # Comentários com texto
    com_texto = total.count - vazios.count
    print(f"   Comentarios com texto: {com_texto}")

    # 2. VERIFICAR TRADUÇÕES
    print("\n[2] VERIFICANDO TRADUCOES...")

    # Comentários traduzidos
    traduzidos = db.supabase.table('video_comments').select(
        '*', count='exact', head=True
    ).not_.is_('comment_text_pt', 'null').neq('comment_text_pt', '').execute()
    print(f"   Comentarios traduzidos: {traduzidos.count}")

    # Percentual traduzido
    if com_texto > 0:
        perc_traduzido = (traduzidos.count / com_texto) * 100
        print(f"   Percentual traduzido: {perc_traduzido:.1f}%")

    # 3. VERIFICAR RESPOSTAS
    print("\n[3] VERIFICANDO RESPOSTAS...")

    # Respostas geradas
    respostas = db.supabase.table('video_comments').select(
        '*', count='exact', head=True
    ).not_.is_('suggested_response', 'null').execute()
    print(f"   Respostas geradas: {respostas.count}")

    # 4. VERIFICAR NOSSOS CANAIS
    print("\n[4] VERIFICANDO NOSSOS CANAIS...")

    # Nossos canais
    nossos = db.supabase.table('canais_monitorados').select(
        '*', count='exact', head=True
    ).eq('tipo', 'nosso').execute()
    print(f"   Nossos canais: {nossos.count}")

    # Canais monetizados
    monetizados = db.supabase.table('canais_monitorados').select(
        '*', count='exact', head=True
    ).eq('subnicho', 'Monetizados').execute()
    print(f"   Canais monetizados: {monetizados.count}")

    # 5. VERIFICAR COMENTÁRIOS DOS NOSSOS CANAIS
    print("\n[5] VERIFICANDO COMENTARIOS DOS NOSSOS CANAIS...")

    nossos_data = db.supabase.table('canais_monitorados').select('id').eq('tipo', 'nosso').execute()
    nossos_ids = [c['id'] for c in nossos_data.data] if nossos_data.data else []

    if nossos_ids:
        # Comentários dos nossos canais
        nossos_comments = db.supabase.table('video_comments').select(
            '*', count='exact', head=True
        ).in_('canal_id', nossos_ids).execute()
        print(f"   Comentarios dos nossos canais: {nossos_comments.count}")

        # Comentários traduzidos dos nossos canais
        nossos_traduzidos = db.supabase.table('video_comments').select(
            '*', count='exact', head=True
        ).in_('canal_id', nossos_ids).not_.is_('comment_text_pt', 'null').neq(
            'comment_text_pt', ''
        ).execute()
        print(f"   Traduzidos (nossos canais): {nossos_traduzidos.count}")

        # Percentual
        if nossos_comments.count > 0:
            perc_nossos = (nossos_traduzidos.count / nossos_comments.count) * 100
            print(f"   Percentual traduzido (nossos): {perc_nossos:.1f}%")

    # 6. VERIFICAR ARQUIVOS NECESSÁRIOS
    print("\n[6] VERIFICANDO ARQUIVOS DO SISTEMA...")

    required_files = [
        'workflow_comments_fixed.py',
        'post_collection_automation.py',
        'translate_comments_optimized.py',
        'comments_manager.py',
        'recover_lost_comments.py'
    ]

    all_files_ok = True
    for file in required_files:
        exists = os.path.exists(file)
        status = "OK" if exists else "FALTANDO"
        print(f"   {file}: {status}")
        if not exists:
            all_files_ok = False

    # 7. RESULTADO FINAL
    print("\n" + "="*60)
    print("RESULTADO DA VALIDACAO")
    print("="*60)

    # Análise dos resultados
    issues = []

    if vazios.count > 100:
        issues.append(f"Muitos comentarios vazios ({vazios.count})")

    if perc_traduzido < 90:
        issues.append(f"Traducao incompleta ({perc_traduzido:.1f}%)")

    if not all_files_ok:
        issues.append("Arquivos do sistema faltando")

    if respostas.count == 0:
        issues.append("Nenhuma resposta gerada")

    if issues:
        print("\nPROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nSTATUS: SISTEMA PRECISA DE AJUSTES")
    else:
        print("\n*** SISTEMA 100% FUNCIONAL ***")
        print("*** PRONTO PARA PRODUCAO ***")

    # Estatísticas finais
    print("\n" + "="*60)
    print("ESTATISTICAS FINAIS")
    print("="*60)
    print(f"Total de comentarios: {total.count}")
    print(f"Comentarios traduzidos: {traduzidos.count}")
    print(f"Respostas geradas: {respostas.count}")
    print(f"Nossos canais: {nossos.count}")
    print(f"Canais monetizados: {monetizados.count}")

    # Data e hora
    print(f"\nValidacao executada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60 + "\n")

    return {
        'total': total.count,
        'traduzidos': traduzidos.count,
        'respostas': respostas.count,
        'issues': issues
    }

if __name__ == "__main__":
    asyncio.run(validate_system())