"""Read source-world diagnostics from an explicitly owned WinUAE PID."""
import argparse,json,re,sys
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);args=p.parse_args()
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",args.log.read_text(errors='replace'))[-1]
    def read(at,n):
        out=bytearray()
        for offset in range(0,n,128):
            text=command(pipe,f'DBG m {at+offset:x} {min(8,(n-offset+15)//16):x}',expected_pid=args.pid)
            for line in text.splitlines():
                match=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
                if match:out.extend(bytes.fromhex(match[1]))
        assert len(out)>=n,(hex(at),n,len(out));return bytes(out[:n])
    def long(at):return int.from_bytes(read(at,4),'big')
    task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
    while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
    bss,symbols=elf_symbols(args.elf);assert len(hunks)==4,hunks
    def address(name):return hunks[3]+symbols[name]-bss
    values={name:read(address(name),2 if name in ('actor_logic_steps','source_fault','actor_loading_epoch') else 1).hex()
        for name in ('actor_logic_steps','source_fault','actor_loading_epoch','actor_world_enabled','loaded','actor_delay_pending','actor_gameover_pending','sp','a','x','y')}
    values['m']={hex(at):read(address('m')+at,n).hex() for at,n in [(0x28,28),(0x48,1),(0x95,63),(0x87,2),(0xd01e,1)]}
    values['hunks']=hunks;print(json.dumps(values,indent=2))
if __name__=='__main__':main()
