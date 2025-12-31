#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testa sistema de retry de vídeos com erro
"""

import sys
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Simula a lógica do scanner
def is_video_ready_for_retry(upload_status):
    """
    Simula _is_video_ready() do scanner

    Deve retornar True para:
    - upload_status vazio
    - upload_status = "❌ Erro"

    Deve retornar False para:
    - upload_status = "✅" (sucesso)
    - upload_status = "❌ Erro Final" (3 tentativas esgotadas)
    """

    if not upload_status or not upload_status.strip():
        return True  # Vazio = primeira tentativa

    upload_clean = upload_status.strip()

    if upload_clean in ["❌ Erro", "❌ erro", "erro", "Erro"]:
        return True  # Permite retry
    else:
        return False  # Ignora (sucesso ou erro final)

# Simula lógica do upload worker
def get_status_after_failure(retry_count):
    """
    Simula lógica de marcação na planilha após falha

    retry_count = 0 → primeira falha → marca "❌ Erro" (permite 2 retries)
    retry_count = 1 → segunda falha → marca "❌ Erro" (permite 1 retry)
    retry_count = 2 → terceira falha → marca "❌ Erro Final" (PARA)
    """

    if retry_count >= 2:
        return "❌ Erro Final"
    else:
        return "❌ Erro"

# Testes
print("=" * 80)
print("TESTE DO SISTEMA DE RETRY")
print("=" * 80)
print()

print("TESTE 1: Scanner detecta videos corretos para retry")
print("-" * 80)

test_cases = [
    ("", True, "Vazio (primeira tentativa)"),
    ("❌ Erro", True, "Erro (permite retry)"),
    ("❌ erro", True, "Erro lowercase"),
    ("✅", False, "Sucesso (ignora)"),
    ("✅ done", False, "Done (ignora)"),
    ("❌ Erro Final", False, "Erro Final (ignora - 3 tentativas)"),
    ("processing", False, "Em processamento (ignora)"),
]

all_pass = True
for upload_status, expected, description in test_cases:
    result = is_video_ready_for_retry(upload_status)
    status = "✅" if result == expected else "❌"

    if result != expected:
        all_pass = False

    print(f"{status} '{upload_status}' → {result} (esperado: {expected}) - {description}")

print()
if all_pass:
    print("✅ TODOS OS TESTES PASSARAM!")
else:
    print("❌ ALGUNS TESTES FALHARAM!")

print()
print()

print("TESTE 2: Marcacao correta apos falhas")
print("-" * 80)

retry_scenarios = [
    (0, "❌ Erro", "Primeira falha → permite 2 retries"),
    (1, "❌ Erro", "Segunda falha → permite 1 retry"),
    (2, "❌ Erro Final", "Terceira falha → PARA (não tenta mais)"),
]

all_pass2 = True
for retry_count, expected_status, description in retry_scenarios:
    result_status = get_status_after_failure(retry_count)
    status = "✅" if result_status == expected_status else "❌"

    if result_status != expected_status:
        all_pass2 = False

    print(f"{status} retry_count={retry_count} → '{result_status}' (esperado: '{expected_status}') - {description}")

print()
if all_pass2:
    print("✅ TODOS OS TESTES PASSARAM!")
else:
    print("❌ ALGUNS TESTES FALHARAM!")

print()
print()

print("TESTE 3: Fluxo completo (video falhando 3 vezes)")
print("-" * 80)

print("\nVideo: 'Teste Video 123' (sempre falha no upload)")
print()

retry_count = 0
upload_status = ""

for tentativa in range(1, 5):  # 4 tentativas para testar limite
    print(f"Scan #{tentativa}:")
    print(f"  Estado atual: retry_count={retry_count}, upload_status='{upload_status}'")

    # Scanner verifica se deve processar
    should_process = is_video_ready_for_retry(upload_status)
    print(f"  Scanner detecta? {should_process}")

    if not should_process:
        print(f"  ⏭️  Skipado (scanner ignora)")
        break

    # Verifica limite de 3 tentativas
    if retry_count >= 3:
        print(f"  ⏭️  Skipado (limite de 3 tentativas atingido)")
        break

    print(f"  ✅ Adicionado à fila")
    print(f"  ⬆️  Tentando upload...")
    print(f"  ❌ Upload falhou!")

    # Atualiza estado após falha
    upload_status = get_status_after_failure(retry_count)
    retry_count += 1

    print(f"  📊 Planilha atualizada: '{upload_status}'")
    print(f"  💾 Banco atualizado: retry_count={retry_count}")
    print()

print()
print("=" * 80)
print("RESULTADO FINAL:")
print(f"  retry_count: {retry_count}")
print(f"  upload_status: '{upload_status}'")
print(f"  Total de tentativas: {retry_count}")
print()

if retry_count == 3 and upload_status == "❌ Erro Final":
    print("✅ FLUXO CORRETO!")
    print("   Vídeo tentou 3 vezes e foi marcado como 'Erro Final'")
    print("   Scanner não vai mais processar este vídeo")
else:
    print("❌ FLUXO INCORRETO!")
    print(f"   Esperado: retry_count=3, upload_status='❌ Erro Final'")

print("=" * 80)
