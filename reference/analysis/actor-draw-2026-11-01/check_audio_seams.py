"""Compare the native CPU state with an observing Paula callback and with none."""
import ctypes as ct
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CALLBACK = ct.CFUNCTYPE(None)


def instance(path):
    lib = ct.CDLL(str(path))
    for name in ("bl_c64_world_start","bl_c64_world_input","bl_c64_world_step"):
        getattr(lib,name).argtypes = [ct.c_long, ct.c_long]
    lib.bl_c64_world_jump.argtypes = [ct.c_long]
    lib.bl_c64_set_audio_poll.argtypes = [CALLBACK]
    lib.bl_c64_world_ready.restype = ct.c_ubyte
    lib.bl_c64_actor_return.restype = lib.bl_c64_fault.restype = ct.c_ushort
    return lib


def main(dll, output):
    copy = dll.with_name("observed.dll")
    shutil.copyfile(dll,copy)
    baseline, observed = instance(dll), instance(copy)
    data = (ct.c_ubyte*65536)()
    regs = (ct.c_ubyte*13)()
    calls = 0

    @CALLBACK
    def count():
        nonlocal calls
        calls += 1

    def state(lib):
        lib.bl_actor_copy(data)
        lib.bl_c64_actor_registers(regs)
        return bytes(data), bytes(regs), lib.bl_c64_actor_return(), lib.bl_c64_fault()

    observed.bl_c64_set_audio_poll(count)
    results = []
    for room,players,human in ((0,1,0),(0,2,1),(11,1,0),(12,2,0)):
        start = calls
        for lib in (baseline,observed):
            lib.bl_c64_world_start(players,human)
            if room: lib.bl_c64_world_jump(room)
        assert state(observed) == state(baseline)
        steps = 0
        for field in range(720):
            for lib in (baseline,observed):
                lib.bl_c64_world_input((2,9,4,17)[(field//40)%4],(field//15)%16)
                lib.bl_c64_field()
            assert state(observed) == state(baseline), (room,field,"IRQ")
            assert observed.bl_c64_world_ready() == baseline.bl_c64_world_ready()
            if baseline.bl_c64_world_ready():
                for lib in (baseline,observed): lib.bl_c64_world_step(1,1)
                assert state(observed) == state(baseline), (room,field,"main")
                steps += 1
        assert calls > start and steps > 0 and not observed.bl_c64_fault()
        results.append(dict(room=room+1,players=players,human_yamo=human,fields=720,
                            steps=steps,polls=calls-start))
    ram = (ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    sites = {0x1c23:"20c329",0x1c29:"209e17",0x25ae:"a651e002",0x2586:"8651"}
    for pc,code in sites.items(): assert ram[pc:pc+len(code)//2].hex()==code
    report = dict(source_sha256=hashlib.sha256(ram).hexdigest(),sites={hex(k):v for k,v in sites.items()},
                  comparisons=results,ram_bytes=65536,registers_and_latches=13,callback="counter only")
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS",sum(r["fields"] for r in results),"fields,",sum(r["steps"] for r in results),
          "game steps,",calls,"audio polls")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]))
