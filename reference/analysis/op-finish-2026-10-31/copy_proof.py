"""Exercise the shipped 68000 sprite copy on its fast and ordered paths."""
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-pipeline/copy-proof"

def main():
    WORK.mkdir(exist_ok=True)
    core=(ROOT/"core/c64_rooms.c").read_text()
    body=core[core.index("static void source_sprite_copy_c(void){"):core.index("typedef struct {\n    unsigned short dest,first,left,right;")]
    code='''#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
static UBYTE before[65536] __attribute__((aligned(4))),actual[65536] __attribute__((aligned(4)));
static UBYTE *m,a,x,y,c,z,n,sp;
static UWORD source_fault;
static UWORD W(UWORD p){return m[p]|((UWORD)m[p+1]<<8);}
typedef struct {UWORD dest,first,left,right;UBYTE xx,yy,wide,carry;} Copy;
extern void bl_sprite_copy(UBYTE *,Copy *);
'''+body+'''
int main(void){
    static const UBYTE heights[]={0,1,2,7,12,20,21,31};
    static const UWORD sources[]={0x6000,0x2770,0xff00,0x3000,0x7f00,0xa000};
    ULONG report[3]={0,0,0},i;UWORD h,w,p;Copy q;BPTR out;
    SysBase=*(struct ExecBase **)4;DOSBase=(struct DosLibrary*)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    for(h=0;h<8;h++)for(w=0;w<2;w++)for(p=0;p<6;p++){
        for(i=0;i<65536;i++)before[i]=actual[i]=(UBYTE)(i*13+report[0]*17);
        q.dest=p==3?0xa001:p==4?0xd100:0xa000;q.first=q.left=q.right=sources[p];
        q.xx=heights[h];q.yy=heights[h]*3;q.wide=w;q.carry=(p&1);
        m=before;m[0x0e]=(UBYTE)q.dest;m[0x0f]=(UBYTE)(q.dest>>8);
        m[0x26ab]=m[0x26e4]=m[0x26ee]=(UBYTE)q.first;
        m[0x26ac]=m[0x26e5]=m[0x26ef]=(UBYTE)(q.first>>8);m[0xe0]=q.xx;
        for(i=0;i<65536;i+=4)*(ULONG*)(actual+i)=*(ULONG*)(before+i);
        a=37;x=0;y=q.yy;c=q.carry;z=!w;sp=250;source_fault=0;
        source_sprite_copy_c();bl_sprite_copy(actual,&q);
        for(i=0;i<65536;i+=4)if(*(ULONG*)(actual+i)!=*(ULONG*)(before+i)){++report[1];break;}
        if(q.xx!=x || q.yy!=y || q.carry!=c || source_fault)++report[1];
        ++report[0];
    }
    report[2]=(report[0]==96 && !report[1]);
    out=Open((CONST_STRPTR)"DH1:proof.bin",MODE_NEWFILE);
    if(out){Write(out,report,12);Close(out);}
    CloseLibrary((struct Library*)DOSBase);return report[2]?0:20;
}
'''
    (WORK/"main.c").write_text(code)
    tools=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    cc=tools/"opt/bin/m68k-amiga-elf-gcc.exe"
    flags="-m68000 -O2 -nostdlib -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns -fomit-frame-pointer -ffunction-sections -fdata-sections".split()
    objects=[]
    for src in (WORK/"main.c",ROOT/"amiga/sprite_copy.s",ROOT/"amiga/start.s",ROOT/"amiga/runtime.c"):
        out=WORK/(src.stem+".o");subprocess.run([cc,*flags,"-c",src,"-o",out],check=True);objects.append(out)
    elf=WORK/"bruce_amiga.elf"
    subprocess.run([cc,*flags,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([tools/"elf2hunk.exe",elf,elf.with_suffix(".exe")],check=True)
    (WORK/"cases.bin").write_bytes((96).to_bytes(4,"big"))

if __name__=="__main__":main()
