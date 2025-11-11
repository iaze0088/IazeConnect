#!/usr/bin/env python3
"""
Debug script para verificar configuração do external storage
"""

import os
import sys
sys.path.append('/app/backend')

# Load .env file first
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('/app/backend/.env'))

from external_storage_service import external_storage

def main():
    print("🔍 DEBUG: External Storage Configuration")
    print("=" * 50)
    
    print(f"USE_EXTERNAL_STORAGE: {os.environ.get('USE_EXTERNAL_STORAGE')}")
    print(f"EXTERNAL_STORAGE_HOST: {os.environ.get('EXTERNAL_STORAGE_HOST')}")
    print(f"EXTERNAL_STORAGE_PORT: {os.environ.get('EXTERNAL_STORAGE_PORT')}")
    
    print("\n🔍 External Storage Service Instance:")
    print(f"use_external: {external_storage.use_external}")
    print(f"external_host: {external_storage.external_host}")
    print(f"external_port: {external_storage.external_port}")
    print(f"upload_endpoint: {external_storage.upload_endpoint}")
    print(f"files_base_url: {external_storage.files_base_url}")
    print(f"local_uploads_dir: {external_storage.local_uploads_dir}")

if __name__ == "__main__":
    main()