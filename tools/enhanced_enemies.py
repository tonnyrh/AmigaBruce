"""Paint the Enhanced enemies on the actual VIC masks, at their native anchors."""
from functools import lru_cache
from PIL import Image
from coarse_fighter_art import ART, SPRITES, fit_mask, native_cells, sprite_shape

NAMES = ('yamo', 'kage')

# The frozen candidate selects these component pairs at $2780-$29C2.
# $2584/$25E2 place them on a 48x21 canvas, including VIC X expansion.
# A/C and B/D are Enhanced variations of the same two source strides.
PAIRS = ((0,2), (0x10,0x12), (0x0e,0x14), (0x10,0x12), (0x0e,0x14),
         (10,10), (12,12), (0x30,0x34), (4,6), (0x22,0x26),
         (0x18,0x1c), (0x3e,0x3a), (0x2c,0x2e))

def reference_pose(actor, slot, face):
    if actor == 1 and slot == 8:  # Kage's extended staff, $286B-$2876.
        return (0x32, 0x36)[face]
    return PAIRS[slot][face]

# Source poses used in the eight edited cells, all drawn at facing 1.
# Kage's second stride is a better reference than a kick: several of his
# attack codes render the same shape as his guard.
STUDY_POSES = ((2,18,10,26,6,28,58,46),(2,18,10,52,54,20,58,56))


@lru_cache(maxsize=2)
def ink_templates(actor):
    """Eight native, palette-indexed poses and their left-facing reflections."""
    templates = []
    for frame in native_cells(NAMES[actor],STUDY_POSES[actor]):
        templates.extend((frame,frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)))
    return templates

def source_shape(actor, pose, face):
    return sprite_shape(NAMES[actor],pose,face)

def pose_family(actor, pose):
    if pose in (0x0e,0x10,0x12,0x14,0x22,0x24,0x26,0x28):
        return (1,5) if actor==1 else (1,)
    if pose in (10,12):return (2,)
    if pose in (0x16,0x1a,0x30,0x34):return (3,)
    if pose in (4,6,0x32,0x36):return (4,)
    if pose in (0x18,0x1c):return (5,) if actor==0 else (0,)
    if pose in (0x3a,0x3e):return (6,)
    if pose in (0x2c,0x2e,0x38,0x3c,0x40,0x42):return (7,)
    return (0,)


@lru_cache(maxsize=2)
def families(actor):
    # One recipe for a cropped silhouette even if the source latched a new
    # facing or placed the same pose at a different anchor.
    result = {}
    def add(pose, face):
        box, mask = source_shape(actor,pose,face)
        result.setdefault((box[2]-box[0],mask),(pose_family(actor,pose),face))
    for slot in range(13):
        for face in (1,0):
            add(reference_pose(actor,slot,face),face)
    left = {0,4,0x0e,0x10,0x16,0x18,0x22,0x24,0x2c,0x30,0x32,0x3c,0x3e,0x40}
    for pose in range(0,70,2):
        direction = int(pose not in left)
        for face in (direction,1-direction):
            add(pose,face)
    return result


@lru_cache(maxsize=None)
def paint_shape(actor, width, mask):
    """Match shapes in two dimensions so that holes never redistribute ink."""
    height = len(mask)//width
    family,face = families(actor)[width,mask]
    candidates = []
    for index,frame in enumerate(ink_templates(actor)):
        cell, reflected = divmod(index,2)
        scaled = frame.resize((width,height),Image.Resampling.NEAREST).tobytes()
        mismatch = sum((pen!=15)!=bool(alpha) for pen,alpha in zip(scaled,mask))
        size_error = abs(frame.width-width)+abs(frame.height-height)
        # Always use the exact native master when there is one. For other
        # animation phases, prefer the same action with a matching outline.
        score = (bool(mismatch or size_error), cell not in family,
                 mismatch+size_error, reflected!=int(not face))
        candidates.append((score,scaled))
    colors = min(candidates,key=lambda item:item[0])[1]
    return fit_mask(colors,mask,width)


@lru_cache(maxsize=None)
def enemy_pixels(actor, pose, face):
    box, mask = source_shape(actor,pose,face)
    left,top,right,bottom = box
    width = right-left
    ink = paint_shape(actor,width,mask)
    pixels = bytearray([15])*(48*21)
    for row,y in enumerate(range(top,bottom)):
        pixels[y*48+left:y*48+right] = ink[row*width:(row+1)*width]
    return tuple(pixels)
