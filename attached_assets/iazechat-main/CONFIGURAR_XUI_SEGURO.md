# 🔒 Configuração Segura - XUI API READ-ONLY

## 📸 Baseado na sua imagem do XUI

Você está na tela correta! Agora siga exatamente estes passos:

---

## ✅ PASSO A PASSO (Baseado na imagem)

### 1️⃣ Tela "Add Code" - Aba "Details"

#### Campo: **Access Code**
```
Digite: iaze_consultas
```
*(ou qualquer nome que você queira)*

#### Campo: **Access Type**
```
Selecione: Reseller API
```

**⚠️ NÃO selecione:**
- ❌ Admin (tem permissões completas)
- ❌ Admin API (pode criar/deletar)

**✅ SELECIONE:**
- ✅ **Reseller API** (permissões limitadas)

#### Toggle: **Enabled**
```
Ative o toggle (deve ficar verde/azul)
```

### 2️⃣ Clique em "Next"

---

### 3️⃣ Aba "Groups" (se aparecer)

Se o XUI mostrar essa aba:

**Grupos permitidos:**
- ✅ Marque APENAS os grupos que você quer que a API veja
- ✅ Se não souber, deixe TODOS marcados (API só vai CONSULTAR mesmo)

---

### 4️⃣ Aba "Restrictions" (IMPORTANTE!)

Aqui você define o que a API PODE fazer:

#### ✅ HABILITAR (READ-ONLY):
- ✅ `get_users` ou `users:list`
- ✅ `get_user_info` ou `users:read`
- ✅ `get_lines` ou `lines:read`
- ✅ `get_live` ou `live:read`

#### ❌ DESABILITAR (WRITE):
- ❌ `create_user` ou `users:create`
- ❌ `edit_user` ou `users:update`
- ❌ `delete_user` ou `users:delete`
- ❌ `renew_user` ou `users:renew`
- ❌ `add_credits` ou `credits:add`
- ❌ Qualquer coisa relacionada a "create", "update", "delete"

---

### 5️⃣ Salvar e Copiar

1. Clique em **"Save"** ou **"Create"**
2. O XUI vai gerar/mostrar o **Access Code**
3. **COPIE esse código!** Ex: `FjgJpVPv`

---

## 📝 Exemplo Visual da Configuração

```
┌─────────────────────────────────────────┐
│        Add Code - Details               │
├─────────────────────────────────────────┤
│                                          │
│  Access Code:  [iaze_consultas    ] 🔄  │
│                                          │
│  Access Type:  [Reseller API      ▼]    │
│                ├─ Admin                  │
│                ├─ Reseller               │
│                ├─ Ministra               │
│                ├─ Admin API              │
│                ├─ ✅ Reseller API        │ ← SELECIONE ESTE
│                └─ Web Player             │
│                                          │
│  Enabled:      [  🟢  ] ON               │
│                                          │
│                         [    Next    ]   │
└─────────────────────────────────────────┘
```

---

## 🔧 Depois de Criar no XUI

### Configurar no IAZE:

```bash
cd /app/backend
nano .env
```

Adicione no final:

```bash
# XUI API - READ ONLY
XUI_API_URL=http://SEU_IP:8080
XUI_API_KEY=FjgJpVPv
```

**Substitua:**
- `SEU_IP:8080` → IP/porta do seu XUI
- `FjgJpVPv` → O Access Code que você copiou

### Reiniciar:

```bash
sudo supervisorctl restart backend
```

### Testar Segurança:

```bash
cd /app
./test_xui_security.sh
```

Este script vai testar se a API está realmente READ-ONLY! ✅

---

## 🎯 Resultado Esperado

Depois de configurar, sua API vai:

| Operação | Status | Descrição |
|----------|--------|-----------|
| 📖 Listar usuários | ✅ PERMITIDO | HTTP 200 |
| 📖 Ver dados | ✅ PERMITIDO | HTTP 200 |
| 🚫 Criar usuário | ❌ BLOQUEADO | HTTP 403/401 |
| 🚫 Editar usuário | ❌ BLOQUEADO | HTTP 403/401 |
| 🚫 Deletar usuário | ❌ BLOQUEADO | HTTP 403/401 |
| 🚫 Renovar assinatura | ❌ BLOQUEADO | HTTP 403/401 |

---

## 🔒 Por que isso é seguro?

1. ✅ **Princípio do Menor Privilégio**
   - API só tem permissões mínimas necessárias

2. ✅ **Sem Risco de Alterações Acidentais**
   - Mesmo se houver bug no IAZE, não vai alterar dados

3. ✅ **Auditoria**
   - Todas operações são apenas consultas

4. ✅ **Isolamento**
   - Não afeta operações administrativas do XUI

---

## ❓ E se eu já criei com Admin API?

**Sem problema!** Você pode:

### Opção 1: Editar o código existente
1. No XUI, vá em **Access Codes**
2. Clique no código que criou
3. Mude para **Reseller API**
4. Salve

### Opção 2: Criar um novo código
1. Delete o antigo (se quiser)
2. Crie um novo seguindo os passos acima

---

## 📞 Precisa de Ajuda?

Após configurar, teste com:

```bash
# Teste completo
cd /app
./test_xui_integration.sh

# Teste de segurança
./test_xui_security.sh
```

Se os dois passarem, está PRONTO! 🎉
