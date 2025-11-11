# 🎯 Guia Completo - WhatsApp Evolution API

## 📋 Visão Geral

Sistema completo de WhatsApp com:
- ✅ Múltiplos números por revenda
- ✅ Planos configuráveis (Básico, Plus, Pro, Premium, Enterprise)
- ✅ Controle anti-banimento (limites por número)
- ✅ Rotação automática entre números
- ✅ Mensagem de transferência customizável

---

## 🚀 INSTALAÇÃO

### **Passo 1: Instalar Docker (se não tiver)**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Reiniciar terminal após instalar
```

### **Passo 2: Iniciar Evolution API**

```bash
cd /app

# Iniciar containers
docker-compose -f docker-compose.evolution.yml up -d

# Verificar se está rodando
docker-compose -f docker-compose.evolution.yml ps

# Ver logs (se necessário)
docker-compose -f docker-compose.evolution.yml logs -f evolution-api
```

**Aguarde 30-60 segundos** para Evolution API inicializar completamente.

### **Passo 3: Verificar se Evolution API está OK**

```bash
curl http://localhost:8080
```

Deve retornar informações da API.

### **Passo 4: Reiniciar Backend**

```bash
sudo supervisorctl restart backend
```

---

## 📊 PLANOS WHATSAPP

| Plano | Números | Preço/mês |
|-------|---------|-----------|
| **Básico** | 1 | R$ 49 |
| **Plus** | 2 | R$ 89 |
| **Pro** | 3 | R$ 129 |
| **Premium** | 5 | R$ 199 |
| **Enterprise** | Ilimitado | R$ 499 |

---

## 🔧 CONFIGURAÇÃO POR REVENDA

### **Como Admin:**

1. Acesse: `/admin`
2. Vá em "Revendas"
3. Edite uma revenda
4. Configure o plano WhatsApp

### **Como Revenda:**

1. Acesse: `{revenda}.suporte.help/reseller-login`
2. Vá em aba "WhatsApp"
3. Configure:
   - Limites de mensagens por número
   - Mensagem de transferência
   - Conectar números via QR Code

---

## 📱 CONECTAR NÚMERO WHATSAPP

### **Passo 1: Criar Conexão**

Na aba WhatsApp, clique "Adicionar Número"

### **Passo 2: Escanear QR Code**

1. QR Code aparece na tela
2. Abra WhatsApp no celular
3. Vá em: **Configurações → Aparelhos conectados → Conectar aparelho**
4. Escaneie o QR Code
5. ✅ Conectado!

### **Passo 3: Configurar Limites**

```
Mensagens Recebidas/dia: 200 (recomendado)
Mensagens Enviadas/dia: 200 (recomendado)
```

### **Passo 4: Ativar Rotação**

Marque "Ativo para rotação" para incluir na rotação automática.

---

## 🔄 ROTAÇÃO AUTOMÁTICA

### **Como Funciona:**

```
Cliente manda WhatsApp → Número 1
        ↓
Número 1: 195/200 mensagens hoje
        ↓
Cliente manda 6ª mensagem
        ↓
Número 1 atingiu limite (200/200)
        ↓
Sistema envia mensagem:
"⏳ Sua mensagem está sendo transferida..."
        ↓
Próximas mensagens vão para Número 2
```

### **Estratégias de Rotação:**

**Round Robin (padrão):**
- Usa números em ordem (1 → 2 → 3 → 1...)
- Quando um atinge limite, passa para próximo

**Least Used:**
- Sempre usa o número com menos mensagens
- Distribui carga de forma equilibrada

---

## ⚙️ CONFIGURAÇÕES

### **Mensagem de Transferência (Customizável):**

Exemplo padrão:
```
⏳ Sua mensagem está sendo transferida para outro atendente. Aguarde um momento...
```

Personalize em: Aba WhatsApp → Configurações

### **Limites Recomendados:**

```
Mensagens Recebidas: 150-200/dia
Mensagens Enviadas: 150-200/dia
```

**⚠️ Importante:** Não exceda 250 mensagens/dia por número para evitar banimento.

---

## 📊 ESTATÍSTICAS

Veja em tempo real:
- Total de números conectados
- Mensagens recebidas hoje (por número)
- Mensagens enviadas hoje (por número)
- Status de cada número
- Progresso dos limites

---

## 🎯 FLUXO COMPLETO

### **1. Cliente manda WhatsApp:**
```
Cliente → +55 11 9999-9999
```

### **2. Evolution API recebe:**
```
Webhook → Backend FastAPI
```

### **3. Sistema verifica limite:**
```
Número 1: 180/200 ✅ OK, pode receber
```

### **4. Cria ticket automaticamente:**
```
Cliente → Ticket criado
Atendente vê na aba "Espera"
```

### **5. Atendente responde:**
```
Atendente digita → Sistema envia via WhatsApp
```

### **6. Se atingir limite:**
```
Número 1: 200/200 ❌ Limite atingido
Sistema rotaciona para Número 2
Envia: "⏳ Transferindo..."
```

---

## 🐛 TROUBLESHOOTING

### **Problema: QR Code não aparece**

```bash
# Ver logs do Evolution API
docker-compose -f docker-compose.evolution.yml logs -f evolution-api

# Reiniciar Evolution API
docker-compose -f docker-compose.evolution.yml restart evolution-api
```

### **Problema: Mensagem não chega no sistema**

1. Verificar webhook configurado
2. Ver logs do backend:
```bash
tail -100 /var/log/supervisor/backend.out.log | grep whatsapp
```

### **Problema: Número desconecta sozinho**

- Normal depois de 14 dias inativo
- Basta escanear QR Code novamente

### **Problema: Evolution API não inicia**

```bash
# Verificar se portas estão livres
sudo netstat -tulpn | grep 8080

# Se porta ocupada, mudar no docker-compose.evolution.yml
```

---

## 📡 ENDPOINTS API

### **Conexões:**
- `POST /api/whatsapp/connections` - Criar nova conexão
- `GET /api/whatsapp/connections` - Listar conexões
- `GET /api/whatsapp/connections/{id}/qrcode` - Buscar QR Code
- `PUT /api/whatsapp/connections/{id}` - Atualizar limites
- `DELETE /api/whatsapp/connections/{id}` - Deletar conexão

### **Configurações:**
- `GET /api/whatsapp/config` - Buscar config da revenda
- `PUT /api/whatsapp/config` - Atualizar config
- `PUT /api/whatsapp/config/plan/{reseller_id}` - Mudar plano (admin)

### **Mensagens:**
- `POST /api/whatsapp/send` - Enviar mensagem
- `POST /api/whatsapp/webhook` - Receber mensagens (webhook)

### **Estatísticas:**
- `GET /api/whatsapp/stats` - Ver estatísticas

---

## 🔒 SEGURANÇA

### **API Key:**
Configurada em `.env`:
```
EVOLUTION_API_KEY=cybertv-suporte-evolution-key-2024
```

**⚠️ MUDE EM PRODUÇÃO!**

### **Webhook:**
Apenas Evolution API pode chamar o webhook.
Verifique IP de origem se necessário.

---

## 💡 BOAS PRÁTICAS

### **Para Evitar Banimento:**

✅ **FAÇA:**
- Respeite os limites configurados
- Use números antigos (não novos)
- Não envie SPAM
- Intervalo mínimo entre mensagens: 3-5 segundos
- Máximo 200 mensagens/dia por número

❌ **NÃO FAÇA:**
- Não exceda 250 mensagens/dia
- Não envie mensagens em massa
- Não use números novos
- Não envie para números não salvos

### **Recomendações:**

1. **Comece com limites baixos** (100-150/dia)
2. **Monitore estatísticas** diariamente
3. **Tenha números backup** (em caso de ban)
4. **Use rotação sempre**
5. **Teste antes de usar em produção**

---

## 📞 SUPORTE

### **Logs Importantes:**

```bash
# Backend
tail -f /var/log/supervisor/backend.out.log

# Evolution API
docker-compose -f docker-compose.evolution.yml logs -f evolution-api

# PostgreSQL (Evolution)
docker-compose -f docker-compose.evolution.yml logs -f postgres-evolution
```

### **Reiniciar Serviços:**

```bash
# Reiniciar tudo
docker-compose -f docker-compose.evolution.yml restart
sudo supervisorctl restart backend

# Apenas Evolution API
docker-compose -f docker-compose.evolution.yml restart evolution-api

# Apenas Backend
sudo supervisorctl restart backend
```

---

## ✅ CHECKLIST PÓS-INSTALAÇÃO

- [ ] Evolution API rodando (`docker ps`)
- [ ] Backend reiniciado
- [ ] Planos configurados para revendas
- [ ] Pelo menos 1 número conectado
- [ ] QR Code funcionando
- [ ] Webhook recebendo mensagens
- [ ] Tickets sendo criados automaticamente
- [ ] Rotação funcionando
- [ ] Limites sendo respeitados

---

## 🎉 PRONTO!

Sistema WhatsApp completo funcionando com:
- ✅ Múltiplos números
- ✅ Planos flexíveis
- ✅ Anti-banimento
- ✅ Rotação automática
- ✅ 100% integrado ao sistema

**Qualquer dúvida, consulte este guia!** 📚
