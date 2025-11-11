#!/bin/bash

#########################################################
# Deploy Completo IAZE para VPS 151.243.218.223
# Execute este script NO SERVIDOR VPS como root
#########################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IAZE - Deploy para VPS  ${NC}"
echo -e "${GREEN}  IP: 151.243.218.223      ${NC}"
echo -e "${GREEN}========================================${NC}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Por favor, execute como root${NC}"
   exit 1
fi

# Configurações
APP_DIR="/var/www/iaze"
DOMAIN="151.243.218.223"

echo -e "${YELLOW}[1/8] Verificando sistema...${NC}"
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✅ Nginx já instalado${NC}"
else
    echo -e "${YELLOW}Instalando Nginx...${NC}"
    apt-get update
    apt-get install -y nginx
fi

if command -v mongod &> /dev/null; then
    echo -e "${GREEN}✅ MongoDB já instalado${NC}"
else
    echo -e "${RED}❌ MongoDB não encontrado. Instale com:${NC}"
    echo "wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -"
    echo "echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse' | tee /etc/apt/sources.list.d/mongodb-org-6.0.list"
    echo "apt-get update && apt-get install -y mongodb-org"
    exit 1
fi

if command -v supervisorctl &> /dev/null; then
    echo -e "${GREEN}✅ Supervisor já instalado${NC}"
else
    echo -e "${YELLOW}Instalando Supervisor...${NC}"
    apt-get install -y supervisor
fi

echo -e "${YELLOW}[2/8] Criando diretório da aplicação...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${YELLOW}[3/8] Baixando código da aplicação...${NC}"
echo -e "${GREEN}Por favor, transfira os arquivos do container para este servidor:${NC}"
echo -e "  scp -r root@<container-ip>:/app/backend $APP_DIR/"
echo -e "  scp -r root@<container-ip>:/app/frontend $APP_DIR/"
echo ""
echo -e "${YELLOW}Ou use git se o código estiver em um repositório${NC}"
echo ""
read -p "Pressione ENTER quando os arquivos estiverem copiados..."

if [ ! -d "$APP_DIR/backend" ] || [ ! -d "$APP_DIR/frontend" ]; then
    echo -e "${RED}❌ Diretórios backend ou frontend não encontrados em $APP_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}[4/8] Configurando Backend...${NC}"
cd $APP_DIR/backend

# Instalar Python venv se necessário
if ! command -v python3 &> /dev/null; then
    apt-get install -y python3 python3-pip python3-venv
fi

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar/atualizar .env
cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=support_chat
CORS_ORIGINS=*
JWT_SECRET=sua-chave-secreta-super-segura-aqui-2024
ADMIN_PASSWORD=102030ab
EMERGENT_LLM_KEY=sk-emergent-eE19e23F32621EdFcF
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers

# Evolution API WhatsApp
EVOLUTION_API_URL=http://evolution.suporte.help:8080
EVOLUTION_API_KEY=iaze-evolution-2025-secure-key

# External Storage
USE_EXTERNAL_STORAGE=false
EXTERNAL_STORAGE_HOST=198.96.94.106
EXTERNAL_STORAGE_PORT=9000
EOF

echo -e "${GREEN}✅ Backend configurado${NC}"

echo -e "${YELLOW}[5/8] Configurando Frontend...${NC}"
cd $APP_DIR/frontend

# Instalar Node.js se necessário
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# Instalar Yarn se necessário
if ! command -v yarn &> /dev/null; then
    npm install -g yarn
fi

# Atualizar .env do frontend
cat > .env << EOF
REACT_APP_BACKEND_URL=http://151.243.218.223
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
REACT_APP_WPPCONNECT_URL=http://95.217.178.51:21465
EOF

# Instalar dependências
yarn install

# Build do frontend
echo -e "${YELLOW}Buildando frontend (pode demorar alguns minutos)...${NC}"
yarn build

echo -e "${GREEN}✅ Frontend buildado${NC}"

echo -e "${YELLOW}[6/8] Configurando Nginx...${NC}"

# Backup da configuração antiga se existir
if [ -f /etc/nginx/sites-enabled/iaze ]; then
    cp /etc/nginx/sites-enabled/iaze /etc/nginx/sites-enabled/iaze.backup
fi

# Criar nova configuração
cat > /etc/nginx/sites-available/iaze << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name 151.243.218.223 suporte.help;
    
    client_max_body_size 100M;
    
    # Frontend - Serve React build
    root /var/www/iaze/frontend/build;
    index index.html;
    
    # Backend API - Proxy to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Frontend routes - SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache control for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Disable cache for index.html
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/iaze
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reload Nginx
systemctl reload nginx

echo -e "${GREEN}✅ Nginx configurado${NC}"

echo -e "${YELLOW}[7/8] Configurando Supervisor para Backend...${NC}"

cat > /etc/supervisor/conf.d/iaze-backend.conf << EOF
[program:iaze-backend]
command=/var/www/iaze/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze-backend.err.log
stdout_logfile=/var/log/iaze-backend.out.log
user=root
environment=PYTHONUNBUFFERED=1
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
EOF

# Configurar WhatsApp Polling
cat > /etc/supervisor/conf.d/iaze-whatsapp-polling.conf << EOF
[program:iaze-whatsapp-polling]
command=/var/www/iaze/backend/venv/bin/python /var/www/iaze/backend/whatsapp_polling.py
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze-whatsapp-polling.err.log
stdout_logfile=/var/log/iaze-whatsapp-polling.out.log
user=root
environment=PYTHONUNBUFFERED=1
EOF

# Recarregar Supervisor
supervisorctl reread
supervisorctl update
sleep 3
supervisorctl restart iaze-backend iaze-whatsapp-polling

echo -e "${GREEN}✅ Supervisor configurado${NC}"

echo -e "${YELLOW}[8/8] Verificando serviços...${NC}"

# Verificar MongoDB
if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}✅ MongoDB rodando${NC}"
else
    echo -e "${RED}❌ MongoDB não está rodando. Iniciando...${NC}"
    systemctl start mongod
    systemctl enable mongod
fi

# Verificar Nginx
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx rodando${NC}"
else
    echo -e "${RED}❌ Nginx não está rodando${NC}"
    systemctl start nginx
fi

# Verificar Backend
sleep 5
if supervisorctl status iaze-backend | grep -q RUNNING; then
    echo -e "${GREEN}✅ Backend rodando${NC}"
else
    echo -e "${RED}❌ Backend não está rodando. Verificando logs:${NC}"
    tail -20 /var/log/iaze-backend.err.log
fi

# Testar Backend
echo -e "${YELLOW}Testando backend...${NC}"
if curl -s http://localhost:8001/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend respondendo corretamente${NC}"
else
    echo -e "${RED}❌ Backend não está respondendo${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploy Concluído! 🚀    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "${GREEN}✅ Domínio:${NC} http://151.243.218.223"
echo -e "${GREEN}✅ Backend:${NC} Porta 8001"
echo -e "${GREEN}✅ Frontend:${NC} Build servido pelo Nginx"
echo -e "${GREEN}✅ MongoDB:${NC} Rodando localmente"
echo -e ""
echo -e "${YELLOW}Credenciais:${NC}"
echo -e "  Admin: admin@admin.com / 102030@ab"
echo -e "  Atendentes: [usuario] / ab181818ab"
echo -e "  Revendedor: fabioro@example.com / 102030a"
echo -e ""
echo -e "${YELLOW}Comandos Úteis:${NC}"
echo -e "  Ver logs backend: tail -f /var/log/iaze-backend.err.log"
echo -e "  Reiniciar backend: supervisorctl restart iaze-backend"
echo -e "  Status: supervisorctl status"
echo -e "  Testar: curl http://localhost:8001/api/health"
echo -e ""
echo -e "${GREEN}Acesse: http://151.243.218.223/admin/login${NC}"
echo -e "${GREEN}========================================${NC}"
