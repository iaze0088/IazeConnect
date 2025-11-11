#!/bin/bash

echo "🚀 INSTALAÇÃO DO SISTEMA IAZE - SERVIDOR DEDICADO"
echo "=================================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Por favor, execute como root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Executando como root${NC}"
echo ""

# 1. Atualizar sistema
echo -e "${YELLOW}📦 Atualizando sistema...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

# 2. Instalar Docker
echo -e "${YELLOW}🐳 Instalando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker instalado${NC}"
else
    echo -e "${GREEN}✅ Docker já está instalado${NC}"
fi

# 3. Instalar Docker Compose
echo -e "${YELLOW}🐳 Instalando Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose instalado${NC}"
else
    echo -e "${GREEN}✅ Docker Compose já está instalado${NC}"
fi

# 4. Instalar Certbot para SSL
echo -e "${YELLOW}🔒 Instalando Certbot (SSL)...${NC}"
apt-get install -y certbot -qq
echo -e "${GREEN}✅ Certbot instalado${NC}"

# 5. Configurar Firewall
echo -e "${YELLOW}🔥 Configurando Firewall...${NC}"
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # Evolution API
echo -e "${GREEN}✅ Firewall configurado${NC}"

# 6. Criar diretórios necessários
echo -e "${YELLOW}📁 Criando estrutura de diretórios...${NC}"
mkdir -p /opt/iaze
mkdir -p /opt/iaze/ssl
mkdir -p /opt/iaze/mongodb_backup
echo -e "${GREEN}✅ Diretórios criados${NC}"

echo ""
echo -e "${GREEN}✅ INSTALAÇÃO DE DEPENDÊNCIAS CONCLUÍDA!${NC}"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Copie os arquivos do sistema para /opt/iaze"
echo "2. Configure o arquivo .env"
echo "3. Gere certificados SSL com: certbot certonly --standalone -d suporte.help"
echo "4. Execute: cd /opt/iaze && docker-compose up -d"
echo ""
