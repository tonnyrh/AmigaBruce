"""Try the original joystick slot at the existing game-field service boundary."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
def replace(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)

def sample_core(core):
    slot=(HERE.parent/"irq-input-2026-10-30/candidate/input_slot.h").read_text()
    slot=slot[slot.index("static unsigned char input_slot_pin"):]
    slot=slot.replace("input_slot_candidate","source_input_pins").replace("input_slot_pin","source_input_pin").replace("input_slot_convert","source_input_convert")
    bridge='''
static unsigned long (*source_read_controls)(long,long);
void bl_c64_set_control_reader(unsigned long (*reader)(long,long)){
    source_read_controls=reader;
}
/* $169D tests the active flag before reading the CIA. The reader supplies
 * the active player's Amiga stick in the low byte and the other stick in
 * the high byte. Reconstruct physical port order for the indexed reads. */
static void source_sample_controls(void){
    unsigned char bruce=actor_input,other=actor_yamo_input,first,second;
    if(!m[0x104]){a=0;NZ(a);return;}
    if(source_read_controls){
        unsigned long pads=source_read_controls(m[3],m[0x42ca]);
        bruce=(unsigned char)pads;other=(unsigned char)(pads>>8);
    }
    first=(unsigned char)(source_direction(bruce)|((bruce&BL_FIRE)?0:16));
    second=(unsigned char)(source_direction(other)|((other&BL_FIRE)?0:16));
    if(m[3])source_input_pins(first,second);else source_input_pins(second,first);
}
'''
    core=replace(core,"static void source_actor_field(void){",slot+bridge+"\nstatic void source_actor_field(void){")
    stmt="m[0x98]=source_direction(actor_input);m[0x9b]=(unsigned char)!(actor_input&BL_FIRE);"
    assert core.count(stmt)==2
    core=core.replace(stmt,"source_sample_controls();")
    return replace(core,"    if(m[0x42ca]){m[0x99]=source_direction(actor_yamo_input);m[0x9c]=(unsigned char)!(actor_yamo_input&BL_FIRE);}\n","")

def sample_main(main,diagnostic=False):
    marker="static UBYTE read_input(void){return read_port(1);}"
    reader='''
static ULONG read_game_controls(long player,long human_yamo){
    UBYTE active=read_port((UBYTE)(player?0:1));
    UBYTE other=human_yamo?read_port((UBYTE)(player?1:0)):0;
    return ((ULONG)other<<8)|active;
}'''
    if diagnostic:
        reader="\nstatic UBYTE diagnostic_pad;"+reader.replace("return ((ULONG)other<<8)|active;","(void)active;return ((ULONG)other<<8)|diagnostic_pad;")
        main=replace(main,"input=light_input(bl_c64_world_stat(0));light_restrict();","input=light_input(bl_c64_world_stat(0));diagnostic_pad=input;light_restrict();")
    main=replace(main,marker,marker+reader)
    # The deterministic fixture still supplies decoded inputs explicitly.
    return replace(main,"bl_c64_set_service(source_game_service);",
        "bl_c64_set_service(source_game_service);\n    if(!BL_AUTOTEST)bl_c64_set_control_reader(read_game_controls);")

def single_pad(core):
    stmt="    first=(unsigned char)(source_direction(bruce)|((bruce&BL_FIRE)?0:16));"
    return replace(core,stmt,'''    /* With one standard stick, $16B1 bypasses PHA and $16D2 exits.
     * Materialize the buffers and the registers/flags at $1703 directly. */
    if(m[3]<2 && !m[0x42ca] && m[0x1383+m[3]]){
        y=m[0x1383+m[3]];x=(unsigned char)(m[3]^1);
        m[0x98]=source_direction(bruce);m[0x9b]=(unsigned char)!(bruce&BL_FIRE);
        c=(m[0x98]>>3)&1;a=0;n=0;z=1;return;
    }
'''+stmt)
