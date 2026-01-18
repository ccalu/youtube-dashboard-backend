# 🍎 SETUP MACBOOK - Configuração Rápida

## 🎯 OBJETIVO
Configurar o MacBook com identificação "cellibs-mac" para commits identificados.

---

## ⚡ SETUP RÁPIDO (5 minutos)

### **PASSO 1: Abrir Terminal no MacBook**

```bash
# Ir para a pasta do projeto
cd ~/ContentFactory/youtube-dashboard-backend

# OU, se estiver em outro lugar:
cd [caminho-da-pasta]/youtube-dashboard-backend
```

---

### **PASSO 2: Configurar Git como "cellibs-mac"**

```bash
# Configurar identificação do MacBook
git config user.name "cellibs-mac"
git config user.email "lucca2703@gmail.com"

# Verificar que configurou
git config user.name
git config user.email
```

**Deve aparecer:**
```
cellibs-mac
lucca2703@gmail.com
```

✅ **Configuração concluída!**

---

### **PASSO 3: Rodar sync para atualizar tudo**

```bash
# Rodar sync (puxa últimas mudanças)
./sync.sh

# Ou, se der erro de permissão:
chmod +x sync.sh
./sync.sh
```

**O sync vai:**
- ✅ Puxar mudanças do GitHub (PC Casa + PC Escritório)
- ✅ Baixar novos arquivos
- ✅ Atualizar tudo automaticamente

---

### **PASSO 4: Teste de validação**

```bash
# Criar arquivo de teste
echo "MacBook (cellibs-mac) configurado e funcionando!" > teste_macbook.txt

# Adicionar ao Git
git add teste_macbook.txt

# Fazer commit (vai aparecer como "cellibs-mac")
git commit -m "Teste sync MacBook - cellibs-mac configurado"

# Enviar para GitHub
git push origin main

# Verificar último commit
git log -1 --pretty=format:"%h - %an - %s"
```

**Deve aparecer:**
```
[hash] - cellibs-mac - Teste sync MacBook - cellibs-mac configurado
```

✅ **MacBook configurado com sucesso!**

---

## 📊 ESTRUTURA DAS 3 MÁQUINAS

Depois da configuração:

```
✅ PC Escritório
   user.name: cellibs-escritorio
   Commits aparecem como: cellibs-escritorio

✅ PC Casa
   user.name: cellibs-casa
   Commits aparecem como: cellibs-casa

✅ MacBook (VOCÊ ESTÁ AQUI!)
   user.name: cellibs-mac
   Commits aparecem como: cellibs-mac
```

**Agora você sabe de QUAL máquina veio cada commit! 🔥**

---

## 🔄 USO DIÁRIO (MacBook)

### **SEMPRE que for trabalhar:**

```bash
# 1. Ir para a pasta
cd ~/ContentFactory/youtube-dashboard-backend

# 2. Rodar sync (puxa atualizações)
./sync.sh

# 3. Trabalhar normalmente...
# (criar/editar arquivos)

# 4. Ao terminar, rodar sync novamente
./sync.sh
```

**Pronto! Mudanças sincronizadas automaticamente!**

---

## 🐛 TROUBLESHOOTING

### **Erro: "Permission denied" ao rodar sync.sh**
```bash
# Solução: Dar permissão de execução
chmod +x sync.sh
./sync.sh
```

### **Erro: "not a git repository"**
```bash
# Solução: Clonar repositório do zero
cd ~/ContentFactory
git clone https://github.com/ccalu/youtube-dashboard-backend.git
cd youtube-dashboard-backend
# Depois voltar ao PASSO 2
```

### **Sync não funciona**
```bash
# Alternativa: Comandos Git manuais
git pull origin main  # Baixar mudanças
# (trabalhar...)
git add .             # Adicionar mudanças
git commit -m "sua mensagem"
git push origin main  # Enviar mudanças
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de considerar setup completo:

- [ ] Terminal aberto na pasta do projeto
- [ ] Git configurado como "cellibs-mac"
- [ ] sync.sh rodou sem erros
- [ ] Arquivo de teste criado
- [ ] Commit identificado como "cellibs-mac"
- [ ] Push enviado para GitHub com sucesso

**Se todos ✅, setup concluído!**

---

## 🎯 COMANDOS RESUMIDOS (Copiar e Colar)

```bash
# Setup completo em 4 comandos:
cd ~/ContentFactory/youtube-dashboard-backend
git config user.name "cellibs-mac"
git config user.email "lucca2703@gmail.com"
./sync.sh

# Teste (opcional):
echo "MacBook configurado!" > teste_macbook.txt
git add teste_macbook.txt
git commit -m "Teste MacBook"
git push origin main
```

---

## 🚀 RESULTADO FINAL

Depois do setup, você terá:

```
3 Máquinas sincronizadas:
✅ PC Escritório (cellibs-escritorio)
✅ PC Casa (cellibs-casa)
✅ MacBook (cellibs-mac)

Workflow:
1. Trabalha em qualquer máquina
2. Roda sync.sh (Mac) ou sync.bat (Windows)
3. Mudanças sincronizam automaticamente!
4. Histórico mostra de qual máquina veio cada commit

Sistema multi-máquina 100% operacional! 🔥
```

---

**Data:** 18/01/2026
**Versão:** 1.0
**Status:** Pronto para uso ✅

**Criado por:** cellibs-escritorio
**Para:** cellibs-mac (você no MacBook!)
