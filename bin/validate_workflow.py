#!/usr/bin/env python3
"""Validate the daily-driver physical contract, return paths and layer precedence."""
from pathlib import Path
import re
from render_keymap import parse_layers
ROOT=Path(__file__).resolve().parents[1]
ORDER=['BASE','NAV','SYM','NUM','SYS']
NUM_BLOCK={22:'KP_DIVIDE',23:'KP_N7',24:'KP_N8',25:'KP_N9',26:'KP_MULTIPLY',27:'COMMA',
           40:'KP_MINUS',41:'KP_N4',42:'KP_N5',43:'KP_N6',44:'KP_PLUS',45:'KP_EQUAL',
           54:'KP_N0',55:'KP_N1',56:'KP_N2',57:'KP_N3',58:'DOT',68:'BSPC',70:'KP_N0'}
ACCESS={52:'NAV',53:'SYM',66:'NUM',75:'SYS'}
MODS={34:'LALT',35:'LCTRL',36:'LGUI',37:'RGUI',38:'RCTRL',39:'RALT',46:'LSHFT',59:'RSHFT'}

def resolve(layers, active, pos):
    for name in reversed(ORDER):
        if name=='BASE' or name in active:
            binding=layers[name][pos]
            if binding!='trans': return binding
    raise ValueError(f'No base binding at {pos}')

def validate(root=ROOT):
    source=(root/'config/adv360.keymap').read_text()
    layers=dict(parse_layers(source)); errors=[]
    if list(layers)!=ORDER or any(len(b)!=76 for b in layers.values()):
        return ['Expected five ordered 76-position layers']
    def expect(layer,pos,binding):
        if layers[layer][pos]!=binding: errors.append(f'{layer}[{pos}]: expected {binding}, got {layers[layer][pos]}')
    for positions,letters in [(range(15,20),'QWERT'),(range(22,27),'YUIOP'),(range(29,34),'ASDFG'),
                              (range(40,44),'HJKL'),(range(47,52),'ZXCVB'),(range(54,56),'NM')]:
        for pos,letter in zip(positions,letters):expect('BASE',pos,'kp '+letter)
    for pos,key in {44:'SEMI',56:'COMMA',57:'DOT',58:'FSLH',14:'TAB',28:'ESC',65:'BSPC',67:'DEL',68:'DEL',69:'ENTER',70:'SPACE',**MODS}.items():
        expect('BASE',pos,'kp '+key)
    for pos,layer in ACCESS.items():
        expect('BASE',pos,'mo '+layer)
        for overlay in ORDER[1:]:expect(overlay,pos,'trans')
    for pos,key in zip((29,30,31,32),('LCTRL','LALT','LGUI','LSHFT')):expect('NAV',pos,'kp '+key)
    for pos,key in zip((41,42,43,44),('LEFT','DOWN','UP','RIGHT')):expect('NAV',pos,'kp '+key)
    for pos,key in NUM_BLOCK.items():expect('NUM',pos,'kp '+key)
    for layer in ORDER[1:]:
        for pos in MODS:expect(layer,pos,'trans')
        for pos in [14,28]:expect(layer,pos,'trans')
    # Every combination retains entry/release controls and all dedicated modifiers.
    for mask in range(16):
        active={name for i,name in enumerate(ORDER[1:]) if mask & (1<<i)}
        for pos,layer in ACCESS.items():
            if resolve(layers,active,pos)!='mo '+layer:errors.append(f'{active}: blocked {layer} access')
        for pos,key in MODS.items():
            if resolve(layers,active,pos)!='kp '+key:errors.append(f'{active}: blocked modifier {key}')
    for layer in ORDER:
        for b in layers[layer]:
            if b.split()[0] in ('lt','mt','tog','sk','sl','oneshot_shift'):
                errors.append(f'{layer}: timing/latching behavior {b}')
    # Distinct physical sources are required for left/right bootloader routing.
    for pos,b in {6:'bootloader',7:'bootloader',20:'sys_reset',21:'sys_reset',64:'to BASE'}.items():expect('SYS',pos,b)
    required=set('LPAR RPAR LBKT RBKT LBRC RBRC LT GT SQT DQT GRAVE COLON SEMI COMMA DOT UNDER EQUAL PLUS MINUS ASTRK FSLH BSLH PIPE DLLR AT HASH PRCNT AMPS EXCL QMARK CARET TILDE'.split())
    present={b[3:] for b in layers['SYM'] if b.startswith('kp ')}
    if required-present:errors.append('Missing SYM symbols: '+str(required-present))
    if not re.search(r'&caps_word\s*\{[^}]*KP_N0[^}]*KP_N9',source,re.S):errors.append('Caps Word must continue keypad digits')
    return errors

if __name__=='__main__':
    errors=validate()
    if errors:raise SystemExit('\n'.join(errors))
    print('Workflow: plain QWERTY, exact NUM/JKL; grid, modifier access, recovery and all 16 layer combinations pass')
