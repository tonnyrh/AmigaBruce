"""Native slot witness using the game's own Amiga joystick register reader."""
import json
from build_field import ROOT,WORK,compile_program
import sys
engine=WORK/(sys.argv[1] if len(sys.argv)>1 else "pad")
stage=WORK/"ports";stage.mkdir(exist_ok=True)
core=(engine/"c64_rooms.c").read_text()
core+='''
long slot_pad(long flags,long old_direction,long state){
    actor_input=actor_yamo_input=0;sp=238;d=0;
    m[0x104]=1;m[3]=0;m[0x42ca]=0;m[0x1383]=flags;m[0xbf]=state;
    m[0x98]=(unsigned char)old_direction;
    source_sample_controls();return m[0x98];
}
'''
base=(ROOT/"amiga/main.c").read_text()
port=base[base.index("static UBYTE read_port(UBYTE port) {"):base.index("static UBYTE read_input(")]
reader=base[base.index("static ULONG read_game_controls("):]
reader=reader[:reader.index("\n}")+2]
cases=json.loads((WORK/"vice-slots.json").read_text())["cases"]
sequence=[(row["direction"],row["state"]) for pose in ("ground","air") for when in ("before","after") for row in cases[pose][when]]
main='''#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <hardware/custom.h>
#include "game.h"
#include "c64_rooms.h"
struct ExecBase *SysBase;struct DosLibrary *DOSBase;
static volatile struct Custom *const hw=(volatile struct Custom *)0xdff000;
extern long slot_pad(long,long,long);
'''+port+reader+'''
static const UBYTE sequence[][2]={'''+",".join("{%d,%d}"%row for row in sequence)+'''};
int main(void){
    ULONG result[3]={0,0,0},i,wait;BPTR file;
    char signal[]="DH1:go00";ULONG old=15;
    SysBase=*(struct ExecBase **)4;DOSBase=(struct DosLibrary*)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    bl_c64_set_control_reader(read_game_controls);
    for(i=0;i<sizeof(sequence)/sizeof(sequence[0]);i++){
        signal[6]=(char)('0'+i/10);signal[7]=(char)('0'+i%10);
        file=Open((CONST_STRPTR)"DH1:request.bin",MODE_NEWFILE);
        if(!file)goto end;Write(file,&i,4);Close(file);
        for(wait=0;wait<1500;wait++){
            file=Open((CONST_STRPTR)signal,MODE_OLDFILE);if(file){Close(file);break;}
            Delay(1);
        }
        if(!file)goto end;
        if(!(i%3))old=15;
        old=slot_pad(1,old,sequence[i][1]);++result[0];
        if(old!=sequence[i][0]){result[1]=(i+1)*256+old;goto end;}
    }
    result[2]=1;
end:
    file=Open((CONST_STRPTR)"DH1:ports.bin",MODE_NEWFILE);
    if(file){Write(file,result,sizeof(result));Close(file);}
    CloseLibrary((struct Library*)DOSBase);return result[2]?0:20;
}
'''
(stage/"main.c").write_text(main);(stage/"c64_rooms.c").write_text(core)
(stage/"c64_actor_programs.h").write_bytes((engine/"c64_actor_programs.h").read_bytes())
compile_program(stage,ROOT/".tmp/op-pipeline/candidate")
