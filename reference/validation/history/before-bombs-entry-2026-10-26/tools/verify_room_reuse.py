"""Cache invalidation controls; source-state rules remain in the room audit."""
import ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/room-reuse-test/reuse.dll'))
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    d.bl_c64_load.argtypes=[ctypes.c_long];d.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    d.bl_c64_build_animation_cache.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_long]
    d.bl_c64_build_animation_cache.restype=ctypes.c_long
    d.bl_c64_reuse_stat.argtypes=[ctypes.c_long];d.bl_c64_reuse_stat.restype=ctypes.c_ushort
    d.bl_c64_paint_room.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_long]
    d.bl_c64_check_interleaved.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_long]
    d.bl_c64_check_interleaved.restype=ctypes.c_long
    from verify_c64_room_runtime import Paint
    def tile(ptr):
        r=ptr.contents;row,col=divmod(r.cell,40)
        for dy in range(8):
            for plane in range(4):r.bitmap[(r.scene_top+row*8+dy)*160+plane*40+col]=r.planes[plane*8+dy]
    callback=ctypes.CFUNCTYPE(None,ctypes.POINTER(Paint))(tile)
    d.bl_c64_set_painter.argtypes=[ctypes.c_void_p];d.bl_c64_set_painter(callback)
    a=(ctypes.c_ubyte*106496)();b=(ctypes.c_ubyte*106496)();picture=(ctypes.c_ubyte*40960)()
    stats=lambda:[d.bl_c64_reuse_stat(i) for i in range(4)]
    word=lambda p:d.bl_c64_read(p)|(d.bl_c64_read(p+1)<<8)
    checks=[]
    def build(label,cache=a,capacity=106496,hit=False):
        before=stats();used=d.bl_c64_build_animation_cache(cache,capacity);after=stats()
        assert after[2]-before[2]==int(hit),(label,before,after)
        assert after[3]-before[3]==int(not hit),(label,before,after)
        d.bl_c64_paint_room(picture,32)
        assert d.bl_c64_check_interleaved(picture,32)==0,(label,'static source image')
        checks.append(dict(label=label,cache_hit=hit,bytes=used,stats=after));return used
    d.bl_c64_reset();d.bl_c64_load(4);d.bl_c64_reuse_reset()
    used=build('cold-R05');assert used>0;saved=bytes(a[:used])
    d.bl_c64_load(4);assert stats()[0]==1
    assert build('same-room',hit=True)==used and bytes(a[:used])==saved
    palette=word(0x480b+8)
    for i in range(12):d.bl_c64_test_write(palette+i,(d.bl_c64_read(palette+i)+1)&15)
    d.bl_c64_load(4);assert stats()[1]==1
    build('changed-palette');assert bytes(a[:used])!=saved
    raster=word(0x4833+8);d.bl_c64_test_write(raster,127);d.bl_c64_load(4)
    build('changed-raster-bands')
    d.bl_c64_test_write(0x42f1,d.bl_c64_read(0x42f1)^1);d.bl_c64_load(4)
    build('changed-roll-pattern')
    cells=[i for i in range(120,1000) if 0x61<=d.bl_c64_read(0x8c00+i)&127<=0x63]
    cell=cells[0]
    d.bl_c64_load(4);d.bl_c64_test_write(0x8c00+cell,d.bl_c64_read(0x8c00+cell)^128)
    build('changed-animated-code')
    d.bl_c64_load(4);build('restore-original-layout')
    d.bl_c64_load(4);d.bl_c64_test_write(0xd800+cell,(d.bl_c64_read(0xd800+cell)+1)&7)
    build('changed-animated-color')
    d.bl_c64_load(4);build('restore-original-color')
    assert build('new-DMA-storage',cache=b)==used
    # A smaller capacity must not claim a warm hit on bytes it cannot hold.
    assert build('insufficient-capacity',cache=b,capacity=used-1)==0
    assert build('rebuild-after-capacity-failure',cache=b)==used
    d.bl_c64_load(18);assert build('different-charset',cache=b)==0
    d.bl_c64_reset();d.bl_c64_load(4);build('fresh-source-reset',cache=b)
    for room in (0,1,4,5,4,13,18,19,4):
        d.bl_c64_load(room);build('room-order-'+str(room+1),cache=b)
    out=ROOT/'reference/analysis/room-load-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    r=dict(status='passed_cache_invalidation_and_source_pixel_controls',natural_playthrough=False,
        cache_controls=checks,source_files=[artifact(p) for p in ['core/c64_rooms.c','core/c64_rooms.h','test-room-reuse.ps1','tools/verify_room_reuse.py']])
    (out/'host-reuse.json').write_text(json.dumps(r,indent=2)+'\n')
    print(f'PASS {len(checks)} room reuse/invalidation controls; source pixels unchanged')
if __name__=='__main__':main()
