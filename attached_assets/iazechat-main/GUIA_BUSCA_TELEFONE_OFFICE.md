# 📱 Guia de Uso: Busca de Clientes por Telefone no OFFICE

## ✅ ÓTIMA NOTÍCIA!

A integração com **gestor.my** (Office) **JÁ ESTÁ PRONTA** e **JÁ funciona com telefone**!

---

## 🎯 Como Funciona

```
Cliente WhatsApp → (11) 99999-9999
       ↓
  IAZE captura o número
       ↓
  Busca no gestor.my pelo telefone
       ↓
  Retorna: Usuário, Senha, Vencimento, Status
```

---

## 🔧 Configuração (Se ainda não tiver)

### 1️⃣ Cadastrar Credenciais do Office

Primeiro, você precisa cadastrar as credenciais do **gestor.my**:

```bash
curl -X POST "http://localhost:8001/api/office/credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://gestor.my",
    "username": "seu_usuario_gestor",
    "password": "sua_senha_gestor",
    "nome": "Office Principal"
  }'
```

### 2️⃣ Verificar Credenciais Cadastradas

```bash
curl -X GET "http://localhost:8001/api/office/credentials"
```

---

## 🔍 Como Buscar Cliente

### Buscar por Telefone:

```bash
curl -X POST "http://localhost:8001/api/office/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "(11) 99999-9999"
  }'
```

### Formatos de Telefone Aceitos:

O sistema normaliza automaticamente:

| Formato de Entrada | Normalizado Para |
|--------------------|------------------|
| `(11) 99999-9999` | `11999999999` |
| `11 99999-9999` | `11999999999` |
| `11999999999` | `11999999999` |
| `+55 11 99999-9999` | `5511999999999` |

---

## 📊 Resposta Esperada

```json
{
  "success": true,
  "data": {
    "nome": "João Silva",
    "usuario": "joao123",
    "senha": "abc123",
    "telefone": "11999999999",
    "vencimento": "31/12/2025",
    "status": "Ativo",
    "conexoes": "1/2"
  },
  "credential_used": {
    "nome": "Office Principal",
    "username": "seu_usuario"
  }
}
```

---

## 🎨 Como os Atendentes Usam no IAZE

### No Chat:

1. Cliente pergunta: **"Qual meu usuário e senha?"**
2. Atendente vê o número do cliente: `(11) 99999-9999`
3. Atendente clica na aba **"OFFICE"**
4. Sistema busca automaticamente pelo número
5. Mostra os dados:

```
📺 Dados do Cliente

👤 Nome: João Silva
🆔 Usuário: joao123
🔑 Senha: abc123
📱 Telefone: (11) 99999-9999
📅 Vencimento: 31/12/2025
🟢 Status: Ativo
📡 Conexões: 1/2
```

6. Atendente copia e envia ao cliente

---

## 🧪 Testar Agora

### 1. Verificar se tem credenciais:

```bash
curl http://localhost:8001/api/office/credentials | python3 -m json.tool
```

**Se retornar vazio `[]`**, você precisa cadastrar primeiro!

### 2. Testar busca:

```bash
# Substitua pelo telefone de um cliente real no gestor.my
curl -X POST "http://localhost:8001/api/office/search" \
  -H "Content-Type: application/json" \
  -d '{"search_term":"11999999999"}'
```

---

## ⚙️ Configuração das Credenciais gestor.my

Se você ainda não cadastrou, faça assim:

### Via Frontend (AdminDashboard):

1. Acesse o painel Admin
2. Vá em **"Office Manager"** ou **"Configurações"**
3. Adicione suas credenciais do gestor.my

### Via Backend (Curl):

```bash
curl -X POST "http://localhost:8001/api/office/credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://gestor.my",
    "username": "SEU_USUARIO_AQUI",
    "password": "SUA_SENHA_AQUI",
    "nome": "Office Principal"
  }'
```

**⚠️ IMPORTANTE:** Use as mesmas credenciais que você usa para fazer login no painel gestor.my!

---

## 🔐 Segurança

As credenciais ficam salvas no MongoDB de forma **criptografada** e só são usadas para:
- ✅ Buscar dados de clientes
- ✅ Consultar status
- ❌ **NÃO são usadas para** renovar, criar ou deletar

---

## 📱 Busca Automática por Telefone WhatsApp

### Como funciona no chat:

Quando um cliente envia mensagem pelo WhatsApp:

1. IAZE pega o número automaticamente: `5511999999999`
2. Busca no gestor.my
3. Se encontrar, já mostra os dados na aba OFFICE
4. Atendente só precisa copiar e enviar

### Sem precisar digitar nada! 🎉

---

## 🎯 Resumo

✅ **Já está pronto!**
✅ **Busca por telefone funciona!**
✅ **Normaliza formatos automaticamente!**
✅ **Tenta em todas credenciais cadastradas!**
✅ **Salva histórico de buscas!**

**Único requisito:** Cadastrar credenciais do gestor.my (se ainda não tiver)

---

## 📞 Teste Rápido

Execute este comando para testar:

```bash
# 1. Verificar credenciais
curl http://localhost:8001/api/office/credentials

# 2. Se vazio, cadastre:
curl -X POST "http://localhost:8001/api/office/credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://gestor.my",
    "username": "seu_usuario",
    "password": "sua_senha",
    "nome": "Office Principal"
  }'

# 3. Teste busca:
curl -X POST "http://localhost:8001/api/office/search" \
  -H "Content-Type: application/json" \
  -d '{"search_term":"11999999999"}'
```

**Funcionou? Pronto para usar! 🚀**
