#!/usr/bin/env python3
"""
md2html.py - Konvertiert Markdown-Dateien zu druckbaren HTML-Dokumenten

Zusätzlich:
- Extrahiert automatisch Lieferanten aus Tabellen
- Generiert "Bezugsquellen" Abschnitt automatisch
- Aktualisiert sowohl .md als auch .html Dateien

Verwendung:
    python md2html.py <datei.md>
    python md2html.py *.md                    # alle .md Dateien
    python md2html.py Aktuell/Planung/         # alle .md in Ordner
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ===============================
# CSS-STIL
# ===============================
CSS = """* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #222; max-width: 1000px; margin: 0 auto; padding: 30px; font-size: 12px; }
h1 { font-size: 22px; border-bottom: 3px solid #0066cc; padding-bottom: 10px; margin-bottom: 20px; margin-top: 30px; }
h1:first-child { margin-top: 0; }
h2 { font-size: 16px; color: #0066cc; margin-top: 35px; margin-bottom: 12px; padding-bottom: 5px; border-bottom: 1px solid #ddd; }
h3 { font-size: 13px; color: #444; margin-top: 20px; margin-bottom: 8px; }
h4 { font-size: 12px; color: #333; margin-top: 15px; margin-bottom: 6px; }
p { margin: 8px 0; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #e8f0f8; font-weight: bold; color: #003366; }
tr:nth-child(even) td { background: #f8f8f8; }
tr:hover td { background: #f0f5ff; }
ul, ol { margin: 8px 0 8px 20px; }
li { margin: 3px 0; }
code { background: #f0f0f0; padding: 1px 4px; font-family: 'Consolas', monospace; font-size: 10px; border-radius: 2px; }
pre { background: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 10px; border: 1px solid #ddd; }
blockquote { border-left: 4px solid #0066cc; padding: 8px 15px; margin: 15px 0; background: #f8fafc; color: #444; font-style: italic; }
blockquote p { margin: 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 25px 0; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }
.summary-box { background: #e8f4fc; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #b8d4e8; }
.summary-box table { background: white; margin: 0; }
.total-row td { font-weight: bold; color: #003366; font-size: 13px; }
.priority-high { color: #cc0000; font-weight: bold; }
.priority-medium { color: #cc6600; }
.warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 15px; margin: 15px 0; }
.warning strong { color: #856404; }
.note { background: #e7f3ff; border-left: 4px solid #0066cc; padding: 8px 12px; margin: 10px 0; font-size: 11px; }
.footer { font-size: 10px; color: #888; margin-top: 40px; padding-top: 15px; border-top: 1px solid #ddd; }
.print-btn { background: #0066cc; color: white; border: none; padding: 10px 20px; font-size: 14px; cursor: pointer; border-radius: 4px; margin-bottom: 20px; }
.print-btn:hover { background: #0055aa; }
@media print { 
    body { padding: 0; font-size: 10px; }
    .print-btn { display: none; }
    h2 { page-break-before: auto; }
    table { page-break-inside: avoid; }
}"""

# ===============================
# KONVERTIERUNG FUNKTIONEN
# ===============================

def md_to_html(md_content, title=None):
    """Wandelt Markdown in HTML um"""
    
    # Titel aus erster Zeile
    lines = md_content.split('\n')
    if title is None and lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
    if title is None:
        title = "Dokument"
    
    html = md_content
    
    # --- Code Blöcke (müssen zuerst) ---
    def replace_code_block(m):
        lang = m.group(1) or ''
        code = m.group(2)
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    
    html = re.sub(r'```(\w*)\n(.+?)```', replace_code_block, html, flags=re.DOTALL)
    
    # --- Inline Code ---
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # --- Überschriften ---
    html = re.sub(r'^###### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # --- Fett, Kursiv, Markiert ---
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # --- Links [text](url) ---
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
    
    # --- Tabellen ---
    html = convert_tables(html)
    
    # --- Blockquotes ---
    html = re.sub(r'^> (.+)$', r'<blockquote><p>\1</p></blockquote>', html, flags=re.MULTILINE)
    
    # --- Horizontale Linien ---
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
    html = re.sub(r'^\*\*\*+$', r'<hr>', html, flags=re.MULTILINE)
    
    # --- Ungeordnete Listen ---
    def convert_list(match):
        items = match.group(0)
        items_html = re.sub(r'^[\*\-] (.+)$', r'<li>\1</li>', items, flags=re.MULTILINE)
        return f'<ul>{items_html}</ul>'
    html = re.sub(r'(?:^[\*\-] .+$\n)+', convert_list, html, flags=re.MULTILINE)
    
    # --- Geordnete Listen ---
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n)+', lambda m: '<ol>' + m.group(0) + '</ol>', html)
    
    # --- Absätze (leere Zeilen trennen) ---
    blocks = re.split(r'\n\n+', html)
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('<h') or block.startswith('<ul') or block.startswith('<ol') or block.startswith('<pre') or block.startswith('<blockquote') or block.startswith('<hr'):
            result.append(block)
        else:
            # Wrap in paragraph, handle line breaks
            block = block.replace('\n', '<br>')
            if not block.startswith('<p'):
                result.append(f'<p>{block}</p>')
            else:
                result.append(block)
    html = '\n\n'.join(result)
    
    return html, title

def extract_suppliers(md_content):
    """Extrahiert Lieferanten aus Überschriften und Tabellen im MD-Content"""
    suppliers = defaultdict(set)
    
    lines = md_content.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Pattern: "### Name (Marke) – lieferant.domain"
        if ' – ' in line and line.startswith('##'):
            parts = line.split(' – ', 1)
            if len(parts) == 2:
                vendor = parts[1].strip().rstrip(')')
                
                if 'reichelt' in vendor:
                    suppliers['reichelt.at'].add('Werkzeuge')
                elif 'conrad' in vendor:
                    suppliers['conrad.at'].add('Elektronik')
                elif 'hoffmann' in vendor or 'pferd' in vendor:
                    suppliers['hoffmann-group.com'].add('Werkzeuge')
                elif 'buerklin' in vendor:
                    suppliers['buerklin.com'].add('Elektronik-Werkzeuge')
                elif 'smadshop' in vendor:
                    suppliers['smadshop.md'].add('Maschinen, Werkzeuge')
                elif 'einhell' in vendor:
                    suppliers['einhell.com'].add('Akku-Werkzeuge')
                elif 'makita' in vendor:
                    suppliers['makita.md'].add('Elektrowerkzeuge')
                elif 'bosch' in vendor:
                    suppliers['Bosch'].add('Elektrowerkzeuge')
                elif 'ali' in vendor:
                    suppliers['AliExpress'].add('CNC-Fräsen')
        
        # Auch in Tabellenzellen suchen (Link-Spalte)
        if '|[' in line:
            if 'reichelt' in line_lower:
                suppliers['reichelt.at'].add('Werkzeuge')
            elif 'conrad' in line_lower:
                suppliers['conrad.at'].add('Elektronik')
            elif 'smadshop' in line_lower:
                suppliers['smadshop.md'].add('Maschinen')
            elif 'buerklin' in line_lower:
                suppliers['buerklin.com'].add('Elektronik')
            elif 'makita' in line_lower:
                suppliers['makita.md'].add('Elektrowerkzeuge')
    
    return suppliers

def generate_bezugsquellen(suppliers):
    """Generiert Bezugsquellen-Abschnitt als Markdown"""
    if not suppliers:
        return ""
    
    lines = ["> **Bezugsquellen:**\n"]
    for vendor, categories in sorted(suppliers.items()):
        cats = ', '.join(sorted(categories))
        lines.append(f"> - [{vendor}](https://{vendor}) – {cats}")
    lines.append("")
    
    return '\n'.join(lines)

def update_md_with_bezugsquellen(md_content, suppliers):
    """Ersetzt Bezugsquellen-Abschnitt oder fügt neuen hinzu"""
    if not suppliers:
        return md_content
    
    new_section = generate_bezugsquellen(suppliers)
    
    # Entferne bestehenden Bezugsquellen-Abschnitt (zwischen > **Bezugsquellen:** und dem nächsten --- oder Preis-Hinweis)
    lines = md_content.split('\n')
    result = []
    in_bezugsquellen = False
    
    for line in lines:
        if 'Bezugsquellen' in line and line.startswith('>'):
            in_bezugsquellen = True
            continue
        if in_bezugsquellen:
            if line.strip() == '' or line.startswith('---') or line.startswith('*Preise'):
                in_bezugsquellen = False
                result.append(line)
            else:
                continue
        else:
            result.append(line)
    
    md_content = '\n'.join(result)
    
    # Füge neuen Abschnitt vor dem letzten --- oder Preis-Hinweis ein
    lines = md_content.split('\n')
    insert_idx = len(lines)
    
    for i, line in enumerate(lines):
        if line.startswith('*Preise'):
            insert_idx = i
            break
    
    result = lines[:insert_idx]
    result.append('\n---\n')
    result.append(new_section)
    result.append('\n')
    result.extend(lines[insert_idx:])
    
    return '\n'.join(result)

def convert_tables(html):
    """Wandelt Markdown-Tabellen in HTML um"""
    
    table_pattern = r'(^\|.+\|\n)+\n?'
    
    def parse_table(match):
        lines = match.group(0).strip().split('\n')
        if len(lines) < 2:
            return match.group(0)
        
        rows = []
        header_found = False
        has_separator = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line == '|':
                continue
            
            # Prüfe auf Separator-Zeile
            if re.match(r'^\|[-:\s|]+\|$', line):
                has_separator = True
                header_found = True
                continue
            
            # Parse Zeile
            cells = [c.strip() for c in line.split('|')]
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]
            
            if not cells:
                continue
            
            if not header_found:
                # Header
                rows.append(''.join([f'<th>{c}</th>' for c in cells]))
            else:
                rows.append(''.join([f'<td>{c}</td>' for c in cells]))
        
        if not rows:
            return match.group(0)
        
        table_html = '<table>\n'
        if has_separator and rows:
            table_html += f'<tr>{rows[0]}</tr>\n'
            table_html += '\n'.join([f'<tr>{r}</tr>' for r in rows[1:]])
        else:
            table_html += '\n'.join([f'<tr>{r}</tr>' for r in rows])
        table_html += '\n</table>'
        
        return table_html
    
    html = re.sub(table_pattern, parse_table, html, flags=re.MULTILINE)
    return html

# ===============================
# DATEI VERARBEITUNG
# ===============================

def process_file(md_file, output_dir=None):
    """Verarbeitet eine MD-Datei und erstellt HTML"""
    
    print(f"Lese: {md_file}")
    
    # MD-Datei einlesen
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Lieferanten extrahieren
    suppliers = extract_suppliers(md_content)
    
    # MD aktualisieren mit Bezugsquellen
    md_updated = update_md_with_bezugsquellen(md_content, suppliers)
    
    if md_updated != md_content:
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_updated)
        print(f"  -> Aktualisiert: {md_file}")
        md_content = md_updated
    
    # Konvertieren
    html_body, title = md_to_html(md_content)
    date_str = datetime.now().strftime('%d.%m.%Y')
    
    # Output-Name
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = Path(md_file).stem
        output_file = os.path.join(output_dir, f"{base_name}.html")
    else:
        output_file = md_file.replace('.md', '.html')
    
    # Bezugsquellen als HTML generieren
    bezugsquellen_html = ""
    if suppliers:
        bezugsquellen_html = "<h2>Bezugsquellen</h2>\n<blockquote>\n"
        for vendor, categories in sorted(suppliers.items()):
            cats = ', '.join(sorted(categories))
            bezugsquellen_html += f'<p><a href="https://{vendor}" target="_blank">{vendor}</a> – {cats}</p>\n'
        bezugsquellen_html += "</blockquote>\n"
    
    # HTML zusammenbauen
    full_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{CSS}
    </style>
</head>
<body>
<button class="print-btn" onclick="window.print()">🖨️ Als PDF drucken</button>

<h1>{title}</h1>
<p class="note">Stand: {date_str}</p>

{html_body}

{bezugsquellen_html}

<div class="footer">
    <p>Quelle: {md_file} | Erstellt: {date_str}</p>
</div>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"  -> Erstellt: {output_file}")
    return output_file

# ===============================
# MAIN
# ===============================

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("md2html.py - Markdown zu druckbarem HTML")
        print("=" * 60)
        print()
        print("Verwendung:")
        print("  python md2html.py datei.md           - eine Datei")
        print("  python md2html.py *.md               - alle .md im Ordner")
        print("  python md2html.py ordner/            - alle .md im Ordner")
        print("  python md2html.py -o out/ datei.md   - Output in eigenem Ordner")
        print()
        sys.exit(1)
    
    output_dir = None
    
    # Check für -o Option
    args = sys.argv[1:]
    if '-o' in args:
        idx = args.index('-o')
        output_dir = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    
    for arg in args:
        if arg == '-o':
            continue
        elif os.path.isfile(arg):
            if arg.endswith('.md'):
                process_file(arg, output_dir)
        elif os.path.isdir(arg):
            for f in sorted(Path(arg).glob('*.md')):
                process_file(str(f), output_dir)
        else:
            # Glob Pattern
            import glob
            for f in glob.glob(arg):
                if f.endswith('.md'):
                    process_file(f, output_dir)
    
    print("\nFertig! HTML-Dateien können im Browser geöffnet und als PDF gedruckt werden.")

if __name__ == '__main__':
    main()