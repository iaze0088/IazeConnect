#!/bin/bash
#########################################################
# DEPLOY RÁPIDO IAZE - Execute no VPS 151.243.218.223
# Como usar: bash deploy_rapido_vps.sh
#########################################################

set -e

echo "🚀 IAZE - Deploy Rápido no VPS"
echo "================================"

# Cores
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
NC='\033[0m'

# Verificar root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${R}Execute como root: sudo bash deploy_rapido_vps.sh${NC}"
   exit 1
fi

# Parar serviços antigos se existirem
echo -e "${Y}Parando serviços antigos...${NC}"
supervisorctl stop all 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Limpar instalações antigas
echo -e "${Y}Limpando instalações antigas...${NC}"
rm -rf /var/www/iaze
rm -f /etc/nginx/sites-enabled/iaze
rm -f /etc/supervisor/conf.d/iaze-*

# Criar diretório
mkdir -p /var/www/iaze/backend /var/www/iaze/frontend

echo -e "${G}✅ Ambiente preparado${NC}"
echo ""
echo -e "${Y}PRÓXIMOS PASSOS:${NC}"
echo "1. Transfira os arquivos para o VPS:"
echo ""
echo "   # Do seu computador/container atual:"
echo "   scp -r /app/backend root@151.243.218.223:/var/www/iaze/"
echo "   scp -r /app/frontend root@151.243.218.223:/var/www/iaze/"
echo ""
echo "2. Após copiar, execute a Parte 2 deste script:"
echo "   bash deploy_rapido_vps.sh parte2"
echo ""

if [ "$1" == "parte2" ]; then
    echo -e "${Y}Executando Parte 2 - Configuração...${NC}"
    
    # Verificar se arquivos foram copiados
    if [ ! -d "/var/www/iaze/backend" ] || [ ! -d "/var/www/iaze/frontend" ]; then
        echo -e "${R}❌ Arquivos não encontrados em /var/www/iaze/${NC}"
        echo "Execute primeiro: scp -r /app/backend root@151.243.218.223:/var/www/iaze/"
        echo "                  scp -r /app/frontend root@151.243.218.223:/var/www/iaze/"
        exit 1
    fi
    
    # Instalar dependências se necessário
    echo -e "${Y}Verificando dependências...${NC}"
    
    # Python
    if ! command -v python3 &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv
    fi
    
    # Node.js e Yarn
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
    
    if ! command -v yarn &> /dev/null; then
        npm install -g yarn
    fi
    
    # Nginx
    if ! command -v nginx &> /dev/null; then
        apt-get install -y nginx
    fi
    
    # Supervisor
    if ! command -v supervisorctl &> /dev/null; then
        apt-get install -y supervisor
    fi
    
    # MongoDB
    if ! command -v mongod &> /dev/null; then
        echo -e "${R}MongoDB não instalado. Instalando...${NC}"
        wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        apt-get update
        apt-get install -y mongodb-org
        systemctl start mongod
        systemctl enable mongod
    fi
    
    echo -e "${G}✅ Dependências OK${NC}"
    
    # Configurar Backend
    echo -e "${Y}Configurando Backend...${NC}"
    cd /var/www/iaze/backend
    
    # Criar venv
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependências
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Configurar .env
    cat > .env << 'ENVEOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=support_chat
CORS_ORIGINS=*
JWT_SECRET=sua-chave-secreta-super-segura-aqui-2024
ADMIN_PASSWORD=102030ab
EMERGENT_LLM_KEY=sk-emergent-eE19e23F32621EdFcF
PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
EVOLUTION_API_URL=http://evolution.suporte.help:8080
EVOLUTION_API_KEY=iaze-evolution-2025-secure-key
USE_EXTERNAL_STORAGE=false
EXTERNAL_STORAGE_HOST=198.96.94.106
EXTERNAL_STORAGE_PORT=9000
ENVEOF
    
    echo -e "${G}✅ Backend configurado${NC}"
    
    # Configurar Frontend
    echo -e "${Y}Configurando Frontend...${NC}"
    cd /var/www/iaze/frontend
    
    # Configurar .env
    cat > .env << 'ENVEOF'
REACT_APP_BACKEND_URL=http://151.243.218.223
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
REACT_APP_WPPCONNECT_URL=http://95.217.178.51:21465
ENVEOF
    
    # Instalar dependências
    yarn install
    
    # Build
    echo -e "${Y}Buildando frontend (aguarde...)${NC}"
    yarn build
    
    echo -e "${G}✅ Frontend buildado${NC}"
    
    # Configurar Nginx
    echo -e "${Y}Configurando Nginx...${NC}"
    cat > /etc/nginx/sites-available/iaze << 'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name 151.243.218.223 suporte.help _;
    client_max_body_size 100M;
    
    root /var/www/iaze/frontend/build;
    index index.html;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
}
NGINXEOF
    
    ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/iaze
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl restart nginx
    
    echo -e "${G}✅ Nginx configurado${NC}"
    
    # Configurar Supervisor
    echo -e "${Y}Configurando Supervisor...${NC}"
    cat > /etc/supervisor/conf.d/iaze-backend.conf << 'SUPEOF'
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
SUPEOF
    
    cat > /etc/supervisor/conf.d/iaze-whatsapp.conf << 'SUPEOF'
[program:iaze-whatsapp-polling]
command=/var/www/iaze/backend/venv/bin/python whatsapp_polling.py
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze-whatsapp.err.log
stdout_logfile=/var/log/iaze-whatsapp.out.log
user=root
SUPEOF
    
    supervisorctl reread
    supervisorctl update
    sleep 3
    supervisorctl restart all
    
    echo -e "${G}✅ Supervisor configurado${NC}"
    
    # Verificar
    echo ""
    echo -e "${Y}Verificando serviços...${NC}"
    sleep 5
    
    if supervisorctl status iaze-backend | grep -q RUNNING; then
        echo -e "${G}✅ Backend RODANDO${NC}"
    else
        echo -e "${R}❌ Backend não iniciou. Vendo logs:${NC}"
        tail -20 /var/log/iaze-backend.err.log
    fi
    
    if systemctl is-active --quiet nginx; then
        echo -e "${G}✅ Nginx RODANDO${NC}"
    else
        echo -e "${R}❌ Nginx não iniciou${NC}"
    fi
    
    if systemctl is-active --quiet mongod; then
        echo -e "${G}✅ MongoDB RODANDO${NC}"
    else
        echo -e "${R}❌ MongoDB não iniciou${NC}"
        systemctl start mongod
    fi
    
    # Teste final
    echo ""
    echo -e "${Y}Teste de conectividade:${NC}"
    if curl -s http://localhost:8001/api/health | grep -q "healthy"; then
        echo -e "${G}✅ Backend respondendo!${NC}"
        echo -e "${G}✅ DEPLOY COMPLETO!${NC}"
        echo ""
        echo "🎉 Sistema IAZE instalado com sucesso!"
        echo ""
        echo "Acesse: http://151.243.218.223/admin/login"
        echo "Admin: admin@admin.com / 102030@ab"
    else
        echo -e "${R}❌ Backend não está respondendo${NC}"
        echo "Verifique os logs: tail -f /var/log/iaze-backend.err.log"
    fi
fi
