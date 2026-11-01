#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
extern ULONG check_decimal(const UBYTE *);
int main(void){
    ULONG report[3]={0,0,0},count=0;
    UBYTE block[31*16];
    BPTR in,out;
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    in=Open((CONST_STRPTR)"DH1:cases.bin",MODE_OLDFILE);
    if(in && Read(in,&count,4)==4 && count && count<10000){
        while(report[0]<count && !report[1]){
            ULONG i,n=count-report[0];if(n>16)n=16;
            if(Read(in,block,n*31)!=(LONG)(n*31))break;
            for(i=0;i<n && !report[1];i++){report[1]=check_decimal(block+i*31);++report[0];}
        }
        report[2]=(report[0]==count && !report[1] && Read(in,block,1)==0);
    }
    if(in)Close(in);
    out=Open((CONST_STRPTR)"DH1:proof.bin",MODE_NEWFILE);
    if(out){Write(out,report,sizeof(report));Close(out);}
    CloseLibrary((struct Library*)DOSBase);
    return report[2]?0:20;
}
