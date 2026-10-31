"""Isolated stationary costs, without AI/main-step or Amiga actor painting."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
HELPER=r'''
static unsigned long enemy_probe_clock(void){
    unsigned long hi,mid,lo,hi2,mid2;
    do{hi=*(volatile unsigned char*)0xbfda00;mid=*(volatile unsigned char*)0xbfd900;lo=*(volatile unsigned char*)0xbfd800;
       hi2=*(volatile unsigned char*)0xbfda00;mid2=*(volatile unsigned char*)0xbfd900;(void)*(volatile unsigned char*)0xbfd800;
    }while(hi!=hi2 || mid!=mid2);return (hi<<16)|(mid<<8)|lo;
}
unsigned long bl_enemy_probe_ram(void){return (unsigned long)m;}
void bl_enemy_stationary_probe(unsigned long *out){
    unsigned short layout,mask,op,i,j,index;unsigned char xx[3],pose[3],flags[3];unsigned long start;
    io_service=0;load_service=0;
    for(layout=0;layout<2;layout++)for(mask=0;mask<4;mask++){
        index=(unsigned short)((layout*4+mask)*5);out[index+3]=0;
        bl_c64_world_start(1,0);actor_delay_pending=actor_gameover_pending=actor_i=0;
        for(j=0;j<3;j++){
            flags[j]=(unsigned char)(j==0?1:j==1?(mask&1?0x81:0):(mask&2?0x41:0));m[0x95+j]=flags[j];
            xx[j]=(unsigned char)(layout?80+4*j:40+60*j);m[0x9e + j]=xx[j];m[0xa1+j]=150;m[0xa4+j]=0;
            pose[j]=(unsigned char)(j*70);m[0x4f48+j]=0;m[0x4f4b+j]=1;m[0x4f4e + j]=pose[j];m[0x4f51+j]=(unsigned char)(pose[j]+1);
        }
        m[0x277d]=m[0x277e]=0;m[0xd017]=m[0xd01b]=m[0xd01c]=m[0xd010]=0;m[0xd01d]=255;
        m[0xd015]=(unsigned char)(3|(mask&1?12:0)|(mask&2?16:0));execute(0x2584);execute(0x25e2);
        for(op=0;op<3;op++){
            for(i=0;i<8;i++){if(op==0)bl_c64_field();else execute(op==1?0x5212:0x2584);}
            start=enemy_probe_clock();
            for(i=0;i<64;i++){if(op==0)bl_c64_field();else execute(op==1?0x5212:0x2584);}
            out[index+op]=(enemy_probe_clock()-start)&0xffffffUL;
            if(source_fault)++out[index+3];
            for(j=0;j<3;j++)if(m[0x95+j]!=flags[j] || m[0x9e + j]!=xx[j] || m[0xa1+j]!=150 || m[0x4f4e + j]!=pose[j])++out[index+3];
        }
        out[index+4]=m[0xd015];
    }
    bl_c64_reset();
}
'''
def main():
    folder=BASE/'stationary';folder.mkdir(exist_ok=True)
    (folder/'c64_rooms.c').write_text((ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')+HELPER,encoding='utf-8')
    (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
    main=(BASE/'main.c').read_text(encoding='utf-8-sig')
    anchor='int main(void) {';assert main.count(anchor)==1
    main=main.replace(anchor,'extern void bl_enemy_stationary_probe(unsigned long *out);\nextern unsigned long bl_enemy_probe_ram(void);\nstatic ULONG enemy_stationary[40],enemy_stationary_mem;\n'+anchor)
    anchor='    intro_start=field_clock();';assert main.count(anchor)==1
    main=main.replace(anchor,'    bl_enemy_stationary_probe(enemy_stationary);enemy_stationary_mem=TypeOfMem((APTR)bl_enemy_probe_ram());\n'+anchor)
    anchor='        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);'
    assert main.count(anchor)==1
    block='''        append(&p,"\\nenemy_stationary_ram_type=");number(&p,enemy_stationary_mem);
        {UWORD q,j;for(q=0;q<8;q++){append(&p,"\\nenemy_stationary_");number(&p,q);append(&p,"=");
        for(j=0;j<5;j++){if(j)append(&p,",");number(&p,enemy_stationary[q*5+j]);}}}
'''
    (folder/'main.c').write_text(main.replace(anchor,block+anchor),encoding='utf-8')
    builder=(BASE/'build.ps1').read_text(encoding='utf-8-sig').replace("'reference/analysis/enemy-cost-2026-10-30/main.c'","'reference/analysis/enemy-cost-2026-10-30/stationary/main.c'")
    anchor='    & $compiler @sourceFlags -c $actualPath -o $obj'
    override="    if($source -eq 'core/c64_rooms.c'){$actualPath=Join-Path $taskRoot 'reference/analysis/enemy-cost-2026-10-30/stationary/c64_rooms.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'core')}\n"
    assert builder.count(anchor)==1;(BASE/'stationary-build.ps1').write_text(builder.replace(anchor,override+anchor),encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'stationary-scope.json').write_text(json.dumps(dict(production_changed=False,method='Injected static legal pose components from existing ripper; separated and overlapping layouts, no AI/main logic/Amiga actor painting during timed kernels. 8warm+64measured calls for field,contact,sprite expansion. Reset before normal measured main starts.',iterations=64,
        inputs=[item(ROOT/p) for p in ['core/c64_rooms.c','core/c64_actor_programs.h','amiga/main.c']],generated=[item(p) for p in list(folder.iterdir())+[BASE/'stationary-build.ps1']]),indent=2)+'\n')
    print('Generated stationary field/contact/sprite probe; game behavior untouched')
if __name__=='__main__':main()
