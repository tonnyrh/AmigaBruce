"""Exercise Classic -> Enhanced -> Classic on a dedicated running WinUAE."""
import argparse
import hashlib
import json
import re
import struct
import time
import wave
from pathlib import Path
from PIL import Image

from build_enhanced_art import PALETTE, display_pixels, EDIT_DIR
from enhanced_architecture import COURTYARD, GALLERY, VAULT, TOWER_INDEX, TOWER_TILES, foreground, masonry
from enhanced_architecture import PAGODA_INDEX, PAGODA_TILES, VAULT_LAMP_INDEX, VAULT_LAMPS
from capture_paula_stream import elf_symbols, elf_hunk_index
from title_reference import picker_reference, reference
from winuae_ipc import command, tap_fire

ROOT = Path(__file__).resolve().parents[1]

def displayed_strike(pose,face):
    slot={6:8,0x1a:13,0x1c:10}[pose]
    return display_pixels(2,slot,face,EDIT_DIR)

def check_bruce_cache(cache):
    """Compare all editor poses with the source mask and the actual A500 inks."""
    from build_c64_sprites import SOURCE, SHA, source_frame
    from enhanced_fighters import BRUCE_SOURCE_POSES, BRUCE_UNDIRECTED
    raw=SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA
    header=(ROOT/'amiga/enhanced_art.h').read_text()
    entries=re.search(r'enhanced_bruce_views\[\]=\{(.*?)\};',header,re.S)[1]
    frames=[tuple(map(int,row.split(','))) for row in re.findall(r'\{([\d,]+)\}',entries)]
    checked=0
    strikes=[]
    for slot in BRUCE_SOURCE_POSES:
        if slot in (3,4):continue
        for face in ((1,) if slot in BRUCE_UNDIRECTED else (0,1)):
            pose=BRUCE_SOURCE_POSES[slot][face]
            words,origin,top,width,height=frames[slot*2+face]
            offset=words*2
            lane=4 if width<=16 else 6
            reference,_=source_frame(raw,0,pose,face)
            colors=display_pixels(2,slot,face,EDIT_DIR)
            for y in range(21):
                for x in range(48):
                    dx,dy=x-origin,y-top
                    visible=False
                    if 0<=dx<width and 0<=dy<height:
                        byte=offset+dy*8*lane+dx//8
                        bit=128>>(dx%8)
                        visible=bool(cache[byte]&bit)
                        assert all(bool(cache[byte+2*lane*p]&bit)==visible for p in range(4))
                        if visible:
                            color=sum((1<<p) for p in range(4) if cache[byte+2*lane*p+lane]&bit)
                            assert color==colors[y*48+x]
                    assert visible==(reference[y*48+x] is not None),(pose,x,y)
            checked+=1
            if slot in (8,13,10):strikes.append(pose)
    return dict(bruce_editor_views=checked,bruce_strike_poses=strikes)

def check_enemy_cache(cache):
    """Check every visible mask/guard bit in the actual expanded A500 cache."""
    from build_c64_sprites import SOURCE, SHA, source_frame
    image = SOURCE.read_bytes()
    assert hashlib.sha256(image).hexdigest()==SHA
    header=(ROOT/'amiga/enhanced_art.h').read_text()
    def offsets(name):
        return list(map(int,re.search(name+r'\[\]=\{([^}]+)\}',header)[1].strip().split(',')))
    normal,alternate=offsets('enhanced_npc_words'),offsets('enhanced_alt_run_words')
    assert len(normal)==140 and len(alternate)==16
    count=0
    for actor in range(2):
        for face in (0,1):
            for pose in range(35):
                source,_=source_frame(image,actor+1,pose*2,face)
                occupied=[divmod(i,48) for i,v in enumerate(source) if v is not None]
                top=min(y for y,x in occupied);left=min(x for y,x in occupied)
                lane=4 if max(x for y,x in occupied)-left+1<=16 else 6
                words=[normal[(actor*2+face)*35+pose]]
                if 7<=pose<=10:words.append(alternate[(actor*2+face)*4+pose-7])
                for word in words:
                    for y in range(top,max(y for y,x in occupied)+1):
                        row=sum(1<<(8*lane-1-x+left) for yy,x in occupied if yy==y)
                        at=word*2+8*lane*(y-top)
                        for plane in range(4):
                            start=at+2*lane*plane
                            actual=int.from_bytes(cache[start:start+lane],'big')
                            assert actual==row,(actor,pose,face,y,plane)
                    count+=1
    return count

def fixed_tower(room,col,y,tile):
    # $3702 swaps these two seven-cell bands while the screen is sampled.
    moving=88<=y<104 and (9<=col<16 or 21<=col<28)
    return room==3 and y>=56 and tile in TOWER_TILES and not moving


def check_structure(ram,bitmap,enhanced=False):
    """Compare the A500 backplate to the source glyph or authored architecture."""
    assert len(ram)==65536 and len(bitmap)==40960
    word=lambda at: ram[at]|(ram[at+1]<<8)
    room=ram[0x29];bank=0xa000+((ram[0xf2]-0x38)//2)*2048
    colors=word(0x480b+room*2);raster=word(0x4833+room*2)
    charset=(ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes()
    structures=COURTYARD if room<3 else GALLERY if room<10 else VAULT
    from bruce_editor_data import EDIT_DIR
    if enhanced and 10<=room<18:
        return check_edited_structure(ram,bitmap,bank,colors,raster,structures+VAULT_LAMPS,charset,EDIT_DIR)
    if enhanced and (room==3 or any(EDIT_DIR.glob('stamp-*.png')) or any(EDIT_DIR.glob('wall-*.png'))):
        return check_edited_structure(ram,bitmap,bank,colors,raster,structures,charset,EDIT_DIR)
    def pixel(at,x):
        return sum(((bitmap[at+40*p]>>(7-x))&1)<<p for p in range(4))
    tested=0
    for y in range(24,200):
        band=0
        for edge in ram[raster:raster+3]:
            if edge==253 or y+51<edge+3:break
            band+=1
        for col in range(40):
            cell=(y//8)*40+col;code=ram[0x8c00+cell]
            # Fixed roofs, floors, ladders, posts and lattice. Exclude
            # moving objects and cells which a pickup could have queued.
            tile=code&127
            live_spear=3<=room<10 and tile==0x40
            room5_lamp=room==4 and col in (11,28) and 56<=y<72
            tower=fixed_tower(room,col,y,tile)
            if y<88 and not (live_spear or room5_lamp or tower):continue
            if tile not in structures and tile!=0 and not tower:continue
            bits=ram[bank+code*8+y%8];at=(32+y)*160+col
            native=enhanced and (tile in structures or tower) and not live_spear and bits==charset[bank-0xa000+code*8+y%8]
            dim_wick=3<=room<10 and code==0xe7
            if room<10 and (code in (0x93,0x94,0xb1) or dim_wick) and y%8 in (2,3):
                # Source $40CE-$412F updates only the wick pair. The painted
                # phase can trail RAM. Require one legal phase for BOTH rows.
                pos=4 if code==0x94 or dim_wick else 2
                shift=6-pos
                first=at-(y%8-2)*160
                if enhanced:
                    wick=(0,4,9,8) if dim_wick else (2,10,7,1)
                else:
                    wick=tuple(ram[colors+band*3+i]&15 for i in range(3))+(ram[0xd800+cell]&7,)
                observed=pixel(first,pos)
                assert observed in wick,(room+1,cell,code,observed,wick)
                base=0x22 if dim_wick else 0x33 if pos==4 else 0xcc
                bits=base|(wick.index(observed)<<shift)
                native=enhanced
            for x in range(8):
                pair=(bits>>(6-(x//2)*2))&3
                if native:
                    expected=foreground(room,tile,x,(8 if code&128 else 0)+y%8,pair)
                elif pair:
                    expected=ram[0xd800+cell]&7 if pair==3 else ram[colors+band*3+pair]&15
                elif enhanced:
                    expected=None
                else:
                    continue
                if expected is None:
                    expected=masonry(col*8+x,y,room<3)
                actual=pixel(at,x)
                assert expected==actual,(room+1,col*8+x,y,code,expected,actual)
                tested+=1
    assert tested>4000
    return tested


def check_edited_structure(ram,bitmap,bank,colors,raster,structures,charset,edits):
    """Same fixed-cell check with the artist's PNG masters. Lamp publication
    may trail the sampled RAM; require one consistent phase across all 8 rows.
    """
    from bruce_editor_data import catalog, load, ALPHA
    from enhanced_architecture import runtime_stamp_index, stamps
    room=ram[0x29];group=0 if room<3 else 1 if room<10 else 2
    lookup,base=stamps(charset)
    assets=[a for a in catalog() if a.key.startswith(('wall-','stamp-')) or (room==3 and a.key=='sky')]
    masters={a.key:load(a,edits)[0] for a in assets}
    repainted={int(a.key.split('-')[1]) for a in assets if a.key.startswith('stamp-') and tuple(masters[a.key])!=a.pixels}
    lookup=runtime_stamp_index(lookup,repainted)
    wall=masters['wall-warm' if group==0 else 'wall-cool'];tested=0
    for top in range(24,200,8):
        panorama=room==3 and top<88
        for col in range(40):
            cell=top//8*40+col;code=ram[0x8c00+cell];tile=code&127
            if panorama and top<56:tile=0  # the four source rows contain only scenery
            room5_lamp=room==4 and col in (11,28) and 56<=top<72
            tower=fixed_tower(room,col,top,tile)
            vault_lamp=10<=room<18 and tile in VAULT_LAMPS
            pagoda=room==15 and top<120 and 13<=col<=27 and tile in PAGODA_TILES
            if top<88 and not ((group==1 and tile==0x40) or room5_lamp or panorama or vault_lamp or pagoda):continue
            if tile not in structures and tile!=0 and not tower and not panorama and not pagoda:continue
            lamp=room<10 and (code in (0x93,0x94,0xb1) or (group==1 and code==0xe7))
            phase_offset=8 if code==0xe7 else 4 if code==0x94 else 0
            offset=TOWER_INDEX if tower else group*256
            ids=(lookup[768+phase_offset:][:4] if lamp else [lookup[offset+code]])
            if pagoda:
                ids=[lookup[PAGODA_INDEX+2*tile+(code>>7)]]
            if vault_lamp and code in (0x93,0x94):
                lamp=True
                start=VAULT_LAMP_INDEX+phase_offset
                ids.extend(lookup[start:start+4])
            actual=[]
            for dy in range(8):
                row=(32+top+dy)*160+col
                actual.extend(sum(((bitmap[row+p*40]>>(7-x))&1)<<p for p in range(4)) for x in range(8))
            for sid in ids:
                expected=[]
                for dy in range(8):
                    y=top+dy;bits=ram[bank+code*8+dy]
                    if lamp and dy in (2,3):bits=base[(sid-1)*48+dy]
                    native=sid and base[(sid-1)*48+dy]==bits
                    band=0
                    for edge in ram[raster:raster+3]:
                        if edge==253 or y+51<edge+3:break
                        band+=1
                    for x in range(8):
                        pen=ALPHA
                        if tile and native:pen=masters[f'stamp-{sid:03}'][dy*8+x]
                        elif tile:
                            pair=(bits>>(6-2*(x//2)))&3
                            if pair:pen=ram[0xd800+cell]&7 if pair==3 else ram[colors+band*3+pair]&15
                        if pen==ALPHA:
                            pen=masters['sky'][(y-24)*320+col*8+x] if panorama else wall[y%32*64+(col*8+x)%64]
                        expected.append(pen)
                if actual==expected:break
            else:raise AssertionError(('edited backplate',room+1,cell,code))
            tested+=64
    assert tested>4000
    return tested


def check(folder, pid, tour=False, strikes=False, foley=False, poses=False, buttons=False):
    log = (folder/'winuaebootlog.txt').read_text(errors='replace')
    pipe = re.findall(r"IPC: Named Pipe '([^']+)' open",log)[-1]
    def cmd(s):
        return command(pipe,s,timeout=15,expected_pid=pid)
    def read(at,size):
        reply=cmd(f'DBG m {at:x} 1')
        match=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',reply)
        return bytes.fromhex(match[1])[:size] if match else b''
    def value(at,size=4):
        return int.from_bytes(read(at,size),'big')
    def key(name):
        cmd('EVT KEY_'+name+' 1');time.sleep(.28);cmd('EVT KEY_'+name+' 0')
    def wait(fn,limit=120):
        end=time.monotonic()+limit
        while time.monotonic()<end:
            try:
                answer=fn()
            except (OSError,TimeoutError):
                answer=False
            if answer:return answer
            time.sleep(.12)
        raise AssertionError(fn.__name__)
    def dump(name,at,size):
        p=folder/name
        if not at or 'Wrote ' not in cmd(f'DBG S {p} {at:x} {size:x}'):return b''
        return p.read_bytes()
    def backplate(label,enhanced):
        # Freeze the emulator across both debugger reads. A source tick may
        # already have queued the next trap tile while the previous one is
        # still drawn. Require a complete matching backplate within the window.
        def toggle_pause():
            cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.08)
        for attempt in range(12):
            toggle_pause()
            try:
                memory=dump(label+'-ram.bin',ram,65536)
                bg=dump(label+'-background.bpl',value(addr('background')),40960)
            finally:
                toggle_pause()
            try:
                return bg,check_structure(memory,bg,enhanced)
            except AssertionError:
                if attempt==11:raise
                time.sleep(.25)
    def visible():
        match=re.search(r'COP1LC: \$([0-9a-f]+)',cmd('DBG c'),re.I)
        if not match:return b''
        copper=dump('copper.bin',int(match[1],16),136)
        if len(copper)!=136:return b''
        w=struct.unpack('>68H',copper)
        if w[0:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
        front=w[19]<<16|w[21]
        return dump('visible.bpl',front,40960) if 0<front<=0x80000-40960 else b''
    def room5_lanterns():
        # Sample the running room loop; entering the room alone only checks one phase.
        seen=set()
        def sample_lamps():
            bg,_=backplate('room05',True)
            memory=(folder/'room05-ram.bin').read_bytes()
            pair=tuple(memory[0x8c00+7*40+col] for col in (11,28))
            assert pair[0] in (0x13,0x66) and pair[1] in (0x14,0x67),pair
            if not set(pair)<=seen:
                (folder/f'room05-lamps-{pair[0]:02x}-{pair[1]:02x}.bpl').write_bytes(bg)
                seen.update(pair)
            return len(seen)==4
        wait(sample_lamps,30)
        return sorted(seen)
    def visible_strike(data,poses):
        # Locate the whole painted actor on the published playfield. Starting
        # from a distinctive contiguous stripe avoids relying on source RAM
        # and the Copper front buffer describing exactly the same logic step.
        if not data:return None
        rows=bytearray(320*256)
        for p in range(4):
            plane=b''.join(data[y*160+p*40:y*160+p*40+40] for y in range(256))
            bits=Image.frombytes('1',(320,256),plane).convert('L').tobytes()
            for i in range(320*56,320*232):
                if bits[i]:rows[i]|=1<<p
        for pose,right,face in poses:
            art=displayed_strike(right,face)
            opaque=[(x,y,art[y*48+x]) for y in range(21) for x in range(48) if art[y*48+x]!=15]
            y=9 if right==0x1c else 5
            x=next(x for x in range(44) if all(art[y*48+i]!=15 for i in range(x,x+5)))
            stripe=bytes(art[y*48+i] for i in range(x,x+5))
            at=rows.find(stripe,320*56)
            while at>=0:
                left,top=at%320-x,at//320-y
                if all(0<=left+dx<320 and 0<=top+dy<256 and rows[(top+dy)*320+left+dx]==c for dx,dy,c in opaque):
                    return pose
                at=rows.find(stripe,at+1)
        return None
    def capture(label,enhanced):
        data=wait(visible)
        (folder/(label+'.bpl')).write_bytes(data)
        copper=struct.unpack('>68H',(folder/'copper.bin').read_bytes())
        assert copper[34:66:2]==tuple(range(0x180,0x1a0,2))
        colors=copper[35:66:2]
        if enhanced:
            assert colors[:15]==PALETTE[:15]
            if value(ram+0x29,1)<18:
                assert colors[15]==PALETTE[15]
        else:
            source=(ROOT/'amiga/main.c').read_text()
            expected=re.search(r'\bpalette\[16\]=\{([^}]+)\}',source)[1]
            assert colors==tuple(int(c,16) for c in expected.split(','))
        image=Image.new('P',(320,256))
        image.putpalette([((color>>shift)&15)*17 for color in colors for shift in (8,4,0)])
        image.putdata([sum(((data[y*160+x//8+p*40]>>(7-x%8))&1)<<p for p in range(4))
                       for y in range(256) for x in range(320)])
        image.resize((640,512),Image.Resampling.NEAREST).save(folder/(label+'.png'))
    room_select=False
    def menu(enhanced):
        expected=reference(enhanced=enhanced,room_select=room_select)
        wait(lambda:visible()==expected,240)
    menu(False)
    task=value(value(4)+276);cli=value(task+172)*4;node=value(cli+60)*4;hunks=[]
    while node:
        hunks.append(node+4);node=value(node)*4
        assert len(hunks)<=8
    bss,symbols=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
    bss_hunk=elf_hunk_index(ROOT/'amiga/out/bruce_amiga.elf')
    def addr(name):
        return hunks[bss_hunk]+symbols[name]-bss
    ram=addr('m');records=[]
    def sample():
        return dict(field=value(addr('game_field_last')),steps=value(addr('actor_logic_steps'),2),
                    flags=list(read(ram+0x95,3)),fault=value(addr('source_fault'),2),
                    missed=value(addr('source_clock_missed')),room=value(ram+0x29,1)+1)
    def check_buttons(label):
        def controls(direction,fire):
            pins=read(ram+0x98,4)
            return len(pins)==4 and (pins[0],pins[3])==(direction,fire)
        for held,direction,fire,state in ((('FIRE_BUTTON',),15,0,17),(('2ND_BUTTON',),14,1,5),
                (('RIGHT','2ND_BUTTON'),6,1,7),(('LEFT','2ND_BUTTON'),10,1,6),
                (('UP',),14,1,5),(('2ND_BUTTON','FIRE_BUTTON'),14,0,None)):
            wait(lambda:controls(15,1) and value(ram+0xbf,1)==0,30)
            try:
                for button in held:cmd(f'EVT JOY2_{button} 1')
                wait(lambda:controls(direction,fire) and (state is None or value(ram+0xbf,1)==state),20)
            finally:
                for button in held:cmd(f'EVT JOY2_{button} 0')
            records.append(dict(look=label,buttons=held,direction=direction,fire_pin=fire,state=state))
    def check_bruce_actions(enhanced,label):
        from build_c64_sprites import SOURCE, SHA, source_frame
        source=SOURCE.read_bytes()
        assert hashlib.sha256(source).hexdigest()==SHA
        for pose,slot,face,buttons in ((0x20,16,1,('UP',)),(0x42,17,1,('DOWN',)),
                                       (0x40,17,0,('DOWN','LEFT'))):
            if enhanced:
                art=display_pixels(2,slot,face,EDIT_DIR)
            else:
                art=[15 if pen is None else pen for pen in source_frame(source,0,pose,face)[0]]
            dots=[(i%48,i//48,c) for i,c in enumerate(art) if c!=15]
            def published():
                if value(ram+0x4f48,1)!=pose:return False
                x=value(ram+0x9e,1)*2-40
                data=visible()
                if not data:return False
                for top in range(120,211):
                    if all(sum(((data[(top+dy)*160+(x+dx)//8+p*40]>>(7-(x+dx)%8))&1)<<p
                               for p in range(4))==c for dx,dy,c in dots):
                        (folder/f'{label}-pose-{pose:02x}.bpl').write_bytes(data)
                        return True
                return False
            try:
                # Select facing on the ground before holding straight down.
                for button in reversed(buttons):cmd(f'EVT JOY2_{button} 1')
                wait(published,45)
            finally:
                for button in buttons:cmd(f'EVT JOY2_{button} 0')
            wait(lambda:value(ram+0xbf,1)==0,30)
            records.append(dict(look=label,joystick=list(buttons),displayed_pose=pose))
    def play(enhanced,label):
        if room_select:
            key('RETURN');assert not value(addr('game_field_active'),1)
            tap_fire(cmd)
        else:key('RETURN')
        wait(lambda:value(addr('game_field_active'),1) and value(addr('actor_logic_steps'),2)>=2)
        assert value(addr('enhanced_active'),1)==int(enhanced)
        if foley:assert value(addr('foley_active'),1)==int(enhanced)
        state=sample();assert state['room']==1 and not state['fault']
        bg,fixed_pixels=backplate(label,enhanced)
        capture(label,enhanced)
        if buttons and label!='restored':check_buttons(label)
        if poses and label!='restored':check_bruce_actions(enhanced,label)
        if enhanced:
            if foley:
                # Real input. Only the observed mask is diagnostic; the game
                # and all three source sound queues run normally throughout.
                mask=lambda:value(addr('foley_played_mask'),4)
                def await_sounds(needed):
                    deadline=time.monotonic()+30
                    while time.monotonic()<deadline:
                        observed=mask()
                        if observed&needed==needed:return
                        with (folder/'foley-events.txt').open('a') as trace:
                            trace.write(f"{observed:04x} state={value(ram+0xbf,1)} count={value(ram+0xce,1)} "
                                        f"step={value(addr('actor_logic_steps'),2)} requests={value(addr('audio_requests_mask'),2):04x}\n")
                        time.sleep(.25)
                    raise AssertionError(('playback mask',needed,mask()))
                cmd(f'EVT AKS_VIDEORECORDFILE "{folder/"combat-audio.avi"}"')
                cmd('EVT AKS_VIDEORECORD 1')
                try:
                    cmd('EVT JOY2_FIRE_BUTTON 1')
                    await_sounds(3)
                    cmd('EVT JOY2_RIGHT 1')
                    await_sounds(12)
                    time.sleep(.25)
                    records.append(dict(joystick_foley_mask=mask()))
                finally:
                    cmd('EVT JOY2_RIGHT 0');cmd('EVT JOY2_FIRE_BUTTON 0')
                    cmd('EVT AKS_VIDEORECORD 0')
                # Isolated audition in this owned emulator. P freezes the
                # actors; enable only Paula service and feed its pending cue
                # selector. C64 RAM and source attack rules are not injected.
                from build_enhanced_audio import CUES,LEVELS,sample_path
                def write_byte(at,b):
                    cmd(f'DBG W {at:x} {b:02x}')
                key('P')
                wait(lambda:not value(addr('source_audio_active'),1))
                bank_base=value(addr('sfx_pcm'))+int(re.search(r'BL_SOURCE_AUDIO_CHIP_BYTES (\d+)',
                    (ROOT/'core/source_audio_data.h').read_text())[1])
                recorded=set(folder.glob('*.avi'))
                played=[]
                cmd('DBG Ma 1')
                cmd(f'EVT AKS_VIDEORECORDFILE "{folder/"foley-bank.avi"}"')
                cmd('EVT AKS_VIDEORECORD 1')
                try:
                    write_byte(addr('source_audio_active'),1)
                    time.sleep(.25)
                    for cue,(name,_,_,_) in enumerate(CUES):
                        for _ in range(2):
                            variant=value(addr('foley_variant')+cue,1)
                            with wave.open(str(sample_path(name,variant)),'rb') as w:
                                n=w.getnframes()
                                samples=struct.unpack(f'<{n}h',w.readframes(n))
                            pcm=bytes(min(LEVELS,key=lambda v:abs(s-256*v))&255 for s in samples)
                            write_byte(addr('foley_voice')+1,2+cue)
                            wait(lambda:dump('foley-page.bin',bank_base,n)==pcm,8)
                            played.append(f'{name}_{variant}')
                            time.sleep(.28)
                    assert mask()==(1<<(2*len(CUES)))-1
                finally:
                    cmd('EVT AKS_VIDEORECORD 0');cmd('DBG Ma f')
                    write_byte(addr('source_audio_active'),0)
                    key('P')
                recordings=set(folder.glob('*.avi'))-recorded
                assert len(recordings)==1
                records.append(dict(controlled_foley_bank=played,recording=recordings.pop().name))
            if strikes:
                size=int(re.search(r'#define ENHANCED_TILE_BASE (\d+)',(ROOT/'amiga/enhanced_art.h').read_text())[1])
                cache=dump('fighter-cache.bin',value(addr('fighter_dma')),size)
                assert len(cache)==size
                records.append(dict(**check_bruce_cache(cache),enemy_source_views=check_enemy_cache(cache)))
                cmd('EVT JOY2_FIRE_BUTTON 1')
                try:
                    punch=wait(lambda:visible_strike(visible(),((4,6,0),(6,6,1))),30)
                    cmd('EVT JOY2_RIGHT 1')
                    kick=wait(lambda:visible_strike(visible(),((0x1c,0x1c,1),)),40)
                    records.append(dict(joystick_visible_punch=punch,joystick_visible_kick=kick))
                finally:
                    cmd('EVT JOY2_RIGHT 0');cmd('EVT JOY2_FIRE_BUTTON 0')
            wait(lambda:read(ram+0x95,3)==b'\x01\x81\x41' and value(addr('actor_logic_steps'),2)>40)
            first=sample();time.sleep(3.5);last=sample()
            assert last['steps']>first['steps'] and not last['fault']
            records.append(dict(both_start=first,both_end=last))
            cmd('EVT JOY2_RIGHT 1');time.sleep(.5);cmd('EVT JOY2_RIGHT 0')
            (folder/'enhanced-actors.bpl').write_bytes(wait(visible))
            if tour:
                visits=[]
                for room in range(2,21):
                    if room==2:cmd('EVT JOY2_FIRE_BUTTON 1')
                    key('F10')
                    wait(lambda:not value(addr('source_audio_active'),1),8)
                    charset=dump('map-charset.bin',ram+0xa000,8192)
                    expect=picker_reference(room-1,charset)
                    wait(lambda:visible()==expect,8)
                    if room==2:
                        frozen=dump('browsing-before.bin',ram,65536)
                        key('RETURN')
                        for button,target in (('F9',0),('F9',19),('F10',0),('F10',1)):
                            key(button)
                            target_image=picker_reference(target,charset)
                            wait(lambda:visible()==target_image,8)
                        assert frozen==dump('browsing-after.bin',ram,65536)
                        cmd('EVT JOY2_FIRE_BUTTON 0');time.sleep(.2)
                    assert value(ram+0x29,1)+1==room-1
                    tap_fire(cmd)
                    try:
                        wait(lambda:value(ram+0x29,1)+1==room,15)
                    except AssertionError as error:
                        raise AssertionError((room,sample(),value(addr('source_audio_active'),1),
                            value(addr('game_field_loading'),1),value(ram+0x48,1),cmd('DBG r'))) from error
                    first_step=value(addr('actor_logic_steps'),2)
                    wait(lambda:2<=((value(addr('actor_logic_steps'),2)-first_step)&65535)<128)
                    now=sample()
                    assert now['room']==room and not now['fault'],now
                    visits.append(room)
                    if room in (2,5,6,12,19,20):
                        capture(f'room-{room:02}',True)
                    if room in (2,5,6,7,9,10,12):
                        _,tested=backplate(f'room{room:02}',True)
                        records.append(dict(room=room,fixed_pixels=tested))
                    if room==5:
                        records.append(dict(room=room,lantern_states=room5_lanterns()))
                    if room==13:
                        wait(lambda:all(b&1 for b in read(ram+0x96,2)),40)
                        records.append(dict(room=room,both_enemies_after_fire=True))
                records.append(dict(debug_room_visits=visits))
        records.append(dict(look=label,state=state,fixed_pixels=fixed_pixels,background_sha256=hashlib.sha256(bg).hexdigest()))
        key('F8' if room_select else 'F10');menu(enhanced)
        return bg
    base=play(False,'classic')
    key('F4');menu(True)
    if tour or strikes or foley:
        cmd('EVT KEY_SHIFT_LEFT 1')
        try:key('D')
        finally:cmd('EVT KEY_SHIFT_LEFT 0')
        wait(lambda:visible()==reference(debug=True))
        key('F1');key('F2')
        wait(lambda:visible()==reference(debug=True,infinite=True,invincible=True))
        if tour:
            key('F3');room_select=True
            for button,number in (('F9',19),('F10',0)):
                key(button)
                expected=reference(debug=True,infinite=True,invincible=True,room_select=True,room=number)
                wait(lambda:visible()[110*160:]==expected[110*160:],8)
        key('F5');menu(True)
    alternate=play(True,'enhanced')
    key('F4');menu(False);restored=play(False,'restored')
    # First two rows of sky are static on this route, with no HUD or actors.
    area=slice((32+24)*160,(32+40)*160)
    assert base[area]==restored[area] and base[area]!=alternate[area]
    if tour:
        cmd('EVT KEY_SHIFT_LEFT 1')
        try:key('D')
        finally:cmd('EVT KEY_SHIFT_LEFT 0')
        key('F10')
        selected=reference(debug=True,infinite=True,invincible=True,room_select=True,room=1)
        wait(lambda:visible()[110*160:]==selected[110*160:],12)
        key('RETURN');assert not value(addr('game_field_active'),1)
        tap_fire(cmd)
        wait(lambda:value(addr('game_field_active'),1) and value(ram+0x29,1)==1)
        wait(lambda:value(addr('actor_logic_steps'),2)>2)
        key('F9');wait(lambda:not value(addr('source_audio_active'),1))
        key('F8');menu(False)
        assert value(ram+0x29,1)==1
        records.append(dict(debug_menu_start_room=2,unconfirmed_jump_cancelled=True))
    if buttons:
        start_room=1 if tour else 0
        cmd('EVT KEY_SHIFT_LEFT 1')
        try:key('D')
        finally:cmd('EVT KEY_SHIFT_LEFT 0')
        if not room_select:key('F3')
        cheats=tour or strikes or foley
        key_state=reference(debug=True,room_select=True,room=start_room,infinite=cheats,invincible=cheats)
        wait(lambda:visible()[110*160:]==key_state[110*160:])
        cmd('EVT JOY2_2ND_BUTTON 1');time.sleep(.5);cmd('EVT JOY2_2ND_BUTTON 0')
        assert not value(addr('game_field_active'),1)
        tap_fire(cmd);wait(lambda:value(addr('game_field_active'),1) and value(addr('actor_logic_steps'),2)>2)
        key('F10');wait(lambda:not value(addr('source_audio_active'),1))
        cmd('EVT JOY2_2ND_BUTTON 1');time.sleep(.5);cmd('EVT JOY2_2ND_BUTTON 0')
        assert value(ram+0x29,1)==start_room and not value(addr('source_audio_active'),1)
        tap_fire(cmd);wait(lambda:value(ram+0x29,1)==start_room+1)
        records.append(dict(room_picker_confirmed_only_by_primary=True))
    (folder/'result.json').write_text(json.dumps(records,indent=2)+'\n')
    print('PASS both menu choices, live room 1, both NPCs and return to Classic')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('pid',type=int)
    p.add_argument('--tour',action='store_true',help='visit the other 19 rooms through the debug controls')
    p.add_argument('--strikes',action='store_true',help='match joystick punch and flying kick pixels on the published playfield')
    p.add_argument('--foley',action='store_true',help='record Enhanced combat audio with ordinary joystick attacks')
    p.add_argument('--poses',action='store_true',help='verify the vertical jump and prone sprites with joystick input in both modes')
    p.add_argument('--buttons',action='store_true',help='check independent attack/jump buttons and room confirmation')
    a=p.parse_args();check(a.folder.resolve(),a.pid,a.tour,a.strikes,a.foley,a.poses,a.buttons)
