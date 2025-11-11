# 🌐 COMO CONFIGURAR DNS PARA DOMÍNIOS DAS REVENDAS

## ❓ Por que preciso configurar DNS?

Atualmente, quando tenta acessar `ajuda.vip/revenda/login`, o domínio **não está apontando** para o servidor. Por isso o login falha com "Email ou senha inválidos".

Para o domínio próprio funcionar, você precisa **configurar o DNS** no provedor onde o domínio foi registrado.

---

## 📋 PASSO A PASSO: Configurar DNS do ajuda.vip

### **1. Descobrir onde o domínio está registrado**

O domínio `ajuda.vip` foi registrado em algum provedor:
- Registro.br
- GoDaddy
- Hostinger
- Locaweb
- UOL Host
- etc.

**Como descobrir?**
- Acesse: https://registro.br/tecnologia/ferramentas/whois/
- Digite: `ajuda.vip`
- Veja onde está registrado

---

### **2. Acessar o Painel DNS do Provedor**

Entre no painel do provedor onde o domínio foi registrado:
- Faça login
- Procure por: "Gerenciar DNS", "DNS Management", "Zona DNS"

---

### **3. Adicionar/Editar Registros DNS**

No painel DNS, adicione ou edite os seguintes registros:

#### **Registro A (principal):**
```
Tipo: A
Nome/Host: @ (ou deixe em branco)
Valor/IP: 34.57.15.54
TTL: 3600 (ou 1 hora)
```

#### **Registro A (www):**
```
Tipo: A
Nome/Host: www
Valor/IP: 34.57.15.54
TTL: 3600
```

**OU** (alternativa para www):

#### **Registro CNAME (www):**
```
Tipo: CNAME
Nome/Host: www
Valor: ajuda.vip
TTL: 3600
```

---

### **4. Salvar e Aguardar Propagação**

Após salvar os registros:
- **Tempo de propagação:** 15 minutos a 48 horas
- **Média:** 2-6 horas
- Não se preocupe se não funcionar imediatamente

---

### **5. Verificar se DNS Funcionou**

Depois de algumas horas, teste:

**Via Terminal/CMD:**
```bash
nslookup ajuda.vip
```

Ou no navegador:
```
https://www.whatsmydns.net/
```
Digite `ajuda.vip` e veja se está apontando para `34.57.15.54`

---

## 🔄 O QUE FAZER ENQUANTO DNS NÃO PROPAGA?

### **Use o Login Unificado!**

**Todas as revendas podem acessar por:**

🔗 https://wppconnect-fix.preview.emergentagent.com/revenda/login

**OU**

🔗 https://wppconnect-fix.preview.emergentagent.com/reseller-login

**Credenciais de exemplo:**
- Email: `michaelrv@gmail.com`
- Senha: `teste123`

✅ **Funciona IMEDIATAMENTE** sem configurar DNS!  
✅ Acesso total a todas as funcionalidades!  
✅ Pop-up DNS vai lembrar de configurar o domínio próprio

---

## 📊 RESUMO DOS DOMÍNIOS

### **Domínios que FUNCIONAM AGORA:**
- ✅ `reseller-sync.preview.emergentagent.com/revenda/login`
- ✅ `reseller-sync.preview.emergentagent.com/reseller-login`

### **Domínios que PRECISAM de DNS:**
- ⚠️ `ajuda.vip` → Precisa apontar para `34.57.15.54`
- ⚠️ `braia123.iaze.xyz` → Precisa apontar para `34.57.15.54`

---

## 🎯 IMPORTANTE: Avisar o Master

Depois de configurar o DNS:
1. Acesse o painel da revenda
2. Vá na aba "Domínio"
3. Configure o domínio próprio
4. **Avise o Master (admin principal)** que configurou
5. Master precisa ativar o domínio no painel dele

---

## ❓ DÚVIDAS FREQUENTES

### **1. Não tenho acesso ao DNS do domínio**
→ Peça ao dono do domínio para configurar  
→ Ou use o login unificado enquanto isso

### **2. DNS já está configurado mas não funciona**
→ Aguarde até 48h para propagação  
→ Use o login unificado enquanto isso  
→ Verifique se IP está correto: `34.57.15.54`

### **3. Posso usar sem domínio próprio?**
→ SIM! Use o login unificado  
→ Funciona perfeitamente  
→ Domínio próprio é opcional

### **4. Quando o domínio de teste para de funcionar?**
→ Somente após ativar o domínio oficial  
→ Até lá, pode usar ambos

---

## 📞 SUPORTE

Se precisar de ajuda para configurar DNS, entre em contato com:
- Provedor do domínio (suporte técnico)
- Administrador do sistema (Master)

---

**Última atualização:** 23/10/2024  
**IP do Servidor:** 34.57.15.54
