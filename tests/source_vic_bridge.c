/* Host-only access to the field-sampled VIC seam. No production test API. */
#include "../core/c64_rooms.c"
void bl_vic_seed(const unsigned char *ram){
    unsigned long at;for(at=0;at<65536;at++)m[at]=ram[at];
    actor_world_enabled=1;vic_valid=vic_collision_valid=0;
}
void bl_vic_write(long at,long value){m[(unsigned short)at]=(unsigned char)value;}
unsigned char bl_vic_sample(void){source_vic_latch();return m[0xd01e];}
unsigned char bl_vic_take(void){return source_vic_read();}
