/* Normal scheduler, controlled debug room requests. No snapshots, fixture
 * comparison or DOS writes during the room-transition timing window. */
#include <dos/dosextens.h>
static const UBYTE op_route[]={1,0,2,3,4,5,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,0,0};
static UBYTE op_touring,op_index,op_pending;
static ULONG op_start,op_beg,op_end,op_events[sizeof(op_route)][5];
static ULONG op_low,op_mark,op_high,op_minsp,op_bytes;
static ULONG op_sp(void){ULONG value;__asm__ volatile("move.l %%sp,%0":"=d"(value));return value;}
static void op_stack_arm(void){
    struct Process *pr=(struct Process*)SysBase->ThisTask;
    struct CommandLineInterface *cli=(struct CommandLineInterface*)((ULONG)pr->pr_CLI<<2);
    ULONG high=(ULONG)pr->pr_ReturnAddr,size,sp_now=op_sp(),p;
    if(!cli || !high)return;
    size=cli->cli_DefaultStack*4UL;
    /* KS1.3 CLI RunCommand stack, not the separate small process stack.
     * Validate both size words and the live SP before writing its unused area. */
    if(size!=16384 || *(ULONG*)high!=size || *(ULONG*)(high-size)!=size+8 ||
       sp_now>=high || sp_now<high-size+1024)return;
    op_high=high;op_low=high-size+8;op_mark=(sp_now-128)&~3UL;
    for(p=op_low;p<op_mark;p+=4)*(volatile ULONG*)p=0xa7d35b19UL^p;
    op_bytes=size;op_minsp=sp_now;
}
static unsigned long step_for_tour(void){return (UWORD)(bl_c64_world_stat(0)-light_start_step);}
static void op_request(void){
    op_pending=1;op_start=line_clock();op_beg=op_end=0;
}
static void op_load(long loading){
    if(!op_touring || !op_pending)return;
    if(loading==1)op_beg=line_clock();
    else if(!loading)op_end=line_clock();
}
static void op_present(UWORD line,UWORD display){
    ULONG *row,now;
    if(!op_pending || !op_end || !display || bl_c64_read(0x29)!=op_route[op_index])return;
    now=line_clock();row=op_events[op_index++];
    row[0]=(op_beg-op_start)&0xffffffUL;row[1]=(op_end-op_beg)&0xffffffUL;
    row[2]=(now-op_end)&0xffffffUL;row[3]=(now-op_start)&0xffffffUL;row[4]=line;
    op_pending=0;
}
static void op_report(char **p){
    UWORD i,j;ULONG q=op_low;
    if(op_low)while(q<op_mark && *(volatile ULONG*)q==(0xa7d35b19UL^q))q+=4;
    append(p,"\nstack_size=");number(p,op_bytes);append(p,"\nstack_untouched=");number(p,q-op_low);
    append(p,"\nstack_used_to_lowest_write=");number(p,op_high-q);
    append(p,"\nstack_arm_sp_margin=");number(p,op_minsp-op_low);
    append(p,"\ntour_count=");number(p,op_index);
    for(i=0;i<op_index;i++){
        append(p,"\ntour_");number(p,i);append(p,"=");number(p,op_route[i]+1);
        for(j=0;j<5;j++){append(p,",");number(p,op_events[i][j]);}
    }
}
