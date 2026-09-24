"""Render pequeño y sin dependencias para los dos manuales Markdown del proyecto.

Sintaxis admitida: títulos, párrafos, listas simples, tablas, enlaces, negritas,
código inline y bloques de código. HTML de origen se escapa deliberadamente.
"""
import html
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
STYLE = '''
*{box-sizing:border-box}body{margin:0;background:#edf2f5;color:#172b3a;font:17px/1.65 Arial,sans-serif}
header{background:#123b50;color:white;padding:28px 6%}header a{color:#d5f2ff}
main{max-width:1100px;margin:auto;padding:26px;background:white}h1{line-height:1.2;font-size:2em}
h2{margin:2.3em 0 .6em;border-top:3px solid #167d91;padding-top:.7em;line-height:1.3}
h3{margin:1.7em 0 .4em}a{color:#075f85;text-decoration:underline}a:focus,button:focus{outline:3px solid #bf6200}
nav{background:#eef6f8;padding:20px;border-left:5px solid #167d91}nav ul{padding-left:22px;margin:0}
nav li{margin:4px 0;break-inside:avoid}nav ul{columns:2;column-gap:28px}li{margin:8px 0}p{margin:.85em 0}strong{color:#102f40}
pre{white-space:pre-wrap;word-wrap:break-word;padding:16px;border:1px solid #cbd9df;background:#f2f5f7}
code{font-family:Consolas,Menlo,monospace;font-size:.9em;background:#f2f5f7;overflow-wrap:anywhere}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:15px 0;font-size:.94em}
th,td{border:1px solid #bbcdd5;text-align:left;vertical-align:top;padding:10px}th{background:#e5f1f5}
tr:nth-child(even){background:#f8fafb}.intro{padding:12px 18px;border-left:5px solid #bd7900;background:#fff8e8}
button{font:inherit;border:1px solid #9bb9c8;background:white;color:#123b50;padding:7px 14px;cursor:pointer}
footer{margin:25px 0;font-size:.9em;color:#456} .back{display:block;margin-top:14px;font-size:.88em}
@media(max-width:800px){nav ul{columns:1}}@media(max-width:680px){main{padding:16px}body{font-size:16px}header{padding:20px}h1{font-size:1.65em}}
@media print{body,main{background:white;font-size:11pt}header{background:white;color:black;padding:0}
header a{color:black}main{max-width:none;padding:0}nav,button,.back{display:none}h2{break-after:avoid}
pre,table{font-size:9pt}tr{break-inside:avoid}a{color:black}h2{margin-top:24px}}
'''


def slug(text):
    plain = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', plain).strip('-')


def inline(text):
    tokens = []
    def save(value):
        tokens.append(value); return '\x00{}\x00'.format(len(tokens)-1)
    text = re.sub(r'`([^`]+)`', lambda m:save('<code>'+html.escape(m[1])+'</code>'), text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m:save('<a href="'+html.escape(m[2],quote=True)+'">'+html.escape(m[1])+'</a>'), text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub('\x00(\d+)\x00', lambda m:tokens[int(m[1])], text)


def render(markdown, title, home, manual):
    lines = markdown.splitlines(); content = []; toc = []; seen = set(); i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        if line.startswith('```'):
            block = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'): block.append(lines[i]); i += 1
            content.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>'); i += 1; continue
        match = re.match(r'^(#{1,3}) (.+)', line)
        if match:
            level = len(match[1]); heading = match[2]; anchor = slug(heading)
            if anchor in seen: raise ValueError('Título duplicado: '+heading)
            seen.add(anchor)
            if level == 2 and toc: content.append('<a class="back" href="#inicio">Volver al índice</a>')
            if level != 1: content.append('<h{0} id="{1}">{2}</h{0}>'.format(level,anchor,inline(heading)))
            if level == 2: toc.append('<li><a href="#'+anchor+'">'+html.escape(heading)+'</a></li>')
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells): rows.append(cells)
                i += 1
            table = '<div class="table"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'
            content.append(table+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>'); continue
        match = re.match(r'^(?:- |\d+\. )(.+)', line)
        if match:
            kind = 'ul' if line.startswith('- ') else 'ol'; entries = []
            while i < len(lines):
                match = re.match(r'^- (.+)' if kind == 'ul' else r'^\d+\. (.+)', lines[i])
                if not match: break
                entries.append('<li>'+inline(match[1])+'</li>'); i += 1
            content.append('<'+kind+'>'+''.join(entries)+'</'+kind+'>'); continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|- |\d+\. )', lines[i]):
            paragraph.append(lines[i]); i += 1
        content.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>'''+html.escape(title)+'''</title><style>'''+STYLE+'''</style></head>
<body id="inicio"><header>Digitalización · Documentación 0.6.3<h1>'''+html.escape(title)+'''</h1>
<a href="'''+home+'''">Cómo actualizar</a> · <a href="'''+manual+'''">Manual de uso</a>
</header><main><p class="intro">Guía local: funciona sin internet. Busca una palabra con Ctrl+F (Mac: Cmd+F).
Para imprimir, usa Ctrl+P (Mac: Cmd+P). Si tu equipo ofrece guardar PDF, puedes elegirlo allí.</p>
<nav aria-label="Índice"><strong>Ir directamente a…</strong><ul>'''+''.join(toc)+'''</ul></nav>
'''+ '\n'.join(content)+'''<a class="back" href="#inicio">Volver al índice</a>
<footer>Documentación para el kit 0.6.3. Los ejemplos son ficticios. La comprobación local en Mac no sustituye la aceptación en Windows 7 y Windows 10.</footer>
</main></body></html>
'''


def build():
    for source, target, title, home, manual in (
        ('docs/ACTUALIZACION.md','ACTUALIZACION.html','Actualizar sin perder datos','ACTUALIZACION.html','docs/MANUAL_USUARIO.html'),
        ('MIGRACION_WINDOWS10.md','MIGRACION_WINDOWS10.html','Migrar a Windows 10 paso a paso','ACTUALIZACION.html','docs/MANUAL_USUARIO.html'),
        ('docs/MANUAL_USUARIO.md','docs/MANUAL_USUARIO.html','Manual de uso de Digitalización','../ACTUALIZACION.html','MANUAL_USUARIO.html')):
        text = (ROOT/source).read_text(encoding='utf-8')
        # La fuente Markdown vive en docs; la guía de actualización se publica en la raíz.
        if target == 'ACTUALIZACION.html':
            text = re.sub(r'\]\(([^)#]+)(#[^)]*)?\)',
                          lambda m:']('+ ('docs/'+m[1] if not m[1].startswith(('../','https:','http:')) else m[1][3:] if m[1].startswith('../') else m[1]) +(m[2] or '')+')',text)
        (ROOT/target).write_text(render(text,title,home,manual),encoding='utf-8')
        print(target)


if __name__ == '__main__': build()
