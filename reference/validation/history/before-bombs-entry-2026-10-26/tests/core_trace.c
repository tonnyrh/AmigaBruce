#include <stdio.h>
#include <stdlib.h>
#include "../core/game.h"

/* Replay the already sampled C64 direction at the portable logic seam.
 * Native joystick sampling latency is measured separately by the recorder. */
int main(void) {
    BlGame game;
    unsigned long direction,fire,late_fire;
    char line[32],*end;
    bl_reset(&game);
    printf("%d,%d,%u,%u,%u\n",bl_x(&game),bl_y(&game),(unsigned int)game.state,(unsigned int)game.prone,0u);
    while(fgets(line,sizeof(line),stdin)){
        unsigned char input=0;
        direction=strtoul(line,&end,10);fire=1;
        if(*end==','){fire=strtoul(end+1,&end,10);if(fire>1)return 2;}
        late_fire=fire;
        if(*end==','){late_fire=strtoul(end+1,&end,10);if(late_fire>1)return 2;}
        if(end==line || (*end!='\n' && *end!='\0') || direction>15)return 2;
        if(!(direction&1))input|=BL_UP;
        if(!(direction&2))input|=BL_DOWN;
        if(!(direction&4))input|=BL_LEFT;
        if(!(direction&8))input|=BL_RIGHT;
        if(!fire)input|=BL_FIRE;
        bl_step_phased(&game,input,late_fire?0:BL_FIRE);
        printf("%d,%d,%u,%u,%u\n",bl_x(&game),bl_y(&game),(unsigned int)game.state,(unsigned int)game.prone,
            game.attack==BL_FLYING_KICK&&game.attack_phase>=13?0u:(unsigned int)game.attack);
    }
    return ferror(stdin)?1:0;
}
