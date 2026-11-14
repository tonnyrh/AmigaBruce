from native import *
from enhanced_architecture import foreground,masonry
from build_enhanced_art import RGB
from PIL import Image,ImageDraw
import json

def expected(m,c,t):
    pix=[];r=m[0x29];base=0xa000 if r<10 else 0xa800
    for dy in range(32):
        y=(2*t-3)*8+dy
        for dx in range(24):
            x=(c-1)*8+dx;cell=y//8*40+x//8;code=m[0x8c00+cell]
            bits=m[base+code*8+y%8];pair=(bits>>(6-2*((x%8)//2)))&3
            pen=foreground(r,code&127,x%8,(code>>7)*8+y%8,pair) if code&127 else None
            pix.append(masonry(x,y,False) if pen is None else pen)
    return bytes(pix)

def region(b,c,t):
    if len(b)!=40960:return b''
    return bytes(sum(((b[(32+y)*160+x//8+p*40]>>(7-x%8))&1)<<p for p in range(4))
                 for y in range((2*t-3)*8,(2*t-3)*8+32) for x in range((c-1)*8,(c-1)*8+24))

key('F8');wait(lambda:front()==reference(room_select=True))
key('F4');wait(lambda:front()==reference(enhanced=True,room_select=True))
tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10)
records=[];gallery=[]
for room in (11,8):
    if room==8:
        for _ in range(3):key('F9');time.sleep(.5)
        tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==7)
    pause()
    try:
        for at,v in {0x95:0,0x96:0,0x97:0,0x5d:255,0x5e:255}.items():put(at,v)
        m=dump(f'room-{room}-art.bin',ram,65536)
    finally:pause()
    assert val(addr('enhanced_active'),1)
    assert not any(m[0x4fde:0x4fe1])
    bombs=[(i%40,(i//40+1)//2) for i in range(120,1000) if m[0x8c00+i]==0x60]
    for col,row in bombs:
        wanted=expected(m,col,row)
        wait(lambda:region(front(),col,row)==wanted,20)
        frame=front()
        (q/f'room-{room}-bomb-{col}-{row}.bpl').write_bytes(frame)
        records.append(dict(room=room,column=col,row=row,pixels=768,match=True))
    col,row=(21,9) if room==11 else (29,4)
    observed=region(front(),col,row);assert observed==expected(m,col,row)
    image=Image.new('RGB',(24,32));image.putdata([RGB[i] for i in observed])
    gallery.append((room,image))
    print('Room',room,':',len(bombs),'idle charge regions match the new art.',flush=True)

sheet=Image.new('RGB',(340,225),(24,28,34));draw=ImageDraw.Draw(sheet)
for i,(room,img) in enumerate(gallery):
    draw.text((14+170*i,10),f'Room {room} - WinUAE',(230,230,230))
    sheet.paste(img.resize((120,160),Image.Resampling.NEAREST),(24+170*i,38))
out=Path('reference/analysis/bomb-margin-2026-11-09')
sheet.save(out/'charges.png')
(q/'art.json').write_text(json.dumps(records,indent=2)+'\n')
