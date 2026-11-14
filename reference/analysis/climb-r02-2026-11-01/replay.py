"""Replay the room 2 net boundary in a dedicated, running PAL x64sc monitor."""
import argparse
import hashlib
import json
import socket
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from inspect_corrupt_screen_snapshot import chunks
from vice_binary import Vice


def replay(port):
    source = (ROOT / ".reference/c64/work/untrained-memory.bin").read_bytes()
    assert hashlib.sha256(source).hexdigest() == "092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    snapshot = ROOT / ".tmp/01.11.2026.uss"
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == "26544c868210cc46ab650669ee2fbed13762736069d4305dfe1c768e4c1ab683"
    saved = chunks(snapshot)["BRAM"][0x637d0:0x737d0]
    assert saved[0x29] == 1 and saved[0x1167:0x1187] == source[0x1167:0x1187]

    ref = json.loads((ROOT / "reference/manifest.json").read_text())["analysis_candidate"]
    start = ROOT / ref["baseline_snapshot_path"]
    assert hashlib.sha256(start.read_bytes()).hexdigest() == ref["baseline_snapshot_sha256"]
    vice = Vice(port)
    vice.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    entry = 0x1bce
    try:
        assert vice.restore(start) == entry
        for first, end in ((0x5212, 0x52ad), (0x1dca, 0x1e13), (0x2008, 0x2048),
                           (0x2080, 0x2082), (0x20f3, 0x20f6), (0x2504, 0x2509), (0x2974, 0x29c3)):
            assert vice.memory(first, end - 1) == source[first:end]
        vice.resource_int("JoyPort1Device", 37)
        check = vice.checkpoint(entry)

        def move(pins, steps, until=None):
            vice.joystick(0xf0 | pins)
            for _ in range(steps):
                vice.next_hit(check, entry)
                ram = vice.memory(0, 0x108)
                if until and until(ram):
                    break
            if until:
                assert until(ram), (ram[0x29], ram[0x9e], ram[0xa1])
            return ram

        # Reach the lower floor of room 2 using the joystick. The game builds
        # its own screen, charset, collision masks, NPCs and sprite images.
        move(7, 85, lambda m: m[0x9e] >= 87)
        move(14, 100)
        move(7, 100, lambda m: m[0x29] == 1)
        move(7, 100, lambda m: m[0x9e] >= 87)
        move(15, 16)
        move(11, 1)
        move(15, 12)
        move(14, 1)
        # Align Bruce's position and pose at the input boundary. No writes
        # to the room, enemy data, grip flags, source code or graphics.
        for at in (0x9e, 0xa1, 0xa4, 0xbf, 0xc2, 0xcb, 0xce, 0x106,
                   0x4f48, 0x4f4b, 0x4f4e, 0x4f51, 0x4f54, 0x4fdb):
            if vice.memory(at, at)[0] != saved[at]:
                vice.command(2, struct.pack("<BHHBH", 0, at, at, 0, 0) + saved[at:at+1])

        for tick in range(56):
            ram = move(14, 1)
            pose = vice.memory(0x4f48, 0x4f4e)
            assert (ram[0x29], ram[0x98], ram[0x9e], ram[0xa1]) == (1, 14, 87, 140)
            state = (ram[0xb6], ram[0xbf], ram[0xce], pose[0], pose[-1])
            assert state == ((1, 5, 15, 8, 8), (5, 0, 0, 10, 10))[tick % 2], (tick, state)
        ram = move(7, 1)
        assert (ram[0x9e], ram[0xa1]) == (89, 140)
        ram = move(14, 56, lambda m: m[0xa1] <= 102)
        assert (ram[0x29], ram[0x9e]) == (1, 89)
        print(f"PASS: 56 stationary updates, one right step, then up to Y={ram[0xa1]}.")
    finally:
        vice.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", type=int, help="binary monitor of a dedicated PAL x64sc instance")
    replay(parser.parse_args().port)
