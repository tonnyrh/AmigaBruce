/* AmigaDOS fixture reader. Only one expected RAM image is resident. */
#include <exec/execbase.h>
#include <exec/memory.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
extern unsigned char *owner_memory(void);
extern ULONG owner_combat(const UBYTE *, UBYTE *);
static BPTR input;
long owner_read(UBYTE *out, ULONG n){return Read(input,out,n)==(LONG)n;}
int main(void){
    BPTR out;
    ULONG cases=0,report[3]={0,0,0};
    UBYTE *expected,header[11];
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    input=Open((CONST_STRPTR)"DH1:cases.bin",MODE_OLDFILE);
    expected=AllocMem(65536UL,MEMF_PUBLIC);
    if(input && expected && owner_read((UBYTE *)&cases,4) && cases==2){
        while(report[0]<cases){
            if(!owner_read(header,sizeof(header)) || !owner_read(owner_memory(),65536UL))break;
            report[1]=owner_combat(header,expected);++report[0];
            if(report[1])break;
        }
        report[2]=(report[0]==cases && !report[1] && Read(input,header,1)==0);
    }
    if(input)Close(input);
    out=Open((CONST_STRPTR)"DH1:proof.bin",MODE_NEWFILE);
    if(out){Write(out,report,sizeof(report));Close(out);}
    if(expected)FreeMem(expected,65536UL);
    CloseLibrary((struct Library*)DOSBase);
    return report[2]?0:20;
}
