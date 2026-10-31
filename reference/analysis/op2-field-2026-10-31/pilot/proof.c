#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
extern void bl_vic_decode_wide(const UBYTE *,UBYTE *,ULONG *,ULONG *);
static UBYTE source[68],raw[68];
static ULONG hi[23],lo[23];
static UWORD expand(UBYTE b){
    UWORD value=0,bit;
    for(bit=0;bit<8;++bit)value=(value<<2)|((b&(0x80>>bit))?3:0);
    return value;
}
int main(void){
    UWORD t,i,row,errors=0,cases=0;
    ULONG result[2];
    BPTR f;
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    for(t=0;t<512;++t){
        UWORD offset=1+(t>>8);
        for(i=0;i<68;++i){source[i]=(UBYTE)(i*29+t);raw[i]=0xa5;}
        for(i=0;i<23;++i)hi[i]=lo[i]=0xabcdef01UL;
        bl_vic_decode_wide(source+offset,raw+offset,hi+1,lo+1);
        for(i=0;i<68;++i){
            UBYTE want=(UBYTE)(i*29+t);
            if(source[i]!=want || raw[i]!=(i>=offset && i<offset+63?want:0xa5))++errors;
        }
        for(row=0;row<21;++row){
            const UBYTE *p=source+offset+3*row;
            if(hi[row+1]!=(((ULONG)expand(p[0])<<16)|expand(p[1])) ||
               lo[row+1]!=((ULONG)expand(p[2])<<16))++errors;
        }
        if(hi[0]!=0xabcdef01UL || hi[22]!=hi[0] || lo[0]!=hi[0] || lo[22]!=hi[0])++errors;
        ++cases;
    }
    result[0]=cases;result[1]=errors;
    f=Open((CONST_STRPTR)"DH1:wide-proof.bin",MODE_NEWFILE);
    if(f){Write(f,result,sizeof(result));Close(f);}
    CloseLibrary((struct Library *)DOSBase);
    return errors || !f ? 20 : 0;
}
