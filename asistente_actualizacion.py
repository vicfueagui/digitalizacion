"""Guía visual; el respaldo y la sustitución siguen a cargo de actualizar.py.

No instala dependencias, no abre producción y no cambia su esquema.
"""
import datetime
import json
import os
from pathlib import Path
import platform
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import uuid
import webbrowser

from actualizar import inspect_release
from app import VERSION
from app.backup import sha256
from app.runtime import resolve as resolve_runtime, environment, validate

ROOT = Path(__file__).resolve().parent
def child_environment():
    return environment()


def validate_profile(info, windows):
    # Adaptador de la API anterior; la decisión del perfil es compartida.
    normalized=dict(info,python_bits=info.get('bits'),implementacion=info.get('implementation'),
                    tk=str(info['tk']) if info.get('tk') else None)
    validate(normalized,'legado' if windows else 'laboratorio')


class UpdateSession:
    """Estado verificable y pruebas aisladas, independiente de los widgets."""
    def __init__(self, source=ROOT, windows=None):
        self.source = Path(source).resolve()
        self.windows = os.name == 'nt' if windows is None else windows
        self.destination = None
        self.interpreter = None
        self.signature = None
        self.rehearsal = None

    def choose(self, destination):
        self.destination = Path(destination).resolve()
        self.interpreter = None
        self.signature = None
        self.rehearsal = None

    def inspect(self):
        self.signature = None
        self.rehearsal = None
        if self.destination is None:
            raise ValueError('Primero elige la carpeta del proyecto que usas a diario.')
        manifest = inspect_release(self.source, self.destination)
        interpreter, info, rejected = resolve_runtime(self.destination,profile='legado' if self.windows else 'laboratorio')
        self.interpreter = interpreter
        self.signature = sha256(self.source / 'release-manifest.json')
        return manifest, info

    def _checked(self):
        if not self.signature or self.interpreter is None:
            raise ValueError('Pulsa primero «2. Comprobar».')
        if sha256(self.source / 'release-manifest.json') != self.signature:
            raise ValueError('El paquete cambió. Vuelve a comprobar y repetir el ensayo.')
        # Revisa todos los hashes y las condiciones del destino en cada fase.
        inspect_release(self.source, self.destination)

    def new_test_path(self, parent):
        candidate = Path(parent).resolve() / ('ensayo-' + VERSION + '-' +
                    datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
        for protected in (self.source, self.destination):
            if candidate == protected or protected in candidate.parents or candidate in protected.parents:
                raise ValueError('Elige una carpeta de pruebas fuera del proyecto y del paquete nuevo.')
        return candidate

    def rehearse(self, parent):
        self._checked()
        self.rehearsal = None
        target = self.new_test_path(parent)
        # El script crea exclusivamente un destino nuevo. No recibe la ruta productiva.
        result = subprocess.run([str(self.interpreter), str(self.source / 'tools/ensayo_oficina.py'),
                                 '--destino', str(target), '--ventanas'], cwd=str(self.source),
                                env=child_environment(), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, universal_newlines=True,
                                encoding='utf-8', timeout=1800)
        if result.returncode != 0:
            raise ValueError('El ensayo no pasó. Conserva sus registros en:\n' + str(target) + '\n' + result.stdout)
        report = json.loads((target / 'resultado.json').read_text(encoding='utf-8'))
        if (not report.get('comprobaciones_automaticas_correctas') or
                report.get('entorno', {}).get('version_aplicacion') != VERSION):
            raise ValueError('Informe de ensayo incompleto o de otra versión: ' + str(target))
        if self.windows and not (report.get('perfil_windows7_coincide') or report.get('perfil_windows10_conservador')):
            raise ValueError('El ensayo no acredita el perfil Windows 7 SP1 o Windows 10 conservador. Revisa ' + str(target))
        self.rehearsal = target
        return target

    def apply(self, confirmed):
        if not confirmed or self.rehearsal is None:
            raise ValueError('Completa el ensayo y confirma la revisión de la demo y el cierre del programa.')
        self._checked()
        log = self.rehearsal / 'actualizacion.log'
        # Un intento consume el ensayo: no repite una actualización accidentalmente.
        self.rehearsal = None
        with log.open('x', encoding='utf-8') as out:
            result = subprocess.run([str(self.interpreter), str(self.source / 'actualizar.py'),
                                     '--destino', str(self.destination), '--aplicar'],
                                    cwd=str(self.source), env=child_environment(),
                                    stdout=out, stderr=subprocess.STDOUT)
        if result.returncode:
            raise ValueError('La actualización no terminó correctamente. No abras el proyecto todavía.\n'
                             'Consulta el registro y «Si algo falla» en la guía:\n' + str(log) + '\n' +
                             log.read_text(encoding='utf-8'))
        return log


class UpdateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Actualizar Digitalización · ' + VERSION)
        self.geometry('820x650'); self.minsize(700,570)
        self.session = UpdateSession()
        self.events = queue.Queue(); self.busy = False; self.demo_process = None
        self.protocol('WM_DELETE_WINDOW', self.close)
        body = ttk.Frame(self, padding=16); body.pack(fill='both', expand=True)
        ttk.Label(body, text='Actualizar el programa conservando tus datos',
                  font=('TkDefaultFont', 15, 'bold')).pack(anchor='w')
        ttk.Label(body, text='Trabaja desde el paquete nuevo extraído. Sigue los pasos en orden.\n'
                  'El ensayo usa datos ficticios. Al aplicar se crea un respaldo completo.',
                  wraplength=760).pack(anchor='w', pady=(8,12))
        self.path = tk.StringVar(value='1. Elige el proyecto que contiene tus datos y tu INICIAR.bat.')
        ttk.Label(body, textvariable=self.path, wraplength=740).pack(anchor='w', pady=5)
        self.select = ttk.Button(body, text='1. Elegir proyecto…', command=self.choose)
        self.select.pack(anchor='w')
        self.check = ttk.Button(body, text='2. Comprobar paquete y proyecto', command=self.inspect)
        self.check.pack(anchor='w', pady=8)
        self.test = ttk.Button(body, text='3. Probar en carpeta independiente…', command=self.rehearse)
        self.test.pack(anchor='w')
        bar = ttk.Frame(body); bar.pack(fill='x', pady=8)
        self.demo = ttk.Button(bar, text='Abrir demo para revisarla', command=self.open_demo)
        self.demo.pack(side='left')
        self.confirmed = tk.BooleanVar()
        self.confirm = ttk.Checkbutton(body, text='Revisé la demo, cerré su ventana y cerré el programa de trabajo\n'
                                      'y otras herramientas que modifican sus archivos.', variable=self.confirmed)
        self.confirm.pack(anchor='w', pady=5)
        self.install = ttk.Button(body, text='4. Respaldar y actualizar el proyecto', command=self.apply)
        self.install.pack(anchor='w', pady=8)
        self.status = tk.StringVar(value='Elige la carpeta del proyecto. Puedes consultar la guía en cualquier momento.')
        ttk.Label(body, textvariable=self.status, wraplength=740).pack(anchor='w', pady=6)
        self.progress = ttk.Progressbar(body, mode='indeterminate'); self.progress.pack(fill='x')
        area = ttk.Frame(body); area.pack(fill='both', expand=True, pady=8)
        self.output = tk.Text(area, height=8, wrap='word', state='disabled')
        scroll = ttk.Scrollbar(area, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.output.pack(fill='both', expand=True)
        ttk.Button(body, text='Guía paso a paso / resolver un problema',
                   command=lambda:webbrowser.open((ROOT/'ACTUALIZACION.html').as_uri())).pack(anchor='w')
        def fit(event):
            if event.widget is body:
                for widget in body.winfo_children():
                    if isinstance(widget, ttk.Label): widget.configure(wraplength=max(250,event.width-8))
        body.bind('<Configure>', fit)
        self.controls(); self.after(100, self.poll)

    def controls(self):
        for button, enabled in ((self.select, True), (self.check, self.session.destination is not None),
                (self.test, self.session.signature is not None), (self.demo, self.session.rehearsal is not None),
                (self.confirm, self.session.rehearsal is not None), (self.install, self.session.rehearsal is not None)):
            button.configure(state='normal' if enabled and not self.busy else 'disabled')

    def write(self, message):
        self.output.configure(state='normal'); self.output.insert('end', message+'\n\n')
        self.output.see('end'); self.output.configure(state='disabled')

    def choose(self):
        path = filedialog.askdirectory(parent=self, title='Proyecto actual: carpeta que contiene main.py y datos')
        if path:
            self.session.choose(path); self.confirmed.set(False)
            self.path.set('Proyecto que se actualizará: ' + str(self.session.destination)); self.controls()

    def run(self, label, action, finished):
        self.busy = True; self.controls(); self.status.set(label); self.progress.start(15)
        def worker():
            try: self.events.put((finished, action(), None))
            except Exception as error: self.events.put((finished, None, str(error)))
        threading.Thread(target=worker, daemon=False).start()

    def poll(self):
        try:
            finished, result, error = self.events.get_nowait()
            self.busy = False; self.progress.stop()
            if error:
                self.status.set('Proceso detenido. Revisa el detalle antes de continuar.')
                self.write(error); messagebox.showerror('Revisar antes de continuar', error, parent=self)
            else: finished(result)
            self.controls()
        except queue.Empty: pass
        self.after(100, self.poll)

    def inspect(self):
        self.confirmed.set(False)
        def done(result):
            manifest, info = result
            self.status.set('Comprobación correcta. Continúa con el ensayo independiente.')
            self.write('Paquete ' + manifest['version'] + ': ' + str(len(manifest['files'])) +
                       ' archivos comprobados.\nPython: ' + json.dumps(info, ensure_ascii=False) +
                       '\nEsta comprobación no modifica los datos del proyecto.')
            if platform.system() != 'Windows': self.write('Este ensayo en Mac/Linux no acredita Windows 7.')
        self.run('Comprobando archivos, base de datos y entorno…', self.session.inspect, done)

    def rehearse(self):
        parent = filedialog.askdirectory(parent=self, title='Carpeta para pruebas, fuera del proyecto y del paquete')
        if not parent: return
        self.confirmed.set(False)
        def done(target):
            self.status.set('Ensayo correcto. Abre la demo, revisa los datos ficticios y ciérrala.')
            self.write('Informe y registros: ' + str(target) + '\nLa demo no contiene datos de producción.')
        self.run('Probando con datos ficticios. Se abrirán y cerrarán ventanas de prueba; espera…',
                 lambda:self.session.rehearse(parent), done)

    def open_demo(self):
        try:
            if self.demo_process and self.demo_process.poll() is None:
                raise ValueError('La demo ya está abierta. Revisa su ventana.')
            target = self.session.rehearsal
            if target is None: raise ValueError('Completa primero el ensayo.')
            with (target/'demo-manual.log').open('a', encoding='utf-8') as out:
                self.demo_process = subprocess.Popen([str(self.session.interpreter), str(ROOT/'main.py'),
                    '--workspace', str(target/'demo')], cwd=str(ROOT), env=child_environment(),
                    stdout=out, stderr=subprocess.STDOUT)
            self.write('Demo abierta. Si no aparece, consulta ' + str(target/'demo-manual.log'))
        except (ValueError, OSError) as error: messagebox.showerror('Demo', str(error), parent=self)

    def apply(self):
        if self.demo_process and self.demo_process.poll() is None:
            messagebox.showinfo('Cierra la demo', 'Cierra la ventana de la demo antes de actualizar.', parent=self); return
        if not self.confirmed.get():
            messagebox.showinfo('Revisión pendiente', 'Revisa la demo y marca la casilla de confirmación.', parent=self); return
        if not messagebox.askyesno('Confirmar carpeta', 'Se respaldará y actualizará:\n' +
                                  str(self.session.destination) + '\n\n¿Es tu proyecto de trabajo?', parent=self): return
        def done(log):
            self.confirmed.set(False)
            self.status.set('Actualización terminada. Consulta abajo el resguardo y los pasos finales.')
            self.write(log.read_text(encoding='utf-8') + '\nRegistro: ' + str(log) +
                       '\nAhora abre DIAGNOSTICO.bat y después INICIAR.bat desde tu proyecto habitual. '
                       'Comprueba los folios, legajos, conteos e imágenes antes de retomar capturas.')
        self.run('Creando respaldo completo y actualizando. No cierres esta ventana ni apagues el equipo…',
                 lambda:self.session.apply(True), done)

    def close(self):
        if self.busy:
            messagebox.showinfo('Proceso en curso', 'Espera a que termine el paso actual. El detalle aparecerá aquí.', parent=self)
        else: self.destroy()


if __name__ == '__main__':
    UpdateApp().mainloop()
