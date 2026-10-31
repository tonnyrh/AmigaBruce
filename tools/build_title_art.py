"""Draw the Bruce title frieze and bake it into an OCS interleaved bitmap.

Original landscape and Latin brush alphabet. The figure is the project's
frozen C64 extraction, Bruce pose $0C facing right (see sprites-v1/manifest).
"""
from pathlib import Path
from PIL import Image, ImageDraw
from build_fighter_dma import pack, unpack

ROOT = Path(__file__).resolve().parents[1]
COLORS = (0x112, 0x223, 0x334, 0x445, 0x657, 0x876, 0xA98, 0xCBA,
          0x822, 0xB43, 0xE64, 0xFA7, 0xFC9, 0xFED, 0x222, 0xDC9)

# Strokes on a seven by nine grid, from the loaded brush to the lifted tip.
STROKES = {
    'A': ('08 40 68', '15 55'), 'B': ('08 10 50 61 53 14', '24 54 66 57 08'),
    'C': ('61 50 20 02 06 18 48 67',), 'D': ('08 10 40 62 65 47 08',),
    'E': ('60 10 08 58', '14 54'), 'F': ('08 10 60', '14 54'),
    'G': ('61 50 20 02 06 18 48 66 64 34',), 'H': ('10 08', '60 58', '14 64'),
    'I': ('10 60', '40 28', '08 58'), 'J': ('20 60 56 38 18 06',),
    'K': ('10 08', '60 14 58'), 'L': ('10 08 58',),
    'M': ('08 10 34 60 58',), 'N': ('08 10 57 60',),
    'O': ('20 50 62 56 38 18 06 12 20',), 'P': ('08 10 50 61 53 14',),
    'Q': ('20 50 62 56 38 18 06 12 20', '45 68'),
    'R': ('08 10 50 61 53 14', '34 68'),
    'S': ('61 50 20 02 13 54 66 57 28 07',),
    'T': ('00 60', '40 28'), 'U': ('10 06 17 37 56 60',),
    'V': ('00 28 60',), 'W': ('00 18 34 48 60',), 'X': ('10 58', '60 08'),
    'Y': ('00 34 60', '34 28'), 'Z': ('00 60 08 58',),
}


def stroke_letter(draw, letter, x, y, sx, sy, width, color):
    for path in STROKES[letter]:
        points = [(round(x + int(p[0])*sx), round(y + int(p[1])*sy)) for p in path.split()]
        draw.line(points, fill=color, width=width)
        if width > 2:
            a, b = points[-1]
            draw.polygon([(a-width//2, b), (a+width//2, b-1), (a+width, b-3)], fill=color)


def landscape():
    image = Image.new('P', (320, 104), 2)
    image.putpalette([((c >> s) & 15)*17 for c in COLORS for s in (8, 4, 0)] + [0]*720)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 24, 319, 62), fill=3)
    d.rectangle((0, 63, 319, 103), fill=4)
    d.ellipse((210, 7, 264, 61), fill=10)
    for y, left, right in [(41, 210, 264), (47, 209, 250), (52, 234, 263)]:
        d.line((left, y, right, y), fill=3)
    d.polygon([(0,49),(18,41),(30,45),(51,27),(63,36),(79,21),(98,39),(107,34),
               (131,52),(157,34),(174,43),(196,24),(219,48),(233,35),(255,53),
               (281,26),(300,41),(319,32),(319,104),(0,104)],fill=4)
    d.polygon([(0,68),(24,48),(42,56),(68,38),(88,49),(97,44),(125,64),(150,50),
               (180,65),(206,48),(231,68),(252,57),(270,62),(300,42),(319,55),
               (319,104),(0,104)],fill=5)
    for x,y,w in [(12,62,40),(38,67,30),(112,63,34),(160,66,34),(265,64,32)]:
        d.line((x,y,x+w,y),fill=6)
    # A pavilion with upturned eaves, seen across the valley.
    for x,y,w in [(177,53,10),(177,60,15),(177,68,20)]:
        d.rectangle((x-w//3,y+1,x+w//3,y+7),fill=2)
        d.polygon([(x-w,y-2),(x-w+3,y),(x-3,y-5),(x,y-8),(x+3,y-5),
                   (x+w-3,y),(x+w,y-2),(x+w-2,y+2),(x-w+2,y+2)],fill=2)
    d.polygon([(0,87),(30,78),(78,85),(103,79),(133,86),(173,71),(185,72),
               (209,84),(235,79),(270,64),(299,70),(319,61),(319,104),(0,104)],fill=1)
    # Dry ink behind the lettering, with broken ends rather than a solid box.
    d.polygon([(0,23),(33,16),(115,14),(142,18),(160,16),(146,21),(169,23),
               (153,30),(163,30),(150,38),(157,38),(143,46),(148,47),
               (123,55),(78,57),(46,55),(0,62)],fill=0)
    for x,y,w in [(12,16,31),(59,12,40),(118,13,13),(8,62,36),(104,55,21)]:
        d.line((x,y,x+w,y-1),fill=1)
    for i,letter in enumerate('BRUCE'):
        stroke_letter(d,letter,12+i*28,22,3.15,3.8,5,13)
    d.polygon([(17,60),(75,57),(135,54),(119,58),(56,62),(21,62)],fill=9)
    # Decorative red seal with a simple geometric lattice.
    d.rectangle((142,54,154,68),fill=8)
    d.rectangle((144,56,152,66),outline=12)
    d.line([(147,56),(147,63),(150,63),(150,59)],fill=12)
    # Dark cliff and a bamboo branch in the foreground.
    d.polygon([(193,103),(212,91),(233,89),(242,84),(266,83),(279,77),
               (297,81),(319,73),(319,104)],fill=0)
    d.line([(300,90),(308,55),(312,27),(317,0)],fill=1,width=3)
    for x,y,dx,dy in [(312,27,-17,-12),(313,24,-8,-18),(308,52,-24,-14),
                      (308,55,-12,-17),(311,34,8,-8),(307,57,12,-9)]:
        d.polygon([(x,y),(x+dx//2-2,y+dy//2+1),(x+dx,y+dy),
                   (x+dx//2+2,y+dy//2-2)],fill=1)
    pose = Image.open(ROOT/'assets/c64/sprites-v1/bruce-0c-f1.png').convert('RGBA')
    pose = pose.crop(pose.getbbox())
    pose = pose.resize((pose.width*3,pose.height*3),Image.Resampling.NEAREST)
    for y in range(pose.height):
        for x in range(pose.width):
            r,_,_,alpha=pose.getpixel((x,y))
            if alpha:image.putpixel((218+x,23+y),0 if not r else 12)
    d.rectangle((0,100,319,103),fill=0)
    d.line((8,100,311,100),fill=5)
    return image


def planar(image):
    width,height=image.size
    out=bytearray()
    for y in range(height):
        row=image.crop((0,y,width,y+1)).tobytes()
        for plane in range(4):
            for x in range(0,width,8):
                out.append(sum(((row[x+i]>>plane)&1)<<(7-i) for i in range(8)))
    return bytes(out)


def alphabet():
    rows=[]
    for letter in STROKES:
        im=Image.new('1',(8,9))
        stroke_letter(ImageDraw.Draw(im),letter,0,0,1,1,1,1)
        rows.append([sum(im.getpixel((x,y))<<(7-x) for x in range(8)) for y in range(9)])
    return rows


def main():
    raw=planar(landscape())
    packed=pack(raw)
    assert bytes(unpack(packed))==raw
    header=['/* Generated by tools/build_title_art.py. CPU-side read-only art. */',
            'static const UWORD title_palette[16]={'+','.join(hex(c) for c in COLORS)+'};',
            'static const UBYTE brush_letters[26][9]={']
    header += ['    {'+','.join(map(str,row))+'},' for row in alphabet()]
    header += ['};','static const UBYTE title_packed[]={']
    header += [','.join(map(str,packed[i:i+32]))+',' for i in range(0,len(packed),32)]
    (ROOT/'amiga/title_art.h').write_text('\n'.join(header+['};','']),encoding='ascii')
    print(f'Packed title frieze: {len(packed)} bytes')


if __name__=='__main__':
    main()
