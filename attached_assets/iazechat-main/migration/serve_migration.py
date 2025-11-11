#!/usr/bin/env python3
"""
Servidor HTTP simples para download do pacote de migração
"""
import http.server
import socketserver
import os

PORT = 9000
DIRECTORY = "/app/migration"
FILE_NAME = "iaze_migration_package.tar.gz"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Content-Disposition', f'attachment; filename="{FILE_NAME}"')
        super().end_headers()

os.chdir(DIRECTORY)
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"✅ Servidor rodando na porta {PORT}")
    print(f"📦 Arquivo disponível em: http://localhost:{PORT}/{FILE_NAME}")
    print(f"⏱️  Este servidor ficará ativo por 10 minutos")
    httpd.serve_forever()
