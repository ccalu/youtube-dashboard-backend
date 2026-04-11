"""
Setup Completo — Shorts Factory (Atualizado 2026-04-11)
Roda este script no novo PC apos instalar os pre-requisitos.
Ele faz tudo automaticamente: clona, instala, configura.

Uso: python setup_shorts.py
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

# === CONFIGURACAO ===
GITHUB_REPO_BACKEND = "https://github.com/ccalu/youtube-dashboard-backend.git"
GITHUB_REPO_SHORTS_EDITOR = "https://github.com/ccalu/shorts-editor.git"
GITHUB_REPO_DASHBOARD = "https://github.com/ccalu/shorts-factory-dashboard.git"

FREEPIK_WORKSPACE_URL = "https://br.freepik.com/pikaso/spaces/a166a80e-8448-4c38-b231-ce4cd2cc49ce"

# Pastas
HOME = Path.home()
DESKTOP = HOME / "Desktop"
CONTENT_FACTORY = DESKTOP / "ContentFactory"
BACKEND_DIR = CONTENT_FACTORY / "youtube-dashboard-backend"
SHORTS_EDITOR_DIR = CONTENT_FACTORY / "shorts-editor"
DASHBOARD_DIR = CONTENT_FACTORY / "shorts-factory-dashboard"
SHORTS_DIR = HOME / "Downloads" / "SHORTS"
MUSICAS_DIR = SHORTS_DIR / "MUSICAS-SHORTS"
CHROME_PROFILE = HOME / "chrome-debug-profile"

SUBNICHOS = [
    "Guerras e Civilizacoes",
    "Frentes de Guerra",
    "Relatos de Guerra",
    "Reis Perversos",
    "Historias Sombrias",
    "Culturas Macabras",
    "Monetizados",
]

MUSICAS_FOLDERS = ["Musicas 02", "Musicas 03", "Musicas 05", "Musicas 06"]


def run(cmd, cwd=None, check=True):
    """Roda comando no terminal."""
    print(f"  > {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=not check)
    if check and result.returncode != 0:
        print(f"  ERRO: {cmd}")
        return False
    return True


def check_prerequisites():
    """Verifica se os pre-requisitos estao instalados."""
    print("\n=== VERIFICANDO PRE-REQUISITOS ===")
    ok = True

    checks = [
        ("python --version", "Python"),
        ("node --version", "Node.js"),
        ("git --version", "Git"),
        ("ffmpeg -version", "ffmpeg"),
        ("claude --version", "Claude CLI"),
    ]

    for cmd, name in checks:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            print(f"  OK: {name} ({version})")
        else:
            print(f"  FALTANDO: {name}")
            ok = False

    # Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        print("  OK: Chrome")
    else:
        print("  FALTANDO: Chrome")
        ok = False

    return ok


def clone_repos():
    """Clona os repositorios do GitHub."""
    print("\n=== CLONANDO REPOSITORIOS ===")
    os.makedirs(CONTENT_FACTORY, exist_ok=True)

    repos = [
        (GITHUB_REPO_BACKEND, BACKEND_DIR, "youtube-dashboard-backend"),
        (GITHUB_REPO_SHORTS_EDITOR, SHORTS_EDITOR_DIR, "shorts-editor"),
        (GITHUB_REPO_DASHBOARD, DASHBOARD_DIR, "shorts-factory-dashboard"),
    ]

    for url, path, name in repos:
        if path.exists():
            print(f"  {name}: ja existe, atualizando (git pull)")
            run("git pull", cwd=str(path), check=False)
        else:
            print(f"  {name}: clonando...")
            run(f"git clone {url} {path}")


def install_python_deps():
    """Instala dependencias Python."""
    print("\n=== INSTALANDO DEPENDENCIAS PYTHON ===")
    run("pip install -r requirements.txt", cwd=str(BACKEND_DIR))
    run("pip install playwright openai-whisper")
    print("  Instalando Playwright browsers...")
    run("playwright install chromium")


def install_node_deps():
    """Instala dependencias Node."""
    print("\n=== INSTALANDO DEPENDENCIAS NODE ===")

    if SHORTS_EDITOR_DIR.exists():
        print("  shorts-editor:")
        run("npm install", cwd=str(SHORTS_EDITOR_DIR))

    if DASHBOARD_DIR.exists():
        print("  shorts-factory-dashboard:")
        run("npm install", cwd=str(DASHBOARD_DIR))


def create_directories():
    """Cria pastas necessarias."""
    print("\n=== CRIANDO PASTAS ===")

    dirs = [SHORTS_DIR, MUSICAS_DIR, CHROME_PROFILE]

    for sub in SUBNICHOS:
        dirs.append(SHORTS_DIR / sub)

    for mus in MUSICAS_FOLDERS:
        dirs.append(MUSICAS_DIR / mus)

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  {d}")


def configure_env():
    """Configura o arquivo .env."""
    print("\n=== CONFIGURANDO .env ===")

    env_path = BACKEND_DIR / ".env"

    if env_path.exists():
        print("  .env ja existe!")
        resp = input("  Deseja sobrescrever? (s/n): ").strip().lower()
        if resp != "s":
            print("  Mantendo .env existente")
            return

    print("\n  Preencha as credenciais abaixo.")
    print("  DICA: A forma mais facil e copiar o .env do PC principal.\n")

    resp = input("  Voce tem o .env do PC principal pra copiar? (s/n): ").strip().lower()

    if resp == "s":
        env_source = input("  Caminho do .env (ex: D:\\env_backup.txt): ").strip().strip('"')
        if os.path.exists(env_source):
            shutil.copy2(env_source, str(env_path))
            print(f"  .env copiado de {env_source}")

            # Atualizar SHORTS_LOCAL_PATH pro novo PC
            with open(str(env_path), "r") as f:
                content = f.read()
            if "SHORTS_LOCAL_PATH" in content:
                import re
                content = re.sub(
                    r"SHORTS_LOCAL_PATH=.*",
                    f"SHORTS_LOCAL_PATH={SHORTS_DIR}",
                    content,
                )
            else:
                content += f"\nSHORTS_LOCAL_PATH={SHORTS_DIR}\n"
            with open(str(env_path), "w") as f:
                f.write(content)
            print(f"  SHORTS_LOCAL_PATH atualizado pra {SHORTS_DIR}")
        else:
            print(f"  Arquivo nao encontrado: {env_source}")
            print("  Configure o .env manualmente depois")
    else:
        env_content = ""
        keys = [
            ("SUPABASE_URL", "URL do Supabase"),
            ("SUPABASE_KEY", "Chave anon do Supabase"),
            ("SUPABASE_SERVICE_ROLE_KEY", "Service role key do Supabase"),
            ("OPENAI_API_KEY", "Chave da OpenAI"),
            ("GOOGLE_SERVICE_ACCOUNT_JSON", "JSON da service account Google (1 linha)"),
            ("GOOGLE_SHEETS_CREDENTIALS_2", "JSON da SA do Sheets (1 linha)"),
        ]

        for key, desc in keys:
            val = input(f"  {desc} [{key}]: ").strip()
            if val:
                env_content += f"{key}={val}\n"

        env_content += f"\nSHORTS_LOCAL_PATH={SHORTS_DIR}\n"
        env_content += "PORT=8000\n"

        with open(str(env_path), "w") as f:
            f.write(env_content)
        print(f"  .env salvo em {env_path}")


def copy_service_account():
    """Copia arquivo de service account."""
    print("\n=== SERVICE ACCOUNT (Google Sheets) ===")

    sa_dest = HOME / "Downloads" / "service-account-492821-217e559c4710.json"
    if sa_dest.exists():
        print(f"  Ja existe: {sa_dest}")
        return

    print(f"  O arquivo service account JSON e necessario pra escrita nas planilhas.")
    sa_source = input("  Caminho do arquivo (ou Enter pra pular): ").strip().strip('"')
    if sa_source and os.path.exists(sa_source):
        shutil.copy2(sa_source, str(sa_dest))
        print(f"  Copiado pra {sa_dest}")
    else:
        print("  Pulando — copie manualmente depois para:")
        print(f"  {sa_dest}")


def update_analyst_path():
    """Atualiza o path do service account no analyst.py pro novo PC."""
    print("\n=== ATUALIZANDO PATHS ===")

    analyst_path = BACKEND_DIR / "_features" / "shorts_production" / "analyst.py"
    if analyst_path.exists():
        with open(str(analyst_path), "r", encoding="utf-8") as f:
            content = f.read()

        sa_path = str(HOME / "Downloads" / "service-account-492821-217e559c4710.json")
        old_pattern = 'SHORTS_SA_CREDS_PATH = r"C:\\Users\\PC\\Downloads\\service-account-492821-217e559c4710.json"'
        new_value = f'SHORTS_SA_CREDS_PATH = r"{sa_path}"'

        if old_pattern in content:
            content = content.replace(old_pattern, new_value)
            with open(str(analyst_path), "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  analyst.py: SA path atualizado")
        elif "SHORTS_SA_CREDS_PATH" in content and str(HOME) not in content:
            # Path diferente, atualizar
            import re
            content = re.sub(
                r'SHORTS_SA_CREDS_PATH\s*=\s*r?"[^"]*"',
                f'SHORTS_SA_CREDS_PATH = r"{sa_path}"',
                content,
            )
            with open(str(analyst_path), "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  analyst.py: SA path atualizado")
        else:
            print(f"  analyst.py: path ja correto")

    # Atualizar remotion_editor.py
    remotion_path = BACKEND_DIR / "_features" / "shorts_production" / "remotion_editor.py"
    if remotion_path.exists():
        with open(str(remotion_path), "r", encoding="utf-8") as f:
            content = f.read()

        import re
        new_remotion = str(SHORTS_EDITOR_DIR).replace("\\", "\\\\")
        content = re.sub(
            r'REMOTION_PROJECT\s*=\s*r?"[^"]*"',
            f'REMOTION_PROJECT = r"{SHORTS_EDITOR_DIR}"',
            content,
        )
        with open(str(remotion_path), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  remotion_editor.py: REMOTION_PROJECT atualizado")


def build_dashboard():
    """Faz build do dashboard frontend."""
    print("\n=== BUILD DO DASHBOARD ===")
    if DASHBOARD_DIR.exists():
        vite_env = DASHBOARD_DIR / ".env"
        if not vite_env.exists():
            with open(str(vite_env), "w") as f:
                f.write("VITE_API_URL=http://localhost:8000\n")
                backend_env = BACKEND_DIR / ".env"
                if backend_env.exists():
                    with open(str(backend_env)) as be:
                        for line in be:
                            if line.startswith("SUPABASE_URL="):
                                f.write(f"VITE_SUPABASE_URL={line.split('=', 1)[1]}")
                            elif line.startswith("SUPABASE_KEY="):
                                f.write(f"VITE_SUPABASE_ANON_KEY={line.split('=', 1)[1]}")
            print("  .env do dashboard criado")

        run("npm run build", cwd=str(DASHBOARD_DIR))
    else:
        print("  Dashboard nao encontrado")


def test_connections():
    """Testa conexoes."""
    print("\n=== TESTANDO CONEXOES ===")

    try:
        sys.path.insert(0, str(BACKEND_DIR))
        os.chdir(str(BACKEND_DIR))
        from dotenv import load_dotenv
        load_dotenv(str(BACKEND_DIR / ".env"))

        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if url and key:
            sb = create_client(url, key)
            result = sb.table("canais_monitorados").select("id").limit(1).execute()
            print(f"  Supabase: OK")
        else:
            print("  Supabase: credenciais nao configuradas")
    except Exception as e:
        print(f"  Supabase: ERRO - {e}")

    try:
        creds_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if creds_str:
            creds_dict = json.loads(creds_str)
            print(f"  Google Drive SA: {creds_dict.get('client_email', '?')}")
        else:
            print("  Google Drive: nao configurado")
    except Exception as e:
        print(f"  Google Drive: ERRO - {e}")

    sa_path = HOME / "Downloads" / "service-account-492821-217e559c4710.json"
    if sa_path.exists():
        with open(str(sa_path)) as f:
            sa = json.load(f)
        print(f"  Google Sheets SA: {sa.get('client_email', '?')}")
    else:
        print(f"  Google Sheets SA: arquivo nao encontrado")


def create_startup_bat():
    """Cria arquivo .bat de inicializacao."""
    print("\n=== CRIANDO INICIALIZADOR ===")

    bat_content = f"""@echo off
title Shorts Factory
color 0A

echo ========================================
echo   SHORTS FACTORY - Iniciando...
echo ========================================
echo.

echo [1/3] Iniciando Backend (porta 8000)...
start /min "Backend" cmd /c "cd /d {BACKEND_DIR} && python main.py"
timeout /t 3 >nul

echo [2/3] Iniciando Chrome + Freepik...
start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="{CHROME_PROFILE}" {FREEPIK_WORKSPACE_URL}
timeout /t 3 >nul

echo [3/3] Iniciando Dashboard (porta 5173)...
start /min "Dashboard" cmd /c "cd /d {DASHBOARD_DIR} && npm run dev"
timeout /t 2 >nul

echo.
echo ========================================
echo   TUDO INICIADO!
echo   Dashboard: http://localhost:5173
echo   Backend:   http://localhost:8000
echo   Chrome:    porta 9222 (Freepik)
echo ========================================
echo.
echo Pode fechar esta janela.
timeout /t 5
exit
"""

    bat_path = DESKTOP / "INICIAR_SHORTS_FACTORY.bat"
    with open(str(bat_path), "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"  Criado: {bat_path}")


def main():
    print("=" * 50)
    print("  SHORTS FACTORY — SETUP COMPLETO")
    print("  Versao: 2026-04-11")
    print("=" * 50)

    if not check_prerequisites():
        print("\n  ATENCAO: Alguns pre-requisitos faltando.")
        resp = input("  Continuar? (s/n): ").strip().lower()
        if resp != "s":
            return

    clone_repos()
    create_directories()
    install_python_deps()
    install_node_deps()
    configure_env()
    copy_service_account()
    update_analyst_path()
    build_dashboard()
    test_connections()
    create_startup_bat()

    print("\n" + "=" * 50)
    print("  SETUP COMPLETO!")
    print("=" * 50)
    print(f"""
  Proximos passos manuais:
  1. Copiar musicas pra {MUSICAS_DIR}
  2. Abrir Chrome e logar no Freepik
  3. Fazer login no Claude CLI: claude login
  4. Duplo clique em INICIAR_SHORTS_FACTORY.bat
  5. Abrir http://localhost:5173

  Para 2 PCs rodando juntos:
  - PC 1: Produzir Leva 1 (18 canais)
  - PC 2: Produzir Leva 2 (17 canais)
  - Ambos usam o mesmo Supabase/Sheets/Drive
""")


if __name__ == "__main__":
    main()
