"""Inspect movement in the local candidate with py65; NOT a full C64 parity test.

Requires py65 (1.2.0 used here). Does not emulate VIC/CIA/SID or interrupts.
Never use these traces as evidence of PAL field timing.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".reference/tools/python"))


def analyze(snapshot, output):
    from py65.devices.mpu6502 import MPU
    data = snapshot.read_bytes()
    manifest = json.loads((ROOT / "reference/manifest.json").read_text(encoding="utf-8"))
    expected = manifest["analysis_candidate"]["baseline_snapshot_sha256"]
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Snapshot does not match the registered candidate baseline")
    offset = data.index(b"C64MEM\0")
    # Registered VICE 3.10 C64MEM 0.1: module header, port bytes, EXROM/GAME,
    # then underlying 64K RAM. Validate the known baseline layout first.
    if data[offset+16:offset+18] != b"\0\1":
        raise ValueError("Unsupported C64MEM module version")
    initial = list(data[offset+26:offset+26+65536])
    if len(initial) != 65536 or initial[0x1bce:0x1bd1] != [0x20,0x29,0x1b]:
        raise ValueError("Unexpected candidate code layout")
    output.mkdir(parents=True, exist_ok=True)
    scenarios = [("idle",15),("right",7),("left",11),("up",14),
                 ("jump-right",6),("jump-left",10),("down",13)]
    summary = {"status":"analysis_only", "cpu":"py65 1.2.0 NMOS6502",
               "snapshot_sha256":expected, "hardware_emulated":False,
               "entry":"$1BCE", "stop":"$1C32", "scenarios":[]}
    for name, direction in scenarios:
        cpu = MPU(memory=initial[:], pc=0x1bce)
        cpu.sp = 0xfd
        rows = []
        for tick in range(48):
            rows.append([tick,cpu.memory[0x9e],cpu.memory[0xa1],cpu.memory[0xc2],
                         cpu.memory[0xcb],cpu.memory[0xb6]])
            cpu.pc = 0x1bce
            cpu.memory[0x98] = direction
            cpu.memory[0x9b] = 1
            for _ in range(100000):
                if cpu.pc == 0x1c32:
                    break
                cpu.step()
            else:
                raise RuntimeError(f"{name}: did not reach stop; PC=${cpu.pc:04X}")
        path = output / (name + ".csv")
        with path.open("w",newline="",encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["tick","x_halfpixels","y","state","animation_timer","collision"])
            writer.writerows(rows)
        summary["scenarios"].append({"name":name,"samples":len(rows),
            "trace_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (output / "summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print("Wrote seven 48-step CPU-only traces. Full-machine parity remains pending.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    analyze(args.snapshot,args.output)
