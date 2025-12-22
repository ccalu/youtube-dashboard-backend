# Como Adicionar Novo Canal ao Dashboard

## Pre-requisitos

1. **Google Cloud Project** configurado com:
   - YouTube Data API v3 habilitada
   - YouTube Analytics API habilitada
   - OAuth 2.0 credentials (client_id e client_secret)

2. **AdsPower** com o proxy do canal aberto

---

## Passo a Passo

### 1. Gerar URL de autorizacao

```bash
python "C:\Users\User-OEM\Desktop\content-factory\monetization_dashboard\oauth_brand_account.py"
```

Vai gerar uma URL como:
```
https://accounts.google.com/o/oauth2/auth?client_id=624181268142-...
```

### 2. Abrir URL no AdsPower

1. Copie a URL gerada
2. Abra no navegador **dentro do AdsPower** (proxy correto)
3. Faca login se necessario
4. **IMPORTANTE:** Selecione a **Brand Account** (o canal), NAO o Gmail pessoal!
5. Autorize o aplicativo "daash"

### 3. Copiar URL de retorno

Apos autorizar, o navegador vai redirecionar para algo como:
```
http://localhost/?code=4/0ATX87lOUHN2qzx...&scope=...
```

**Copie essa URL completa.**

### 4. Adicionar canal ao sistema

Edite o arquivo `add_channel.py` e atualize a linha do CODE:

```python
CODE = "4/0ATX87lOUHN2qzx..."  # Cole o codigo aqui
```

Tambem atualize o proxy_name se necessario:
```python
"proxy_name": "C003.1",  # Nome do proxy no AdsPower
```

Execute:
```bash
python "C:\Users\User-OEM\Desktop\content-factory\monetization_dashboard\add_channel.py"
```

### 5. Verificar

```bash
python "C:\Users\User-OEM\Desktop\content-factory\monetization_dashboard\check_data.py"
```

---

## Estrutura dos Arquivos

| Arquivo | Funcao |
|---------|--------|
| `oauth_brand_account.py` | Gera URL de autorizacao |
| `add_channel.py` | Troca codigo por tokens e salva no Supabase |
| `coleta_diaria.py` | Coleta metricas de todos os canais |
| `check_data.py` | Verifica dados no Supabase |

---

## Troubleshooting

### Erro "invalid_grant"
- Codigo OAuth expirou (dura ~5 minutos)
- Gere nova URL e refaca o processo

### Erro 403 Forbidden
- Voce selecionou o Gmail ao inves da Brand Account
- Refaca o OAuth selecionando o canal correto

### Canal nao aparece na lista
- O canal pode estar em outra conta Google
- Verifique se esta no proxy correto

---

## Google Cloud Setup (para novos projetos)

Se precisar configurar um novo projeto Google Cloud:

1. Acesse https://console.cloud.google.com
2. Crie novo projeto ou selecione existente
3. Va em "APIs & Services" > "Enable APIs"
4. Habilite:
   - YouTube Data API v3
   - YouTube Analytics API
5. Va em "Credentials" > "Create Credentials" > "OAuth client ID"
6. Tipo: "Desktop app"
7. Baixe o JSON e copie client_id e client_secret para `config.py`

---

## Canais Configurados

| Canal | Proxy | Status |
|-------|-------|--------|
| Reis Perversos | C000.1 | OK |
| Cronicas da Guerra | C000.1 | OK |
| Relatos Obscuros | C000.1 | OK |
| Batallas Silenciadas | C003.1 | Pendente |

---

**Ultima atualizacao:** 08/12/2025
