"""Ensayo conservado: integraciones, entrega acumulada y recuperación completa."""
import json
import tempfile
from pathlib import Path
import unittest
from app.core import Store
from app.demo import create_demo
from app.coding import CodingService
from app.delivery import Deliveries
from app.review import Reviews
from app.integrations import Integrations
from app.backup import create_backup,restore_backup,verify_backup,sha256


class PersistentDemoTests(unittest.TestCase):
    def test_complete_delivery_restore_and_demo(self):
        from PIL import Image,ImageDraw
        root=Path(tempfile.gettempdir()).parent/'ensayo-conservado';root.mkdir(exist_ok=False)
        demo=create_demo(root/'demo');s=Store(workspace=demo,operador='Responsable ficticio')
        try:
            coder=CodingService(s);d=Deliveries(s);reviews=Reviews(s);integrations=Integrations(s)
            work=s.works()[0]['id'];delivery=s.rows('SELECT id FROM entregas WHERE trabajo_id=? ORDER BY numero DESC LIMIT 1',(work,))[0]['id']
            for row in s.rows("SELECT id FROM observaciones_revision WHERE estado='Resuelta'"):
                reviews.update_observation(row['id'],'Validada','Cotejo sintético de imagen corregida',delivery)
            reviews.begin(delivery);reviews.approve(delivery,'Revisión sintética de carga inicial')
            original=d.verify(delivery);oldfolder=s.workspace.path(d.get(delivery)['ruta'])
            hashes={p.relative_to(oldfolder).as_posix():sha256(p) for p in oldfolder.rglob('*') if p.is_file()}
            folio=s.save_folio('INTEGRACIONES-DEMO/2026','2026-09-30')
            for number in (1,2):
                integrations.start(work,'Documentación adicional ficticia '+str(number),'2026-09-30' if number==1 else '2026-10-01',folio,'Acuse de ensayo '+str(number),'Digitalizador ficticio '+str(number),True)
                s.add_count(work,number+1);s.confirm_count(work)
                frames=[]
                for page in range(number+1):
                    frame=Image.new('L',(640,900),'white');draw=ImageDraw.Draw(frame)
                    draw.rectangle((30,30,610,870),outline='black',width=3)
                    draw.text((55,60),'FICTICIO - INTEGRACION {} - PAGINA {}'.format(number,page+1),fill='black');frames.append(frame)
                path=s.workspace.root/'muestras'/('integracion_'+str(number)+'.tif')
                frames[0].save(path,save_all=True,append_images=frames[1:],compression='tiff_deflate')
                for frame in frames:frame.close()
                result=coder.import_files(work,[path]);self.assertEqual(result['importados'],1)
                ident=s.rows('SELECT MAX(id) AS id FROM archivos_tiff WHERE trabajo_id=?',(work,))[0]['id'];coder.assign(ident,'DP-01')
                coder.organize(work);latest=s.rows('SELECT id FROM entregas WHERE trabajo_id=? ORDER BY numero DESC LIMIT 1',(work,))[0]['id']
                reviews.begin(latest);reviews.approve(latest,'Cotejo completo ficticio '+str(number))
                self.assertEqual(len(d.verify(latest)['items']),2+number)
                self.assertEqual(d.verify(delivery),original)
            totals=integrations.totals(work);self.assertEqual((totals['hojas_totales'],totals['tiff'],totals['paginas']),(8,4,9))
            self.assertEqual(hashes,{p.relative_to(oldfolder).as_posix():sha256(p) for p in oldfolder.rglob('*') if p.is_file()})
            integrations.start(work,'Tercera integración ficticia por contar','2026-10-01',folio,'Acuse sintético pendiente','Digitalizador ficticio 2',True)
            tables=('integraciones','conteos','historial','trabajos','archivos_tiff','documentos_logicos','versiones_archivo','entregas','entrega_items','prestamo_items','asignaciones','lotes_tiff')
            before={table:s.rows('SELECT * FROM '+table+' ORDER BY rowid') for table in tables}
            backup=create_backup(s,root/'respaldo');verified=verify_backup(backup)
        finally:s.db.close()
        restored=restore_backup(backup,root/'restaurado');s=Store(workspace=restored)
        try:
            for table in tables:self.assertEqual(before[table],s.rows('SELECT * FROM '+table+' ORDER BY rowid'),table)
            for row in s.rows("SELECT id FROM entregas WHERE estado NOT IN ('Preparando','Incompleta')"):Deliveries(s).verify(row['id'])
            self.assertEqual(s.rows('PRAGMA foreign_key_check'),[])
            evidence={'correcto':True,'tablas_comparadas':len(tables),'filas_comparadas':sum(map(len,before.values())),
                'archivos_respaldo':len(verified['files']),'integraciones':Integrations(s).list(work),
                'totales_antes_de_tercera':totals,'total_con_tercera_pendiente':Integrations(s).totals(work),
                'entregas_conservadas':len(s.rows('SELECT id FROM entregas')),'datos':'Exclusivamente ficticios',
                'limite':'Se comparan doce tablas de negocio. Las rutas históricas del diario son normalizadas por el respaldo existente; no se afirma igualdad literal de toda la base.'}
            (root/'resultado.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        finally:s.db.close()
