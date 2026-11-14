"""Palette-locked Enhanced masters, inspired by Harrier's graphics editor.

Sparse indexed PNG overrides are consumed by the production packer. Classic
and source geometry are read-only. Pen 16 is an editor-only alpha sentinel;
it is never an OCS colour register (opaque black remains pen 0).
"""
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
from uuid import uuid4
from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
EDIT_DIR = ROOT / 'assets/graphics/enhanced-edits'
HISTORY = ROOT / '.tmp/graphics-history'
ALPHA = 16


@dataclass(frozen=True)
class Asset:
    key: str
    label: str
    group: str
    width: int
    height: int
    pixels: tuple[int, ...]
    max_pen: int = 15

    @property
    def identity(self):
        # Detect a changed default catalog (including stamp IDs), not just size.
        return sha256(bytes(self.pixels)).hexdigest()

    @property
    def path(self):
        return EDIT_DIR / (self.key + '.png')


def palette():
    from build_enhanced_art import PALETTE, RGB
    return PALETTE, RGB


def image_for(asset, pixels):
    image = Image.new('P', (asset.width, asset.height))
    colors = [c for rgb in palette()[1] for c in rgb]
    image.putpalette(colors + [0] * (768-len(colors)))
    image.putdata(pixels)
    image.info['transparency'] = ALPHA
    return image


def validate(asset, pixels):
    if len(pixels) != len(asset.pixels):
        raise ValueError('The image has the wrong dimensions.')
    for original, pen in zip(asset.pixels, pixels):
        if type(pen) is not int or (pen != ALPHA and not 0 <= pen <= asset.max_pen):
            raise ValueError('A pixel is outside this asset’s Amiga palette.')
        if (original == ALPHA) != (pen == ALPHA):
            raise ValueError('The silhouette is locked. Keep all opaque pixels in their original positions.')


def _rebase_first_bruce_edit(asset, base_hash, pixels):
    """Carry only deliberate pen changes across the first Bruce repaint."""
    if asset.group=='Bruce' and asset.key.startswith('fighter-2-') and int(asset.key.split('-')[2])<14:
        from enhanced_fighters import bruce_pixels as original_pose
        from enhanced_bruce_strikes import strike_pixels as original_strike
        _,_,slot,face = asset.key.split('-')
        slot,face = int(slot),int(face)
        strike = {8:0x06,10:0x1c,13:0x1a}.get(slot)
        old = original_strike(strike,face) if strike else original_pose(slot,face)
        if not face:
            old = flip(old,48)
        original = bytes(ALPHA if value==15 else value for value in old)
        if sha256(original).hexdigest()==base_hash and all(
                (a==ALPHA)==(b==ALPHA) for a,b in zip(original,asset.pixels)):
            return [new if edit==before else edit for before,edit,new in zip(original,pixels,asset.pixels)]
    raise ValueError(f'{asset.key}: the original image has changed. Import the edited PNG again to match it to the new original.')


def decode(asset, raw):
    with Image.open(BytesIO(raw)) as image:
        if image.mode != 'P' or image.size != (asset.width, asset.height):
            raise ValueError(f'{asset.key}: expected an indexed PNG with the original dimensions.')
        if image.info.get('transparency') != ALPHA:
            raise ValueError(f'{asset.key}: incorrect transparency index.')
        expected = [c for rgb in palette()[1] for c in rgb]
        if image.getpalette()[:48] != expected:
            raise ValueError(f'{asset.key}: the palette has changed.')
        if image.info.get('bruce.asset') != asset.key:
            raise ValueError(f'{asset.key}: the PNG belongs to a different asset.')
        pixels = list(image.tobytes())
        if image.info.get('bruce.base') != asset.identity:
            pixels = _rebase_first_bruce_edit(asset,image.info.get('bruce.base'),pixels)
        validate(asset, pixels)
        return pixels


def encode(asset, pixels, provenance=None):
    validate(asset, pixels)
    info = PngImagePlugin.PngInfo()
    info.add_text('bruce.asset', asset.key)
    info.add_text('bruce.base', asset.identity)
    info.add_text('bruce.origin', json.dumps(provenance or {'method':'manual pixel editor'}, ensure_ascii=False))
    out = BytesIO()
    image_for(asset, pixels).save(out, format='PNG', pnginfo=info, transparency=ALPHA)
    raw = out.getvalue()
    assert decode(asset, raw) == list(pixels)
    return raw


def load(asset, directory=EDIT_DIR):
    path = directory / (asset.key + '.png')
    raw = path.read_bytes() if path.exists() else None
    return (decode(asset, raw) if raw is not None else list(asset.pixels)), raw


def save(asset, pixels, expected, provenance=None, directory=EDIT_DIR, history=HISTORY):
    raw = encode(asset, pixels, provenance)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (asset.key + '.png')
    # Exclusive sibling lock serializes this editor's writers. Also check
    # optimistic version before replacing so stale windows cannot lose work.
    lock = path.with_suffix('.lock')
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ValueError('Another window is saving this image.') from exc
    temporary = path.with_name('.' + path.stem + '-' + uuid4().hex + '.tmp')
    try:
        os.close(handle)
        current = path.read_bytes() if path.exists() else None
        if current != expected:
            raise ValueError('The image has changed on disk. Export your draft before reloading it.')
        if current is not None:
            history.mkdir(parents=True, exist_ok=True)
            (history / (asset.key + '-' + uuid4().hex + '.png')).write_bytes(current)
        temporary.write_bytes(raw)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)
    return raw


def apply_override(asset, directory=EDIT_DIR):
    return load(asset, directory)[0]


def flip(pixels, width):
    return [v for i in range(0, len(pixels), width) for v in reversed(pixels[i:i+width])]


def fighter_asset(actor, slot, face, pixels):
    names = ('Yamo', 'Kage', 'Bruce')
    poses = ('Guard', 'Run A', 'Run B', 'Run C', 'Run D', 'Climb A',
             'Climb B', 'Wind-up', 'Strike', 'Jump', 'Kick', 'Knocked down', 'Hit reaction', 'Kick wind-up',
             'Vertical jump · Set', 'Vertical jump · Tuck', 'Vertical jump · Extend', 'Lie flat')
    label=f'{names[actor]} · {poses[slot]}'
    if actor!=2 or slot not in (14,15,16):
        label+=' · '+('right' if face else 'left')
    return Asset(f'fighter-{actor}-{slot:02}-{face}',label,
                 names[actor], 48, 21, tuple(ALPHA if p==15 else p for p in pixels), 14)


def stamp_asset(index, data, label=None):
    colors = tuple(sum(((data[16+p*8+y]>>(7-x))&1)<<p for p in range(4))
                   if data[8+y] & (128>>x) else ALPHA for y in range(8) for x in range(8))
    return Asset(f'stamp-{index:03}', label or f'Structure {index:03}', 'Structures', 8, 8, colors)


def stamp_bytes(asset, source, pixels):
    validate(asset, pixels)
    # First 16 bytes: original live-source comparison and visual alpha.
    return source[:16] + bytes(sum(((pixels[y*8+x] if pixels[y*8+x]!=ALPHA else 0)>>p & 1)<<(7-x)
                                   for x in range(8)) for p in range(4) for y in range(8))


def planar_pixels(w, h, raw):
    return [sum(((raw[((y//8)*(w//8)+x//8)*32+p*8+y%8]>>(7-x%8))&1)<<p for p in range(4))
            for y in range(h) for x in range(w)]


@lru_cache(maxsize=1)
def catalog():
    from build_enhanced_art import base_pixels, base_scenery
    from enhanced_architecture import PAGODA_INDEX, TOWER_INDEX, VAULT_LAMP_INDEX, stamps
    from enhanced_fighters import BRUCE_SOURCE_POSES, BRUCE_UNDIRECTED
    assets = []
    for actor in (2,0,1):
        for slot in range(len(BRUCE_SOURCE_POSES) if actor==2 else 13):
            # Bruce uses the two source running forms. Slots 3/4 are unused aliases.
            if actor==2 and slot in (3,4):continue
            for face in ((1,) if slot in (BRUCE_UNDIRECTED if actor==2 else (5,6)) else (1,0)):
                assets.append(fighter_asset(actor,slot,face,base_pixels(actor,slot,face)))
    for key,label,w,h,data in base_scenery():
        assets.append(Asset(key,label,'Backgrounds',w,h,tuple(planar_pixels(w,h,data))))
    lookup,raw = stamps((ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes())
    for i in range(len(raw)//48):
        uses = [j for j,v in enumerate(lookup[:768]) if v==i+1]
        names = ('Courtyard','Gallery','Vault')
        label = f'{names[uses[0]//256]} · tile ${uses[0]%256:02X}' if uses else f'Lantern flame {i+1}'
        if not uses and i+1 in lookup[TOWER_INDEX:VAULT_LAMP_INDEX]:
            label=f'Room 4 tower · tile ${lookup.index(i+1,TOWER_INDEX)-TOWER_INDEX:02X}'
        elif not uses and i+1 in lookup[VAULT_LAMP_INDEX:PAGODA_INDEX]:
            side,phase=divmod(lookup.index(i+1,VAULT_LAMP_INDEX)-VAULT_LAMP_INDEX,4)
            label=f'Vault lantern · {"right" if side else "left"} · flame {phase+1}'
        elif not uses and i+1 in lookup[PAGODA_INDEX:]:
            tile,half=divmod(lookup.index(i+1,PAGODA_INDEX)-PAGODA_INDEX,2)
            label=f'Room 16 roof · tile ${tile+128*half:02X}'
        assets.append(stamp_asset(i+1,raw[i*48:(i+1)*48],label))
    return tuple(assets)


def check_files(directory=EDIT_DIR):
    paths=list(directory.glob('*.png'))
    if not paths:return 0
    by_key = {a.key:a for a in catalog()}
    for path in paths:
        if path.stem not in by_key:
            raise ValueError(f'Unknown asset: {path.name}')
        decode(by_key[path.stem],path.read_bytes())
    return len(paths)


def check_export_path(path):
    dest=Path(path).resolve()
    if dest.suffix.lower()!='.png':
        raise ValueError('Choose a file with a .png extension.')
    protected=(ROOT/'assets', ROOT/'.reference', ROOT/'.BruceLeeII', ROOT/'reference')
    if any(dest.is_relative_to(d.resolve()) for d in protected):
        raise ValueError('Choose another export folder. The originals and build inputs are protected.')


def convert_candidate(asset, candidate, current):
    """Fit RGB to native canvas; quantize while retaining the exact alpha mask."""
    candidate = candidate.convert('RGBA')
    if asset.key.startswith('fighter-'):
        # Keep the ink at the centre of each enlarged square. Averaging
        # adjacent inks can introduce a third, unrelated palette color.
        candidate = candidate.resize((asset.width,asset.height),Image.Resampling.NEAREST)
    else:
        candidate.thumbnail((4096,4096))
        candidate = candidate.resize((asset.width,asset.height),Image.Resampling.BOX)
    colors = palette()[1]
    result=[]
    rgba=iter(candidate.tobytes())
    for i,(r,g,b,a) in enumerate(zip(rgba,rgba,rgba,rgba)):
        if asset.pixels[i]==ALPHA:result.append(ALPHA)
        elif a<128:result.append(current[i])
        else:result.append(min(range(asset.max_pen+1),key=lambda p:sum((u-v)**2 for u,v in zip((r,g,b),colors[p]))))
    validate(asset,result)
    return result
