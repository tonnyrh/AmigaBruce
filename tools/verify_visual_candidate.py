"""Validate current OCS animation assets and source-bound native evidence."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/graphics/v2'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))

def main():
    if (ROOT/'reference/validation/c64-candidate.json').exists():
        from verify_c64_candidate import verify
        return verify()
    manifest=read('assets/graphics/v2/fighters-manifest.json')
    assert not manifest['original_pixels_shipped'] and not manifest['exact_c64_sprite_composition']
    for source in manifest['source_files']:assert sha(ROOT/source['path'])==source['sha256']
    assert len(manifest['frames'])==48 and manifest['packed_bytes']==29952
    assert (manifest['width'],manifest['height'],manifest['poses_per_actor'])==(48,26,16)
    header=(ROOT/'amiga/fighter_art_data.h').read_text()
    packed=bytes(map(int,re.search(r'fighter_art\[\]=\{(.*?)\};',header,re.S)[1].replace('\n','').strip(',').split(',')))
    assert len(packed)==29952
    rows=[tuple(map(int,pair)) for pair in re.findall(r'\{(\d+),(\d+)\}',header.split('fighter_art_rows')[1])]
    assert len(rows)==48
    bounds=[tuple(map(int,pair)) for pair in re.findall(r'\{(\d+),(\d+),(\d+),(\d+)\}',header.split('fighter_art_bounds')[1])]
    assert len(bounds)==48
    atlas=Image.open(ART/'fighters-indexed.png')
    assert atlas.mode=='P' and atlas.size==(768,78) and atlas.info['transparency']==0
    palette=atlas.getpalette()[:48]
    assert all(c%17==0 for c in palette)
    runtime=(ROOT/'amiga/main.c').read_text()
    colors=[int(v.strip(),16) for v in re.search(r'palette\[16\]=\{([^}]+)\}',runtime)[1].split(',')]
    assert colors==manifest['palette_ocs']
    for index,frame in enumerate(manifest['frames']):
        assert frame['anchor']==[24,25]
        piece=packed[index*624:(index+1)*624]
        pixels=bytes(n for value in piece for n in (value>>4,value&15))
        assert hashlib.sha256(pixels).hexdigest()==frame['sha256']
        if frame['actor']=='yamo':
            assert pixels.count(14)+pixels.count(15)>3*pixels.count(13),'Yamo skin must remain predominantly green'
        used=[i//48 for i,c in enumerate(pixels) if c]
        assert rows[index]==(min(used),max(used)+1)
        used_x=[i%48 for i,c in enumerate(pixels) if c]
        assert bounds[index]==(min(used_x),min(used),max(used_x)+1,max(used)+1)
        x,y=frame['pose']*48,(index//16)*26
        assert atlas.crop((x,y,x+48,y+26)).tobytes()==pixels
        image=Image.open(ART/f"{frame['actor']}-{frame['pose']:02}.png")
        assert image.mode=='P' and image.size==(48,26) and image.info['transparency']==0
        assert image.tobytes()==pixels and image.getpalette()[:48]==palette
        # Transparent edge columns preserve every pixel under anchor reflection.
        assert not any(pixels[row*48] or pixels[row*48+47] for row in range(26))
    for path,filename in [('assets/graphics/v2','fighters'),('assets/graphics/v1','mountains')]:
        report=read(f'{path}/{filename}.validation.json')
        assert report['valid'] and not report['errors']
        assert sha(ROOT/f'{path}/{filename}-indexed.png')==(report['output_sha256'] or report['input_sha256'])
    assert Image.open(ROOT/'assets/graphics/v1/mountains-indexed.png').getpalette()[:48]==palette
    sources=read('reference/validation/candidate-openings.json')
    for source in sources['source_files']:assert sha(ROOT/source['path'])==source['sha256'],source['path']
    for name in ['a500-m3-combat.json','a500-m4-rooms.json','a500-room-tour.json','a500-gates.json']:
        report=read('reference/validation/'+name)
        if name=='a500-gates.json':assert len(report['runs'])==2
        if report.get('preview'):assert sha(ROOT/report['preview']['path'])==report['preview']['sha256']
        for source in report['source_files']:
            assert sha(ROOT/source['path'])==source['sha256'],(name,source['path'])
        for run in report['runs']:
            assert run['restored_os']=='1' and run['missed_frames']=='0'
            assert int(run['max_gap_excluding_framebuffer_capture'])<=1
            assert int(run['sfx_played'])==int(run['sfx_silence_reloads'])
            assert int(run['chip_largest_loaded'])>=65536
            if run['combat_mode']=='1':
                assert run['cpu_stamp_chip_bytes']=='0' and run['explicit_chip_bytes']=='172228'
                assert run['canvas_residue_bytes']=='0'
            if name=='a500-room-tour.json':assert run['visited_rooms_mask']=='1048575'
            if name=='a500-gates.json':
                assert run['gate_checks']=='127' and run['room_transitions']=='3'
                assert run['lantern_pickups']=='31' and run['score']=='3875'
                assert int(run['pose_bruce'])&240==240
    candidate=read('reference/validation/visual-candidate.json')
    assert candidate['poses']==48 and not candidate['full_m4_parity'] and not candidate['full_m5_complete']
    for artifact in candidate['artifacts']:
        assert sha(ROOT/artifact['path'])==artifact['sha256'],artifact['path']
    print('PASS:48 animation slots, OCS16 palette,48x26 fixed anchors, source-backed openings and fresh native combat/rooms/tour/repeat/gate evidence; full C64 parity remains open')

if __name__=='__main__':main()
