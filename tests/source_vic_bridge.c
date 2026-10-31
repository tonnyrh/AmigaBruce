/* Host-only access to the field-sampled VIC seam. No production test API. */
#include "../core/c64_rooms.c"
void bl_vic_seed(const unsigned char *ram){
    unsigned long at;for(at=0;at<65536;at++)m[at]=ram[at];
    actor_world_enabled=1;vic_valid=vic_collision_valid=0;
}
void bl_vic_write(long at,long value){m[(unsigned short)at]=(unsigned char)value;}
unsigned char bl_vic_sample(void){source_vic_latch();return m[0xd01e];}
unsigned char bl_vic_take(void){return source_vic_read();}

/* Isolate one pixel on each side. Dense sprites can hide a one-bit error at
 * the 15/16 and 31/32 seams because an unrelated pair also sets the latch. */
unsigned long bl_vic_pair_basis(void){
    unsigned short offset,left,right;
    unsigned long failures=0;
    for(offset=0;offset<48;offset++){
        for(left=0;left<48;left++){
            vic_high[0][0]=left<32?0x80000000UL>>left:0;
            vic_low[0][0]=left>=32?0x80000000UL>>(left-32):0;
            for(right=0;right<48;right++){
                vic_high[1][20]=right<32?0x80000000UL>>right:0;
                vic_low[1][20]=right>=32?0x80000000UL>>(right-32):0;
                failures+=source_vic_flat_pair(0,1,0,20,1,offset)!=(left==right+offset);
            }
        }
    }
    return failures;
}
