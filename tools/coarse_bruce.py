"""Paint Enhanced Bruce on the actual source silhouette and sprite anchor."""
from functools import lru_cache
from PIL import Image
from coarse_fighter_art import fit_mask, native_cells, sprite_shape
from enhanced_fighters import BRUCE_SOURCE_POSES

# Guard, both strides, wind-up; punch, jump, both kick phases;
# two alternating wall-facing climbs, reaction, knockdown.
STUDY_SLOTS = (0,1,2,7,8,9,13,10,5,6,12,11)
STUDY_POSES = tuple(BRUCE_SOURCE_POSES[slot][1] for slot in STUDY_SLOTS)

# Native OCS inks on the candidate's cropped masks. The vertical jump turns
# Bruce's back to the viewer. The two prone silhouettes are asymmetric.
ACTION_INKS = {
    0x08: """
......0000...... ....00000000.... ....0004aaaa.... ....00aaaa00....
....04a4aaaa.... ....04aaaaa4.... ......4aa4...... ....4aaaaaa4....
..4aaaaaaaaaa4.. ..aaaa44aaaaa4.. ..4aa4aaaa4aa4.. 4aaa..4444..aa04
aa....4774....aa ......4774...... ......4774...... ......4774......
......4774...... ......4774...... ......4774...... ....00444400....
....00000000....
""",
    0x1e: """
......0000...... ....00000000.... ....00440000.... ....00000000....
....00000000.... ......0000...... aa....4aa4....aa 4aaaaaa44aaaaaa4
4aaa4aaaaaa4aaa4 aaa4..4aa4..4aaa aa....4aa4....aa ......4444......
....47777774.... ..477740047774.. 477774....477774 4774........4774
..0004....4000.. ....00....00....
""",
    0x20: """
aa....0000....aa a4..00000000..4a a4aa00044000aa4a 4a..00000000..a4
4a..00000000..a4 aa....0000....aa 4aaa..4aa4..aaa4 ..aaaaaaaaaaaa..
..4aaa4aa4aaa4.. ....4aaaaaa4.... ......4aa4...... ......4444......
......4774...... ......4774...... ......4774...... ......4774......
......4774...... ......4774...... ....47744774.... ....40....04....
..00........00..
""",
    0x40: """
..0000........................
..aa4a0000............0000....
..044aaa00............0440....
..aa00aa04....4774....47744400
..4aaaaaaa44477777777777774400
aa4aaaa4440047777777774444....
....aaaa......................
""",
    0x42: """
........................0000..
....0000............0000a4aa..
....0440............00aaa440..
00444774....4774....40aa00aa..
00447777777777777444aaaaaaa4..
....444477777777aa00444aaaa4aa
................aa....aaaa....
""",
}


@lru_cache(maxsize=None)
def bruce_pixels(slot,face):
    if slot in (3,4):
        slot -= 2
    pose = BRUCE_SOURCE_POSES[slot][face]
    box,mask = sprite_shape('bruce',pose,face)
    left,top,right,bottom = box
    width = right-left
    if pose in ACTION_INKS:
        rows=ACTION_INKS[pose].split()
        inks=bytes(15 if c=='.' else int(c,16) for row in rows for c in row)
        if any(len(row)!=width for row in rows) or bytes(255 if p!=15 else 0 for p in inks)!=mask:
            raise ValueError(f'Action inks do not match the C64 silhouette for Bruce pose {pose:02x}')
    else:
        frame = native_cells('bruce',STUDY_POSES)[STUDY_SLOTS.index(slot)]
        if frame.size != (width,bottom-top):
            raise ValueError(f'Unexpected source dimensions for Bruce pose {pose:02x}')
        # The left punch has a different elbow even after mirroring.
        if not face and bytes(255 if p!=15 else 0 for p in frame.tobytes()) != mask:
            frame = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        inks = fit_mask(frame.tobytes(),mask,width)
    canvas = bytearray([15])*(48*21)
    for row,y in enumerate(range(top,bottom)):
        canvas[y*48+left:y*48+right] = inks[row*width:(row+1)*width]
    return tuple(canvas)
