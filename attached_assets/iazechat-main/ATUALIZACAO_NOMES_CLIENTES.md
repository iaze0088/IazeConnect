# 📝 Sistema de Atualização Automática de Nomes de Clientes

## 🎯 Objetivo

Este sistema busca automaticamente os nomes dos clientes no **gestor.my** pelo telefone e salva no banco de dados.

---

## ✨ Funcionalidades

### 1. **Atualização Automática para Novos Clientes**
- Quando um cliente **sem nome** envia a primeira mensagem
- Sistema busca automaticamente o nome no gestor.my
- Salva o nome no banco de dados
- Tudo acontece em background (não atrasa a conversa)

### 2. **Atualização em Massa de Clientes Existentes**
- Endpoint para atualizar TODOS os clientes sem nome
- Busca no gestor.my pelo telefone
- Atualiza ambas coleções: `users` e `clients`
- Executa em background

### 3. **Atualização Individual**
- Endpoint para atualizar um cliente específico
- Útil para casos pontuais

---

## 🔧 Como Usar

### **1. Verificar Status Atual**

```bash
curl http://localhost:8001/api/client-names/status
```

**Resposta:**
```json
{
  "users": {
    "total": 50,
    "with_name": 8,
    "without_name": 42,
    "percentage_complete": 16.0
  },
  "clients": {
    "total": 30,
    "with_name": 30,
    "without_name": 0,
    "percentage_complete": 100.0
  },
  "total": {
    "all_clients": 80,
    "with_name": 38,
    "without_name": 42
  }
}
```

---

### **2. Atualizar Todos os Clientes Sem Nome**

```bash
curl -X POST http://localhost:8001/api/client-names/update-all
```

**Resposta:**
```json
{
  "success": true,
  "message": "Atualização iniciada em background para 42 clientes",
  "total_users": 42,
  "total_clients": 0,
  "total": 42
}
```

**⚠️ IMPORTANTE:**
- O processo roda em background
- Pode levar alguns minutos
- Verifique o status novamente após alguns minutos

---

### **3. Atualizar Cliente Individual**

```bash
curl -X POST "http://localhost:8001/api/client-names/update-single/CLIENT_ID?collection=users"
```

**Parâmetros:**
- `CLIENT_ID`: ID do cliente
- `collection`: "users" ou "clients" (default: "users")

---

### **4. Usando o Script de Teste**

```bash
cd /app
python3 test_update_client_names.py
```

O script:
1. Mostra status atual
2. Pergunta se quer atualizar
3. Inicia a atualização
4. Mostra progresso

---

## 🤖 Automação para Novos Clientes

### **Como Funciona:**

1. Cliente novo envia primeira mensagem
2. Sistema cria ticket
3. **Verifica se cliente tem nome:**
   - ✅ Se tem nome → nada acontece
   - ❌ Se não tem nome → busca no gestor.my

4. Busca em background:
   - Não atrasa a conversa
   - Login no gestor.my
   - Busca pelo telefone
   - Salva nome no banco

---

## 📊 Logs

**Para acompanhar o processo:**

```bash
tail -f /var/log/supervisor/backend.out.log | grep "Cliente sem nome\|Nome encontrado\|Nome atualizado"
```

**Exemplos de logs:**
```
📝 Cliente sem nome detectado, buscando no Office: 5511999998888
🔍 Buscando nome do cliente para telefone: 5511999998888
✅ Nome encontrado: João Silva
✅ Nome atualizado no banco: João Silva (collection: users)
```

---

## 🔍 Estrutura das Coleções

### **users (novos clientes):**
```json
{
  "id": "uuid",
  "whatsapp": "5511999998888",
  "display_name": "João Silva",  ← Campo atualizado
  "pin_hash": "...",
  "created_at": "..."
}
```

### **clients (clientes antigos):**
```json
{
  "id": "uuid",
  "phone": "5511999998888",
  "name": "João Silva",  ← Campo atualizado
  "email": "...",
  "created_at": "..."
}
```

---

## ⚠️ Requisitos

1. **Credenciais Office cadastradas:**
   - Pelo menos 1 credencial ativa no banco
   - Collection: `office_credentials`

2. **Playwright funcionando:**
   - Service `office_service_playwright` rodando

3. **gestor.my acessível:**
   - URL configurada nas credenciais
   - Sistema online

---

## 🐛 Troubleshooting

### **Problema: Nome não está sendo atualizado**

**Verificar:**
1. Credenciais Office ativas:
   ```bash
   mongosh
   use support_chat
   db.office_credentials.find({active: true}).count()
   ```

2. Logs de erro:
   ```bash
   tail -f /var/log/supervisor/backend.err.log | grep "Nome\|Office"
   ```

3. Cliente existe no gestor.my:
   - Login manual no gestor.my
   - Buscar pelo telefone

---

### **Problema: Atualização muito lenta**

**Motivo:**
- Playwright precisa fazer login para cada cliente
- Processo sequencial

**Solução:**
- Aguardar conclusão (pode levar 5-10 min para 50 clientes)
- Acompanhar logs

---

## 📈 Próximos Passos

1. **Executar atualização inicial:**
   ```bash
   python3 /app/test_update_client_names.py
   ```

2. **Aguardar conclusão** (5-10 minutos)

3. **Verificar status:**
   ```bash
   curl http://localhost:8001/api/client-names/status
   ```

4. **Novos clientes:** Automático a partir de agora!

---

## ✅ Conclusão

Sistema completo e funcionando:
- ✅ Atualização em massa de clientes existentes
- ✅ Automação para novos clientes
- ✅ Endpoints de gerenciamento
- ✅ Logs detalhados
- ✅ Script de teste

**Tudo pronto para uso!** 🎉
