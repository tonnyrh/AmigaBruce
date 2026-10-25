#ifndef BRUCE_GATE_FIXTURE_H
#define BRUCE_GATE_FIXTURE_H
/* Injected setup at known contact coordinates, then ordinary progression.
 * This is a regression fixture, not proof of a natural complete playthrough. */
static void gate_position(BlCombat *w,int x,int y){
    BlGame *g=&w->player.body;
    g->x=(BlCoord)(x*16);g->y=(BlCoord)(y*16);
    g->previous_x=g->x;g->previous_y=g->y;
    g->state=BL_GROUND;g->attack=BL_ATTACK_NONE;g->prone=0;
}
static void gate_lamp(BlProgress *p,BlCombat *w,int room,int index){
    const BlLantern *lamp=&bl_room((unsigned char)room)->lanterns[index];
    if(p->room!=room)bl_progress_inspect_room(p,w,(unsigned char)room);
    gate_position(w,lamp->column*8-8,lamp->row*16+12);
}
static unsigned char gate_fixture_prepare(BlProgress *p,BlCombat *w,unsigned short step){
    if(step<6)gate_lamp(p,w,0,step);
    else if(step<12)gate_lamp(p,w,1,step-6);
    else if(step<22)gate_lamp(p,w,2,step-12);
    else if(step==22){gate_position(w,298,196);return BL_RIGHT;}
    else if(step==23){bl_progress_inspect_room(p,w,1);gate_position(w,120,196);}
    else if(step==60)gate_position(w,150,196); /* No DOWN: contact hatch. */
    else if(step==61)gate_lamp(p,w,5,2); /* $4D81; alone cannot open return. */
    else if(step>=100 && step<108)gate_lamp(p,w,6,step-100);
    else if(step==108){bl_progress_inspect_room(p,w,5);gate_position(w,272,50);}
    else if(step==109){bl_progress_inspect_room(p,w,2);gate_position(w,298,196);return BL_RIGHT;}
    else if(step==140){bl_progress_inspect_room(p,w,2);gate_position(w,260,196);}
    else if(step==180){
        bl_progress_inspect_room(p,w,0);gate_position(w,156,164);
        w->player.body.state=BL_CLIMB;
    }
    if(step>=180)return BL_UP;
    return 0;
}
static unsigned short gate_fixture_check(const BlProgress *p,const BlCombat *w,unsigned short step){
    if(step==21 && (p->openings&BL_OPEN_R02_HATCH) && !(p->openings&BL_OPEN_R03_EAST) && p->pickups==22)return 1;
    if(step==22 && p->room==2 && !p->transitions)return 2;
    if(step==60 && p->room==5 && bl_x(&w->player.body)==64 && bl_y(&w->player.body)==50)return 4;
    if(step==61 && !(p->openings&BL_OPEN_R06_RETURN))return 8;
    if(step==107 && !(p->openings&BL_OPEN_R02_HATCH) && (p->openings&BL_OPEN_R03_EAST) && (p->openings&BL_OPEN_R06_RETURN))return 16;
    if(step==108 && p->room==1 && bl_x(&w->player.body)==152 && bl_y(&w->player.body)==102)return 32;
    if(step==109 && p->room==3 && bl_x(&w->player.body)==8 && bl_y(&w->player.body)==196 && p->transitions==3)return 64;
    return 0;
}
#endif
