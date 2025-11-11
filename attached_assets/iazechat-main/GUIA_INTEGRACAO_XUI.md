# 🎬 Guia Completo: Integração XUI API com IAZE

## 📋 O que é essa integração?

Permite que os atendentes do IAZE consultem dados de clientes IPTV (XUI Panel) diretamente pela aba OFFICE, incluindo:
- ✅ Usuário e Senha
- ✅ Data de Vencimento
- ✅ Status da Conta (Ativo/Inativo)
- ✅ Conexões Ativas/Máximas
- ✅ Pacote/Bouquet

---

## 🔧 Passo 1: Configurar API no XUI Panel

### 1.1 Acessar o Painel XUI

Acesse seu painel XUI (mostrado na sua imagem)

### 1.2 Obter Credenciais da API

Existem **2 métodos** para autenticação:

#### **Método 1: API Key (Recomendado)**
1. Vá em **Settings** → **API Settings**
2. Procure por "API Token" ou "API Key"
3. Copie a chave gerada
4. **Guarde essa chave!**

#### **Método 2: Usuário/Senha Admin**
1. Use as credenciais de admin do XUI
2. Username: `admin` (ou seu usuário admin)
3. Password: sua senha admin

### 1.3 Anotar a URL da API

```
http://seu-ip-xui.com
```

**Exemplo:**
- Se você acessa o painel em: `http://192.168.1.100:8080`
- A URL da API será: `http://192.168.1.100:8080`

---

## ⚙️ Passo 2: Configurar no IAZE (Backend)

### 2.1 Editar arquivo `.env` do backend

```bash
cd /app/backend
nano .env
```

### 2.2 Adicionar as variáveis XUI

Adicione estas linhas no final do arquivo:

```bash
# ==================== XUI IPTV INTEGRATION ====================
# URL do seu painel XUI (sem barra no final)
XUI_API_URL=http://192.168.1.100:8080

# Método 1: API Key (RECOMENDADO)
XUI_API_KEY=sua-api-key-aqui

# Método 2: Usuário e Senha (alternativa)
XUI_USERNAME=admin
XUI_PASSWORD=sua-senha-admin
```

**⚠️ IMPORTANTE:**
- Use **OU** API Key **OU** Username/Password (não precisa dos dois)
- Remova `http://` ou `https://` se já estiver na URL
- Não coloque barra `/` no final da URL

### 2.3 Exemplo Real de Configuração

```bash
# Exemplo 1: Usando API Key
XUI_API_URL=http://198.96.94.106:8080
XUI_API_KEY=abc123def456ghi789

# Exemplo 2: Usando Usuário/Senha
XUI_API_URL=http://meu-servidor-iptv.com
XUI_USERNAME=admin
XUI_PASSWORD=senhaSegura123
```

---

## 🚀 Passo 3: Reiniciar Serviços

### No Emergent:
```bash
sudo supervisorctl restart backend
```

### No Servidor Externo (Docker):
```bash
docker restart iaze_backend
```

---

## 🧪 Passo 4: Testar a Integração

### 4.1 Verificar Conexão

```bash
curl -X GET "http://localhost:8001/api/xui/check-connection" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta esperada:**
```json
{
  "success": true,
  "connected": true,
  "xui_url": "http://192.168.1.100:8080"
}
```

### 4.2 Buscar Usuário Específico

```bash
curl -X GET "http://localhost:8001/api/xui/search-user/teste123" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta esperada:**
```json
{
  "success": true,
  "user": {
    "username": "teste123",
    "password": "senha123",
    "expiration_date": "31/12/2025",
    "status": "Ativo",
    "is_active": true,
    "max_connections": 2,
    "active_connections": 1,
    "package": "Premium HD"
  }
}
```

### 4.3 Buscar por Palavra-Chave

```bash
curl -X POST "http://localhost:8001/api/xui/search-users" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"jose"}'
```

---

## 📱 Passo 5: Como Usar no IAZE

### 5.1 Na Aba OFFICE

1. Atendente abre o chat com cliente
2. Cliente pergunta: "Qual meu usuário e senha?"
3. Atendente vai na aba **OFFICE**
4. Pesquisa por:
   - Nome do cliente
   - Telefone
   - Parte do nome de usuário
5. Sistema busca no XUI automaticamente
6. Atendente vê os dados e envia ao cliente

### 5.2 Resposta Formatada

O sistema retorna automaticamente formatado:

```
📺 Dados IPTV - joao123

👤 Usuário: joao123
🔑 Senha: abc123
📅 Vencimento: 15/12/2025
🟢 Status: Ativo
📡 Conexões: 1/2
📦 Pacote: Premium HD
```

---

## 🔍 Passo 6: Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/xui/check-connection` | GET | Verifica conexão com XUI |
| `/api/xui/search-user/{username}` | GET | Busca usuário por nome exato |
| `/api/xui/search-users` | POST | Busca por palavra-chave |
| `/api/xui/user-details/{username}` | GET | Detalhes formatados |

---

## 🛠️ Troubleshooting

### ❌ Erro: "Sem token de autenticação XUI"

**Solução:** Verifique se adicionou `XUI_API_KEY` ou `XUI_USERNAME/PASSWORD` no `.env`

### ❌ Erro: "Connection refused"

**Solução:** 
1. Verifique se a URL do XUI está correta
2. Confirme que o XUI está rodando
3. Verifique firewall

### ❌ Erro: "Usuário não encontrado"

**Solução:**
1. Verifique se o usuário existe no XUI
2. Teste diretamente no painel XUI
3. Verifique se a API está habilitada no XUI

---

## 📊 Estrutura dos Arquivos Criados

```
/app/backend/
├── xui_service.py          # Serviço de integração com XUI
├── xui_routes.py           # Rotas da API XUI
└── server.py               # Atualizado com rotas XUI
```

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**
- Nunca compartilhe suas credenciais XUI
- Use HTTPS em produção
- Mantenha o `.env` seguro
- Não comite o `.env` no Git

---

## ✅ Checklist Final

- [ ] Obtive API Key ou credenciais do XUI
- [ ] Adicionei variáveis no `/app/backend/.env`
- [ ] Reiniciei o backend
- [ ] Testei a conexão com `/check-connection`
- [ ] Testei buscar um usuário
- [ ] Funcionou! 🎉

---

## 📞 Próximos Passos

Após configurar, você pode:
1. ✅ Atendentes consultam dados IPTV automaticamente
2. ✅ Integrar com AI para responder automaticamente
3. ✅ Criar relatórios de consultas
4. ✅ Adicionar mais campos personalizados

---

**Criado em:** 01/11/2025  
**Versão:** 1.0  
**Status:** ✅ Pronto para uso
