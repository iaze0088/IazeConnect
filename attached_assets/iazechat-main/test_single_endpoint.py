#!/usr/bin/env python3
import requests
import json

# Get admin token
response = requests.post("https://suporte.help/api/auth/admin/login", 
                        json={"password": "102030@ab"})
token = response.json()['token']

# Test reseller creation
headers = {"Authorization": f"Bearer {token}"}
data = {"name": "Test Reseller", "email": "test@example.com", "password": "123456"}

print("Testing reseller creation...")
response = requests.post("https://suporte.help/api/resellers", 
                        json=data, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")