"""Check actual DOS-loaded executable, normal joystick/keyboard, no guest state writes."""
import hashlib
import json
import re
import struct
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
from capture_paula_stream import elf_symbols
from title_reference import reference
from winuae_ipc import command
from audit_vic_native_kernels import sections

def main():
    folder,pid,mode=Path(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
    log=folder/"winuaebootlog.txt"
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",log.read_text(errors="replace"))[-1]
    def cmd(s):return command(pipe,s,expected_pid=pid)
    def mem(at,size):
        s=cmd(f"DBG m {at:x} {(size+15)//16:x}");data=b"".join(bytes.fromhex(m[1]) for m in re.finditer(r"(?m)^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})",s))
        assert len(data)>=size
        return data[:size]
    def val(at,n=4):return int.from_bytes(mem(at,n),"big")
    def key(k):
        cmd("EVT KEY_"+k+" 1");time.sleep(.4);cmd("EVT KEY_"+k+" 0");time.sleep(1.3)
    def wait(test,seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if test():return
            time.sleep(.5)
        raise AssertionError("timeout: "+str(test))
    expected=reference();hunks=[]
    def menu():
        try:
            task=val(val(4)+276);node=val(val(task+172)*4+60)*4;hunks.clear()
            while node and len(hunks)<5:hunks.append(node+4);node=val(node)*4
            if len(hunks)!=4:return False
            copper=int(re.search(r"COP1LC: \$([0-9a-fA-F]+)",cmd("DBG c"))[1],16)
            words=struct.unpack(">34H",mem(copper,68));front=words[19]*65536+words[21]
            if not 0<front<0x80000:return False
            # Compare visible menu before measurement. No snapshots during the timed run.
            picture=folder/"menu.bpl"
            return "Wrote " in cmd(f"DBG S {picture} {front:x} a000") and picture.read_bytes()==expected
        except (IndexError,TypeError,AssertionError,ValueError):return False
    wait(menu,180)
    elf=ROOT/"amiga/out/bruce_amiga.elf";_,symbols=elf_symbols(elf)
    _,ss=sections(elf);segs=[dict(ss)[s] for s in (".text",".rodata",".data",".bss")]
    def addr(name):
        at=symbols[name];i=next(i for i,s in enumerate(segs) if s[3]<=at<s[3]+s[5])
        return hunks[i]+at-segs[i][3]
    ram=addr("m")
    def measure():
        return dict(field=val(addr("game_field_last")),steps=val(addr("actor_logic_steps"),2),
                    ticks=val(addr("source_audio_fields")),misses=val(addr("source_clock_missed")),
                    room=val(ram+0x29,1)+1,actors=list(mem(ram+0x95,3)),fault=val(addr("source_fault"),2))
    # Normal menu selection. Two-player mode lets the post-run death test
    # observe the source hand-off, through normal controls only.
    if mode=="adf":key("F3")
    cmd("EVT KEY_SHIFT_LEFT 1");key("D");cmd("EVT KEY_SHIFT_LEFT 0")
    key("F1");key("F2");key("RETURN")
    wait(lambda:val(addr("game_field_active"),1) and val(addr("actor_logic_steps"),2)>=120,120)
    assert val(addr("actor_invincible"),1) and val(addr("actor_infinite"),1)
    assert val(ram+0x42c9,1)==int(mode=="adf")
    key("P");paused=measure();time.sleep(1);paused_after=measure()
    assert paused["steps"]==paused_after["steps"] and paused["ticks"]==paused_after["ticks"]
    key("P")
    wait(lambda:val(addr("actor_logic_steps"),2)!=paused["steps"],30)
    before=measure()
    duration=10 if mode=="cross" else 6000
    wait(lambda:((val(addr("game_field_last"))-before["field"])&0xffffff)>=duration,360)
    after=measure()
    layout=[dict(section=n,base=at,bytes=s[5]) for n,at,s in zip((".text",".rodata",".data",".bss"),hunks,segs)]
    dma={n:val(addr(n)) for n in ("background","sfx_pcm","tile_dma","fighter_dma")}
    assert all(0<at<524288 for at in dma.values())
    fields=(after["field"]-before["field"])&0xffffff
    steps=(after["steps"]-before["steps"])&65535
    assert fields>=duration and steps>0 and not(before["fault"] or after["fault"])
    data=dict(mode=mode,normal_exe_sha256=hashlib.sha256((ROOT/"amiga/out/bruce_amiga.exe").read_bytes()).hexdigest(),
              complete_menu=True,menu_sha256=hashlib.sha256(expected).hexdigest(),layout=layout,dma=dma,
              before=before,after=after,fields=fields,steps=steps,misses=after["misses"]-before["misses"])
    data["pause_preserved"]=True
    path=folder/"normal.json";path.write_text(json.dumps(data,indent=2)+"\n")
    if mode=="adf":
        # A new game resets defaults in the menu. Select two players if needed.
        key("F10");time.sleep(1)
        key("RETURN");time.sleep(3)
        if val(ram+0x42c9,1)==0:
            key("F10");time.sleep(1);key("F3");key("RETURN")
        wait(lambda:val(addr("actor_logic_steps"),2)>4,60)
        if val(addr("actor_invincible"),1):
            key("F10");time.sleep(1);cmd("EVT KEY_SHIFT_LEFT 1");key("D");cmd("EVT KEY_SHIFT_LEFT 0");key("F2");key("RETURN")
        wait(lambda:val(ram+3,1)==1 and val(addr("actor_life_events"),2)>0,300)
        data["turn_after_death"]=dict(player=val(ram+3,1)+1,room=val(ram+0x29,1)+1,
            falls=val(ram+0x28,1),fault=val(addr("source_fault"),2))
        assert data["turn_after_death"]["fault"]==0
    else:
        # The right-hand door is on the mezzanine (source Y=146).
        # The purple central net at x=144..167 is climbable in room 1.
        # Reach the upper walk, then run right onto the lower exit.
        key("F10");time.sleep(1);key("RETURN")
        wait(lambda:val(addr("game_field_active"),1) and val(ram+0x29,1)==0,60)
        def position():
            p=mem(ram+0x9e,4)
            return (p[0]*2-24,p[3])
        def joy(name,on):cmd("EVT JOY2_"+name+" "+str(int(on)))
        start=time.monotonic()
        while abs(position()[0]-152)>4:
            assert time.monotonic()-start<60,position()
            direction="RIGHT" if position()[0]<152 else "LEFT"
            joy(direction,True);time.sleep(.16);joy(direction,False)
        data["trellis_entry"]=position()
        joy("UP",True)
        try:wait(lambda:position()[1]<=98,60)
        finally:joy("UP",False)
        data["trellis_exit"]=position()
        for direction,room in (("RIGHT",2),("LEFT",1)):
            cmd("EVT JOY2_"+direction+" 1")
            try:wait(lambda:val(ram+0x29,1)==room-1,45)
            finally:cmd("EVT JOY2_"+direction+" 0")
            data.setdefault("joystick_crossings",[]).append(room)
    path.write_text(json.dumps(data,indent=2)+"\n")
    print(mode,fields,steps,data["misses"])

if __name__=="__main__":main()
