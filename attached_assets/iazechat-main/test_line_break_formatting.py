"""
Teste simples para validar formatação de quebras de linha após perguntas
"""
import re

def format_questions_with_line_breaks(text: str) -> str:
    """
    Adiciona quebra de linha dupla após cada pergunta (frase terminando com "?")
    para melhorar legibilidade da conversa.
    """
    # Regex para detectar "?" seguido de espaço e texto (não quebra de linha)
    # Adiciona \n\n após cada "?" que não tem \n logo após
    formatted = re.sub(
        r'\?(\s+)([^\n])',  # ? seguido de espaço(s) e caractere que não é \n
        r'?\n\n\2',  # Substitui por ? + dupla quebra + o caractere
        text
    )
    
    return formatted

# Testes
print("=" * 60)
print("TESTE 1: Exemplo do usuário")
print("=" * 60)
input1 = "pra gerar um teste gratis, primeiro me informa qual aparelho deseja usar? se for smartv ou tv box me avisa."
output1 = format_questions_with_line_breaks(input1)
print(f"INPUT:\n{input1}\n")
print(f"OUTPUT:\n{output1}\n")

print("=" * 60)
print("TESTE 2: Múltiplas perguntas")
print("=" * 60)
input2 = "Olá! Como posso ajudar? Você tem alguma dúvida? Me avise se precisar de algo."
output2 = format_questions_with_line_breaks(input2)
print(f"INPUT:\n{input2}\n")
print(f"OUTPUT:\n{output2}\n")

print("=" * 60)
print("TESTE 3: Pergunta no final")
print("=" * 60)
input3 = "Para continuar, preciso que você me informe: qual é o seu nome?"
output3 = format_questions_with_line_breaks(input3)
print(f"INPUT:\n{input3}\n")
print(f"OUTPUT:\n{output3}\n")

print("=" * 60)
print("TESTE 4: Sem perguntas")
print("=" * 60)
input4 = "Suas credenciais foram encontradas. Usuário: user123. Senha: pass456."
output4 = format_questions_with_line_breaks(input4)
print(f"INPUT:\n{input4}\n")
print(f"OUTPUT:\n{output4}\n")

print("=" * 60)
print("TESTE 5: Pergunta com quebra de linha já existente (não deve duplicar)")
print("=" * 60)
input5 = "Qual aparelho você usa?\n\nMe avise para continuar."
output5 = format_questions_with_line_breaks(input5)
print(f"INPUT:\n{repr(input5)}\n")
print(f"OUTPUT:\n{repr(output5)}\n")
