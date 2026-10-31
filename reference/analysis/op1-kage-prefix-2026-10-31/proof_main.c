#include <exec/execbase.h>
#include <exec/memory.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
extern unsigned char *pilot_ram(void);
extern unsigned long pilot_witness(unsigned char *,unsigned char *,unsigned char *);
int main(void){
    BPTR input=0,output=0;
    UBYTE *first=0,*last=0,header[35];
    ULONG report[3]={0,0,0},cases=0;
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary*)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    input=Open((CONST_STRPTR)"DH1:cases.bin",MODE_OLDFILE);
    first=AllocMem(65536UL,MEMF_PUBLIC);last=AllocMem(65536UL,MEMF_PUBLIC);
    if(!input || !first || !last || Read(input,&cases,4)!=4 || cases>512)goto done;
    while(report[0]<cases){
        if(Read(input,header,35)!=35 || Read(input,pilot_ram(),65536)!=65536 ||
           Read(input,first,65536)!=65536 || Read(input,last,65536)!=65536)goto done;
        report[1]=pilot_witness(header,first,last);++report[0];
        if(report[1])goto done;
    }
    report[2]=1;
done:
    if(input)Close(input);
    output=Open((CONST_STRPTR)"DH1:proof.bin",MODE_NEWFILE);
    if(output){Write(output,report,sizeof(report));Close(output);}
    if(first)FreeMem(first,65536UL);if(last)FreeMem(last,65536UL);
    CloseLibrary((struct Library*)DOSBase);return report[2]?0:20;
}
