#!/bin/bash

# ============================================
# Script de Deploy Rápido - Sistema IAZE
# ============================================

set -e

echo "🚀 Iniciando deployment do Sistema IAZE..."

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Por favor, execute como root${NC}"
    exit 1
fi

# Variáveis
PROJECT_DIR="/var/www/iaze"
DOMAIN="seu-dominio.com"

# 1. Instalar dependências do sistema
echo -e "\n${YELLOW}📦 Instalando dependências do sistema...${NC}"
apt-get update
apt-get install -y curl git nginx

# 2. Instalar Node.js 20
echo -e "\n${YELLOW}📦 Instalando Node.js 20...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# 3. Instalar PM2
echo -e "\n${YELLOW}📦 Instalando PM2...${NC}"
npm install -g pm2

# 4. Criar diretório do projeto
echo -e "\n${YELLOW}📁 Criando diretório do projeto...${NC}"
mkdir -p $PROJECT_DIR

# 5. Mensagem sobre upload de arquivos
echo -e "\n${GREEN}✅ Preparação concluída!${NC}"
echo -e "${YELLOW}📤 Agora faça o upload dos arquivos do projeto para: $PROJECT_DIR${NC}"
echo -e "${YELLOW}   Use SCP, SFTP ou Git para copiar os arquivos${NC}"
echo ""
echo -e "Exemplos:"
echo -e "  SCP:  scp -r ./projeto root@SEU_IP:$PROJECT_DIR/"
echo -e "  Git:  cd $PROJECT_DIR && git clone <URL_REPO> ."
echo ""
read -p "Pressione ENTER depois de copiar os arquivos para continuar..."

# 6. Verificar se arquivos foram copiados
if [ ! -f "$PROJECT_DIR/package.json" ]; then
    echo -e "${RED}❌ Arquivos do projeto não encontrados em $PROJECT_DIR${NC}"
    echo -e "${YELLOW}   Certifique-se de copiar todos os arquivos do projeto${NC}"
    exit 1
fi

# 7. Instalar dependências do projeto
echo -e "\n${YELLOW}📦 Instalando dependências do projeto...${NC}"
cd $PROJECT_DIR
npm install --production

# 8. Criar arquivo .env se não existir
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "\n${YELLOW}⚙️  Criando arquivo .env...${NC}"
    cat > .env << 'EOF'
NODE_ENV=production
PORT=5000
SESSION_SECRET=CHANGE_THIS_TO_RANDOM_STRING

WPPCONNECT_API_URL=http://wppconnect.suporte.help:21465
WPPCONNECT_SECRET_KEY=YOUR_SECRET_KEY_HERE
EOF
    echo -e "${RED}⚠️  IMPORTANTE: Edite o arquivo .env e configure as variáveis${NC}"
    echo -e "${YELLOW}   nano $PROJECT_DIR/.env${NC}"
fi

# 9. Configurar PM2
echo -e "\n${YELLOW}⚙️  Configurando PM2...${NC}"
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'iaze',
    script: 'server/index.ts',
    interpreter: 'node',
    interpreter_args: '--loader tsx',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 5000
    }
  }]
};
EOF

# 10. Iniciar aplicação
echo -e "\n${YELLOW}🚀 Iniciando aplicação...${NC}"
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 11. Configurar Nginx
echo -e "\n${YELLOW}⚙️  Configurando Nginx...${NC}"
cat > /etc/nginx/sites-available/iaze << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 12. Configurar firewall
echo -e "\n${YELLOW}🔥 Configurando firewall...${NC}"
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
echo "y" | ufw enable

# 13. Finalização
echo -e "\n${GREEN}✅ Deployment concluído com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📊 Próximos passos:${NC}"
echo -e "  1. Edite o arquivo .env: nano $PROJECT_DIR/.env"
echo -e "  2. Configure seu domínio para apontar para este servidor"
echo -e "  3. Instale SSL com: certbot --nginx -d $DOMAIN"
echo -e "  4. Acesse: http://$DOMAIN/admin"
echo ""
echo -e "${YELLOW}🔍 Comandos úteis:${NC}"
echo -e "  Ver logs:        pm2 logs iaze"
echo -e "  Status:          pm2 status"
echo -e "  Reiniciar:       pm2 restart iaze"
echo -e "  Parar:           pm2 stop iaze"
echo ""
echo -e "${GREEN}🎉 Sistema IAZE está pronto!${NC}"
