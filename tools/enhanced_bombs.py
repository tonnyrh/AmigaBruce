"""Native pixel masters for the Enhanced floor charges and both C64 blast layouts."""

# Palette indices from the shared OCS playfield. A dot exposes the wall or floor.
INK = {'.':None,'k':0,'s':6,'m':11,'h':12,'b':4,'r':2,'o':10,'g':7,'w':1}

# Gallery charges sit on a low ledge; vault charges are set into its upper lip.
GALLERY_CHARGE = (
    '.....or.', '....br..', '..khhk..', '.khggok.',
    'khgoorrk', 'kkkkkkkk',
)
VAULT_CHARGE = (
    '.....or.', '..khhk..', '.khggok.', 'khgoorrk',
    'kkkkkkkk',
)

# One coordinated 24-pixel-wide painting per source phase. The charge is at
# x=12. The second silhouette throws sparks farther out and higher up.
FLASH = (
    '..........o',
    '..........g',
    '......o....r.....o',
    '.......g...o....g',
    '........r..g...r',
    '.....o.....go..o...r',
    '......g.r..og.og..o',
    '.......or..og.og.g',
    '....r...or.rgog..o',
    '.....go..oogwog.og..r',
    '......or.rgwwggog..o',
    '.......roogwwggroog',
    '....rooggggwwgggorr',
    '......roogwwwwgor',
    '.......rogwwwggor',
    '........roogggorr',
)
PLUME = (
    '..........o....r',
    '......r...g....o....s',
    '......o....r..g....h',
    '..s....g...o..r..o',
    '...h....r..og...g..r',
    '.....o.....go..ro..o',
    '...r..g..r..og.go.g',
    '.o..g..o..ooog.ogor...o',
    '..g..o.ro.rgogogor...g',
    '......rog..googgo...or',
    '..r..o.ogr.ogggor.ogo',
    '...go..rgorogggorogo...r',
    '.....o..rogogwgorgor..o',
    '.ro...go.rgggwggogor.g',
    '...og..oogggwwgggorro',
    'r...rogoggggwwggogor..og',
    '.og...roogggwwwgggorrgo',
    '...roogggggwwggggooorr',
    '.....rooogggggggor',
    '.......roooggggoorr',
)


def bomb_ink(tile,x,y,gallery):
    """Return (owns pixel, ink). Unowned pixels use the normal platform art."""
    deck=10 if gallery else 4
    if tile==0x60:
        rows=GALLERY_CHARGE if gallery else VAULT_CHARGE
        # Flat casing base sits exactly at the platform lip. No rounded
        # lower half hangs beneath the ground; the floor continues below.
        row=y-(deck+1-len(rows))
        mark=rows[row][x] if 0<=row<len(rows) else '.'
        return mark!='.' or y<deck, INK[mark]

    phase,part=divmod(tile-0x71,6)
    px=(part%3)*8+x
    py=(part//3)*16+y
    base=16+deck
    if py>=base:
        return False,None
    if phase==0:
        row=py-base+len(FLASH)
        line=FLASH[row] if row>=0 else ''
    else:
        line=PLUME[py*(len(PLUME)-1)//(base-1)]
    return True, INK[line[px]] if px<len(line) else None
