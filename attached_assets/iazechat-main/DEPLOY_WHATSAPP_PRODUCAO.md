# 🚀 GUIA DE DEPLOY - SISTEMA WHATSAPP EM PRODUÇÃO

## 📋 PRÉ-REQUISITOS

### **Servidor Principal (Backend + Frontend)**
- Ubuntu 20.04+ ou similar
- 2GB RAM mínimo (4GB recomendado)
- 20GB disco
- Python 3.9+
- Node.js 18+
- MongoDB 5.0+

### **Servidor Evolution API (Separado)**
- Ubuntu 20.04+
- 1GB RAM mínimo (2GB recomendado)
- 10GB disco
- Docker 20.10+
- Docker Compose 2.0+

---

## 🔧 PASSO 1: INSTALAR EVOLUTION API (Servidor Separado)

### **1.1 Instalar Docker**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adicionar repositório Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalação
docker --version
docker compose version
```

### **1.2 Baixar e Configurar Evolution API**

```bash
# Criar diretório
mkdir -p ~/evolution-api
cd ~/evolution-api

# Criar docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  evolution-api:
    image: atendai/evolution-api:latest
    container_name: evolution-api
    restart: always
    ports:
      - "8080:8080"
    environment:
      # Server Config
      - SERVER_URL=https://evolution.seudominio.com
      - CORS_ORIGIN=*
      - CORS_METHODS=GET,POST,PUT,DELETE
      - CORS_CREDENTIALS=true
      
      # Authentication
      - AUTHENTICATION_API_KEY=SUA_CHAVE_SUPER_SEGURA_AQUI_2024
      
      # Database (PostgreSQL)
      - DATABASE_ENABLED=true
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@postgres:5432/evolution
      - DATABASE_SAVE_DATA_INSTANCE=true
      - DATABASE_SAVE_DATA_NEW_MESSAGE=true
      - DATABASE_SAVE_MESSAGE_UPDATE=true
      - DATABASE_SAVE_DATA_CONTACTS=true
      - DATABASE_SAVE_DATA_CHATS=true
      
      # Webhook
      - WEBHOOK_GLOBAL_ENABLED=true
      - WEBHOOK_GLOBAL_URL=https://resellerchat.seudominio.com/api/whatsapp/webhook
      - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=true
      - WEBHOOK_EVENTS_QRCODE_UPDATED=true
      - WEBHOOK_EVENTS_MESSAGES_UPSERT=true
      - WEBHOOK_EVENTS_CONNECTION_UPDATE=true
      
      # Log
      - LOG_LEVEL=ERROR
      - LOG_COLOR=true
      
      # Storage
      - STORE_MESSAGES=true
      - STORE_CONTACTS=true
      - STORE_CHATS=true
      
      # QR Code
      - QRCODE_LIMIT=30
      - QRCODE_COLOR=#198754
      
    volumes:
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store
    
    depends_on:
      - postgres
    
    networks:
      - evolution-network

  postgres:
    image: postgres:15-alpine
    container_name: postgres-evolution
    restart: always
    environment:
      - POSTGRES_USER=evolution
      - POSTGRES_PASSWORD=evolution123
      - POSTGRES_DB=evolution
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - evolution-network

volumes:
  evolution_instances:
  evolution_store:
  postgres_data:

networks:
  evolution-network:
    driver: bridge
EOF

# Iniciar serviços
docker compose up -d

# Verificar logs
docker compose logs -f evolution-api
```

### **1.3 Configurar SSL/HTTPS (Nginx + Let's Encrypt)**

```bash
# Instalar Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Criar configuração Nginx
sudo tee /etc/nginx/sites-available/evolution << 'EOF'
server {
    listen 80;
    server_name evolution.seudominio.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# Ativar site
sudo ln -s /etc/nginx/sites-available/evolution /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obter certificado SSL
sudo certbot --nginx -d evolution.seudominio.com
```

### **1.4 Testar Evolution API**

```bash
# Testar endpoint
curl https://evolution.seudominio.com/

# Deve retornar informações da API
```

---

## 🔧 PASSO 2: CONFIGURAR BACKEND (Servidor Principal)

### **2.1 Atualizar Variáveis de Ambiente**

```bash
# Editar arquivo .env do backend
cd /app/backend
nano .env
```

**Adicionar/Atualizar:**
```bash
# Evolution API WhatsApp
EVOLUTION_API_URL="https://evolution.seudominio.com"
EVOLUTION_API_KEY="SUA_CHAVE_SUPER_SEGURA_AQUI_2024"
```

### **2.2 Reiniciar Backend**

```bash
sudo supervisorctl restart backend
```

### **2.3 Verificar Logs**

```bash
tail -f /var/log/supervisor/backend.*.log | grep -i "whatsapp\|evolution"
```

---

## 🔧 PASSO 3: CONFIGURAR DNS E DOMÍNIOS

### **3.1 Configurar DNS Principal**

**Registros necessários:**
```
Tipo A: resellerchat.seudominio.com → IP_SERVIDOR_PRINCIPAL
Tipo A: *.suporte.help → IP_SERVIDOR_PRINCIPAL (wildcard para subdomínios)
Tipo A: evolution.seudominio.com → IP_SERVIDOR_EVOLUTION
```

### **3.2 Cloudflare (Recomendado)**

1. Adicionar domínio ao Cloudflare
2. Criar registros DNS:
   - `resellerchat.seudominio.com` → IP servidor principal
   - `*.suporte.help` → IP servidor principal (wildcard)
   - `evolution.seudominio.com` → IP servidor evolution
3. Ativar SSL/TLS (Full ou Full Strict)
4. Ativar proteção DDoS

---

## 🔧 PASSO 4: CONFIGURAR FIREWALL

### **4.1 Servidor Principal**

```bash
# UFW Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### **4.2 Servidor Evolution API**

```bash
# UFW Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp  # Evolution API (interno)
sudo ufw enable
```

---

## 🔧 PASSO 5: BACKUP E MONITORAMENTO

### **5.1 Configurar Backup Automático**

```bash
# Criar script de backup
sudo tee /usr/local/bin/backup-whatsapp.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backups/whatsapp"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --uri="mongodb://localhost:27017/support_chat" --out="$BACKUP_DIR/mongo_$DATE"

# Backup Evolution API volumes
docker run --rm \
  -v evolution_instances:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/evolution_instances_$DATE.tar.gz -C /data .

docker run --rm \
  -v evolution_store:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/evolution_store_$DATE.tar.gz -C /data .

# Limpar backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup concluído: $DATE"
EOF

sudo chmod +x /usr/local/bin/backup-whatsapp.sh

# Agendar backup diário (3h da manhã)
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-whatsapp.sh") | crontab -
```

### **5.2 Monitoramento de Saúde**

```bash
# Criar script de verificação
sudo tee /usr/local/bin/check-whatsapp-health.sh << 'EOF'
#!/bin/bash

# Verificar backend
if ! curl -f http://localhost:8001/api/whatsapp/stats > /dev/null 2>&1; then
    echo "ALERTA: Backend WhatsApp não está respondendo!"
    sudo supervisorctl restart backend
fi

# Verificar Evolution API
if ! curl -f http://localhost:8080/ > /dev/null 2>&1; then
    echo "ALERTA: Evolution API não está respondendo!"
    cd ~/evolution-api && docker compose restart
fi

# Verificar uso de disco
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERTA: Disco acima de 80%!"
fi
EOF

sudo chmod +x /usr/local/bin/check-whatsapp-health.sh

# Executar a cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/check-whatsapp-health.sh") | crontab -
```

---

## 📊 PASSO 6: VERIFICAÇÃO FINAL

### **6.1 Checklist de Verificação**

```bash
# 1. Verificar Evolution API
curl https://evolution.seudominio.com/

# 2. Verificar Backend
curl https://resellerchat.seudominio.com/api/whatsapp/stats

# 3. Verificar MongoDB
mongo --eval "db.adminCommand('ping')"

# 4. Verificar Frontend
curl https://resellerchat.seudominio.com/

# 5. Verificar logs
tail -n 100 /var/log/supervisor/backend.*.log
docker compose -f ~/evolution-api/docker-compose.yml logs --tail=100
```

### **6.2 Teste de Conexão WhatsApp**

1. Acessar: `https://resellerchat.seudominio.com/reseller-login`
2. Login com credenciais de revenda
3. Ir em "WhatsApp"
4. Clicar em "Adicionar Número"
5. Escanear QR Code no WhatsApp
6. Aguardar status mudar para "connected"

---

## 🔐 PASSO 7: SEGURANÇA ADICIONAL

### **7.1 Configurar Rate Limiting**

```bash
# Adicionar no Nginx (/etc/nginx/nginx.conf)
http {
    limit_req_zone $binary_remote_addr zone=whatsapp:10m rate=10r/s;
    
    # No server block da Evolution API
    location /instance/create {
        limit_req zone=whatsapp burst=5;
    }
}
```

### **7.2 Adicionar Autenticação Extra**

```bash
# Gerar senha para Nginx basic auth
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Adicionar no Nginx (Evolution API)
location / {
    auth_basic "Evolution API";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... resto da configuração
}
```

---

## 📝 TROUBLESHOOTING

### **Problema: Evolution API não inicia**

```bash
# Verificar logs
cd ~/evolution-api
docker compose logs evolution-api

# Verificar PostgreSQL
docker compose logs postgres

# Reiniciar tudo
docker compose down
docker compose up -d
```

### **Problema: Webhook não funciona**

```bash
# Verificar se URL está acessível
curl -X POST https://resellerchat.seudominio.com/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Verificar logs do backend
tail -f /var/log/supervisor/backend.*.log | grep webhook
```

### **Problema: QR Code não aparece**

```bash
# Verificar se instância foi criada
curl https://evolution.seudominio.com/instance/list \
  -H "apikey: SUA_CHAVE_AQUI"

# Buscar QR Code manualmente
curl https://evolution.seudominio.com/instance/connect/NOME_INSTANCIA \
  -H "apikey: SUA_CHAVE_AQUI"
```

---

## ✅ CHECKLIST FINAL DE DEPLOY

- [ ] Evolution API rodando com SSL
- [ ] Backend configurado com URL correta
- [ ] Frontend acessível via HTTPS
- [ ] DNS configurado (principal + wildcard)
- [ ] Firewall configurado
- [ ] Backup automático ativado
- [ ] Monitoramento configurado
- [ ] Teste de conexão WhatsApp realizado
- [ ] Documentação entregue à equipe

---

## 📞 SUPORTE

Em caso de problemas durante o deploy:
1. Verificar logs: `/var/log/supervisor/`
2. Verificar Docker: `docker compose logs`
3. Verificar conectividade: `curl` nos endpoints
4. Consultar documentação: `/app/SISTEMA_WHATSAPP_COMPLETO.md`

---

**Sistema desenvolvido e documentado com sucesso ✅**  
**Data: Janeiro 2025**
