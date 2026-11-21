/* Optional display resources. The source engine owns every contact mask. */
typedef struct { UWORD input,words; UBYTE width,height; } EnhancedBlock;
typedef struct { UWORD words; UBYTE left,top,width,height; } EnhancedView;
#define ENHANCED_STORAGE
#include "enhanced_art.h"
#if ENHANCED_TILE_BASE+ENHANCED_TILE_BYTES > BL_FIGHTER_CACHE_BYTES
#error Enhanced art exceeds the shared Chip buffer
#endif
static UBYTE enhanced_selected,enhanced_active;

static __attribute__((noinline,optimize("Os"))) void prepare_enhanced(UBYTE *temporary){
    UWORD i;
    unpack_art(temporary,enhanced_packed,0);
    for(i=0;i<sizeof(enhanced_blocks)/sizeof(enhanced_blocks[0]);i++){
        const EnhancedBlock *f=&enhanced_blocks[i];
        UBYTE *dest=fighter_dma+2UL*f->words;UWORD y,x,p;
        UWORD lane=f->width<=16?4:6;
        for(y=0;y<f->height;y++,dest+=8*lane){
            UBYTE mask[6]={0},planes[4][6]={{0}};
            const UBYTE *row=temporary+f->input+y*((f->width+1)>>1);
            for(x=0;x<f->width;x++){
                UBYTE color=row[x>>1],bit=128>>(x&7);
                color=(x&1)?color&15:color>>4;
                if(color==15)continue;
                mask[x>>3]|=bit;
                for(p=0;p<4;p++)if(color&(1<<p))planes[p][x>>3]|=bit;
            }
            for(p=0;p<4;p++)for(x=0;x<lane;x++){
                dest[2*lane*p+x]=mask[x];dest[2*lane*p+lane+x]=planes[p][x];
            }
        }
        source_audio_service();
    }
    for(i=0;i<ENHANCED_TILE_BYTES;i++)
        fighter_dma[ENHANCED_TILE_BASE+i]=temporary[ENHANCED_NIBBLES+i];
}

static ULONG enhanced_frame(const BlGame *g,UWORD kind,UWORD pose,UBYTE *bounds){
    /* Bruce's Enhanced poses. NPCs use the original pose and its actual facing. */
    static const UBYTE slots[35]={0,0,8,8,14,5,6,1,1,1,1,9,10,9,10,15,16,9,4,9,2,0,12,12,7,8,7,8,12,11,12,11,17,17,16};
    UWORD slot=slots[pose],face=g->facing!=0;
    /* $288B-$28B0 selects a directional kick pair from state 12/13.
     * Facing can change while the selected pose remains latched. */
    if(kind<2){
        UWORD actor_face=kind*2+face,index=actor_face*35+pose;
        const UBYTE *source=c64_sprite_bounds[index];
        bounds[0]=source[0];bounds[1]=source[1];bounds[2]=source[2];bounds[3]=source[3];
        if(pose>=0x0e/2 && pose<=0x14/2 && (bl_x(g)&8))
            return 2UL*enhanced_alt_run_words[actor_face*4+pose-0x0e/2];
        return 2UL*enhanced_npc_words[index];
    }
    if(pose>=0x16/2 && pose<=0x1c/2){
        face=pose>=0x1a/2;
        if(slot==9)slot=13;
    }
    if(slot==1)slot=(pose==0x0e/2 || pose==0x14/2)?2:1;
    if(slot==5 || slot==6)face=1; /* Wall-facing poses have their own left/right hands. */
    if(slot==17)face=pose==0x42/2; /* $27A6: the latched pose selects the prone silhouette. */
    /* $27B8-$27BE selects pose $08 for death state 25. Keep the source
     * pose mapping (slot 14); a reaction override would hide the stiff pose. */
    const EnhancedView *f=&enhanced_bruce_views[slot*2+face];
    bounds[0]=f->left;bounds[1]=f->top;
    bounds[2]=bounds[0]+f->width;bounds[3]=f->top+f->height;
    return 2UL*f->words;
}

static void paint_enhanced_tile(const BlC64Paint *original){
    UWORD cell=original->cell,row=cell/40,col=cell-row*40;
    UBYTE code=bl_c64_screen(cell),tile=code&127;
    /* Leave the animated object blocks and the finale's palette effects
     * to the original painter. */
    if(enhanced_room>=18 || (tile>=0x61 && tile<=0x63)){
        paint_source_tile(original);return;
    }
    UBYTE sky=enhanced_room<=3 && row>=3 && row<11;
    UWORD tile_index=(row&3)*8+(col&7);
    const UBYTE *art=sky?fighter_dma+ENHANCED_TILE_BASE+((row-3)*40+col)*32:
        enhanced_wall_tiles+32*(UWORD)enhanced_wall_map[(enhanced_room<3?32:0)+tile_index];
    BlC64Paint request=*original;
    UBYTE stamp[32];
    if(ENHANCED_SOURCE_TRAPS && enhanced_room==13 && (tile&0x7c)==0x64 &&
       (original->rows==3 || original->rows==0xc0)){
        UWORD first=original->rows==3?0:6;
        const UBYTE *glyph=bl_c64_display_glyph(code);
        UBYTE *dest=original->bitmap+native_cell_offset[cell]+first*ROW_BYTES;
        wait_blitter();
        for(UWORD y=first;y<first+2;y++,dest+=ROW_BYTES){
            UBYTE pairs=(glyph[y]|(glyph[y]>>1))&0x55,mask=pairs|(pairs<<1);
            for(UWORD plane=0;plane<4;plane++){
                UWORD i=plane*8+y;
                dest[plane*40]=(original->planes[i]&mask)|(art[i]&~mask);
            }
        }
        return;
    }
    /* In room 4 the panorama continues behind the battlements. From row 7,
     * $09/$0A/$36 are tower stones, even where sky shows through the gaps. */
    if((sky && (enhanced_room<3 || row<7) && (tile==7 || tile==8 || (tile>=9 && tile<=12) || tile==14 ||
                tile==0x23 || (tile>=0x33 && tile<=0x37))) || tile==0){
        request.planes=art;
    }else{
        const UBYTE *glyph=bl_c64_display_glyph(code);
        UWORD group=enhanced_room<3?0:enhanced_room<10?256:512;
        /* Room 4's tower courses start at character row 7. Its skyline
         * uses some of the very same character codes above that row. */
        UWORD bank=(enhanced_room==3 && row>=7)?ENHANCED_TOWER_INDEX:group;
        UWORD id=enhanced_arch_index[bank+code];
        if(group==512){
            /* $2D/$2E share their glyphs. Room 17 init $359F writes
             * colour 7 at the two extra-life emblems; other copies are
             * white. Read live colour RAM, including each lower half. */
            if(tile==0x2d || tile==0x2e)
                id=enhanced_vault_detail_index[4+(bl_c64_screen_color(cell)==7?4:0)+2*(tile-0x2d)+(code>>7)];
            else if((enhanced_room==14 || enhanced_room==16) && row<=4 && (tile==0x43 || tile==0x45))
                id=enhanced_vault_detail_index[(tile==0x45?2:0)+(code>>7)];
        }
        /* The central crown, its brackets and the two side eaves. The same
         * $0C and $2F also occur on the side platforms and bottom floor. */
        if(enhanced_room==15 && row<=14 && col>=13 && col<=27 && tile<=0x2f){
            UWORD roof=enhanced_pagoda_index[2*tile+(code>>7)];
            if(roof)id=roof;
        }
        if(enhanced_room<10){
            if(code==0x93 || code==0xb1)id=enhanced_arch_index[ENHANCED_LAMP_INDEX+((glyph[2]>>4)&3)];
            if(code==0x94)id=enhanced_arch_index[ENHANCED_LAMP_INDEX+4+((glyph[2]>>2)&3)];
            if(code==0xe7 && group==256)id=enhanced_arch_index[ENHANCED_LAMP_INDEX+8+((glyph[2]>>2)&3)];
        }else if(code==0x93 || code==0x94){
            UBYTE left=code==0x93,shift=left?4:2;
            UBYTE phase=glyph[2]>>shift;
            if(phase<4 && glyph[2]==(phase<<shift))
                id=enhanced_arch_index[ENHANCED_VAULT_LAMP_INDEX+(left?0:4)+phase];
        }
        /* Architecture stamps live in CPU memory. Each includes the source rows it
         * replaces. A changed row (pickup, door, animated glyph) still uses
         * the live source until the matching artwork is displayed again. */
        const UWORD *offsets=id?enhanced_pair_offsets+(id-1)*4:0;
        for(UWORD y=0;y<8;y+=2){
            const UBYTE *pair=offsets?enhanced_arch_pairs+*offsets++:0;
            for(UWORD dy=0;dy<2;dy++){
                UBYTE bits=glyph[y+dy],keep;
                UBYTE painted=pair && pair[dy]==bits;
                if(painted)keep=pair[2+dy];
                else{
                    UBYTE occupied=(bits|(bits>>1))&0x55;
                    keep=occupied|(occupied<<1);
                }
                for(UWORD p=0;p<4;p++){
                    UWORD i=p*8+y+dy;
                    UBYTE ink=painted?pair[4+p*2+dy]:original->planes[i];
                    /* Vault spear $40/$C0 ($AA00/$AE00): source pair 2
                     * is colour 11 in room 12, also our masonry body ink.
                     * Lighten only its blade pixels; keep the live mounting
                     * cap, background and source contact mask unchanged. */
                    if(!painted && group==512 && tile==0x40){
                        UBYTE blade=(bits&~(bits<<1))&0xaa;
                        blade|=blade>>1;
                        ink=(ink&~blade)|(p==0?blade:0);
                    }
                    stamp[i]=(ink&keep)|(art[i]&~keep);
                }
            }
        }
        request.planes=stamp;
    }
    paint_source_tile(&request);
}
