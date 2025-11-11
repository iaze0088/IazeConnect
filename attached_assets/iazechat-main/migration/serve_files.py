#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 9001
DIRECTORY = "/app/migration"

os.chdir(DIRECTORY)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

Handler = MyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅ Servidor HTTP rodando na porta {PORT}")
    print(f"📦 Arquivos disponíveis em: http://198.96.94.106:{PORT}/")
    print("\nArquivos disponíveis:")
    print("  - backend_code.tar.gz (130KB)")
    print("  - frontend_src.tar.gz (1.1MB)")
    print("  - mongodb_backup.tar.gz (980KB)")
    httpd.serve_forever()
