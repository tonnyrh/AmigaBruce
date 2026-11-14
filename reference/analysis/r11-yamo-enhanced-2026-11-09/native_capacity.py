from native import *
import json
key('F8');wait(lambda:front()==reference(enhanced=False,room_select=True))
key('F4');wait(lambda:front()==reference(enhanced=True,room_select=True))
tap_fire(cmd)
wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10)
time.sleep(2)
assert val(addr('enhanced_active'),1)
pause()
try:
    values={0x95:1,0x96:0,0x97:0,0x5d:255,0x5e:255,0x9e:96,0xa1:140,0xbf:0,0xce:0,0x4f4e:2}
    for i,col in enumerate((9,21,34)):
        values.update({0x4fde+i:1,0x4fe1+i:col-1,0x4fe4+i:11,0xd800+23*40+col:0xfd})
    for at,v in values.items():put(at,v)
finally:pause()
records=[];full=False;armed=False;blast=False
for i in range(30):
    pause()
    try:
        m=dump('capacity-ram.bin',ram,65536);step=val(addr('actor_logic_steps'),2)
        frame=dump('capacity-bg.bpl',val(addr('background'),4),40960)
    finally:pause()
    rec=dict(step=step,actors=list(m[0x95:0x98]),x=m[0x9e],y=m[0xa1],contact=m[0xb6],timers=list(m[0x4fde:0x4fe7]),target_attr=m[0xd800+17*40+21],target_code=m[0x8c00+17*40+21])
    records.append(rec)
    if all(m[0x4fde:0x4fe1]) and list(m[0x4fe4:0x4fe7])==[11]*3:
        assert rec['target_attr']==0xf8;full=True
    if any(m[0x4fde+k] and m[0x4fe1+k]==20 and m[0x4fe4+k]==8 for k in range(3)):
        assert full;armed=True
    if armed and 0x71<=rec['target_code']<=0x7c:
        blast=True;(q/'capacity-blast.bpl').write_bytes(frame);break
    if i%4==0:print(rec,flush=True)
(q/'native-capacity.json').write_text(json.dumps(dict(full_rejected=full,rearmed=armed,blast=blast,events=records),indent=2))
assert full and armed and blast
print('PASS native Enhanced: three occupied slots refuse a fourth bomb; walking contact arms it after release and the blast follows.',flush=True)
