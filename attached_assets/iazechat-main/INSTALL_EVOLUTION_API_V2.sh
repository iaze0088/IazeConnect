#!/bin/bash
# ============================================================================
# INSTALAÇÃO EVOLUTION API V2.1.1 - SERVIDOR IAZE (151.243.218.223)
# ============================================================================
# 
# INSTRUÇÕES DE USO:
# 1. Copiar este script para o servidor 151.243.218.223
# 2. Executar: chmod +x INSTALL_EVOLUTION_API_V2.sh
# 3. Executar: ./INSTALL_EVOLUTION_API_V2.sh
#
# ============================================================================

set -e  # Parar em caso de erro

echo "🚀 =============================================="
echo "🚀 INSTALAÇÃO EVOLUTION API V2.1.1"
echo "🚀 Servidor: suporte.help (151.243.218.223)"
echo "🚀 =============================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variáveis de configuração
EVOLUTION_VERSION="v2.1.1"
EVOLUTION_PORT="8080"
POSTGRES_PORT="5432"
REDIS_PORT="6379"
EVOLUTION_API_KEY="iaze-evolution-2025-secure-key"
POSTGRES_PASSWORD="iaze-postgres-2025"
POSTGRES_USER="evolution"
POSTGRES_DB="evolution"

echo -e "${YELLOW}📋 Verificando ambiente...${NC}"

# 1. Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado!${NC}"
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✅ Docker instalado${NC}"

# 2. Verificar portas em uso
echo -e "${YELLOW}🔍 Verificando portas em uso...${NC}"
if netstat -tuln | grep -q ":${EVOLUTION_PORT} "; then
    echo -e "${YELLOW}⚠️  Porta ${EVOLUTION_PORT} já está em uso!${NC}"
    echo "Containers rodando na porta 8080:"
    docker ps --filter "publish=8080" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    read -p "Deseja parar esses containers? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        docker ps --filter "publish=8080" -q | xargs -r docker stop
        echo -e "${GREEN}✅ Containers parados${NC}"
    else
        echo -e "${RED}❌ Instalação cancelada. Libere a porta 8080 primeiro.${NC}"
        exit 1
    fi
fi

# 3. Criar diretório para Evolution API
echo -e "${YELLOW}📁 Criando diretórios...${NC}"
mkdir -p /opt/evolution-api
cd /opt/evolution-api

# 4. Criar docker-compose.yml
echo -e "${YELLOW}📝 Criando docker-compose.yml...${NC}"
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: evolution_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT}:5432"
    networks:
      - evolution_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: evolution_redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT}:6379"
    networks:
      - evolution_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Evolution API
  evolution-api:
    image: atendai/evolution-api:${EVOLUTION_VERSION}
    container_name: evolution_api
    restart: unless-stopped
    ports:
      - "${EVOLUTION_PORT}:8080"
    environment:
      # API Configuration
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - CORS_ORIGIN=*
      - CORS_METHODS=GET,POST,PUT,DELETE
      - CORS_CREDENTIALS=true
      
      # Authentication
      - AUTHENTICATION_TYPE=apikey
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      - AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true
      
      # Database PostgreSQL
      - DATABASE_ENABLED=true
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?schema=public
      - DATABASE_SAVE_DATA_INSTANCE=true
      - DATABASE_SAVE_DATA_NEW_MESSAGE=true
      - DATABASE_SAVE_MESSAGE_UPDATE=true
      - DATABASE_SAVE_DATA_CONTACTS=true
      - DATABASE_SAVE_DATA_CHATS=true
      
      # Redis Cache
      - CACHE_REDIS_ENABLED=true
      - CACHE_REDIS_URI=redis://redis:6379
      - CACHE_REDIS_PREFIX_KEY=evolution
      - CACHE_REDIS_SAVE_INSTANCES=true
      - CACHE_LOCAL_ENABLED=false
      
      # QR Code Configuration
      - QRCODE_LIMIT=30
      - QRCODE_COLOR=#198754
      
      # WhatsApp Configuration
      - WEBSOCKET_ENABLED=true
      - WEBSOCKET_GLOBAL_EVENTS=false
      - CONFIG_SESSION_PHONE_CLIENT=Evolution API
      - CONFIG_SESSION_PHONE_NAME=Chrome
      
      # Logs
      - LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG,VERBOSE,DARK,WEBHOOKS
      - LOG_COLOR=true
      - LOG_BAILEYS=error
      
      # Instance Configuration
      - DEL_INSTANCE=false
      - DEL_TEMP_INSTANCES=true
      
      # Webhook
      - WEBHOOK_GLOBAL_ENABLED=false
      - WEBHOOK_GLOBAL_URL=
      - WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false
      
      # RabbitMQ (Desabilitado)
      - RABBITMQ_ENABLED=false
      
      # Chatwoot (Desabilitado)
      - CHATWOOT_MESSAGE_READ=false
      
    volumes:
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store
    networks:
      - evolution_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  evolution_instances:
    driver: local
  evolution_store:
    driver: local

networks:
  evolution_network:
    driver: bridge
EOF

echo -e "${GREEN}✅ docker-compose.yml criado${NC}"

# 5. Iniciar serviços
echo -e "${YELLOW}🚀 Iniciando Evolution API...${NC}"
echo "Isso pode demorar alguns minutos na primeira vez..."

docker-compose down -v 2>/dev/null || true
docker-compose pull
docker-compose up -d

# 6. Aguardar serviços ficarem prontos
echo -e "${YELLOW}⏳ Aguardando serviços iniciarem...${NC}"
sleep 10

# Verificar PostgreSQL
echo -n "Verificando PostgreSQL... "
for i in {1..30}; do
    if docker exec evolution_postgres pg_isready -U ${POSTGRES_USER} &>/dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        break
    fi
    sleep 2
    echo -n "."
done

# Verificar Redis
echo -n "Verificando Redis... "
for i in {1..30}; do
    if docker exec evolution_redis redis-cli ping &>/dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        break
    fi
    sleep 2
    echo -n "."
done

# Verificar Evolution API
echo -n "Verificando Evolution API... "
for i in {1..60}; do
    if curl -s http://localhost:${EVOLUTION_PORT} | grep -q "Evolution API"; then
        echo -e "${GREEN}✅ OK${NC}"
        break
    fi
    sleep 3
    echo -n "."
done

# 7. Testar API
echo ""
echo -e "${YELLOW}🧪 Testando Evolution API...${NC}"
RESPONSE=$(curl -s http://localhost:${EVOLUTION_PORT})
if echo "$RESPONSE" | grep -q "Evolution API"; then
    echo -e "${GREEN}✅ Evolution API está respondendo!${NC}"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}❌ Evolution API não está respondendo corretamente${NC}"
    echo "Response: $RESPONSE"
    echo ""
    echo "Verificando logs..."
    docker-compose logs --tail=50 evolution-api
    exit 1
fi

# 8. Mostrar informações finais
echo ""
echo -e "${GREEN}✅ =============================================="
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "✅ ==============================================${NC}"
echo ""
echo -e "${YELLOW}📋 INFORMAÇÕES DA INSTALAÇÃO:${NC}"
echo ""
echo "🌐 Evolution API URL: http://151.243.218.223:${EVOLUTION_PORT}"
echo "🔑 API Key: ${EVOLUTION_API_KEY}"
echo ""
echo "📊 PostgreSQL:"
echo "   - Host: localhost:${POSTGRES_PORT}"
echo "   - User: ${POSTGRES_USER}"
echo "   - Password: ${POSTGRES_PASSWORD}"
echo "   - Database: ${POSTGRES_DB}"
echo ""
echo "📦 Redis:"
echo "   - Host: localhost:${REDIS_PORT}"
echo ""
echo -e "${YELLOW}📝 PRÓXIMOS PASSOS:${NC}"
echo ""
echo "1. Verificar status dos containers:"
echo "   docker-compose ps"
echo ""
echo "2. Ver logs da Evolution API:"
echo "   docker-compose logs -f evolution-api"
echo ""
echo "3. Testar criação de instância:"
echo "   curl -X POST http://localhost:${EVOLUTION_PORT}/instance/create \\"
echo "     -H 'apikey: ${EVOLUTION_API_KEY}' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"instanceName\": \"teste\", \"integration\": \"WHATSAPP-BAILEYS\", \"qrcode\": true}'"
echo ""
echo "4. Parar serviços:"
echo "   cd /opt/evolution-api && docker-compose down"
echo ""
echo "5. Reiniciar serviços:"
echo "   cd /opt/evolution-api && docker-compose restart"
echo ""
echo -e "${GREEN}🎉 Evolution API V2.1.1 instalado com sucesso!${NC}"
echo ""

# 9. Criar script de gerenciamento
cat > /usr/local/bin/evolution-ctl <<'EOFCTL'
#!/bin/bash
cd /opt/evolution-api
case "$1" in
    start)
        docker-compose up -d
        echo "Evolution API iniciado"
        ;;
    stop)
        docker-compose down
        echo "Evolution API parado"
        ;;
    restart)
        docker-compose restart
        echo "Evolution API reiniciado"
        ;;
    status)
        docker-compose ps
        ;;
    logs)
        docker-compose logs -f evolution-api
        ;;
    *)
        echo "Uso: evolution-ctl {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOFCTL

chmod +x /usr/local/bin/evolution-ctl

echo -e "${GREEN}✅ Comando 'evolution-ctl' criado para gerenciar a Evolution API${NC}"
echo "   Uso: evolution-ctl {start|stop|restart|status|logs}"
echo ""
