#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher Universal - Dashboard Upload + Backend FastAPI
Compatível com Windows, macOS e Linux
Autor: Claude
Data: 10/02/2026
"""

import subprocess
import os
import sys
import io
import signal
import time
import platform
import webbrowser
from pathlib import Path
from threading import Thread
import socket

# Configura UTF-8 para Windows
if platform.system() == "Windows":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class DashboardLauncher:
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        self.is_running = True

        # Detecta sistema operacional
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_mac = self.system == "Darwin"
        self.is_linux = self.system == "Linux"

        # Configurações de sistema
        self.setup_environment()

    def setup_environment(self):
        """Configura ambiente baseado no SO"""
        # Garante UTF-8 em todos os sistemas
        if self.is_windows:
            # Windows UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            # Tenta configurar codepage UTF-8 no Windows
            try:
                subprocess.run("chcp 65001", shell=True, capture_output=True)
            except:
                pass
        else:
            # Unix-like (Mac/Linux)
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['LC_ALL'] = 'en_US.UTF-8'
            os.environ['LANG'] = 'en_US.UTF-8'

    def check_port(self, port):
        """Verifica se uma porta está disponível"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    def get_python_command(self):
        """Retorna comando Python apropriado para o SO"""
        if self.is_windows:
            return [sys.executable]
        else:
            # Mac/Linux - tenta python3 primeiro, depois python
            for cmd in ['python3', 'python']:
                try:
                    result = subprocess.run([cmd, '--version'],
                                         capture_output=True,
                                         text=True)
                    if result.returncode == 0:
                        return [cmd]
                except:
                    continue
            return [sys.executable]

    def clear_screen(self):
        """Limpa tela do terminal (cross-platform)"""
        if self.is_windows:
            os.system('cls')
        else:
            os.system('clear')

    def print_header(self):
        """Exibe cabeçalho bonito"""
        self.clear_screen()
        print("=" * 70)
        print("🚀 SISTEMA DE UPLOAD YOUTUBE - DASHBOARD COMPLETO")
        print("=" * 70)
        print(f"📍 Sistema Operacional: {self.system}")
        print(f"📍 Python: {sys.version.split()[0]}")
        print(f"📍 Diretório: {self.base_dir}")
        print("=" * 70)

    def start_backend(self):
        """Inicia FastAPI Backend (porta 8000)"""
        print("\n🔧 Iniciando Backend FastAPI...")

        # Verifica se porta está livre
        if not self.check_port(8000):
            print("⚠️  Porta 8000 já está em uso!")
            print("   Tentando encerrar processo anterior...")
            if self.is_windows:
                subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq FastAPI*\"",
                             shell=True, capture_output=True)
            else:
                subprocess.run("pkill -f 'python.*main.py'",
                             shell=True, capture_output=True)
            time.sleep(2)

        # Comando para iniciar
        python_cmd = self.get_python_command()
        cmd = python_cmd + ["main.py"]

        # Configurações específicas por SO
        if self.is_windows:
            # Windows: CREATE_NEW_PROCESS_GROUP para melhor controle
            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if self.is_windows else 0
            )
        else:
            # Mac/Linux: preexec_fn para novo grupo de processo
            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                preexec_fn=os.setsid if not self.is_windows else None
            )

        self.processes.append(("Backend FastAPI", process, 8000))

        # Monitor de logs em thread separada
        def monitor_logs():
            for line in iter(process.stdout.readline, ''):
                if line and self.is_running:
                    # Filtra logs desnecessários
                    if not any(skip in line for skip in ['GET /api/status', 'GET /favicon.ico']):
                        print(f"   [Backend] {line.strip()}")

        Thread(target=monitor_logs, daemon=True).start()

        # Aguarda backend inicializar
        print("   ⏳ Aguardando backend inicializar...")
        for i in range(10):
            if not self.check_port(8000):
                print("   ✅ Backend FastAPI rodando na porta 8000!")
                return True
            time.sleep(1)

        print("   ⚠️ Backend pode estar demorando para iniciar...")
        return False

    def start_dashboard(self):
        """Inicia Flask Dashboard (porta 5006)"""
        print("\n📊 Iniciando Dashboard Flask...")

        # Verifica se porta está livre
        if not self.check_port(5006):
            print("⚠️  Porta 5006 já está em uso!")
            print("   Tentando encerrar processo anterior...")
            if self.is_windows:
                subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq *dashboard*\"",
                             shell=True, capture_output=True)
            else:
                subprocess.run("pkill -f 'python.*dash_upload_final.py'",
                             shell=True, capture_output=True)
            time.sleep(2)

        # Comando para iniciar
        python_cmd = self.get_python_command()
        cmd = python_cmd + ["dash_upload_final.py"]

        # Configurações específicas por SO
        if self.is_windows:
            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if self.is_windows else 0
            )
        else:
            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid if not self.is_windows else None
            )

        self.processes.append(("Dashboard Flask", process, 5006))

        # Monitor de logs em thread separada
        def monitor_logs():
            for line in iter(process.stdout.readline, ''):
                if line and self.is_running:
                    # Filtra logs desnecessários
                    if not any(skip in line for skip in ['GET /static', 'GET /favicon.ico']):
                        print(f"   [Dashboard] {line.strip()}")

        Thread(target=monitor_logs, daemon=True).start()

        # Aguarda dashboard inicializar
        print("   ⏳ Aguardando dashboard inicializar...")
        for i in range(10):
            if not self.check_port(5006):
                print("   ✅ Dashboard Flask rodando na porta 5006!")
                return True
            time.sleep(1)

        print("   ⚠️ Dashboard pode estar demorando para iniciar...")
        return False

    def open_browser(self):
        """Abre o navegador automaticamente"""
        time.sleep(2)  # Aguarda um pouco
        url = "http://localhost:5006"
        print(f"\n🌐 Abrindo navegador em {url}...")
        try:
            webbrowser.open(url)
            print("   ✅ Navegador aberto!")
        except:
            print(f"   ⚠️ Não foi possível abrir o navegador automaticamente")
            print(f"   📍 Acesse manualmente: {url}")

    def shutdown(self, signum=None, frame=None):
        """Encerra todos os processos de forma limpa"""
        if not self.is_running:
            return

        self.is_running = False
        print("\n\n" + "=" * 70)
        print("⏹️  ENCERRANDO SISTEMA...")
        print("=" * 70)

        for name, process, port in self.processes:
            if process and process.poll() is None:
                print(f"   📍 Encerrando {name} (porta {port})...")
                try:
                    if self.is_windows:
                        # Windows: envia CTRL_BREAK_EVENT
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        # Mac/Linux: envia SIGTERM para o grupo
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

                    # Aguarda encerramento gracioso
                    process.wait(timeout=5)
                    print(f"   ✅ {name} encerrado com sucesso")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ {name} não respondeu, forçando encerramento...")
                    process.kill()
                except Exception as e:
                    print(f"   ⚠️ Erro ao encerrar {name}: {e}")
                    try:
                        process.kill()
                    except:
                        pass

        print("\n👋 Sistema encerrado com sucesso!")
        print("=" * 70)
        sys.exit(0)

    def monitor_processes(self):
        """Monitora se os processos estão rodando"""
        while self.is_running:
            time.sleep(2)
            for name, process, port in self.processes:
                if process and process.poll() is not None:
                    print(f"\n❌ {name} parou inesperadamente!")
                    print(f"   Código de saída: {process.returncode}")
                    self.shutdown()
                    break

    def run(self):
        """Executa o launcher"""
        try:
            # Exibe cabeçalho
            self.print_header()

            # Registra handlers de sinal (cross-platform)
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
            if self.is_windows:
                signal.signal(signal.SIGBREAK, self.shutdown)

            # Inicia serviços
            print("\n🎬 INICIANDO SERVIÇOS...")
            print("-" * 70)

            # 1. Backend FastAPI
            if not self.start_backend():
                print("\n❌ Falha ao iniciar Backend!")
                print("   Verifique se main.py está no diretório correto")
                self.shutdown()
                return

            time.sleep(2)

            # 2. Dashboard Flask
            if not self.start_dashboard():
                print("\n❌ Falha ao iniciar Dashboard!")
                print("   Verifique se dash_upload_final.py está no diretório correto")
                self.shutdown()
                return

            # 3. Abre navegador
            Thread(target=self.open_browser, daemon=True).start()

            # Exibe status final
            print("\n" + "=" * 70)
            print("✅ SISTEMA COMPLETO RODANDO!")
            print("=" * 70)
            print("\n📍 URLs DISPONÍVEIS:")
            print("   🔧 Backend API:  http://localhost:8000")
            print("   📊 Dashboard:    http://localhost:5006")
            print("\n📍 CONTROLES:")
            print("   🔄 Recarregar página: F5")
            print("   🛑 Encerrar sistema: Ctrl+C")
            print("\n📍 STATUS:")
            print("   ✅ Botão de upload forçado funcional")
            print("   ✅ Histórico de uploads disponível")
            print("   ✅ Sistema pronto para uso!")
            print("=" * 70)
            print("\n⏳ Monitorando processos... (Ctrl+C para encerrar)")

            # Monitora processos
            self.monitor_processes()

        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            print(f"\n❌ Erro crítico: {e}")
            self.shutdown()


if __name__ == "__main__":
    # Verifica Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ é necessário!")
        sys.exit(1)

    # Executa launcher
    launcher = DashboardLauncher()
    launcher.run()