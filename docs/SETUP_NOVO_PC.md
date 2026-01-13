# 🆕 Setup em Novo PC (Casa, Trabalho, Qualquer Lugar)

**Para:** Configurar repositório completo em um PC novo pela primeira vez
**Tempo:** ~5 minutos

---

## 🎯 O Que Você Vai Ter

Após este setup:
- ✅ Repositório COMPLETO (código Python + docs + tudo)
- ✅ Sincronização automática com outros PCs
- ✅ Pode trabalhar em qualquer arquivo
- ✅ sync.bat/sync.sh sincroniza TUDO automaticamente

---

## 📋 Pré-requisitos

### **Windows:**
- Git instalado ([baixar aqui](https://git-scm.com/downloads))

### **Mac/Linux:**
- Git instalado (já vem instalado na maioria)

---

## 🚀 Setup (3 passos simples)

### **1. Abrir Terminal/PowerShell**

**Windows:**
- Pressione `Win + R`
- Digite `powershell`
- Enter

**Mac:**
- Pressione `Cmd + Espaço`
- Digite `terminal`
- Enter

### **2. Navegar para onde quer a pasta**

```bash
# Exemplo: Desktop
cd ~/Desktop

# Ou: Documentos
cd ~/Documents

# Ou: Onde preferir
cd /caminho/desejado
```

### **3. Clonar o repositório**

```bash
git clone https://github.com/ccalu/youtube-dashboard-backend.git
```

**O que acontece:**
- Baixa ~5-10 MB do GitHub
- Cria pasta `youtube-dashboard-backend/`
- Contém TUDO (código + docs + tudo)

### **4. Entrar na pasta**

```bash
cd youtube-dashboard-backend
```

### **5. Verificar que funcionou**

```bash
# Windows
dir

# Mac/Linux
ls -la
```

**Deve ver:**
- `docs/` - Documentação completa
- `main.py` - Backend FastAPI
- `collector.py` - Coletor YouTube
- `database.py` - Conexão Supabase
- `README.md` - Este guia
- `sync.bat` / `sync.sh` - Scripts de sincronização
- ... (e todos os outros arquivos)

---

## 🔄 Uso Diário

### **Sincronizar (SEMPRE antes e depois de trabalhar):**

**Windows:**
```bash
cd youtube-dashboard-backend/docs
sync.bat
```

**Mac/Linux:**
```bash
cd youtube-dashboard-backend/docs
./sync.sh
```

### **Workflow Completo:**

```bash
# 1. Ao começar o dia (puxar atualizações)
cd youtube-dashboard-backend/docs
sync.bat  # (Windows) ou ./sync.sh (Mac)

# 2. Trabalhar
# - Editar código Python
# - Criar/editar documentação
# - Fazer qualquer coisa

# 3. Ao terminar (enviar mudanças)
cd youtube-dashboard-backend/docs
sync.bat  # (Windows) ou ./sync.sh (Mac)

# 4. Ir para outro PC
# - Rodar sync lá
# - Recebe TUDO atualizado automaticamente!
```

---

## 📊 O Que o Sync Faz

### **BAIXAR (git pull):**
✅ Arquivos novos criados em outro PC
✅ Edições feitas em outro PC
✅ Arquivos deletados em outro PC
✅ Pastas novas criadas em outro PC
✅ **TUDO**

### **ENVIAR (git add + commit + push):**
✅ Arquivos novos que você criou
✅ Edições que você fez
✅ Arquivos que você deletou
✅ Pastas novas que você criou
✅ **TUDO**

### **Resultado:**
Sincronização PERFEITA entre TODOS os PCs!

---

## 🗂️ Estrutura do Projeto

```
youtube-dashboard-backend/
├── docs/                   ← Documentação completa
│   ├── README.md           ← Guia da documentação
│   ├── FRONTEND_COMPLETO.md ← Frontend: 6 abas
│   ├── documentacao-completa/ ← 16 docs técnicos
│   ├── mini-steps/         ← 11 mini-steps
│   ├── sync.bat            ← Sincronização Windows
│   ├── sync.sh             ← Sincronização Mac/Linux
│   ├── CONVERT_TO_FULL_CLONE.md ← Guia para Mac
│   └── SETUP_NOVO_PC.md    ← Este arquivo
│
├── scripts-temp/           ← Scripts de teste (NÃO vão pro Git)
├── backups/                ← Backups (NÃO vão pro Git)
├── debug/                  ← Arquivos debug (NÃO vão pro Git)
│
├── main.py                 ← Backend FastAPI (1122 linhas)
├── collector.py            ← Coletor YouTube (792 linhas)
├── database.py             ← Conexão Supabase
├── notifier.py             ← Sistema notificações (449 linhas)
├── monetization_collector.py ← Coleta receita OAuth
├── financeiro.py           ← Sistema financeiro
├── requirements.txt        ← Dependências Python
├── .env                    ← Variáveis ambiente (local, NÃO vai pro Git)
├── .gitignore              ← Arquivos ignorados
└── README.md               ← README principal
```

---

## 🔧 Configuração Extra (Opcional)

### **Instalar Dependências Python (se for rodar código localmente):**

```bash
# Navegar para a raiz
cd youtube-dashboard-backend

# Instalar dependências
pip install -r requirements.txt --break-system-packages
```

### **Configurar .env (se for rodar backend localmente):**

```bash
# Copiar exemplo
cp .env.example .env

# Editar .env com suas credenciais
# (Supabase, YouTube API keys, etc)
```

---

## ❓ Problemas Comuns

### **"git: command not found"**
Instale o Git:
- **Windows:** https://git-scm.com/downloads
- **Mac:** `brew install git`
- **Linux:** `sudo apt install git`

### **"Permission denied (publickey)"**
Você precisa configurar SSH no GitHub:
1. Vá em: https://github.com/settings/keys
2. Adicione sua chave SSH
3. Ou use HTTPS em vez de SSH (já configurado)

### **"sync.bat não funciona no Mac"**
Use `sync.sh`:
```bash
chmod +x sync.sh
./sync.sh
```

### **"sync.sh não funciona no Windows"**
Use `sync.bat`:
```bash
sync.bat
```

---

## 🎉 Pronto!

Você agora tem:
- ✅ Repositório completo configurado
- ✅ Sincronização automática funcionando
- ✅ Pode trabalhar em qualquer arquivo
- ✅ Preparado para trabalhar de qualquer lugar

**Próximos passos:**
1. Leia [README.md](../README.md) para overview do projeto
2. Leia [docs/README.md](./README.md) para índice da documentação
3. Comece a trabalhar!

**Voltar:** [README.md](./README.md)
