/* GENERATED actual6502 fixtures. Packed data, freed before runtime allocations. */
#include "../core/source_climb.h"
#include "../core/c64_sprites.h"
#if defined(__m68k__)
#include <exec/memory.h>
#include <proto/exec.h>
#define BL_CLIMB_ALLOC(n) AllocMem((n),MEMF_PUBLIC)
#define BL_CLIMB_FREE(p,n) FreeMem((p),(n))
#else
#include <stdlib.h>
#define BL_CLIMB_ALLOC(n) malloc(n)
#define BL_CLIMB_FREE(p,n) free(p)
#endif
#define BL_CLIMB_DISPATCH_CASES 100
#define BL_CLIMB_VECTOR_BYTES 2200
#define BL_CLIMB_RAW_BYTES 4504
#define BL_CLIMB_RAW_FNV 492911978UL
static const unsigned char source_climb_packed[]={131,80,120,1,6,0,134,1,0,77,120,0,3,5,0,129,12,0,0,19,7,4,0,0,0,11,11,10,0,134,3,1,30,0,1,7,17,0,0,0,44,21,134,6,1,3,12,0,5,3,0,0,0,92,6,8,0,0,0,44,21,132,1,1,0,12,0,0,26,5,131,3,1,6,0,0,132,32,134,13,1,0,4,0,2,3,0,0,0,44,32,140,4,0,0,9,1,30,4,1,1,0,0,4,0,0,132,35,131,3,1,28,0,0,220,43,130,2,13,0,0,220,43,129,13,0,0,220,43,129,3,0,0,220,34,131,1,0,1,0,0,220,5,134,29,3,1,1,0,1,0,0,220,38,0,1,184,96,129,0,0,1,184,43,0,0,44,31,0,1,184,145,0,0,220,37,0,1,184,7,0,0,44,28,131,3,0,3,0,1,184,10,129,3,0,1,184,255,0,1,184,171,0,3,112,30,133,29,0,0,15,12,4,0,129,26,10,0,134,3,1,3,0,1,8,0,0,22,16,0,1,184,255,10,0,0,1,184,103,131,7,0,7,0,1,184,10,129,7,0,3,112,60,132,3,0,0,9,0,1,206,5,129,22,10,0,138,6,1,0,12,0,12,12,0,0,3,0,0,22,12,0,1,184,255,10,0,0,1,184,56,136,4,148,176,0,3,6,0,10,4,0,0,0,24,8,0,0,134,8,0,0,16,6,134,29,0,3,0,1,6,4,0,0,0,32,22,133,7,0,3,3,0,0,0,32,27,132,13,0,3,1,0,0,32,28,132,3,0,3,7,0,0,32,28,129,5,0,0,64,31,129,63,0,0,128,31,129,4,0,0,64,31,132,12,0,3,0,0,0,64,31,0,0,32,29,129,28,0,0,64,63,0,0,128,64,129,252,0,0,128,127,0,1,0,128,129,60,0,1,0,254,133,56,242,0,3,6,0,3,160,28,0,3,192,255,0,3,192,225,129,4,7,0,133,252,0,0,6,25,6,0,0,0,33,5,129,253,0,1,184,34,130,2,25,0,0,32,29,0,0,17,9,130,3,25,3,0,129,3,0,1,168,31,132,5,0,3,3,0,0,80,28,129,5,0,0,17,7,129,3,0,0,80,7,3,0,0,0,16,7,0,0,168,30,129,5,0,0,168,31,0,0,88,190,136,6,52,233,1,0,0,24,6,0,1,199,6,132,4,6,0,60,3,0,138,3,0,6,3,60,0,1,0,1,0,0,0,24,6,133,2,7,6,0,12,3,0,133,3,0,6,3,12,0,0,24,15,0,0,48,255,0,0,48,64,128};
static const signed short source_climb_starts[][5]={{0,120,4,148,179},{120,120,4,172,179},{240,48,4,148,150}};
#define BL_CLIMB_FIXTURE_CASES 390
static unsigned short climb_fixture_data(const unsigned char *raw){
    unsigned short i,j,at;BlSourceActor a;BlGame g;BlFighter f;BlC64Sprite visual;
    for(i=0;i<BL_CLIMB_DISPATCH_CASES;i++){
        const unsigned char *v=raw+i*22;
        for(j=0;j<9;j++)((unsigned char*)&a)[j]=v[j];
        if(bl_source_climb_step(&a,v[9],v[10])!=v[21])return i+1;
        for(j=0;j<9;j++)if(((unsigned char*)&a)[j]!=v[11+j])return i+1;
        if(bl_source_climb_pose(&a,10)!=v[20])return i+1;
    }
    for(i=0;i<sizeof(source_climb_starts)/sizeof(source_climb_starts[0]);i++){
        const signed short *s=source_climb_starts[i];
        bl_c64_reset();bl_c64_load(s[2]);bl_reset(&g);g.room=(unsigned char)s[2];
        g.x=(BlCoord)(s[3]*16);g.y=(BlCoord)(s[4]*16);g.facing=0;
        for(j=0;j<s[1];j++){
            const unsigned char *v=raw+BL_CLIMB_VECTOR_BYTES+(s[0]+j)*8;at=(unsigned short)(BL_CLIMB_DISPATCH_CASES+s[0]+j+1);
            bl_step(&g,(unsigned char)v[0]);
            if(bl_x(&g)!=v[1]||bl_y(&g)!=v[2]||g.facing!=v[3]||g.climb_wait!=v[4]||
               g.wall.animation!=v[5]||g.wall.previous!=v[6]||bl_c64_object_pose(&g)!=v[7])return at;
        }
    }
    /* Net display/contact must not hide the existing prone/reaction states.
     * Pose66=source26/facing1; pose58=source19/counter9/facing1. */
    bl_reset(&f.body);f.active=1;f.sai=0;f.timer=0;
    f.body.state=BL_CLIMB;f.body.wall.pose=10;f.body.prone=1;f.body.facing=1;
    f.reaction=BL_REACTION_DOWN;f.stun=9;
    visual.initialized=0;
    if(bl_c64_object_pose(&f.body)!=66)return BL_CLIMB_FIXTURE_CASES-1;
    bl_c64_sprite_step(&visual,&f,2);
    if(visual.pose!=58)return BL_CLIMB_FIXTURE_CASES;
    return 0;
}
static unsigned short climb_fixture_run(void){
    unsigned char *raw=BL_CLIMB_ALLOC(BL_CLIMB_RAW_BYTES),*dest=raw,count;
    const unsigned char *source=source_climb_packed;
    unsigned short i,distance,result=65535;unsigned long hash=2166136261UL;
    if(!raw)return result;
    while((count=*source++)!=128){
        if(!count){distance=(unsigned short)((source[0]<<8)|source[1]);count=source[2];source+=3;
            if(!distance || distance>dest-raw || dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--){*dest=*(dest-distance);++dest;}
        }else if(count&128){count&=127;if(dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--)*dest++=*source++;
        }else{unsigned char value=*source++;if(dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--)*dest++=value;}
    }
    if(dest!=raw+BL_CLIMB_RAW_BYTES)goto done;
    for(i=22;i<BL_CLIMB_VECTOR_BYTES;i++)raw[i]^=raw[i-22];
    for(i=BL_CLIMB_VECTOR_BYTES+8;i<BL_CLIMB_RAW_BYTES;i++)raw[i]^=raw[i-8];
    for(i=0;i<BL_CLIMB_RAW_BYTES;i++)hash=((hash^raw[i])*16777619UL)&0xffffffffUL;
    if(hash!=BL_CLIMB_RAW_FNV)goto done;
    result=climb_fixture_data(raw);
done:
    BL_CLIMB_FREE(raw,BL_CLIMB_RAW_BYTES);return result;
}
#undef BL_CLIMB_ALLOC
#undef BL_CLIMB_FREE
