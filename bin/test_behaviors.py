#!/usr/bin/env python3
"""Exercise production bindings in the pinned ZMK native_posix_64 simulator.

Four physical positions per scenario; all five layers retained. SYS hardware
controls and the Bluetooth-clear combo are intentionally not invoked. Tests
cover key/HID events, not physical scanning, host repeat or USB/BLE transport.
"""
import argparse,re,subprocess
from pathlib import Path
from render_keymap import parse_layers
ROOT=Path(__file__).resolve().parents[1]

def fixture(positions,events):
    source=(ROOT/'config/adv360.keymap').read_text()
    layers=parse_layers(source)
    layer_defines='\n'.join(re.findall(r'^#define\s+(?:BASE|NAV|SYM|NUM|SYS)\s+\d+\s*$',source,re.M))
    timing_defines='\n'.join(re.findall(r'^#define\s+HRM_(?:TAPPING_TERM|QUICK_TAP|PRIOR_IDLE)_MS\s+\d+\s*$',source,re.M))
    def source_positions(name):
        raw=re.search(rf'^#define\s+{name}\s+(.+)$',source,re.M)[1]
        return {int(x) for x in re.findall(r'\d+',raw)}
    groups={name:source_positions(name) for name in ('KEYS_L','KEYS_R','THUMBS')}
    # The native fixture remaps selected production positions to 0..N-1. Remap
    # positional-HRM trigger sets too so same/cross-hand behavior stays realistic.
    pos_defines=[]
    for name,original in groups.items():
        slots=[i for i,p in enumerate(positions) if p in original]
        pos_defines.append(f'#define {name} '+(' '.join(map(str,slots)) if slots else '99'))
    caps=re.search(r'&caps_word\s*\{.*?\};',source,re.S)[0]
    behaviors=re.search(r'\n    behaviors \{(.*?)\n    \};\n\n    combos',source,re.S)[1]
    text='#include <behaviors.dtsi>\n#include <dt-bindings/zmk/keys.h>\n#include <dt-bindings/zmk/kscan_mock.h>\n'+layer_defines+'\n'+timing_defines+'\n'+'\n'.join(pos_defines)+'\n'+caps
    text+='\n/ { behaviors {'+behaviors+'\n}; keymap { compatible = "zmk,keymap";\n'
    for i,(_,bindings) in enumerate(layers):
        text+=f'layer_{i} {{ bindings = <'+' '.join('&none' if i==4 else '&'+bindings[p] for p in positions)+'>; };\n'
    text+='}; };\n&kscan { events = <\n'
    for action,slot,delay in events:text+=f'ZMK_MOCK_{action}({slot//2},{slot%2},{delay})\n'
    return text+'>; };\n'

def tap(slot,delay=10):return [('PRESS',slot,delay),('RELEASE',slot,delay)]
def press(slot,delay=10):return [('PRESS',slot,delay)]
def release(slot,delay=10):return [('RELEASE',slot,delay)]

def run(zmk,output):
    cases={
        'plain-asdf':((29,30,31,32),sum((tap(i,1) for i in range(4)),[]),['0x04','0x16','0x07','0x09']),
        'plain-jkl-semi':((41,42,43,44),sum((tap(i,1) for i in range(4)),[]),['0x0D','0x0E','0x0F','0x33']),
        # Same-hand rolls must remain taps; l-i mirrors the open Kinesis HRM issue.
        'hrm-fast-roll-as':((29,30,40,41),press(0,1)+press(1,25)+release(0,25)+release(1,25),['0x04','0x16']),
        'hrm-fast-roll-li':((43,24,29,40),press(0,1)+press(1,25)+release(0,25)+release(1,25),['0x0F','0x0C']),
        # Opposite-hand interrupt should turn A into Command while H remains H.
        'hrm-cross-hand-cmd':((29,40,30,41),press(0,1)+press(1,25)+release(1,25)+release(0,25),['0xE3','0x0B']),
        # Digit is held 1 second; releasing NUM first must release the same usage.
        'num-hold-release':((66,23,70,28),press(0,1)+press(1,1000)+release(0,1)+release(1)+tap(1)+press(0)+tap(2)+tap(3)+tap(1)+release(0)+tap(2),
                            ['0x5F','0x18','0x62','0x29','0x5F','0x2C']),
        # Cmd+Shift+Left remains a balanced chord when NAV releases first.
        'nav-selection-release':((52,31,32,41),press(0,1)+press(1,1)+press(2,1)+press(3)+release(0)+release(3)+release(2)+release(1)+tap(1),
                                  ['0xE3','0xE1','0x50','0x07']),
        'layer-precedence':((66,53,52,41),press(2)+press(1)+press(0)+tap(3)+release(0)+tap(3)+release(1)+tap(3)+release(2)+tap(3)
                            +press(0)+press(1)+press(2)+tap(3)+release(2)+release(1)+release(0),
                            ['0x5C','0x2D','0x50','0x0D','0x5C']),
        'caps-keypad':((20,29,66,41),tap(0)+tap(1)+press(2)+tap(3)+release(2)+tap(1)+tap(0)+tap(1),
                       ['0x04','0x5C','0x04','0x04']),
        'immediate-shift':((46,32,52,41),press(0,1)+press(1,1)+release(1)+release(0)+press(2)+press(3)+release(3)+release(2),
                            ['0xE1','0x09','0x50']),
    }
    for name,(positions,events,expected) in cases.items():
        config=output/'tests'/name;config.mkdir(parents=True,exist_ok=True)
        (config/'native_posix_64.keymap').write_text(fixture(positions,events))
        (config/'native_posix_64.conf').write_text('CONFIG_GPIO=n\nCONFIG_ZMK_BLE=n\nCONFIG_LOG=y\nCONFIG_LOG_BACKEND_SHOW_COLOR=n\nCONFIG_ZMK_LOG_LEVEL_DBG=y\n')
        build=output/'build'/name
        with (config/'build.log').open('w') as log:
            result=subprocess.run(['west','build','-s',str(zmk),'-b','native_posix_64','-p','-d',str(build),'--','-DCONFIG_ASSERT=y',f'-DZMK_CONFIG={config}'],stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'{name}: build failed; see {config}/build.log')
        result=subprocess.run([str(build/'zephyr/zmk.exe')],capture_output=True,text=True,timeout=30,check=True)
        log=result.stdout+result.stderr;(config/'events.log').write_text(log)
        pressed=re.findall(r'hid_listener_keycode_pressed: usage_page 0x07 keycode (0x[0-9A-F]+)',log)
        released=re.findall(r'hid_listener_keycode_released: usage_page 0x07 keycode (0x[0-9A-F]+)',log)
        if pressed!=expected or sorted(pressed)!=sorted(released):raise AssertionError(f'{name}: incorrect/unbalanced events {pressed} / {released}')
        if name=='nav-selection-release':
            report=log.split('hid_listener_keycode_pressed: usage_page 0x07 keycode 0x50',1)[1].split('zmk_endpoints_send_report:',1)[0]
            if 'Modifiers set to 0x0A' not in report:raise AssertionError('Cmd+Shift not held with Left')
        if name=='caps-keypad':
            reports=[s.split('zmk_endpoints_send_report:',1)[0] for s in log.split('hid_listener_keycode_pressed: usage_page 0x07 keycode 0x04')[1:]]
            if not all('Modifiers set to 0x02' in s for s in reports[:2]) or 'Modifiers set to 0x02' in reports[2]:
                raise AssertionError('Caps Word did not continue across keypad input or toggle off')
        print(f'PASS pinned ZMK events: {name}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zmk',type=Path,default=Path('/app/zmk/app'))
    p.add_argument('--output',type=Path,default=ROOT/'firmware/behavior-tests')
    a=p.parse_args();run(a.zmk.resolve(),a.output.resolve())
