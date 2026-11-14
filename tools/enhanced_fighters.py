"""First-generation Bruce inks retained for earlier graphics editor saves.

One line runs from left to right across the opaque pixels of a sprite row.
Gaps in the silhouette stay transparent. Related strides share the same
strokes so the face, belt and highlights travel with the body.
"""
from pathlib import Path
from PIL import Image

# Native sprite writer $2584/$25E2; pose selector $2780-$29C2.
# Left/right source-pose pairs for the existing Enhanced slots. Climbing
# has two wall-facing poses, independent of actor facing. Running follows
# the two source shapes; slots 3/4 remain aliases for the old atlas layout.
BRUCE_SOURCE_POSES = {
    0:(0x00,0x02), 1:(0x10,0x12), 2:(0x0e,0x14),
    3:(0x10,0x12), 4:(0x0e,0x14), 5:(0x0a,0x0a), 6:(0x0c,0x0c),
    7:(0x30,0x34), 8:(0x04,0x06), 9:(0x22,0x26), 10:(0x18,0x1c),
    11:(0x3e,0x3a), 12:(0x2c,0x2e), 13:(0x16,0x1a),
    14:(0x08,0x08), 15:(0x1e,0x1e), 16:(0x20,0x20), 17:(0x40,0x42),
}
BRUCE_UNDIRECTED = (5,6,14,15,16)


def bruce_pixels(slot, face=1):
    """Original silhouette; authored inks. Input faces right for the packer."""
    pose = BRUCE_SOURCE_POSES[slot][face]
    folder = Path(__file__).resolve().parents[1] / 'assets/c64/sprites-v1'
    with Image.open(folder / f'bruce-{pose:02x}-f{face}.png') as image:
        mask = image.getchannel('A')
        if not face:
            mask = mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        data = [0 if alpha else 15 for alpha in mask.tobytes()]
    return ink_rows(data,BRUCE_ROWS[slot])

# Bruce: warm amber (a / $D96) is the skin tone; the HUD white (1 /
# $FFE) must not appear on his skin. Ink marks the shaded edge; the belt
# and shoes separate the gold trousers from the climbing rungs.
BRUCE_GUARD = """
0000
0000aa
04aaaaa4
04aa00aa
04aaaaa4
4aaaa4
4aa4
4aaaa4
4aaaaaa4
4aa44aaaa4 aa
4a0044aaaaaa40
4aaaa4
047740
477774
74 4774
74 74
74 74
74 74
40 40
0000 0000
000000 000000
"""
BRUCE_CLIMB_LEFT = """
aa 0000
aa aa000000
4aa4aa000000
a4 aaaa0000
a4 aaaa0000
4a aaaa
4aaaaaaaaaa4
4aaaaaaaaaa4
4aaaaaaaa4
4aaaaaaa4a
0474 aa40
4774
4774
74 74
74 74
4774 74
4774 74
74
74
0000
0000
"""
BRUCE_CLIMB_RIGHT = "\n".join(line[::-1] for line in BRUCE_CLIMB_LEFT.strip().splitlines())

BRUCE_STRIDE = """
000000
0000aaaa
0044aa00
004aaaa4
004aaaa4
4aaaa4
4aaaa4
4aaaa4
4aaaa4
4a444aa4
0044aaa400
04777740
47777774
4774
4774
74
4774
40
00
"""
BRUCE_AIR = """
00
0600
0004aa
04aaaaa04
04aa04aaa40
aa0 aaaa244
4a0 04aa4a0
00477740
0777474
0b47740
0740470
0774060
060 004
00 0
"""
BRUCE_DOWN = """
000
0600
0 4aa0a4
007777777b4aaaaa40 0
06b00444406a40a4aa4aa
00 000000000000000000
"""

BRUCE_ROWS = {0:BRUCE_GUARD,1:BRUCE_STRIDE,2:BRUCE_STRIDE,3:BRUCE_STRIDE,4:BRUCE_STRIDE,
              5:BRUCE_CLIMB_LEFT,6:BRUCE_CLIMB_RIGHT,7:BRUCE_STRIDE,
              9:BRUCE_AIR,11:BRUCE_DOWN,12:BRUCE_AIR}


def ink_rows(data, recipe):
    strokes = [[int(c,16) for c in line if c!=' ']
               for line in recipe.strip().splitlines()]
    rows = [[y*48+x for x in range(48) if data[y*48+x]!=15] for y in range(21)]
    occupied = [row for row in rows if row]
    for y,row in enumerate(occupied):
        ink=strokes[round(y*(len(strokes)-1)/(len(occupied)-1))]
        for i,at in enumerate(row):
            data[at]=ink[round(i*(len(ink)-1)/max(1,len(row)-1))]
    return data
