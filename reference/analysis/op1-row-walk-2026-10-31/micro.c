#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;

typedef struct { UWORD lane[3]; UBYTE a,x,y,count; } Batch;
typedef void (*Kernel)(UBYTE *,Batch *);
extern void bl_contact_rows8(UBYTE *,Batch *), parent_rows(UBYTE *,Batch *);
static UBYTE ram[65536];
static ULONG lines[9][4];

static ULONG clock_lines(void) {
    volatile UBYTE *hi=(UBYTE *)0xbfda00,*mid=(UBYTE *)0xbfd900,*lo=(UBYTE *)0xbfd800;
    ULONG h=*hi, m=*mid, l=*lo;
    return (h<<16)|(m<<8)|l;
}
static ULONG measure(Kernel kernel, UBYTE count) {
    Batch q={{0xa000,0xa020,0xa040},0,0,0,count};
    ULONG begin, end;
    UWORD i;
    Disable();
    begin=clock_lines();
    for(i=0;i<256;++i) {
        q.y=0;
        kernel(ram,&q);
    }
    end=clock_lines();
    Enable();
    return (end-begin)&0xffffffUL;
}
int main(void) {
    UWORD pattern,length,i,slot;
    static const UBYTE sizes[]={1,4,8};
    BPTR f;
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase) return 20;
    for(pattern=0;pattern<3;++pattern) {
        for(i=0;i<96;++i) {
            ram[0xa000+i]=(UBYTE)(17*i+61);
            ram[0xcae0+i]=pattern==0?0:pattern==1?(i%3==0?255:0):255;
        }
        for(length=0;length<3;++length) {
            slot=3*pattern+length;
            lines[slot][0]=measure(parent_rows,sizes[length]);
            lines[slot][1]=measure(bl_contact_rows8,sizes[length]);
            lines[slot][2]=measure(bl_contact_rows8,sizes[length]);
            lines[slot][3]=measure(parent_rows,sizes[length]);
        }
    }
    f=Open((CONST_STRPTR)"DH1:micro.bin",MODE_NEWFILE);
    if(f){Write(f,lines,sizeof(lines));Close(f);}
    CloseLibrary((struct Library *)DOSBase);
    return f?0:20;
}
