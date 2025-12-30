#!/usr/bin/env python3

"""
Genera README.md e README.html dalla documentazione dei moduli oa-*.py
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

    md.append("# Open-Automator - Documentazione Moduli\n")
    md.append("Documentazione automatica dei moduli e funzioni disponibili.\n")
    md.append("---\n")

    md.append("## 📑 Indice Moduli\n")
    for module_data in modules_data:
        module_name = module_data['module']
        func_count = len(module_data['functions'])
        md.append(f"- [{module_name}](#{module_name.replace('-', '')}) - {func_count} funzioni")
    md.append("\n---\n")

    for module_data in modules_data:
        module_name = module_data['module']
        functions = module_data['functions']

        if not functions:
            continue

        md.append(f"## {module_name}\n")
        md.append(f"### 📋 Funzioni disponibili ({len(functions)})\n")

        for func in functions:
            func_name = func['name']
            first_line = func['docstring'].split('\n')[0].strip()
            md.append(f"- [`{func_name}()`](#{module_name.replace('-', '')}-{func_name}) - {first_line}")

        md.append("\n---\n")

        for func in functions:
            func_name = func['name']
            docstring = func['docstring']
            parsed = parse_docstring(docstring)

            md.append(f"### `{func_name}()` {{#{module_name.replace('-', '')}-{func_name}}}\n")
            md.append(f"{parsed['description']}\n")

            if parsed['args']:
                md.append("**Parametri:**\n")
                for arg in parsed['args']:
                    arg_clean = arg.lstrip('- ').strip()
                    if ':' in arg_clean:
                        param_name, param_desc = arg_clean.split(':', 1)
                        md.append(f"- `{param_name.strip()}`: {param_desc.strip()}")
                    else:
                        md.append(f"- {arg_clean}")
                md.append("")

            if parsed['returns']:
                md.append("**Ritorna:**\n")
                for ret in parsed['returns']:
                    ret_clean = ret.strip()
                    md.append(f"{ret_clean}\n")

            md.append("---\n")

    md.append("\n---\n")
    md.append("*Documentazione generata automaticamente da `generate_readme.py`*\n")

    return '\n'.join(md)

def generate_html(modules_data):
    """Genera HTML da dati estratti"""
    html = []

    html.append("""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open-Automator - Documentazione Moduli</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding: 10px;
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
        }

        h3 {
            color: #555;
            margin-top: 25px;
            margin-bottom: 15px;
        }

        .subtitle {
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .module-index {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }

        .module-index h2 {
            margin-top: 0;
        }

        .module-index ul {
            list-style: none;
            padding-left: 0;
        }

        .module-index li {
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }

        .module-index li:last-child {
            border-bottom: none;
        }

        .module-index a {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }

        .module-index a:hover {
            text-decoration: underline;
        }

        .function-list {
            background-color: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }

        .function-list ul {
            list-style: none;
            padding-left: 0;
        }

        .function-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .function-list li:last-child {
            border-bottom: none;
        }

        .function-detail {
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }

        .function-name {
            font-family: 'Courier New', Courier, monospace;
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 10px 15px;
            border-radius: 5px;
            display: inline-block;
            margin-bottom: 15px;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            color: #e74c3c;
        }

        .params, .returns {
            margin: 15px 0;
        }

        .params strong, .returns strong {
            color: #2980b9;
            display: block;
            margin-bottom: 8px;
        }

        .params ul, .returns ul {
            margin-left: 20px;
        }

        .params li {
            margin: 5px 0;
        }

        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }

        .footer {
            text-align: center;
            color: #95a5a6;
            font-style: italic;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
        }

        a {
            color: #3498db;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Open-Automator - Documentazione Moduli</h1>
        <p class="subtitle">Documentazione automatica dei moduli e funzioni disponibili.</p>
""")

    html.append('        <div class="module-index">')
    html.append('            <h2>📑 Indice Moduli</h2>')
    html.append('            <ul>')

    for module_data in modules_data:
        module_name = module_data['module']
        func_count = len(module_data['functions'])
        anchor = module_name.replace('-', '')
        html.append(f'                <li><a href="#{anchor}">{module_name}</a> - {func_count} funzioni</li>')

    html.append('            </ul>')
    html.append('        </div>')
    html.append('        <hr>')

    for module_data in modules_data:
        module_name = module_data['module']
        functions = module_data['functions']

        if not functions:
            continue

        anchor = module_name.replace('-', '')
        html.append(f'        <h2 id="{anchor}">{module_name}</h2>')
        html.append(f'        <div class="function-list">')
        html.append(f'            <h3>📋 Funzioni disponibili ({len(functions)})</h3>')
        html.append('            <ul>')

        for func in functions:
            func_name = func['name']
            first_line = func['docstring'].split('\n')[0].strip()
            func_anchor = f"{anchor}-{func_name}"
            html.append(f'                <li><a href="#{func_anchor}"><code>{func_name}()</code></a> - {first_line}</li>')

        html.append('            </ul>')
        html.append('        </div>')

        for func in functions:
            func_name = func['name']
            docstring = func['docstring']
            parsed = parse_docstring(docstring)
            func_anchor = f"{anchor}-{func_name}"

            html.append(f'        <div class="function-detail" id="{func_anchor}">')
            html.append(f'            <div class="function-name">{func_name}()</div>')
            html.append(f'            <p>{parsed["description"]}</p>')

            if parsed['args']:
                html.append('            <div class="params">')
                html.append('                <strong>Parametri:</strong>')
                html.append('                <ul>')
                for arg in parsed['args']:
                    arg_clean = arg.lstrip('- ').strip()
                    if ':' in arg_clean:
                        param_name, param_desc = arg_clean.split(':', 1)
                        html.append(f'                    <li><code>{param_name.strip()}</code>: {param_desc.strip()}</li>')
                    else:
                        html.append(f'                    <li>{arg_clean}</li>')
                html.append('                </ul>')
                html.append('            </div>')

            if parsed['returns']:
                html.append('            <div class="returns">')
                html.append('                <strong>Ritorna:</strong>')
                for ret in parsed['returns']:
                    ret_clean = ret.strip()
                    html.append(f'                <p>{ret_clean}</p>')
                html.append('            </div>')

            html.append('        </div>')

        html.append('        <hr>')

    html.append('        <div class="footer">')
    html.append('            <p>Documentazione generata automaticamente da <code>generate_readme.py</code></p>')
    html.append('        </div>')
    html.append('    </div>')
    html.append('</body>')
    html.append('</html>')

    return '\n'.join(html)

def main():
    """Genera README.md e README.html dai moduli"""
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
            print(f"   ✓ {len(data['functions'])} funzioni trovate")

    markdown = generate_markdown(modules_data)
    html_content = generate_html(modules_data)

    output_md = 'README_MODULES.md'
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"\n✅ Generato {output_md}")

    output_html = 'README_MODULES.html'
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Generato {output_html}")

    print(f"   {len(modules_data)} moduli documentati")
    total_functions = sum(len(m['functions']) for m in modules_data)
    print(f"   {total_functions} funzioni totali")

    print(f"\n📖 Apri Markdown con: cat {output_md}")
    print(f"🌐 Apri HTML nel browser: {output_html}")

if __name__ == '__main__':
    main()
