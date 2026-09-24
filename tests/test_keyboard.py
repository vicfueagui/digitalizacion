import unittest
from types import SimpleNamespace
from unittest.mock import patch
from app.coding_v3 import NumericInput
from app.coding_ui_v3 import CodingUIV3


class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.h=SimpleNamespace(numeric=NumericInput(),pressed=set(),catalog=[{'combinacion':'Ctrl','numero':15,'codigo':'DP-15'},{'combinacion':'Ctrl+Shift','numero':100,'codigo':'HL-100'}])
        self.assigned=[];self.h.safe=lambda f:f();self.h.assign=self.assigned.append
        self.h.info=SimpleNamespace(set=lambda x:None);self.h.crop_mode=SimpleNamespace(set=lambda x:None)
        self.widget=SimpleNamespace(winfo_toplevel=lambda:self.h,winfo_class=lambda:'Canvas')
        for name in ('save','undo','rename','navigate','page_move','only_image'):setattr(self.h,name,lambda *args:None)
    def event(self,key,state=4,widget=None,keycode=0):return SimpleNamespace(keysym=key,state=state,widget=widget or self.widget,keycode=keycode)
    def press(self,key,state=4,widget=None,keycode=0):CodingUIV3.key_press(self.h,self.event(key,state,widget,keycode))
    def release(self,key,widget=None):CodingUIV3.key_release(self.h,self.event(key,widget=widget))
    def test_sequence_repeated_press_does_not_fire_early(self):
        self.press('1');self.press('1');self.release('1');self.press('5');self.release('5')
        self.assertEqual(self.assigned,[]);self.release('Control_L');self.assertEqual(self.assigned,['DP-15'])
    def test_keypad_and_shift_100(self):
        for key in ('KP_1','KP_0','KP_0'):self.press(key,5);self.release(key)
        self.release('Control_L');self.assertEqual(self.assigned,['HL-100'])
    def test_entry_focus_release_never_assigns(self):
        for key in ('1','5'):self.press(key);self.release(key)
        entry=SimpleNamespace(winfo_toplevel=lambda:self.h,winfo_class=lambda:'TEntry')
        self.release('Control_L',entry);self.assertEqual(self.assigned,[])
        self.press('1',widget=entry);self.release('Control_L',entry);self.assertEqual(self.assigned,[])
    def test_modifier_switch_cancels_whole_sequence(self):
        n=NumericInput();n.digit('1');n.digit('5',True);self.assertIsNone(n.finish())
    def test_spanish_shift_uses_physical_windows_digit(self):
        with patch('app.coding_ui_v3.sys.platform','win32'):
            self.press('exclam',5,keycode=49);self.release('exclam')
            self.press('equal',5,keycode=48);self.release('equal')
            self.press('equal',5,keycode=48);self.release('equal')
        self.release('Control_L');self.assertEqual(self.assigned,['HL-100'])
    def test_child_dialog_never_codes(self):
        child=SimpleNamespace(winfo_toplevel=lambda:object(),winfo_class=lambda:'Canvas')
        self.press('1',widget=child);self.release('Control_L',child);self.assertEqual(self.assigned,[])
