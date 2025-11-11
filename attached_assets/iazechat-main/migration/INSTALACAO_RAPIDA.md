# 🚀 INSTALAÇÃO RÁPIDA - 3 COMANDOS

## 📋 INFORMAÇÕES
- **Servidor:** 198.96.94.106
- **Senha:** 102030ab
- **Domínio:** suporte.help

---

## ⚡ INSTALAÇÃO EM 3 PASSOS (10 MINUTOS)

### PASSO 1: Baixar e Enviar Pacote

**No seu computador:**
```bash
# Baixar do Emergent (substitua EMERGENT_HOST pelo host correto)
scp root@salesbot-iaze.preview.emergentagent.com:/app/migration/iaze_migration_package.tar.gz ./

# Enviar para servidor dedicado
scp iaze_migration_package.tar.gz root@198.96.94.106:/root/
```

### PASSO 2: Extrair e Executar

**No servidor dedicado:**
```bash
# Conectar
ssh root@198.96.94.106
# Senha: 102030ab

# Ir para /root
cd /root

# Extrair
tar -xzf iaze_migration_package.tar.gz

# Executar instalação AUTOMATIZADA
bash install_completo.sh
```

### PASSO 3: Configurar DNS

**No provedor do domínio (onde comprou suporte.help):**

Adicionar 2 registros:

**Registro 1:**
```
Tipo: A
Nome: @
Valor: 198.96.94.106
TTL: 3600
```

**Registro 2:**
```
Tipo: A  
Nome: vpn
Valor: 198.96.94.106
TTL: 3600
```

---

## ✅ PRONTO!

Aguarde **5-60 minutos** para DNS propagar.

Depois acesse:
- **https://suporte.help** (IAZE)
- **https://suporte.help/revenda/login**
- **https://vpn.suporte.help** (X-UI)

**Credenciais:**
- Email: admin@suporte.help
- Senha: 102030@ab

---

## 🎯 O QUE O SCRIPT FAZ AUTOMATICAMENTE

✅ Detecta porta do X-UI
✅ Instala Docker + Docker Compose
✅ Instala Certbot (SSL)
✅ Instala e configura Nginx
✅ Configura Firewall
✅ Gera certificados SSL
✅ Restaura backup MongoDB
✅ Sobe todos os containers
✅ Configura proxy reverso
✅ Configura renovação automática SSL

**TUDO AUTOMÁTICO!** Só execute e aguarde!

---

## 📊 TEMPO ESTIMADO

- Download/upload do pacote: **2-5 minutos**
- Execução do script: **5-10 minutos**
- Propagação DNS: **5-60 minutos**

**Total: ~15-75 minutos**

---

## 🚨 SE ALGO DER ERRADO

Ver logs:
```bash
cd /opt/iaze
docker-compose logs -f
```

Reexecutar script:
```bash
cd /root
bash install_completo.sh
```

---

## 📞 COMANDOS ÚTEIS

```bash
# Ver containers
cd /opt/iaze && docker-compose ps

# Ver logs em tempo real
cd /opt/iaze && docker-compose logs -f

# Reiniciar tudo
cd /opt/iaze && docker-compose restart

# Parar tudo
cd /opt/iaze && docker-compose down

# Iniciar tudo
cd /opt/iaze && docker-compose up -d
```

---

## 🎉 RESULTADO FINAL

Após instalação:
- ✅ Sistema 10-20x mais rápido
- ✅ IAZE em https://suporte.help
- ✅ X-UI em https://vpn.suporte.help
- ✅ SSL válido em ambos
- ✅ Sem conflitos
- ✅ Tudo automatizado

**Boa instalação!** 🚀
