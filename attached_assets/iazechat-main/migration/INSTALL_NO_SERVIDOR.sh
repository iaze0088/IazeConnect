#!/bin/bash
# Script de instalação completa do IAZE no servidor dedicado
# Execute este script no servidor 198.96.94.106

set -e

echo "🚀 Iniciando instalação do IAZE..."

# Ir para diretório de instalação
cd /opt/iaze

# Criar estrutura de diretórios
echo "📁 Criando diretórios..."
mkdir -p backend frontend mongodb_backup ssl

# ========================================
# 1. DOCKER-COMPOSE.YML
# ========================================
echo "📝 Criando docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: iaze_mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: support_chat
    networks:
      - iaze_network

  backend:
    image: python:3.11-slim
    container_name: iaze_backend
    restart: always
    working_dir: /app
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=support_chat
      - JWT_SECRET=sua-chave-secreta-super-segura-aqui-2024
      - CORS_ORIGINS=*
      - ADMIN_PASSWORD=102030@ab
      - EMERGENT_LLM_KEY=sk-emergent-eE19e23F32621EdFcF
      - EVOLUTION_API_URL=http://evolution.suporte.help:8080
      - EVOLUTION_API_KEY=iaze-evolution-2025-secure-key
      - USE_EXTERNAL_STORAGE=true
      - EXTERNAL_STORAGE_HOST=198.96.94.106
      - EXTERNAL_STORAGE_PORT=9000
      - VAPID_PUBLIC_KEY=BOozFZ70h_Yg9mylQQdpC4eQLape96unxkMAbKdog9IwpMZkhGYxYTlR803Lch0QagjZi2hYTPiNZI1qSEK6oKM
      - VAPID_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgu6dtMTqMCOlNBX+h
Nj0pfPQh86a1NyRmLQZ17BSEGq+hRANCAATqMxWe9If2IPZspUEHaQuHkC2qXver
p8ZDAGynaIPSMKTGZIRmMWE5UfNNy3IdEGoI2YtoWEz4jWSNakhCuqCj
-----END PRIVATE KEY-----
    volumes:
      - backend_data:/app
      - backend_uploads:/app/uploads
    networks:
      - iaze_network
    command: bash -c "pip install --no-cache-dir -r requirements.txt && python -m uvicorn server:app --host 0.0.0.0 --port 8001"

  frontend:
    image: node:18-alpine
    container_name: iaze_frontend
    restart: always
    working_dir: /app
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=https://suporte.help
      - NODE_ENV=production
    volumes:
      - frontend_data:/app
    networks:
      - iaze_network
    command: sh -c "yarn install && yarn start"

volumes:
  mongodb_data:
  backend_data:
  backend_uploads:
  frontend_data:

networks:
  iaze_network:
    driver: bridge
EOF

# ========================================
# 2. NGINX CONFIGURATION
# ========================================
echo "📝 Criando configuração do Nginx..."
cat > /etc/nginx/sites-available/iaze << 'EOF'
# Configuração principal do IAZE
server {
    listen 80;
    listen [::]:80;
    server_name suporte.help www.suporte.help;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name suporte.help www.suporte.help;

    # SSL certificates (will be created by Certbot)
    ssl_certificate /etc/letsencrypt/live/suporte.help/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/suporte.help/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_read_timeout 86400;
    }

    # WebSocket específico
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/

# ========================================
# 3. BAIXAR BACKUP DO MONGODB
# ========================================
echo "📦 Baixando backup do MongoDB..."
cd /opt/iaze
# Nota: Este link precisa ser atualizado com o link correto
# Por enquanto, vamos criar um backup vazio
mkdir -p mongodb_backup

# ========================================
# 4. BAIXAR CÓDIGO FONTE
# ========================================
echo "📥 Preparando código fonte..."
echo "⚠️  ATENÇÃO: Você precisará copiar manualmente os arquivos backend/ e frontend/"
echo "    Use SCP ou SFTP para transferir os diretórios"

# ========================================
# 5. INICIAR SERVIÇOS
# ========================================
echo "🔧 Testando configuração do Nginx..."
nginx -t

echo "🔄 Recarregando Nginx..."
systemctl reload nginx

echo "✅ Instalação base completa!"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Transferir código backend e frontend para /opt/iaze/"
echo "2. Restaurar backup do MongoDB"
echo "3. Obter certificado SSL: certbot --nginx -d suporte.help -d www.suporte.help"
echo "4. Iniciar containers: cd /opt/iaze && docker-compose up -d"
echo ""
echo "🔗 Após conclusão, acesse: https://suporte.help"
EOF

chmod +x /app/migration/INSTALL_NO_SERVIDOR.sh
