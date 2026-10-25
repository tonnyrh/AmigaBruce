"""Read-only backend comparison; DMA block arithmetic is not a latency test.

Uses the already compiled Bruce parameter renderer and frozen register traces.
Does not execute Harrier or change game data, playback, binaries or reports
from earlier native runs.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import subprocess

from verify_source_audio import ROOT, SHA, State, Voice

OUT = ROOT / 'reference/analysis/harrier-audio-2026-10-25/report.json'
CLOCK = 3546895


def artifact(path):
    path = Path(path).resolve()
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = path.as_posix()
    return dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def inspect(harrier):
    source = ROOT / '.reference/c64/work/untrained-memory.bin'
    assert artifact(source)['sha256'] == SHA
    dll = ROOT / '.tmp/source-audio-test/audio.dll'
    lib = ctypes.CDLL(str(dll))
    traces = json.loads((ROOT / 'assets/audio/c64-equivalent-v1/source-registers.json').read_text())
    metrics = []
    groups = [('title', traces['music'])]
    groups += [(f'${128+i:02X}', rows) for i, rows in enumerate(traces['effects'])]
    for label, rows in groups:
        state = State()
        lib.bl_source_audio_reset(ctypes.byref(state))
        voices = (Voice * 3)()
        peak = None
        active = long_blocks = 0
        for field, registers in enumerate(rows):
            lib.bl_source_audio_render(ctypes.byref(state), (ctypes.c_ubyte * 26)(*registers), voices)
            for channel, voice in enumerate(voices):
                if not voice.volume:
                    continue
                active += 1
                milliseconds = voice.length * voice.period * 1000 / CLOCK
                long_blocks += milliseconds > 20
                if peak is None or milliseconds > peak['milliseconds']:
                    peak = dict(milliseconds=milliseconds, zero_based_field=field,
                                channel=channel, offset=voice.offset,
                                length_bytes=voice.length, period=voice.period,
                                volume=voice.volume)
        assert lib.bl_source_audio_faults() == 0
        metrics.append(dict(sequence=label, source_fields=len(rows),
                            audible_parameter_fields=active,
                            block_duration_above_20ms_fields=long_blocks,
                            longest_constant_parameter_block=peak))
    command = ['git', '-C', str(harrier), 'rev-parse', 'HEAD']
    commit = subprocess.check_output(command, text=True).strip()
    status = subprocess.check_output(['git', '-C', str(harrier), 'status', '--porcelain'], text=True)
    report = dict(date='2026-10-25', status='read_only_backend_code_review_and_parameter_arithmetic',
        source_sha256=SHA, edition_verified=False, game_code_changed=False,
        native_recording_made=False, harrier_executed=False,
        harrier_root=harrier.as_posix(), harrier_commit=commit,
        harrier_worktree_clean_at_review=not bool(status.strip()),
        paula_clock_used=CLOCK, metrics=metrics,
        interpretation='Constant-parameter block durations, not measured reload latency. The old active block, subsequent period writes, remaining samples and OCS DMA scheduling determine actual latency.',
        findings=[
            'Harrier PCM/MOD retriggers separate DMA off and on across service calls, then queue loop/silence after latch delay',
            'Harrier MOD uses four exclusive channels; Bruce uses three persistent source-derived voices',
            'Harrier current frameCounter increments in polled WaitVbl, not an independent VBL interrupt',
            'Bruce rewrites LC/LEN while DMA continues; native parameter signatures do not measure block adoption',
            'Bruce offline preview changes wave immediately and does not model OCS DMA reload state',
            'Do not copy Harrier effect priorities, retrigger guards, tempo percentages or one-field note gap into C64 rules'
        ],
        hardware_reference=dict(title='Commodore Amiga Hardware Reference Manual, chapter 5',
            url='https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_5.html',
            sections=['Stopping the Audio DMA', 'Joining Tones', 'The Audio State Machine']),
        source_files=[artifact(p) for p in (
            harrier/'amiga/main.c', harrier/'amiga/audio_refinement_tests.h',
            ROOT/'amiga/source_audio.h', ROOT/'amiga/main.c', ROOT/'core/source_audio.c',
            ROOT/'core/source_audio.h', ROOT/'core/source_audio_data.h',
            ROOT/'core/c64_sfx.h', ROOT/'tools/verify_source_audio.py',
            ROOT/'assets/audio/c64-equivalent-v1/source-registers.json',
            ROOT/'tools/compare_harrier_audio.py', ROOT/'docs/HARRIER_AUDIO_REVIEW.md')],
        transient_parameter_renderer=artifact(dll),
        existing_build=[artifact(ROOT/f'amiga/out/bruce_amiga.{suffix}') for suffix in ('exe','adf')],
        limitations=['No new audible/native result or whole-game parity claim',
            'Standalone effects use controlled reset states; inherited and concurrent SFX remain separate cases',
            'Period clipping and 50Hz envelope/wave approximations are existing conversion limits',
            'Harrier comments do not replace C64 machine code or Commodore hardware documentation'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'REVIEWED Harrier {commit[:12]}; {len(metrics)} Bruce sequences; no runtime changes')
    for item in metrics:
        peak = item['longest_constant_parameter_block']
        print(f"{item['sequence']}: max constant-parameter block {peak['milliseconds']:.3f}ms; not measured latency")


def verify():
    report = json.loads(OUT.read_text())
    for item in report['source_files'] + report['existing_build']:
        assert artifact(ROOT/item['path'])['sha256'] == item['sha256'], item['path']
    assert not report['game_code_changed'] and not report['native_recording_made']
    assert report['source_sha256'] == SHA
    assert len(report['metrics']) == 16
    print('VERIFIED read-only Harrier/Bruce review identities; no new playback claim')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--harrier-root', type=Path, default=ROOT.parent/'harrierattackreloaded')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    verify() if args.verify else inspect(args.harrier_root.resolve())
