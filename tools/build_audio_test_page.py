"""Build a standalone, offline listening page from the current Enhanced sound bank."""
import argparse
import base64
import io
import json
import struct
import wave
import webbrowser
from pathlib import Path

from build_enhanced_audio import CUES, LEVELS, ROOT, sample_path, sample_pitch

PAL_CLOCK = 3546895
PREVIEW_RATE = 16000
TEMPLATE = Path(__file__).with_name('audio_test.html')
CANDIDATES = ROOT/'assets/audio/auditions/2026-11-14-r3/manifest.json'


def wav_uri(samples, rate=PREVIEW_RATE):
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as output:
        output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        output.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return 'data:audio/wav;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')


def render(samples, period, volume):
    """Sample-and-hold preview at the PAL playback period and programmed volume."""
    count = round(len(samples) * PREVIEW_RATE * period / PAL_CLOCK)
    return [round(samples[min(len(samples)-1, int(i*PAL_CLOCK/(period*PREVIEW_RATE)))]
                  * volume / 64) for i in range(count)]


def generation_metadata(path):
    """Use the exact recorded prompt for this selected asset, not a new description."""
    manifest = path.parent/'sources.json'
    if not manifest.exists():
        return {}
    entries = json.loads(manifest.read_text(encoding='utf-8'))
    if isinstance(entries, dict):
        return entries
    return next((entry for entry in entries if entry.get('name') == path.stem), {})


def clips():
    result = []
    for name, rate, _, volume in CUES:
        actor, action = name.split('_', 1)
        for variant in range(1 if action == 'shout' else 2):
            path = sample_path(name, variant)
            metadata = generation_metadata(path)
            with wave.open(str(path), 'rb') as source:
                assert (source.getframerate(), source.getnchannels(), source.getsampwidth()) == (rate, 1, 2)
                count = source.getnframes()
                samples = struct.unpack(f'<{count}h', source.readframes(count))
            period = round(PAL_CLOCK/(rate*sample_pitch(name,variant)))
            pcm = [256*min(LEVELS, key=lambda level: abs(value-256*level)) for value in samples]
            title = {'hit': 'Impact received', 'blade': 'Weapon swing', 'shout': 'Punch cry — imported shout'}.get(action, action.title())
            result.append(dict(id=f'{name}_{variant}', group=actor.title(), title=title, audition=False,
                               variant=None if action == 'shout' else variant+1,
                               duration=round(count*period/PAL_CLOCK*1000),
                               source=path.relative_to(ROOT).as_posix(),
                               prompt=metadata.get('prompt'), generator=metadata.get('generator'),
                               game=wav_uri(render(pcm, period, volume)),
                               original=wav_uri(render(samples, period, volume))))
    return result


def candidate_clips():
    """Read audition assets only; never write the game's sample bank or headers."""
    if not CANDIDATES.exists():
        return []
    result = []
    for item in json.loads(CANDIDATES.read_text(encoding='utf-8'))['clips']:
        path = CANDIDATES.parent/item['file']
        with wave.open(str(path), 'rb') as source:
            assert (source.getnchannels(), source.getsampwidth()) == (1, 2)
            rate, count = source.getframerate(), source.getnframes()
            samples = struct.unpack(f'<{count}h', source.readframes(count))
        period = round(PAL_CLOCK/(rate*item.get('pitch', 1.0)))
        pcm = [256*min(LEVELS, key=lambda level: abs(value-256*level)) for value in samples]
        result.append(dict(id=item['id'], group=item['group'], title=item['title'],
                           variant=item['variant'], audition=True,
                           duration=round(count*period/PAL_CLOCK*1000),
                           source=path.relative_to(ROOT).as_posix(),
                           prompt=item.get('prompt'), generator=item.get('generator'),
                           note=item.get('note'), use_for=item.get('use_for'),
                           game=wav_uri(render(pcm, period, item['volume'])),
                           original=wav_uri(render(samples, period, item['volume']))))
    return result


def build(output):
    sounds = candidate_clips() + clips()
    payload = json.dumps(sounds, ensure_ascii=True).replace('<', '\\u003c')
    page = TEMPLATE.read_text(encoding='utf-8').replace('/* SOUND_DATA */ []', payload)
    assert '/* SOUND_DATA */' not in page
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    count = sum(sound['audition'] for sound in sounds)
    print(f'Audio test page: {count} selected takes, {len(sounds)-count} current Enhanced samples; {output}')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'.tmp/audio-test/index.html', help='Standalone HTML output file')
    parser.add_argument('--open', action='store_true', help='Open the generated page in your default browser')
    args = parser.parse_args()
    page = build(args.output.resolve())
    if args.open:
        webbrowser.open(page.as_uri())
