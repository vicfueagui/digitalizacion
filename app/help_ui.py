"""Ayuda local con fuentes explícitas; nunca muestra bitácoras ni datos del workspace."""
import tkinter as tk
from tkinter import ttk
from html.parser import HTMLParser
from .core import ROOT
from .directory import normalized

TOPICS=[('Integraciones, entregas y atajos','INTEGRACIONES_V070.md'),
        ('Recepción e indicadores','RECEPCION_INDICADORES_V061.md'),('Operación paso a paso','OPERACION_V05.md')]


class PlainHTML(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
        if tag in ('p','h1','h2','h3','li','tr','br'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)


class HelpWindow(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.title('Ayuda · cómo trabajar con Digitalización');self.geometry('1000x650')
        self.documents={}
        for title,name in TOPICS:
            path=ROOT/'docs'/name
            if not path.is_file():continue
            content=path.read_text(encoding='utf-8')
            if name.endswith('.html'):
                parser=PlainHTML();parser.feed(content);content=''.join(parser.parts)
            self.documents[title]=content
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x')
        ttk.Label(bar,text='Buscar en la ayuda').pack(side='left');self.query=tk.StringVar();entry=ttk.Entry(bar,textvariable=self.query);entry.pack(side='left',fill='x',expand=True,padx=8)
        body=ttk.Panedwindow(self,orient='horizontal');body.pack(fill='both',expand=True,padx=8,pady=8)
        self.topics=tk.Listbox(body,width=30,exportselection=False);body.add(self.topics,weight=1)
        frame=ttk.Frame(body);body.add(frame,weight=4)
        self.text=tk.Text(frame,wrap='word',padx=18,pady=15,font='AppReadingFont',spacing1=2,spacing3=5);scroll=ttk.Scrollbar(frame,command=self.text.yview);self.text.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.text.pack(fill='both',expand=True)
        self.text.tag_configure('heading',font='AppReadingHeadingFont',foreground='#B3282A',spacing1=14,spacing3=6)
        self.topics.bind('<<ListboxSelect>>',lambda e:self.show());self.query.trace_add('write',lambda *a:self.filter())
        self.filter();entry.focus_set()
    def filter(self):
        q=normalized(self.query.get());self.matches=[title for title,content in self.documents.items() if q in normalized(title+' '+content)]
        self.topics.delete(0,'end')
        for title in self.matches:self.topics.insert('end',title)
        if self.matches:self.topics.selection_set(0)
        self.show()
    def show(self):
        selected=self.topics.curselection();self.text.configure(state='normal');self.text.delete('1.0','end')
        content=self.documents[self.matches[selected[0]]] if selected else 'No se encontraron temas. Prueba otra palabra.'
        for line in content.splitlines():self.text.insert('end',line.lstrip('# ')+'\n','heading' if line.startswith('#') else ())
        q=normalized(self.query.get())
        if q:
            for line_number,line in enumerate(content.splitlines(),1):
                if q in normalized(line):self.text.see(str(line_number)+'.0');break
        self.text.configure(state='disabled')
