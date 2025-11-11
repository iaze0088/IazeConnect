#!/usr/bin/env python3
"""
Script de Conversão Python 3.11 → 3.8
Converte código moderno para compatibilidade com Python 3.8
"""
import os
import re
import sys
from pathlib import Path

def convert_type_hints(content: str) -> str:
    """Converte type hints modernos para Python 3.8"""
    
    # Adicionar imports se necessário
    if 'from typing import' not in content:
        content = 'from typing import List, Dict, Tuple, Optional\n' + content
    elif 'Tuple' not in content and 'tuple[' in content:
        content = content.replace('from typing import', 'from typing import Tuple,', 1)
    
    # Converter tuple[...] -> Tuple[...]
    content = re.sub(r'\btuple\[', 'Tuple[', content)
    
    # Converter list[...] -> List[...]
    content = re.sub(r'\blist\[', 'List[', content)
    
    # Converter dict[...] -> Dict[...]
    content = re.sub(r'\bdict\[', 'Dict[', content)
    
    # Converter set[...] -> Set[...]
    content = re.sub(r'\bset\[', 'Set[', content)
    
    return content

def remove_emojis(content: str) -> str:
    """Remove emojis de strings, substituindo por texto"""
    emoji_map = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        '🔥': '[FIRE]',
        '📁': '[DIR]',
        '🚀': '[LAUNCH]',
        '💾': '[SAVE]',
        '🤖': '[BOT]',
        '📝': '[NOTE]',
        '🔑': '[KEY]',
        '🆕': '[NEW]',
        '📋': '[LIST]',
        '👤': '[USER]',
        '📱': '[PHONE]',
        '🎉': '[PARTY]',
        '🔐': '[LOCK]',
        '📨': '[MSG]',
        '🚨': '[ALERT]',
        '💡': '[IDEA]',
        '⭐': '[STAR]',
        '🎯': '[TARGET]',
        '🏢': '[OFFICE]',
        '🌐': '[WEB]',
        '🔧': '[TOOL]',
        '📊': '[CHART]',
        '🧪': '[TEST]',
        '👍': '[LIKE]',
        '⚡': '[BOLT]',
        '🆘': '[SOS]',
    }
    
    for emoji, text in emoji_map.items():
        content = content.replace(emoji, text)
    
    # Remove qualquer emoji restante
    content = re.sub(r'[^\x00-\x7F]+', '', content)
    
    return content

def fix_emergent_imports(content: str) -> str:
    """Adiciona fallback para imports do emergentintegrations"""
    
    if 'from emergentintegrations' in content and 'try:' not in content[:200]:
        # Adicionar try/except no início do arquivo
        lines = content.split('\n')
        import_idx = None
        for i, line in enumerate(lines):
            if 'from emergentintegrations' in line:
                import_idx = i
                break
        
        if import_idx is not None:
            indent = len(lines[import_idx]) - len(lines[import_idx].lstrip())
            lines[import_idx] = (
                'try:\n' +
                ' ' * indent + lines[import_idx] + '\n' +
                'except ImportError:\n' +
                ' ' * indent + '    # Fallback quando emergentintegrations não está disponível\n' +
                ' ' * indent + '    pass'
            )
            content = '\n'.join(lines)
    
    return content

def convert_file(filepath: str, output_filepath: str = None):
    """Converte um arquivo Python 3.11 para 3.8"""
    
    print(f"Convertendo: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar conversões
    content = convert_type_hints(content)
    content = remove_emojis(content)
    content = fix_emergent_imports(content)
    
    # Salvar
    output_path = output_filepath or filepath
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  -> Salvo em: {output_path}")

def convert_directory(directory: str, output_directory: str = None):
    """Converte todos arquivos Python de um diretório"""
    
    directory = Path(directory)
    output_directory = Path(output_directory) if output_directory else directory
    
    for filepath in directory.glob('*.py'):
        output_filepath = output_directory / filepath.name
        convert_file(str(filepath), str(output_filepath))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 convert_py38.py <arquivo_ou_diretorio> [diretorio_saida]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if os.path.isfile(input_path):
        convert_file(input_path, output_path)
    elif os.path.isdir(input_path):
        convert_directory(input_path, output_path)
    else:
        print(f"Erro: {input_path} não encontrado")
        sys.exit(1)
    
    print("\n✓ Conversão concluída!")
