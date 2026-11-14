"""Expected visible images for the live OCS title/menu publication checks."""
import re
from functools import lru_cache
from PIL import Image, ImageDraw
from build_title_art import ROOT, landscape, alphabet, planar


@lru_cache
def body_font():
    source=(ROOT/'amiga/main.c').read_text(encoding='utf-8')
    def letters(name):
        table=re.search(name+r'\[\d+\]\[7\]=\{(.*?)\};',source,re.S)[1]
        return [list(map(int,re.findall(r'\d+',row))) for row in re.findall(r'\{([^{}]+)\}',table)]
    body=dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',letters('glyphs')))
    body.update(zip('0123456789',letters('digits')))
    return body


def draw_text(d,x,y,string,color,heading=False):
    font=dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',alphabet())) if heading else body_font()
    for char in string:
        for row,bits in enumerate(font.get(char,())):
            for col in range(7 if heading else 5):
                if bits & ((128 if heading else 16)>>col):d.point((x+col,y+row),color)
        x+=9 if heading else 6


def notice_reference(label):
    image=Image.new('P',(320,256))
    draw_text(ImageDraw.Draw(image),(320-len(label)*6)//2,124,label,7)
    return planar(image)

def draw_room_map(image,room,top,charset=None):
    assets=ROOT/'assets/c64/rooms-v1'
    cells=(assets/'rooms.bin').read_bytes()[room*440:(room+1)*440]
    if charset is None:charset=(assets/'charsets.bin').read_bytes()
    bank=0 if room<10 else 4096 if room==18 else 2048
    for i,raw in enumerate(cells):
        for y in range(8):
            code=(raw&127)+(128 if y>=4 else 0)
            bits=charset[bank+code*8+(y%4)*2]
            for x in range(4):
                image.putpixel((80+i%40*4+x,top+i//40*8+y),(0,5,12,7)[(bits>>(6-2*x))&3])

def picker_reference(room,charset):
    image=Image.new('P',(320,256));d=ImageDraw.Draw(image)
    draw_text(d,139,42,f'ROOM {room+1:02}',1)
    draw_room_map(image,room,60,charset)
    draw_text(d,76,168,'F9 PREVIOUS     F10 NEXT',1)
    draw_text(d,106,188,'FIRE TO ENTER ROOM',7)
    draw_text(d,88,221,'F8 MENU    ESC AMIGADOS',12)
    return planar(image)


@lru_cache
def reference(debug=False,players=1,human=False,infinite=False,invincible=False,room=0,loading=False,game_over=False,enhanced=False,room_select=False):
    image=Image.new('P',(320,256))
    art=landscape()
    image.putpalette(art.getpalette())
    if debug and room_select:draw_room_map(image,room,12)
    else:image.paste(art,(0,64 if loading else 4))
    d=ImageDraw.Draw(image)
    def text(x,y,string,color,heading=False):
        draw_text(d,x,y,string,color,heading)
    def rule(y):
        d.line((12,y,154,y),fill=5);d.line((165,y,307,y),fill=5)
        d.rectangle((158,y-1,161,y+1),fill=9)
    if loading:
        rule(181)
        text(129,196,'LOADING',12,True)
    else:
        text(20,114,'TEST OPTIONS' if debug else 'GAME OVER' if game_over else 'GAME SETUP',12,True)
        if debug:
            text(24,129,'F1  INFINITE FALLS',13);text(218,129,'ON' if infinite else 'OFF',11)
            text(24,143,'F2  INVINCIBLE',13);text(218,143,'ON' if invincible else 'OFF',11)
            text(24,157,'F3  ROOM SELECT',13);text(218,157,'ON' if room_select else 'OFF',11)
            text(24,171,'F9 F10  START ROOM',13);text(218,171,f'{room+1:02}',11)
            text(24,210,'F5 BACK',7);text(24,224,'F9 PREVIOUS  F10 NEXT  F8 MENU',7)
        else:
            text(24,137,'F3  PLAYERS',13);text(218,137,str(players),11)
            text(24,154,'F5  YAMO',13);text(218,154,'JOYSTICK 1' if human else 'COMPUTER',11)
            text(24,168,'F4  LOOK',13);text(218,168,'ENHANCED' if enhanced else 'CLASSIC',11)
            text(24,210,'SHIFT D TEST OPTIONS',7)
            text(24,224,'TAKE TURNS   1P JOY 2   2P JOY 1',7)
        rule(183 if debug else 179);text(106 if room_select else 91,190,'FIRE TO ENTER ROOM' if room_select else 'FIRE OR RETURN TO START',13)
        text(24,241,'ESC AMIGADOS',6);text(248,241,'P PAUSE',6)
    return planar(image)
