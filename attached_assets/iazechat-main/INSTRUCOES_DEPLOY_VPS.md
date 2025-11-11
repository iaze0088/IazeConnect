# 🚀 Instruções de Deploy para VPS 151.243.218.223

## 📋 Pré-requisitos no VPS:
- Ubuntu 20.04+ ou Debian 11+
- Acesso root via SSH
- Portas 80, 8001 abertas no firewall

## 🔧 Passo 1: Preparar Pacote de Deploy

Execute no seu computador local (ou pode pular e fazer direto no VPS):

```bash
# Criar pacote compactado com o código
cd /app
tar -czf iaze-deploy.tar.gz backend/ frontend/ deploy_to_vps.sh
```

## 📤 Passo 2: Transferir para o VPS

### Opção A: Via SCP (do seu computador)
```bash
scp /app/iaze-deploy.tar.gz root@151.243.218.223:/root/
scp /app/deploy_to_vps.sh root@151.243.218.223:/root/
```

### Opção B: Direto no VPS via wget
```bash
# Conectar no VPS
ssh root@151.243.218.223

# Criar diretório temporário
mkdir -p /root/iaze-deploy
cd /root/iaze-deploy

# Copiar arquivos manualmente ou usar git clone se tiver repositório
```

## 🚀 Passo 3: Executar Deploy no VPS

```bash
# Conectar via SSH
ssh root@151.243.218.223
# Senha: 102030ab

# Dar permissão de execução
chmod +x /root/deploy_to_vps.sh

# Extrair arquivos (se usou tar)
cd /root
tar -xzf iaze-deploy.tar.gz -C /var/www/iaze/

# OU criar diretórios e copiar manualmente
mkdir -p /var/www/iaze
# Copiar backend/ e frontend/ para /var/www/iaze/

# Executar script de deploy
cd /root
./deploy_to_vps.sh
```

## ⚡ Passo 3 ALTERNATIVO: Deploy Manual Rápido

Se preferir fazer manualmente, execute estes comandos no VPS:

```bash
# 1. Instalar dependências básicas
apt-get update
apt-get install -y nginx supervisor python3 python3-pip python3-venv nodejs npm mongodb-org

# 2. Instalar Yarn
npm install -g yarn

# 3. Criar diretórios
mkdir -p /var/www/iaze
cd /var/www/iaze

# 4. Copiar código (ajuste o caminho conforme necessário)
# Você precisará copiar /app/backend e /app/frontend para aqui

# 5. Configurar Backend
cd /var/www/iaze/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Criar .env
cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=support_chat
CORS_ORIGINS=*
JWT_SECRET=sua-chave-secreta-super-segura-aqui-2024
ADMIN_PASSWORD=102030ab
EOF

# 6. Configurar Frontend
cd /var/www/iaze/frontend
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://151.243.218.223
EOF

yarn install
yarn build

# 7. Configurar Nginx
cat > /etc/nginx/sites-available/iaze << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name 151.243.218.223 suporte.help;
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
    }
}
EOF

ln -sf /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/iaze
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# 8. Configurar Supervisor
cat > /etc/supervisor/conf.d/iaze-backend.conf << 'EOF'
[program:iaze-backend]
command=/var/www/iaze/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1
directory=/var/www/iaze/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/iaze-backend.err.log
stdout_logfile=/var/log/iaze-backend.out.log
user=root
environment=PYTHONUNBUFFERED=1
EOF

supervisorctl reread
supervisorctl update
supervisorctl restart iaze-backend

# 9. Iniciar MongoDB
systemctl start mongod
systemctl enable mongod

# 10. Verificar
supervisorctl status
curl http://localhost:8001/api/health
```

## ✅ Verificação Final

Após o deploy, teste:

```bash
# No VPS:
curl http://localhost:8001/api/health
curl http://localhost/

# Do seu navegador:
http://151.243.218.223/admin/login
```

## 🔍 Troubleshooting

### Backend não inicia:
```bash
# Ver logs
tail -f /var/log/iaze-backend.err.log

# Verificar se MongoDB está rodando
systemctl status mongod

# Reiniciar backend
supervisorctl restart iaze-backend
```

### Nginx 502:
```bash
# Verificar se backend responde
curl http://localhost:8001/api/health

# Ver logs do Nginx
tail -f /var/log/nginx/error.log

# Testar configuração
nginx -t
```

### Frontend não carrega:
```bash
# Verificar build
ls -la /var/www/iaze/frontend/build/

# Rebuild se necessário
cd /var/www/iaze/frontend
yarn build
```

## 📞 Credenciais

- **Admin:** admin@admin.com / 102030@ab
- **Atendentes:** biancaatt, jessicaatt, andressaatt, leticiaatt / ab181818ab
- **Revendedor:** fabioro@example.com / 102030a

## 🎯 URLs de Acesso

- **Admin:** http://151.243.218.223/admin/login
- **Atendente:** http://151.243.218.223/atendente/login
- **Cliente:** http://151.243.218.223/
- **API Health:** http://151.243.218.223/api/health
