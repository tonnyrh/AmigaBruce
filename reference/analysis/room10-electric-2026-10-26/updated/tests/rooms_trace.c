#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include "../core/rooms.h"
int main(void){
    BlProgress p;BlCombat w;unsigned int direction,fire;
    bl_progress_reset(&p);bl_combat_reset(&w);
    printf("0,%d,%d,0,0\n",bl_x(&w.player.body),bl_y(&w.player.body));
    while(scanf("%u,%u",&direction,&fire)==2){
        unsigned char input=(unsigned char)(((direction&4)?0:BL_LEFT)|((direction&8)?0:BL_RIGHT)|
            ((direction&1)?0:BL_UP)|((direction&2)?0:BL_DOWN)|(fire?0:BL_FIRE));
        bl_progress_step(&p,&w,input);
        printf("%u,%d,%d,%u,%u\n",p.room,bl_x(&w.player.body),bl_y(&w.player.body),p.collected[0],p.pickups);
    }
    return 0;
}
