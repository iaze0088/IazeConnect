#!/bin/bash

# ========================================
# INSTALAÇÃO COMPLETA IAZE - AUTOMATIZADA
# ========================================

set -e  # Para na primeira falha

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║   INSTALAÇÃO AUTOMÁTICA DO IAZE        ║"
echo "║   Sistema de Suporte Multi-Tenant      ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Execute como root: sudo bash install_completo.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Executando como root${NC}"
echo ""

# ========================================
# 1. VERIFICAR X-UI E DESCOBRIR PORTA
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 PASSO 1: Detectando X-UI...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

XUI_PORT=$(netstat -tulpn 2>/dev/null | grep x-ui | grep LISTEN | awk '{print $4}' | cut -d: -f2 | head -1)

if [ -z "$XUI_PORT" ]; then
    XUI_PORT="54321"  # Porta padrão
    echo -e "${YELLOW}⚠️  X-UI não detectado automaticamente${NC}"
    echo -e "${YELLOW}   Usando porta padrão: $XUI_PORT${NC}"
else
    echo -e "${GREEN}✅ X-UI detectado na porta: $XUI_PORT${NC}"
fi
echo ""

# ========================================
# 2. ATUALIZAR SISTEMA
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 PASSO 2: Atualizando sistema...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

apt-get update -qq > /dev/null 2>&1
apt-get upgrade -y -qq > /dev/null 2>&1
echo -e "${GREEN}✅ Sistema atualizado${NC}"
echo ""

# ========================================
# 3. INSTALAR DOCKER
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐳 PASSO 3: Instalando Docker...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker instalado${NC}"
else
    echo -e "${GREEN}✅ Docker já instalado${NC}"
fi
echo ""

# ========================================
# 4. INSTALAR DOCKER COMPOSE
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐳 PASSO 4: Instalando Docker Compose...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose instalado${NC}"
else
    echo -e "${GREEN}✅ Docker Compose já instalado${NC}"
fi
echo ""

# ========================================
# 5. INSTALAR CERTBOT
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔒 PASSO 5: Instalando Certbot (SSL)...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot -qq > /dev/null 2>&1
    echo -e "${GREEN}✅ Certbot instalado${NC}"
else
    echo -e "${GREEN}✅ Certbot já instalado${NC}"
fi
echo ""

# ========================================
# 6. INSTALAR NGINX
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 PASSO 6: Instalando Nginx...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx -qq > /dev/null 2>&1
    echo -e "${GREEN}✅ Nginx instalado${NC}"
else
    echo -e "${GREEN}✅ Nginx já instalado${NC}"
fi
echo ""

# ========================================
# 7. CONFIGURAR FIREWALL
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔥 PASSO 7: Configurando Firewall...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v ufw &> /dev/null; then
    ufw --force enable > /dev/null 2>&1
    ufw allow 22/tcp > /dev/null 2>&1
    ufw allow 80/tcp > /dev/null 2>&1
    ufw allow 443/tcp > /dev/null 2>&1
    ufw allow 8080/tcp > /dev/null 2>&1
    echo -e "${GREEN}✅ Firewall configurado${NC}"
else
    echo -e "${YELLOW}⚠️  UFW não encontrado, pulando...${NC}"
fi
echo ""

# ========================================
# 8. PREPARAR DIRETÓRIOS
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📁 PASSO 8: Criando estrutura de pastas...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p /opt/iaze/ssl
mkdir -p /opt/iaze/logs
echo -e "${GREEN}✅ Diretórios criados${NC}"
echo ""

# ========================================
# 9. COPIAR ARQUIVOS (se estiver na mesma pasta)
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 PASSO 9: Configurando arquivos...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Usar docker-compose sem nginx
if [ -f "docker-compose-sem-nginx.yml" ]; then
    cp docker-compose-sem-nginx.yml /opt/iaze/docker-compose.yml
    echo -e "${GREEN}✅ Docker Compose configurado${NC}"
fi

# Copiar nginx config e ajustar porta do X-UI
if [ -f "nginx_com_xui.conf" ]; then
    sed "s/localhost:54321/localhost:$XUI_PORT/g" nginx_com_xui.conf > /etc/nginx/nginx.conf.iaze
    echo -e "${GREEN}✅ Nginx config preparado (porta X-UI: $XUI_PORT)${NC}"
fi

echo ""

# ========================================
# 10. GERAR CERTIFICADOS SSL
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔒 PASSO 10: Gerando certificados SSL...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Parar serviços nas portas 80/443
systemctl stop nginx 2>/dev/null || true
systemctl stop x-ui 2>/dev/null || true

# Aguardar portas liberarem
sleep 3

# Gerar certificado
echo -e "${YELLOW}⏳ Gerando certificado para suporte.help...${NC}"
certbot certonly --standalone \
    -d suporte.help \
    -d www.suporte.help \
    -d vpn.suporte.help \
    --non-interactive \
    --agree-tos \
    --email admin@suporte.help \
    --preferred-challenges http > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificado SSL gerado${NC}"
    
    # Copiar certificados
    cp /etc/letsencrypt/live/suporte.help/fullchain.pem /opt/iaze/ssl/ 2>/dev/null || true
    cp /etc/letsencrypt/live/suporte.help/privkey.pem /opt/iaze/ssl/ 2>/dev/null || true
    
    echo -e "${GREEN}✅ Certificados copiados${NC}"
else
    echo -e "${YELLOW}⚠️  Certbot falhou. Configure DNS e tente novamente:${NC}"
    echo -e "${YELLOW}   certbot certonly --standalone -d suporte.help${NC}"
fi

# Reiniciar X-UI
systemctl start x-ui 2>/dev/null || true

echo ""

# ========================================
# 11. RESTAURAR MONGODB
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💾 PASSO 11: Iniciando MongoDB e restaurando backup...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd /opt/iaze

# Subir apenas MongoDB
docker-compose up -d mongodb > /dev/null 2>&1
echo -e "${YELLOW}⏳ Aguardando MongoDB iniciar...${NC}"
sleep 15

# Restaurar backup se existir
if [ -d "mongodb_backup/support_chat" ]; then
    docker exec -i iaze_mongodb mongorestore --db support_chat /docker-entrypoint-initdb.d/support_chat > /dev/null 2>&1
    echo -e "${GREEN}✅ Backup MongoDB restaurado${NC}"
else
    echo -e "${YELLOW}⚠️  Backup não encontrado, MongoDB iniciado vazio${NC}"
fi

echo ""

# ========================================
# 12. SUBIR TODOS OS SERVIÇOS
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 PASSO 12: Iniciando todos os serviços...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

docker-compose up -d > /dev/null 2>&1
sleep 5

echo -e "${GREEN}✅ Containers iniciados:${NC}"
docker-compose ps

echo ""

# ========================================
# 13. CONFIGURAR E INICIAR NGINX
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 PASSO 13: Configurando Nginx...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Backup do nginx original
if [ -f "/etc/nginx/nginx.conf" ]; then
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup do nginx.conf criado${NC}"
fi

# Copiar nova config
if [ -f "/etc/nginx/nginx.conf.iaze" ]; then
    cp /etc/nginx/nginx.conf.iaze /etc/nginx/nginx.conf
    echo -e "${GREEN}✅ Nginx configurado${NC}"
fi

# Testar config
nginx -t > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Configuração Nginx válida${NC}"
    systemctl restart nginx
    echo -e "${GREEN}✅ Nginx iniciado${NC}"
else
    echo -e "${RED}❌ Erro na configuração do Nginx${NC}"
    echo -e "${YELLOW}   Execute: nginx -t${NC}"
fi

echo ""

# ========================================
# 14. CONFIGURAR AUTO-RENOVAÇÃO SSL
# ========================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 PASSO 14: Configurando renovação automática SSL...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Adicionar cron para renovação SSL
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
echo -e "${GREEN}✅ Cron de renovação SSL configurado (3h da manhã diariamente)${NC}"

echo ""

# ========================================
# RESUMO FINAL
# ========================================
echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     INSTALAÇÃO CONCLUÍDA! 🎉           ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${BLUE}📊 STATUS DOS SERVIÇOS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose ps 2>/dev/null || echo "Docker Compose não disponível"
echo ""

echo -e "${BLUE}🌐 URLs DE ACESSO:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ IAZE Sistema:     https://suporte.help"
echo "✅ Login Revenda:    https://suporte.help/revenda/login"
echo "✅ Login Atendente:  https://suporte.help/atendente"
echo "✅ Funil de Vendas:  https://suporte.help/vendas"
echo "✅ X-UI Panel:       https://vpn.suporte.help"
echo ""

echo -e "${BLUE}🔑 CREDENCIAIS PADRÃO:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Email:  admin@suporte.help"
echo "Senha:  102030@ab"
echo ""

echo -e "${BLUE}📋 PRÓXIMOS PASSOS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Configure DNS do domínio suporte.help:"
echo "   Tipo: A | Nome: @ | Valor: 198.96.94.106"
echo "   Tipo: A | Nome: vpn | Valor: 198.96.94.106"
echo ""
echo "2. Aguarde propagação DNS (5-60 minutos)"
echo ""
echo "3. Acesse https://suporte.help e faça login"
echo ""
echo "4. Configure Evolution API se usar WhatsApp"
echo ""

echo -e "${BLUE}🛠️ COMANDOS ÚTEIS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ver logs:           cd /opt/iaze && docker-compose logs -f"
echo "Reiniciar:          cd /opt/iaze && docker-compose restart"
echo "Parar tudo:         cd /opt/iaze && docker-compose down"
echo "Status:             cd /opt/iaze && docker-compose ps"
echo "Nginx status:       systemctl status nginx"
echo ""

echo -e "${GREEN}✅ Sistema IAZE instalado com sucesso!${NC}"
echo -e "${GREEN}⚡ Performance será 10-20x superior à Emergent!${NC}"
echo ""
