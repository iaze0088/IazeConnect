#!/bin/bash

echo "=========================================="
echo "  INSTALAÇÃO EVOLUTION API v2.3.6"
echo "  Com Volumes Persistentes"
echo "=========================================="
echo ""

# 1. PARAR CONTAINERS ANTIGOS
echo "🛑 Passo 1/7: Parando containers antigos..."
docker stop evolution-api postgres redis 2>/dev/null
docker rm evolution-api postgres redis 2>/dev/null
echo "✅ Containers antigos removidos"
echo ""

# 2. CRIAR DIRETÓRIO
echo "📁 Passo 2/7: Criando diretório..."
mkdir -p /opt/evolution-api
cd /opt/evolution-api
echo "✅ Diretório criado: /opt/evolution-api"
echo ""

# 3. BAIXAR EVOLUTION API v2.3.6
echo "⬇️ Passo 3/7: Baixando Evolution API v2.3.6..."
wget -q --show-progress https://customer-assets.emergentagent.com/job_wa-bridge-1/artifacts/1v3ots2w_evolution-api-2.3.6.tar.gz -O evolution.tar.gz
echo "✅ Download concluído"
echo ""

# 4. EXTRAIR ARQUIVOS
echo "📦 Passo 4/7: Extraindo arquivos..."
tar -xzf evolution.tar.gz
cd evolution-api-2.3.6
echo "✅ Arquivos extraídos"
echo ""

# 5. CRIAR ARQUIVO .ENV
echo "⚙️ Passo 5/7: Criando arquivo de configuração..."
cat > .env << 'EOF'
SERVER_NAME=evolution
SERVER_TYPE=http
SERVER_PORT=8080
SERVER_URL=http://evolution.suporte.help:8080

CORS_ORIGIN=*
CORS_METHODS=GET,POST,PUT,DELETE
CORS_CREDENTIALS=true

LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG,VERBOSE,DARK,WEBHOOKS
LOG_COLOR=true
LOG_BAILEYS=error

DEL_INSTANCE=false

DATABASE_PROVIDER=postgresql
POSTGRES_HOST=evolution-postgres
POSTGRES_PORT=5432
POSTGRES_USER=evolution
POSTGRES_PASSWORD=evolution_secure_2025
POSTGRES_DATABASE=evolution_db
DATABASE_CONNECTION_URI=postgresql://evolution:evolution_secure_2025@evolution-postgres:5432/evolution_db?schema=evolution_api
DATABASE_CONNECTION_CLIENT_NAME=evolution_iaze

DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
DATABASE_SAVE_DATA_HISTORIC=true

CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=redis://evolution-redis:6379/6
CACHE_REDIS_TTL=604800
CACHE_REDIS_PREFIX_KEY=evolution
CACHE_REDIS_SAVE_INSTANCES=true

AUTHENTICATION_API_KEY=iaze-evolution-2025-secure-key
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

TELEMETRY_ENABLED=false
EOF
echo "✅ Arquivo .env criado"
echo ""

# 6. AJUSTAR DOCKER-COMPOSE (Expor porta publicamente)
echo "🔧 Passo 6/7: Ajustando docker-compose..."
sed -i 's/127.0.0.1:8080:8080/8080:8080/g' docker-compose.yaml
sed -i '/dokploy-network:/d' docker-compose.yaml
sed -i '/external: true/d' docker-compose.yaml
echo "✅ Docker-compose ajustado"
echo ""

# 7. INICIAR EVOLUTION API
echo "🚀 Passo 7/7: Iniciando Evolution API..."
docker network create evolution-net 2>/dev/null || true
docker-compose up -d

echo ""
echo "⏳ Aguardando 30 segundos para inicialização..."
sleep 30

# VERIFICAR STATUS
echo ""
echo "=========================================="
echo "  STATUS DOS CONTAINERS"
echo "=========================================="
docker-compose ps
echo ""

# TESTAR API
echo "=========================================="
echo "  TESTANDO API"
echo "=========================================="
curl -s http://localhost:8080 | grep -o '"version":"[^"]*"' || echo "❌ API não está respondendo ainda"
echo ""

# VERIFICAR VOLUMES
echo "=========================================="
echo "  VOLUMES PERSISTENTES CRIADOS"
echo "=========================================="
docker volume ls | grep evolution

echo ""
echo "=========================================="
echo "✅ INSTALAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "🔗 URL: http://evolution.suporte.help:8080"
echo "🔑 API Key: iaze-evolution-2025-secure-key"
echo ""
echo "📋 COMANDOS ÚTEIS:"
echo "  Ver logs:      docker-compose logs -f api"
echo "  Reiniciar:     docker-compose restart"
echo "  Parar:         docker-compose down"
echo "  Ver status:    docker-compose ps"
echo ""
