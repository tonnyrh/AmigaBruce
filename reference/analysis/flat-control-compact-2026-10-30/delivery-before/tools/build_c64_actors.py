"""Statically translate the complete reachable candidate actor/combat chain.

Original RAM bytes are never edited. Hardware input, collision latches and
waits are explicit boundaries. Gameplay is statically translated native code.
"""
from pathlib import Path
import hashlib,json,sys
from build_c64_rooms import translate,array,word
from build_fighter_dma import pack,unpack
ROOT=Path(__file__).resolve().parents[1]
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(b).hexdigest()==SHA
    roots=[0x0743,0x0763,0x09bc,0x0a9b,0x0f72,0x0b30,0x1bc2,0x1bee,0x179e,0x1c5b,0x2780,0x29c3,
        0x2d55,0x2d7c,0x2e39,0x2584,0x5212,0x196c,0x1981,0x1818,0x182a,0x1886,0x2f9a,
        0x15b8,0x1703,0x3175,0x331c,0x0f71,0x52a4]
    roots += [word(b,t+2*r)+1 for t in (0x4e9c,0x4ec4) for r in range(20)]
    code,meta=translate(b,roots,actors=True)
    out=ROOT/'core/c64_actor_programs.h';out.write_text(code,encoding='utf-8')
    packed=pack(b);assert bytes(unpack(packed))==b and len(packed)<65536
    data=[array('actor_seed_packed',packed),
        f'#define BL_C64_COLD_KAGE {b[0x130b]}',f'#define BL_C64_COLD_YAMO {b[0x1347]}',
        'static void seed_actor_memory(void){unsigned short at=0,distance;unsigned long dest=0;unsigned char count,value;',
        'while((count=actor_seed_packed[at++])!=128){if(!count){distance=(unsigned short)(((unsigned short)actor_seed_packed[at]<<8)|actor_seed_packed[at+1]);at+=2;count=actor_seed_packed[at++];',
        'while(count--){m[dest]=m[dest-distance];++dest;}}else if(count&128){count&=127;while(count--)m[dest++]=actor_seed_packed[at++];}',
        'else{value=actor_seed_packed[at++];while(count--)m[dest++]=value;}}}']
    seed=ROOT/'core/c64_actor_data.h';seed.write_text('\n'.join(data)+'\n',encoding='utf-8')
    folder=ROOT/'reference/analysis/actor-chain-2026-10-26';folder.mkdir(parents=True,exist_ok=True)
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    decoder=Disassembler(MPU(memory=list(b)))
    import re
    listing=[]
    for pc in sorted(set(int(x,16) for x in re.findall(r'^L([0-9a-f]{4}):',code,re.M))):
        size,text=decoder.instruction_at(pc)
        listing.append(f'{pc:04X}  {b[pc:pc+size].hex(" "):8} {text}')
    disassembly=folder/'source-disassembly.txt';disassembly.write_text('\n'.join(listing)+'\n')
    report=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,production_enabled=True,
        roots=[f'${a:04X}' for a in roots],**meta,packed_seed_bytes=len(packed),
        boundaries={'$050F/$0584':'Return to native main menu',
            '$0F47':'Player-announcement IRQ field wait; CPU delay loop phase remains uncertified',
            '$169D/$1703':'CIA controller sampling replaced by decoded Amiga inputs',
            '$179D':'End of game-facing IRQ fragment',
            '$1968/$197D':'254/64-field Game Over waits',
            '$1BC2':'End of startup when explicitly preparing a room; otherwise actual main entry',
            '$1C32':'Three-field wait at end of complete main iteration',
            '$D01E':'Field-sampled source VIC sprite opaque-pixel latch, cleared on read; not raster-exact'},
        decoded_helpers={'$2E39/$2E6E':'Native actor/object cell pass; original cell handlers and non-local room/lifetime boundaries',
            '$55AB':'Fixed class-buffer clear with source final flags and frame',
            '$31D5/$32EE':'Native 24-bit score to packed BCD with source scratch, saved status byte and final registers',
            '$2E89':'Ordered native object dispatch; exact final comparison and shift flags at original handler boundaries',
            '$5212':'Binary native contact driver; original per-actor service, JSR frames and non-local row completion',
            '$26A0':'Source sprite bitmap copy with scratch/flags/stack',
            '$52AD':'Source contact-mask alignment with scratch/flags/stack',
            '$530A':'Binary contact address preparation; ordered reads, exact internal JSR bytes and final arithmetic flags',
            '$537E':'Local virtual registers, synchronized source services/helpers, exact JSR bytes and original non-local return',
            '$5431':'Source class reduction, exact OR operands, stack bytes and final flags',
            '$55E6/$5658/$56CA':'Source seven-pair class exchanges; final A/X/N/Z and restored SP'},
        generated=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (out,seed,disassembly)])
    (folder/'translation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Translated{meta["instructions"]} actor/world instructions;{len(packed)} packed seed bytes; native source world enabled')
if __name__=='__main__':main()
