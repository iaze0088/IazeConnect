# 🌐 Guia Completo: Sistema de Subdomínios para Revendas

## 📋 Visão Geral

O sistema agora gera automaticamente subdomínios para cada revenda no formato:
```
{nome_revenda}.suporte.help
```

Exemplo: Se criar revenda "lucasrv" → Gera `lucasrv.suporte.help`

---

## 🚀 Como Criar uma Nova Revenda

### Passo 1: Acessar Admin Dashboard
```
https://wppconnect-fix.preview.emergentagent.com/admin
Senha: 102030@ab
```

### Passo 2: Ir na aba "Revendas"

### Passo 3: Preencher o formulário

**Campos obrigatórios:**
- **Nome da Revenda**: Ex: `lucasrv` (use apenas letras e números, sem espaços)
- **Email**: Ex: `lucas@dominio.com`
- **Senha**: Ex: `senha123`

**Campo opcional:**
- **Domínio customizado**: Deixe vazio para usar o subdomínio automático

### Passo 4: Clicar em "Criar Revenda"

O sistema irá:
✅ Gerar automaticamente: `lucasrv.suporte.help`
✅ Mostrar modal com todas as informações
✅ Fornecer URLs de acesso

---

## 🌐 URLs Geradas Automaticamente

Para revenda "lucasrv":

### 📱 Para CLIENTES da revenda:
```
https://lucasrv.suporte.help/chat
```

### 👤 Para RESELLER (dono da revenda):
```
https://lucasrv.suporte.help/reseller-login
```

### 🎯 Para ATENDENTES da revenda:
```
https://lucasrv.suporte.help/atendente/login
```

---

## ⚙️ Configuração de DNS (IMPORTANTE!)

Para que o subdomínio funcione, você PRECISA configurar o DNS:

### Opção 1: DNS Tipo A (Recomendado)

**No painel de DNS do domínio `suporte.help`, adicione:**

```
Tipo: A
Nome: lucasrv
Valor: [IP_DO_SERVIDOR]
TTL: 3600 (ou automático)
```

### Opção 2: DNS Tipo CNAME (Alternativo)

```
Tipo: CNAME
Nome: lucasrv
Valor: tenant-shield-1.preview.emergentagent.com
TTL: 3600 (ou automático)
```

### ⏱️ Tempo de Propagação
- DNS geralmente propaga em 5-30 minutos
- Pode levar até 24-48 horas em alguns casos

---

## 🧪 Como Testar

### 1. Verificar se DNS está propagado:
```bash
nslookup lucasrv.suporte.help
```

Deve retornar o IP do servidor.

### 2. Acessar no navegador:
```
https://lucasrv.suporte.help/chat
```

### 3. Cliente faz login:
- **WhatsApp**: Ex: `5511999999999`
- **PIN**: Criar novo (2 dígitos), Ex: `88`

### 4. Cliente envia mensagem:
- Escreve qualquer mensagem
- Ticket é criado automaticamente

### 5. Atendente vê o ticket:
- Atendente acessa: `https://lucasrv.suporte.help/atendente/login`
- Faz login com credenciais da revenda
- Vê ticket na aba "Espera"

---

## 📝 Regras de Geração de Subdomínio

O sistema automaticamente:
- ✅ Remove espaços
- ✅ Remove caracteres especiais
- ✅ Converte para minúsculas
- ✅ Mantém apenas letras e números

**Exemplos:**

| Nome da Revenda | Subdomínio Gerado |
|----------------|-------------------|
| `LucasRV` | `lucasrv.suporte.help` |
| `Lucas RV` | `lucasrv.suporte.help` |
| `Lucas-RV-123` | `lucasrv123.suporte.help` |
| `São Paulo` | `saopaulo.suporte.help` |

---

## 🎯 Fluxo Completo de Atendimento

```
1. Cliente acessa: lucasrv.suporte.help/chat
   ↓
2. Cliente faz login (WhatsApp + PIN)
   ↓
3. Cliente envia mensagem
   ↓
4. Sistema cria ticket automaticamente
   ↓
5. Ticket vinculado à revenda "lucasrv"
   ↓
6. Atendente da revenda vê ticket
   ↓
7. Atendente clica e inicia atendimento
   ↓
8. Chat em tempo real via WebSocket
```

---

## 🔒 Isolamento Multi-Tenant

✅ **Cada revenda vê apenas seus próprios dados:**
- Tickets
- Atendentes
- Clientes
- Configurações
- Tutoriais
- Apps IPTV

✅ **Admin Master vê tudo de todas as revendas**

---

## ❓ Troubleshooting

### Problema: "Preview Unavailable - Agent is resting"
**Solução**: DNS ainda não propagado. Configure o DNS tipo A.

### Problema: Site não carrega
**Solução**: 
1. Verifique se DNS foi configurado
2. Aguarde propagação (até 24h)
3. Teste com: `nslookup {subdominio}.suporte.help`

### Problema: Cliente não consegue fazer login
**Solução**:
1. Verifique se está usando o domínio correto
2. Use formato: `55119XXXXXXXX` (com DDI)
3. PIN deve ter exatamente 2 dígitos

### Problema: Atendente não vê tickets
**Solução**:
1. Cliente precisa ENVIAR uma mensagem para criar ticket
2. Verifique se atendente pertence à revenda correta
3. Verifique isolamento multi-tenant

---

## 📞 Suporte

Para problemas técnicos ou dúvidas, consulte:
- Logs do backend: `/var/log/supervisor/backend.err.log`
- Logs do frontend: Console do navegador (F12)
- Documentação completa: `/app/README_SISTEMA_COMPLETO.md`

---

## 🎉 Pronto!

Agora você tem um sistema completo de subdomínios automáticos para revendas!

**Resumo:**
1. ✅ Cria revenda com nome simples (ex: lucasrv)
2. ✅ Sistema gera: `lucasrv.suporte.help`
3. ✅ Configura DNS tipo A
4. ✅ Compartilha link com clientes: `https://lucasrv.suporte.help/chat`
5. ✅ Atendentes acessam: `https://lucasrv.suporte.help/atendente/login`

**É só isso! 🚀**
