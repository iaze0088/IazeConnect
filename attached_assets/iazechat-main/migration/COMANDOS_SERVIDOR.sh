#!/bin/bash
#########################################################
# COMANDOS PARA INSTALAR IAZE NO SERVIDOR DEDICADO
# Copie e cole BLOCO POR BLOCO no terminal
#########################################################

# ========================================
# BLOCO 1: Docker Compose (docker-compose.yml)
# ========================================
cd /opt/iaze
cat > docker-compose.yml << 'DOCKER_COMPOSE_EOF'
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
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 10s
      retries: 5

  backend:
    image: python:3.11-slim
    container_name: iaze_backend
    restart: always
    working_dir: /app
    ports:
      - "8001:8001"
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      MONGO_URL: "mongodb://mongodb:27017"
      DB_NAME: "support_chat"
      JWT_SECRET: "sua-chave-secreta-super-segura-aqui-2024"
      CORS_ORIGINS: "*"
      ADMIN_PASSWORD: "102030@ab"
      EMERGENT_LLM_KEY: "sk-emergent-eE19e23F32621EdFcF"
      EVOLUTION_API_URL: "http://evolution.suporte.help:8080"
      EVOLUTION_API_KEY: "iaze-evolution-2025-secure-key"
      USE_EXTERNAL_STORAGE: "true"
      EXTERNAL_STORAGE_HOST: "198.96.94.106"
      EXTERNAL_STORAGE_PORT: "9000"
      VAPID_PUBLIC_KEY: "BOozFZ70h_Yg9mylQQdpC4eQLape96unxkMAbKdog9IwpMZkhGYxYTlR803Lch0QagjZi2hYTPiNZI1qSEK6oKM"
    volumes:
      - ./backend:/app
      - backend_uploads:/app/uploads
    networks:
      - iaze_network
    command: bash -c "apt-get update && apt-get install -y build-essential && pip install --no-cache-dir -r requirements.txt && python -m uvicorn server:app --host 0.0.0.0 --port 8001"

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
      REACT_APP_BACKEND_URL: "https://suporte.help"
      NODE_ENV: "production"
    volumes:
      - ./frontend:/app
      - frontend_node_modules:/app/node_modules
    networks:
      - iaze_network
    command: sh -c "yarn install --network-timeout 100000 && yarn start"

volumes:
  mongodb_data:
  backend_uploads:
  frontend_node_modules:

networks:
  iaze_network:
    driver: bridge
DOCKER_COMPOSE_EOF

echo "✅ docker-compose.yml criado!"

# ========================================
# BLOCO 2: Configuração Nginx
# ========================================
cat > /etc/nginx/sites-available/iaze << 'NGINX_EOF'
server {
    listen 80;
    listen [::]:80;
    server_name suporte.help www.suporte.help;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name suporte.help www.suporte.help;

    ssl_certificate /etc/letsencrypt/live/suporte.help/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/suporte.help/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

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
        proxy_read_timeout 86400;
    }

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
NGINX_EOF

ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "✅ Nginx configurado!"

# ========================================
# BLOCO 3: Obter certificado SSL
# ========================================
echo "🔒 Obtendo certificado SSL..."
certbot --nginx -d suporte.help -d www.suporte.help --non-interactive --agree-tos --email admin@suporte.help

echo "✅ SSL configurado!"

# ========================================
# BLOCO 4: Criar diretórios
# ========================================
cd /opt/iaze
mkdir -p backend frontend mongodb_backup

echo "✅ Diretórios criados!"

# ========================================
# PRÓXIMOS PASSOS MANUAIS
# ========================================
echo ""
echo "========================================="
echo "✅ CONFIGURAÇÃO BASE COMPLETA!"
echo "========================================="
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. COPIAR CÓDIGO BACKEND E FRONTEND"
echo "   (Vou te passar os arquivos em seguida)"
echo ""
echo "2. RESTAURAR BACKUP DO MONGODB"
echo "   (Vou te passar o comando)"
echo ""
echo "3. INICIAR OS CONTAINERS:"
echo "   cd /opt/iaze"
echo "   docker-compose up -d"
echo ""
echo "4. VERIFICAR LOGS:"
echo "   docker-compose logs -f"
echo ""
