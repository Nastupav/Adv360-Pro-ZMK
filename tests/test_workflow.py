import shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from validate_workflow import validate

class WorkflowRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);shutil.copytree(ROOT/'config',self.root/'config')
    def change(self,layer,before,after):
        p=self.root/'config/adv360.keymap';s=p.read_text();start=s.index('layer_'+layer+' {')
        p.write_text(s[:start]+s[start:].replace(before,after,1))
    def test_production(self):self.assertEqual(validate(self.root),[])
    def test_toggle_num_rejected(self):
        self.change('base','&mo NUM','&tog NUM');self.assertTrue(validate(self.root))
    def test_unapproved_hold_tap_rejected(self):
        self.change('base','&kp G ','&mt LCTRL G ');self.assertTrue(validate(self.root))
    def test_hrm_mapping_required(self):
        self.change('base','&hml LGUI A ','&kp A ');self.assertTrue(validate(self.root))
    def test_left_shifted_grid_rejected(self):
        self.change('num','&kp KP_DIVIDE','&kp KP_N7');self.assertTrue(validate(self.root))
    def test_czech_number_row_rejected(self):
        self.change('num','&kp KP_N7','&kp N7');self.assertTrue(validate(self.root))
    def test_locale_sensitive_decimal_rejected(self):
        self.change('num','&kp DOT','&kp KP_DOT');self.assertTrue(validate(self.root))
    def test_thumb_zero_required(self):
        # Mutate by parsed binding position so formatting cannot skip the change.
        p=self.root/'config/adv360.keymap';s=p.read_text();start=s.index('layer_num {');end=s.index('>;',start)
        import re
        block=s[start:end]; matches=list(re.finditer(r'&[a-z_]+(?:\s+[A-Z][A-Z0-9_()]*)*',block))
        m=matches[70];block=block[:m.start()]+'&trans'+block[m.end():];p.write_text(s[:start]+block+s[end:])
        self.assertTrue(validate(self.root))
    def test_nav_shift_required(self):
        self.change('nav','&kp LSHFT','&kp LG(V)');self.assertTrue(validate(self.root))
    def test_nav_jkl_semicolon_contract(self):
        self.change('nav','&kp LEFT','&trans');self.assertTrue(validate(self.root))
    def test_nav_app_shortcut_bank_rejected(self):
        self.change('nav','&trans              &trans              &trans              &trans              &trans              &trans              &trans              &trans              &kp LG(UP)',
                    '&trans              &kp LG(A)           &trans              &trans              &trans              &trans              &trans              &trans              &kp LG(UP)')
        self.assertTrue(validate(self.root))
    def test_blocked_access_rejected(self):
        self.change('sys','&trans','&none');self.assertTrue(validate(self.root))
    def test_recovery_source_required(self):
        self.change('sys','&bootloader','&none');self.assertTrue(validate(self.root))
