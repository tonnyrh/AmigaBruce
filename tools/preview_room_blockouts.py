"""Own prototype geometry preview, not original C64 artwork."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def main():
    rooms=json.loads((ROOT/'reference/validation/room-blockouts.json').read_text())['rooms']
    first=[dict(room=1,platforms=[[0,320,196],[0,208,101],[248,320,98],[0,32,128],[56,96,152],[200,320,146]],nets=[[144,168,104,164,101]]),
           dict(room=2,platforms=[[0,320,196],[0,80,98],[120,144,101],[176,200,101],[240,320,98],[0,128,146],[192,320,146],[152,168,146]],nets=[[152,168,148,180,146]])]
    facts=json.loads((ROOT/'reference/validation/candidate-rooms.json').read_text())['rooms']
    sheet=Image.new('RGB',(4*336,5*244),'#001111');d=ImageDraw.Draw(sheet)
    for i,r in enumerate(first+rooms):
        x=i%4*336+8;y=i//4*244+24
        d.rectangle((x,y,x+319,y+201),fill='#334455')
        d.text((x,y-17),f"ROOM {i+1:02} - PROVISIONAL",fill='#eeeeaa')
        for a,b,top,bottom,_ in r['nets']:
            for col in range(a,b,6):d.line((x+col,y+top,x+col,y+bottom),fill='#77aabb')
            for row in range(top,bottom,6):d.line((x+a,y+row,x+b,y+row),fill='#77aabb')
        for a,b,h in r['platforms']:d.line((x+a,y+h,x+b-1,y+h),fill='#dd9966',width=2)
        for lamp in facts[i]['lanterns']:
            left=x+lamp['column']*8-4;top=y+lamp['row']*16-8
            d.rectangle((left,top,left+5,top+9),fill='#ffdd55')
        sx=x+facts[i]['entry_x'];sy=y+facts[i]['entry_y']
        d.ellipse((sx-3,sy-6,sx+3,sy),fill='#66ff88')
    path=ROOT/'docs/images/rooms20-layout.png';sheet.save(path);print(path)


if __name__=='__main__':main()
