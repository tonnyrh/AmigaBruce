"""Extract candidate room data and statically translate its room subroutines.

Generated C contains native branches/calls, never an opcode interpreter.
Only room programs and their reachable helpers are translated. Hardware IRQ,
actor movement/combat and the whole C64 main loop are NOT translated here.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
from c64_room_model import decode, word

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.reference/tools/python'))

SOURCE = ROOT / '.reference/c64/work/untrained-memory.bin'
ASSETS = ROOT / 'assets/c64/rooms-v1'
HOOKS = {0x0b30,0x17e2,0x2f8e, 0x33bd, 0x3a6f}
BRANCHES = {'bcc': '!c', 'bcs': 'c', 'beq': 'z', 'bne': '!z',
            'bmi': 'n', 'bpl': '!n', 'bvc': '!v', 'bvs': 'v'}


def array(name, data):
    rows = [','.join(str(x) for x in data[i:i+24]) for i in range(0,len(data),24)]
    return f'static const unsigned char {name}[{len(data)}]={{\n' + ',\n'.join(rows) + '\n};\n'


def translate(memory, roots, *, actors=False):
    from py65.devices.mpu6502 import MPU
    cpu = MPU(memory=list(memory))
    hooks=(HOOKS-{0x0b30,0x2f8e}) | {0x050f,0x0584,0x0f47,0x1c32,0x1968,0x197d,0x169d,0x179d} if actors else HOOKS
    entries, pending, code = set(roots) | hooks, list(roots), {}
    while pending:
        pc = pending.pop()
        if pc in hooks or pc in code:
            continue
        op, mode = cpu.disassemble[memory[pc]]
        op = op.lower()
        assert op != '???', f'Undecodable room instruction ${pc:04X}'
        size = 1 if mode in ('acc','imp') else 3 if mode in ('abs','abx','aby','ind') else 2
        operand = memory[pc+1] if size == 2 else word(memory,pc+1) if size == 3 else 0
        code[pc] = (op,mode,size,operand)
        if op in BRANCHES:
            pending += [pc+size, (pc+size+(operand if operand<128 else operand-256))&65535]
        elif op in ('jmp','jsr'):
            assert mode == 'abs', f'Indirect control flow ${pc:04X}: must be resolved explicitly'
            entries.add(operand); pending.append(operand)
            if op == 'jsr':
                pending.append(pc+size)
                if actors:entries.add(pc+size)
        elif op not in ('rts','brk'):
            pending.append(pc+size)
    def addr(mode,o):
        if mode in ('abs','zpg'): return f'0x{o:04x}'
        if mode=='abx': return f'(unsigned short)(0x{o:04x}+x)'
        if mode=='aby': return f'(unsigned short)(0x{o:04x}+y)'
        if mode=='zpx': return f'(unsigned char)(0x{o:02x}+x)'
        if mode=='zpy': return f'(unsigned char)(0x{o:02x}+y)'
        if mode=='iny': return f'(unsigned short)(W(0x{o:02x})+y)'
        if mode=='inx': return f'ZW((unsigned char)(0x{o:02x}+x))'
        raise AssertionError(mode)
    def watched(mode,o):
        # Only these addresses can change visible characters/attributes.
        # Fixed source-state writes need no renderer notification.
        if mode in ('iny','inx'):return True
        if mode in ('zpg','zpx','zpy'):return False
        last=o+(255 if mode in ('abx','aby') else 0)
        return any(o<end and last>=start for start,end in ((0x8c78,0x8fe8),(0xa000,0xc000),(0xd878,0xdbe8))) or last>65535
    lines=['/* GENERATED from frozen bytes by tools/build_c64_rooms.py. */',
           ('static void actor_code(unsigned short entry){' if actors else 'static void room_code(unsigned short entry){'),
           'unsigned short address;unsigned char q,old;',
           'switch(entry){']
    for e in sorted(entries): lines.append(f'case 0x{e:04x}:goto L{e:04x};')
    lines+=['default:source_fault=entry;return;','}']
    for pc in sorted(set(code)|hooks):
        lines.append(f'L{pc:04x}:; /* ${pc:04X} */')
        if pc in hooks:
            statement={0x0b30:'sp+=2;return;',0x17e2:'source_string();return;',0x2f8e:'source_transition(a,y,m[0x4e]);return;',
                          0x33bd:'x=(unsigned char)(2*m[0x29]);a=m[0x4e9d+x];m[0x100+sp--]=a;a=m[0x4e9c+x];NZ(a);m[0x100+sp--]=a;sp+=2;room_code(W(0x4e9c+x)+1);return;',
                          0x3a6f:'room_code(W(0x4ec4+2*m[0x29])+1);return;',
                          0x050f:'actor_reset_pending=1;return;',0x0584:'actor_reset_pending=1;return;',
                          0x1968:'actor_gameover_pending=1;return;',0x197d:'actor_gameover_pending=2;return;',
                          0x0f47:'actor_delay_pending=1;return;',
                          0x169d:'actor_irq_stop=1;return;',0x179d:'actor_irq_stop=1;return;',
                          0x1bc2:'return;',0x1c32:'actor_stop_pc=0x1c32;return;',
                          0x2f9a:'source_transition(a,y,m[0x4e]);return;'}[pc]
            if actors and pc in (0x33bd,0x3a6f):
                table=0x4e9c if pc==0x33bd else 0x4ec4
                statement=f'a=m[0x29];c=(a>>7);a=(unsigned char)(a<<1);x=a;NZ(x);a=m[0x{table+1:04x}+x];NZ(a);m[0x100+sp--]=a;a=m[0x{table:04x}+x];NZ(a);m[0x100+sp--]=a;sp+=2;room_code(W(0x{table:04x}+x)+1);return;'
            if actors and pc not in (0x050f,0x0584,0x0f47,0x1968,0x197d,0x169d,0x179d,0x1bc2,0x1c32):statement=statement.replace('return;','actor_return=source_stack_return();return;')
            lines.append(statement);continue
        op,mode,size,o=code[pc]
        if actors and pc==0x1bc2:lines.append('if(actor_preparing){actor_stop_pc=0x1bc2;return;} ++actor_logic_steps;')
        if actors and pc==0x09f6:lines.append('if(actor_debug_target==11)goto L0a0e;')
        if actors and pc==0x0b30:lines.append('if(actor_legacy_load){sp+=2;actor_return=source_stack_return();return;}')
        if actors and pc==0x09bc:lines.append('source_actor_loading_begin();')
        if actors and pc==0x1818:lines.append('++actor_life_events;')
        if actors and pc in (0x5214,0x2586):lines.append('if(actor_world_enabled && io_service)io_service();')
        if actors and pc in (0x0cd5,0x0df8):lines.append('++actor_spawn_events;')
        if actors and pc==0x1826:lines.append('if(actor_infinite){NZ(m[0x28]);goto L1828;}')
        if actors and pc==0x2b4e:lines.append('if(actor_invincible)m[0xbc]&=1;')
        if actors and pc==0x304b:lines.append('if(actor_invincible && !m[0x51]){sp+=2;actor_return=source_stack_return();return;}')
        if actors and pc==0x407d:lines.append('if(actor_invincible && !x){sp+=2;actor_return=source_stack_return();return;}')
        return_helper='actor_return=source_stack_return();' if actors else ''
        if pc==0x2cf1:lines.append('if(!d && m[0x64]<8){source_animation();'+return_helper+'return;}')
        if pc==0x104b:lines.append('if(!d){source_movers();'+return_helper+'return;}')
        if pc==0x2509:lines.append('source_sound();'+return_helper+'return;')
        if actors and pc==0x26a0:lines.append('if(!d && m[0xe0+x]<32){source_sprite_copy();'+return_helper+'return;}')
        if actors and pc==0x52ad:lines.append('if(m[0x1b]<4 && m[0x1c]<8){source_contact_align();'+return_helper+'return;}')
        if actors and pc==0x537e:lines.append('source_contact_rows();'+return_helper+'return;')
        value=f'0x{o:02x}' if mode=='imm' else 'a' if mode=='acc' else f'm[{addr(mode,o)}]' if mode not in ('imp','rel') else ''
        if actors and mode=='abs' and o==0xd01e:
            assert op=='lda',(hex(pc),op)
            value='source_vic_read()'
        if pc==0x2d2b: value='m[(unsigned short)(W(0x2d2c)+x)]' # Source SMC rotating glyph pattern.
        if pc in (0x0d55,0x0d85):value=f'm[W(0x{pc+1:04x})]' # Original return-delay operand writes.
        if actors and pc in (0x26aa,0x26e3,0x26ed,0x52cb,0x5380,0x539a,0x53b4):
            # $2719 and the contact kernel change operands, not game rules.
            value=f'm[(unsigned short)(W(0x{pc+1:04x})'+('+x' if mode=='abx' else '+y' if mode=='aby' else '')+')]'
        if actors and pc in (0x1159,0x1ffe):
            lines.append(f'if(m[0x{pc:04x}]!=0x{memory[pc]:02x}){{source_fault=0x{pc:04x};return;}}')
        if op in ('lda','ldx','ldy'): statement=f'{op[-1]}={value};NZ({op[-1]});'
        elif op in ('sta','stx','sty'):statement=f'address={addr(mode,o)};m[address]={op[-1]};source_written(address);'
        elif op in ('tax','tay','txa','tya'):statement=f'{op[-1]}={op[1]};NZ({op[-1]});'
        elif op=='txs' and actors:statement='sp=x;'
        elif op=='tsx' and actors:statement='x=sp;NZ(x);'
        elif op in ('inx','iny','dex','dey'):statement=f'{op[2]}{("++" if op[:2]=="in" else "--")};NZ({op[2]});'
        elif op in ('inc','dec'):statement=f'address={addr(mode,o)};m[address]{("++" if op=="inc" else "--")};NZ(m[address]);source_written(address);'
        elif op in ('and','ora','eor'):statement=f'a{dict(and_="&",ora="|",eor="^")["and_" if op=="and" else op]}={value};NZ(a);'
        elif op in ('cmp','cpx','cpy'):
            reg={'cmp':'a','cpx':'x','cpy':'y'}[op]
            statement=(f'c=1;NZ({reg});' if mode=='imm' and o==0 else f'c={reg}>={value};NZ((unsigned char)({reg}-{value}));')
        elif op=='bit':statement=f'z=(a&{value})==0;n=({value}&128)!=0;v=({value}&64)!=0;'
        elif op in ('asl','lsr','rol','ror'):
            statement=f'old={value};'
            statement+=f'{value}=(unsigned char)'+{'asl':'(old<<1)','lsr':'(old>>1)','rol':'((old<<1)|c)','ror':'((old>>1)|(c<<7))'}[op]+';'
            statement+=f'c=(old&{128 if op in ("asl","rol") else 1})!=0;NZ({value});'
            if mode!='acc':statement+=f'source_written({addr(mode,o)});'
        elif op in ('adc','sbc'):statement=f'{op}({value});'
        elif op in ('clc','sec','clv','cld','sed'):statement={'clc':'c=0;','sec':'c=1;','clv':'v=0;','cld':'d=0;','sed':'d=1;'}[op]
        elif op in ('sei','cli') and actors:statement='actor_i='+('1;' if op=='sei' else '0;')
        elif op=='pha':statement='m[0x100+sp--]=a;'
        elif op=='pla':statement='a=m[0x100+(unsigned char)++sp];NZ(a);'
        elif op=='php':statement='m[0x100+sp--]=(unsigned char)(0x30|c|(z<<1)|(d<<3)|(v<<6)|(n<<7)'+('|(actor_i<<2)' if actors else '')+');'
        elif op=='plp':statement='q=m[0x100+(unsigned char)++sp];c=q&1;z=(q>>1)&1;d=(q>>3)&1;v=(q>>6)&1;n=q>>7;'+('actor_i=(q>>2)&1;' if actors else '')
        elif op=='nop':statement=''
        elif op=='brk':statement=f'source_fault=0x{pc:04x};return;'
        elif op=='rts':statement='sp+=2;'+return_helper+'return;'
        elif op=='jsr':
            statement=f'm[0x100+sp--]=0x{(pc+2)>>8:02x};m[0x100+sp--]=0x{(pc+2)&255:02x};'
            if o==0x1159:
                # Inline the complete source helper. Repeated re-entry into
                # the large native dispatch is unnecessary; source stack,
                # pointer wrap and final flags remain exactly the same.
                statement+='if(m[0x104]){++m[0x16];a=m[(unsigned short)(W(0x16)+y)];}else a=1;NZ(a);sp+=2;'
            elif o in (0x478d,0x4794):
                pointer=6 if o==0x478d else 8
                statement+=f'if(++m[{pointer}]){{NZ(m[{pointer}]);}}else{{++m[{pointer+1}];NZ(m[{pointer+1}]);}}sp+=2;'
            elif o==0x199f:
                statement+='a=0;q=m[0x43bc];m[0x43bb]=q>>5;m[0x43bc]=(unsigned char)(q<<3);c=0;NZ(m[0x43bb]);sp+=2;'
            elif actors:statement+=f'actor_code(0x{o:04x});if(transition_pending || actor_delay_pending || actor_gameover_pending || actor_reset_pending || actor_irq_stop || source_fault || actor_return!=0x{pc+size:04x})return;'
            else:statement+=f'room_code(0x{o:04x});if(transition_pending)return;'
        elif op=='jmp':statement=f'goto L{o:04x};'
        elif op in BRANCHES:
            target=(pc+size+(o if o<128 else o-256))&65535
            statement=f'if({BRANCHES[op]})goto L{target:04x};'
        else:raise AssertionError(f'Unsupported {op} at ${pc:04X}')
        if op in ('sta','stx','sty','inc','dec','asl','lsr','rol','ror') and mode!='acc' and not watched(mode,o):
            statement=re.sub(r'source_written\([^;]+\);','',statement)
        lines.append(statement)
        if op not in ('rts','jmp','brk'):lines.append(f'goto L{pc+size:04x};')
    lines.append('}\n')
    return re.sub(r'(0x[0-9a-fA-F]+)([+-])',r'\1 \2 ', '\n'.join(lines)), dict(instructions=len(code),entries=[f'${e:04X}' for e in sorted(entries)],
                                instruction_bytes_sha256=hashlib.sha256(b''.join(bytes([pc>>8,pc&255])+memory[pc:pc+code[pc][2]] for pc in sorted(code))).hexdigest())


def main():
    if not SOURCE.exists():
        report=json.loads((ASSETS/'manifest.json').read_text())
        for item in report['generated_outputs']+report['assets']:
            path=ROOT/item['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],f'Stale extracted file: {path}'
        print('Verified checked-in source extraction; local immutable C64 candidate is not installed')
        return
    m=SOURCE.read_bytes()
    expected=json.loads((ROOT/'reference/validation/candidate-rooms.json').read_text())['source_files'][0]['sha256']
    assert hashlib.sha256(m).hexdigest()==expected
    assert m[0x1159:0x1166]==bytes.fromhex('ad0401d003a90160e616b11660')
    assert m[0x478d:0x479b]==bytes.fromhex('e606d002e60760e608d002e60960')
    assert m[0x199f:0x19b8]==bytes.fromhex('a9008dbb43182ebc432ebb432ebc432ebb432ebc432ebb4360')
    for pose in (2,4,6,64,66):
        mask=m[0x1167+pose]+256*m[0x1239+pose]
        assert m[mask+64:mask+85]==bytes(21),'Fast constant masks require the verified empty third source column'
        assert all((byte&0x55)==((byte>>1)&0x55) for column in range(3) for byte in m[mask+column*32:mask+column*32+21]),'Constant-mask coverage path requires full two-bit source pairs'
    roots=[word(m,table+2*r)+1 for table in (0x4e9c,0x4ec4) for r in range(20)]
    roots += [0x0a9b,0x0bfa,0x0da4,0x0d0f,0x0db1,0x304b,0x17e2,0x336e,0x33ca,0x10c5,0x2fd6,0x2fef,0x30d4,0x40bc]
    code,details=translate(m,roots)
    ASSETS.mkdir(parents=True,exist_ok=True)
    ranges=[(0,0x200),(0x1000,0x1400),(0x2500,0x2584),(0x2c70,0x2d55),
            (0x2763,0x277f),(0x42ca,0x4ff0),(0x59a5,0x59b4),(0x5cbf,0x5da0),(0x6800,0x8180),(0x8340,0x8400),(0x9000,0xcb40),
            (0xcf79,0xcf7a),(0xcf99,0xcf9a)]
    header=['/* GENERATED candidate data: original source is immutable. */']
    for start,end in ranges:header.append(array(f'seed_{start:04x}',m[start:end]))
    header.append('static void seed_memory(void){unsigned short i;')
    for start,end in ranges:header.append(f'for(i=0;i<{end-start};i++)m[0x{start:04x}+i]=seed_{start:04x}[i];')
    header.append('}\n')
    (ROOT/'core/c64_room_data.h').write_text('\n'.join(header))
    (ROOT/'core/c64_room_programs.h').write_text(code)
    (ASSETS/'charsets.bin').write_bytes(m[0xa000:0xc000])
    cells=b''.join(bytes(decode(m,r)['cells']) for r in range(20))
    (ASSETS/'rooms.bin').write_bytes(cells)
    palette=['#000','#FFF','#833','#7CC','#84A','#6A4','#338','#CC7',
             '#852','#541','#B77','#444','#777','#AF9','#78C','#BBB']
    (ASSETS/'ocs-palette.txt').write_text('\n'.join(palette)+'\n')
    report=dict(status='extracted_and_statically_translated',date='2026-10-24',
        source=dict(path=SOURCE.relative_to(ROOT).as_posix(),sha256=expected),
        edition_verified=False,room_count=20,**details,
        boundaries={'$2F8E':'Native room transition request; no C64 stack reset/IRQ takeover',
                    '$17E2':'Native decoded string writer; source stack/register/final flag effects retained',
                    '$33BD':'Decoded init table dispatch','$3A6F':'Decoded loop table dispatch'},
        native_helpers=[dict(start='$17E2',end='$1817',sha256=hashlib.sha256(m[0x17e2:0x1818]).hexdigest()),
                        dict(start='$1A67',end='$1A89',sha256=hashlib.sha256(m[0x1a67:0x1a8a]).hexdigest()),
                        dict(start='$199F',end='$19B7',sha256=hashlib.sha256(m[0x199f:0x19b8]).hexdigest()),
                        dict(start='$478D',end='$479A',sha256=hashlib.sha256(m[0x478d:0x479b]).hexdigest()),
                        dict(start='$2CF1',end='$2D54',sha256=hashlib.sha256(m[0x2cf1:0x2d55]).hexdigest()),
                        dict(start='$104B',end='$10B4',sha256=hashlib.sha256(m[0x104b:0x10b5]).hexdigest()),
                        dict(start='$2509',end='$255D',sha256=hashlib.sha256(m[0x2509:0x255e]).hexdigest()),
                        dict(start='$404E',end='$407C',sha256=hashlib.sha256(m[0x404e:0x407d]).hexdigest())],
        scope='Room programs only; existing actor movement/combat remains a separate parity task',
        generated_outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (ROOT/'core/c64_room_data.h',ROOT/'core/c64_room_programs.h')],
        assets=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (ASSETS/'charsets.bin',ASSETS/'rooms.bin',ASSETS/'ocs-palette.txt')])
    (ASSETS/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Extracted20 rooms,4 charset banks; translated{details["instructions"]} source instructions to native C')


if __name__=='__main__':main()
