# 🚀 Guia de Deployment - Sistema IAZE

## 📋 Pré-requisitos no Servidor

### 1. Software Necessário
```bash
# Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# PM2 (Process Manager)
sudo npm install -g pm2

# Nginx (Proxy Reverso)
sudo apt-get install -y nginx

# PostgreSQL (Banco de Dados - Opcional)
sudo apt-get install -y postgresql postgresql-contrib
```

### 2. Preparar Diretórios
```bash
sudo mkdir -p /var/www/iaze
sudo chown -R $USER:$USER /var/www/iaze
```

## 📦 Upload do Projeto

### Opção 1: Via SCP (do seu computador)
```bash
# Baixe o projeto do Replit primeiro, depois:
scp -r ./iaze-project root@46.62.253.32:/var/www/iaze/
```

### Opção 2: Via Git (Recomendado)
```bash
# No servidor
cd /var/www/iaze
git clone <URL_DO_SEU_REPOSITORIO> .
```

### Opção 3: Via SFTP
Use um cliente SFTP como FileZilla ou WinSCP para transferir os arquivos.

## ⚙️ Configuração no Servidor

### 1. Instalar Dependências
```bash
cd /var/www/iaze
npm install --production
```

### 2. Criar Arquivo de Ambiente
```bash
cat > .env << 'EOF'
NODE_ENV=production
PORT=5000
SESSION_SECRET=seu_secret_super_seguro_aqui

# WPP Connect Configuration
WPPCONNECT_API_URL=http://wppconnect.suporte.help:21465
WPPCONNECT_SECRET_KEY=seu_secret_key_aqui

# Database (se usar PostgreSQL)
DATABASE_URL=postgresql://usuario:senha@localhost:5432/iaze_db
EOF
```

### 3. Configurar PM2 (Process Manager)
```bash
# Criar arquivo ecosystem
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

# Iniciar aplicação
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 4. Configurar Nginx (Proxy Reverso)
```bash
sudo cat > /etc/nginx/sites-available/iaze << 'EOF'
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Ativar site
sudo ln -s /etc/nginx/sites-available/iaze /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Configurar Firewall
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 6. SSL com Let's Encrypt (HTTPS)
```bash
# Instalar Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo certbot renew --dry-run
```

## 🗄️ Configurar Banco de Dados PostgreSQL (Opcional)

```bash
# Criar usuário e banco
sudo -u postgres psql

postgres=# CREATE DATABASE iaze_db;
postgres=# CREATE USER iaze_user WITH ENCRYPTED PASSWORD 'senha_segura';
postgres=# GRANT ALL PRIVILEGES ON DATABASE iaze_db TO iaze_user;
postgres=# \q

# Importar dados (se tiver backup)
psql -U iaze_user -d iaze_db < backup.sql
```

## 🔐 Segurança Adicional

### 1. Trocar Senhas Padrão
```bash
# Atualizar senha do admin no código
# Gerar novo hash:
node -e "const bcrypt = require('bcrypt'); bcrypt.hash('sua_nova_senha', 12).then(h => console.log(h));"
```

### 2. Configurar Fail2Ban
```bash
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Desabilitar Login Root via SSH
```bash
sudo nano /etc/ssh/sshd_config
# Alterar: PermitRootLogin no
sudo systemctl restart sshd
```

## 📊 Monitoramento

### Logs da Aplicação
```bash
# Ver logs em tempo real
pm2 logs iaze

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoramento do Sistema
```bash
# Status da aplicação
pm2 status

# Reiniciar aplicação
pm2 restart iaze

# Parar aplicação
pm2 stop iaze
```

## 🔄 Atualizações

### Deploy de Nova Versão
```bash
cd /var/www/iaze

# Pull das alterações
git pull origin main

# Instalar dependências
npm install --production

# Reiniciar aplicação
pm2 restart iaze
```

## 🆘 Troubleshooting

### Aplicação não inicia
```bash
# Verificar logs
pm2 logs iaze --lines 100

# Verificar porta
sudo netstat -tulpn | grep 5000

# Verificar permissões
ls -la /var/www/iaze
```

### Nginx retorna 502 Bad Gateway
```bash
# Verificar se app está rodando
pm2 status

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Testar configuração
sudo nginx -t
```

### Problemas de Memória
```bash
# Aumentar limite de memória no PM2
pm2 start ecosystem.config.js --max-memory-restart 2G

# Monitorar uso
pm2 monit
```

## 📝 Checklist de Deploy

- [ ] Node.js 20+ instalado
- [ ] Projeto copiado para /var/www/iaze
- [ ] Dependências instaladas (npm install)
- [ ] Arquivo .env configurado
- [ ] PM2 configurado e rodando
- [ ] Nginx configurado como proxy
- [ ] Firewall configurado
- [ ] SSL/HTTPS configurado (Certbot)
- [ ] Senhas padrão alteradas
- [ ] Backup configurado
- [ ] Monitoramento ativo

## 🎯 URLs de Acesso

Após o deploy:
- **Aplicação**: http://seu-dominio.com (ou https://)
- **Admin**: http://seu-dominio.com/admin
- **API**: http://seu-dominio.com/api

## 📞 Suporte

Para problemas durante o deployment, verifique:
1. Logs da aplicação (pm2 logs)
2. Logs do Nginx (sudo tail -f /var/log/nginx/error.log)
3. Status do servidor (pm2 status, sudo systemctl status nginx)
