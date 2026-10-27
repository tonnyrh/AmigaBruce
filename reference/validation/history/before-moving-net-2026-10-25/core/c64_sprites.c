#include "c64_sprites.h"
#include "c64_sprite_pose_data.h"

unsigned char bl_source_pose(const BlSourcePose *p){
    unsigned char s=p->state,c=p->counter,f=p->facing,old=p->previous;
    if(p->locked)return old; /* $2780-$2783; $1C5F waits retain the lock. */
    if(s==14)return (unsigned char)(p->contact&8?8:68);
    if(s==26)return (unsigned char)(f==1?66:64);
    if(s==25)return 8;
    if(s==24)return (unsigned char)(old==68 || p->width || p->second_width?8:old);
    if(s==27)return (unsigned char)(f?(c>=4?56:58):(c>=4?60:62));
    if(s==19)return (unsigned char)(f?(c>=10?56:58):(c>=10?60:62));
    if(s==16)return 42;
    if(s==17)return (unsigned char)(f==1?6:4);
    if(s==18)return (unsigned char)(f==1?46:44);
    if(s==22)return (unsigned char)(f==1?(c>=11?52:54):(c>=11?48:50));
    if(s==15)return (unsigned char)(f==1?2:0);
    if(s==12)return (unsigned char)(c>=10?22:24);
    if(s==13)return (unsigned char)(c>=10?26:28);
    if(s==3 || ((s==20 || s==21) && f!=1)){
        if(!(p->contact&4))return (unsigned char)(old==14?16:14);
    }else if(s==4 || s==20 || s==21){
        if(!(p->contact&4))return (unsigned char)(old==18?20:18);
    }else if(s==5)return (unsigned char)(c>=15?8:c>=12?30:c>=2?32:c==1?30:8);
    else if(s==6)return (unsigned char)(c>=12 || c<3?34:36);
    else if(s==7)return (unsigned char)(c>=12 || c<3?38:40);
    else if(s==23 && p->aa)return old;
    else if(s==0){
        if(!(p->contact&4))return (unsigned char)(f==1?2:0);
        if(old==10 || old==12)return old;
    }
    return (unsigned char)(old==10?12:10); /* $2985-$2993 */
}

void bl_c64_sprite_step(BlC64Sprite *v,const BlFighter *f,int kind){
    const BlGame *g=&f->body;BlSourcePose p;
    if(!f->active){v->initialized=0;return;}
    if(!v->initialized){v->pose=(unsigned char)(kind==0?42:2);v->initialized=1;}
    p.previous=v->pose;p.facing=g->facing;
    p.width=c64_sprite_width[kind][v->pose];
    p.second_width=kind==1?0:c64_sprite_width[kind][v->pose+1];
    p.contact=g->wall.contact;
    if(g->state==BL_CLIMB)p.contact|=4;
    p.aa=p.locked=0;p.counter=0;p.state=0;
    /* This projection is explicitly not a port of $1C5B. Use source graphics
     * for the states already represented by the adapter; keep its counters
     * and waits labelled as provisional rather than inventing extra frames. */
    if(g->wall.state==24){v->pose=g->wall.pose;goto done;}
    if(kind==2 && g->state==BL_CLIMB && !g->attack && !g->prone &&
       !f->reaction && !f->sai){v->pose=g->wall.pose;goto done;}
    if(f->reaction==BL_REACTION_DEAD){p.state=25;p.counter=f->stun;}
    else if(f->reaction==BL_REACTION_DOWN){p.state=19;p.counter=f->stun;}
    else if(f->reaction==BL_REACTION_HURT)p.state=18;
    else if(f->reaction==BL_REACTION_FALL)p.state=14;
    else if(f->sai){p.state=22;p.counter=f->timer;}
    else if(g->attack==BL_FLYING_KICK){p.state=(unsigned char)(g->facing?13:12);p.counter=(unsigned char)(g->attack_phase<12?12-g->attack_phase:0);}
    else if(g->attack==BL_PUNCH)p.state=17;
    else if(g->prone)p.state=26;
    else if(g->state==BL_AIR){
        p.state=(unsigned char)(g->jump_phase==255?14:!g->jump_direction?5:g->jump_direction<0?6:7);
        p.counter=(unsigned char)(g->jump_phase<16?16-g->jump_phase:0);
    }else if(kind==0 && f->ai==BL_AI_WAIT && f->timer>=16)p.state=16;
    else if(g->state==BL_CLIMB){
        p.state=(unsigned char)(g->x!=v->x?(g->facing?4:3):g->y!=v->y?(g->climb_direction<0?1:2):0);
        /* Original waits leave $4FDB set. The adapter exposes a different
         * counter, so unchanged climbing travel retains its current pose. */
        p.locked=(unsigned char)(g->x==v->x && g->y==v->y);
    }else if(g->x!=v->x && g->walk_steps)p.state=(unsigned char)(g->facing?4:3);
    v->pose=bl_source_pose(&p);
done:
    v->x=g->x;v->y=g->y;
}
