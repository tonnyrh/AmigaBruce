"""Verify current expansion evidence without recertifying original gameplay."""
import hashlib
import json
from pathlib import Path
from verify_evidence import verify as verify_baseline

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def identities(report):
    for source in report['source_files']:
        assert sha(source['path'])==source['sha256'],source['path']


def main():
    verify_baseline()
    geometry=read('reference/validation/room-blockouts.json')
    assert not geometry['full_m4_parity']
    assert [r['room'] for r in geometry['rooms']]==list(range(3,21))
    assert geometry['generated_sha256']==sha('core/room_geometry.h')
    assert geometry['script_sha256']==sha('tools/build_room_geometry.py')
    packed=read('reference/validation/room-backgrounds.json')
    identities(packed)
    assert packed['roundtrip_passed'] and packed['original_pixels_used'] is False
    assert len(packed['rooms'])==20 and packed['total_packed_bytes']<120000
    assert packed['generated_sha256']==sha('amiga/room_background_data.h')
    tour=read('reference/validation/a500-room-tour.json');identities(tour)
    assert sha(tour['preview']['path'])==tour['preview']['sha256']
    for run in tour['runs']:
        assert run['frames']=='7200' and run['visited_rooms_mask']=='1048575'
        assert run['room_tour']=='1' and run['room_load_events']=='19'
        assert run['restored_os']=='1' and run['missed_frames']=='0'
        assert int(run['max_gap_excluding_framebuffer_capture'])<=1
        assert int(run['explicit_chip_bytes'])<=180000
        assert int(run['chip_largest_loaded'])>=65536
    art=read('reference/validation/art-inventory.json')
    assert art['reference_only'] and not art['production_art_generated']
    assert not art['original_pixels_shipped']
    assert art['tile_components']==384 and art['sprite_components']==210
    assert art['extraction_script_sha256']==sha('tools/extract_c64_art.py')
    assert art['prompt_document_sha256']==sha(art['prompt_path'])
    milestone=read('docs/parity/evidence/M4-0002.json')
    assert milestone['inspection_room_count']==20 and milestone['background_cache_slots']==2
    assert not milestone['full_m4_parity'] and not milestone['natural_completion_available']
    for artifact in milestone['artifacts']:
        assert sha(artifact['path'])==artifact['sha256'],artifact['path']
    print('PASS: 20-room inspection, two-slot runtime, lossless own-art packing and reference-only art inventory; full M4 remains open')


if __name__=='__main__':main()
