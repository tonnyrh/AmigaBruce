"""Full-machine traces of the registered local candidate, not a retail certification.

Uses VICE 3.10 IO Simulation through CIA, never writes gameplay RAM/code/PC.
The initial registered snapshot was bootstrapped as documented in manifest.json.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from vice_binary import Vice

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = 0x1bce
FIELDS = 63 * 312


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample(vice, tick, input_value, origin):
    before = vice.history_clock()
    ram = vice.memory(0, 0x10f)
    regs = vice.registers()
    after = vice.history_clock()
    if before != after or regs[3] != ADDRESS or before[0] != 0x1bcc:
        raise RuntimeError("CPU advanced during paused observation or wrong loop boundary")
    return [tick, input_value, before[1]-origin, regs[0x35], regs[0x36],
            ram[0x98], ram[0x9b], ram[0x9e], ram[0xa1], ram[0xb9], ram[0xa4],
            ram[0xbf], ram[0xc2], ram[0xcb], ram[0xb6], ram[0x106], ram[0x29]]


def capture(port, output, selected=None, capture_id="MACHINE-0001", scenario_file=None):
    manifest = json.loads((ROOT / "reference/manifest.json").read_text(encoding="utf-8"))
    candidate = manifest["analysis_candidate"]
    snapshot = ROOT / candidate["baseline_snapshot_path"]
    if digest(snapshot) != candidate["baseline_snapshot_sha256"]:
        raise ValueError("Snapshot hash mismatch")
    for section, path_key, hash_key in [(candidate,"working_prg_path","working_prg_sha256"),
            (manifest["emulator"],"executable_path","executable_sha256")]:
        if digest(ROOT / section[path_key]) != section[hash_key]:
            raise ValueError("Candidate/emulator identity mismatch")
    output.mkdir(parents=True, exist_ok=True)
    scenarios = {
        "idle": [0xff]*48,
        "right": [0xf7]*32+[0xff]*16,
        "left": [0xfb]*20+[0xff]*28,
        "standing-jump": [0xfe]*2+[0xff]*46,
        "moving-jump": [0xf7]*10+[0xf6]*2+[0xff]*36,
        "reverse": [0xf7]*12+[0xfb]*12+[0xff]*24,
        "climb": [0xf7]*11+[0xfe]*30+[0xff]*7,
        "climb-down": [0xf7]*11+[0xfe]*12+[0xfd]*12+[0xff]*13,
        "held-jump": [0xfe]*40+[0xff]*8,
        "central-climb": [0xf7]*24+[0xfe]*40+[0xff]*16,
        "central-climb-down": [0xf7]*24+[0xfe]*20+[0xfd]*20+[0xff]*16,
        "central-top-held": [0xf7]*24+[0xfe]*140+[0xff]*16,
        "central-top-release": [0xf7]*24+[0xfe]*100+[0xff]*8+[0xfe]*32+[0xff]*16,
    }
    if scenario_file:
        programs=json.loads(scenario_file.read_text(encoding="utf-8"))
        custom={}
        for name,segments in programs.items():
            values=[]
            for value,count in segments:
                if not isinstance(value,int) or not 0<=value<=255 or not isinstance(count,int) or not 1<=count<=2048:
                    raise ValueError("Invalid joystick program segment")
                values.extend([value]*count)
            if len(values)>2048:raise ValueError("Joystick program too long")
            custom[name]=values
        scenarios=custom
    if selected:
        scenarios={name:scenarios[name] for name in selected}
    columns = ["tick","joystick_active_low","cycles","raster_line","raster_cycle",
        "sampled_direction","sampled_fire","target_x_halfpixels","target_y",
        "latched_x_halfpixels","facing_raw","next_state","state","animation_timer",
        "collision","wait","room"]
    vice = Vice(port)
    checkpoint = None
    summary = {"capture_id":capture_id, "status":"candidate_full_machine_replay",
        "primary_edition_verified":False, "snapshot_sha256":digest(snapshot),
        "emulator_sha256":manifest["emulator"]["executable_sha256"],
        "profile":"VICE 3.10 x64sc PAL C64 MOS6569R3; sound disabled; IO Simulation on port 1",
        "input":"active-low joystick lines via VICE IO Simulation device 37, zero-based port 0",
        "boundary":"$1BCE before keyboard parser; last executed instruction $1BCC",
        "warmup_idle_steps":8, "repetitions":2, "scenarios":[]}
    summary["recorder_sources"]=[{"path":name,"sha256":digest(ROOT/name)}
        for name in ("tools/vice_binary.py","tools/capture_c64_movement.py","capture-c64.ps1")]
    if scenario_file:
        summary["input_program_sha256"]=digest(scenario_file)
    try:
        for name, inputs in scenarios.items():
            repetitions = []
            for repetition in range(2):
                if checkpoint is not None:
                    vice.command(0x13, checkpoint.to_bytes(4,"little"))
                if vice.restore(snapshot) != ADDRESS:
                    raise RuntimeError("Unexpected snapshot PC")
                vice.resource_int("JoyPort1Device",37)
                vice.resource_int("JoyPort2Device",1)
                vice.joystick(0xff)
                checkpoint = vice.checkpoint(ADDRESS)
                for _ in range(8):
                    vice.next_hit(checkpoint, ADDRESS)
                origin = vice.history_clock()[1]
                rows = [sample(vice,0,0xff,origin)]
                for tick, value in enumerate(inputs,1):
                    vice.joystick(value)
                    vice.next_hit(checkpoint,ADDRESS)
                    rows.append(sample(vice,tick,value,origin))
                repetitions.append(rows)
            if repetitions[0] != repetitions[1]:
                raise RuntimeError(f"{name}: repeated capture differs")
            rows = repetitions[0]
            gaps = [rows[i][2]-rows[i-1][2] for i in range(1,len(rows))]
            field_intervals=[gap-((rows[i][3]-rows[i-1][3])*63+rows[i][4]-rows[i-1][4])
                for i,gap in enumerate(gaps,1)]
            if any(interval != 3*FIELDS for interval in field_intervals):
                raise RuntimeError(f"{name}: unexpected step cadence {min(gaps)}..{max(gaps)}")
            path = output / f"{name}.csv"
            with path.open("w",newline="",encoding="utf-8") as stream:
                writer=csv.writer(stream)
                writer.writerow(columns)
                writer.writerows(rows)
            summary["scenarios"].append({"name":name,"samples":len(rows),"identical_replays":2,
                "sha256":digest(path),"min_step_cycles":min(gaps),"max_step_cycles":max(gaps),
                "phase_corrected_cycles_per_step":3*FIELDS,
                "x_range":[min(r[7] for r in rows),max(r[7] for r in rows)],
                "y_range":[min(r[8] for r in rows),max(r[8] for r in rows)]})
            print(f"PASS {name}: two identical replays, {len(rows)} samples, {min(gaps)}..{max(gaps)} cycles/step",flush=True)
        (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    finally:
        if checkpoint is not None:
            vice.command(0x13,checkpoint.to_bytes(4,"little"))
        vice.close()


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=6512)
    parser.add_argument("--output",type=Path,default=ROOT/"reference/traces/MACHINE-0001")
    parser.add_argument("--scenario",action="append")
    parser.add_argument("--capture-id",default="MACHINE-0001")
    parser.add_argument("--scenario-file",type=Path)
    args=parser.parse_args()
    capture(args.port,args.output,args.scenario,args.capture_id,args.scenario_file)
