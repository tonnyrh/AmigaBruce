"""Generate only active ABI bridges; never assume optional APIs were linked."""
import argparse,json,struct
from pathlib import Path
from audit_vic_native_kernels import sections
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/native-d7-2026-10-31/candidate'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=BASE/'out');args=parser.parse_args()
    raw,ss=sections(args.out/'c64_rooms.o');plan=json.loads((BASE/'abi-plan.json').read_text());names=set()
    for _,s in ss:
        if s[1]!=2:continue
        table=ss[s[6]][1];strings=raw[table[4]:table[4]+table[5]]
        for at in range(s[4],s[4]+s[5],s[9]):
            n,value,size,info,other,index=struct.unpack_from('>IIIBBH',raw,at)
            name=strings[n:strings.index(0,n)].decode()
            if index and name.endswith('_d7') and info>>4==1:names.add(name[:-3])
    assert names<=set(plan),(names-set(plan))
    lines=['/* Public Amiga ABI: preserve all32 caller D7 bits and long args. */'];active=[]
    for name in sorted(names):
        q=plan[name]
        if not q['bridge']:continue
        # Every scalar public argument is long, all other arguments pointers.
        args=q['args'];assert args<=8,(name,args)
        tokens=q['arg_tokens'];assert not any(t in tokens for t in ['...','float','double']),(name,tokens)
        assert not any(t in tokens for t in ['char','short','int']) or '*' in tokens,(name,tokens)
        lines += [f'    .section .text.{name},"ax"',f'    .globl {name}',name+':','    move.l %d7,-(%sp)']
        lines += [f'    move.l {4*(args+1)}(%sp),-(%sp)']*args
        lines += ['    move.b bruce_a_mirror,%d7',f'    jsr {name}_d7']
        if args:lines += [f'    lea {4*args}(%sp),%sp']
        lines += ['    move.b %d7,bruce_a_mirror','    move.l (%sp)+,%d7','    rts']
        active.append(dict(name=name,args=args))
    (BASE/'abi-wrappers.s').write_text('\n'.join(lines)+'\n')
    (BASE/'active-abi.json').write_text(json.dumps(dict(active=active,readonly_aliases=sorted(names-set(q['name'] for q in active))),indent=2)+'\n')
    print('Generated',len(active),'D7 bridges;',len(names)-len(active),'readonly aliases')

if __name__=='__main__':main()
