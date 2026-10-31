/* Gameplay-only. At a mapped checkpoint, present the saved caller context
 * and physical CIA pins to the source-selected IRQ. IRQ-local engine
 * continuations must not replace the suspended main program's continuation. */
static unsigned short owner_checkpoint;
static void owner_at(unsigned short pc){
    unsigned short saved=owner_checkpoint;owner_checkpoint=pc;
    if(io_service)io_service();
    owner_checkpoint=saved;
}
unsigned long owner_pc(void){
    if(!actor_world_enabled || actor_i || actor_delay_pending || actor_gameover_pending || source_fault)return 0;
    if(owner_checkpoint)return owner_checkpoint;
    return actor_stop_pc==0x1c32 || actor_stop_pc==0x1bc2?actor_stop_pc:0;
}
