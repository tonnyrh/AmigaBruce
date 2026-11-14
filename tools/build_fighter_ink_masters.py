"""Convert the coarse AI studies into fixed-palette, native-size ink masters."""
import argparse
from pathlib import Path
from PIL import Image
from build_enhanced_art import RGB
from coarse_fighter_art import ART, SPRITES, fit_mask, sprite_shape
from coarse_bruce import STUDY_POSES as BRUCE_POSES
from enhanced_enemies import NAMES as ENEMIES, STUDY_POSES as ENEMY_POSES

NAMES = (*ENEMIES,'bruce')
STUDY_POSES = (*ENEMY_POSES,BRUCE_POSES)

# Representative inks in the generated artwork and their destination OCS pens.
# Lift the hood highlight one OCS step so it reads against the slate walls.
SWATCHES = (
    (((16,16,16),0), ((99,150,53),5), ((184,213,108),13), ((151,173,192),3)),
    (((10,9,9),0), ((21,32,55),6), ((66,82,113),3), ((133,47,30),2),
     ((214,119,67),10), ((240,168,79),10)),
    (((9,8,8),0), ((211,129,77),10), ((169,66,43),2), ((225,185,41),7)),
)


def pen_for(rgb, swatches):
    return min(swatches,key=lambda s:sum((c-p)**2 for c,p in zip(s[0],rgb)))[1]


def shade_bruce_skin(inks, mask, width):
    """Keep the shadow side of the bare arms readable against warm masonry."""
    painted = bytes(inks)
    for i in range(width,len(inks)-width):
        x = i%width
        if painted[i]!=10 or x+1>=width or painted[i+1]!=10:
            continue
        left_edge = x==0 or not mask[i-1]
        underside = not mask[i+width] and x+2<width and painted[i+2]==10
        if (left_edge or underside) and (painted[i-width] in (2,10) or painted[i+width] in (2,10)):
            inks[i] = 2


def convert_cell(cell, actor, mask, width):
    box = cell.getchannel('A').point(lambda alpha: 255 if alpha>=160 else 0).getbbox()
    if box is None:
        raise ValueError('Empty pose in the generated sheet')
    height = len(mask)//width
    # Vote on palette indices at nine subpixel centres. Mixing their RGB
    # values would create new inks along the border of two flat colors.
    samples = cell.crop(box).resize((width*3,height*3),Image.Resampling.NEAREST)
    colors = []
    eye_samples = []
    for y in range(height):
        for x in range(width):
            votes = []
            for dx,dy in ((1,1),(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2)):
                r,g,b,a = samples.getpixel((3*x+dx,3*y+dy))
                votes.append(pen_for((r,g,b),SWATCHES[actor]) if a>=128 else 15)
                # In the study the eyes are yellow-amber, the staff orange.
                if actor==1 and a>=128 and r>209 and g>140 and g>0.61*r and b<0.75*g:
                    eye_samples.append((x+(dx+0.5)/3,y+(dy+0.5)/3))
            colors.append(max(votes,key=votes.count))
    result = bytearray(fit_mask(colors,mask,width))
    if actor==2:
        shade_bruce_skin(result,mask,width)
    if eye_samples:
        # The VIC mask cuts a notch in the hood at eye level. Anchor this
        # small accent on the nearest opaque pair if the notch took its ink.
        ex = sum(x for x,y in eye_samples)/len(eye_samples)
        ey = sum(y for x,y in eye_samples)/len(eye_samples)
        pairs = (i for i in range(len(mask)-1) if i%width<width-1 and mask[i] and mask[i+1])
        index = min(pairs,key=lambda i:(i%width+1-ex)**2+(i//width+0.5-ey)**2)
        result[index:index+2] = bytes((10,10))
    return Image.frombytes('P',(width,height),bytes(result))


def build(actor, guide_dir=None):
    name = NAMES[actor]
    rows = (len(STUDY_POSES[actor])+3)//4
    master = Image.new('P',(128,32*rows),15)
    master.putpalette([value for color in RGB for value in color])
    guide = Image.new('RGBA',master.size,'#d8d1de') if guide_dir else None
    with Image.open(ART/f'{name}-coarse-source.png') as image:
        sheet = image.convert('RGBA')
    for i,pose in enumerate(STUDY_POSES[actor]):
        box,mask = sprite_shape(name,pose,1)
        width,height = box[2]-box[0],box[3]-box[1]
        col,row = i%4,i//4
        location = (32*col+(32-width)//2,32*row+(32-height)//2)
        cell = sheet.crop((col*sheet.width//4,row*sheet.height//rows,
                           (col+1)*sheet.width//4,(row+1)*sheet.height//rows))
        master.paste(convert_cell(cell,actor,mask,width),location)
        if guide is not None:
            with Image.open(SPRITES/f'{name}-{pose:02x}-f1.png') as original:
                reference = original.convert('RGBA').crop(box)
            if actor==1:
                reference = Image.new('RGBA',(width,height),(*RGB[11],255))
                reference.putalpha(Image.frombytes('L',(width,height),mask))
            guide.alpha_composite(reference,location)
    master.save(ART/f'{name}-coarse-native.png',transparency=15)
    if guide is not None:
        guide_dir.mkdir(parents=True,exist_ok=True)
        guide.convert('RGB').resize((1536,384*rows),Image.Resampling.NEAREST).save(guide_dir/f'{name}-shape-guide.png')


def main(default_actor='all'):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actor', choices=(*NAMES,'enemies','all'), default=default_actor)
    parser.add_argument('--guide-dir',type=Path,help='also write the enlarged C64 templates used in the prompts')
    args=parser.parse_args()
    for actor,name in enumerate(NAMES):
        if args.actor in (name,'all') or (args.actor=='enemies' and name in ENEMIES):
            build(actor,args.guide_dir)


if __name__=='__main__':
    main()
