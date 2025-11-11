#!/bin/bash
###############################################################################
# DEPLOY COMPLETO IAZE - VPS 151.243.218.223
# Cole este script INTEIRO no terminal do VPS e execute
# Vai instalar e configurar TUDO automaticamente
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║          IAZE - Deploy Automático VPS                      ║${NC}"
echo -e "${GREEN}║          IP: 151.243.218.223                               ║${NC}"
echo -e "${GREEN}║          Domínio: suporte.help                             ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ Execute como root: sudo su${NC}"
   exit 1
fi

echo -e "${BLUE}[INFO] Iniciando deploy completo...${NC}"
sleep 2

# ==============================================================================
# PASSO 1: Parar serviços antigos
# ==============================================================================
echo -e "\n${YELLOW}[1/12] Parando serviços antigos...${NC}"
supervisorctl stop all 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
killall node 2>/dev/null || true
killall python3 2>/dev/null || true
killall uvicorn 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Serviços parados${NC}"

# ==============================================================================
# PASSO 2: Limpar instalações antigas
# ==============================================================================
echo -e "\n${YELLOW}[2/12] Limpando instalações antigas...${NC}"
rm -rf /var/www/iaze
rm -f /etc/nginx/sites-enabled/iaze
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/supervisor/conf.d/iaze-*
rm -f /etc/supervisor/conf.d/cybertv-*
echo -e "${GREEN}✅ Limpeza concluída${NC}"

# ==============================================================================
# PASSO 3: Atualizar sistema e instalar dependências básicas
# ==============================================================================
echo -e "\n${YELLOW}[3/12] Instalando dependências do sistema...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget git build-essential software-properties-common \
    python3 python3-pip python3-venv nginx supervisor \
    ufw apt-transport-https ca-certificates gnupg > /dev/null 2>&1
echo -e "${GREEN}✅ Dependências básicas instaladas${NC}"

# ==============================================================================
# PASSO 4: Instalar Node.js 18.x e Yarn
# ==============================================================================
echo -e "\n${YELLOW}[4/12] Instalando Node.js 18 e Yarn...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs > /dev/null 2>&1
fi
if ! command -v yarn &> /dev/null; then
    npm install -g yarn > /dev/null 2>&1
fi
echo -e "${GREEN}✅ Node.js $(node -v) e Yarn $(yarn -v) instalados${NC}"

# ==============================================================================
# PASSO 5: Instalar MongoDB 6.0
# ==============================================================================
echo -e "\n${YELLOW}[5/12] Instalando MongoDB 6.0...${NC}"
if ! command -v mongod &> /dev/null; then
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - > /dev/null 2>&1
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list > /dev/null
    apt-get update -qq
    apt-get install -y mongodb-org > /dev/null 2>&1
fi
systemctl start mongod
systemctl enable mongod > /dev/null 2>&1
echo -e "${GREEN}✅ MongoDB instalado e rodando${NC}"

# ==============================================================================
# PASSO 6: Criar estrutura de diretórios
# ==============================================================================
echo -e "\n${YELLOW}[6/12] Criando estrutura de diretórios...${NC}"
mkdir -p /var/www/iaze/{backend,frontend}
mkdir -p /var/log/iaze
cd /var/www/iaze
echo -e "${GREEN}✅ Diretórios criados${NC}"

# ==============================================================================
# PASSO 7: Aguardar cópia dos arquivos
# ==============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    ATENÇÃO IMPORTANTE                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Agora você precisa copiar os arquivos do container para este VPS.${NC}"
echo ""
echo -e "${GREEN}EXECUTE ESTES COMANDOS EM OUTRO TERMINAL (do container/local):${NC}"
echo ""
echo -e "${BLUE}# Comprimir arquivos:${NC}"
echo -e "cd /app"
echo -e "tar -czf /tmp/iaze-backend.tar.gz backend/"
echo -e "tar -czf /tmp/iaze-frontend.tar.gz frontend/"
echo ""
echo -e "${BLUE}# Copiar para o VPS:${NC}"
echo -e "scp /tmp/iaze-backend.tar.gz root@151.243.218.223:/tmp/"
echo -e "scp /tmp/iaze-frontend.tar.gz root@151.243.218.223:/tmp/"
echo ""
echo -e "${YELLOW}Pressione ENTER depois de copiar os arquivos...${NC}"
read -p ""

# Verificar se os arquivos foram copiados
if [ ! -f "/tmp/iaze-backend.tar.gz" ] || [ ! -f "/tmp/iaze-frontend.tar.gz" ]; then
    echo -e "${RED}❌ Arquivos não encontrados em /tmp/${NC}"
    echo -e "${YELLOW}Execute os comandos acima para copiar os arquivos e tente novamente.${NC}"
    exit 1
fi

# Extrair arquivos
echo -e "\n${YELLOW}Extraindo arquivos...${NC}"
tar -xzf /tmp/iaze-backend.tar.gz -C /var/www/iaze/ 2>/dev/null || {
    echo -e "${RED}❌ Erro ao extrair backend${NC}"
    exit 1
}
tar -xzf /tmp/iaze-frontend.tar.gz -C /var/www/iaze/ 2>/dev/null || {
    echo -e "${RED}❌ Erro ao extrair frontend${NC}"
    exit 1
}
echo -e "${GREEN}✅ Arquivos extraídos${NC}"

# ==============================================================================
# PASSO 8: Configurar Backend
# ==============================================================================
echo -e "\n${YELLOW}[8/12] Configurando Backend...${NC}"
cd /var/www/iaze/backend

# Criar ambiente virtual Python
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
echo -e "${BLUE}Instalando dependências Python (pode demorar)...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Criar arquivo .env
cat > .env << 'ENVEOF'
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

# Health Monitor
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_TIMEOUT=5
HEALTH_MAX_FAILURES=3

# VAPID Keys
VAPID_PUBLIC_KEY=BOozFZ70h_Yg9mylQQdpC4eQLape96unxkMAbKdog9IwpMZkhGYxYTlR803Lch0QagjZi2hYTPiNZI1qSEK6oKM
VAPID_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgu6dtMTqMCOlNBX+h
Nj0pfPQh86a1NyRmLQZ17BSEGq+hRANCAATqMxWe9If2IPZspUEHaQuHkC2qXver
p8ZDAGynaIPSMKTGZIRmMWE5UfNNy3IdEGoI2YtoWEz4jWSNakhCuqCj
-----END PRIVATE KEY-----

# XUI IPTV Integration
XUI_API_URL=http://209.14.88.42:8080
XUI_API_KEY=FjgJpVPv
ENVEOF

deactivate
echo -e "${GREEN}✅ Backend configurado${NC}"

# ==============================================================================
# PASSO 9: Configurar Frontend
# ==============================================================================
echo -e "\n${YELLOW}[9/12] Configurando Frontend...${NC}"
cd /var/www/iaze/frontend

# Criar arquivo .env
cat > .env << 'ENVEOF'
REACT_APP_BACKEND_URL=http://151.243.218.223
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
REACT_APP_WPPCONNECT_URL=http://95.217.178.51:21465
ENVEOF

# Instalar dependências
echo -e "${BLUE}Instalando dependências Node.js (pode demorar bastante)...${NC}"
yarn install > /dev/null 2>&1

# Build do frontend
echo -e "${BLUE}Buildando frontend (aguarde 2-3 minutos)...${NC}"
yarn build > /dev/null 2>&1

echo -e "${GREEN}✅ Frontend buildado com sucesso${NC}"

# ==============================================================================
# PASSO 10: Configurar Nginx
# ==============================================================================
echo -e "\n${YELLOW}[10/12] Configurando Nginx...${NC}"

cat > /etc/nginx/sites-available/iaze << 'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name 151.243.218.223 suporte.help www.suporte.help;
    
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
        
        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        
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
NGINXEOF

# Ativar site
ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/iaze
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx > /dev/null 2>&1

echo -e "${GREEN}✅ Nginx configurado e rodando${NC}"

# ==============================================================================
# PASSO 11: Configurar Supervisor
# ==============================================================================
echo -e "\n${YELLOW}[11/12] Configurando Supervisor...${NC}"

# Backend
cat > /etc/supervisor/conf.d/iaze-backend.conf << 'SUPEOF'
[program:iaze-backend]
command=/var/www/iaze/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze/backend.err.log
stdout_logfile=/var/log/iaze/backend.out.log
user=root
environment=PYTHONUNBUFFERED=1
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
SUPEOF

# WhatsApp Polling
cat > /etc/supervisor/conf.d/iaze-whatsapp.conf << 'SUPEOF'
[program:iaze-whatsapp-polling]
command=/var/www/iaze/backend/venv/bin/python whatsapp_polling.py
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze/whatsapp.err.log
stdout_logfile=/var/log/iaze/whatsapp.out.log
user=root
environment=PYTHONUNBUFFERED=1
SUPEOF

# Recarregar Supervisor
supervisorctl reread > /dev/null 2>&1
supervisorctl update > /dev/null 2>&1
sleep 3
supervisorctl restart all > /dev/null 2>&1

echo -e "${GREEN}✅ Supervisor configurado${NC}"

# ==============================================================================
# PASSO 12: Configurar Firewall
# ==============================================================================
echo -e "\n${YELLOW}[12/12] Configurando Firewall...${NC}"
ufw --force enable > /dev/null 2>&1
ufw allow 22/tcp > /dev/null 2>&1  # SSH
ufw allow 80/tcp > /dev/null 2>&1  # HTTP
ufw allow 443/tcp > /dev/null 2>&1 # HTTPS
ufw status > /dev/null 2>&1
echo -e "${GREEN}✅ Firewall configurado${NC}"

# ==============================================================================
# VERIFICAÇÃO FINAL
# ==============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              VERIFICANDO SERVIÇOS                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

sleep 5

# MongoDB
echo -ne "${YELLOW}MongoDB...${NC} "
if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}✅ RODANDO${NC}"
else
    echo -e "${RED}❌ PARADO${NC}"
fi

# Nginx
echo -ne "${YELLOW}Nginx...${NC} "
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ RODANDO${NC}"
else
    echo -e "${RED}❌ PARADO${NC}"
fi

# Backend
echo -ne "${YELLOW}Backend...${NC} "
if supervisorctl status iaze-backend 2>/dev/null | grep -q RUNNING; then
    echo -e "${GREEN}✅ RODANDO${NC}"
else
    echo -e "${RED}❌ PARADO (verifique logs)${NC}"
fi

# WhatsApp Polling
echo -ne "${YELLOW}WhatsApp Polling...${NC} "
if supervisorctl status iaze-whatsapp-polling 2>/dev/null | grep -q RUNNING; then
    echo -e "${GREEN}✅ RODANDO${NC}"
else
    echo -e "${YELLOW}⚠️  OPCIONAL${NC}"
fi

# Teste de conectividade
echo ""
echo -ne "${YELLOW}Testando Backend API...${NC} "
sleep 2
if curl -s http://localhost:8001/api/health 2>/dev/null | grep -q "healthy"; then
    echo -e "${GREEN}✅ RESPONDENDO${NC}"
else
    echo -e "${RED}❌ NÃO RESPONDE${NC}"
    echo -e "${YELLOW}Vendo últimas linhas do log:${NC}"
    tail -20 /var/log/iaze/backend.err.log
fi

# ==============================================================================
# CONCLUSÃO
# ==============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              🎉 DEPLOY CONCLUÍDO COM SUCESSO! 🎉          ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 URLs de Acesso:${NC}"
echo -e "   ${GREEN}http://151.243.218.223/admin/login${NC}"
echo -e "   ${GREEN}http://suporte.help/admin/login${NC}"
echo ""
echo -e "${BLUE}🔑 Credenciais:${NC}"
echo -e "   ${YELLOW}Admin:${NC} admin@admin.com / 102030@ab"
echo -e "   ${YELLOW}Atendentes:${NC} biancaatt, jessicaatt, andressaatt, leticiaatt / ab181818ab"
echo -e "   ${YELLOW}Revendedor:${NC} fabioro@example.com / 102030a"
echo ""
echo -e "${BLUE}📊 Status dos Serviços:${NC}"
echo -e "   supervisorctl status"
echo ""
echo -e "${BLUE}📝 Ver Logs:${NC}"
echo -e "   tail -f /var/log/iaze/backend.err.log"
echo -e "   tail -f /var/log/nginx/error.log"
echo ""
echo -e "${BLUE}🔄 Reiniciar Serviços:${NC}"
echo -e "   supervisorctl restart iaze-backend"
echo -e "   systemctl restart nginx"
echo ""
echo -e "${GREEN}✨ Sistema IAZE instalado e funcionando! ✨${NC}"
echo ""
