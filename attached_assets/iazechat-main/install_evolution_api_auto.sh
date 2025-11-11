#!/bin/bash

###############################################################################
# SCRIPT DE INSTALAÇÃO AUTOMÁTICA - EVOLUTION API PARA WHATSAPP
# Sistema: CYBERTV Suporte
# Versão: 1.0.0
# Data: Janeiro 2025
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   INSTALADOR EVOLUTION API - CYBERTV SUPORTE             ║
║   Sistema WhatsApp Multi-tenant                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
   log_error "Este script precisa ser executado como root (sudo)"
   exit 1
fi

# Solicitar informações do usuário
echo ""
log_info "Vamos configurar seu servidor Evolution API"
echo ""

read -p "Digite o domínio da Evolution API (ex: evolution.seudominio.com): " EVOLUTION_DOMAIN
read -p "Digite o domínio do backend (ex: resellerchat.seudominio.com): " BACKEND_DOMAIN
read -sp "Digite uma chave API segura (min 32 caracteres): " API_KEY
echo ""

if [ ${#API_KEY} -lt 32 ]; then
    log_error "Chave API deve ter no mínimo 32 caracteres!"
    exit 1
fi

# Confirmar
echo ""
echo -e "${YELLOW}Configuração:${NC}"
echo "  Evolution Domain: $EVOLUTION_DOMAIN"
echo "  Backend Domain: $BACKEND_DOMAIN"
echo "  API Key: ${API_KEY:0:10}...${API_KEY: -5}"
echo ""
read -p "Confirma as configurações acima? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Instalação cancelada pelo usuário"
    exit 0
fi

# Atualizar sistema
log_info "Atualizando sistema operacional..."
apt update && apt upgrade -y

# Instalar dependências
log_info "Instalando dependências..."
apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg

# Instalar Docker
log_info "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    log_info "Docker instalado com sucesso"
else
    log_info "Docker já está instalado"
fi

# Instalar Nginx
log_info "Instalando Nginx..."
apt install -y nginx

# Instalar Certbot
log_info "Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# Criar diretório Evolution API
log_info "Configurando Evolution API..."
mkdir -p /opt/evolution-api
cd /opt/evolution-api

# Criar docker-compose.yml
cat > docker-compose.yml << EOF
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
      - SERVER_URL=https://${EVOLUTION_DOMAIN}
      - CORS_ORIGIN=*
      - CORS_METHODS=GET,POST,PUT,DELETE
      - CORS_CREDENTIALS=true
      
      # Authentication
      - AUTHENTICATION_API_KEY=${API_KEY}
      
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
      - WEBHOOK_GLOBAL_URL=https://${BACKEND_DOMAIN}/api/whatsapp/webhook
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

# Configurar Nginx
log_info "Configurando Nginx..."
cat > /etc/nginx/sites-available/evolution << EOF
server {
    listen 80;
    server_name ${EVOLUTION_DOMAIN};
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/evolution /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Iniciar Evolution API
log_info "Iniciando Evolution API..."
docker compose up -d

# Aguardar serviços
log_info "Aguardando serviços iniciarem (30 segundos)..."
sleep 30

# Verificar se está rodando
if docker compose ps | grep -q "Up"; then
    log_info "Evolution API iniciada com sucesso!"
else
    log_error "Erro ao iniciar Evolution API. Verificar logs:"
    docker compose logs
    exit 1
fi

# Configurar SSL
echo ""
log_info "Configurando SSL/HTTPS com Let's Encrypt..."
log_warn "IMPORTANTE: Certifique-se de que o DNS ${EVOLUTION_DOMAIN} está apontando para este servidor!"
echo ""
read -p "DNS configurado corretamente? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Digite seu email para notificações SSL: " SSL_EMAIL
    certbot --nginx -d ${EVOLUTION_DOMAIN} --non-interactive --agree-tos -m ${SSL_EMAIL}
    
    if [ $? -eq 0 ]; then
        log_info "SSL configurado com sucesso!"
    else
        log_warn "Erro ao configurar SSL. Configure manualmente depois."
    fi
else
    log_warn "Pulando configuração SSL. Configure manualmente depois com:"
    echo "  sudo certbot --nginx -d ${EVOLUTION_DOMAIN}"
fi

# Configurar firewall
log_info "Configurando firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Criar script de monitoramento
log_info "Criando script de monitoramento..."
cat > /usr/local/bin/evolution-health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8080/ > /dev/null 2>&1; then
    echo "$(date): Evolution API não responde, reiniciando..."
    cd /opt/evolution-api && docker compose restart
fi
EOF

chmod +x /usr/local/bin/evolution-health-check.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/evolution-health-check.sh") | crontab -

# Criar script de backup
log_info "Criando script de backup..."
cat > /usr/local/bin/evolution-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/evolution"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd /opt/evolution-api

docker run --rm \
  -v evolution_instances:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/evolution_instances_$DATE.tar.gz -C /data .

docker run --rm \
  -v evolution_store:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/evolution_store_$DATE.tar.gz -C /data .

# Limpar backups antigos (manter 7 dias)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "$(date): Backup concluído"
EOF

chmod +x /usr/local/bin/evolution-backup.sh
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/evolution-backup.sh") | crontab -

# Salvar configurações
log_info "Salvando configurações..."
cat > /opt/evolution-api/CONFIG.txt << EOF
=== CONFIGURAÇÃO EVOLUTION API ===

Domínio: ${EVOLUTION_DOMAIN}
Backend: ${BACKEND_DOMAIN}
API Key: ${API_KEY}

URLs:
  Evolution API: https://${EVOLUTION_DOMAIN}
  Webhook: https://${BACKEND_DOMAIN}/api/whatsapp/webhook

Comandos úteis:
  Status: cd /opt/evolution-api && docker compose ps
  Logs: cd /opt/evolution-api && docker compose logs -f
  Restart: cd /opt/evolution-api && docker compose restart
  Stop: cd /opt/evolution-api && docker compose down
  Start: cd /opt/evolution-api && docker compose up -d

Backup: /backups/evolution (automático 3h diariamente)
Monitoramento: /usr/local/bin/evolution-health-check.sh (a cada 5min)

Data instalação: $(date)
EOF

# Mostrar resumo
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!                    ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
log_info "Configurações salvas em: /opt/evolution-api/CONFIG.txt"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Adicione estas variáveis no backend (/app/backend/.env):"
echo "   EVOLUTION_API_URL=\"https://${EVOLUTION_DOMAIN}\""
echo "   EVOLUTION_API_KEY=\"${API_KEY}\""
echo ""
echo "2. Reinicie o backend:"
echo "   sudo supervisorctl restart backend"
echo ""
echo "3. Teste a API:"
echo "   curl https://${EVOLUTION_DOMAIN}/"
echo ""
echo -e "${GREEN}Instalação concluída!${NC}"
echo ""
