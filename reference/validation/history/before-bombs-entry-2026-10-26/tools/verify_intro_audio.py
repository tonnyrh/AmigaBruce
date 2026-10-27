"""Check shipped voice bytes and the 68000 startup DMA / bitmap handoff."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import wave

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_assets():
    folder = ROOT / 'assets/audio/intro-v1'
    manifest = json.loads((folder / 'manifest.json').read_text())
    header = (ROOT / 'amiga/intro_audio_data.h').read_text()
    def array(name):
        return list(map(int, re.search(name + r'\[.*?\]=\{(.*?)\};', header, re.S)[1].replace('\n', '').strip(',').split(',')))
    packed = bytes(array('bl_intro_packed'))
    steps, indices = array('bl_intro_steps'), array('bl_intro_index')
    assert len(packed) == manifest['packed_bytes'] == manifest['samples'] // 2
    assert len(steps) == 89 and len(indices) == 8
    assert sha(ROOT / manifest['source']) == manifest['source_sha256']
    assert hashlib.sha256(packed).hexdigest() == manifest['packed_sha256']
    assert manifest['extra_chip_bytes'] == 0 and not manifest['original_audio_used']
    assert manifest['samples'] + 4 <= 40960
    predictor = index = 0
    decoded = bytearray()
    checksum = 2166136261
    for byte in packed:
        for code in (byte >> 4, byte & 15):
            step = steps[index]
            delta = (step >> 3) + (step if code & 4 else 0) + (step >> 1 if code & 2 else 0) + (step >> 2 if code & 1 else 0)
            predictor = min(32767, max(-32768, predictor + (-delta if code & 8 else delta)))
            index = min(88, max(0, index + indices[code & 7]))
            sample = (predictor >> 8) & 255
            decoded.append(sample)
            checksum = ((checksum ^ sample) * 16777619) & 0xffffffff
    assert hashlib.sha256(decoded).hexdigest() == manifest['decoded_sha256']
    with wave.open(str(folder / 'kiai-paula.wav'), 'rb') as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (1, 1, 11025, manifest['samples'])
        assert wav.readframes(wav.getnframes()) == bytes((v + 128) & 255 for v in decoded)
    assert abs((decoded[0] + 128) % 256 - 128) <= 1
    assert abs((decoded[-1] + 128) % 256 - 128) <= 1
    assert 1 < manifest['duration_seconds'] < 4
    assert '"BRUCE LEE AMIGA"' not in (ROOT / 'amiga/main.c').read_text()
    assert "-l 'Bruce'" in (ROOT / 'amiga-build.ps1').read_text()
    return dict(samples=len(decoded), native_decode_fnv=checksum, packed_bytes=len(packed), extra_chip_bytes=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets-only', action='store_true')
    args = parser.parse_args()
    expected = check_assets()
    if args.assets_only:
        print(json.dumps(expected))
        return
    count = 0
    for name in ['a500-m3-combat.json', 'a500-gates.json', 'a500-m4-rooms.json', 'a500-room-tour.json']:
        report = json.loads((ROOT / 'reference/validation' / name).read_text(encoding='utf-8-sig'))
        for source in report['source_files']:
            assert sha(ROOT / source['path']) == source['sha256'], source['path']
        for run in report['runs']:
            assert int(run['intro_pcm_hash']) == expected['native_decode_fnv']
            assert int(run['intro_samples']) == expected['samples']
            for field in ['intro_silence_reload', 'intro_finished', 'intro_dma_stopped', 'intro_bitmap_restored']:
                assert run[field] == '1', (name, field)
            assert 118 <= int(run['intro_fields']) <= 600
            assert run['restored_os'] == '1' and run['canvas_residue_bytes'] == '0'
            count += 1
    print(f'PASS: {expected["packed_bytes"]} packed voice bytes; exact 68000 decode, one-shot DMA, framebuffer reuse and OS restore in {count} native runs; listening acceptance pending')


if __name__ == '__main__':
    main()
