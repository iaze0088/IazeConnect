# 🎬 Como Encontrar a API Key no XUI Panel

## 📍 Localização no Painel

Baseado na imagem que você enviou do XUI, siga estes passos:

### Passo 1: Acessar Configurações
```
Menu Superior → ⚙️ Settings (ou Configurações)
```

### Passo 2: Procurar API Settings
Você vai encontrar uma das seguintes opções:
- **API Settings**
- **API Configuration**  
- **API Access**
- **Configurações de API**

### Passo 3: Locais Comuns da API Key

A API key pode estar em diferentes lugares dependendo da versão do XUI:

#### 📂 Opção 1: Settings → API
```
Settings
  └── API Settings
      └── API Token: [copiar]
      └── API Key: [copiar]
```

#### 📂 Opção 2: Management → API
```
⚙️ Management
  └── API Configuration
      └── Generate API Key [botão]
      └── Your API Key: [copiar]
```

#### 📂 Opção 3: Users → Admin Settings
```
👥 Users
  └── Admin User (seu usuário)
      └── API Access
          └── API Token: [copiar]
```

---

## 🔍 Se NÃO Encontrar "API Settings"

Algumas versões do XUI não têm interface gráfica para API. Neste caso:

### Use Credenciais de Admin

1. **Username:** Seu usuário admin (geralmente `admin`)
2. **Password:** Sua senha de admin

**Configure no `.env`:**
```bash
XUI_API_URL=http://SEU_IP:8080
XUI_USERNAME=admin
XUI_PASSWORD=sua_senha_admin
```

---

## 🧪 Testar Manualmente a API

### Teste 1: Autenticar

```bash
curl -X POST "http://SEU_IP:8080/api/auth" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}'
```

**Resposta esperada:**
```json
{
  "token": "abc123def456...",
  "success": true
}
```

### Teste 2: Listar Usuários

```bash
# Se você obteve um token
curl -X GET "http://SEU_IP:8080/api/users" \
  -H "Authorization: Bearer SEU_TOKEN"

# Se você tem API Key
curl -X GET "http://SEU_IP:8080/api/users" \
  -H "Authorization: Bearer SUA_API_KEY"
```

---

## 📊 Estrutura da API XUI

Baseado no painel mostrado na imagem, os endpoints comuns são:

| Endpoint | Descrição |
|----------|-----------|
| `/api/auth` | Autenticar e obter token |
| `/api/users` | Listar todos os usuários |
| `/api/user/{username}` | Buscar usuário específico |
| `/api/lines` | Listar linhas/conexões |
| `/api/streams` | Listar streams disponíveis |

---

## 🎯 Configuração Final no IAZE

Após obter suas credenciais XUI, adicione no arquivo `/app/backend/.env`:

### Se você tem API Key:
```bash
XUI_API_URL=http://192.168.1.100:8080
XUI_API_KEY=sua_api_key_obtida_no_painel
```

### Se você vai usar Admin:
```bash
XUI_API_URL=http://192.168.1.100:8080
XUI_USERNAME=admin
XUI_PASSWORD=sua_senha_admin
```

---

## ⚠️ Troubleshooting

### Problema: "API não habilitada"

**Solução:**
1. Vá em **Settings** → **System**
2. Procure por "Enable API"
3. Marque a opção
4. Salve e reinicie o XUI

### Problema: "Acesso negado"

**Solução:**
1. Verifique se o usuário tem permissão de API
2. Tente com credenciais de superadmin
3. Verifique firewall do servidor

### Problema: "Endpoint não encontrado"

**Solução:**
- A versão do seu XUI pode ter endpoints diferentes
- Verifique a documentação da sua versão
- Ou use as credenciais de admin (sempre funciona)

---

## 📞 Próximo Passo

Após configurar, teste com:
```bash
cd /app
./test_xui_integration.sh
```

Este script vai testar automaticamente se a integração está funcionando! ✅
