#!/usr/bin/env python3
"""Generate physical layer PNGs from firmware and vendor geometry.

Rendering requires Pillow; --check and model validation use only Python 3.11+.
Use --font to override the system Arial / DejaVu Sans fallback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from render_keymap import ROOT, parse_layers, label
from validate_workflow import NUM_BLOCK, ORDER

OUT = ROOT / 'docs/layers'
GEOMETRY = 'config/boards/arm/adv360/adv360-layouts.dtsi'
SOURCES = ['config/adv360.keymap', 'config/macros.dtsi', GEOMETRY,
           'bin/render_layer_images.py', 'bin/render_keymap.py', 'bin/validate_workflow.py']
CONTEXTS = {name: [name, 'BASE'] for name in ORDER}
CONTEXTS['BASE'] = ['BASE']
NOTES = {
 'BASE': 'HRM: ASDF = Cmd / Option / Ctrl / Shift · JKL; = Shift / Ctrl / Option / Cmd',
 'NAV': 'Hold left middle thumb 52 · ASDF = Ctrl / Option / Cmd / Shift',
 'SYM': 'Hold right middle thumb 53 · symbols require ABC / US input',
 'NUM': 'Hold large left thumb 66 · keypad digits work in ABC and Czech',
 'SYS': 'Hold bottom-right key 75 · function, media, Bluetooth and recovery',
}
RGB = {'ON':'RGB on','OFF':'RGB off','TOG':'RGB toggle','HUD':'Hue −','HUI':'Hue +',
       'SAD':'Saturation −','SAI':'Saturation +','BRD':'RGB dimmer','BRI':'RGB brighter',
       'EFF':'Next effect','EFR':'Previous effect','SPD':'Effect slower','SPI':'Effect faster'}
KEY_NAMES = {'BSPC':'Backspace','DEL':'Delete','ENTER':'Enter','SPACE':'Space','ESC':'Escape',
 'TAB':'Tab','LSHFT':'Shift','RSHFT':'Shift','LCTRL':'Ctrl','RCTRL':'Ctrl','LGUI':'Cmd','RGUI':'Cmd',
 'LALT':'Option','RALT':'Option','LEFT':'←','DOWN':'↓','UP':'↑','RIGHT':'→','PG_UP':'Page up','PG_DN':'Page down',
 'C_PREV':'Previous track','C_NEXT':'Next track','C_PP':'Play / pause','C_VOL_DN':'Volume −','C_VOL_UP':'Volume +',
 'C_BRI_DN':'Screen dimmer','C_BRI_UP':'Screen brighter','C_STOP':'Media stop','C_MUTE':'Mute',
 'C_EJECT':'Eject','C_AL_CALC':'Calculator','C_AL_FILES':'Files','C_AC_SEARCH':'Search',
 'C_AL_LOCK':'Lock screen','GLOBE':'Globe','KP_NUM':'Num Lock','PSCRN':'Print screen','SLCK':'Scroll Lock',
 'PAUSE_BREAK':'Pause','K_APP':'Menu','CAPS':'Caps Lock'}
PALETTE = {'normal':('#edf2f8','#182d44'), 'digits':('#e1dcfb','#432776'),
 'operators':('#fff0d4','#754300'), 'modifiers':('#e1e8f0','#31475e'),
 'layers':('#d5eee5','#165444'), 'direction':('#d7eafa','#124e7b'),
 'inherited':('#f5f7f9','#71818e'), 'inactive':('#f7f8fa','#a4aeb7')}


def physical_keys(root=ROOT):
    source=(root/GEOMETRY).read_text()
    rows=re.findall(r'<&key_physical_attrs\s+([^>]+)>',source)
    result=[]
    for row in rows:
        values=[int(x) for x in re.findall(r'-?\d+', row)]
        if len(values)!=7: raise ValueError('Invalid vendor key geometry')
        w,h,x,y,rot,rx,ry=values
        result.append(dict(w=w,h=h,x=x,y=y,angle=rot/100,rx=rx,ry=ry))
    if len(result)!=76: raise ValueError('Vendor layout must contain 76 keys')
    return result


def rotate(x,y,g):
    a=math.radians(g['angle']); dx=x-g['rx']; dy=y-g['ry']
    return (g['rx']+dx*math.cos(a)-dy*math.sin(a),g['ry']+dx*math.sin(a)+dy*math.cos(a))


def generic_action(binding):
    parts=binding.split(); kind=parts[0]; args=parts[1:]
    if kind=='none': return 'Inactive'
    if kind=='kp': return KEY_NAMES.get(args[0],label(binding))
    if kind in ('hml','hmr'):
        return f"{KEY_NAMES.get(args[1],label('kp '+args[1]))} / hold {KEY_NAMES.get(args[0],args[0])}"
    if kind=='mo': return 'Hold '+args[0]
    if kind=='tog': return 'Toggle '+args[0]
    if kind=='to': return 'Select '+args[0]
    if kind=='oneshot_shift': return 'One-shot Shift'
    if kind=='caps_word': return 'Caps Word'
    if kind=='key_repeat': return 'Repeat'
    if kind=='mmv': return 'Pointer '+args[0].removeprefix('MOVE_').lower()
    if kind=='msc': return 'Scroll '+args[0].removeprefix('SCRL_').lower()
    if kind=='mkp': return {'LCLK':'Left click','RCLK':'Right click','MCLK':'Middle click'}[args[0]]
    if kind=='bt':
        if args[0]=='BT_SEL': return 'Select BT '+args[1]
        if args[0]=='BT_DISC': return 'Disconnect BT '+args[1]
        return {'BT_NXT':'Next BT profile','BT_PRV':'Previous BT profile','BT_CLR':'Clear selected bond'}[args[0]]
    if kind=='out': return {'OUT_USB':'USB output','OUT_BLE':'BLE output','OUT_TOG':'Toggle output'}[args[0]]
    if kind=='bl': return {'BL_TOG':'Backlight toggle','BL_DEC':'Backlight dimmer','BL_INC':'Backlight brighter'}[args[0]]
    if kind=='rgb_ug': return RGB[args[0].removeprefix('RGB_')]
    result=label(binding)
    if result==kind: raise ValueError('Missing behavior label: '+binding)
    return result


def source_fingerprint(root=ROOT):
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SOURCES}
    combined=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    return combined,hashes


def build_model(root=ROOT):
    layers=dict(parse_layers((root/'config/adv360.keymap').read_text()))
    if list(layers)!=ORDER or any(len(b)!=76 for b in layers.values()): raise ValueError('Unexpected layer structure')
    geometry=physical_keys(root)
    result=[]
    for name in ORDER:
        keys=[]
        for pos,raw in enumerate(layers[name]):
            origin=next(layer for layer in CONTEXTS[name] if layers[layer][pos]!='trans')
            effective=layers[origin][pos]; kind=effective.split()[0]
            inherited=raw=='trans'
            action=generic_action(effective)
            secondary=label(effective)
            category='normal'
            if kind in ('mo','to','tog'): category='layers'
            elif kind in ('hml','hmr','oneshot_shift') or effective in ['kp '+k for k in ('LGUI','RGUI','LCTRL','RCTRL','LALT','RALT','LSHFT','RSHFT')]: category='modifiers'
            elif effective in ('kp LEFT','kp RIGHT','kp UP','kp DOWN'): category='direction'
            elif re.fullmatch(r'kp (?:KP_)?N\d',effective): category='digits'
            elif effective.startswith('m_') or (len(action)==1 and not action.isalnum()): category='operators'
            if name in ('NAV',) and pos in (41,42,43,44): category='direction'
            if inherited: category='inherited'
            if kind=='none': category='inactive'
            keys.append(dict(position=pos,base=label(layers['BASE'][pos]),raw=raw,binding=effective,
                             origin=origin,inherited=inherited,action=action,signal=secondary,category=category,
                             highlight=(name=='NUM' and pos in NUM_BLOCK) or (name in ('NAV',) and pos in (41,42,43,44)),geometry=geometry[pos]))
        result.append(dict(name=name,context=CONTEXTS[name],keys=keys))
    return result


def render(output=OUT,font_path=None):
    from PIL import Image,ImageDraw,ImageFont
    model=build_model()
    candidates=[font_path] if font_path else ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    font_path=next((p for p in candidates if p and Path(p).exists()),None)
    if not font_path: raise ValueError('No font found; pass --font /path/to/font.ttf')
    fonts={}
    def font(size):
        if size not in fonts: fonts[size]=ImageFont.truetype(font_path,size)
        return fonts[size]
    def text(draw,xy,value,size=24,fill='#23384d',anchor=None):
        draw.text(xy,value,font=font(size),fill=fill,anchor=anchor)
    def fit(draw,value,width,size=24,minsize=12):
        while size>=minsize:
            lines=[]; line=''
            for word in value.split():
                candidate=(line+' '+word).strip()
                if draw.textlength(candidate,font=font(size))>width and line:
                    lines.append(line); line=word
                else: line=candidate
            if line: lines.append(line)
            if len(lines)<=3 and all(draw.textlength(line,font=font(size))<=width for line in lines): return lines,size
            size-=1
        raise ValueError('Label cannot fit without clipping: '+value)
    def single(draw,value,width,size):
        while draw.textlength(value,font=font(size))>width and size>8: size-=1
        if draw.textlength(value,font=font(size))>width: raise ValueError('Signal too wide: '+value)
        return size
    scale=1.18; pw,ph=2260,1300
    corners=[rotate(g['x']+dx,g['y']+dy,g) for g in physical_keys() for dx,dy in [(0,0),(g['w'],0),(g['w'],g['h']),(0,g['h'])]]
    minx=min(x for x,y in corners); maxx=max(x for x,y in corners)
    miny=min(y for x,y in corners); maxy=max(y for x,y in corners)
    ox=(pw-(maxx-minx)*scale)/2-minx*scale; oy=205-miny*scale
    if oy+maxy*scale>ph-135: raise ValueError('Geometry would overlap footer')
    fp,hashes=source_fingerprint()
    output.mkdir(parents=True,exist_ok=True)
    poster=Image.new('RGB',(pw*2+120,ph*((len(ORDER)+1)//2)+550),'#eaf0f5'); d=ImageDraw.Draw(poster)
    text(d,(60,40),'ADVANTAGE360 PRO',54)
    text(d,(62,110),'Five layers · macOS daily driver · ABC/US symbols',30)
    for j,(cat,caption) in enumerate([('digits','Digits'),('operators','Operators'),('modifiers','Modifiers'),('layers','Layer controls'),('direction','Directions'),('inherited','Inherited'),('inactive','Inactive')]):
        x=65+j*330
        d.rounded_rectangle((x,171,x+28,199),radius=6,fill=PALETTE[cat][0],outline='#a7b5c2')
        text(d,(x+42,170),caption,24)
    text(d,(65,225),'Small top label = position · base key. Faint keys show inherited actions; unused keys are inactive.',26)
    text(d,(65,268),'Other simultaneous layer combinations can differ. G = Cmd/GUI · C = Ctrl · A = Alt · S = Shift.',26)
    artifacts=[]
    for i,layer in enumerate(model):
        name=layer['name']; panel=Image.new('RGBA',(pw,ph),'white'); dr=ImageDraw.Draw(panel)
        dr.rounded_rectangle((0,0,pw-1,ph-1),radius=22,outline='#c9d7e3',width=2)
        text(dr,(50,32),f'{i:02d}  {name}',38)
        text(dr,(50,91),NOTES[name],25)
        text(dr,(50,137),'Shown context: '+' → '.join(layer['context']),20,fill='#6c7f90')
        for key in layer['keys']:
            g=key['geometry']; w=round(g['w']*scale)-7; h=round(g['h']*scale)-7
            tile=Image.new('RGBA',(w,h)); td=ImageDraw.Draw(tile); fill,ink=PALETTE[key['category']]
            td.rounded_rectangle((1,1,w-2,h-2),radius=9,fill=fill,outline=('#2984ae' if key['highlight'] else '#cbd7e2'),width=3 if key['highlight'] else 1)
            small=f"{key['position']} · {key['base']}"
            text(td,(8,7),small,single(td,small,w-16,13),fill='#6c7d8e')
            if key['category']=='inactive':
                text(td,(w/2,h/2+4),'—',24,fill=ink,anchor='mm')
            else:
                lines,size=fit(td,key['action'],w-16,26 if len(key['action'])<=2 else 21)
                lineheight=size+3
                center=h/2+2
                for n,line in enumerate(lines): text(td,(w/2,center+(n-(len(lines)-1)/2)*lineheight),line,size,fill=ink,anchor='mm')
                if name in ('GLOBAL','EDIT') and not key['inherited']:
                    sub=key['signal']; text(td,(w/2,h-13),sub,single(td,sub,w-12,11),fill='#596b7e',anchor='mm')
                elif key['inherited']:
                    text(td,(w/2,h-13),'from '+key['origin'],11,fill='#8b98a4',anchor='mm')
            # ZMK physical-layout rotation is clockwise in screen coordinates.
            rotated=tile.rotate(-g['angle'],resample=Image.Resampling.BICUBIC,expand=True)
            cx,cy=rotate(g['x']+g['w']/2,g['y']+g['h']/2,g)
            x=round(ox+cx*scale-rotated.width/2); y=round(oy+cy*scale-rotated.height/2)
            if x<0 or y<190 or x+rotated.width>pw or y+rotated.height>ph-120: raise ValueError('Key clipped: '+str(key['position']))
            panel.alpha_composite(rotated,(x,y))
        footer='Vendor physical geometry · key sizes and thumb angles preserved · drawing is not life-size'
        if name=='NUM': footer='U I O = 7 8 9   ·   J K L = 4 5 6   ·   M , . = 1 2 3   ·   Space thumb = 0   ·   / = decimal'
        if name=='SYS': footer='SYS: 0+13 clears selected bond · boot 6 left / 7 right · reset 20 left / 21 right'
        if name=='POINTER': footer='Hold a mouse button to drag; release to drop · no drag lock · modifiers remain available'
        if name=='GLOBAL': footer='macOS / AeroSpace actions · fullscreen substitutes for pin · clipboard helper requires host permissions'
        text(dr,(50,ph-91),footer,21,fill='#51697e')
        text(dr,(50,ph-51),'Source '+fp[:12]+' · inherited keys use the shown context',18,fill='#81909d')
        filename=f'{i:02d}-{name.lower()}.png'; panel.convert('RGB').save(output/filename); artifacts.append(filename)
        poster.paste(panel.convert('RGB'),(40+(i%2)*(pw+40),340+(i//2)*(ph+25)))
    text(d,(65,poster.height-44),'Generated from firmware and vendor geometry · source '+fp[:12],23,fill='#5c7387')
    poster.save(output/'all-layers.png'); artifacts.append('all-layers.png')
    with zipfile.ZipFile(output/'layer-images.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in artifacts: archive.write(output/name,name)
    artifacts.append('layer-images.zip')
    manifest={'fingerprint':fp,'sources':hashes,'layers':model,'font_sha256':hashlib.sha256(Path(font_path).read_bytes()).hexdigest(),
              'artifacts':{name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in artifacts}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print('Rendered 5 × 76 physical keys:',output/'all-layers.png')


def check(output=OUT):
    model=build_model(); fp,hashes=source_fingerprint()
    manifest=json.loads((output/'manifest.json').read_text())
    if manifest['fingerprint']!=fp or manifest['sources']!=hashes or manifest['layers']!=model:
        raise ValueError('Layer images are stale; regenerate with bin/render_layer_images.py')
    expected={f'{i:02d}-{name.lower()}.png' for i,name in enumerate(ORDER)}|{'all-layers.png','layer-images.zip'}
    if set(manifest['artifacts'])!=expected: raise ValueError('Incomplete layer image artifact set')
    for name,digest in manifest['artifacts'].items():
        if hashlib.sha256((output/name).read_bytes()).hexdigest()!=digest: raise ValueError('Image artifact changed: '+name)
    print('Layer images: 380 positions, contexts, command labels and source/artifact fingerprints verified')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true'); parser.add_argument('--font'); parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    if args.check: check(args.output)
    else: render(args.output,args.font)
