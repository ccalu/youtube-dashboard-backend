# ⚡ COMANDOS RÁPIDOS - Sistema Multi-Máquina

## 🎯 REFERÊNCIA RÁPIDA

### **📍 Identificação das Máquinas:**

```
PC Escritório:  cellibs-escritorio
PC Casa:        cellibs-casa
MacBook:        cellibs-mac
```

---

## 🔧 COMANDOS ESSENCIAIS

### **Sync (TODO DIA):**

```bash
# Windows (PC Escritório / PC Casa):
cd D:\ContentFactory\youtube-dashboard-backend
.\sync.bat

# Mac:
cd ~/ContentFactory/youtube-dashboard-backend
./sync.sh
```

---

### **Configurar Git pela primeira vez:**

```bash
# PC Escritório:
git config user.name "cellibs-escritorio"
git config user.email "lucca2703@gmail.com"

# PC Casa:
git config user.name "cellibs-casa"
git config user.email "lucca2703@gmail.com"

# MacBook:
git config user.name "cellibs-mac"
git config user.email "lucca2703@gmail.com"
```

---

### **Verificar configuração:**

```bash
git config user.name
git config user.email
```

---

### **Ver histórico de commits:**

```bash
# Últimos 5 commits
git log -5 --pretty=format:"%h - %an - %s - %ar"

# Últimos 10 commits
git log -10 --oneline
```

---

### **Workflow manual (sem sync.bat):**

```bash
# 1. Puxar atualizações
git pull origin main

# 2. Trabalhar nos arquivos...

# 3. Ver o que mudou
git status

# 4. Adicionar mudanças
git add .

# 5. Fazer commit
git commit -m "Sua mensagem aqui"

# 6. Enviar para GitHub
git push origin main
```

---

## 🧪 TESTES RÁPIDOS

### **Criar arquivo de teste:**

```bash
# Windows:
echo "Teste %COMPUTERNAME%" > teste.txt

# Mac/Linux:
echo "Teste $(hostname)" > teste.txt
```

### **Commit rápido:**

```bash
git add teste.txt
git commit -m "Teste de sincronia"
git push origin main
```

---

## 📊 COMANDOS ÚTEIS

### **Ver status do Git:**

```bash
git status
```

### **Ver diferenças (antes de commit):**

```bash
git diff
```

### **Ver último commit:**

```bash
git log -1
```

### **Ver branches:**

```bash
git branch -a
```

### **Desfazer último commit (NÃO pushed):**

```bash
git reset --soft HEAD~1
```

### **Limpar arquivos não rastreados:**

```bash
git clean -fd
```

---

## 🚨 EMERGÊNCIA

### **Resetar para última versão do GitHub:**

```bash
# CUIDADO! Vai apagar mudanças locais não commitadas!
git fetch origin
git reset --hard origin/main
```

### **Ver configuração global do Git:**

```bash
git config --global --list
```

### **Mudar identificação (temporário, só neste repo):**

```bash
git config user.name "novo-nome"
git config user.email "novo@email.com"
```

---

## 📁 ESTRUTURA DO PROJETO

```
youtube-dashboard-backend/
├── 1_CONTEXTO_NEGOCIO/         (Docs de negócio)
├── 2_DASHBOARD_TECNICO/        (Docs técnicos)
├── 3_OPERACIONAL/              (Guias operacionais)
├── archive/                    (Backups)
├── database/                   (Migrations + schemas)
├── DNA/                        (HTMLs de análise)
├── referencia/                 (Docs de referência)
├── trend-monitor/              (Projeto trend monitor)
├── utils/                      (Utilitários)
├── scripts/                    (Scripts auxiliares)
├── collector.py                (Código Python)
├── main.py
├── database.py
├── sync.bat / sync.sh          (Sincronização)
├── SETUP_MACBOOK.md           (Guia setup MacBook)
└── COMANDOS_RAPIDOS.md        (Este arquivo!)
```

---

## 🔗 LINKS ÚTEIS

- **GitHub Repo:** https://github.com/ccalu/youtube-dashboard-backend
- **Documentação Completa:** Ver `referencia/documentacao-completa/`
- **Setup MacBook:** Ver `SETUP_MACBOOK.md`

---

## 💡 DICAS

1. **SEMPRE rode sync ANTES de trabalhar** (puxa últimas mudanças)
2. **SEMPRE rode sync DEPOIS de trabalhar** (envia suas mudanças)
3. **Use mensagens de commit descritivas**
4. **Commits são identificados por máquina automaticamente**
5. **Se der conflito, delete pasta e clone do zero**

---

## 📞 TROUBLESHOOTING RÁPIDO

### **Problema:** sync.bat não funciona
```bash
# Solução: Rodar comandos manualmente
git pull origin main
git add .
git commit -m "Suas mudanças"
git push origin main
```

### **Problema:** "Permission denied"
```bash
# Solução: Dar permissão (Mac/Linux)
chmod +x sync.sh
```

### **Problema:** "Merge conflict"
```bash
# Solução rápida: Resetar
git fetch origin
git reset --hard origin/main
```

---

**Mantenha este arquivo como referência rápida!** 📌

**Criado por:** cellibs-escritorio
**Data:** 18/01/2026
**Versão:** 1.0
