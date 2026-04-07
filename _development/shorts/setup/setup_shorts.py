"""
Setup automatizado do Shorts Factory.
Roda em um PC novo para configurar tudo.

Uso: python setup_shorts.py
"""

import os
import sys
import subprocess
import shutil


def run(cmd, cwd=None, check=True):
    """Roda comando e mostra output."""
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    if check and result.returncode != 0:
        print(f"  ERRO: comando falhou (code {result.returncode})")
        return False
    return True


def check_prereqs():
    """Verifica pre-requisitos."""
    print("=" * 50)
    print("VERIFICANDO PRE-REQUISITOS")
    print("=" * 50)

    checks = {
        "Python": "python --version",
        "Node.js": "node --version",
        "npm": "npm --version",
        "Git": "git --version",
        "ffmpeg": "ffmpeg -version",
    }

    all_ok = True
    for name, cmd in checks.items():
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                print(f"  OK: {name} — {version}")
            else:
                print(f"  FALTANDO: {name} — instale antes de continuar")
                all_ok = False
        except Exception:
            print(f"  FALTANDO: {name} — instale antes de continuar")
            all_ok = False

    # Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        print(f"  OK: Chrome")
    else:
        print(f"  FALTANDO: Chrome — instale em {chrome_path}")
        all_ok = False

    return all_ok


def clone_repos(base_dir):
    """Clona repositorios se nao existirem."""
    print("\n" + "=" * 50)
    print("CLONANDO REPOSITORIOS")
    print("=" * 50)

    repos = {
        "youtube-dashboard-backend": "https://github.com/ccalu/youtube-dashboard-backend.git",
    }

    for name, url in repos.items():
        path = os.path.join(base_dir, name)
        if os.path.exists(path):
            print(f"  JA EXISTE: {name}")
            run(f"git pull", cwd=path, check=False)
        else:
            run(f"git clone {url}", cwd=base_dir)


def install_python_deps(backend_dir):
    """Instala dependencias Python."""
    print("\n" + "=" * 50)
    print("INSTALANDO DEPENDENCIAS PYTHON")
    print("=" * 50)

    run(f"pip install -r requirements.txt", cwd=backend_dir, check=False)

    # Pacotes extras necessarios pro Shorts
    extras = [
        "playwright",
        "openai-whisper",
        "gdown",
    ]
    for pkg in extras:
        run(f"pip install {pkg}", check=False)


def install_node_deps(base_dir):
    """Instala dependencias Node."""
    print("\n" + "=" * 50)
    print("INSTALANDO DEPENDENCIAS NODE")
    print("=" * 50)

    # Shorts Editor (Remotion)
    editor_dir = os.path.join(base_dir, "shorts-editor")
    if os.path.exists(editor_dir):
        run("npm install", cwd=editor_dir, check=False)
    else:
        print(f"  AVISO: {editor_dir} nao encontrado. Clonar manualmente.")

    # Dashboard
    dash_dir = os.path.join(base_dir, "shorts-factory-dashboard")
    if os.path.exists(dash_dir):
        run("npm install", cwd=dash_dir, check=False)
        run("npm run build", cwd=dash_dir, check=False)
    else:
        print(f"  AVISO: {dash_dir} nao encontrado. Clonar manualmente.")


def setup_env(backend_dir):
    """Configura .env interativamente."""
    print("\n" + "=" * 50)
    print("CONFIGURANDO .env")
    print("=" * 50)

    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        print(f"  .env ja existe em {env_path}")
        resp = input("  Sobrescrever? (s/n): ").strip().lower()
        if resp != "s":
            print("  Mantendo .env existente.")
            return

    print("\n  Preencha as variaveis (deixe vazio pra pular):\n")

    vars = {}
    vars["SUPABASE_URL"] = input("  SUPABASE_URL: ").strip()
    vars["SUPABASE_KEY"] = input("  SUPABASE_KEY (anon): ").strip()
    vars["SUPABASE_SERVICE_ROLE_KEY"] = input("  SUPABASE_SERVICE_ROLE_KEY: ").strip()
    vars["OPENAI_API_KEY"] = input("  OPENAI_API_KEY: ").strip()
    vars["GOOGLE_SERVICE_ACCOUNT_JSON"] = input("  GOOGLE_SERVICE_ACCOUNT_JSON (JSON completo em 1 linha): ").strip()

    user = os.path.expanduser("~")
    vars["SHORTS_LOCAL_PATH"] = os.path.join(user, "Downloads", "SHORTS")

    with open(env_path, "w") as f:
        for k, v in vars.items():
            if v:
                f.write(f"{k}={v}\n")

    print(f"\n  .env salvo em {env_path}")


def create_folders():
    """Cria pastas necessarias."""
    print("\n" + "=" * 50)
    print("CRIANDO PASTAS")
    print("=" * 50)

    user = os.path.expanduser("~")
    shorts_path = os.path.join(user, "Downloads", "SHORTS")

    folders = [
        shorts_path,
        os.path.join(shorts_path, "MUSICAS-SHORTS"),
        os.path.join(shorts_path, "Reis Perversos"),
        os.path.join(shorts_path, "Historias Sombrias"),
        os.path.join(shorts_path, "Culturas Macabras"),
        os.path.join(shorts_path, "Relatos de Guerra"),
        os.path.join(shorts_path, "Frentes de Guerra"),
        os.path.join(shorts_path, "Guerras e Civilizacoes"),
        os.path.join(shorts_path, "Monetizados"),
    ]

    for f in folders:
        os.makedirs(f, exist_ok=True)
        print(f"  OK: {f}")

    # Chrome debug profile
    profile = os.path.join(user, "chrome-debug-profile")
    os.makedirs(profile, exist_ok=True)
    print(f"  OK: {profile}")


def create_startup_bat(base_dir):
    """Cria atalho INICIAR_SHORTS_FACTORY.bat no Desktop."""
    print("\n" + "=" * 50)
    print("CRIANDO ATALHO")
    print("=" * 50)

    user = os.path.expanduser("~")
    desktop = os.path.join(user, "Desktop")
    bat_path = os.path.join(desktop, "INICIAR_SHORTS_FACTORY.bat")

    backend_dir = os.path.join(base_dir, "youtube-dashboard-backend")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_path = os.path.join(user, "chrome-debug-profile")
    freepik_url = "https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce"

    bat_content = f"""@echo off
title Shorts Factory

echo Matando processos antigos...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

echo Iniciando backend...
start /min "" cmd /c "cd /d {backend_dir} && python run_shorts_server.py"
timeout /t 3 >nul

echo Iniciando Chrome + Freepik...
start "" "{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_path}" {freepik_url}
timeout /t 3 >nul

echo Abrindo dashboard...
start "" http://localhost:5173

echo Shorts Factory iniciado!
timeout /t 3
exit
"""

    with open(bat_path, "w") as f:
        f.write(bat_content)

    print(f"  OK: {bat_path}")


def test_connections(backend_dir):
    """Testa conexoes basicas."""
    print("\n" + "=" * 50)
    print("TESTANDO CONEXOES")
    print("=" * 50)

    # Testar Supabase
    print("  Testando Supabase...")
    result = subprocess.run(
        [sys.executable, "-c", """
from dotenv import load_dotenv
load_dotenv()
from database import SupabaseClient
db = SupabaseClient()
r = db.supabase.table('canais_monitorados').select('id').limit(1).execute()
print(f'OK: Supabase conectado ({len(r.data)} registros)')
"""],
        cwd=backend_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"    {result.stdout.strip()}")
    else:
        print(f"    ERRO: {result.stderr[:200]}")

    # Testar ffmpeg
    print("  Testando ffmpeg...")
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"    OK: ffmpeg funcionando")
    else:
        print(f"    ERRO: ffmpeg nao encontrado")

    # Testar Whisper
    print("  Testando Whisper...")
    result = subprocess.run(
        [sys.executable, "-c", "import whisper; print('OK: Whisper instalado')"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"    {result.stdout.strip()}")
    else:
        print(f"    ERRO: Whisper nao instalado")

    # Testar Playwright
    print("  Testando Playwright...")
    result = subprocess.run(
        [sys.executable, "-c", "from playwright.sync_api import sync_playwright; print('OK: Playwright instalado')"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"    {result.stdout.strip()}")
    else:
        print(f"    ERRO: Playwright nao instalado")


def main():
    print("=" * 50)
    print("  SHORTS FACTORY — SETUP COMPLETO")
    print("=" * 50)

    # 1. Verificar pre-requisitos
    if not check_prereqs():
        print("\n  INSTALE os itens faltando e rode novamente.")
        sys.exit(1)

    # 2. Definir diretorio base
    user = os.path.expanduser("~")
    default_base = os.path.join(user, "Desktop", "ContentFactory")
    base = input(f"\n  Diretorio base [{default_base}]: ").strip() or default_base
    os.makedirs(base, exist_ok=True)

    backend_dir = os.path.join(base, "youtube-dashboard-backend")

    # 3. Clonar repos
    clone_repos(base)

    # 4. Instalar dependencias Python
    install_python_deps(backend_dir)

    # 5. Instalar dependencias Node
    install_node_deps(base)

    # 6. Configurar .env
    setup_env(backend_dir)

    # 7. Criar pastas
    create_folders()

    # 8. Criar atalho
    create_startup_bat(base)

    # 9. Testar conexoes
    test_connections(backend_dir)

    print("\n" + "=" * 50)
    print("  SETUP CONCLUIDO!")
    print("=" * 50)
    print("""
  PASSOS MANUAIS RESTANTES:

  1. Abrir Chrome com debug port (duplo clique no atalho do Desktop)
  2. Fazer login no Freepik Spaces (unica vez)
  3. Copiar pasta MUSICAS-SHORTS para Downloads/SHORTS/
  4. Testar producao completa pelo dashboard

  Pronto! Shorts Factory configurado.
""")


if __name__ == "__main__":
    main()
