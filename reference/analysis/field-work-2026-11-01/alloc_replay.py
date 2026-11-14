"""Inspect the failed test image's allocations with its four HUNK sizes preserved."""
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
from winuae_ipc import command

def main(folder="alloc-replay"):
    WORK=ROOT/".tmp/field-work"/folder
    out=WORK/"run";out.mkdir()
    elf=WORK/"bruce_test.elf";raw=(WORK/"bruce_test.exe").read_bytes();image=bytearray(raw)
    _,symbols=elf_symbols(elf)
    n=struct.unpack_from(">I",image,8)[0];pos=20+4*n
    assert struct.unpack_from(">I",image,pos)[0]==1001;code=pos+8
    # Stop after the final AllocMem, before cleanup. Skip only the slow
    # CPU fixtures, which make no persistent Exec allocation.
    objdump=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32/opt/bin/m68k-amiga-elf-objdump.exe"))[-1]
    listing=subprocess.check_output([objdump,"-d","--start-address=0","--stop-address=0x800",elf],text=True)
    stop=int(re.search(r"(?m)^\s*([0-9a-f]+):\s+4ab9 [^\n]+tst\.l [^\n]+<fighter_dma>",listing)[1],16)
    assert image[code+stop:code+stop+2]==bytes.fromhex("4ab9")
    image[code+stop:code+stop+2]=bytes.fromhex("60fe")
    for name in ("source_actor_fixture_run","bl_c64_vic_compare_selftest"):
        at=code+symbols[name]
        image[at:at+4]=bytes.fromhex("70004e75")
    (out/"bruce_test.exe").write_bytes(image)
    for name in ("winuae64.exe","winuae.ini"):shutil.copyfile(ROOT/".tmp/session-ui"/name,out/name)
    cfg=(ROOT/".tmp/bruce-a500-test.uae").read_text()
    cfg=re.sub(r"(?m)^filesystem2=rw,dh1:.*$",lambda _:"filesystem2=rw,dh1:dh1:"+str(out)+",-128",cfg)
    (out/"machine.uae").write_text(cfg)
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
    emu=subprocess.Popen([out/"winuae64.exe","-ini",out/"winuae.ini","-f",out/"machine.uae"],cwd=out,startupinfo=si)
    try:
        time.sleep(5);log=(out/"winuaebootlog.txt").read_text(errors="replace")
        pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",log)[-1]
        def cmd(s):return command(pipe,s,expected_pid=emu.pid)
        def word(at):
            s=cmd(f"DBG m {at:x} 1")
            return int("".join(re.search(r"(?mi)^[\da-f]{8}\s+([a-f\d]{4})\s+([a-f\d]{4})",s).groups()),16)
        end=time.monotonic()+120
        while time.monotonic()<end:
            r=cmd("DBG r")
            m=re.search(r"(?mi)^([a-f\d]{8})\s+60fe\b",r)
            if m:break
            time.sleep(1)
        else:raise AssertionError("Allocation checkpoint not reached")
        base=[int(m[1],16)-stop]
        for _ in range(3):base.append(4*word(base[-1]-4)+4)
        obj=dict(sections(elf)[1]);bss=obj[".bss"][3]
        nodes={k:word(base[3]+symbols[k]-bss+i*4) for k,i in (("tile_dma",0),("fighter_dma",0),("sfx_pcm",0),("background",0),("capture",0),("tone",0))}
        for k in ("buffers","copper","room_slots"):
            nodes[k]=[word(base[3]+symbols[k]-bss+i*4) for i in range(2)]
        result=dict(original_sha256=hashlib.sha256(raw).hexdigest(),controlled_copy_sha256=hashlib.sha256(image).hexdigest(),
            code_offset=stop,hunks=dict(zip((".text",".rodata",".data",".bss"),base)),allocations=nodes)
        (WORK/"allocation.json").write_text(json.dumps(result,indent=2)+"\n");print(result)
    finally:
        if emu.poll() is None:emu.terminate();emu.wait(10)

if __name__=="__main__":main(*sys.argv[1:])
