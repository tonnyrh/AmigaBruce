"""Read game-resolution paint masters aligned to the frozen C64 sprite rasters."""
from functools import lru_cache
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/graphics/enhanced-study'
SPRITES = ROOT / 'assets/c64/sprites-v1'


@lru_cache(maxsize=None)
def sprite_shape(name, pose, face):
    with Image.open(SPRITES / f'{name}-{pose:02x}-f{face}.png') as source:
        alpha = source.getchannel('A')
    box = alpha.getbbox()
    return box, alpha.crop(box).tobytes()


@lru_cache(maxsize=3)
def native_cells(name, poses):
    rows = (len(poses)+3)//4
    with Image.open(ART / f'{name}-coarse-native.png') as image:
        if image.mode!='P' or image.size!=(128,rows*32) or image.info.get('transparency')!=15:
            raise ValueError(f'Invalid native ink sheet for {name}')
        frames = []
        for index,pose in enumerate(poses):
            box,mask = sprite_shape(name,pose,1)
            width,height = box[2]-box[0],box[3]-box[1]
            x = index%4*32+(32-width)//2
            y = index//4*32+(32-height)//2
            frame = image.crop((x,y,x+width,y+height))
            if bytes(255 if pen!=15 else 0 for pen in frame.tobytes()) != mask:
                raise ValueError(f'Ink sheet does not match the C64 mask for {name} pose {pose:02x}')
            frames.append(frame)
    return tuple(frames)


def fit_mask(colors, mask, width):
    """Extend the nearest painted edge only where the target needs more ink."""
    result = bytearray(colors)
    opaque = [(i%width,i//width,pen) for i,pen in enumerate(colors) if pen!=15]
    for i,alpha in enumerate(mask):
        if not alpha:
            result[i] = 15
        elif colors[i]==15:
            x,y = i%width,i//width
            result[i] = min(opaque,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)[2]
    return bytes(result)
