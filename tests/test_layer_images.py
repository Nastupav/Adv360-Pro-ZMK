import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bin'))
import render_layer_images as images
class LayerImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.layers={x['name']:x for x in images.build_model()}
    def test_geometry(self):
        g=images.physical_keys();self.assertEqual(len(g),76)
        self.assertEqual([i for i,k in enumerate(g) if k['h']==200],[65,66,69,70])
        self.assertEqual(g[35]['angle'],15);self.assertEqual(g[37]['angle'],-15)
    def test_num_effective_thumb_bindings(self):
        k=self.layers['NUM']['keys']
        self.assertEqual((k[66]['binding'],k[66]['origin']),('mo NUM','BASE'))
        self.assertEqual(k[70]['binding'],'kp KP_N0')
        self.assertEqual(k[69]['binding'],'kp ENTER')
    def test_base_hrm_anchors(self):
        k=self.layers['BASE']['keys']
        self.assertEqual([k[i]['binding'] for i in range(29,33)],
                         ['hml LGUI A','hml LALT S','hml LCTRL D','hml LSHFT F'])
        self.assertEqual([k[i]['binding'] for i in range(41,45)],
                         ['hmr RSHFT J','hmr RCTRL K','hmr RALT L','hmr RGUI SEMI'])
    def test_nav_anchors(self):
        k=self.layers['NAV']['keys']
        self.assertEqual([k[i]['binding'] for i in range(41,45)],['kp LEFT','kp DOWN','kp UP','kp RIGHT'])
        self.assertEqual([k[i]['action'] for i in range(29,33)],['Ctrl','Option','Cmd','Shift'])
    def test_system_no_accidental_letters(self):
        self.assertEqual(self.layers['SYS']['keys'][33]['action'],'Inactive')
        self.assertEqual(self.layers['SYS']['keys'][6]['binding'],'bootloader')
        self.assertEqual(self.layers['SYS']['keys'][7]['binding'],'bootloader')
