import json
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/".tmp/field-work"
sys.path.insert(0,str(ROOT/"tools"))
from winuae_ipc import command

def run(label):
    folder=WORK/label;folder.mkdir()
    for name in ("winuae64.exe","winuae.ini"):shutil.copyfile(ROOT/".tmp/session-ui"/name,folder/name)
    shutil.copyfile(WORK/"ports/bruce_amiga.exe",folder/"bruce_amiga.exe")
    cfg=(ROOT/".tmp/bruce-a500.uae").read_text()
    cfg=re.sub(r"(?m)^filesystem2=rw,dh1:.*$",lambda _:"filesystem2=rw,dh1:dh1:"+str(folder)+",-128",cfg)
    (folder/"machine.uae").write_text(cfg)
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
    emulator=subprocess.Popen([folder/"winuae64.exe","-ini",folder/"winuae.ini","-f",folder/"machine.uae"],cwd=folder,startupinfo=si)
    try:
        deadline=time.monotonic()+120
        for i in range(12):
            while not (folder/"request.bin").exists() or (folder/"request.bin").read_bytes()!=struct.pack(">I",i):
                if time.monotonic()>deadline or (folder/"ports.bin").exists():raise RuntimeError(("request",i))
                time.sleep(.1)
            pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(folder/"winuaebootlog.txt").read_text(errors="replace"))[-1]
            command(pipe,"EVT JOY2_RIGHT "+str(int(i%6!=3)),expected_pid=emulator.pid)
            time.sleep(.25);(folder/f"go{i:02}").write_bytes(b"1")
        while not (folder/"ports.bin").exists() and time.monotonic()<deadline:time.sleep(.1)
        result=struct.unpack(">III",(folder/"ports.bin").read_bytes())
        assert result==(12,0,1),result
        print("actual JOY1DAT via WinUAE compared with 12 VICE slot samples",result)
    finally:
        if emulator.poll() is None:emulator.terminate();emulator.wait(timeout=10)

if __name__=="__main__":run(sys.argv[1])
