"""
SCRIPT DE VALIDAÇÃO DETALHADA DOS RESULTADOS
Data: 27/01/2026
Autor: Claude

Este script valida detalhadamente os resultados do processamento de comentários.
Verifica traduções, respostas, e gera relatório completo.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import SupabaseClient
from dotenv import load_dotenv
import random
from colorama import init, Fore, Style

# Inicializar colorama
init()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class ResultValidator:
    """Valida resultados do processamento de comentários"""

    def __init__(self):
        self.db = SupabaseClient()
        self.validation_results = {
            'translations': {'valid': 0, 'invalid': 0, 'samples': []},
            'responses': {'valid': 0, 'invalid': 0, 'samples': []},
            'coverage': {'total': 0, 'processed': 0, 'pending': 0},
            'quality_issues': []
        }

    async def validate_all(self):
        """Executa validação completa"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("VALIDAÇÃO DETALHADA DOS RESULTADOS")
        print(f"{'='*60}{Style.RESET_ALL}\n")

        # 1. Validar cobertura geral
        await self._validate_coverage()

        # 2. Validar traduções
        await self._validate_translations()

        # 3. Validar respostas
        await self._validate_responses()

        # 4. Validar canais monetizados
        await self._validate_monetized_channels()

        # 5. Verificar problemas de qualidade
        await self._check_quality_issues()

        # 6. Gerar relatório
        self._generate_report()

    async def _validate_coverage(self):
        """Valida cobertura do processamento"""
        print(f"{Fore.YELLOW}[1/5] Validando Cobertura...{Style.RESET_ALL}")

        # Total de comentários dos nossos canais
        nossos_canais = self.db.supabase.table('canais_monitorados').select('id').eq('tipo', 'nosso').execute()
        canal_ids = [c['id'] for c in nossos_canais.data] if nossos_canais.data else []

        if canal_ids:
            # Total de comentários
            total_query = self.db.supabase.table('video_comments').select(
                'id', count='exact', head=True
            ).in_('canal_id', canal_ids).execute()

            self.validation_results['coverage']['total'] = total_query.count

            # Comentários com texto original
            with_text = self.db.supabase.table('video_comments').select(
                'id', count='exact', head=True
            ).in_('canal_id', canal_ids).not_.is_('comment_text_original', 'null').neq(
                'comment_text_original', ''
            ).execute()

            # Comentários traduzidos
            translated = self.db.supabase.table('video_comments').select(
                'id', count='exact', head=True
            ).in_('canal_id', canal_ids).not_.is_('comment_text_pt', 'null').neq(
                'comment_text_pt', ''
            ).execute()

            self.validation_results['coverage']['processed'] = translated.count
            self.validation_results['coverage']['pending'] = with_text.count - translated.count

            print(f"  ✓ Total: {total_query.count} comentários")
            print(f"  ✓ Com texto: {with_text.count}")
            print(f"  ✓ Traduzidos: {translated.count}")
            print(f"  ✓ Pendentes: {self.validation_results['coverage']['pending']}")

            coverage_percent = (translated.count / with_text.count * 100) if with_text.count > 0 else 0
            print(f"  📊 Cobertura: {coverage_percent:.1f}%")

    async def _validate_translations(self):
        """Valida qualidade das traduções"""
        print(f"\n{Fore.YELLOW}[2/5] Validando Traduções...{Style.RESET_ALL}")

        # Buscar amostra de traduções
        sample = self.db.supabase.table('video_comments').select(
            'comment_text_original, comment_text_pt, author_name'
        ).not_.is_('comment_text_pt', 'null').neq('comment_text_pt', '').limit(100).execute()

        if sample.data:
            for comment in sample.data:
                original = comment.get('comment_text_original', '')
                translated = comment.get('comment_text_pt', '')

                # Validações básicas
                is_valid = True
                issues = []

                # Verificar se não está vazio
                if not translated or translated == 'null':
                    is_valid = False
                    issues.append("Tradução vazia")

                # Verificar se não é igual ao original (exceto PT)
                elif translated == original and not self._is_portuguese(original):
                    is_valid = False
                    issues.append("Tradução igual ao original")

                # Verificar placeholders suspeitos
                elif 'texto traduzido' in translated.lower():
                    is_valid = False
                    issues.append("Placeholder não substituído")

                if is_valid:
                    self.validation_results['translations']['valid'] += 1
                else:
                    self.validation_results['translations']['invalid'] += 1
                    if len(self.validation_results['translations']['samples']) < 5:
                        self.validation_results['translations']['samples'].append({
                            'original': original[:50] + '...' if len(original) > 50 else original,
                            'translated': translated[:50] + '...' if len(translated) > 50 else translated,
                            'issues': issues
                        })

            total_checked = (self.validation_results['translations']['valid'] +
                           self.validation_results['translations']['invalid'])

            print(f"  ✓ Traduções válidas: {self.validation_results['translations']['valid']}/{total_checked}")
            print(f"  ✓ Traduções inválidas: {self.validation_results['translations']['invalid']}")

            if self.validation_results['translations']['invalid'] > 0:
                print(f"  ⚠️ Exemplos de problemas:")
                for sample in self.validation_results['translations']['samples'][:3]:
                    print(f"    • Original: {sample['original']}")
                    print(f"      Tradução: {sample['translated']}")
                    print(f"      Problema: {', '.join(sample['issues'])}")

    async def _validate_responses(self):
        """Valida respostas geradas"""
        print(f"\n{Fore.YELLOW}[3/5] Validando Respostas...{Style.RESET_ALL}")

        # Buscar respostas geradas
        responses = self.db.supabase.table('video_comments').select(
            'comment_text_pt, suggested_response, author_name, like_count'
        ).not_.is_('suggested_response', 'null').limit(100).execute()

        if responses.data:
            for comment in responses.data:
                response = comment.get('suggested_response', '')

                is_valid = True
                issues = []

                # Validações
                if not response:
                    is_valid = False
                    issues.append("Resposta vazia")
                elif len(response) < 10:
                    is_valid = False
                    issues.append("Resposta muito curta")
                elif len(response) > 500:
                    issues.append("Resposta muito longa")

                # Verificar menção ao autor
                author = comment.get('author_name', '')
                if author and '@' + author.lower() not in response.lower():
                    issues.append("Não menciona o autor")

                if is_valid:
                    self.validation_results['responses']['valid'] += 1
                else:
                    self.validation_results['responses']['invalid'] += 1

                # Coletar amostra
                if len(self.validation_results['responses']['samples']) < 3:
                    self.validation_results['responses']['samples'].append({
                        'comment': comment.get('comment_text_pt', '')[:50] + '...',
                        'response': response[:100] + '...' if len(response) > 100 else response,
                        'likes': comment.get('like_count', 0)
                    })

            total_responses = (self.validation_results['responses']['valid'] +
                             self.validation_results['responses']['invalid'])

            print(f"  ✓ Respostas válidas: {self.validation_results['responses']['valid']}/{total_responses}")
            print(f"  ✓ Respostas inválidas: {self.validation_results['responses']['invalid']}")

            print(f"\n  📝 Exemplos de respostas:")
            for sample in self.validation_results['responses']['samples']:
                print(f"    • Comentário: {sample['comment']}")
                print(f"      Resposta: {sample['response']}")
                print(f"      Likes: {sample['likes']}")

    async def _validate_monetized_channels(self):
        """Valida processamento de canais monetizados"""
        print(f"\n{Fore.YELLOW}[4/5] Validando Canais Monetizados...{Style.RESET_ALL}")

        # Buscar canais monetizados
        monetizados = self.db.supabase.table('canais_monitorados').select(
            'id, nome_canal'
        ).eq('subnicho', 'Monetizados').execute()

        if monetizados.data:
            print(f"  ✓ Total de canais monetizados: {len(monetizados.data)}")

            for canal in monetizados.data:
                # Verificar comentários com resposta
                responses = self.db.supabase.table('video_comments').select(
                    'id', count='exact', head=True
                ).eq('canal_id', canal['id']).not_.is_('suggested_response', 'null').execute()

                if responses.count > 0:
                    print(f"    • {canal['nome_canal']}: {responses.count} respostas")
                else:
                    print(f"    ⚠️ {canal['nome_canal']}: SEM respostas")
                    self.validation_results['quality_issues'].append(
                        f"Canal monetizado '{canal['nome_canal']}' sem respostas geradas"
                    )

    async def _check_quality_issues(self):
        """Verifica problemas de qualidade"""
        print(f"\n{Fore.YELLOW}[5/5] Verificando Qualidade...{Style.RESET_ALL}")

        # 1. Comentários duplicados
        duplicates_check = """
        SELECT comment_text_original, COUNT(*) as count
        FROM video_comments
        WHERE comment_text_original IS NOT NULL
        GROUP BY comment_text_original
        HAVING COUNT(*) > 1
        LIMIT 5
        """

        # 2. Traduções suspeitas (muito curtas)
        short_translations = self.db.supabase.table('video_comments').select(
            'comment_text_original, comment_text_pt'
        ).not_.is_('comment_text_pt', 'null').execute()

        suspicious_count = 0
        if short_translations.data:
            for comment in short_translations.data:
                original = comment.get('comment_text_original', '')
                translated = comment.get('comment_text_pt', '')

                if len(original) > 50 and len(translated) < 10:
                    suspicious_count += 1

        if suspicious_count > 0:
            self.validation_results['quality_issues'].append(
                f"{suspicious_count} traduções suspeitamente curtas"
            )

        # 3. Respostas genéricas demais
        generic_responses = self.db.supabase.table('video_comments').select(
            'suggested_response'
        ).not_.is_('suggested_response', 'null').limit(50).execute()

        if generic_responses.data:
            responses_text = [r['suggested_response'] for r in generic_responses.data]
            # Verificar repetições
            unique_responses = set(responses_text)
            if len(unique_responses) < len(responses_text) * 0.8:
                self.validation_results['quality_issues'].append(
                    "Muitas respostas repetidas/genéricas"
                )

        if self.validation_results['quality_issues']:
            print(f"  ⚠️ Problemas encontrados:")
            for issue in self.validation_results['quality_issues']:
                print(f"    • {issue}")
        else:
            print(f"  ✓ Nenhum problema crítico de qualidade encontrado")

    def _is_portuguese(self, text: str) -> bool:
        """Verifica se texto parece ser português"""
        pt_words = ['que', 'não', 'você', 'está', 'isso', 'muito', 'obrigado', 'aqui', 'para']
        text_lower = text.lower()
        pt_count = sum(1 for word in pt_words if word in text_lower)
        return pt_count >= 2

    def _generate_report(self):
        """Gera relatório final"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("RELATÓRIO DE VALIDAÇÃO")
        print(f"{'='*60}{Style.RESET_ALL}\n")

        # Cobertura
        coverage = self.validation_results['coverage']
        if coverage['total'] > 0:
            coverage_percent = (coverage['processed'] / coverage['total'] * 100)
            print(f"{Fore.CYAN}COBERTURA:{Style.RESET_ALL}")
            print(f"  • Total: {coverage['total']} comentários")
            print(f"  • Processados: {coverage['processed']} ({coverage_percent:.1f}%)")
            print(f"  • Pendentes: {coverage['pending']}")

        # Traduções
        trans = self.validation_results['translations']
        if trans['valid'] + trans['invalid'] > 0:
            quality_percent = (trans['valid'] / (trans['valid'] + trans['invalid']) * 100)
            print(f"\n{Fore.CYAN}TRADUÇÕES:{Style.RESET_ALL}")
            print(f"  • Qualidade: {quality_percent:.1f}%")
            print(f"  • Válidas: {trans['valid']}")
            print(f"  • Inválidas: {trans['invalid']}")

        # Respostas
        resp = self.validation_results['responses']
        if resp['valid'] + resp['invalid'] > 0:
            resp_quality = (resp['valid'] / (resp['valid'] + resp['invalid']) * 100)
            print(f"\n{Fore.CYAN}RESPOSTAS:{Style.RESET_ALL}")
            print(f"  • Qualidade: {resp_quality:.1f}%")
            print(f"  • Válidas: {resp['valid']}")
            print(f"  • Inválidas: {resp['invalid']}")

        # Problemas
        if self.validation_results['quality_issues']:
            print(f"\n{Fore.YELLOW}⚠️ ATENÇÃO:{Style.RESET_ALL}")
            for issue in self.validation_results['quality_issues']:
                print(f"  • {issue}")

        # Conclusão
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        # Determinar status
        if coverage_percent >= 95 and quality_percent >= 90:
            print(f"{Fore.GREEN}✅ VALIDAÇÃO APROVADA - Sistema pronto para produção!{Style.RESET_ALL}")
        elif coverage_percent >= 80 and quality_percent >= 80:
            print(f"{Fore.YELLOW}⚠️ VALIDAÇÃO COM RESSALVAS - Revisar problemas antes do deploy{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ VALIDAÇÃO REPROVADA - Correções necessárias{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        # Salvar relatório
        self._save_report()

    def _save_report(self):
        """Salva relatório em arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}.json"

        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)

        print(f"📄 Relatório salvo em: {filename}")


async def main():
    """Executa validação"""
    validator = ResultValidator()
    await validator.validate_all()


if __name__ == "__main__":
    asyncio.run(main())