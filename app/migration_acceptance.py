"""Ensayo aislado, aceptación explícita y arranque del código conservado."""
import datetime
import json
from pathlib import Path
import platform
import subprocess
import sys
import uuid

from .backup import sha256
from .runtime import probe,environment,resolve
from .transfer import load_installation,verify_destination,code_files
from .update_recovery import write_json
from .workspace import WorkspaceLock


def target_runtime(executable,laboratory):
    info=probe(executable,'laboratorio' if laboratory else 'legado')
    if not laboratory:
        # platform.release puede decir 10 también en Windows 11.
        result=subprocess.run([str(executable),'-I','-c','import sys; print(sys.getwindowsversion().build)'],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',env=environment(),timeout=30)
        if info['sistema']!='Windows' or info['sistema_version']!='10' or result.returncode or not result.stdout.strip().isdigit() or not 10240<=int(result.stdout.strip())<22000:
            raise ValueError('La aceptación de producción de esta fase requiere Windows 10. Otros sistemas solo admiten demos.')
    return info


def require_equal(root,locked=False):
    report=verify_destination(root,locked=locked)
    if report['diferencias']:raise ValueError('MIGRACION NO VERIFICADA: '+'; '.join(report['diferencias']))
    return report


def rehearse(root,executable=None):
    root,state,manifest=load_installation(root)
    if (root/'INCOMPLETO.txt').exists():raise ValueError('Instalación incompleta.')
    executable=Path(executable or sys.executable).absolute()
    info=target_runtime(executable,manifest['solo_laboratorio'])
    if not manifest['solo_laboratorio']:
        source=manifest['entorno_origen']
        for key in ('python','python_bits','implementacion','tk','tcl','pillow','libtiff','libtiff_version','sqlite'):
            if info.get(key)!=source.get(key):raise ValueError('El runtime difiere del origen en '+key+'. Conserva también las mismas bibliotecas para esta fase.')
    lock=WorkspaceLock(root/'workspace')
    try:
        require_equal(root,True)
        output=root/'ensayos'/('ensayo-'+uuid.uuid4().hex);output.mkdir(parents=True)
        results=[]
        commands=[('suite_herramientas',[root/'herramientas/tools/run_tests.py','--resultado',output/'pruebas_herramientas.json'],1200),
                  ('suite_origen',[root/'programa/tools/run_tests.py','--resultado',output/'pruebas.json'],1200),
                  ('crear_demo',[root/'programa/main.py','--crear-demo',output/'demo'],120),
                  ('ventanas_tiff',[root/'programa/tools/smoke_ui.py'],180)]
        # El ensayo original de interfaz abre TIFF individuales/multipágina y páginas editadas.
        for name,arguments,timeout in commands:
            with (output/(name+'.log')).open('x',encoding='utf-8') as stream:
                try:
                    process=subprocess.run([str(executable)]+[str(a) for a in arguments],cwd=str(root/'programa'),
                                           stdout=stream,stderr=subprocess.STDOUT,env=environment(),timeout=timeout)
                    results.append({'etapa':name,'correcto':process.returncode==0,'codigo':process.returncode})
                except (OSError,subprocess.TimeoutExpired) as error:
                    results.append({'etapa':name,'correcto':False,'error':type(error).__name__})
            if not results[-1]['correcto']:break
        require_equal(root,True)
        report={'paquete_id':manifest['id'],'manifiesto':state['manifest_sha256'],'entorno':info,'instalacion':str(root),
                'ejecutable':str(executable),'fecha':datetime.datetime.now().astimezone().isoformat(),
                'etapas':results,'correcto':len(results)==len(commands) and all(r['correcto'] for r in results)}
        write_json(output/'resultado.json',report)
        if report['correcto']:
            state['ensayo']=(output/'resultado.json').relative_to(root).as_posix()
            state['ensayo_sha256']=sha256(output/'resultado.json');write_json(root/'migracion.json',state)
        else:raise ValueError('El ensayo falló. Producción permanece bloqueada. Consulta '+str(output))
        return report
    finally:lock.close()


def activate(root,confirmed=False):
    if not confirmed:raise ValueError('Confirma la revisión visual y que Windows 7 está cerrado y congelado.')
    root,state,manifest=load_installation(root)
    if (root/'INCOMPLETO.txt').exists():raise ValueError('Instalación incompleta.')
    from .manifests import plain_path
    if not state.get('ensayo'):raise ValueError('Primero ejecuta el ensayo completo en este destino.')
    report_path=plain_path(root,state['ensayo'])
    if sha256(report_path)!=state.get('ensayo_sha256'):raise ValueError('El informe del ensayo cambió.')
    report=json.loads(report_path.read_text(encoding='utf-8'))
    if not report.get('correcto') or report.get('manifiesto')!=state['manifest_sha256'] or report.get('paquete_id')!=manifest['id']:
        raise ValueError('No hay ensayo válido para este paquete.')
    if report.get('instalacion')!=str(root):raise ValueError('La instalación cambió de ubicación. Repite el ensayo en esta carpeta.')
    info=target_runtime(report['ejecutable'],manifest['solo_laboratorio'])
    if info!=report['entorno']:raise ValueError('El entorno cambió después del ensayo. Repítelo.')
    lock=WorkspaceLock(root/'workspace')
    try:
        comparison=require_equal(root,True)
        state.update(estado='Laboratorio habilitado' if manifest['solo_laboratorio'] else 'Producción habilitada',
                     aceptacion=datetime.datetime.now().astimezone().isoformat(),ejecutable=report['ejecutable'],entorno=info,instalacion=str(root))
        write_json(root/'evidencia/aceptacion.json',dict(comparison,fecha=state['aceptacion'],ensayo_sha256=state['ensayo_sha256']))
        write_json(root/'migracion.json',state)
        marker=root/'workspace/.restauracion_incompleta'
        if marker.exists():marker.unlink()  # Último paso: interrupciones previas permanecen bloqueadas.
        return {'conclusion':'MIGRACION VERIFICADA','estado':state['estado'],'solo_laboratorio':manifest['solo_laboratorio']}
    finally:lock.close()


def launch(root):
    root,state,manifest=load_installation(root)
    if (root/'INCOMPLETO.txt').exists() or (root/'workspace/.restauracion_incompleta').exists() or state['estado'] not in ('Laboratorio habilitado','Producción habilitada'):
        raise ValueError('Completa Verificar, Ensayar y Habilitar antes de abrir.')
    if state.get('instalacion')!=str(root):raise ValueError('No muevas una producción aceptada; prepara otro traslado verificable.')
    # Tras nuevas capturas la base debe poder evolucionar. La igualdad inicial queda certificada en evidencia/.
    if code_files(root/'programa')!=manifest['programa'] or code_files(root/'herramientas')!=manifest['herramientas']:
        raise ValueError('El código cambió desde la aceptación. Requiere un procedimiento de actualización independiente.')
    chosen,ignored_info,rejected=resolve(root/'herramientas',state['ejecutable'],
                                        'laboratorio' if manifest['solo_laboratorio'] else 'legado')
    info=target_runtime(chosen,manifest['solo_laboratorio'])
    if {k:v for k,v in info.items() if k!='ejecutable'}!={k:v for k,v in state['entorno'].items() if k!='ejecutable'}:
        raise ValueError('Las versiones o capacidades del runtime cambiaron desde la aceptación.')
    if str(chosen)!=state['ejecutable']:
        # Una ruta rota puede tener alternativa con exactamente las mismas bibliotecas.
        # Registrar fuera de la base; nunca rebajar requisitos ni perder nuevas capturas.
        write_json(root/('evidencia/runtime-'+uuid.uuid4().hex+'.json'),
                   {'anterior':state['ejecutable'],'actual':str(chosen),'entorno':info,'descartados':rejected,
                    'fecha':datetime.datetime.now().astimezone().isoformat()})
        state.update(ejecutable=str(chosen),entorno=info);write_json(root/'migracion.json',state)
    return subprocess.call([str(chosen),str(root/'programa/main.py'),'--workspace',str(root/'workspace')],
                           cwd=str(root/'programa'),env=environment())
