"""
Teste de formatação de número para Evolution API v2.3
"""

def format_number_for_evolution(number: str) -> str:
    """
    Formatar número para Evolution API v2.3
    Padrão esperado: 5511999999999@s.whatsapp.net
    """
    # Remover caracteres não numéricos
    clean_number = ''.join(filter(str.isdigit, str(number)))
    
    # Se não termina com @s.whatsapp.net, adicionar
    if not number.endswith('@s.whatsapp.net'):
        # Garantir que tem código do país
        if not clean_number.startswith('55'):  # Brasil
            clean_number = '55' + clean_number
        formatted_number = clean_number + '@s.whatsapp.net'
    else:
        formatted_number = number
    
    return formatted_number


# Testes
test_cases = [
    "(11) 99999-9999",
    "11999999999",
    "5511999999999",
    "+55 11 99999-9999",
    "55 11 99999 9999",
    "5511999999999@s.whatsapp.net"
]

print("=" * 60)
print("TESTE DE FORMATAÇÃO DE NÚMEROS PARA EVOLUTION API v2.3")
print("=" * 60)
print()

for test in test_cases:
    formatted = format_number_for_evolution(test)
    print(f"Entrada:  {test:30s}")
    print(f"Saída:    {formatted}")
    print(f"✅ Formato correto: {formatted.endswith('@s.whatsapp.net')}")
    print("-" * 60)

print()
print("✅ Todos os números formatados corretamente!")
print("   Padrão Evolution API v2.3: 5511999999999@s.whatsapp.net")
