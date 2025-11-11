# 🚀 GUIA DE UPGRADE - EVOLUTION API v2.3.6

## ⚠️ PROBLEMA ATUAL
- Evolution API v1.8.6 NÃO tem volumes persistentes
- Instâncias WhatsApp somem quando API reinicia
- Webhooks não são mantidos

## ✅ SOLUÇÃO: EVOLUTION API v2.3.6 COM PERSISTÊNCIA

---

## 📋 PASSO A PASSO

### 1️⃣ PREPARAÇÃO NO SERVIDOR (45.157.157.69)

Conecte-se via SSH no servidor:
```bash
ssh root@45.157.157.69
```

### 2️⃣ FAZER BACKUP DA VERSÃO ATUAL

```bash
# Verificar containers rodando
docker ps -a

# Fazer backup dos dados (se houver)
mkdir -p /opt/backups
docker exec evolution-api tar czf - /evolution 2>/dev/null > /opt/backups/evolution-backup-$(date +%Y%m%d).tar.gz || echo "Sem dados para backup"

# Parar containers antigos
docker stop evolution-api postgres redis 2>/dev/null || true
```

### 3️⃣ BAIXAR E EXTRAIR EVOLUTION API v2.3.6

```bash
# Criar diretório
mkdir -p /opt/evolution-api
cd /opt/evolution-api

# Baixar arquivo
wget https://customer-assets.emergentagent.com/job_wa-bridge-1/artifacts/1v3ots2w_evolution-api-2.3.6.tar.gz -O evolution-api-2.3.6.tar.gz

# Extrair
tar -xzf evolution-api-2.3.6.tar.gz
cd evolution-api-2.3.6
```

### 4️⃣ CRIAR ARQUIVO .ENV COM CONFIGURAÇÕES CORRETAS

```bash
cat > .env << 'EOF'
# Server Configuration
SERVER_NAME=evolution
SERVER_TYPE=http
SERVER_PORT=8080
SERVER_URL=http://evolution.suporte.help:8080

# Cors
CORS_ORIGIN=*
CORS_METHODS=GET,POST,PUT,DELETE
CORS_CREDENTIALS=true

# Logs
LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG,VERBOSE,DARK,WEBHOOKS
LOG_COLOR=true
LOG_BAILEYS=error

# Instance Management
DEL_INSTANCE=false

# Database Configuration
DATABASE_PROVIDER=postgresql
POSTGRES_HOST=evolution-postgres
POSTGRES_PORT=5432
POSTGRES_USER=evolution
POSTGRES_PASSWORD=evolution_secure_2025
POSTGRES_DATABASE=evolution_db
DATABASE_CONNECTION_URI=postgresql://evolution:evolution_secure_2025@evolution-postgres:5432/evolution_db?schema=evolution_api
DATABASE_CONNECTION_CLIENT_NAME=evolution_iaze

# Database Save Options
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
DATABASE_SAVE_DATA_HISTORIC=true

# Redis Configuration
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=redis://evolution-redis:6379/6
CACHE_REDIS_TTL=604800
CACHE_REDIS_PREFIX_KEY=evolution
CACHE_REDIS_SAVE_INSTANCES=true

# Authentication
AUTHENTICATION_API_KEY=iaze-evolution-2025-secure-key
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

# Telemetry
TELEMETRY_ENABLED=false
EOF
```

### 5️⃣ AJUSTAR DOCKER-COMPOSE.YAML (EXPOR PORTA 8080)

```bash
# Editar docker-compose.yaml para expor porta publicamente
sed -i 's/127.0.0.1:8080:8080/8080:8080/g' docker-compose.yaml
```

### 6️⃣ INICIAR EVOLUTION API v2.3.6

```bash
# Criar network
docker network create evolution-net 2>/dev/null || true

# Remover dokploy-network do docker-compose se não existir
sed -i '/dokploy-network:/d' docker-compose.yaml
sed -i '/external: true/d' docker-compose.yaml

# Iniciar com docker-compose
docker-compose up -d

# Aguardar 30 segundos para inicialização
sleep 30

# Verificar status
docker-compose ps
docker-compose logs api | tail -50
```

### 7️⃣ TESTAR EVOLUTION API

```bash
# Testar API
curl http://localhost:8080

# Deve retornar algo como:
# {"status":200,"message":"Welcome to the Evolution API...","version":"2.3.6"}
```

### 8️⃣ VERIFICAR VOLUMES PERSISTENTES

```bash
# Listar volumes
docker volume ls | grep evolution

# Deve mostrar:
# evolution_instances
# evolution_redis
# postgres_data
```

---

## 🔍 VERIFICAÇÃO DE FUNCIONAMENTO

### Teste 1: API está respondendo
```bash
curl http://evolution.suporte.help:8080
```

### Teste 2: Criar instância de teste
```bash
curl -X POST http://evolution.suporte.help:8080/instance/create \
  -H "apikey: iaze-evolution-2025-secure-key" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "test_instance",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### Teste 3: Reiniciar e verificar persistência
```bash
# Reiniciar API
docker-compose restart api

# Aguardar 10 segundos
sleep 10

# Buscar instâncias (deve manter a instância criada)
curl http://evolution.suporte.help:8080/instance/fetchInstances \
  -H "apikey: iaze-evolution-2025-secure-key"
```

---

## 🛠️ RESOLUÇÃO DE PROBLEMAS

### Se a API não iniciar:
```bash
# Ver logs completos
docker-compose logs -f api

# Verificar se PostgreSQL está ok
docker-compose logs postgres

# Verificar se Redis está ok
docker-compose logs redis
```

### Se houver erro de conexão com banco:
```bash
# Entrar no container PostgreSQL
docker exec -it evolution_postgres psql -U evolution -d evolution_db

# Verificar conexão
\conninfo
\q
```

### Reiniciar tudo do zero:
```bash
# Parar e remover tudo
docker-compose down -v

# Remover volumes (CUIDADO: apaga dados!)
docker volume rm evolution_instances evolution_redis postgres_data

# Iniciar novamente
docker-compose up -d
```

---

## 📊 MONITORAMENTO

### Ver logs em tempo real:
```bash
docker-compose logs -f api
```

### Ver uso de recursos:
```bash
docker stats evolution_api evolution_postgres evolution_redis
```

---

## ✅ CONFIRMAÇÃO DE SUCESSO

Após concluir, você deve ter:
1. ✅ Evolution API v2.3.6 rodando
2. ✅ PostgreSQL com volume persistente
3. ✅ Redis com volume persistente
4. ✅ Instâncias WhatsApp mantidas após restart
5. ✅ Webhooks persistindo corretamente

---

## 🔗 INTEGRAÇÃO COM IAZE

Após a instalação bem-sucedida, o backend IAZE já está configurado para usar:
- **URL**: http://evolution.suporte.help:8080
- **API Key**: iaze-evolution-2025-secure-key

Não é necessário alterar nada no backend IAZE! 🎉

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verifique os logs: `docker-compose logs -f api`
2. Verifique se todos os containers estão rodando: `docker-compose ps`
3. Teste a conexão: `curl http://localhost:8080`
