"""Datos inventados: no representan expedientes ni identidades verificadas."""
import csv
import json
from .workspace import Workspace


def create_demo(destination):
    from PIL import Image, ImageDraw
    from .core import Store
    from .coding import CodingService
    ws = Workspace(destination)
    ws.root.mkdir(parents=True, exist_ok=False)
    (ws.root / 'DEMO.json').write_text(json.dumps({'demo': True, 'description': 'Datos ficticios para pruebas'}), encoding='utf-8')
    store = Store(workspace=ws.root, operador='Operador de demostración')
    try:
        folio = store.save_folio('DEMO/2026', '2026-09-21')
        other = store.save_folio('DEMO-B/2026', '2026-09-21')
        works = [store.save_work(folio, 'AAAA900101HYNBBB01', 'Persona ficticia de demostración', n, recibido='2026-09-21') for n in (1, 2)]
        store.save_work(other, 'EEEE900102MYNCCC02', 'Otra persona ficticia', 1)
        for code, folder, title in [('DP-01', 'PERSONALES', 'Documento de prueba'), ('DP-15', 'PERSONALES', 'Acta ficticia'), ('FP-20', 'PERSONALES', 'Formato ficticio'), ('HL-100', 'FEDERAL', 'Historia ficticia')]:
            store.save_catalog('documento', code, folder, title)
        store.save_catalog('incidencia', 'REVISAR', '', 'Revisar imagen de prueba')
        for work in works:
            store.add_count(work, 3); store.confirm_count(work)
        from .operations import Operations
        ops=Operations(store)
        ops.receive_folio(folio,'Archivo ficticio','Persona que entrega (demo)','Persona que recibe (demo)','Acuse ficticio')
        for work in works:
            w=store.one('trabajos',work)
            ops.validate_item(w['prestamo_item_id'],'Aceptado',w['curp'],w['legajo'],'Cotejo físico simulado')
        ops.assign('Digitalizador de demostración','Asignación de ensayo',folio=folio)
        samples = ws.path('muestras'); samples.mkdir()
        frames = []
        for n, size in enumerate(((640, 900), (900, 640), (640, 900))):
            im = Image.new('1', size, 'white')
            draw = ImageDraw.Draw(im)
            draw.rectangle((25, 25, size[0]-25, size[1]-25), outline='black', width=3)
            draw.text((60, 55), 'DEMO - PAGINA %d - DATOS FICTICIOS' % (n+1), fill='black')
            for x in range(60, size[0]-60, 6):
                draw.line((x, 100, x, 240), fill='black', width=1)
            frames.append(im)
        single = samples / 'Una página.tif'; multi = samples / 'Tres páginas.tif'
        frames[0].save(single, compression='tiff_deflate', dpi=(300, 300))
        frames[0].save(multi, save_all=True, append_images=frames[1:], compression='tiff_deflate', dpi=(300, 300))
        for frame in frames: frame.close()
        service = CodingService(store)
        for work in works:
            result = service.import_files(work, [single, multi])
            if result['errores']: raise ValueError(str(result))
            files = service.files(work)
            service.assign(files[0]['id'], 'DP-15'); service.assign(files[1]['id'], 'HL-100')
        service.organize(works[0])
        from .delivery import Deliveries
        from .review import Reviews
        delivery=store.rows('SELECT id FROM entregas WHERE trabajo_id=? ORDER BY numero DESC LIMIT 1',(works[0],))[0]['id']
        reviews=Reviews(store);session=reviews.begin(delivery);first=service.files(works[0])[0]
        observation=reviews.observe(session,'Orientación/recorte','Revisar orientación de la hoja ficticia','Digitalizador de demostración',first['documento_id'],first['version_id'],1,'Hoja de demostración')
        service.save_edit(first['id'],0,[('rotate',90)])
        next_delivery=Deliveries(store).prepare(works[0])
        reviews.update_observation(observation,'Resuelta','Orientación corregida; pendiente de validar por el responsable',next_delivery)
        service.mark_correction(service.files(works[1])[1]['id'], 2, 'Separador de ejemplo, hoja sin número registrado', 'Revisar orientación del escaneo sintético')
        store.save_task('Resolver reescaneo ficticio', work=works[1])
        examples=ws.path('ejemplos');examples.mkdir()
        with (examples/'lista_folio_sintetica.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(['CURP O RFC','No.','APELLIDO PATERNO, MATERNO, NOMBRE','CURP O RFC2','Integra','folio','sistema','fecha solicitud','TRABAJADOS'])
            for n,identity in enumerate(('IIII900103HYNDDD03','OOOO900104MYNFFF04','UUUU900105HYNHHH05'),1):
                writer.writerow([identity,n,'Persona ficticia de lista '+str(n),identity,'Integrador de demostración','LISTA-DEMO/2026','Sistema ficticio','18/8/2026','NO TRABAJADO'])
        return ws.root
    finally:
        store.db.close()
