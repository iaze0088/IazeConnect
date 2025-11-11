#!/bin/bash
# Script para configurar servidor Evolution como storage para IAZE

EVOLUTION_IP="198.96.94.106"
EVOLUTION_PORT="9000"
STORAGE_DIR="/var/www/iaze-storage"

echo "🚀 Configurando servidor Evolution como storage para IAZE"
echo "=========================================================="
echo ""
echo "IP: $EVOLUTION_IP"
echo "Diretório: $STORAGE_DIR"
echo ""

# Este script deve ser executado NO SERVIDOR EVOLUTION (198.96.94.106)
# Conecte via SSH: ssh root@198.96.94.106

cat << 'REMOTE_SCRIPT' > /tmp/setup_evolution_storage.sh
#!/bin/bash

# Instalar Nginx se não estiver instalado
if ! command -v nginx &> /dev/null; then
    echo "📦 Instalando Nginx..."
    apt-get update
    apt-get install -y nginx
fi

# Criar diretório de storage
echo "📁 Criando diretório de storage..."
mkdir -p /var/www/iaze-storage/{uploads,cache,temp}
chown -R www-data:www-data /var/www/iaze-storage
chmod -R 755 /var/www/iaze-storage

# Configurar Nginx para servir arquivos
echo "⚙️ Configurando Nginx..."
cat > /etc/nginx/sites-available/iaze-storage << 'EOF'
server {
    listen 9000;
    server_name _;
    
    # Diretório raiz
    root /var/www/iaze-storage;
    
    # Logs
    access_log /var/log/nginx/iaze-storage-access.log;
    error_log /var/log/nginx/iaze-storage-error.log;
    
    # Servir arquivos estáticos
    location /uploads/ {
        alias /var/www/iaze-storage/uploads/;
        autoindex off;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS, DELETE';
        add_header Access-Control-Allow-Headers 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
        add_header Access-Control-Expose-Headers 'Content-Length,Content-Range';
        
        # Cache
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Endpoint para upload
    location /upload {
        client_max_body_size 100M;
        
        # Script PHP para processar upload
        fastcgi_pass unix:/var/run/php/php-fpm.sock;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME /var/www/iaze-storage/upload.php;
    }
    
    # Health check
    location /health {
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Criar script PHP para upload
echo "📝 Criando script de upload..."
cat > /var/www/iaze-storage/upload.php << 'PHPEOF'
<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

if (!isset($_FILES['file'])) {
    http_response_code(400);
    echo json_encode(['error' => 'No file uploaded']);
    exit;
}

$file = $_FILES['file'];
$uploadDir = '/var/www/iaze-storage/uploads/';

// Gerar nome único
$extension = pathinfo($file['name'], PATHINFO_EXTENSION);
$filename = uniqid() . '_' . time() . '.' . $extension;
$destination = $uploadDir . $filename;

// Validar tamanho (max 100MB)
if ($file['size'] > 100 * 1024 * 1024) {
    http_response_code(413);
    echo json_encode(['error' => 'File too large']);
    exit;
}

// Mover arquivo
if (move_uploaded_file($file['tmp_name'], $destination)) {
    chmod($destination, 0644);
    
    $url = 'http://' . $_SERVER['HTTP_HOST'] . '/uploads/' . $filename;
    
    echo json_encode([
        'success' => true,
        'filename' => $filename,
        'url' => $url,
        'size' => $file['size']
    ]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Upload failed']);
}
PHPEOF

# Instalar PHP-FPM se necessário
if ! command -v php-fpm &> /dev/null; then
    echo "📦 Instalando PHP-FPM..."
    apt-get install -y php-fpm php-cli
fi

# Ativar configuração
ln -sf /etc/nginx/sites-available/iaze-storage /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "✅ Configuração completa!"
echo ""
echo "📊 Status:"
df -h /var/www/iaze-storage
echo ""
echo "🌐 Endpoints:"
echo "  - Upload: http://$HOSTNAME:9000/upload"
echo "  - Files:  http://$HOSTNAME:9000/uploads/{filename}"
echo "  - Health: http://$HOSTNAME:9000/health"
echo ""
echo "🔥 Para testar:"
echo "curl http://localhost:9000/health"

REMOTE_SCRIPT

echo "📋 Script criado: /tmp/setup_evolution_storage.sh"
echo ""
echo "🔧 PRÓXIMOS PASSOS:"
echo ""
echo "1. Conecte ao servidor Evolution:"
echo "   ssh root@198.96.94.106"
echo ""
echo "2. Execute o script de configuração:"
echo "   bash < /tmp/setup_evolution_storage.sh"
echo ""
echo "3. Teste o endpoint:"
echo "   curl http://198.96.94.106:9000/health"
echo ""
echo "4. Me avise quando estiver pronto para configurar o backend IAZE!"
