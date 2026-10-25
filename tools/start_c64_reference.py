"""Restore the frozen local C64 candidate for manual keyboard testing."""
import argparse
import hashlib
import json
from pathlib import Path
from vice_binary import Vice

ROOT = Path(__file__).resolve().parents[1]


def main(port):
    manifest = json.loads((ROOT/'reference/manifest.json').read_text())
    candidate = manifest['analysis_candidate']
    snapshot = ROOT/candidate['baseline_snapshot_path']
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == candidate['baseline_snapshot_sha256']
    vice = Vice(port)
    try:
        vice.resource_int('SidEngine', 1)
        vice.resource_int('Sound', 0)
        assert vice.restore(snapshot) == 0x1bce
        vice.resource_int('Sound', 0)
        # Snapshot was recorded using IO Simulation. Return port1 to an
        # ordinary joystick driven by VICE's numeric keypad, with no trainer.
        vice.resource_int('JoyPort1Device', 1)
        vice.resource_int('JoyPort2Device', 1)
        vice.resource_int('JoyDevice1', 1)
        vice.resource_int('JoyDevice2', 0)
        vice.resource_int('KeySetEnable', 1)
    finally:
        vice.close()
    print('C64 reference restored; port1 numeric keypad; normal PAL speed; trainers off')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=6522)
    main(parser.parse_args().port)
