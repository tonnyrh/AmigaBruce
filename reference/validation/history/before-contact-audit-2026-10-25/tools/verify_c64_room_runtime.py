"""Compare compiled native C room programs with actual candidate6502 routines.

Supplementary CPU fixtures, not emulator hardware or natural-play evidence.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import sys
from datetime import date
from c64_room_model import room_memory, word, oracle_contact

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU


def invoke(m,entry):
    cpu=MPU(memory=m,pc=entry)
    cpu.sp=0xfd;m[0x1fe]=0xfe;m[0x1ff]=0xff
    for _ in range(100000):
        if cpu.pc==0xffff:return cpu
        if cpu.pc==0x2f8e:return # Shared native transition boundary; verified separately.
        cpu.step()
    raise AssertionError(f'6502 escaped ${entry:04X} at ${cpu.pc:04X}')


class Paint(ctypes.Structure):
    _fields_=[('bitmap',ctypes.POINTER(ctypes.c_ubyte)),('planes',ctypes.POINTER(ctypes.c_ubyte))]+[(key,ctypes.c_ulong) for key in ('cell','slot','changed','scene_top')]
class Block(ctypes.Structure):
    _fields_=[('bitmap',ctypes.POINTER(ctypes.c_ubyte)),('pixels',ctypes.POINTER(ctypes.c_ubyte))]+[(key,ctypes.c_ulong) for key in ('left','top','width','height','first_mask','last_mask')]


def verify_animation_cache(native,source):
    tile_type=ctypes.CFUNCTYPE(None,ctypes.POINTER(Paint));block_type=ctypes.CFUNCTYPE(None,ctypes.POINTER(Block))
    def tile(ptr):
        r=ptr.contents;row,col=divmod(r.cell,40)
        for dy in range(8):
            for plane in range(4):r.bitmap[(r.scene_top+row*8+dy)*160+plane*40+col]=r.planes[plane*8+dy]
    block_calls=[0]
    def block(ptr):
        r=ptr.contents;block_calls[0]+=1
        for line in range(r.height*4):
            for col in range(0,r.width,2):
                mask=(r.first_mask if col==0 else 65535)&(r.last_mask if col+2==r.width else 65535)
                for byte in range(2):
                    at=r.top*160+r.left+line*40+col+byte;part=(mask>>(8 if byte==0 else 0))&255
                    r.bitmap[at]=(r.bitmap[at]&(~part&255))|(r.pixels[line*r.width+col+byte]&part)
    tile_fn=tile_type(tile);block_fn=block_type(block)
    native.bl_c64_set_painter.argtypes=[ctypes.c_void_p];native.bl_c64_set_block_painter.argtypes=[ctypes.c_void_p]
    native.bl_c64_build_animation_cache.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_long]
    native.bl_c64_build_animation_cache.restype=ctypes.c_long
    native.bl_c64_check_interleaved.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_long]
    native.bl_c64_check_interleaved.restype=ctypes.c_long
    cache=(ctypes.c_ubyte*106496)();bitmap=(ctypes.c_ubyte*40960)();checks=[]
    try:
        native.bl_c64_set_painter(tile_fn);native.bl_c64_set_block_painter(block_fn)
        for room in range(20):
            native.bl_c64_reset();native.bl_c64_load(room);native.bl_c64_paint_room(bitmap,32);native.bl_c64_clear_dirty()
            used=native.bl_c64_build_animation_cache(cache,len(cache));before=block_calls[0];max_parts=0
            assert 0<=used<=len(cache)
            # Empty presentation calls must not poison the next animation.
            empty=ctypes.c_ushort();native.bl_c64_paint_part(bitmap,32,160,ctypes.byref(empty))
            assert empty.value==0
            for phase in range(8):
                for address,value in ((0x60,1),(0x65,0),(0x66,16),(0x64,(phase-1)&255)):native.bl_c64_test_write(address,value)
                m=[native.bl_c64_read(i) for i in range(65536)];m[0x500:0x4300]=source[0x500:0x4300]
                invoke(m,0x2c70);native.bl_c64_test_execute(0x2c70)
                for lo,hi in ((0,0x200),(0x2d2c,0x2d2e),(0x43bb,0x43bd),(0xa000,0xb000)):
                    for address in range(lo,hi):assert m[address]==native.bl_c64_read(address),(room+1,phase,hex(address))
                count=ctypes.c_ushort()
                for part in range(10):
                    native.bl_c64_paint_part(bitmap,32,160,ctypes.byref(count))
                    if native.bl_c64_paint_done():break
                else:raise AssertionError('animation cache presentation did not finish')
                max_parts=max(max_parts,part+1)
                native.bl_c64_clear_dirty()
                assert native.bl_c64_check_interleaved(bitmap,32)==0,(room+1,phase,'cached interleaved image')
            assert max_parts<=2,(room+1,'animation requires more than two presentation fields',max_parts)
            checks.append(dict(room=room+1,cache_bytes=used,source_phases=8,block_draws=block_calls[0]-before,max_presentation_parts=max_parts))
    finally:
        native.bl_c64_set_painter(None);native.bl_c64_set_block_painter(None)
    return checks


def main():
    identity=json.loads((ROOT/'.tmp/c64-room-test/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for item in identity:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],f"Source changed before CPU verification: {item['path']}"
    native=ctypes.CDLL(str(ROOT/'.tmp/c64-room-test/rooms.dll'))
    native.bl_c64_read.restype=ctypes.c_ubyte
    native.bl_c64_read.argtypes=[ctypes.c_long]
    native.bl_c64_paint_done.restype=ctypes.c_ubyte
    native.bl_c64_fault.restype=ctypes.c_ushort
    native.bl_c64_test_write.argtypes=[ctypes.c_long,ctypes.c_long]
    native.bl_c64_contact.argtypes=[ctypes.c_long]*4
    native.bl_c64_contact.restype=ctypes.c_ubyte
    native.bl_c64_planar.argtypes=[ctypes.c_long]*3
    native.bl_c64_planar.restype=ctypes.c_ulong
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    checks=[];contacts=0;door_checks=0
    # Every room, original lamp flags plus all lamps removed, and moving actors.
    ranges=[(0,0x200),(0x2500,0x2584),(0xd400,0xd419),
            (0xeb00,0xeb01),(0xef70,0xef71),(0xf070,0xf071),
            (0x4321,0x4338),(0x4d0a,0x4e9c),(0x4fde,0x4fe7),
            (0x8340,0x83c0),(0x8c78,0x8fe8),(0xa000,0xc000),(0xd878,0xdbe8)]
    for room in range(20):
        for clear in (False,True):
            native.bl_c64_reset()
            if clear:
                for r in range(20):
                    native.bl_c64_test_write(0x2a+r,0)
                    p=word(source,0x4ce2+2*r)
                    while not source[p]&128:native.bl_c64_test_write(p,0);p+=4
            # Capture BEFORE native init, then run the source decoder and init
            # independently. Add executable source bytes only to the CPU side.
            m=[native.bl_c64_read(i) for i in range(65536)]
            m[0x500:0x4300]=source[0x500:0x4300]
            m[0x9e]=source[0x4bae+room];m[0xa1]=source[0x4bc2+room];m[0xb6]=1;m[0xce]=4
            m[0x29]=room;m[0x100]=m[0x106]=m[0xbf]=0;m[0x65]=0;m[0x4321]=7
            for i in range(132):m[0x4f57+i]=0
            for i in range(3):m[0x4fde+i]=0
            for i in range(1000):m[0x8c00+i]=6;m[0xd800+i]=m[0x47a0+room]
            native.bl_c64_load(room)
            assert not native.bl_c64_fault()
            loaded,_=room_memory(m,room,stack_pointer=0xfd)
            for i in range(5):loaded[0x4e97+i]=0
            invoke(loaded,0x336e);invoke(loaded,word(source,0x4ec4+2*room)+1)
            for lo,hi in ranges:
                for addr in range(lo,hi):
                    if loaded[addr]!=native.bl_c64_read(addr):
                        raise AssertionError(f'R{room+1:02} init clear={clear}: ${addr:04X} native={native.bl_c64_read(addr):02X} source={loaded[addr]:02X}')
            planes=(ctypes.c_ubyte*40960)();native.bl_c64_paint_room(planes,32);native.bl_c64_clear_dirty()
            if not clear:
                from rip_c64_room_graphics import indexed
                from PIL import Image
                picture=indexed(320,200)
                for yy in range(24,200):
                    for xx in range(320):
                        value=sum(1<<p for p in range(4) if planes[p*10240+(yy+32)*40+xx//8]&(128>>(xx&7)))
                        if room==19 and value==15:
                            value=native.bl_c64_read(0xdaac)&7 # Dedicated OCS register, same source color.
                        picture.putpixel((xx,yy),value)
                assert picture.tobytes()==Image.open(ROOT/f'assets/c64/rooms-v1/room-{room+1:02}.png').tobytes(),f'R{room+1} planar LUT differs from source extraction'
                contact_memory=list(loaded);contact_memory[0x5000:0x5800]=source[0x5000:0x5800]
                contact_memory[0x7c]=(0xa0 if room<10 else 0xb0 if room==18 else 0xa8)
                for pose in (0,2,8):
                    for px in (20,22,26,144,290):
                        for py in (50,98,102,146,196):
                            expected=oracle_contact(contact_memory,px,py,pose)
                            actual=tuple(native.bl_c64_contact(px,py,pose,body) for body in (0,1))
                            assert actual==expected,(room+1,px,py,pose,actual,expected)
                            contacts+=1
                # Actual carry gate and destination tables, including hub R12.
                for px,py,fall in ((2,98,False),(302,196,False),(150,198,True),(280,48,False)):
                    for latch in (0,1):
                        for addr in (0x4f57,0x4f5d,0x4f60):native.bl_c64_test_write(addr,latch)
                        dm=list(loaded);dm[0x9e]=(px+24)//2;dm[0xa1]=py;dm[0xbf]=14 if fall else 0
                        for addr in (0x4f57,0x4f5d,0x4f60):dm[addr]=latch
                        dm[0x500:0x4300]=source[0x500:0x4300]
                        cpu=invoke(dm,0x30d4);allowed=not(cpu.p&1)
                        for slot in range(4):
                            result=native.bl_c64_door(slot+2,px,py,fall)
                            assert bool(result)==allowed,(room+1,px,py,latch,slot,'gate')
                            if result:
                                nx=ctypes.c_long();ny=ctypes.c_long();nr=ctypes.c_ubyte()
                                assert native.bl_c64_transition(ctypes.byref(nx),ctypes.byref(ny),ctypes.byref(nr))
                                assert (nx.value,ny.value,nr.value)==(2*source[0x4bfe+slot*40+room]-24,source[0x4c12+slot*40+room],source[0x4b5e+slot*20+room])
                            door_checks+=1
                # Door probes are separate injected fixtures. Restore the exact
                # initialized snapshot before comparing source room loops.
                for addr in range(65536):native.bl_c64_test_write(addr,loaded[addr] if addr<0x500 or addr>=0x4300 else native.bl_c64_read(addr))
            # Room loop, same field counter seam. Keep original hardware bytes
            # in the shadow; source instructions never touch host hardware.
            m=loaded
            for step in range(64):
                px=28+(step*4)%260;py=196-(step%24)*2
                for _ in range(3):
                    native.bl_c64_field();m[0x16]=(m[0x16]+1)&255
                    if m[0x49]:m[0x49]-=1
                    elif m[0x4a]:m[0x4a]-=1;m[0x49]=255
                m[0x9e]=(px+24)//2;m[0xa1]=py;m[2]=50;m[0x100]=0
                m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0}.get(m[0xf2],0xb8)
                native.bl_c64_tick(px,py)
                invoke(m,0x40bc);m[0x7b]=m[0x7b]-1 if m[0x7b] else 1
                invoke(m,word(source,0x4ec4+2*room)+1)
                for lo,hi in ranges:
                    for addr in range(lo,hi):
                        if m[addr]!=native.bl_c64_read(addr):
                            raise AssertionError(f'R{room+1:02} step={step} clear={clear}: ${addr:04X} native={native.bl_c64_read(addr):02X} source={m[addr]:02X}')
                assert not native.bl_c64_fault()
                dirty_count=ctypes.c_ushort()
                # Deliberately small presentation chunks; source contacts must
                # remain correct after visual dirt has been consumed/cleared.
                for part in range(60):
                    native.bl_c64_paint_part(planes,32,17,ctypes.byref(dirty_count))
                    assert dirty_count.value<=17
                    if native.bl_c64_paint_done():break
                else:raise AssertionError('character presentation did not finish')
                native.bl_c64_clear_dirty()
            # Compare actual partial updates after64 source loops, including
            # mutable glyphs, attributes, boss phase and OCS register15.
            from rip_c64_room_graphics import render,indexed
            expected_picture=render(m,room);picture=indexed(320,200)
            for yy in range(24,200):
                for xx in range(320):
                    value=sum(1<<p for p in range(4) if planes[p*10240+(yy+32)*40+xx//8]&(128>>(xx&7)))
                    if room==19 and value==15:value=native.bl_c64_read(0xdaac)&7
                    picture.putpixel((xx,yy),value)
            assert picture.tobytes()==expected_picture.tobytes(),f'R{room+1} clear={clear}: partial renderer differs after source loops'
            contact_memory=list(m);contact_memory[0x5000:0x5800]=source[0x5000:0x5800]
            contact_memory[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0}.get(m[0xf2],0xb8)
            for px in (22,144,290):
                for py in (50,146,196):
                    expected=oracle_contact(contact_memory,px,py,2)
                    actual=tuple(native.bl_c64_contact(px,py,2,body) for body in (0,1))
                    assert actual==expected,(room+1,clear,'dynamic contact',px,py,actual,expected)
                    contacts+=1
            checks.append(dict(room=room+1,all_lamps_cleared=clear,source_loop_calls=64,matched=True))
    animation_checks=verify_animation_cache(native,source)
    for item in identity:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],f"Source changed during CPU verification: {item['path']}"
    report=dict(date=str(date.today()),status='passed_native_c_vs_source_cpu_fixtures',rooms=20,
        source_loop_calls=2560,source_animation_calls=160,animation_cache_checks=animation_checks,contact_checks=contacts,door_gate_checks=door_checks,
        indexed_room_images_compared=20,dynamic_room_images_compared=40,checks=checks,natural_playthrough=False,hardware_parity=False,
        source_sha256=hashlib.sha256(source).hexdigest(),
        source_files=identity)
    (ROOT/'reference/validation/c64-room-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS20 room init programs,2560 loop calls,{contacts} contacts,{door_checks} door gates,20 planar images (native C vs source fixtures)')


if __name__=='__main__':main()
