/* Same owner_poll and owner_dispatch as the A500 route. Only the field/beam
 * and the output sink are controlled. Execute $29C3 to its caller without
 * loading intermediate RAM images into the running engine. */
typedef unsigned long ULONG;
typedef unsigned short UWORD;
typedef unsigned char UBYTE;
extern long owner_read(UBYTE *,ULONG);
static ULONG test_field,owner_write_first,owner_write_last,sink_calls,check_error;
static UWORD test_beam;
static UBYTE owner_on,owner_busy,source_audio_active=1,game_field_active=1,game_field_loading;
static UBYTE source_registers[26],sink_packet[26],event[47],*expected_ram;
static UBYTE remaining,visits;
static ULONG field_clock(void){return test_field;}
static UWORD raster(void){return test_beam;}
static void source_audio_output(UBYTE music){
    UWORD i;(void)music;
    owner_write_first=owner_write_last=test_field;++sink_calls;
    for(i=0;i<26;i++)sink_packet[i]=source_registers[i];
}
#include "clock.h"
UBYTE *owner_memory(void){return m;}
static ULONG compare_cpu(const UBYTE *r){
    ULONG at;
    if(a!=r[0] || x!=r[1] || y!=r[2] || c!=r[3] || z!=r[4] ||
       n!=r[5] || v!=r[6] || d!=r[7] || sp!=r[8] || actor_i!=r[9])return 1;
    for(at=0;at<65536UL;at++)if(m[at]!=expected_ram[at])return 0x10000UL+at;
    return 0;
}
static void check_field(void){
    UWORD line,vector,i;
    ULONG ticks,prior;
    if(check_error || owner_checkpoint!=0x2c51)return;
    ++visits;
    if(!remaining || !(visits&1))return;
    if(!owner_read(event,sizeof(event)) || !owner_read(expected_ram,65536UL)){check_error=2;return;}
    line=(event[5]<<8)|event[6];vector=((UWORD)event[7]<<8)|event[8];
    test_field=((ULONG)event[1]<<24)|((ULONG)event[2]<<16)|((ULONG)event[3]<<8)|event[4];
    if(event[0]!=visits || owner_vector()!=vector || owner_line()!=line){check_error=3;return;}
    bl_c64_world_input(event[9],event[10]);prior=sink_calls;ticks=owner_bands+owner_games;
    test_beam=line-1;owner_poll();
    test_beam=line;actor_i=1;owner_poll();actor_i=0;
    if(ticks!=owner_bands+owner_games || prior!=sink_calls){check_error=4;return;}
    owner_poll();owner_poll(); /* Duplicate poll of the same clock sample. */
    if(owner_fault || owner_hw_duplicate || owner_hw_missing || owner_slot_errors ||
       owner_bands+owner_games!=ticks+1 || sink_calls!=prior+(vector==0x48c1)){check_error=5;return;}
    check_error=compare_cpu(event+11);
    for(i=0;i<26;i++)if(sink_packet[i]!=event[21+i])check_error=6;
    --remaining;
}
ULONG owner_combat(const UBYTE *header,UBYTE *expected){
    const UBYTE *r=header+1;
    UBYTE final_regs[10];
    UWORD i;
    expected_ram=expected;remaining=header[0];visits=0;
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    loaded=m[0x29];actor_world_enabled=actor_invincible=1;
    actor_preparing=actor_irq_stop=actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
    actor_stop_pc=actor_return=source_fault=0;transition_pending=index_ready=0;
    audio_gates=vic_valid=vic_collision_valid=0;vic_repeat.valid=0;
    owner_checkpoint=owner_keep=owner_records=0;owner_on=owner_busy=0;
    owner_fault=owner_games=owner_bands=owner_publications=owner_slot_errors=0;
    owner_hw_missing=owner_hw_duplicate=owner_crossed_publish=sink_calls=check_error=0;
    for(i=0;i<26;i++)sink_packet[i]=source_registers[i]=0;
    test_beam=0;test_field=0xfffffeUL;owner_arm();
    io_service=check_field;actor_code(0x29c3);io_service=0;
    if(check_error)return check_error;
    if(remaining || source_fault || actor_return!=0x1c26 || owner_games!=3 || sink_calls!=3)return 7;
    if(!owner_read(final_regs,10) || !owner_read(expected_ram,65536UL))return 8;
    return compare_cpu(final_regs);
}
