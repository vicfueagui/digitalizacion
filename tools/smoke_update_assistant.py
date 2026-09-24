"""Comprobación real de la ventana sin seleccionar ni modificar una instalación."""
import sys
import time
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from asistente_actualizacion import UpdateApp


def main():
    app = UpdateApp(); errors = []
    app.report_callback_exception = lambda kind,error,tb:errors.append(str(error))
    try:
        for size in ('700x570','820x650','1024x720'):
            app.geometry(size); app.update()
            assert str(app.check['state']) == 'disabled'
            assert str(app.install['state']) == 'disabled'
            for button in (app.select,app.check,app.test,app.demo,app.confirm,app.install):
                left = button.winfo_rootx()-app.winfo_rootx()
                top = button.winfo_rooty()-app.winfo_rooty()
                assert 0 <= left and left+button.winfo_width() <= app.winfo_width(), size
                assert 0 <= top and top+button.winfo_height() <= app.winfo_height(), size
        results = []
        app.run('Comprobación sintética de respuesta de interfaz',lambda:'sin datos',results.append)
        assert app.busy and str(app.select['state']) == 'disabled'
        with patch('asistente_actualizacion.messagebox.showinfo') as warning:
            app.close(); warning.assert_called_once()
        deadline = time.monotonic()+5
        while app.busy and time.monotonic()<deadline:
            app.update(); time.sleep(.01)
        assert results == ['sin datos'] and not app.busy
        assert str(app.select['state']) == 'normal'
        assert not errors, errors
        print('OK: asistente 700/820/1024, pasos bloqueados, tarea en hilo, cierre protegido y resultado en Tk.')
    finally:app.destroy()


if __name__ == '__main__':main()
