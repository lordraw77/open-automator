#!/usr/bin/env python3
"""
Genera README.md dalla documentazione dei moduli oa-*.py
Con elenco funzioni in testa ad ogni modulo
"""

import os
import re
import ast
from pathlib import Path

def extract_module_docs(file_path):
    """Estrae docstring da file Python"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except:
        return None

    module_name = Path(file_path).stem
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Verifica se ha decorator @oacommon.trace
            has_trace = any(
                (isinstance(d, ast.Name) and 'trace' in d.id) or
                (isinstance(d, ast.Attribute) and d.attr == 'trace')
                for d in node.decorator_list
            )

            if has_trace and ast.get_docstring(node):
                docstring = ast.get_docstring(node)
                functions.append({
                    'name': node.name,
                    'docstring': docstring
                })

    return {
        'module': module_name,
        'functions': functions
    }

def parse_docstring(docstring):
    """Converte docstring in formato markdown"""
    lines = docstring.strip().split('\n')

    # Estrai descrizione (prima riga)
    description = []
    args_section = []
    returns_section = []

    current_section = 'description'

    for line in lines:
        line = line.strip()
        if line.startswith('Args:'):
            current_section = 'args'
        elif line.startswith('Returns:'):
            current_section = 'returns'
        elif current_section == 'description' and line:
            description.append(line)
        elif current_section == 'args' and line and not line.startswith('Args:'):
            args_section.append(line)
        elif current_section == 'returns' and line and not line.startswith('Returns:'):
            returns_section.append(line)

    return {
        'description': ' '.join(description),
        'args': args_section,
        'returns': returns_section
    }

def generate_markdown(modules_data):
    """Genera markdown da dati estratti"""
    md = []

    # Header
    md.append("# Open-Automator - Documentazione Moduli\n")
    md.append("Documentazione automatica dei moduli e funzioni disponibili.\n")
    md.append("---\n")

    # Indice Moduli
    md.append("## 📑 Indice Moduli\n")
    for module_data in modules_data:
        module_name = module_data['module']
        func_count = len(module_data['functions'])
        md.append(f"- [{module_name}](#{module_name.replace('-', '')}) - {func_count} funzioni")
    md.append("\n---\n")

    # Moduli
    for module_data in modules_data:
        module_name = module_data['module']
        functions = module_data['functions']

        if not functions:
            continue

        # Titolo modulo
        md.append(f"## {module_name}\n")

        # ✨ ELENCO FUNZIONI DEL MODULO
        md.append(f"### 📋 Funzioni disponibili ({len(functions)})\n")
        for func in functions:
            func_name = func['name']
            # Estrai prima riga della descrizione
            first_line = func['docstring'].split('\n')[0].strip()
            md.append(f"- [`{func_name}()`](#{module_name.replace('-', '')}-{func_name}) - {first_line}")
        md.append("\n---\n")

        # Documentazione dettagliata
        for func in functions:
            func_name = func['name']
            docstring = func['docstring']
            parsed = parse_docstring(docstring)

            # Funzione con anchor
            md.append(f"### `{func_name}()` {{#{module_name.replace('-', '')}-{func_name}}}\n")
            md.append(f"{parsed['description']}\n")

            # Parametri
            if parsed['args']:
                md.append("**Parametri:**\n")
                for arg in parsed['args']:
                    # Rimuovi trattini iniziali e formatta
                    arg_clean = arg.lstrip('- ').strip()
                    if ':' in arg_clean:
                        param_name, param_desc = arg_clean.split(':', 1)
                        md.append(f"- `{param_name.strip()}`: {param_desc.strip()}")
                    else:
                        md.append(f"- {arg_clean}")
                md.append("")

            # Returns
            if parsed['returns']:
                md.append("**Ritorna:**\n")
                for ret in parsed['returns']:
                    ret_clean = ret.strip()
                    md.append(f"{ret_clean}\n")

            md.append("---\n")

    # Footer
    md.append("\n---\n")
    md.append("*Documentazione generata automaticamente da `generate_readme.py`*\n")

    return '\n'.join(md)

def main():
    """Genera README.md dai moduli"""
    # Trova tutti i file oa-*.py
    module_files = sorted(Path('./modules').glob('oa-*.py'))

    if not module_files:
        print("❌ Nessun modulo oa-*.py trovato")
        return

    print(f"📦 Trovati {len(module_files)} moduli")

    modules_data = []
    for file_path in module_files:
        print(f"   Processando {file_path.name}...")
        data = extract_module_docs(file_path)
        if data and data['functions']:
            modules_data.append(data)
            print(f"      ✓ {len(data['functions'])} funzioni trovate")

    # Genera markdown
    markdown = generate_markdown(modules_data)

    # Salva README.md
    output_file = 'README_MODULES.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ Generato {output_file}")
    print(f"   {len(modules_data)} moduli documentati")

    total_functions = sum(len(m['functions']) for m in modules_data)
    print(f"   {total_functions} funzioni totali")

    print(f"\n📖 Apri con: cat {output_file}")

if __name__ == '__main__':
    main()
