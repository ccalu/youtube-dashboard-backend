# -*- coding: utf-8 -*-
"""
Script para adicionar o canal coreano automaticamente
"""

import subprocess
import time

# Inputs para o wizard
inputs = """UCiMgKMWsYH8a8EFp94TClIQ
전쟁의 목소리
11
PLe-V17oPwzExLhmRHSL9MITHkeaLadY-x
1
16VWyE0zuAvJOeiGtXVPVGWTXGGBJmVu9YVQVJ1-4g0
10
"""

print("Executando wizard v2 para adicionar canal...")
print("=" * 80)

# Executa o wizard com os inputs
process = subprocess.Popen(
    ['python', 'add_canal_wizard_v2.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

# Envia os inputs
stdout, stderr = process.communicate(input=inputs)

# Mostra resultado
print(stdout)
if stderr:
    print("Erros:", stderr)

print("\n" + "=" * 80)
print("IMPORTANTE: Agora você precisa fazer o OAuth manualmente!")
print("O wizard deve ter aberto o navegador para autorização.")
print("Se não abriu, execute manualmente: python add_canal_wizard_v2.py")