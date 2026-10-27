"""Convert reviewed AI cells to fixed-anchor 48x26 OCS animation frames.

No reference game pixels, geometry or collision state are read. Facing and
opposite-side climbing reflection are runtime presentation transforms.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/graphics/v2'
PALETTE=[0x011,0x123,0x345,0x567,0x9ab,0xcde,0xfff,0x7ab,
         0x235,0x357,0x468,0xb64,0xdb8,0xfe5,0x4b4,0x163]
RGB=[tuple(((c>>s)&15)*17 for s in (8,4,0)) for c in PALETTE]
WIDTH,HEIGHT,POSES=48,26,16
# Reviewed cell boundaries, feet baselines and body-centre anchors.
# One actor-wide scale preserves body size between upright and prone poses.
LAYOUTS={
 'bruce':dict(columns=[0,350,700,1050,1402],rows=[0,294,584,870,1122],
              baselines=[286,572,852,1104],scale=.085,
              anchors=[190]*4+[185]*4+[190,180,170,190,180,125,185,190]),
 'ninja':dict(columns=[0,390,780,1170,1558],rows=[0,282,538,767,1010],
              baselines=[265,528,751,980],scale=.10,
              anchors=[235]*4+[225]*4+[225,210,175,225,230,150,230,240]),
 'yamo':dict(source='yamo-green-source-v3.png',
             columns=[0,420,800,1160,1536],rows=[0,280,550,786,1024],
             baselines=[270,538,786,1008],scale=.095,
             anchors=[265,210,160,180,270,197,143,138,250,180,120,140,235,125,160,205]),
}

def main():
    atlas=Image.new('P',(WIDTH*POSES,HEIGHT*3),0)
    atlas.putpalette([v for rgb in RGB for v in rgb]+[0]*720)
    atlas.info['transparency']=0
    packed,records,occupied,bounds_table,sources=bytearray(),[],[],[],[]
    for kind,actor in enumerate(['yamo','ninja','bruce']):
        layout=LAYOUTS[actor]
        source=ART/layout.get('source',f'{actor}-source.png');image=Image.open(source).convert('RGBA')
        sources.append(dict(path=str(source.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
        cols=layout['columns'];rows=layout['rows'];scale=layout['scale']
        assert image.size==(cols[-1],rows[-1])
        for pose in range(POSES):
            source_pose=pose-2 if actor=='bruce' and pose in (6,7) else pose
            row,col=divmod(source_pose,4)
            bounds=(cols[col],rows[row],cols[col+1],rows[row+1])
            # Recovery shares its source row with a wide prone neighbour.
            # Exclude that neighbour's shoe rather than importing a third leg.
            if pose==14 and actor=='yamo':bounds=(cols[col],rows[row],1080,rows[row+1])
            if pose==14 and actor=='ninja':bounds=(cols[col],rows[row],1090,rows[row+1])
            if pose==14 and actor=='bruce':bounds=(cols[col],rows[row],1010,rows[row+1])
            if pose==15 and actor=='ninja':bounds=(1090,rows[row],1558,rows[row+1])
            if pose==15 and actor=='bruce':bounds=(1010,rows[row],1402,rows[row+1])
            if pose==15 and actor=='yamo':bounds=(1090,rows[row],1536,rows[row+1])
            tile=image.crop(bounds)
            tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.BOX)
            canvas=Image.new('RGBA',(WIDTH,HEIGHT))
            left=round(24-layout['anchors'][source_pose]*scale)
            baseline=992 if actor=='yamo' and pose==15 else layout['baselines'][row]
            top=round(25-(baseline-bounds[1])*scale)
            canvas.paste(tile,(left,top))
            pixels=[]
            for red,green,blue,alpha in canvas.getdata():
                if alpha<128:pixels.append(0);continue
                candidates=range(1,16)
                if actor=='yamo' and green>red and green>blue:
                    # Shared OCS palette: keep green skin on the green ramp.
                    # Unrestricted nearest RGB makes lime skin mostly yellow.
                    candidates=(1,14,15)
                    # Sparse highlight dithering preserves the rounded belly
                    # with this fixed palette without turning its base yellow.
                    position=len(pixels)
                    if red>160 and green>205 and blue>35 and not ((position%WIDTH)&1) and not ((position//WIDTH)&1):
                        candidates=(13,14,15)
                pixels.append(min(candidates,key=lambda i:sum((a-b)**2 for a,b in zip((red,green,blue),RGB[i]))))
            assert any(pixels),(actor,pose)
            used=[i//WIDTH for i,c in enumerate(pixels) if c]
            occupied.append((min(used),max(used)+1))
            columns=[i%WIDTH for i,c in enumerate(pixels) if c]
            bounds_table.append((min(columns),min(used),max(columns)+1,max(used)+1))
            sprite=Image.frombytes('P',(WIDTH,HEIGHT),bytes(pixels))
            sprite.putpalette(atlas.getpalette());sprite.info['transparency']=0
            sprite.save(ART/f'{actor}-{pose:02}.png',transparency=0)
            atlas.paste(sprite,(pose*WIDTH,kind*HEIGHT))
            packed.extend((pixels[i]<<4)|pixels[i+1] for i in range(0,len(pixels),2))
            records.append(dict(actor=actor,pose=pose,source_pose=source_pose,source_rect=bounds,
                source_anchor=[layout['anchors'][source_pose],baseline-bounds[1]],
                anchor=[24,25],width=WIDTH,height=HEIGHT,
                opposite_side_runtime_reflection=actor=='bruce' and pose in (6,7),
                sha256=hashlib.sha256(bytes(pixels)).hexdigest()))
    atlas.save(ART/'fighters-indexed.png',transparency=0)
    atlas.convert('RGBA').resize((WIDTH*POSES*2,HEIGHT*3*3),Image.Resampling.NEAREST).save(ART/'fighters-preview.png')
    (ART/'palette.txt').write_text('\n'.join(f'#{c:03x}' for c in PALETTE)+'\n')
    header='/* AI art; fixed24,25 anchors; build_fighter_art.py. */\nstatic const unsigned char fighter_art[]={\n'
    header+='\n'.join(','.join(str(v) for v in packed[i:i+32])+',' for i in range(0,len(packed),32))+'\n};\n'
    header+='static const unsigned char fighter_art_rows[48][2]={'
    header+=','.join('{%d,%d}'%r for r in occupied)+'};\n'
    header+='static const unsigned char fighter_art_bounds[48][4]={'
    header+=','.join('{%d,%d,%d,%d}'%b for b in bounds_table)+'};\n'
    (ROOT/'amiga/fighter_art_data.h').write_text(header,encoding='ascii')
    report=dict(generator='built-in image_gen',exact_c64_sprite_composition=False,original_pixels_shipped=False,
        packed_bytes=len(packed),width=WIDTH,height=HEIGHT,poses_per_actor=POSES,palette_ocs=PALETTE,frames=records,
        source_files=sources)
    (ART/'fighters-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('48 animation slots;48x26;16 OCS colors;',len(packed),'CPU packed bytes')

if __name__=='__main__':main()
