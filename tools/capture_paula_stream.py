"""Record the current normal program through an owned full WinUAE instance.

No UI input or global configuration changes. Source SFX queues are explicitly
injected in the otherwise idle title loop for the final diagnostic take.
"""
import argparse
import ctypes
import json
from pathlib import Path
import re
import struct
import time
from winuae_ipc import command

ROOT=Path(__file__).resolve().parents[1]


def elf_hunk_index(path, section_name='.bss'):
    """Locate an allocated ELF section, including optional Chip audio hunks."""
    b=Path(path).read_bytes();assert b[:6]==b'\x7fELF\x01\x02'
    off=struct.unpack_from('>I',b,32)[0]
    size,count,names=struct.unpack_from('>HHH',b,46)
    sections=[struct.unpack_from('>10I',b,off+i*size) for i in range(count)]
    strings=sections[names];text=b[strings[4]:strings[4]+strings[5]]
    allocated=[s for s in sections if s[2]&2 and s[5]]
    return next(i for i,s in enumerate(allocated)
                if text[s[0]:text.index(0,s[0])].decode()==section_name)


def elf_symbols(path):
    b=path.read_bytes();assert b[:6]==b'\x7fELF\x01\x02'
    off=struct.unpack_from('>I',b,32)[0]
    size,count,names=struct.unpack_from('>HHH',b,46)
    sections=[struct.unpack_from('>10I',b,off+i*size) for i in range(count)]
    strings=sections[names];text=b[strings[4]:strings[4]+strings[5]]
    def name(table,at):return table[at:table.index(0,at)].decode()
    bss=[s for s in sections if name(text,s[0])=='.bss'][0]
    symbols={}
    for s in sections:
        if s[1]!=2:continue
        strings=sections[s[6]];table=b[strings[4]:strings[4]+strings[5]]
        for at in range(s[4],s[4]+s[5],s[9]):
            n,value,_,_,_,_=struct.unpack_from('>IIIBBH',b,at)
            if n:symbols[name(table,n)]=value
    return bss[3],symbols


def capture(folder,pid):
    log=(folder/'winuaebootlog.txt').read_text(errors='replace')
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",log)[-1]
    calls=[]
    def cmd(text):
        result=command(pipe,text,expected_pid=pid)
        calls.append(dict(command=text,result=result,qpc=time.perf_counter()))
        return result
    def memory(at,n):
        text=cmd(f'DBG m {at:x} {(n+15)//16:x}')
        data=bytearray()
        for line in text.splitlines():
            match=re.match(r'^[0-9A-Fa-f]{8}\s+((?:[0-9A-Fa-f]{4}\s+){1,8})',line)
            if match:data.extend(bytes.fromhex(match[1]))
        assert len(data)>=n,(text,n)
        return bytes(data[:n])
    def long(at):return int.from_bytes(memory(at,4),'big')
    # ExecBase.ThisTask, Process.pr_CLI and CLI.cli_Module offsets verified
    # against the bundled Kickstart-compatible ABI headers (276/172/60).
    execbase=long(4);task=long(execbase+276);cli=long(task+172)*4;node=long(cli+60)*4
    hunks=[]
    while node:
        assert len(hunks)<8
        hunks.append(node+4);node=long(node)*4
    bss_hunk=elf_hunk_index(ROOT/'amiga/out/bruce_amiga.elf')
    assert len(hunks)>bss_hunk,hunks
    bss,symbols=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
    def address(name):return hunks[bss_hunk]+symbols[name]-bss
    def counter(name):return long(address(name))
    def clock():
        a=time.perf_counter();value=counter('source_music_fields');b=time.perf_counter()
        return (a+b)/2,value
    addrs={n:address(n) for n in ('m','source_audio','source_audio_mode','source_music_fields',
        'source_audio_fields','source_clock_last','source_clock_missed','source_clock_elapsed','sfx_pcm')}
    assert memory(addrs['source_audio_mode'],1)==b'\x01', 'Expected title music'
    assert 0<counter('source_music_fields')<100000
    (folder/'addresses.json').write_text(json.dumps(dict(hunks=hunks,bss_vma=bss,addresses=addrs),indent=2)+'\n')
    (folder/'hardware-before.txt').write_text(cmd('DBG c'))
    takes=[]
    def begin(label,mask):
        cmd(f'DBG Ma {mask:x}')
        before=set(folder.glob('*.avi'));qpc,fields=clock()
        cmd(f'EVT AKS_VIDEORECORDFILE "{folder/label}.avi"')
        cmd('EVT AKS_VIDEORECORD 1')
        return before,qpc,fields
    def end(label,state):
        cmd('EVT AKS_VIDEORECORD 0')
        time.sleep(.15)
        files=set(folder.glob('*.avi'))-state[0];assert len(files)==1,files
        qpc,fields=clock()
        takes.append(dict(name=label,file=files.pop().relative_to(ROOT).as_posix(),
            host_seconds=qpc-state[1],title_fields_before=state[2],title_fields_after=fields))
        print('RECORDED',label,flush=True)
    for label,mask in [('title-paula-0',1),('title-paula-1',2),('title-paula-2',4),('title-mixed',7)]:
        print('RECORDING',label,flush=True);state=begin(label,mask);time.sleep(26.1);end(label,state)
    # Keep normal main in the idle title wait; switch only its audio dispatch
    # and controlled source queues. No test/replacement executable is loaded.
    cmd(f'DBG W {addrs["source_audio_mode"]:x} 00')
    cmd(f'DBG W {addrs["source_audio"]:x} '+('00 '*48))
    m=addrs['m'];time.sleep(.1)
    events=[];state=begin('noise-to-lantern',1)
    for fx in (0x80,0x8e,0x85,0x8e,0x84,0x8e):
        cmd(f'DBG W {m+0xd418:x} 15')
        before=counter('source_audio_fields')
        cmd(f'DBG W {m+0xeb00:x} {fx:02x}')
        events.append(dict(effect=fx,before_field=before,after_field=counter('source_audio_fields'),host_qpc=time.perf_counter()))
        time.sleep(.85)
    time.sleep(.5);end('noise-to-lantern',state)
    (folder/'hardware-after.txt').write_text(cmd('DBG c'))
    report=dict(method='Owned normal executable; diagnostic voice masks and injected source queues in idle title loop',
        pid=pid,pipe=pipe,natural_playthrough=False,takes=takes,events=events,
        counters={n:counter(n) for n in ('source_music_fields','source_audio_fields','source_clock_last','source_clock_missed','source_clock_elapsed')},
        calls=calls)
    (folder/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    try:cmd('IPC_QUIT')
    except (OSError,TimeoutError):pass # Process may close its pipe before replying.


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--pid',type=int,required=True)
    a=p.parse_args();capture(a.folder.resolve(),a.pid)
