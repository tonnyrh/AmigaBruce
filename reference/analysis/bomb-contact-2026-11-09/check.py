from native import *
import json
wait(lambda:front()==reference())
key('F4');wait(lambda:front()==reference(enhanced=True))
cmd('EVT KEY_SHIFT_LEFT 1');key('D');cmd('EVT KEY_SHIFT_LEFT 0')
wait(lambda:front()==reference(debug=True))
key('F1');key('F2')
for n in range(1,11):
    key('F10');title=reference(debug=True,invincible=True,infinite=True,room_select=True,room=n)
    wait(lambda:front()[110*160:]==title[110*160:],15)
tap_fire(cmd)
wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10)
time.sleep(2)

from build_enhanced_art import RGB
from PIL import Image
records=[]
for look in ('enhanced','classic'):
    if look=='classic':
        key('F8');wait(lambda:front()==reference(enhanced=True,room_select=True))
        key('F4');wait(lambda:front()==reference(enhanced=False,room_select=True))
        tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10);time.sleep(2)
    assert bool(val(addr('enhanced_active'),1))==(look=='enhanced')
    for height in (139,140):
        # Controlled placement, then normal joystick motion. All timers are free.
        pause()
        try:
            m=dump('before.bin',ram,65536)
            assert list(m[0x4fde:0x4fe1])==[0,0,0]
            assert m[0x8c00+17*40+21]==0x60 and m[0xd800+17*40+21]==0xf8
            for at,v in {0x95:1,0x96:0,0x97:0,0x5d:255,0x5e:255,0x9e:106,0xa1:height,0xa4:0,0xbf:0,0xce:0,0x4f4e:2,0x4f48:2}.items():put(at,v)
            cmd('EVT JOY2_LEFT 1')
        finally:pause()
        events=[];captured=False;blast=False;armed=False;end=time.monotonic()+35
        while time.monotonic()<end:
            pause()
            try:
                m=dump('ram.bin',ram,65536);step=val(addr('actor_logic_steps'),2)
                # Sample live source coordinates and timer ownership.
                rec=dict(step=step,x=m[0x9e]*2-24,y=m[0xa1],state=m[0xbf],pose=m[0x4f4e],contact=m[0xb6],object_row=m[0xe9],timers=list(m[0x4fde:0x4fe7]),code=m[0x8c00+17*40+21])
                if 150<=rec['x']<=170 and not captured:
                    (q/f'{look}-y{height}-contact.bpl').write_bytes(front());captured=True
                    (q/f'{look}-y{height}-contact.bin').write_bytes(m)
                if any(m[0x4fde+k] and m[0x4fe1+k]==20 and m[0x4fe4+k]==8 for k in range(3)):armed=True
                if 0x71<=rec['code']<=0x7c:blast=True
                if rec['x']<125:cmd('EVT JOY2_LEFT 0')
            finally:pause()
            events.append(rec)
            if rec['x']<125 and (height==139 or (blast and not any(m[0x4fde:0x4fe1]))):break
        cmd('EVT JOY2_LEFT 0')
        record=dict(mode=look,initial_y=height,armed=armed,blast=blast,captured=captured,events=events)
        records.append(record);(q/'native-walks.json').write_text(json.dumps(records,indent=2))
        assert rec['x']<125 and armed==(height==140),(look,height,record)
        if height==140:assert blast
        print(look,'initial height',height,'armed',armed,'blast',blast,flush=True)
