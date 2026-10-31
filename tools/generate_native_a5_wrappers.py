"""Public ABI bridges for the isolated A5 RAM-base experiment."""
import json,struct
from pathlib import Path
from audit_vic_native_kernels import sections
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/native-a5-2026-10-31/candidate'

def main():
    raw,ss=sections(BASE/'out/c64_rooms.o');plan=json.loads((BASE/'abi-plan.json').read_text());names=set()
    for _,s in ss:
        if s[1]!=2:continue
        table=ss[s[6]][1];strings=raw[table[4]:table[4]+table[5]]
        for at in range(s[4],s[4]+s[5],s[9]):
            n,value,size,info,other,index=struct.unpack_from('>IIIBBH',raw,at)
            name=strings[n:strings.index(0,n)].decode()
            if index and name.endswith('_a5') and info>>4==1:names.add(name[:-3])
    assert names<=set(plan)
    lines=[];active=[]
    for name in sorted(names):
        q=plan[name]
        if not q['bridge']:continue
        args=q['args'];assert args<=8
        lines += [f'    .section .text.{name},"ax"',f'    .globl {name}',name+':','    move.l %a5,-(%sp)']
        lines += [f'    move.l {4*(args+1)}(%sp),-(%sp)']*args
        lines += ['    lea bruce_m_storage,%a5',f'    jsr {name}_a5']
        if args:lines += [f'    lea {4*args}(%sp),%sp']
        lines += ['    move.l (%sp)+,%a5','    rts'];active.append(name)
    (BASE/'abi-wrappers.s').write_text('\n'.join(lines)+'\n')
    (BASE/'active-abi.json').write_text(json.dumps(active,indent=2)+'\n')
    print('Generated',len(active),'A5 bridges')

if __name__=='__main__':main()
