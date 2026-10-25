#include <exec/execbase.h>
#include <exec/memory.h>
#include <graphics/gfxbase.h>
#include <graphics/view.h>
#include <proto/exec.h>
#include <proto/graphics.h>
#include <proto/dos.h>
#include <hardware/custom.h>
#include <hardware/dmabits.h>
#include "../core/game.h"
#include "../core/presentation.h"
#include "../core/combat.h"
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "fighter_art_data.h"
#include "fighter_dma_data.h"

struct ExecBase *SysBase;
struct GfxBase *GfxBase;
struct DosLibrary *DOSBase;
static volatile struct Custom *hw=(volatile struct Custom *)0xdff000;
#include "intro_audio.h"
#define WIDTH 320
#define HEIGHT 256
#define PLANES 4
#define PLANE_BYTES (40*HEIGHT)
#define BITMAP_BYTES (PLANE_BYTES*PLANES)
#define COPPER_BYTES 1024
#define TILE_DMA_BYTES 106496UL
#define ROW_BYTES 160
#define FIGHTER_DMA_BYTES (BL_FIGHTER_CACHE_BYTES+BL_FIGHTER_CLIP_BYTES)
#define SCENE_TOP 32
#ifndef BL_AUTOTEST
#define BL_AUTOTEST 0
#endif
#ifndef BL_C64_PROFILE
#define BL_C64_PROFILE 0
#endif
#ifndef BL_TEST_FRAMES
#define BL_TEST_FRAMES 360
#endif
#ifndef BL_TEST_START_ROOM
#define BL_TEST_START_ROOM 0
#endif
#ifndef BL_COLLECT_FRAME_DROPS
#define BL_COLLECT_FRAME_DROPS 0
#endif
#ifndef BL_COMBAT_WARMUP
#define BL_COMBAT_WARMUP 0
#endif
#ifndef BL_COMBAT_TEST
#define BL_COMBAT_TEST 0
#endif
#ifndef BL_ROOM_TEST
#define BL_ROOM_TEST 0
#endif
#ifndef BL_ENEMY_EDGE_TEST
#define BL_ENEMY_EDGE_TEST 0
#endif
#ifndef BL_ROOM_TOUR
#define BL_ROOM_TOUR 0
#endif
#ifndef BL_GATE_TEST
#define BL_GATE_TEST 0
#endif
#define BL_CAPTURE_FRAME (BL_GATE_TEST?450:(BL_ROOM_TOUR?6950:(BL_ENEMY_EDGE_TEST?360:(BL_ROOM_TEST?630:(BL_COMBAT_TEST?900:120)))))
#include "source_audio.h"
#if BL_ROOM_TEST
#include "../tests/room_fixture.h"
#endif
#if BL_GATE_TEST
#include "../tests/gate_fixture.h"
#endif
static UBYTE *background, *buffers[2],*room_backgrounds[20],*room_slots[2];
static UBYTE slot_room[2]={0,1};
static UBYTE *capture,*tone,*fighter_dma,*tile_dma;
static UWORD native_cell_offset[1000];
static ULONG source_render_checks,source_render_mismatches;
static void wait_blitter(void);
static void paint_source_tile(const BlC64Paint *request);
static void paint_source_block(const BlC64Block *request);
static UWORD *copper[2];
/* CPU-side test-target stamps; fixed eight-pixel knockback keeps byte alignment. */
static UBYTE target_stamp[6][4][26][2],target_mask[6][26][2];
/* Unshifted CPU poses:74880 bytes for3 actors/2 faces/16 phases. The OCS
 * barrel shifters also handle clipped edges through a second Chip buffer. */
static ULONG source_words[2][25];
static UBYTE source_rows[2][25];
static UWORD painted_lanterns[20];
static UBYTE painted_openings[20];
static UWORD actor_pose_seen[3];
typedef struct { short left,top,right,bottom; } BlDirty;
static void restore_actor(UBYTE *b,const BlDirty *dirty);
static BlDirty actor_dirty[2][5];
/* Deterministic12-bit OCS representation of the16 C64 color indices. */
static const UWORD palette[16]={0x000,0xfff,0x833,0x7cc,0x84a,0x6a4,0x338,0xcc7,
    0x852,0x541,0xb77,0x444,0x777,0xaf9,0x78c,0xbbb};
/* Existing AI actors, recolored to the source room palette at load time. */
static ULONG fighter_cache_hash=2166136261UL,fighter_cache_bytes;
static ULONG fighter_fnv(ULONG hash,UBYTE value){
    ULONG input=hash^value,low=(UWORD)input,high=(UWORD)(input>>16);
    /* Exact FNV prime$01000193 using two native68000 word multiplies. */
    __asm__ volatile("mulu.w #403,%0" : "+d"(low) : : "cc");
    __asm__ volatile("mulu.w #403,%0" : "+d"(high) : : "cc");
    high+=(UWORD)(input<<8)+(low>>16);
    return (high<<16)|(UWORD)low;
}

static void copy(UBYTE *d,const UBYTE *s,ULONG n) {while(n--) *d++=*s++;}
static void pixel(UBYTE *b,int x,int y,UBYTE color) {
    UWORD p; ULONG offset; UBYTE mask;
    if(x<0||x>=WIDTH||y<0||y>=HEIGHT)return;
    offset=(ULONG)y*ROW_BYTES+(x>>3);mask=0x80>>(x&7);
    b+=offset;
    for(p=0;p<PLANES;p++) {
        if(color&(1<<p))*b|=mask;else *b&=(UBYTE)~mask;
        b+=40;
    }
}
static void rect(UBYTE *b,int x,int y,int w,int h,UBYTE color) {
    int end=x+w,bottom=y+h,first,last,row,plane,byte;
    UBYTE left_mask,right_mask;
    if(x<0)x=0;
    if(y<0)y=0;
    if(end>WIDTH)end=WIDTH;
    if(bottom>HEIGHT)bottom=HEIGHT;
    if(x>=end||y>=bottom)return;
    first=x>>3;last=(end-1)>>3;
    left_mask=(UBYTE)(0xffU>>(x&7));right_mask=(UBYTE)(0xffU<<(7-((end-1)&7)));
    for(plane=0;plane<PLANES;plane++) {
        UBYTE *dst=b+(ULONG)y*ROW_BYTES;
        for(row=y;row<bottom;row++) {
            for(byte=first;byte<=last;byte++) {
                UBYTE mask=0xff;
                if(byte==first)mask&=left_mask;
                if(byte==last)mask&=right_mask;
                if(color&(1<<plane))dst[byte]|=mask;else dst[byte]&=(UBYTE)~mask;
            }
            dst+=ROW_BYTES;
        }
        b+=40;
    }
}

/* Compact authored 5x7 alphabet for the prototype status and controls. */
static const UBYTE glyphs[26][7]={
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},
 {30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
 {14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{14,4,4,4,4,4,14},
 {7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
 {17,27,21,21,17,17,17},{17,25,25,21,19,19,17},{14,17,17,17,17,17,14},
 {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
 {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
 {17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
 {17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
static const UBYTE digits[10][7]={
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
 {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
 {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},
 {14,17,17,15,1,1,14}};
static void text(UBYTE *b,int x,int y,const char *s,UBYTE c) {
    while(*s) {
        const UBYTE *glyph=*s>='A'&&*s<='Z'?glyphs[*s-'A']:
            *s>='0'&&*s<='9'?digits[*s-'0']:0;
        if(glyph){int row,col;
        for(row=0;row<7;row++)for(col=0;col<5;col++)
            if(glyph[row]&(16>>col))pixel(b,x+col,y+row,c);
    }x+=6;s++;}
}

/* Temporary title until the user's loading illustration is attached. */
static void draw_loading(UBYTE *b){
    const char *title="BRUCE";int n,row,col;
    for(n=0;n<5;n++)for(row=0;row<7;row++)for(col=0;col<5;col++)
        if(glyphs[title[n]-'A'][row]&(16>>col))
            rect(b,73+n*36+col*6,88+row*6,6,6,13);
    text(b,139,166,"LOADING",5);
}


static void draw_room(const BlGame *game,const BlProgress *progress){
    ULONG i;char title[]="ROOM 01";wait_blitter();
    for(i=0;i<BITMAP_BYTES;i++)background[i]=0;
    bl_c64_paint_room(background,SCENE_TOP);wait_blitter();
    if(BL_AUTOTEST){source_render_mismatches+=(ULONG)bl_c64_check_interleaved(background,SCENE_TOP);++source_render_checks;}
    bl_c64_clear_dirty();
    (void)bl_c64_build_animation_cache(tile_dma,TILE_DMA_BYTES);
    text(background,8,7,"BRUCE",7);
    title[5]=(char)('0'+(game->room+1)/10);title[6]=(char)('0'+(game->room+1)%10);
    text(background,264,7,title,1);
    text(background,16,19,"KAGE",2);text(background,128,19,"YAMO",5);text(background,240,19,"BRUCE",7);
    text(background,8,238,"F1 F2 ROOMS  JOYSTICK MOVE",1);
    text(background,8,248,"ESC EXIT  C64 SOURCE ROOMS",12);
    if(progress){painted_lanterns[progress->room]=progress->collected[progress->room];painted_openings[progress->room]=0;}
}
static void load_room_background(const BlGame *game,const BlProgress *progress,int force){
    /* Source full loader $09F3->$255E silences SID before reinitializing.
     * Do not hold an old Paula tone through multi-field bitmap preparation. */
    source_audio_mute();
    UBYTE room=progress->room;int slot=background==room_slots[0]?1:0;
    (void)force;
    room_backgrounds[slot_room[slot]]=0;slot_room[slot]=room;room_backgrounds[room]=room_slots[slot];
    background=room_slots[slot];draw_room(game,progress);
    {int b,i;for(b=0;b<2;b++)for(i=0;i<25;i++){source_rows[b][i]=0;source_words[b][i]=0;}}
}
static ULONG line_clock(void);
static ULONG elapsed_work(ULONG start);
static int update_lantern_background(const BlProgress *progress){
    UWORD count,pos;const unsigned long *words;const unsigned char *rows;(void)progress;
    ULONG part=0;if(BL_C64_PROFILE)part=line_clock();
    (void)bl_c64_paint_part(background,SCENE_TOP,160,&count);
    if(BL_C64_PROFILE){bl_c64_profile_add(1,count);bl_c64_profile_add(2,elapsed_work(part));part=line_clock();}
    words=bl_c64_part_words();rows=bl_c64_part_rows();
    for(pos=3;pos<25;pos++)if(words[pos]){
        source_words[0][pos]|=words[pos];source_words[1][pos]|=words[pos];
        source_rows[0][pos]|=rows[pos];source_rows[1][pos]|=rows[pos];
    }
    if(BL_C64_PROFILE){bl_c64_profile_add(3,elapsed_work(part));part=line_clock();}
    if(bl_c64_paint_done())bl_c64_clear_dirty();else return 0;
    if(BL_C64_PROFILE)bl_c64_profile_add(6,elapsed_work(part));
    return 1;
}

static void restore_source_cells(UBYTE *b,int buffer){
    UWORD row,budget=5000;
    for(row=3;row<25;row++)if(source_rows[buffer][row]){
        UBYTE bits=source_rows[buffer][row];UWORD dy=0,last=row;ULONG words=source_words[buffer][row];BlDirty strip;
        if(bits==255)while(last<24 && source_rows[buffer][last+1]==255 && source_words[buffer][last+1]==words)++last;
        {ULONG value=words;UWORD word_count=0,scan_count=0,cost;UBYTE mask=bits;
        while(value){++word_count;value&=value-1;}while(mask){++scan_count;mask&=(UBYTE)(mask-1);}
        cost=(UWORD)(word_count*scan_count*8);
        if(cost>budget)break;
        while(last>row && (UWORD)(cost*(last-row+1))>budget)--last;
        budget=(UWORD)(budget-cost*(last-row+1));}
        while(dy<8){
            UWORD col=0;
            if(!(bits&(1u<<dy))){++dy;continue;}
            strip.top=(short)(SCENE_TOP+row*8+dy);
            do{++dy;}while(dy<8 && (bits&(1u<<dy)));
            strip.bottom=(short)(SCENE_TOP+last*8+dy);
            while(col<20){
                if(!(words&(1UL<<col))){++col;continue;}
                strip.left=(short)(col*16);do{++col;}while(col<20 && (words&(1UL<<col)));
                strip.right=(short)(col*16);restore_actor(b,&strip);
            }
        }
        do{source_rows[buffer][row]=0;source_words[buffer][row]=0;}while(row++<last);
        --row;
    }
}

static void draw_player(UBYTE *b,const BlGame *g) {
    int x=bl_x(g),y=SCENE_TOP+bl_y(g),s=(g->step&2)?2:-2;
    if(g->prone){
        int head=x+(g->facing?7:-12);
        rect(b,x-11,y-5,22,5,13);rect(b,x-1,y-5,2,5,0);
        rect(b,head,y-6,5,5,12);rect(b,head,y-6,5,1,0);
        rect(b,x+(g->facing?2:-7),y-2,5,2,12);
        return;
    }
    rect(b,x-3,y-22,6,6,12);rect(b,x-4,y-21,8,2,0);
    pixel(b,x+(g->facing?2:-2),y-19,0);
    rect(b,x-4,y-16,8,9,13);rect(b,x-4,y-9,8,2,0);
    if(g->state==BL_CLIMB){
        int phase=(g->step&2)?1:0;
        /* Opposite hand and knee reach together. Keep every limb inside
         * the existing 32x26 dirty footprint, including the raised foot. */
        rect(b,x-8,y-(phase?16:21),3,8,12);
        rect(b,x+5,y-(phase?21:16),3,8,12);
        rect(b,x-5,y-7,3,phase?4:7,13);
        rect(b,x+2,y-7,3,phase?7:4,13);
        rect(b,x-7,y-(phase?5:2),5,2,12);
        rect(b,x+2,y-(phase?2:5),5,2,12);
        return;
    }
    else{rect(b,x-7,y-14,3,7,12);rect(b,x+4,y-14,3,7,12);}
    if(g->state==BL_AIR)s=3;
    if(g->attack==BL_FLYING_KICK){
        /* Two legs: tucked rear leg and the extended kicking leg. */
        rect(b,x+(g->facing?-6:3),y-7,3,6,13);
    }else{
        rect(b,x-4-s,y-7,3,7,13);rect(b,x+1+s,y-7,3,7,13);
    }
    if(g->attack==BL_PUNCH){
        rect(b,x+(g->facing?4:-13),y-15,9,3,12);
    }else if(g->attack==BL_FLYING_KICK){
        rect(b,x+(g->facing?3:-13),y-10,10,4,13);
        rect(b,x+(g->facing?10:-14),y-10,4,4,12);
    }
}

static void draw_health(UBYTE *b,int kind,int health){
    /* Equal readable display widths; actual health/damage stays36/20/7.
     * Each word has two seven-pixel segments separated by a dark pixel.
     * Word-aligned writes keep HUD updates cheap on the68000. */
    int column=kind==0?30:kind==1?16:2;
    int maximum=kind==0?36:kind==1?20:7;
    UBYTE color=kind==0?13:kind==1?14:11;
    int c,p,filled;
    if(health<0)health=0;
    if(health>maximum)health=maximum;
    filled=health*56/maximum;
    for(c=0;c<4;c++){
        int remaining=filled-c*14,second=remaining-7;
        UBYTE hi=remaining>=7?254:remaining>0?(UBYTE)(255U<<(8-remaining)):0;
        UBYTE lo=second>=7?254:second>0?(UBYTE)(255U<<(8-second)):0;
        UWORD fill=(UWORD)(((UWORD)hi<<8)|lo);
        for(p=0;p<4;p++){
            UWORD value=(color&(1<<p))?fill:0;
            UWORD *d=(UWORD *)(b+p*40+28*ROW_BYTES+column+c*2);
            if(p==0)value|=(UWORD)~fill;
            d[0]=value;d[80]=value;d[160]=value;
        }
    }
}

static void prepare_target(void) {
    UBYTE saved[4][26][2];
    int p,r,c,v;
    for(p=0;p<4;p++)for(r=0;r<26;r++)for(c=0;c<2;c++)
        saved[p][r][c]=background[p*40+(203+r)*ROW_BYTES+13+c];
    for(v=0;v<6;v++){
        UBYTE color=(v&1)?6:14;
        rect(background,104,203,16,26,0);
        rect(background,109,206,6,6,12);rect(background,106,212,12,10,color);
        rect(background,107,222,3,6,color);rect(background,114,222,3,6,color);
        rect(background,106,203,(v/2+1)*4,1,13);
        for(r=0;r<26;r++)for(c=0;c<2;c++){
            UBYTE mask=0;
            for(p=0;p<4;p++){
                UBYTE value=background[p*40+(203+r)*ROW_BYTES+13+c];
                target_stamp[v][p][r][c]=value;mask|=value;
            }
            target_mask[v][r][c]=mask;
        }
    }
    for(p=0;p<4;p++)for(r=0;r<26;r++)for(c=0;c<2;c++)
        background[p*40+(203+r)*ROW_BYTES+13+c]=saved[p][r][c];
}

/* Expand packed indexed art once, keeping all phases in CPU-only memory. */
static void prepare_fighters(void){
    const UBYTE *source=fighter_dma_packed;UBYTE *dest=fighter_dma;
    UBYTE count,value;
    while((count=*source++)!=128){
        if(!count){
            UWORD distance=(UWORD)(((UWORD)source[0]<<8)|source[1]);count=source[2];source+=3;
            while(count--){value=*(dest-distance);*dest++=value;
                if(BL_AUTOTEST)fighter_cache_hash=fighter_fnv(fighter_cache_hash,value);}
        }else if(count&128){count&=127;while(count--){value=*source++;*dest++=value;
            if(BL_AUTOTEST)fighter_cache_hash=fighter_fnv(fighter_cache_hash,value);}}
        else{value=*source++;while(count--){*dest++=value;
            if(BL_AUTOTEST)fighter_cache_hash=fighter_fnv(fighter_cache_hash,value);}}
    }
    fighter_cache_bytes=(ULONG)(dest-fighter_dma);
}
static void wait_blitter(void){(void)hw->dmaconr;while(hw->dmaconr&DMAF_BLTDONE){}}
static void paint_source_tile(const BlC64Paint *request){
    const UBYTE *src=request->planes;UBYTE *dest=request->bitmap+native_cell_offset[(UWORD)request->cell];
    wait_blitter();
#define TILE_ROW(r) "move.b " #r "(%0)," #r "*160(%1)\n\t" \
    "move.b " #r "+8(%0)," #r "*160+40(%1)\n\t" \
    "move.b " #r "+16(%0)," #r "*160+80(%1)\n\t" \
    "move.b " #r "+24(%0)," #r "*160+120(%1)\n\t"
    __asm__ volatile(TILE_ROW(0) TILE_ROW(1) TILE_ROW(2) TILE_ROW(3)
                     TILE_ROW(4) TILE_ROW(5) TILE_ROW(6) TILE_ROW(7)
                     : : "a"(src),"a"(dest) : "memory","cc");
#undef TILE_ROW
}
static void paint_source_block(const BlC64Block *request){
    UBYTE *target=request->bitmap+request->top*ROW_BYTES+request->left;
    wait_blitter();hw->bltcon0=0x07ca;hw->bltcon1=0;
    hw->bltafwm=(UWORD)request->first_mask;hw->bltalwm=(UWORD)request->last_mask;
    hw->bltadat=0xffff;hw->bltbdat=0;
    hw->bltbmod=0;hw->bltcmod=(WORD)(40-request->width);hw->bltdmod=(WORD)(40-request->width);
    hw->bltbpt=(APTR)request->pixels;hw->bltcpt=(APTR)target;hw->bltdpt=(APTR)target;
    hw->bltsize=(UWORD)((request->height*4<<6)|(request->width>>1));
}

static void copy_room_bitmap(UBYTE *dest,const UBYTE *source){
    wait_blitter();hw->bltcon0=0x09f0;hw->bltcon1=0;
    hw->bltafwm=0xffff;hw->bltalwm=0xffff;
    hw->bltamod=0;hw->bltdmod=0;
    hw->bltapt=(APTR)source;hw->bltdpt=(APTR)dest;
    /* OCS height zero encodes1024 rows;20 words =40 bytes per row.
     * Copies all four contiguous planes, exactly40960 bytes. */
    hw->bltsize=20;wait_blitter();
}
static void draw_fighter(UBYTE *b,const BlFighter *f,const BlGame *g,int kind,int frame,int buffer){
    int pose=bl_visual_pose(g,f->sai);
    int left=bl_x(g)-16,top=SCENE_TOP+bl_y(g)-25,col=left>>3;
    int face=bl_visual_face(g,(UBYTE)pose,kind);
    int row_start=fighter_art_rows[kind*BL_POSE_COUNT+pose][0];
    int height=fighter_art_rows[kind*BL_POSE_COUNT+pose][1]-row_start;
    BlDirty *dirty=&actor_dirty[buffer][kind];
    const UBYTE *bounds=fighter_art_bounds[kind*BL_POSE_COUNT+pose];
    dirty->left=dirty->right=0;dirty->top=dirty->bottom=0;
    if(!f->active || (f->reaction==BL_REACTION_HURT && (frame&2)))return;
    if(BL_AUTOTEST)actor_pose_seen[kind]|=(UWORD)(1u<<pose);
    top+=row_start;
    dirty->left=(short)(left+(face?bounds[0]:49-bounds[2]));
    dirty->right=(short)(left+(face?bounds[2]:49-bounds[0]));
    dirty->top=(short)top;dirty->bottom=(short)(top+height);
    {
        int aligned=col&~1,skip=aligned<0?-aligned:0,shift=left&15;
        int source_right=face?bounds[2]:49-bounds[0];
        int full_width=((source_right+shift+15)>>4)*2,width=full_width-skip;
        int clipped=aligned<0 || aligned+full_width>40,pitch=12;
        UBYTE *source=fighter_dma+fighter_dma_offsets[(kind*2+face)*BL_POSE_COUNT+pose];
        UBYTE *mask=source,*pixels=source+6;
        if(aligned+skip+width>40)width=40-aligned-skip;
        if(width<=0 || top<0 || top+height>HEIGHT)return;
        wait_blitter();
        if(clipped){
            /* Expand six-byte lanes before cropping; the final source word
             * is padding and must be masked before the barrel shifter. */
            hw->bltcon0=(UWORD)(0x09f0|(shift<<12));hw->bltcon1=0;
            hw->bltafwm=0xffff;hw->bltalwm=0;
            hw->bltamod=-2;hw->bltdmod=0;hw->bltadat=0;
            hw->bltapt=(APTR)source;hw->bltdpt=(APTR)(fighter_dma+BL_FIGHTER_CACHE_BYTES);
            hw->bltsize=(UWORD)(((height*8)<<6)|4);wait_blitter();
            mask=fighter_dma+BL_FIGHTER_CACHE_BYTES;pixels=mask+8;pitch=16;shift=0;
        }
        hw->bltcon0=(UWORD)(0x0fca|(shift<<12));hw->bltcon1=(UWORD)(shift<<12);
        hw->bltafwm=0xffff;hw->bltalwm=(UWORD)(!clipped && width==8?0:0xffff);
        hw->bltamod=(WORD)(pitch-width);hw->bltbmod=(WORD)(pitch-width);
        hw->bltcmod=(WORD)(40-width);hw->bltdmod=(WORD)(40-width);
        hw->bltadat=0;hw->bltbdat=0;
        hw->bltapt=(APTR)(mask+skip);hw->bltbpt=(APTR)(pixels+skip);
        hw->bltcpt=(APTR)(b+top*ROW_BYTES+aligned+skip);hw->bltdpt=(APTR)(b+top*ROW_BYTES+aligned+skip);
        hw->bltsize=(UWORD)(((height*4)<<6)|(width>>1));
        wait_blitter();
    }
}
static void restore_actor(UBYTE *b,const BlDirty *dirty){
    int left,right,top=dirty->top,bottom=dirty->bottom,width,height,offset;
    if(dirty->right<=dirty->left || bottom<=top)return;
    left=(dirty->left>>4)*2;right=((dirty->right+15)>>4)*2;
    if(left<0)left=0;
    if(right>40)right=40;
    if(top<0)top=0;
    if(bottom>HEIGHT)bottom=HEIGHT;
    width=right-left;height=bottom-top;
    if(width<=0 || height<=0)return;
    wait_blitter();hw->bltcon0=0x09f0;hw->bltcon1=0;
    hw->bltafwm=0xffff;hw->bltalwm=0xffff;
    hw->bltamod=(WORD)(40-width);hw->bltdmod=(WORD)(40-width);
    offset=top*ROW_BYTES+left;
    hw->bltapt=(APTR)(background+offset);hw->bltdpt=(APTR)(b+offset);
    hw->bltsize=(UWORD)((height*4<<6)|(width>>1));
    wait_blitter();
}

/* R19 VIC sprites6/7 are monochrome and X-expanded ($05B8/$361A).
 * Keep original generated bits, coordinates and colors, with separate dirt. */
static void draw_source_projectiles(UBYTE *b,int buffer){
    int i,row,col,bit;
    for(i=0;i<2;i++){
        BlC64Projectile sprite;BlDirty *dirty=&actor_dirty[buffer][3+i];
        dirty->left=dirty->right=0;
        bl_c64_projectile((UBYTE)i,&sprite);if(!sprite.active)continue;
        dirty->left=sprite.x;dirty->right=(short)(sprite.x+24*sprite.width);
        dirty->top=(short)(SCENE_TOP+sprite.y);dirty->bottom=(short)(dirty->top+21);
        for(row=0;row<21;row++)for(col=0;col<3;col++){
            UBYTE bits=sprite.bits[row*3+col];if(!bits)continue;
            for(bit=0;bit<8;bit++)if(bits&(0x80>>bit))
                rect(b,sprite.x+(col*8+bit)*sprite.width,SCENE_TOP+sprite.y+row,sprite.width,1,sprite.color);
        }
    }
}

/* Capture-only check for trails/carry leaks outside the current actors. */
static ULONG canvas_residue(const UBYTE *b,int buffer){
    ULONG bad=0,offset;
    int p,y,x,n,allowed;
    for(p=0;p<4;p++)for(y=0;y<HEIGHT;y++)for(x=0;x<40;x++){
        offset=p*40+y*ROW_BYTES+x;
        if(b[offset]==background[offset] || (y>=28 && y<=30))continue;
        allowed=0;
        for(n=0;n<5;n++){
            const BlDirty *d=&actor_dirty[buffer][n];
            if(d->right>d->left && y>=d->top && y<d->bottom &&
               x*8<d->right && x*8+8>d->left){allowed=1;break;}
        }
        if(!allowed)++bad;
    }
    return bad;
}

static void draw_target(UBYTE *b,const BlTarget *t) {
    int p,r,c,v=(t->health-1)*2+(t->invulnerable!=0),left=(t->x-8)>>3;
    for(p=0;p<4;p++)for(r=0;r<26;r++)for(c=0;c<2;c++){
        UBYTE *d=b+p*40+(203+r)*ROW_BYTES+left+c;
        *d=(*d&~target_mask[v][r][c])|target_stamp[v][p][r][c];
    }
}

static void restore_player(UBYTE *b,int x,int y) {
    BlDirty dirty;dirty.left=(short)(x-24);dirty.right=(short)(x+25);
    dirty.top=(short)(y-25);dirty.bottom=(short)(y+2);restore_actor(b,&dirty);
}

static void emit(UWORD **p,UWORD reg,UWORD value){*(*p)++=reg;*(*p)++=value;}
static void make_copper(UWORD *list,UBYTE *bitmap) {
    UWORD *p=list;int n;ULONG addr;
    emit(&p,0x100,0x4200);emit(&p,0x102,0);emit(&p,0x104,0);emit(&p,0x108,120);emit(&p,0x10a,120);
    emit(&p,0x08e,0x2c81);emit(&p,0x090,0x2cc1);emit(&p,0x092,0x0038);emit(&p,0x094,0x00d0);
    for(n=0;n<PLANES;n++){addr=(ULONG)(bitmap+(ULONG)n*40);emit(&p,0xe0+n*4,addr>>16);emit(&p,0xe2+n*4,addr);}
    for(n=0;n<16;n++)emit(&p,0x180+n*2,palette[n]);
    *p++=0xffff;*p++=0xfffe;
}
static UWORD raster(void){return (UWORD)((*(volatile ULONG*)0xdff004>>8)&0x1ff);}
static void wait_frame(void){while(raster()>=300){}while(raster()<300){}}
static ULONG field_clock(void){
    ULONG hi=*(volatile UBYTE*)0xbfea01;
    ULONG mid=*(volatile UBYTE*)0xbfe901;
    ULONG lo=*(volatile UBYTE*)0xbfe801;
    return (hi<<16)|(mid<<8)|lo;
}
static ULONG line_clock(void){
    ULONG hi,mid,lo,hi2,mid2;
    do{
        hi=*(volatile UBYTE*)0xbfda00;mid=*(volatile UBYTE*)0xbfd900;lo=*(volatile UBYTE*)0xbfd800;
        hi2=*(volatile UBYTE*)0xbfda00;mid2=*(volatile UBYTE*)0xbfd900;
        (void)*(volatile UBYTE*)0xbfd800;
    }while(hi!=hi2 || mid!=mid2);
    return (hi<<16)|(mid<<8)|lo;
}
static ULONG elapsed_work(ULONG start){return (line_clock()-start)&0xffffff;}
static UBYTE read_input(void) {
    UWORD joy=hw->joy1dat;UBYTE result=0;
    if(joy&2)result|=BL_RIGHT;
    if(joy&0x200)result|=BL_LEFT;
    if(((joy>>1)^joy)&1)result|=BL_DOWN;
    if(((joy>>1)^joy)&0x100)result|=BL_UP;
    if(!(*(volatile UBYTE*)0xbfe001&128))result|=BL_FIRE;
    return result;
}

/* Poll the keyboard while OS interrupts are disabled. Acknowledge every
 * serial byte, including releases, so the keyboard keeps transmitting. */
static UBYTE read_key(void) {
    volatile UBYTE *icr=(volatile UBYTE*)0xbfed01;
    volatile UBYTE *sdr=(volatile UBYTE*)0xbfec01;
    volatile UBYTE *cra=(volatile UBYTE*)0xbfee01;
    UBYTE serial,raw,control;
    volatile UWORD delay;
    if(!(*icr&8))return 255;
    serial=*sdr;
    raw=(UBYTE)~((serial>>1)|(serial<<7));
    control=*cra;
    *sdr=0;*cra=(UBYTE)(control|64);
    for(delay=0;delay<700;delay++){}
    *cra=(UBYTE)(control&~64);
    return raw;
}

static char report[3584];
extern unsigned long bruce_runtime_check(void);
static void number(char **p,ULONG v){char s[12];int n=0;do{s[n++]=(char)('0'+v%10);v/=10;}while(v);while(n)*(*p)++=s[--n];}
static void append(char **p,const char *s){while(*s)*(*p)++=*s++;}

int main(void) {
    struct View *old_view;UWORD old_dma,old_int,old_adk;
    ULONG free_chip_before,free_slow_before,last_field=0,max_gap=0,max_runtime_gap=0,capture_gap=0;
    ULONG climb_periods=0,air_periods=0,jump_starts=0,fall_starts=0,prone_periods=0;
    ULONG punch_periods=0,kick_periods=0;
    ULONG target_defeats=0,target_respawns=0;
    ULONG max_work_lines=0,max_work_frame=0,missed_frames=0,first_missed=0;
    ULONG stage[6]={0,0,0,0,0,0},miss_stage[6]={0,0,0,0,0,0};
    ULONG last_line_clock=0,max_hsync_gap=0,first_missed_hsync=0,cia_miss_hsync=0;
    ULONG time_walk_a=0,time_walk_b=0,time_jump_a=0,time_jump_b=0,time_fall_a=0,time_fall_b=0;
    UBYTE timing_seen=0,enemy_edge_checks=0,old_keyboard_control=0;
    UWORD timing_lines=0,timing_mode_changes=0;
    ULONG chip_largest_before=0,chip_free_loaded=0,chip_largest_loaded=0;
    ULONG cpu_stamp_chip_bytes=0,held_images=0,drawn_images=0,held_streak=0,max_held_streak=0;
    UWORD present_min=511,present_max=0,bad_presents=0;
    int n,back=0,frame=0,result=0;
    UBYTE field_phase=0;ULONG arithmetic_errors=0;
    const char *report_path="DH1:autotest-1.txt";
    int oldx[2]={28,28},oldy[2]={228,228},oldtarget[2]={112,112};UBYTE held=0,input=0,room_request=255;
    UBYTE oldtargetlook[2]={255,255};
    BlCombat world;
    BlProgress progress;
    UWORD drawn_room_revision[2]={0,0},drawn_lanterns[2]={0,0};
    ULONG room_load_fields=0,room_load_max_gap=0,room_load_events=0;
    UWORD gate_checks=0;
    ULONG capture_residue=0;UWORD capture_color15=0;
    UWORD source_worst[16]={0};
    ULONG visited_rooms_mask=1;
    ULONG intro_start=0,intro_fields=0,intro_pcm_hash=2166136261UL;
    UBYTE intro_armed=0,intro_finished=0,intro_stopped=0,intro_restored=0,exit_requested=0;
    UBYTE room_paint_pending=0;
    BlVisual enemy_visual[2];
    int oldhealth[2][3]={{-99,-99,-99},{-99,-99,-99}};
    BlTarget target;
    BlGame game,render_game;
    BlVisual visual;
    SysBase=*(struct ExecBase**)4;
    GfxBase=(struct GfxBase*)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    DOSBase=(struct DosLibrary*)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!GfxBase||!DOSBase){
        if(GfxBase)CloseLibrary((struct Library*)GfxBase);
        if(DOSBase)CloseLibrary((struct Library*)DOSBase);
        return 20;
    }
    if(BL_AUTOTEST){BPTR previous=Open((CONST_STRPTR)report_path,MODE_OLDFILE);
        if(previous){Close(previous);report_path="DH1:autotest-2.txt";}}
    if(BL_AUTOTEST)arithmetic_errors=bruce_runtime_check();
    free_chip_before=AvailMem(MEMF_CHIP);free_slow_before=AvailMem(MEMF_FAST);
    if(BL_AUTOTEST)chip_largest_before=AvailMem(MEMF_CHIP|MEMF_LARGEST);
    background=AllocMem(BITMAP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    tile_dma=AllocMem(TILE_DMA_BYTES,MEMF_CHIP|MEMF_CLEAR);
    room_backgrounds[0]=background;
    if(!BL_AUTOTEST || BL_COMBAT_TEST)room_backgrounds[1]=AllocMem(BITMAP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    room_slots[0]=background;room_slots[1]=room_backgrounds[1];
    if(!BL_AUTOTEST || BL_COMBAT_TEST)fighter_dma=AllocMem(FIGHTER_DMA_BYTES,MEMF_CHIP|MEMF_CLEAR);
    if(BL_AUTOTEST){capture=AllocMem(BITMAP_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}
    sfx_pcm=AllocMem(BL_SFX_CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    for(n=0;n<2;n++){buffers[n]=AllocMem(BITMAP_BYTES,MEMF_CHIP|MEMF_CLEAR);copper[n]=AllocMem(COPPER_BYTES,MEMF_CHIP|MEMF_CLEAR);}
    if(((!BL_AUTOTEST || BL_COMBAT_TEST)&&(!fighter_dma||!room_backgrounds[1]))||!background||!buffers[0]||!buffers[1]||!copper[0]||!copper[1]||
       !tile_dma||!sfx_pcm||(BL_AUTOTEST&&(!capture||!tone))) {result=20;goto cleanup;}
    source_audio_copy();
    if(BL_AUTOTEST){chip_free_loaded=AvailMem(MEMF_CHIP);chip_largest_loaded=AvailMem(MEMF_CHIP|MEMF_LARGEST);}
    if(BL_AUTOTEST)for(n=0;n<32;n++)tone[n]=(UBYTE)(n<16?40:-40);
    /* Decode into the back bitmap before DMA owns it. No extra Chip RAM. */
    intro_decode(buffers[1]);
    if(BL_AUTOTEST){ULONG i;for(i=0;i<BL_INTRO_PCM_BYTES;i++)
        intro_pcm_hash=(intro_pcm_hash^buffers[1][i])*16777619UL;}
    draw_loading(buffers[0]);
    for(n=0;n<2;n++)make_copper(copper[n],buffers[n]);
    old_view=GfxBase->ActiView;
    Forbid();LoadView(0);WaitTOF();WaitTOF();OwnBlitter();WaitBlit();Disable();
    old_dma=hw->dmaconr;old_int=hw->intenar;old_adk=hw->adkconr;
    if(!BL_AUTOTEST){
        old_keyboard_control=*(volatile UBYTE*)0xbfee01;
        *(volatile UBYTE*)0xbfee01=(UBYTE)(old_keyboard_control&~64);
        (void)*(volatile UBYTE*)0xbfed01;
    }
    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    hw->cop1lc=(ULONG)copper[0];hw->copjmp1=0;
    hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_BLITHOG;
    intro_start=field_clock();
    hw->aud[0].ac_ptr=(volatile UWORD*)buffers[1];
    hw->aud[0].ac_len=BL_INTRO_PCM_BYTES/2;
    hw->aud[0].ac_per=BL_INTRO_PERIOD;hw->aud[0].ac_vol=48;
    hw->dmacon=DMAF_SETCLR|DMAF_AUD0;
    /* Paula interrupts when the initial DMA registers latch. Arm silence
     * before the lengthy CPU-side preparation, rather than replaying voice. */
    for(n=0;n<4;n++){
        wait_frame();
        if(hw->intreqr&0x80){
            hw->aud[0].ac_ptr=(volatile UWORD*)(buffers[1]+BL_INTRO_PCM_BYTES);
            hw->aud[0].ac_len=2;hw->intreq=0x80;intro_armed=1;break;
        }
    }
    {int row,col;for(row=0;row<25;row++)for(col=0;col<40;col++){
        native_cell_offset[row*40+col]=(UWORD)((SCENE_TOP+row*8)*ROW_BYTES+col);
    }}
    bl_c64_set_painter(paint_source_tile);bl_c64_set_block_painter(paint_source_block);
    bl_combat_reset(&world);bl_progress_reset(&progress);
    if(BL_AUTOTEST && BL_ROOM_TOUR && BL_TEST_START_ROOM)bl_progress_inspect_room(&progress,&world,BL_TEST_START_ROOM);
    draw_room(&world.player.body,(!BL_AUTOTEST || BL_COMBAT_TEST)?&progress:0);
    prepare_target();if(!BL_AUTOTEST || BL_COMBAT_TEST)prepare_fighters();
    if(BL_AUTOTEST && BL_COMBAT_TEST){
        for(n=0;n<BL_COMBAT_WARMUP;n++)bl_combat_step(&world,n<1000?0:BL_FIRE);
    }
    for(n=0;n<2;n++)bl_visual_reset(&enemy_visual[n],&world.enemy[n].body);
    bl_reset(&game);if(BL_AUTOTEST && BL_COMBAT_TEST)game=world.player.body;
    bl_visual_reset(&visual,&game);bl_target_reset(&target);
    for(;;){
        intro_fields=(field_clock()-intro_start)&0xffffff;
        if(intro_armed && (hw->intreqr&0x80)){intro_finished=1;break;}
        if(intro_fields>=BL_INTRO_TIMEOUT_FIELDS)break;
        if(!BL_AUTOTEST && read_key()==0x45){exit_requested=1;break;}
        wait_frame();
    }
    hw->dmacon=DMAF_AUD0;hw->aud[0].ac_vol=0;hw->intreq=0x80;
    /* At least four complete raster lines exceed two period322 samples. */
    {UWORD previous=raster();for(n=0;n<5;n++){
        while(raster()==previous){}previous=raster();}}
    intro_stopped=(UBYTE)((hw->dmaconr&DMAF_AUD0)==0);
    if(exit_requested)goto restore_os;
    /* Source $06DA/$154C plays the title theme until the start input;
     * gameplay $15A8 switches to the three independent SFX drivers. */
    rect(buffers[0],0,160,320,18,0);text(buffers[0],106,166,"FIRE TO START",5);
    wait_frame();hw->cop1lc=(ULONG)copper[0];
    source_audio_begin();
    for(;;){
        bl_source_audio_music(&source_audio,source_registers);source_audio_output(1);
        wait_frame();
        if(BL_AUTOTEST){if(source_music_fields>=120)break;}
        else{
            UBYTE key=read_key();if(key==0x45){exit_requested=1;break;}
            if(read_input()&BL_FIRE)break;
        }
    }
    source_music_faults=bl_source_audio_faults();
    for(n=0;n<3;n++)hw->aud[n].ac_vol=0;
    if(exit_requested)goto restore_os;
    bl_source_audio_reset(&source_audio);bl_c64_audio_reset();
    copy(buffers[1],background,BITMAP_BYTES);
    wait_frame();hw->cop1lc=(ULONG)copper[1];wait_frame();
    copy(buffers[0],background,BITMAP_BYTES);intro_restored=1;
    for(;;) {
        ULONG now,gap,measured_line_gap=0,render_clock=line_clock();
        UBYTE hold_image=0;
        UBYTE room_load_this_frame=0;
        /* Exercise all15 valid source requests, including low priorities. */
        if(BL_AUTOTEST && frame>=20 && frame<=300 && frame%20==0)
            bl_c64_audio_request(0x80+frame/20-1);
        if(!BL_AUTOTEST){
            UBYTE key=read_key();
            if(key==0x45)break;
            if(key==0x50)room_request=(UBYTE)((progress.room+19)%20);
            if(key==0x51)room_request=(UBYTE)((progress.room+1)%20);
        }
        input=read_input();
        if(BL_AUTOTEST && !BL_COMBAT_TEST){
            if(frame==1080){bl_reset(&game);bl_visual_reset(&visual,&game);bl_target_reset(&target);held=0;}
            if(frame==1440){
                unsigned short hits=target.hits;
                bl_reset(&game);game.x=112*16;game.y=166*16;
                game.previous_x=game.x;game.previous_y=game.y;
                game.state=BL_AIR;game.velocity_y=2*16;
                bl_visual_reset(&visual,&game);bl_target_reset(&target);target.hits=hits;held=0;
            }
            if(frame==1530){bl_reset(&game);bl_visual_reset(&visual,&game);held=0;}
            if(frame==1620){
                bl_reset(&game);game.x=128*16;game.y=136*16;
                game.previous_x=game.x;game.previous_y=game.y;
                game.state=BL_AIR;game.velocity_y=2*16;target.x=304;
                bl_visual_reset(&visual,&game);held=0;
            }
            if(frame==120)copy(capture,buffers[back],BITMAP_BYTES);
            input=frame<18?BL_DOWN:frame<42?BL_FIRE:frame<60?0:frame<132?BL_RIGHT:frame<252?BL_UP:frame<336?BL_RIGHT:0;
            if(frame>=360){
                unsigned int phase=(unsigned int)(frame-360)%240;
                input=phase<65?BL_RIGHT:phase<110?BL_UP:phase<175?BL_LEFT:
                    phase<215?BL_UP:BL_DOWN;
                if(phase<30)input|=BL_FIRE;
            }
            if(frame>=1080)input=frame<1122?BL_RIGHT:frame<1170?BL_FIRE:
                frame<1200?(BL_RIGHT|BL_FIRE):0;
            if(frame>=1530)input=frame<1536?BL_UP:0;
            if(frame>=BL_TEST_FRAMES)break;
        }
        if(BL_AUTOTEST && BL_COMBAT_TEST){
            if(frame==BL_CAPTURE_FRAME){
                copy(capture,buffers[back],BITMAP_BYTES);
                capture_residue=canvas_residue(buffers[back],back);capture_color15=copper[back][65];
            }
            input=frame+BL_COMBAT_WARMUP*3<3000?0:BL_FIRE;if(frame>=BL_TEST_FRAMES)break;}
#if BL_ENEMY_EDGE_TEST
        input=frame<192?BL_RIGHT:frame<384?0:frame<576?BL_LEFT:0;
#endif
#if BL_ROOM_TEST
        input=room_fixture_input((UWORD)(frame/3));
#endif
#if BL_ROOM_TOUR
        input=0;
        if(frame && frame%360==0){
            wait_blitter();source_render_mismatches+=(ULONG)bl_c64_check_interleaved(background,SCENE_TOP);++source_render_checks;
            room_request=(UBYTE)((frame/360+BL_TEST_START_ROOM)%20);
        }
#endif
#if BL_GATE_TEST
        input=0;
#endif
        if(BL_AUTOTEST && BL_COMBAT_TEST)stage[0]=elapsed_work(last_line_clock);
        held|=input;
        if(BL_AUTOTEST)bl_c64_profile_reset();
        /* MACHINE-0001 observes three PAL fields per candidate game step.
         * Native input phase and retail edition parity remain unverified. */
        bl_c64_audio_frame(source_registers);source_audio_output(0);
        bl_c64_field();
        if(field_phase==0){
            UBYTE previous_state=game.state;
            UBYTE previous_health=target.health;
            if(!BL_AUTOTEST || BL_COMBAT_TEST){
                UWORD previous_revision=progress.revision;
                UBYTE previous_room=progress.room;
                UBYTE states[2],active[2],player_active=world.player.active;
                for(n=0;n<2;n++){states[n]=world.enemy[n].body.state;active[n]=world.enemy[n].active;}
#if BL_GATE_TEST
                input=gate_fixture_prepare(&progress,&world,(UWORD)(frame/3));
#endif
                {ULONG tick_start=BL_C64_PROFILE?line_clock():0;
                if(room_request<20){
                    bl_progress_inspect_room(&progress,&world,room_request);room_request=255;
                }else bl_progress_step(&progress,&world,input|(held&(BL_UP|BL_FIRE)));
                if(BL_C64_PROFILE)bl_c64_profile_add(4,elapsed_work(tick_start));}
                bl_c64_prepare_paint();
                game=world.player.body;
#if BL_GATE_TEST
                gate_checks|=gate_fixture_check(&progress,&world,(UWORD)(frame/3));
#endif
                visited_rooms_mask|=1UL<<progress.room;
#if BL_ENEMY_EDGE_TEST
                /* Same ordinary-input route as ENEMY-EDGE-0001. Check the
                 * compiled 68000 state, including the below-platform player. */
                {
                    const BlFighter *f=&world.enemy[BL_NINJA];
                    int x=bl_x(&f->body),y=bl_y(&f->body);
                    if(world.step==96 && f->active && x==294 && y==98 && f->body.facing)enemy_edge_checks|=1;
                    if(world.step==114 && !f->active && x==302 && y==98 && f->respawn==160 && bl_y(&world.player.body)==196)enemy_edge_checks|=2;
                    if(world.step==274 && f->active && x==294 && y==98 && !f->body.facing)enemy_edge_checks|=4;
                    if(world.step==290 && f->active && x==290 && y==98)enemy_edge_checks|=8;
                }
#endif
                if(previous_revision==progress.revision && bl_c64_needs_full_paint())++progress.revision;
                if(previous_revision!=progress.revision){
                    (void)previous_room;
                    room_paint_pending=0;
                    ++room_load_events;
                    load_room_background(&game,&progress,previous_room==progress.room);
                    bl_visual_reset(&visual,&game);
                    for(n=0;n<2;n++){
                        bl_visual_reset(&enemy_visual[n],&world.enemy[n].body);
                        oldhealth[n][0]=-99;oldhealth[n][1]=-99;oldhealth[n][2]=-99;
                    }
                }else room_paint_pending=1;
                if(!player_active && world.player.active)bl_visual_reset(&visual,&game);
                for(n=0;n<2;n++){
                    if(!active[n] && world.enemy[n].active)bl_visual_reset(&enemy_visual[n],&world.enemy[n].body);
                    else bl_visual_target(&enemy_visual[n],&world.enemy[n].body,states[n]);
                }
            }else bl_step(&game,input|(held&(BL_UP|BL_FIRE)));
            held=0;
            if(BL_AUTOTEST && frame>=1080){
                ULONG stamp=field_clock();
                UWORD lines=(UWORD)(312+((hw->vposr&0x8000)!=0));
                if(!timing_lines)timing_lines=lines;
                else if(timing_lines!=lines)++timing_mode_changes;
                if(frame<1122){
                    if(!(timing_seen&1) && bl_x(&game)==32){time_walk_a=stamp;timing_seen|=1;}
                    if(!(timing_seen&2) && bl_x(&game)==98){time_walk_b=stamp;timing_seen|=2;}
                }
                if(frame>=1530 && frame<1620){
                    if(!(timing_seen&4) && game.state==BL_AIR){time_jump_a=stamp;timing_seen|=4;}
                    if((timing_seen&4) && !(timing_seen&8) && game.state==BL_GROUND){time_jump_b=stamp;timing_seen|=8;}
                }
                if(frame>=1620){
                    if(!(timing_seen&16) && bl_y(&game)==138){time_fall_a=stamp;timing_seen|=16;}
                    if(!(timing_seen&32) && bl_y(&game)==196){time_fall_b=stamp;timing_seen|=32;}
                }
            }
            if(BL_AUTOTEST && !BL_COMBAT_TEST)bl_target_step(&target,&game);
            if(BL_AUTOTEST){
                if(previous_health && !target.health)++target_defeats;
                if(!previous_health && target.health)++target_respawns;
            }
            bl_visual_target(&visual,&game,previous_state);
            if(BL_AUTOTEST&&previous_state!=BL_AIR&&game.state==BL_AIR){
                if(game.jump_phase!=255)++jump_starts;else ++fall_starts;
            }
        }
        /* Source state/collision changes happen in the logic field. Publish
         * changed character pixels one PAL field later, sharing work across
         * the three-field seam while keeping logic/input cadence unchanged. */
        if(room_paint_pending && field_phase!=0){
            ULONG paint_start=BL_C64_PROFILE?line_clock():0;
            room_paint_pending=(UBYTE)!update_lantern_background(&progress);
            if(BL_C64_PROFILE)bl_c64_profile_add(5,elapsed_work(paint_start));
        }
        if(BL_AUTOTEST && BL_COMBAT_TEST)stage[1]=elapsed_work(last_line_clock);
        if(BL_AUTOTEST){if(game.state==BL_CLIMB)++climb_periods;if(game.state==BL_AIR)++air_periods;if(game.prone)++prone_periods;}
        if(BL_AUTOTEST){if(game.attack==BL_PUNCH)++punch_periods;if(game.attack==BL_FLYING_KICK)++kick_periods;}
        render_game=game;
        bl_visual_frame(&visual);
        render_game.x=visual.x;render_game.y=visual.y;
        /* Climbing poses follow displayed travel, not a running timer:
         * stopping freezes the pose, and descending reverses the cycle. */
        if(!BL_AUTOTEST || BL_COMBAT_TEST){
            ULONG spent;UBYTE pending=0;
            for(n=0;n<2;n++)bl_visual_frame(&enemy_visual[n]);
            spent=elapsed_work(render_clock);
            if(drawn_room_revision[back^1]==progress.revision && spent>140){
                int row;for(row=3;row<25;row++)if(source_rows[back^1][row]){pending=1;break;}
                if(spent>(pending?140:220))hold_image=1;
            }
        }
        if(hold_image){++held_images;++held_streak;if(held_streak>max_held_streak)max_held_streak=held_streak;}
        else{++drawn_images;held_streak=0;
        back^=1;
        if((!BL_AUTOTEST || BL_COMBAT_TEST) && drawn_room_revision[back]!=progress.revision){
            room_load_this_frame=1;
            copy_room_bitmap(buffers[back],background);
            drawn_room_revision[back]=progress.revision;
            drawn_lanterns[back]=progress.collected[progress.room];
        }
        if(!BL_AUTOTEST || BL_COMBAT_TEST)restore_actor(buffers[back],&actor_dirty[back][2]);
        else restore_player(buffers[back],oldx[back],oldy[back]);
        if(!BL_AUTOTEST || BL_COMBAT_TEST){
            UWORD mask=progress.collected[progress.room],changed=(UWORD)(mask^drawn_lanterns[back]);
            if(changed){
                const BlRoomFacts *room=bl_room(progress.room);
                for(n=0;n<room->lantern_count;n++)if(changed&(1u<<n))
                    restore_player(buffers[back],room->lanterns[n].column*8-4,
                        SCENE_TOP+room->lanterns[n].row*16+8);
                drawn_lanterns[back]=mask;
            }
            for(n=0;n<2;n++)restore_actor(buffers[back],&actor_dirty[back][n]);
            restore_actor(buffers[back],&actor_dirty[back][3]);
            restore_actor(buffers[back],&actor_dirty[back][4]);
            restore_source_cells(buffers[back],back);
            if(BL_AUTOTEST && BL_COMBAT_TEST)stage[2]=elapsed_work(last_line_clock);
            for(n=0;n<2;n++){
                BlGame body=world.enemy[n].body;
                body.x=enemy_visual[n].x;body.y=enemy_visual[n].y;
                draw_fighter(buffers[back],&world.enemy[n],&body,n,frame,back);
            }
            if(BL_AUTOTEST && BL_COMBAT_TEST)stage[3]=elapsed_work(last_line_clock);
            draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);
            draw_source_projectiles(buffers[back],back);
            if(BL_AUTOTEST && BL_COMBAT_TEST)stage[4]=elapsed_work(last_line_clock);
            for(n=0;n<3;n++){
                int health=n==0?world.player.health:world.enemy[n-1].health;
                if(health!=oldhealth[back][n]){
                    draw_health(buffers[back],n,health);
                    oldhealth[back][n]=health;
                }
            }
        }else{
        {
        UBYTE look=target.respawn?0:(target.health|(target.invulnerable?8:0));
        int changed=oldtarget[back]!=target.x || oldtargetlook[back]!=look;
        if(changed)restore_player(buffers[back],oldtarget[back],SCENE_TOP+196);
        if(!target.respawn && (changed ||
           (oldx[back]>target.x-29 && oldx[back]<target.x+29) ||
           (bl_x(&render_game)>target.x-29 && bl_x(&render_game)<target.x+29))){
            draw_target(buffers[back],&target);
        }
        oldtarget[back]=target.x;oldtargetlook[back]=look;
        }
        draw_player(buffers[back],&render_game);
        }
        if(BL_AUTOTEST && BL_COMBAT_TEST)stage[5]=elapsed_work(last_line_clock);
        oldx[back]=bl_x(&render_game);oldy[back]=SCENE_TOP+bl_y(&render_game);
        }
        /* Finish the back buffer before waiting for presentation. Restarting
         * Copper after drawing can reload bitplane pointers mid-display.
         * Publish only during vertical blank; hardware restarts at field 0. */
        if(BL_AUTOTEST && frame && frame!=BL_CAPTURE_FRAME && !room_load_this_frame){
            ULONG work=elapsed_work(last_line_clock);
            if(work>max_work_lines){max_work_lines=work;max_work_frame=(ULONG)frame;
                if(BL_C64_PROFILE){for(n=0;n<16;n++)source_worst[n]=bl_c64_profile((UBYTE)n);}
                else{source_worst[0]=bl_c64_profile(0);source_worst[4]=bl_c64_profile(4);}
            }
        }
        copper[back][65]=palette[bl_c64_flash_color()];
        wait_frame();
        if(BL_AUTOTEST){
            ULONG pulse=line_clock(),linegap=(pulse-last_line_clock)&0xffffff;
            if(frame && frame!=BL_CAPTURE_FRAME && !room_load_this_frame && linegap>max_hsync_gap)max_hsync_gap=linegap;
            if(frame && frame!=BL_CAPTURE_FRAME && !room_load_this_frame && linegap>314 && !first_missed_hsync)first_missed_hsync=linegap;
            measured_line_gap=linegap;last_line_clock=pulse;
        }
        now=field_clock();gap=(now-last_field)&0xffffff;
        if(frame && gap>max_gap)max_gap=gap;
        if(BL_AUTOTEST&&frame==BL_CAPTURE_FRAME)capture_gap=gap;
        else if(BL_AUTOTEST && room_load_this_frame){
            room_load_fields+=gap;if(gap>room_load_max_gap)room_load_max_gap=gap;
        }
        else if(frame){
            if(gap>max_runtime_gap)max_runtime_gap=gap;
            if(BL_AUTOTEST && gap>1){if(!missed_frames){cia_miss_hsync=measured_line_gap;first_missed=(ULONG)frame;for(n=0;n<6;n++)miss_stage[n]=stage[n];}++missed_frames;}
        }
        last_field=now;
        if(BL_AUTOTEST){
            UWORD line=raster();
            if(line<present_min)present_min=line;
            if(line>present_max)present_max=line;
            if(line<300||line>308)++bad_presents;
        }
        hw->cop1lc=(ULONG)copper[back];
        ++frame;field_phase=(UBYTE)(field_phase==2?0:field_phase+1);
        if(BL_AUTOTEST && max_runtime_gap>1 && !BL_COLLECT_FRAME_DROPS)break;
    }
restore_os:
    wait_frame();WaitBlit();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;
    hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
    hw->adkcon=old_adk|0x8000;hw->dmacon=old_dma|0x8000;hw->intena=old_int|0x8000;
    if(!BL_AUTOTEST)*(volatile UBYTE*)0xbfee01=old_keyboard_control;
    Enable();DisownBlitter();LoadView(old_view);WaitTOF();WaitTOF();Permit();
    if(BL_AUTOTEST){
        char *p=report;BPTR file;
        append(&p,"Bruce prototype autotest\nframes=");number(&p,frame);
        append(&p,"\nchip_available_before=");number(&p,free_chip_before);
        append(&p,"\nexpansion_available_before=");number(&p,free_slow_before);
        append(&p,"\nchip_largest_before=");number(&p,chip_largest_before);
        append(&p,"\nchip_free_loaded=");number(&p,chip_free_loaded);
        append(&p,"\nchip_largest_loaded=");number(&p,chip_largest_loaded);
        append(&p,"\npresent_min_line=");number(&p,present_min);
        append(&p,"\npresent_max_line=");number(&p,present_max);
        append(&p,"\nbad_presents=");number(&p,bad_presents);
        append(&p,"\nexplicit_chip_bytes=");number(&p,BITMAP_BYTES*(BL_COMBAT_TEST?4:3)+TILE_DMA_BYTES+COPPER_BYTES*2+32+(BL_COMBAT_TEST?FIGHTER_DMA_BYTES:0)+BL_SFX_CHIP_BYTES+cpu_stamp_chip_bytes);
        append(&p,"\ncpu_stamp_chip_bytes=");number(&p,cpu_stamp_chip_bytes);
        append(&p,"\nfighter_cache_bytes=");number(&p,fighter_cache_bytes);
        append(&p,"\nfighter_cache_hash=");number(&p,fighter_cache_hash);
        append(&p,"\nsource_audio_chip_bytes=");number(&p,BL_SFX_CHIP_BYTES);
        append(&p,"\nsource_audio_fields=");number(&p,source_audio_fields);
        append(&p,"\nsource_music_fields=");number(&p,source_music_fields);
        append(&p,"\nsource_audio_hash=");number(&p,source_audio_hash);
        append(&p,"\nsource_music_hash=");number(&p,source_music_hash);
        append(&p,"\nsource_audio_voice_mask=");number(&p,source_voice_mask);
        append(&p,"\nsource_sfx_request_mask=");number(&p,bl_c64_audio_requests());
        append(&p,"\nsource_audio_faults=");number(&p,bl_c64_audio_faults()+bl_source_audio_faults()+source_music_faults);
        append(&p,"\nintro_pcm_hash=");number(&p,intro_pcm_hash);
        append(&p,"\nintro_samples=");number(&p,BL_INTRO_PCM_BYTES);
        append(&p,"\nintro_fields=");number(&p,intro_fields);
        append(&p,"\nintro_silence_reload=");number(&p,intro_armed);
        append(&p,"\nintro_finished=");number(&p,intro_finished);
        append(&p,"\nintro_dma_stopped=");number(&p,intro_stopped);
        append(&p,"\nintro_bitmap_restored=");number(&p,intro_restored);
        append(&p,"\nmax_pal_field_gap=");number(&p,max_gap);
        append(&p,"\nmax_gap_excluding_framebuffer_capture=");number(&p,max_runtime_gap);
        append(&p,"\nframebuffer_capture_gap=");number(&p,capture_gap);
        append(&p,"\nclimb_periods=");number(&p,climb_periods);
        append(&p,"\nprone_periods=");number(&p,prone_periods);
        append(&p,"\npunch_periods=");number(&p,punch_periods);
        append(&p,"\nkick_periods=");number(&p,kick_periods);
        append(&p,"\nmax_work_lines=");number(&p,max_work_lines);
        append(&p,"\nmax_work_frame=");number(&p,max_work_frame);
        append(&p,"\nmissed_frames=");number(&p,missed_frames);
        append(&p,"\nfirst_missed_frame=");number(&p,first_missed);
        for(n=0;n<6;n++){append(&p,"\nstage");number(&p,n);append(&p,"=");number(&p,miss_stage[n]);}
        append(&p,"\nmax_hsync_gap=");number(&p,max_hsync_gap);
        append(&p,"\nfirst_missed_hsync=");number(&p,first_missed_hsync);
        append(&p,"\ncia_miss_hsync=");number(&p,cia_miss_hsync);
        append(&p,"\ncombat_warmup_steps=");number(&p,BL_COMBAT_WARMUP);
        append(&p,"\ncombat_mode=");number(&p,BL_COMBAT_TEST);
        append(&p,"\nenemy_spawns=");number(&p,world.spawns);
        append(&p,"\nenemy_edge_test=");number(&p,BL_ENEMY_EDGE_TEST);
        append(&p,"\nenemy_edge_checks=");number(&p,enemy_edge_checks);
        append(&p,"\nroom_test=");number(&p,BL_ROOM_TEST);
        append(&p,"\nroom_tour=");number(&p,BL_ROOM_TOUR);
        append(&p,"\ntest_start_room=");number(&p,BL_TEST_START_ROOM);
        append(&p,"\nsource_profile=");number(&p,BL_C64_PROFILE);
        append(&p,"\ncollect_frame_drops=");number(&p,BL_COLLECT_FRAME_DROPS);
        append(&p,"\ngate_test=");number(&p,BL_GATE_TEST);
        append(&p,"\ngate_checks=");number(&p,gate_checks);
        append(&p,"\nheld_image_fields=");number(&p,held_images);
        append(&p,"\ndrawn_image_fields=");number(&p,drawn_images);
        append(&p,"\nmax_held_image_streak=");number(&p,max_held_streak);
        append(&p,"\nruntime_arithmetic_errors=");number(&p,arithmetic_errors);
        append(&p,"\nc64_render_checks=");number(&p,source_render_checks);
        append(&p,"\nc64_render_mismatches=");number(&p,source_render_mismatches);
        append(&p,"\nc64_room_fault=");number(&p,bl_c64_fault());
        for(n=0;n<16;n++){append(&p,"\nc64_profile_");number(&p,n);append(&p,"=");number(&p,source_worst[n]);}
        append(&p,"\nc64_room_revision=");number(&p,bl_c64_revision());
        append(&p,"\ncapture_color15=");number(&p,capture_color15);
        append(&p,"\ncanvas_residue_bytes=");number(&p,capture_residue);
        append(&p,"\npose_yamo=");number(&p,actor_pose_seen[0]);
        append(&p,"\npose_ninja=");number(&p,actor_pose_seen[1]);
        append(&p,"\npose_bruce=");number(&p,actor_pose_seen[2]);
        append(&p,"\nvisited_rooms_mask=");number(&p,visited_rooms_mask);
        append(&p,"\nroom_transitions=");number(&p,progress.transitions);
        append(&p,"\nlantern_pickups=");number(&p,progress.pickups);
        append(&p,"\nscore=");number(&p,progress.score);
        append(&p,"\nfinal_room=");number(&p,progress.room);
        append(&p,"\nroom_load_events=");number(&p,room_load_events);
        append(&p,"\nroom_load_fields=");number(&p,room_load_fields);
        append(&p,"\nroom_load_max_gap=");number(&p,room_load_max_gap);
        append(&p,"\ncombat_hits=");number(&p,world.hits);
        append(&p,"\nenemy_defeats=");number(&p,world.defeats);
        append(&p,"\nplayer_deaths=");number(&p,world.player_deaths);
        append(&p,"\nplayer_respawns=");number(&p,world.player_respawns);
        append(&p,"\ntarget_hits=");number(&p,target.hits);
        append(&p,"\ntarget_stomps=");number(&p,target.stomps);
        append(&p,"\ntarget_defeats=");number(&p,target_defeats);
        append(&p,"\ntarget_respawns=");number(&p,target_respawns);
        append(&p,"\ntiming_seen=");number(&p,timing_seen);
        append(&p,"\ntiming_pal_lines=");number(&p,timing_lines);
        append(&p,"\ntiming_mode_changes=");number(&p,timing_mode_changes);
        append(&p,"\ntiming_walk_fields=");number(&p,(time_walk_b-time_walk_a)&0xffffff);
        append(&p,"\ntiming_jump_fields=");number(&p,(time_jump_b-time_jump_a)&0xffffff);
        append(&p,"\ntiming_fall_fields=");number(&p,(time_fall_b-time_fall_a)&0xffffff);
        append(&p,"\nair_periods=");number(&p,air_periods);
        append(&p,"\njump_starts=");number(&p,jump_starts);
        append(&p,"\nfall_starts=");number(&p,fall_starts);
        append(&p,"\nfinal_x=");number(&p,bl_x(&game));
        append(&p,"\nfinal_y=");number(&p,bl_y(&game));append(&p,"\nrestored_os=1\nparity=PROVISIONAL\n");
        file=Open((CONST_STRPTR)report_path,MODE_NEWFILE);
        if(file){Write(file,report,p-report);Close(file);}else result=10;
        file=Open((CONST_STRPTR)"DH1:autotest-frame.bpl",MODE_NEWFILE);
        if(file){Write(file,capture,BITMAP_BYTES);Close(file);}else result=10;
    }
cleanup:
    if(result==20 && BL_AUTOTEST){
        BPTR failure=Open((CONST_STRPTR)report_path,MODE_NEWFILE);
        char message[]="allocation_failed=1\nframes=0\nparity=PROVISIONAL\n";
        if(failure){Write(failure,message,sizeof(message)-1);Close(failure);}
    }
    for(n=0;n<2;n++){if(buffers[n])FreeMem(buffers[n],BITMAP_BYTES);if(copper[n])FreeMem(copper[n],COPPER_BYTES);}
    if(fighter_dma)FreeMem(fighter_dma,FIGHTER_DMA_BYTES);
    if(tile_dma)FreeMem(tile_dma,TILE_DMA_BYTES);
    bl_c64_set_painter(0);bl_c64_set_block_painter(0);
    for(n=0;n<2;n++)if(room_slots[n])FreeMem(room_slots[n],BITMAP_BYTES);
    if(capture)FreeMem(capture,BITMAP_BYTES);
    if(tone)FreeMem(tone,32);
    if(sfx_pcm)FreeMem(sfx_pcm,BL_SFX_CHIP_BYTES);
    CloseLibrary((struct Library*)DOSBase);CloseLibrary((struct Library*)GfxBase);
    return result;
}
