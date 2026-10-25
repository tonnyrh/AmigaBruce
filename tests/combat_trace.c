#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include "../core/combat.h"
static void emit(const BlCombat *w){
    int i;
    for(i=-1;i<BL_ENEMIES;i++){
        const BlFighter *f=i<0?&w->player:&w->enemy[i];
        printf("%u,%d,%d,%d%s",(unsigned int)f->active,bl_x(&f->body),bl_y(&f->body),(int)f->health,i==BL_NINJA?"\n":",");
    }
}
int main(void){
    BlCombat w;unsigned int direction,fire;char line[64];
    bl_combat_reset(&w);emit(&w);
    while(fgets(line,sizeof(line),stdin)){
        unsigned char input=0;
        if(sscanf(line,"%u,%u",&direction,&fire)!=2||direction>15||fire>1)return 2;
        if(!(direction&1))input|=BL_UP;if(!(direction&2))input|=BL_DOWN;
        if(!(direction&4))input|=BL_LEFT;if(!(direction&8))input|=BL_RIGHT;
        if(!fire)input|=BL_FIRE;
        bl_combat_step(&w,input);emit(&w);
    }
    return ferror(stdin)?1:0;
}
