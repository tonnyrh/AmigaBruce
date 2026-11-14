"""Original OCS pixel art for the courtyard. Numbers are playfield colour indices."""
from functools import lru_cache
from pathlib import Path
from enhanced_bombs import bomb_ink


DRAGON = ((0x41,0x42,0x43,0x44,0x45,0), (0x46,0x48,0x49,0x4a,0x4b,0x4c))
SHRINE = ((0x6b,0x6c,0x6d), (0x6e,0x6f,0x70))
ORNAMENTS = {tile:(layout,col*8,row*16) for layout in (DRAGON,SHRINE)
             for row,tiles in enumerate(layout) for col,tile in enumerate(tiles) if tile}

# The two halves of a C64 object are 128 character codes apart. These are
# the courtyard's architectural objects in the $a000 display character set.
COURTYARD_BASE = (0x09, 0x0d, 0x10, 0x11, 0x12, 0x13, 0x14, *range(0x15, 0x20),
             0x20, 0x21, 0x22, 0x24, 0x25, 0x26, *range(0x28, 0x2e),
             0x31, 0x32, 0x38, 0x39, 0x3a, 0x3b, 0x3d, 0x4d, 0x4e, 0x52, *ORNAMENTS)
# Room 3 swaps the lower-left cell of the relief ($36E2/$36F0).
# Shade its alternate jaw against the adjoining head and plinth.
CALLING_DRAGON = (DRAGON[0], (0x47, *DRAGON[1][1:]))
ORNAMENTS[0x47] = (CALLING_DRAGON, 0, 16)
COURTYARD = COURTYARD_BASE + (0x47,)
# Below the courtyard the same bank is used for stone galleries. The second
# bank ($a800) instead has its own arched platforms and twisted columns.
GALLERY_ARCH = (0x11,0x12,0x13,0x14,*range(0x15,0x20),0x20,0x21,0x28,0x2c,
           0x2d,0x2e,0x2f,0x30,0x31,0x32,0x39,0x3b,0x3e,0x40)
UNLIT_LAMPS = (0x66,0x67)
GALLERY = GALLERY_ARCH + UNLIT_LAMPS
VAULT = (0x07,0x08,0x0a,0x0b,0x0c,0x0d,0x0e,0x10,0x11,0x46,0x48)
TOWER_TILES = (0x09,0x0a,0x36,0x3c,0x4b,0x68,0x69,0x6a)
TOWER_INDEX = 3*256+12  # after the three banks and the lantern phases
VAULT_LAMP_INDEX = TOWER_INDEX+256
VAULT_LAMPS = (0x13,0x14,0x1e,0x1f)
PAGODA_INDEX = VAULT_LAMP_INDEX+8
PAGODA_TILES = (0x0a,0x0b,0x0c,0x0d,0x19,0x23,0x2f)


def pagoda_roof(tile,x,y,pair):
    """Glazed clay, copper flashing and a dark underside on the source silhouette."""
    if not pair:
        return None
    if y>=12:
        return (10,2,4,0)[y-12]
    if tile in (0x19,0x23):
        ridge=x if tile==0x19 else 7-x
        if pair==1:
            return 15 if ridge==0 else 10
        return (10,2,2,4)[(ridge+y//4)%4]
    if tile==0x0d:
        return 7 if pair==1 else 10 if y in (6,10) else 4
    return 10 if y in (6,10) else 2 if x%4!=3 else 4

# Right-facing brass wall bracket and amber paper lantern. The left-facing
# fitting is its mirror. The live wick occupies two pixels in rows 10/11.
VAULT_BRACKET = ('........','........','m.......','bmmmm...','b..bm...','....b...')
VAULT_SHADE = ('...bgb..','..rgagr.','.rogaogr','.roggggr','.rog**gr',
               '.rog**gr','..ogggor','...rbr..','....r...','....a...')
LAMP_INKS = {'.':None,'b':4,'m':9,'r':2,'o':10,'g':7,'a':15}


def vault_lantern(tile,x,y,pair):
    if tile in (0x13,0x1e):
        x=7-x
    if y<len(VAULT_BRACKET):
        return LAMP_INKS[VAULT_BRACKET[y][x]]
    if tile in (0x1e,0x1f):
        return None
    mark=VAULT_SHADE[y-len(VAULT_BRACKET)][x]
    return (2,10,7,1)[pair] if mark=='*' else LAMP_INKS[mark]


def tower_stone(tile,x,y,pair):
    """Coursed sandstone, with a stepped cornice on the battlements."""
    if not pair:
        return None
    if tile in (0x68,0x69,0x6a,0x3c):
        if y==4:
            return 15  # sunlit caps
        if y in (9,10,11):
            return (15,9,4)[y-9]
        if tile==0x68 and x<2 or tile==0x69 and x>=6:
            return 15 if tile==0x68 else 9
    if tile==0x4b and y>=12:
        return (15,10,9,4)[y-12]  # corbels above the moving section
    if tile==0x36 and x<2:
        return 15
    if tile==0x0a and x>=6:
        return 9
    course,row=divmod(y,5)
    joint=(x+(0,4,1,5)[course])%8
    if row==4:
        return 9
    if joint==0:
        return 9
    return 15 if row==0 and joint<=4 else 8


def masonry(x, y, courtyard):
    """64 x 32 running bond. Courses wrap at both edges, including the chamfers."""
    course, row = divmod(y % 32, 8)
    offset = (0, 9, 2, 12)[course]
    joint = (x + offset) % 64
    widths = ((19, 23, 22), (22, 18, 24), (23, 22, 19), (18, 24, 22))[course]
    for brick, width in enumerate(widths):
        if joint < width:
            break
        joint -= width
    body, mortar, light = (8, 9, 15) if courtyard else (11, 6, 12)
    if row == 7 or joint == 0 or (row == 6 and joint == width-1):
        return mortar
    # Broken lips at the upper corners suggest bevelled clay without covering
    # the wall in contrast noise. Keep the middle of each stone quiet.
    if row == 0 and 1 <= joint < (3, 7, 5)[(brick + course) % 3]:
        return light
    return body


def roof(x, y):
    # Convex glazed barrel tiles over the load-bearing fascia.
    if y < 8:
        return 3 if y == 6 else 12
    if y < 12:
        return (11, 12, 3, 12, 11, 6, 6, 11)[(x + (11-y)//2) % 8]
    return (10, 2, 4, 0)[y-12]


def eave(x, y):
    # Interlocking cedar brackets below the eaves.
    return ((4,4,2,2,2,2,2,4), (2,10,10,2,2,4,4,2),
            (4,2,10,2,4,4,2,4), (0,4,2,2,4,2,4,0),
            (0,0,4,2,2,4,0,0), (0,0,0,4,4,0,0,0))[y][x]


def pillar(x, y):
    if y % 16 in (0, 15):
        return (4, 4, 10, 2, 2, 4, 4, 0)[x]
    return (0, 4, 2, 10, 2, 2, 4, 0)[x]


def lattice(x, y):
    # Warm pierced screens. Chamfered diagonal bars meet at bronze pegs.
    a, b = (x-y) % 8, (x+y) % 8
    if y % 8 == 0:
        return 10 if x % 4 == 0 else 4
    if a == 0 or b == 0:
        return 10
    if a == 1 or b == 1:
        return 4
    return None


def lantern(tile, x, y, pair):
    lamp = ('..w...', '.www..', '.gggg.', 'gagagg', 'gagagg',
            'gaagag', '.gggg.', '.www..', '..g...', '..a...')
    column = x - (2 if tile in (0x14,0x67) else 0)
    dark = tile in UNLIT_LAMPS
    if y in (10,11) and column in (2,3):
        return (0,4,9,8)[pair] if dark else (2,10,7,1)[pair]
    if 0 <= column < 6:
        inks = {'.':None,'w':4,'g':9,'a':4} if dark else {'.':None,'w':4,'g':7,'a':10}
        return inks[lamp[y-6][column]]
    return None


@lru_cache(maxsize=3)
def relief(layout):
    charset=(Path(__file__).resolve().parents[1]/'assets/c64/rooms-v1/charsets.bin').read_bytes()
    return {(col*8+x,row*16+y) for row,tiles in enumerate(layout) for col,tile in enumerate(tiles)
            for y in range(16) for x in range(8)
            if (charset[(tile|(y//8)*128)*8+y%8]>>(6-2*(x//2)))&3}


def cast_metal(tile,x,y,pair):
    layout,left,top=ORNAMENTS[tile]
    x+=left
    y+=top
    shape=relief(layout)
    if (x,y+1) not in shape or (x+1,y) not in shape:
        return 4
    if (x,y-1) not in shape or (x-1,y) not in shape:
        return 10
    if layout==SHRINE:
        return (10,2,4,11)[y%4] if pair!=3 else (6,11,12,11)[x%4]
    if y>=28:
        return (10,2,9,4)[y-28]
    if y<10:
        return 7 if y%4==0 else 10
    if pair==3:
        return 0 if x<15 and y<20 else 6
    if x<17:
        return 10 if y in (11,15,19,22) else 8 if y<18 else 9
    # Staggered scallops follow the cast flank across character boundaries.
    u=(x+(3 if (y//4)%2 else 0))%6
    if (u,y%4) in ((0,0),(1,1),(2,2),(3,2),(4,1),(5,0)):
        return 10 if y<19 else 12
    return 12 if y<16 else 11


def architecture_pixel(tile, x, y, pair):
    """One 8 x 16 visual, in source cell coordinates. None exposes the wall."""
    if 0x15 <= tile <= 0x1d:
        if tile in (0x18, 0x19, 0x1a) and y >= 10:
            return (10, 2, 4, 4, 11, 0)[y-10]
        if (tile in (0x15,0x18,0x1b) and x < 2 or
            tile in (0x17,0x1a,0x1d) and x >= 6):
            return 4 if x in (0,7) else 10
        return lattice(x, y)
    if tile in (0x20,0x21,0x2c):
        if tile == 0x2c and y >= 14:
            return None
        # Both terminal halves have the same source code. Align each stile
        # with its termination; an eight-row cycle tiles without a short rung.
        if y % 8 in (0,1,4,5):
            return 10 if y % 4 == 0 else 4
        if x == 3:
            return 10
        return 4 if x == 4 else None
    if tile in (0x13,0x14,0x31) and y >= 6:
        return lantern(tile,x,y,pair)
    if not pair:
        return None
    if tile in ORNAMENTS:
        return cast_metal(tile,x,y,pair)
    if tile in (0x4d,0x4e,0x52):
        if y>=10:
            return (10,2,4,4,11,0)[y-10]
        return 10 if (x+y)%5==0 else 11 if pair==3 else 4
    if tile in (0x0d,0x25,0x26,0x38) or tile == 0x29 and y >= 6:
        if tile == 0x38 and y < 6:
            return pillar(x,y)
        return roof(x,y)
    if tile in (0x10,0x22,0x2a):
        if y < 12:
            return 3 if y == 6 else (12,11,11,6,11,12,11,6)[(x+y//3)%8]
        return (10,2,4,0)[y-12]
    if tile in (0x11,0x2d,0x39) and y >= 10:
        return (10, 2, 4, 4, 11, 0)[y-10]
    if tile in (0x12,0x13,0x14,0x1e,0x1f,0x28,0x31,0x3b) and y < 6:
        return eave(x,y)
    if tile in (0x2b,0x3d,0x24,0x3a):
        return 10 if y % 4 < 2 else 4
    if tile == 0x28:
        return 10 if y == 8 or x == 1 else 4
    return pillar(x,y)


def foreground(room, tile, x, y, pair):
    if room==3 and tile in TOWER_TILES:
        return tower_stone(tile,x,y,pair)
    if 3<=room<18:
        if room>=10 and tile in VAULT_LAMPS:
            return vault_lantern(tile,x,y,pair)
        deck=0x11 if room<10 else 0x0d
        if tile==0x60 or 0x71<=tile<=0x7c:
            owns,ink=bomb_ink(tile,x,y,room<10)
            if owns:return ink
            tile=deck
        elif tile==0x7d or (room>=10 and tile==0x70):
            tile=deck  # same platform glyph after the blast, also used in room 12
    if room < 3:
        return architecture_pixel(tile,x,y,pair)
    if room < 10:
        if tile in UNLIT_LAMPS:
            if y>=6:
                return lantern(tile,x,y,pair)
            tile=0x13 if tile==0x66 else 0x14  # same bracket as its lit state
        if tile == 0x40:
            # Room 5 editor preview ($A200/$A600). In game, the mounting
            # cap (pair 3) takes its ink from the live cell's color RAM.
            return {0:None, 2:1, 3:0}[pair]
        # $A170: pair 3 continues the $32 post into the platform. Pair 1
        # belongs to the floor lip, including where both occur on one row.
        if tile==0x2e and y<8 and pair==3:
            tile=0x32
        if tile in (0x2e,0x2f,0x30,0x3e):
            if not pair:
                return None
            if y < 8:
                return (14,12,11,6)[(x//2+y//2)%4] if pair==1 else 11
            return (12,14,11,6,11,11,6,6)[y-8]
        color=architecture_pixel(tile,x,y,pair)
        if tile in (0x13,0x14,0x31) and y>=6:
            return color
        return {2:11,4:6,10:12}.get(color,color)
    if not pair:
        return None
    if tile in (0x07,0x08,0x46,0x48):
        return 6 if y%8 in (0,7) or x%2 else 14
    if tile in (0x10,0x11):
        return (14,12,8,11,6,11)[(x + (y if tile==0x10 else -y)) % 6]
    if y < 6:
        return 12 if y%4==0 else (14,11,11,6)[x%4]
    if y < 10:
        return (8,9,11,6)[y-6]
    return 12 if x==2 and y<14 else 11 if x<5 else 6


def stamps(charset):
    """Store each distinct half once: source rows, artist's opacity, four planes."""
    unique, lookup = [], bytearray(3*256)
    def intern(room,code,source,painter=None):
        tile, half = code & 127, code >> 7
        draw=painter if painter else lambda t,x,y,pair:foreground(room,t,x,y,pair)
        pixels = [[draw(tile,x,y+half*8,(bits >> (6-2*(x//2))) & 3)
                       for x in range(8)] for y,bits in enumerate(source)]
        mask = bytes(sum((c is not None) << (7-x) for x,c in enumerate(row)) for row in pixels)
        planes = bytes(sum((((c or 0) >> p) & 1) << (7-x) for x,c in enumerate(row))
                           for p in range(4) for row in pixels)
        stamp = source + mask + planes
        if stamp not in unique:
            unique.append(stamp)
        return unique.index(stamp)+1
    for group, (room, tiles) in enumerate(((0,COURTYARD_BASE),(3,GALLERY_ARCH),(10,VAULT))):
        for code in (*tiles, *(tile+128 for tile in tiles)):
            offset = (2048 if room==10 else 0)+code*8
            lookup[group*256+code] = intern(room,code,charset[offset:offset+8])
    # $40CE-$4127 drives the actual flame. $93 and $b1 share all eight
    # lower rows in bank $a000; $94 has its light two pixels farther right.
    for code,base,shift in ((0x93,0xcc,4),(0x94,0x33,2)):
        for phase in range(4):
            source=bytearray(charset[code*8:code*8+8])
            source[2:4]=bytes([base|(phase<<shift)])*2
            lookup.append(intern(0,code,source))
    # Append after the existing editor stamps: saved paintings refer to their IDs.
    for tile in UNLIT_LAMPS:
        for code in (tile,tile|128):
            lookup[256+code]=intern(3,code,charset[code*8:code*8+8])
    # $412A-$412F also writes the right unlit wick, two rows in $E7.
    for phase in range(4):
        source=bytearray(charset[0xe7*8:0xe8*8])
        source[2:4]=bytes([0x22|(phase<<2)])*2
        lookup.append(intern(3,0xe7,source))
    # Append the hazard art to keep saved editor stamp IDs stable. $3228
    # places each six-cell flash using the strings at $4612..$4625.
    hazards=(0x60,*range(0x71,0x7e))
    for group,room,bank,tiles in ((1,6,0,hazards),(2,10,2048,hazards+(0x70,))):
        for tile in tiles:
            for code in (tile,tile|128):
                offset=bank+code*8
                lookup[group*256+code]=intern(room,code,charset[offset:offset+8])
    # Keep the IDs of existing graphics-editor paintings stable.
    for code in (0x47,0xc7):
        lookup[code]=intern(2,code,charset[code*8:code*8+8])
    # Room 4 reuses mountain glyphs for tower walls. Keep a separate map
    # for the lower courses so the skyline and other rooms keep their inks.
    tower_map=lookup[256:512]
    for tile in TOWER_TILES:
        for code in (tile,tile|128):
            tower_map[code]=intern(3,code,charset[code*8:code*8+8])
    lookup.extend(tower_map)
    # $40D0/$411C write the wick into $AC9A/B and $ACA2/3. The rest of
    # these two live scanlines is zero in this bank. Keep the original
    # unanimated rows addressable as well, including their mounting arm.
    for tile in VAULT_LAMPS:
        for code in (tile,tile|128):
            offset=2048+code*8
            lookup[512+code]=intern(10,code,charset[offset:offset+8])
    for code,shift in ((0x93,4),(0x94,2)):
        offset=2048+code*8
        for phase in range(4):
            source=bytearray(charset[offset:offset+8])
            source[2:4]=bytes([phase<<shift])*2
            lookup.append(intern(10,code,source))
    # Roof stamps follow all stable editor IDs. The extra table uses word
    # IDs; the existing room banks remain byte tables in the executable.
    lookup=list(lookup)
    roof=[0]*(2*(max(PAGODA_TILES)+1))
    for tile in PAGODA_TILES:
        for half in (0,1):
            code=tile|(half<<7)
            offset=2048+code*8
            roof[2*tile+half]=intern(15,code,charset[offset:offset+8],pagoda_roof)
    lookup.extend(roof)
    return lookup, b''.join(unique)


def runtime_stamp_index(library, repainted):
    """Use live VIC inks for each unpainted half of the gallery ceiling spear."""
    lookup = library.copy()
    for code in (0x40, 0xc0):
        index = 256 + code  # gallery bank
        if lookup[index] not in repainted:
            lookup[index] = 0
            lookup[TOWER_INDEX+code] = 0
    return lookup
