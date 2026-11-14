"""Paint Bruce's Enhanced attacks inside the displayed C64 sprite silhouettes."""
from pathlib import Path
from PIL import Image

SPRITES = Path(__file__).resolve().parents[1] / 'assets/c64/sprites-v1'

# One colour per opaque pixel of the normal right-facing pose, from head
# to feet. Spaces separate strokes. 0 is opaque ink; 15 is reserved for air.
# Pose selection: $282F-$283E (punch), $288B-$28B0 (two kick phases).
PAINT = {
    0x06: (
        '0000', '060000', '0060aaa0', '04aaaaa0',
        '4aaaaaaa aaa4aaaa', '4aaaa4 a0', '04aaaaa4', '4aaaaa24',
        '4aaa244aaa', '0440 a0', '0774', '0774', '0774',
        '047774', '477704', '77 04', '74 04', '04 04', '00 6000',
    ),
    0x1a: (
        '0000', '00600aaa', '004aa00aaa', '004a00aaaa', '04aaaaaaa4',
        '4aaaaaa4aaaa40', '4aaaa244aaa0', '4aaaa2a244 aa', '4aaaa22440 aa',
        '4aa2244442aaaa', 'a0 444206', 'aa 07777740', 'a4 0777477774',
        '40 0777042774', 'a4077774 7774', '0774 7774', '0774 0774',
        '0474007774', '00066000',
    ),
    0x1c: (
        '0000', '00600aaa', '004aa00aaa', '004a00aaaa', '04aaaaaaa22224',
        '4aaaaa24aaa4', '4aaaaa2244aaa4', '04aaaa224404aaa0',
        '4aaa 222204a0', 'aa 4aaa24277777777777744000', 'a0 4477777774222222244000',
        'aa40 07777774 6000', '4aa0 0774', '0774', '0774 04',
        '077777777400', '044222444000',
    ),
}
LEFT = {0x06:0x04, 0x1a:0x16, 0x1c:0x18}


def strike_pixels(pose, face):
    """Both nibbled inputs face right. The Amiga mirrors the left input once."""
    def mask(code, facing):
        with Image.open(SPRITES/f'bruce-{code:02x}-f{facing}.png') as im:
            return im.getchannel('A')
    right = mask(pose, 1)
    shape = right if face else mask(LEFT[pose], 0).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert right.getbbox() == shape.getbbox()
    pixels = [15]*(48*21)
    _, top, _, bottom = right.getbbox()
    assert len(PAINT[pose]) == bottom-top
    for y, stroke in enumerate(PAINT[pose], top):
        xs = [x for x in range(48) if right.getpixel((x,y))]
        ink = [int(c,16) for c in stroke if c!=' ']
        assert len(xs)==len(ink) and 15 not in ink,(hex(pose),y,len(xs),len(ink))
        colors = dict(zip(xs,ink))
        for x in range(48):
            if shape.getpixel((x,y)):
                # The left punch has a slightly different elbow and head.
                sx = x if x in colors else min(xs,key=lambda other:abs(other-x))
                pixels[y*48+x] = colors[sx]
    return pixels
