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


@lru_cache
def reference(debug=False,players=1,human=False,infinite=False,invincible=False,room=0,loading=False,game_over=False):
    image=Image.new('P',(320,256))
    art=landscape()
    image.putpalette(art.getpalette())
    image.paste(art,(0,64 if loading else 4))
    d=ImageDraw.Draw(image)
    def text(x,y,string,color,heading=False):
        draw_text(d,x,y,string,color,heading)
    def rule(y):
        d.line((12,y,154,y),fill=5);d.line((165,y,307,y),fill=5)
        d.rectangle((158,y-1,161,y+1),fill=9)
    if loading:
        text(107,35,'MARTIAL ARTS',7,True);rule(181);text(129,196,'LOADING',12,True)
    else:
        text(20,114,'TEST OPTIONS' if debug else 'GAME OVER' if game_over else 'GAME SETUP',12,True)
        if debug:
            text(24,133,'F1  INFINITE FALLS',13);text(218,133,'ON' if infinite else 'OFF',11)
            text(24,148,'F2  INVINCIBLE',13);text(218,148,'ON' if invincible else 'OFF',11)
            text(24,163,'F3 F4  START ROOM',13);text(218,163,f'{room+1:02}',11)
            text(24,210,'F5 BACK',7);text(24,224,'IN GAME F1 F2 CHANGE ROOM',7)
        else:
            text(24,137,'F3  PLAYERS',13);text(218,137,str(players),11)
            text(24,154,'F5  YAMO',13);text(218,154,'JOYSTICK 1' if human else 'COMPUTER',11)
            text(24,210,'SHIFT D TEST OPTIONS',7)
            text(24,224,'TAKE TURNS   1P JOY 2   2P JOY 1',7)
        rule(179);text(91,190,'FIRE OR RETURN TO START',13)
        text(24,241,'ESC AMIGADOS',6);text(248,241,'P PAUSE',6)
    return planar(image)
