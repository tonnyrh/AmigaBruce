"""Verify shipped audio bytes and fresh native A500 audio evidence."""
from pathlib import Path
import hashlib
import json
import re
import wave

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    if (ROOT/'reference/validation/source-audio-delivery.json').exists():
        from verify_audio_delivery import verify as verify_source_delivery
        return verify_source_delivery()
    directory = ROOT / 'assets/audio/combat-v1'
    manifest = json.loads((directory / 'manifest.json').read_text())
    header = (ROOT / 'amiga/combat_audio_data.h').read_text()
    packed = bytes(map(int, re.search(r'bl_sfx_packed\[\]=\{(.*?)\};', header, re.S)[1].replace('\n', '').strip(',').split(',')))
    levels = list(map(int, re.search(r'bl_sfx_levels\[16\]=\{(.*?)\}', header)[1].split(',')))
    assert len(packed) == manifest['packed_bytes'] == 2000
    assert manifest['chip_bytes'] == 4004
    assert not manifest['original_audio_used']
    cursor = 0
    for item in manifest['variants']:
        assert sha(directory / (item['name'] + '_source.wav')) == item['source_sha256']
        count = item['samples']
        segment = packed[cursor:cursor + count // 2]
        cursor += count // 2
        assert hashlib.sha256(segment).hexdigest() == item['packed_sha256']
        decoded = bytes((levels[n] + 128) for b in segment for n in (b >> 4, b & 15))
        with wave.open(str(directory / (item['name'] + '.wav')), 'rb') as wav:
            assert wav.getnchannels() == 1 and wav.getsampwidth() == 1
            assert wav.getframerate() == 8000 and wav.getnframes() == count
            assert wav.readframes(count) == decoded
        assert decoded[0] == decoded[-1] == 128
    checked = []
    for name in ['a500-m3-combat.json', 'a500-gates.json']:
        report = json.loads((ROOT / 'reference/validation' / name).read_text(encoding='utf-8-sig'))
        for source in report['source_files']:
            assert sha(ROOT / source['path']) == source['sha256'], source['path']
        for run in report['runs']:
            assert int(run['sfx_played']) >= 4
            assert run['sfx_played'] == run['sfx_silence_reloads']
            assert run['sfx_variant_mask'] == '15' and run['sfx_chip_bytes'] == '4004'
            assert run['restored_os'] == '1'
            assert int(run['max_gap_excluding_framebuffer_capture']) <= 1
        checked.append(name)
    print('PASS: four short assets, exact nibble decoding, 4004 Chip bytes; fresh native combat and repeat-launch DMA checks: ' + ', '.join(checked))


if __name__ == '__main__':
    verify()
