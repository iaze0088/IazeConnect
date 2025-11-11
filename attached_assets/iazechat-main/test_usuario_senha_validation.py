"""
Teste de validação de formato de usuário/senha
"""
import re

def validate_user_password_format(text: str) -> bool:
    """
    Valida se texto está no formato permitido de usuário/senha
    Aceita variações de maiúscula/minúscula, com ou sem acentos, e com texto antes/depois
    
    Exemplos válidos:
    - usuario: xxx senha: xxx
    - Usuário: xxx Senha: xxx
    - esse aqui é seu usuario e senha segue\nUsuario: xxx\nSenha: xxx
    """
    # Padrão flexível que aceita:
    # - usuario/usuário em qualquer capitalização
    # - senha/password em qualquer capitalização
    # - texto antes e depois
    # - quebras de linha
    pattern = r'(usuario|usuário|user)\s*:\s*.+\s+(senha|password)\s*:\s*.+'
    
    # Buscar em qualquer lugar do texto (não apenas no início)
    return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))


# Testes
print("=" * 80)
print("TESTE DE VALIDAÇÃO: Formato Usuario/Senha")
print("=" * 80)

test_cases = [
    # Casos válidos
    ("usuario: teste123 senha: abc123", True, "Formato simples minúsculo"),
    ("Usuario: teste123 Senha: abc123", True, "Formato capitalizado"),
    ("Usuário: teste123 Senha: abc123", True, "Com acento"),
    ("USUARIO: teste123 SENHA: abc123", True, "Tudo maiúsculo"),
    ("USUÁRIO: teste123 SENHA: abc123", True, "Tudo maiúsculo com acento"),
    
    # Com texto antes
    ("esse aqui é seu usuario e senha segue usuario: teste123 senha: abc123", True, "Com texto antes"),
    ("Olá! Segue suas credenciais: Usuario: teste123 Senha: abc123", True, "Com saudação antes"),
    
    # Com texto depois
    ("usuario: teste123 senha: abc123 espero que funcione!", True, "Com texto depois"),
    ("Usuario: teste123 Senha: abc123\nQualquer dúvida entre em contato", True, "Com texto depois e quebra de linha"),
    
    # Com quebras de linha
    ("Usuario: teste123\nSenha: abc123", True, "Com quebra de linha entre campos"),
    ("esse aqui é seu usuario e senha segue\nUsuario: teste123\nSenha: abc123", True, "Com quebras de linha múltiplas"),
    ("Suas credenciais:\n\nUsuario: teste123\n\nSenha: abc123\n\nObrigado!", True, "Com múltiplas quebras e texto"),
    
    # Variações com espaços
    ("usuario:teste123 senha:abc123", True, "Sem espaços após dois pontos"),
    ("usuario : teste123 senha : abc123", True, "Com espaços extras"),
    
    # Usando "user" e "password"
    ("user: teste123 password: abc123", True, "Inglês: user/password"),
    ("User: teste123 Password: abc123", True, "Inglês capitalizado"),
    
    # Casos inválidos
    ("apenas texto sem credenciais", False, "Sem credenciais"),
    ("usuario: teste123", False, "Só usuário"),
    ("senha: abc123", False, "Só senha"),
    ("teste abc 123", False, "Texto aleatório"),
]

print("\n🧪 EXECUTANDO TESTES:\n")

passed = 0
failed = 0

for text, expected, description in test_cases:
    result = validate_user_password_format(text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} - {description}")
    if result != expected:
        print(f"       Texto: {text[:60]}...")
        print(f"       Esperado: {expected}, Obtido: {result}")
    print()

print("=" * 80)
print(f"RESULTADO: {passed} passaram, {failed} falharam de {len(test_cases)} testes")
print("=" * 80)

if failed == 0:
    print("\n🎉 TODOS OS TESTES PASSARAM!")
else:
    print(f"\n⚠️ {failed} TESTES FALHARAM")
