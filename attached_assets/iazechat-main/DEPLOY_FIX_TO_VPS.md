# 🚀 Como Aplicar a Correção no VPS

Você tem 2 opções:

## OPÇÃO 1: Script Automático (Recomendado)

1. Copie o arquivo `FIX_WHATSAPP_VPS.sh` para o VPS:
```bash
scp FIX_WHATSAPP_VPS.sh root@151.243.218.223:/root/
```

2. Conecte no VPS e execute:
```bash
ssh root@151.243.218.223
chmod +x /root/FIX_WHATSAPP_VPS.sh
bash /root/FIX_WHATSAPP_VPS.sh
```

## OPÇÃO 2: Correção Manual

Siga o guia em `MANUAL_FIX_WHATSAPP_VPS.md`

---

## ⚡ Correção Rápida Via SSH (Uma linha)

Execute este comando no VPS:

```bash
ssh root@151.243.218.223 "cd /var/www/iaze/backend && python3 << 'PYTHON_EOF'
import re

# Backup
import shutil
shutil.copy('whatsapp_routes.py', 'whatsapp_routes.py.backup')

# Ler arquivo
with open('whatsapp_routes.py', 'r') as f:
    content = f.read()

# Remover get_current_user do import
content = re.sub(r'from server import ([^\\n]*?)get_current_user([^\\n]*)', r'from server import \\1\\2', content)

# Adicionar nova função após router
router_line = 'router = APIRouter(prefix=\"/api/whatsapp\", tags=[\"whatsapp\"])'
if router_line in content and 'async def get_current_user(authorization: Optional[str] = Header(None)):' not in content:
    new_func = '''

# Criar uma dependência que funciona sem import circular  
async def get_current_user(authorization: Optional[str] = Header(None)):
    \"\"\"Dependência de autenticação - importa dinamicamente para evitar circular import\"\"\"
    from server import verify_token
    if not authorization or not authorization.startswith(\"Bearer \"):
        raise HTTPException(status_code=401, detail=\"Not authenticated\")
    token = authorization.split(\" \")[1]
    return verify_token(token)
'''
    content = content.replace(router_line, router_line + new_func)

# Garantir que Optional está importado
if 'from typing import' in content and 'Optional' not in content:
    content = re.sub(r'from typing import (.*)', r'from typing import \\1, Optional', content)

# Salvar
with open('whatsapp_routes.py', 'w') as f:
    f.write(content)

print('✅ Arquivo corrigido!')
PYTHON_EOF
&& sudo supervisorctl restart backend && sleep 5 && curl -s http://localhost:8001/api/health"
```

---

## 📋 Checklist Final

- [ ] Arquivo whatsapp_routes.py corrigido no VPS
- [ ] Admin criado no banco (email: admin@admin.com)
- [ ] Backend reiniciado
- [ ] Teste de health OK
- [ ] Teste de login OK
- [ ] Teste no browser: https://suporte.help/admin

---

## 🆘 Suporte

Se encontrar problemas, me envie:
1. Output do comando: `tail -n 50 /var/log/supervisor/backend.err.log`
2. Screenshot do erro no browser
