"""Paleta solicitada; estados también se distinguen por texto, no solo color."""
from tkinter import ttk, font as tkfont
GUINDA='#B3282A'
GRAY='#808285'
GOLD='#896B32'


def fonts(widget):
    """Fuentes por función, en puntos; conserva la escala de Windows/Tk."""
    root=widget._root()
    if hasattr(root,'_digitalizacion_fonts'):return root._digitalizacion_fonts
    available=set(tkfont.families(root))
    default=tkfont.Font(root=root,name='TkDefaultFont',exists=True).actual('family')
    body='Segoe UI' if 'Segoe UI' in available else default
    strong='Segoe UI Semibold' if 'Segoe UI Semibold' in available else body
    weight='normal' if strong!=body else 'bold'
    roles={'AppBodyFont':(body,10,'normal'),'AppStrongFont':(strong,10,weight),
           'AppTitleFont':(strong,18,weight),'AppSubtitleFont':(strong,12,weight),
           'AppMetricFont':(strong,23,weight),'AppReadingFont':(body,11,'normal'),
           'AppReadingHeadingFont':(strong,13,weight),'AppSmallFont':(body,9,'normal')}
    result={name:tkfont.Font(root=root,name=name,family=family,size=size,weight=bold)
            for name,(family,size,bold) in roles.items()}
    for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkCaptionFont','TkSmallCaptionFont','TkIconFont','TkTooltipFont'):
        tkfont.Font(root=root,name=name,exists=True).configure(family=body,size=9 if name in ('TkSmallCaptionFont','TkTooltipFont') else 10,weight='normal')
    tkfont.Font(root=root,name='TkHeadingFont',exists=True).configure(family=strong,size=10,weight=weight)
    fixed='Consolas' if 'Consolas' in available else tkfont.Font(root=root,name='TkFixedFont',exists=True).actual('family')
    tkfont.Font(root=root,name='TkFixedFont',exists=True).configure(family=fixed,size=10)
    root.option_add('*Font','AppBodyFont')
    root._digitalizacion_fonts=result
    return result


def apply(root):
    typography=fonts(root)
    style=ttk.Style(root)
    if 'clam' in style.theme_names():style.theme_use('clam')
    root.configure(background='#F6F3F0')
    style.configure('.',background='#F6F3F0',foreground='#29282A',font='AppBodyFont')
    style.configure('TButton',padding=(9,6),font='AppStrongFont')
    style.map('TButton',background=[('active','#EADCD5')])
    style.configure('Title.TLabel',font='AppTitleFont',foreground=GUINDA)
    style.configure('Subtitle.TLabel',font='AppSubtitleFont',foreground='#772023')
    style.configure('Metric.TLabel',font='AppMetricFont')
    style.configure('Treeview',rowheight=max(30,typography['AppBodyFont'].metrics('linespace')+12),font='AppBodyFont',background='white',fieldbackground='white',foreground='#29282A')
    style.map('Treeview',background=[('selected',GUINDA)],foreground=[('selected','white')])
    style.configure('Treeview.Heading',background='#E8E3DF',foreground='#29282A',font='AppStrongFont',padding=(7,7))
    style.configure('TNotebook.Tab',padding=(10,7),font='AppStrongFont')
    style.map('TNotebook.Tab',background=[('selected',GUINDA)],foreground=[('selected','white')])
    style.configure('TLabelframe.Label',foreground=GOLD,font='AppStrongFont')
