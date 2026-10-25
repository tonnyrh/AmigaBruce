"""Preview the actual pose selection/facing transforms; does not edit art."""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/graphics/v2'

def main():
    for action,poses in [('run',[0,1,2,3]),('climb',[4,5,6,7]),
                         ('attacks',[8,9,10,11,8,12,13,14,15,8])]:
        frames=[]
        for pose in poses:
            canvas=Image.new('RGBA',(192,38),(0,17,17,255))
            for i,actor in enumerate(['bruce','ninja','yamo']):
                sprite=Image.open(ART/f'{actor}-{pose:02}.png').convert('RGBA')
                if actor=='bruce' and pose in (6,7):
                    # Runtime uses source_x=48-x to reflect about anchor24.
                    flipped=Image.new('RGBA',sprite.size)
                    flipped.paste(sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
                    sprite=flipped
                canvas.alpha_composite(sprite,(i*64+8,5))
            frames.append(canvas.resize((768,152),Image.Resampling.NEAREST))
        frames[0].save(ART/f'{action}.gif',save_all=True,append_images=frames[1:],
                       duration=160 if action=='climb' else 120,loop=0,disposal=2)
    print('Presentation previews: run.gif, climb.gif, attacks.gif; these are not runtime timing evidence')

if __name__=='__main__':main()
