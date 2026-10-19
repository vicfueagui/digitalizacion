"""Compatibilidad real de cierre TIFF; conserva las páginas y detecta finalizadores."""
import gc
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ModernTiffTests(unittest.TestCase):
    def test_multipage_edit_closes_writer_once_and_preserves_pixels(self):
        from PIL import Image
        from app.coding import stream_edit, page_info
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'original.tif';target=root/'editado.tif'
            a=Image.new('RGB',(16,20),'white');b=Image.new('RGB',(24,32),'black')
            a.save(source,save_all=True,append_images=[b],format='TIFF');a.close();b.close()
            gc.collect();errors=[]
            with patch.object(sys,'unraisablehook',lambda event:errors.append(str(event.exc_value))):
                stream_edit(source,target,1,[('rotate',90)])
                gc.collect()
            self.assertEqual(errors,[])
            self.assertEqual([i['size'] for i in page_info(target,True)],[(16,20),(32,24)])
            self.assertEqual([i['size'] for i in page_info(source,True)],[(16,20),(24,32)])
