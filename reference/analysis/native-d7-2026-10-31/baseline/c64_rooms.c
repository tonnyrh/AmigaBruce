#include "c64_rooms.h"
#include <stddef.h>

/* Frozen source data + state in CPU RAM. No C64 instruction fetch/decode.
 * Original IRQs/SID/VIC registers have no access to Amiga hardware here. */
#if defined(__GNUC__)
#define BL_VIC_ALIGNED __attribute__((aligned(4)))
#else
#define BL_VIC_ALIGNED
#endif
static unsigned char m[65536] BL_VIC_ALIGNED;
static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;
static unsigned char target_x,target_y,target_room;
static unsigned short revision,source_fault;
static unsigned short audio_requests_mask;
static void (*io_service)(void);
void bl_c64_set_service(void (*service)(void)){io_service=service;}
static void (*load_service)(long);
void bl_c64_set_load_service(void (*service)(long loading)){load_service=service;}
static unsigned short profile[16];
#if defined(__m68k__) && defined(BL_C64_PROFILE) && BL_C64_PROFILE
static unsigned long profile_clock(void){
    unsigned long hi,mid,lo,hi2,mid2;
    do{hi=*(volatile unsigned char*)0xbfda00;mid=*(volatile unsigned char*)0xbfd900;lo=*(volatile unsigned char*)0xbfd800;
       hi2=*(volatile unsigned char*)0xbfda00;mid2=*(volatile unsigned char*)0xbfd900;(void)*(volatile unsigned char*)0xbfd800;
    }while(hi!=hi2||mid!=mid2);
    return (hi<<16)|(mid<<8)|lo;
}
#define PROFILE_START(q) unsigned long q=profile_clock()
#define PROFILE_END(q,i) profile[i]+=(unsigned short)((profile_clock()-(q))&0xffffff)
typedef struct {
    unsigned long calls,total,self,maximum;
    unsigned short bins[BL_PERF_BINS];
    unsigned char room,state[3];
} SourcePerf;
static SourcePerf source_perf[BL_PERF_SLOTS];
static struct {unsigned long start,children;unsigned short slot;} perf_stack[12];
static unsigned char perf_depth;
static unsigned long perf_errors,perf_overhead_lines;
void bl_perf_begin(long slot){
    unsigned long stamp=profile_clock();
    if(perf_depth>=12){++perf_errors;return;}
    perf_stack[perf_depth].start=stamp;perf_stack[perf_depth].children=0;
    perf_stack[perf_depth++].slot=(unsigned short)slot;
}
void bl_perf_end(long slot){
    unsigned long stamp=profile_clock(),cost,self;unsigned short bin;SourcePerf *p;
    if(!perf_depth || perf_stack[perf_depth-1].slot!=slot){++perf_errors;return;}
    --perf_depth;cost=(stamp-perf_stack[perf_depth].start)&0xffffffUL;
    self=cost-perf_stack[perf_depth].children;
    if(perf_depth)perf_stack[perf_depth-1].children+=cost;
    p=&source_perf[slot];++p->calls;p->total+=cost;p->self+=self;
    /* Exact 0..15 lines, then 16-line buckets to255 and256-line buckets.
     * >=2304 is the overflow bucket. Histogram is exclusive work. */
    bin=self<16?(unsigned short)self:self<256?(unsigned short)(15+(self>>4)):
        self<2304?(unsigned short)(30+(self>>8)):39;
    if(p->bins[bin]!=65535)++p->bins[bin];
    if(cost>p->maximum){p->maximum=cost;p->room=m[0x29];p->state[0]=m[0xbf];p->state[1]=m[0xc0];p->state[2]=m[0xc1];}
}
void bl_perf_reset(void){
    unsigned short i;unsigned char *p=(unsigned char*)source_perf;
    for(i=0;i<sizeof(source_perf);i++)p[i]=0;
    perf_depth=0;perf_errors=0;
    {unsigned long start=profile_clock();
    for(i=0;i<32;i++){bl_perf_begin(BL_PERF_LOOP);bl_perf_end(BL_PERF_LOOP);}
    perf_overhead_lines=(profile_clock()-start)&0xffffffUL;}
    for(i=0;i<sizeof(source_perf);i++)p[i]=0;
}
unsigned long bl_perf_value(long slot,long field){
    SourcePerf *p;if(slot<0)return field?perf_overhead_lines:perf_errors;
    p=&source_perf[slot];
    if(field==0)return p->calls;
    if(field==1)return p->total;
    if(field==2)return p->self;
    if(field==3)return p->maximum;
    if(field==4)return ((unsigned long)p->room<<24)|((unsigned long)p->state[0]<<16)|((unsigned long)p->state[1]<<8)|p->state[2];
    return p->bins[field-5];
}
#else
#define PROFILE_START(q) ((void)0)
#define PROFILE_END(q,i) ((void)0)
#endif
void bl_c64_profile_reset(void){unsigned char i;for(i=0;i<16;i++)profile[i]=0;}
unsigned short bl_c64_profile(long item){return profile[item&15];}
void bl_c64_profile_add(long item,long lines){profile[item&15]+=(unsigned short)lines;}
static union {unsigned char bytes[1000];unsigned long words[250];} cell_dirt;
static union {unsigned char bytes[256];unsigned long words[64];} glyph_dirt;
#define dirty_cells cell_dirt.bytes
#define dirty_glyphs glyph_dirt.bytes
static unsigned char display_dirty,old_bank,paint_bank=255;
static unsigned short paint_list[880],paint_count,paint_cursor;
static unsigned short animation_fallback[880],animation_fallback_count;
static unsigned char animation_pending,animation_fallback_dirty;
static unsigned char paint_queued[1000];
static unsigned char paint_rows[1000],flash_cells[1000],flash_changed;
static unsigned short cell_offsets[1000];
static unsigned char cell_y[1000];
static unsigned long cell_word_mask[1000],part_words[25];
static unsigned char part_rows[25];
static unsigned long part_priority_words[25];
static unsigned char part_priority_rows[25];
typedef struct {
    unsigned long tag;
    unsigned short generation,epoch;
    unsigned char planes[4][8];
} CharacterCache;
static CharacterCache character_cache[1024];
static unsigned short cell_cache[1000];
static unsigned char *cell_stamp[1000];
static unsigned short cache_references[1024];
static BlC64Painter tile_painter;
static BlC64Paint paint_request;
void bl_c64_set_painter(BlC64Painter painter){tile_painter=painter;}
typedef struct {unsigned short left,right,top,bottom;unsigned long offset,size,words;unsigned char group;} AnimationRect;
static AnimationRect animation_rects[128];
static unsigned short animation_count,animation_cell[1000];
static unsigned char animation_code[1000],animation_color[1000],animation_done[128];
static unsigned char animation_mismatch[1000],animation_started,animation_ready,animation_part;
static unsigned short animation_differences[128];
static unsigned char animation_pattern[24],animation_phase_valid;
static unsigned char animation_variants[8][48];
static unsigned short animation_checked_revision;
static unsigned char *animation_cache;
static BlC64BlockPainter block_painter;
void bl_c64_set_block_painter(BlC64BlockPainter painter){block_painter=painter;}
#if defined(__GNUC__)
__attribute__((noinline,noclone))
#else
__declspec(noinline)
#endif
static void animation_cell_changed_active(unsigned short cell){
    unsigned short item;unsigned char mismatch;
    if((m[0x8c00 + cell]&127)>=0x61 && (m[0x8c00 + cell]&127)<=0x63)animation_fallback_dirty=1;
    if((item=animation_cell[cell])==65535)return;
    animation_fallback_dirty=1;
    mismatch=(unsigned char)(m[0x8c00 + cell]!=animation_code[cell] || (m[0xd800 + cell]&7)!=animation_color[cell]);
    if(mismatch!=animation_mismatch[cell]){
        if(mismatch)++animation_differences[item];else --animation_differences[item];
        animation_mismatch[cell]=mismatch;
    }
}
#if defined(__GNUC__)
static inline __attribute__((always_inline))
#else
static __forceinline
#endif
void animation_cell_changed(unsigned short cell){
    if(animation_count)animation_cell_changed_active(cell);
}
static void rebuild_animation_fallback(void){
    unsigned short cell;animation_fallback_count=0;animation_fallback_dirty=0;
    if(!animation_count)return;
    for(cell=120;cell<1000;cell++){
        unsigned char code=m[0x8c00 + cell]&127;unsigned short item=animation_cell[cell];
        if(code>=0x61 && code<=0x63 && (item==65535 || animation_differences[item]))animation_fallback[animation_fallback_count++]=cell;
    }
}
static void release_cell_cache(unsigned short cell){
    if(cell_cache[cell]!=65535){--cache_references[cell_cache[cell]];cell_cache[cell]=65535;}
    cell_stamp[cell]=0;
}
static unsigned short glyph_epoch[256];
static unsigned char glyph_changes[256],glyph_changed_list[256];
static unsigned short glyph_changed_count;
static unsigned short glyph_head[256],glyph_next[1000],glyph_previous[1000];
static unsigned char glyph_index_dirty[256];
/* $40BC-$4132 absolute writes; $2CF1-$2D54 rotating glyphs.
 * Other codes retain a correct lazy index, rebuilt if they actually change. */
static unsigned char glyph_tracking[256];
static unsigned char indexed_screen[1000],indexed_color[1000],index_ready;
static unsigned char indexed_glyph[2048];
static unsigned short charset(void);
#if BL_ROOM_REUSE
/* Base colors depend on the palette; foreground bits do not. Splitting
 * their disjoint masks saves23552 CPU-RAM bytes and eight repeated base
 * writes per byte whenever a new palette is prepared. */
static unsigned long planar_base[4][256],planar_foreground[9][256];
static const unsigned long source_color_planes[16]={
    0x00000000UL,0xff000000UL,0x00ff0000UL,0xffff0000UL,
    0x0000ff00UL,0xff00ff00UL,0x00ffff00UL,0xffffff00UL,
    0x000000ffUL,0xff0000ffUL,0x00ff00ffUL,0xffff00ffUL,
    0x0000ffffUL,0xff00ffffUL,0x00ffffffUL,0xffffffffUL};
#define PLANAR_WORD(b,c,p) (planar_base[b][p]|planar_foreground[c][p])
#else
static unsigned long planar_lut[4][9][256];
#define PLANAR_WORD(b,c,p) planar_lut[b][c][p]
#endif
static unsigned char line_band[200],line_colors[200][3];
static unsigned char coverage_ready,palette_ready,palette_key[12];
static unsigned short reuse_stats[4]; /* palette hit/miss, animation hit/miss */
static unsigned short animation_saved_count;
static unsigned long animation_saved_bytes;
static unsigned char animation_saved_palette[12],animation_saved_bands[200];
void bl_c64_reuse_reset(void){unsigned char i;for(i=0;i<4;i++)reuse_stats[i]=0;}
unsigned short bl_c64_reuse_stat(long i){return reuse_stats[i&3];}
static void prepare_palette(void);
static unsigned char contact_bitmap[8000],contact_cells[1000];
/* Safe actor masks contain full two-bit pairs. Four class lanes need four
 * bits each, so a word preserves the same contacts as the former long. */
static unsigned short contact_coverage[8000],coverage_table[2][256],spread_masks[256];
static unsigned short contact_bank,contact_epoch[1000];
static unsigned char contact_classes[2][256],constant_masks[5][4][21][3];
static unsigned char constant_poses[5],constant_classes[35],constant_bands[5];
static unsigned short constant_ages[5];
typedef struct {int x,y;unsigned char pose,room,all,body,valid,view_count;unsigned short generation,used,view[16],view_epoch[16];} ContactCache;
static ContactCache contact_cache[8];
static unsigned short contact_generation,contact_checked_revision,contact_use;
static unsigned char contact_last;
static void reset_contact_masks(void){
    unsigned char i;
    for(i=0;i<5;i++){constant_poses[i]=255;constant_ages[i]=0;constant_bands[i]=0;}
    for(i=0;i<35;i++)constant_classes[i]=0;
    for(i=0;i<8;i++)contact_cache[i].valid=0;
}
static void invalidate_contacts(void){
    unsigned char slot;
    if(contact_checked_revision==revision)return;
    PROFILE_START(invalidation_start);
    for(slot=0;slot<8;slot++)if(contact_cache[slot].valid && contact_cache[slot].generation==contact_generation && contact_cache[slot].room==loaded){
        unsigned char index;
        for(index=0;index<contact_cache[slot].view_count;index++){
            unsigned short cell=contact_cache[slot].view[index];
            if(dirty_cells[cell] || contact_cache[slot].view_epoch[index]!=glyph_epoch[indexed_screen[cell]] || (flash_changed&&flash_cells[cell]) || old_bank!=m[0xf2]){contact_cache[slot].valid=0;break;}
        }
    }
    contact_checked_revision=revision;
    PROFILE_END(invalidation_start,7);
}

static void mark_cell(unsigned short cell,unsigned char pixels,unsigned char rows){
    dirty_cells[cell]=1;
    if(!paint_queued[cell]){paint_queued[cell]=1;paint_list[paint_count++]=cell;}
    else if(paint_queued[cell]==2)paint_queued[cell]=3;
    /* 1=pending,2=consumed,3=changed again after consumption. Keep one
     * unique queue slot per source cell; clear_dirty carries state3. */
    display_dirty=1;paint_rows[cell]|=rows;
    if(pixels)contact_cells[cell]=1;
}
static void index_screen(void){
    unsigned short cell;for(cell=0;cell<256;cell++){glyph_head[cell]=65535;glyph_index_dirty[cell]=0;}
    for(cell=120;cell<1000;cell++){
        unsigned char code=m[0x8c00 + cell];unsigned short next=glyph_head[code];
        indexed_screen[cell]=code;indexed_color[cell]=m[0xd800 + cell]&15;
        glyph_next[cell]=next;glyph_previous[cell]=65535;
        if(next!=65535)glyph_previous[next]=cell;
        glyph_head[code]=cell;
    }
    for(cell=0;cell<2048;cell++)indexed_glyph[cell]=m[charset()+cell];
    index_ready=1;
}
static unsigned short glyph_first(unsigned char code){
    if(glyph_index_dirty[code]){
        unsigned short cell,head=65535;
        for(cell=120;cell<1000;cell++)if(indexed_screen[cell]==code){
            glyph_next[cell]=head;glyph_previous[cell]=65535;
            if(head!=65535)glyph_previous[head]=cell;
            head=cell;
        }
        glyph_head[code]=head;glyph_index_dirty[code]=0;
    }
    return glyph_head[code];
}
static void source_written(unsigned short address){
    /* A442-cell stream can reach mask0. Invalidate mask validation/cache
     * independently of glyphs if a source write changes mask storage. */
    if(address>=0x9000 && address<0x9a20){reset_contact_masks();return;}
    if(!index_ready)return;
    if(address>=0x8c78&&address<0x8fe8){
        unsigned short cell=address-0x8c00,prev,next;unsigned char code=m[address],old=indexed_screen[cell];
        unsigned char tracking=(unsigned char)(m[0xf2]==0x38?1:m[0xf2]==0x3a?2:0);
        if(old==code)return;
        if(glyph_tracking[old]&tracking){
            (void)glyph_first(old);prev=glyph_previous[cell];next=glyph_next[cell];
            if(prev==65535)glyph_head[old]=next;else glyph_next[prev]=next;
            if(next!=65535)glyph_previous[next]=prev;
        }else glyph_index_dirty[old]=1;
        if(glyph_tracking[code]&tracking){
            next=glyph_first(code);glyph_next[cell]=next;glyph_previous[cell]=65535;
            if(next!=65535)glyph_previous[next]=cell;
            glyph_head[code]=cell;
        }else glyph_index_dirty[code]=1;
        if(animation_count && (((code&127)>=0x61&&(code&127)<=0x63)||((old&127)>=0x61&&(old&127)<=0x63)))animation_fallback_dirty=1;
        indexed_screen[cell]=code;release_cell_cache(cell);animation_cell_changed(cell);mark_cell(cell,1,255);
    }else if(address>=0xd878&&address<0xdbe8){
        unsigned short cell=address-0xd800;unsigned char color=m[address]&15;
        if(color!=indexed_color[cell]){
            unsigned char physical=(unsigned char)(((color&7)==0)!=((indexed_color[cell]&7)==0));
            indexed_color[cell]=color;release_cell_cache(cell);animation_cell_changed(cell);
            if(loaded==19 && flash_cells[cell]){
                flash_changed=1;display_dirty=1;
                if(physical)contact_cells[cell]=1;
            }
            else mark_cell(cell,physical,255);
        }
    }else if(address>=0xa000&&address<0xc000 && (address&0xf800)==charset()){
        unsigned char code=(unsigned char)((address&2047)>>3);
        if(indexed_glyph[address&2047]==m[address])return;
        indexed_glyph[address&2047]=m[address];
        if(!glyph_changes[code]){
            glyph_changed_list[glyph_changed_count++]=code;
            if(++glyph_epoch[code]==0){unsigned short item;for(item=0;item<1024;item++)character_cache[item].epoch=65535;}
        }
        glyph_changes[code]|=(unsigned char)(1u<<(address&7));
    }
}
static void flush_glyph_changes(void){
    unsigned short item;for(item=0;item<glyph_changed_count;item++){
        unsigned char code=glyph_changed_list[item],rows=glyph_changes[code];unsigned short cell;
        if(animation_count && (code&127)>=0x61 && (code&127)<=0x63){
            animation_pending=1;display_dirty=1;
            if(!animation_fallback_dirty){unsigned short probe;for(probe=0;probe<animation_fallback_count;probe++){
                cell=animation_fallback[probe];if(indexed_screen[cell]==code)mark_cell(cell,0,rows);
            }}
        }else{
            cell=glyph_first(code);while(cell!=65535){mark_cell(cell,0,rows);cell=glyph_next[cell];}
        }
        glyph_changes[code]=0;
    }
    glyph_changed_count=0;
}

#define NZ(q) do{z=((unsigned char)(q)==0);n=(((unsigned char)(q)&128)!=0);}while(0)
static unsigned short W(unsigned short p){return (unsigned short)(m[p]|((unsigned short)m[(unsigned short)(p+1)]<<8));}
static void adc(unsigned char q){
    unsigned short t=(unsigned short)a+q+c;unsigned char old=a;
    v=((~(old^q)&(old^t)&128)!=0);
    if(d){unsigned short lo=(old&15)+(q&15)+c;if(lo>9)t+=6;if(t>0x99)t+=0x60;}
    c=t>255;a=(unsigned char)t;NZ(a);
}
static void sbc(unsigned char q){
    unsigned short t=(unsigned short)a-q-(1-c);unsigned char old=a;
    v=(((old^q)&(old^t)&128)!=0);
    if(d){int lo=(old&15)-(q&15)-(1-c);int hi=(old>>4)-(q>>4);
        if(lo<0){lo-=6;--hi;}if(hi<0)hi-=6;
        a=(unsigned char)((hi<<4)|(lo&15));
    }else a=(unsigned char)t;
    c=t<256;NZ(a);
}
static void source_transition(unsigned char sx,unsigned char sy,unsigned char room){
    target_x=sx;target_y=sy;target_room=room;transition_pending=1;
}
#include "c64_actor_data.h"
#if defined(__GNUC__)
#define SOURCE_INLINE static inline __attribute__((always_inline))
#else
#define SOURCE_INLINE static __forceinline
#endif
#if defined(__GNUC__)
#define SOURCE_NOINLINE __attribute__((noinline,noclone))
#else
#define SOURCE_NOINLINE __declspec(noinline)
#endif
/* Color-only observer; all callers have already established index_ready and
 * the source $D878-$DBE7 range. Metadata effects match source_written. */
SOURCE_INLINE void source_color_written(unsigned short address){
        unsigned short cell=address-0xd800;unsigned char color=m[address]&15;
        if(color!=indexed_color[cell]){
            unsigned char physical=(unsigned char)(((color&7)==0)!=((indexed_color[cell]&7)==0));
            indexed_color[cell]=color;release_cell_cache(cell);
            /* The active observer has no effect without either an animated
             * glyph or a cached animation-cell membership. Keep its exact
             * body for all cells for which it can change metadata. */
            if(animation_count){
                unsigned char code=m[0x8c00 + cell]&127;
                if((code>=0x61 && code<=0x63) || animation_cell[cell]!=65535)
                    animation_cell_changed_active(cell);
            }
            if(loaded==19 && flash_cells[cell]){
                flash_changed=1;display_dirty=1;
                if(physical)contact_cells[cell]=1;
            }
            else mark_cell(cell,physical,255);
        }
}
/* Source $42A1-$42BA: eight stores per descending column, no IRQ/service
 * seam. The original DEX leaves X=$FF,N=1,Z=0; A/Y/C/V/D/SP are unchanged.
 * Entry guard in the generator retains the original path for X>$1C. */
static SOURCE_NOINLINE void source_final_colors(void){
    unsigned char column=x,row,value=a,ready=index_ready;
    do{
        unsigned short address=(unsigned short)(0xdaac+column);
        for(row=0;row<8;row++){
            m[address]=value;if(ready)source_color_written(address);
            address+=40;
        }
    }while(--column<128);
    x=column;z=0;n=1;
}
/* Native decoding of $17E2-$1817 and its $1A67 helper. Preserve source RAM,
 * source stack bytes, registers and terminating CMP flags, without paying a
 * generic native subroutine dispatch for every character in a room string. */
SOURCE_INLINE void source_string(void){
    PROFILE_START(string_start);
    unsigned char original=a,yy=y;unsigned short pointer,address,upper,lower;
    m[0x100 + sp--]=a;m[0x100 + sp--]=0x17;m[0x100 + sp--]=0xe5;
    m[4]=m[0x4338 + x];m[5]=m[0x434c + x];m[8]=m[0x4360 + x];m[9]=m[0x4374 + x];
    if(m[0x100]){m[8]=0;m[9]=0xce;}
    sp+=2;a=m[0x100 + (unsigned char)++sp];
    a=(unsigned char)(original<<1);x=a;
    pointer=(unsigned short)((m[0x43be + x]|((unsigned short)m[0x43bf + x]<<8))-y);
    m[6]=(unsigned char)pointer;m[7]=(unsigned char)(pointer>>8);
    upper=W(4);lower=W(8);
    for(;;){
        unsigned char code=(unsigned char)(m[(unsigned short)(pointer+yy)]-32);
        if(code==128){a=128;y=yy;c=1;z=1;n=v=0;sp+=2;PROFILE_END(string_start,8);return;}
        address=(unsigned short)(upper+yy);m[address]=code&127;source_written(address);
        address=(unsigned short)(lower+yy);m[address]=code|128;source_written(address);
        if(++yy==0){++m[5];++m[7];++m[9];pointer=W(6);upper=W(4);lower=W(8);}
    }
}
/* Decoded $2509-$255D, including source priority comparisons and stack return.
 * These are shadow SID queues; they never address Amiga hardware. */
SOURCE_INLINE void source_sound(void){
    PROFILE_START(sound_start);
    unsigned short queue,priority;
    if(y>=128 && y<=142)audio_requests_mask|=(unsigned short)(1U<<(y-128));
    m[0xd418]=0x15;
    a=m[0xeb00];NZ(a);
    if(!a){queue=0xeb00;priority=0x2581;}
    else{a=m[0xef70];NZ(a);
        if(!a){queue=0xef70;priority=0x2582;}
        else{a=m[0xf070];NZ(a);
            if(!a){queue=0xf070;priority=0x2583;}
            else{
                x=y&15;a=m[0x2572 + x];NZ(a);
                c=a>=m[0x2581];NZ((unsigned char)(a-m[0x2581]));
                if(c){queue=0xeb00;priority=0x2581;}
                else{c=a>=m[0x2582];NZ((unsigned char)(a-m[0x2582]));
                    if(c){queue=0xef70;priority=0x2582;}
                    else{c=a>=m[0x2583];NZ((unsigned char)(a-m[0x2583]));
                        if(!c){sp+=2;PROFILE_END(sound_start,10);return;}
                        queue=0xf070;priority=0x2583;
                    }
                }
            }
        }
    }
    m[queue]=y;x=y&15;a=m[0x2572 + x];m[priority]=a;NZ(a);sp+=2;PROFILE_END(sound_start,10);
}
#include "c64_sfx.h"
/* Decoded $104B-$10B4 + $404E-$407C. Original moving-cell positions,
 * wrapping tests, string IDs, call-return bytes and final flags are retained. */
static void source_movers(void){
    PROFILE_START(movers_start);
    unsigned char reverse,special;unsigned short ret;
    x=8;
    do{
        a=m[0x10f + x];NZ(a);
        if(a){
            reverse=a&128;
            m[0x100 + sp--]=x;
            m[0x12d + x]=m[0x70]=m[0x119 + x];m[0x6f]=m[0x123 + x];
            if(reverse){
                a=++m[0x119 + x];c=a>=m[0x141 + x];
                if(c)a=m[0x119 + x]=m[0x137 + x];
            }else{
                a=--m[0x119 + x];c=a>=m[0x137 + x];
                if(!c)a=m[0x119 + x]=m[0x141 + x];
            }
            m[0x6e]=a;special=(unsigned char)(m[0x6f]==5 || m[0x6f]==10);
            ret=special?0x108b:reverse?0x10ae:0x1085;
            m[0x100 + sp--]=(unsigned char)(ret>>8);m[0x100 + sp--]=(unsigned char)ret;
            ret=special?0x4065:0x4050;
            m[0x100 + sp--]=(unsigned char)(ret>>8);m[0x100 + sp--]=(unsigned char)ret;
            y=0x89;source_sound();
            a=special?0x55:0x1c;x=m[0x6f];y=m[0x70];ret=special?0x406e:0x4059;
            m[0x100 + sp--]=(unsigned char)(ret>>8);m[0x100 + sp--]=(unsigned char)ret;
            source_string();
            a=special?0x54:0x1b;x=m[0x6f];y=m[0x6e];source_string();
            a=m[0x100 + (unsigned char)++sp];x=a;
        }
        --x;NZ(x);
    }while(!(x&128));
    sp+=2;PROFILE_END(movers_start,9);
}
/* Decoded $2CF1-$2D54. Valid source phases0..7, binary arithmetic only;
 * the generated instruction path remains available for other inputs. */
static void source_animation(void){
    unsigned short table=W(0x7d),column,row,base,address,bank=charset();
    unsigned char value=0,code,changed,high=(unsigned char)(m[0x7c]+3);
    for(column=0;column<3;column++){
        base=(unsigned short)(((unsigned short)high<<8)+8+column*8);
        for(row=0;row<8;row++){
            value=m[(unsigned short)(table+column*8+((m[0x64]+row)&7))];
            address=(unsigned short)(base+(row<4?row*2:1024+(row-4)*2));
            m[address]=value;m[(unsigned short)(address+1)]=value;
        }
    }
    if(index_ready && bank==((unsigned short)m[0x7c]<<8))for(column=0;column<6;column++){
        code=(unsigned char)(0x61 + column%3+(column>=3?128:0));changed=0;
        for(row=0;row<8;row++){
            unsigned short offset=(unsigned short)(((unsigned short)code<<3)+row);
            value=m[bank+offset];if(indexed_glyph[offset]!=value){indexed_glyph[offset]=value;changed|=(unsigned char)(1u<<row);}
        }
        if(changed){
            if(!glyph_changes[code]){
                glyph_changed_list[glyph_changed_count++]=code;
                if(++glyph_epoch[code]==0){unsigned short item;for(item=0;item<1024;item++)character_cache[item].epoch=65535;}
            }
            glyph_changes[code]|=changed;
        }
    }
    m[0x51]=0;m[0x2d2c]=m[0x7d];m[0x2d2d]=m[0x7e];m[0x43bb]=3;m[0x43bc]=8;
    m[6]=12;m[7]=high;m[8]=8;m[9]=(unsigned char)(high+4);
    m[0x100 + sp]=0x2d;m[0x100 + (unsigned char)(sp-1)]=0x40;sp+=2;
    a=m[(unsigned short)(table+((m[0x64]+7)&7))];x=255;y=8;c=1;z=0;n=1;
    v=(unsigned char)((~(high^4)&(high^(unsigned char)(high+4))&128)!=0);
}
/* Complete source actor/world chain. Legacy adapter APIs below remain for
 * historical controls; the live session uses bl_c64_world_* exclusively. */
static unsigned short actor_return,actor_life_events,actor_spawn_events;
static unsigned char actor_life_pending,actor_reset_pending,actor_preparing,actor_i;
static unsigned char actor_gameover_pending,actor_legacy_load,actor_infinite,actor_invincible,actor_loading_pending;
static unsigned char actor_irq_stop,actor_world_enabled,actor_input,actor_yamo_input,actor_debug_target=255;
static unsigned short actor_logic_steps,actor_loading_epoch,actor_stop_pc;
static unsigned char actor_delay_pending;
static unsigned long vic_high[8][21],vic_low[8][21];
/* 64-byte stride keeps every cached sprite even for 68000 longword reads.
 * The source still compares exactly the first63 bytes. */
typedef struct {
    unsigned char bytes[8][64];
    unsigned short sx[8],sy[8];
    unsigned char layout[8],valid,collision_valid,active,tall,wide,bits,candidates,pairs[8];
} SourceVicRepeat;
static SourceVicRepeat vic_repeat BL_VIC_ALIGNED;
/* Fixed byte/word layout shared with vic_compare.s; no -mshort scalar ABI. */
typedef char SourceVicRepeatLayout[(sizeof(SourceVicRepeat)==568 && offsetof(SourceVicRepeat,sx)==512 && offsetof(SourceVicRepeat,sy)==528 && offsetof(SourceVicRepeat,layout)==544 && offsetof(SourceVicRepeat,valid)==552 && offsetof(SourceVicRepeat,collision_valid)==553 && offsetof(SourceVicRepeat,active)==554 && offsetof(SourceVicRepeat,tall)==555 && offsetof(SourceVicRepeat,wide)==556 && offsetof(SourceVicRepeat,bits)==557 && offsetof(SourceVicRepeat,candidates)==558 && offsetof(SourceVicRepeat,pairs)==559)?1:-1];
#define vic_bytes vic_repeat.bytes
#define vic_last_x vic_repeat.sx
#define vic_last_y vic_repeat.sy
#define vic_layout vic_repeat.layout
#define vic_valid vic_repeat.valid
#define vic_collision_valid vic_repeat.collision_valid
#define vic_last_active vic_repeat.active
#define vic_last_tall vic_repeat.tall
#define vic_last_wide vic_repeat.wide
#define vic_last_bits vic_repeat.bits
#define vic_last_candidates vic_repeat.candidates
#define vic_last_pairs vic_repeat.pairs
#if !defined(__m68k__) || (defined(BL_AUTOTEST) && BL_AUTOTEST && defined(BL_SOURCE_PERF_TEST) && BL_SOURCE_PERF_TEST && !BL_C64_PROFILE)
/* Exact repeat predicate, also an independent portable native-test reference.
 * Only the accumulated latch can be written; a miss has no side effects. */
static unsigned long source_vic_repeat_c(unsigned char *ram,const SourceVicRepeat *q){
    unsigned char i,k,active=ram[0xd015],layout;
    unsigned short bank,matrix,pointer,sx;
    if(!q->collision_valid || q->active!=active || q->tall!=ram[0xd017] || q->wide!=ram[0xd01d])return 0;
    for(i=0;i<8;i++)if(active&(1<<i)){
        sx=(unsigned short)(ram[0xd000+i*2]+((ram[0xd010]&(1<<i))?256:0));
        if(q->sx[i]!=sx || q->sy[i]!=ram[0xd001+i*2])return 0;
    }
    if(q->candidates){
        if((q->valid&q->candidates)!=q->candidates)return 0;
        bank=(unsigned short)(((~ram[0xdd00])&3)<<14);matrix=(unsigned short)(bank+((unsigned short)(ram[0xd018]>>4)<<10));
        for(i=0;i<8;i++)if(q->candidates&(1<<i)){
            layout=(unsigned char)(((ram[0xd01c]&(1<<i))?1:0)|((ram[0xd01d]&(1<<i))?2:0));
            if(q->layout[i]!=layout)return 0;
            pointer=(unsigned short)(bank+((unsigned short)ram[(unsigned short)(matrix+0x3f8+i)]<<6));
            for(k=0;k<63;k++)if(q->bytes[i][k]!=ram[(unsigned short)(pointer+k)])return 0;
        }
    }
    ram[0xd01e]|=q->bits;return 1;
}
#endif
#if defined(__m68k__)
extern unsigned long bl_vic_repeat(unsigned char *ram,const SourceVicRepeat *q);
#endif

#if defined(__m68k__)
extern unsigned char bl_vic_equal63(const unsigned char *before,const unsigned char *current);
#if defined(BL_AUTOTEST) && BL_AUTOTEST
#if BL_C64_VIC_REPEAT_CASES
static unsigned short source_vic_repeat_selftest(void){
    static SourceVicRepeat q BL_VIC_ALIGNED;
    unsigned short test,i,k,bank,matrix,pointer,errors=0;unsigned char first,second,active,kind,mask,latch,wanted_latch;
    unsigned long wanted,actual;unsigned char original[sizeof(SourceVicRepeat)];
    if(((unsigned long)&q&3)||((unsigned long)m&3))++errors;
    for(test=0;test<BL_C64_VIC_REPEAT_CASES;test++){
        first=(unsigned char)(test&7);second=(unsigned char)((first+1)&7);mask=(unsigned char)(1<<first);
        active=(unsigned char)((test<1024 && (test&64))?255:mask|(1<<second));
        if(test<8)active=0; /* empty active set, cached zero and accumulated external latch bits */
        m[0xd015]=active;m[0xd010]=(unsigned char)(test*29);m[0xd017]=(unsigned char)(test*19);
        m[0xd01d]=(unsigned char)(test*37);m[0xd01c]=(unsigned char)(test*13);
        m[0xdd00]=(unsigned char)(test&3);m[0xd018]=(unsigned char)(((test>>2)&15)<<4);
        bank=(unsigned short)(((~m[0xdd00])&3)<<14);matrix=(unsigned short)(bank+((unsigned short)(m[0xd018]>>4)<<10));
        q.valid=active;q.collision_valid=1;q.active=active;q.tall=m[0xd017];q.wide=m[0xd01d];
        q.candidates=(unsigned char)((!active || (test<1024 && (test&128)))?0:mask|(1<<second));
        q.bits=q.candidates?((test&256)?q.candidates:0):0;
        for(i=0;i<8;i++){
            m[0xd000+i*2]=(unsigned char)(100+i*3);m[0xd001+i*2]=(unsigned char)(60+i);
            q.sx[i]=(unsigned short)(m[0xd000+i*2]+((m[0xd010]&(1<<i))?256:0));q.sy[i]=m[0xd001+i*2];
            q.layout[i]=(unsigned char)(((m[0xd01c]&(1<<i))?1:0)|((m[0xd01d]&(1<<i))?2:0));q.pairs[i]=0;
            m[(unsigned short)(matrix+0x3f8+i)]=(unsigned char)(128+i);pointer=(unsigned short)(bank+(128+i)*64);
            for(k=0;k<63;k++)m[pointer+k]=q.bytes[i][k]=(unsigned char)(test*11+i*17+k*31);
            m[pointer+63]=0xa5;q.bytes[i][63]=0x5a;
        }
        pointer=(unsigned short)(bank+(128+first)*64);
        if(test>=1024)m[pointer+((test-1024)>>3)]^=0x80; /* all63 bytes + ignored padding for all8 sprites */
        else{
            kind=(unsigned char)((test>>3)&15);
            if(kind==1)m[0xd015]^=mask;
            else if(kind==2)m[0xd017]^=mask;
            else if(kind==3)m[0xd01d]^=mask;
            else if(kind==4)++m[0xd000+first*2];
            else if(kind==5)m[0xd010]^=mask;
            else if(kind==6)++m[0xd001+first*2];
            else if(kind==7)m[0xd01c]^=mask;
            else if(kind==8)m[pointer]^=0x80;
            else if(kind==9)m[pointer+62]^=0x80;
            else if(kind==10)m[pointer+63]^=0x80;
            else if(kind==11){
                m[(unsigned short)(matrix+0x3f8+first)]=(unsigned char)(144+first);pointer=(unsigned short)(bank+(144+first)*64);
                for(k=0;k<63;k++)m[pointer+k]=q.bytes[first][k];
            }else if(kind==12){
                m[0xdd00]^=1;bank=(unsigned short)(((~m[0xdd00])&3)<<14);matrix=(unsigned short)(bank+((unsigned short)(m[0xd018]>>4)<<10));
                for(i=0;i<8;i++){
                    m[(unsigned short)(matrix+0x3f8+i)]=(unsigned char)(128+i);pointer=(unsigned short)(bank+(128+i)*64);
                    for(k=0;k<63;k++)m[pointer+k]=q.bytes[i][k];
                }
            }else if(kind==13)m[(unsigned short)(bank+(128+((first+2)&7))*64)]^=0x80;
            else if(kind==14)q.valid&=(unsigned char)~mask;
            else if(kind==15)q.collision_valid=0;
        }
        latch=(unsigned char)(test*7);m[0xd01e]=latch;
        for(k=0;k<sizeof(q);k++)original[k]=((const unsigned char*)&q)[k];
        wanted=source_vic_repeat_c(m,&q);wanted_latch=m[0xd01e];m[0xd01e]=latch;
        actual=bl_vic_repeat(m,&q);
        if(actual!=wanted || m[0xd01e]!=wanted_latch)++errors;
        for(k=0;k<sizeof(q);k++)if(original[k]!=((const unsigned char*)&q)[k]){++errors;break;}
    }
    return errors;
}
#endif
unsigned short bl_c64_vic_compare_selftest(void){
    static unsigned char before[64] BL_VIC_ALIGNED,current[64] BL_VIC_ALIGNED;
    unsigned short i,errors=0;
    if(((unsigned long)before&3)||((unsigned long)current&3)||((unsigned long)m&3)||((unsigned long)vic_bytes&3))++errors;
    for(i=0;i<64;i++)before[i]=current[i]=(unsigned char)(13+i*17);
    if(bl_vic_equal63(before,current)!=1)++errors;
    for(i=0;i<63;i++){
        current[i]^=0x80;
        if(bl_vic_equal63(before,current)!=0)++errors;
        current[i]^=0x80;
    }
    current[63]^=0x80;
    if(bl_vic_equal63(before,current)!=1)++errors;
#if BL_C64_VIC_REPEAT_CASES
    errors+=source_vic_repeat_selftest();
#endif
    return errors;
}
#endif
#endif
static void source_actor_loading_begin(void);
static void source_actor_loading_end(void);
static void source_actor_field(void);
static unsigned char source_vic_read(void){unsigned char latch=m[0xd01e];if(actor_world_enabled)m[0xd01e]=0;return latch;}
static void actor_code(unsigned short entry);
static void room_code(unsigned short entry){PERF_BEGIN(BL_PERF_ROOM);actor_code(entry);PERF_END(BL_PERF_ROOM);}
static unsigned short source_stack_return(void){
    return (unsigned short)((m[0x100 + (unsigned char)(sp-1)]|
        ((unsigned short)m[0x100 + sp]<<8))+1);
}
/* Decoded $26A0-$2702 and $52AD-$5309 hot loops. These retain scratch RAM,
 * stack, final flags and source self-modifying operands, not just pixels. */
static void source_sprite_copy_c(void){
    unsigned char remaining=63,wide=(unsigned char)!z,value;
    unsigned short dest=W(0x0e),first=W(0x26ab),left=W(0x26e4),right=W(0x26ee);
    m[0x277f]=remaining;
    if(!wide){
        x=m[0xe0 + x];
        for(;;){
            m[(unsigned short)(dest+y)]=m[(unsigned short)(first+x)];--remaining;m[0x277f]=remaining;--x;
            if(x&128)break;
            --y;m[(unsigned short)(dest+y)]=0;--remaining;m[0x277f]=remaining;
            --y;m[(unsigned short)(dest+y)]=0;--remaining;m[0x277f]=remaining;--y;if(y&128)break;
        }
    }else{
        value=m[0xe0 + x];c=value>>7;x=(unsigned char)(value*2-1);y-=2;
        for(;;){
            m[(unsigned short)(dest+y)]=m[(unsigned short)(left+x)];--remaining;m[0x277f]=remaining;--x;--y;
            m[(unsigned short)(dest+y)]=m[(unsigned short)(right+x)];--remaining;m[0x277f]=remaining;--x;
            if(x&128)break;
            --y;m[(unsigned short)(dest+y)]=0;--remaining;m[0x277f]=remaining;--y;
            if(y&128){source_fault=0x2703;return;}
        }
    }
    y=(unsigned char)(remaining^63);
    do{m[(unsigned short)(dest+y++)]=0;--remaining;m[0x277f]=remaining;}while(!(remaining&128));
    m[0x277f]=remaining;a=0;z=0;n=1;sp+=2;
}
typedef struct {
    unsigned short dest,first,left,right;
    unsigned char xx,yy,wide,carry;
} SourceSpriteCopy;
typedef char SourceSpriteCopyLayout[(sizeof(SourceSpriteCopy)==12 && offsetof(SourceSpriteCopy,xx)==8)?1:-1];
#if defined(__m68k__)
extern void bl_sprite_copy(unsigned char *ram,SourceSpriteCopy *q);
#endif
/* Source pointers/operands and count scratch must not be overwritten by
 * destination writes. Unusual low/straddling destinations use source code. */
static unsigned char source_sprite_copy(void){
    unsigned short dest=W(0x0e);unsigned char height=m[0xe0+x];
    if(dest<0x8000 || dest>0xff00 || (!z && y!=(unsigned char)(height*3)))return 0;
#if defined(__m68k__)
    SourceSpriteCopy q;
    q.dest=dest;q.first=W(0x26ab);q.left=W(0x26e4);q.right=W(0x26ee);
    if(q.first<=0xff00 && q.left<=0xff00 && q.right<=0xff00){
        q.xx=height;q.yy=y;q.wide=(unsigned char)!z;q.carry=c;
        bl_sprite_copy(m,&q);x=q.xx;y=q.yy;c=q.carry;
        a=0;z=0;n=1;sp+=2;return 1;
    }
    return 0;
#else
    source_sprite_copy_c();return 1;
#endif
}

#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static void source_contact_align_c(void){
    unsigned char row,shift,left,middle,right,last,offset=m[0x1c],phase=m[0x1b];unsigned short pointer=W(0x52cc);
    for(row=0;row<offset;row++)m[0xcae0 + row]=0;
    if(phase==3){for(row=0;row<32;row++)m[0xcae0 + offset+row]=0;offset+=32;}
    for(row=0;row<96;row++)m[0xcae0 + offset+row]=m[(unsigned short)(pointer+row)];
    if(!phase){a=0;x=96;y=(unsigned char)(offset+96);c=1;z=1;n=0;sp+=2;return;}
    /* $52E3-$5307: rows are independent. Fold the2/4 complete shift passes
     * into one pass; carry at exit is from row0 in the final source pass.
     * The preceding forward copy retains source/destination alias behavior. */
    if(phase==3){
        for(row=32;row--;){
            left=m[0xcae0 + row];middle=m[0xcb00 + row];right=m[0xcb20 + row];last=m[0xcb40 + row];
            m[0xcae0 + row]=(unsigned char)((left<<2)|(middle>>6));
            m[0xcb00 + row]=(unsigned char)((middle<<2)|(right>>6));
            m[0xcb20 + row]=(unsigned char)((right<<2)|(last>>6));m[0xcb40 + row]=(unsigned char)(last<<2);
            c=(left>>6)&1;
        }
        a=3;
    }else{
        a=shift=(unsigned char)(phase<<1);
        for(row=32;row--;){
            left=m[0xcae0 + row];middle=m[0xcb00 + row];right=m[0xcb20 + row];
            m[0xcae0 + row]=(unsigned char)(left>>shift);
            m[0xcb00 + row]=(unsigned char)((middle>>shift)|(left<<(8-shift)));
            m[0xcb20 + row]=(unsigned char)((right>>shift)|(middle<<(8-shift)));
            c=(right>>(shift-1))&1;
        }
    }
    x=255;y=0;z=1;n=0;sp+=2;
}
/* $52AD-$5309: the packed 68000 kernel is valid only for the source
 * driver's phase0..3, offset0..7 and a nonwrapping 96-byte source span.
 * Other injected entries retain the byte-ordered C path. No I/O service
 * observes the copy/shift interiors; all source bytes and exit flags stay. */
#if defined(__m68k__)
extern unsigned long bl_contact_align4(unsigned char *ram,unsigned long pointer,unsigned long phase,unsigned long offset);
#endif
static void source_contact_align(void){
#if defined(__m68k__)
    unsigned char phase=m[0x1b],offset=m[0x1c];unsigned short pointer=W(0x52cc);
    if(phase<4 && offset<8 && pointer<=0xffa0){
        c=(unsigned char)bl_contact_align4(m,pointer,phase,offset);
        if(!phase){a=0;x=96;y=(unsigned char)(offset+96);}
        else{a=phase==3?3:(unsigned char)(phase<<1);x=255;y=0;}
        z=1;n=0;sp+=2;return;
    }
#endif
    source_contact_align_c();
}
/* Keep a portable instruction-equivalent reference for host controls and
 * the separate extended native kernel test; not in the production Hunk. */
#if !defined(__m68k__) || (defined(BL_SOURCE_PERF_TEST) && BL_SOURCE_PERF_TEST && (!defined(BL_C64_PROFILE) || !BL_C64_PROFILE))
#define BL_CONTACT_C_REFERENCE 1
#else
#define BL_CONTACT_C_REFERENCE 0
#endif
#if defined(__m68k__)
extern void bl_contact_clear72(unsigned char *ram);
extern unsigned long bl_contact_swap_lane(unsigned char *ram,unsigned long base);
extern unsigned long bl_contact_classify_full(unsigned char *ram,unsigned long stack);
#endif
/* $55E6/$5658/$56CA: seven exact exchanges in one23-byte class lane.
 * A ends with the old left byte, X/N/Z with the source actor index.
 * C/V/D/Y and every source stack byte remain untouched here. */
#if BL_CONTACT_C_REFERENCE
static void source_contact_swap_c(unsigned short base){
    static const unsigned char offsets[7]={3,7,11,12,13,14,15};
    unsigned char i,value;
    for(i=0;i<7;i++){
        a=m[base+offsets[i]];value=m[base+16+i];m[base+offsets[i]]=value;m[base+16+i]=a;
    }
    x=m[0x50];NZ(x);sp+=2;
}
#endif
static void source_contact_swap(unsigned short base){
    DETAIL_BEGIN(BL_PERF_CONTACT_SWAP);
#if defined(__m68k__)
    a=(unsigned char)bl_contact_swap_lane(m,(unsigned long)base);
    x=m[0x50];NZ(x);sp+=2;
#else
    source_contact_swap_c(base);
#endif
    DETAIL_END(BL_PERF_CONTACT_SWAP);
}
/* $5431-$55AA. The OR operands below are the frozen instruction operands,
 * including the repeated $4EFE. No class is inferred from tile artwork. */
#if !defined(__m68k__) || (defined(BL_AUTOTEST) && BL_AUTOTEST)
static unsigned char source_contact_summary_c(void){
    unsigned char col,mask=0,bit;unsigned short flag;
    m[0x4f3c]=(unsigned char)((m[0x4eee]|m[0x4ef1]|m[0x4ef2]|m[0x4ef3]|m[0x4ef4]|m[0x4efe]|m[0x4ef6]|m[0x4efa]|m[0x4f01]|m[0x4f05]|m[0x4f08]|m[0x4f09]|m[0x4f0a]|m[0x4f0b]|m[0x4efe]|m[0x4f0d]|m[0x4f11]|m[0x4f18]|m[0x4f1c]|m[0x4f1f]|m[0x4f20]|m[0x4f21]|m[0x4f22]|m[0x4f2c]|m[0x4f24]|m[0x4f28]|m[0x4f2f])!=0);
    m[0x4f3d]=(unsigned char)((m[0x4eef]|m[0x4ef3]|m[0x4ef5]|m[0x4ef6]|m[0x4ef7]|m[0x4ef8]|m[0x4efb]|m[0x4eff]|m[0x4f02]|m[0x4f06]|m[0x4f0a]|m[0x4f0c]|m[0x4f0d]|m[0x4f0e]|m[0x4f0f]|m[0x4f12]|m[0x4f16]|m[0x4f19]|m[0x4f1d]|m[0x4f21]|m[0x4f23]|m[0x4f24]|m[0x4f25]|m[0x4f26]|m[0x4f29]|m[0x4f2d]|m[0x4f30])!=0);
    m[0x4f3e]=(unsigned char)((m[0x4efd]|m[0x4efe]|m[0x4eff]|m[0x4f00]|m[0x4f01]|m[0x4f02]|m[0x4f03]|m[0x4f14]|m[0x4f15]|m[0x4f16]|m[0x4f17]|m[0x4f18]|m[0x4f19]|m[0x4f1a]|m[0x4f2b]|m[0x4f2c]|m[0x4f2d]|m[0x4f2e]|m[0x4f2f]|m[0x4f30]|m[0x4f31])!=0);
    m[0x4f3f]=(unsigned char)((m[0x4ef0]|m[0x4ef4]|m[0x4ef8]|m[0x4ef9]|m[0x4efa]|m[0x4efb]|m[0x4efc]|m[0x4f07]|m[0x4f0b]|m[0x4f0f]|m[0x4f10]|m[0x4f11]|m[0x4f12]|m[0x4f13]|m[0x4f1e]|m[0x4f22]|m[0x4f26]|m[0x4f27]|m[0x4f28]|m[0x4f29]|m[0x4f2a])!=0);
    for(col=5;--col;){flag=(unsigned short)(0x4f3b+col);bit=m[flag]&1;m[flag]>>=1;mask=(unsigned char)((mask<<1)|bit);}
    return mask;
}
#endif
#if defined(__m68k__)
extern unsigned long bl_contact_classes4(const unsigned char *ram);
#endif
#if BL_CONTACT_C_REFERENCE
static void source_contact_classes_c(void){
    unsigned char col,mask;unsigned short flag;
    for(col=0;col<5;col++)m[0x4f3b+col]=0;
    for(col=0;col<3;col++){
        flag=(unsigned short)(0x4f32+col);
        if(m[flag]){
            --m[flag];
            /* Actual JSR sites $5443/$544E/$5459. Preserve even the stack
             * bytes below the restored SP; the source reader can see them. */
            m[0x100+sp--]=0x54;m[0x100+sp--]=(unsigned char)(0x45+11*col);
            source_contact_swap_c((unsigned short)(0x4eed+23*col));
        }
    }
    mask=source_contact_summary_c();
    x=m[0x50];a=0;m[0xb6+x]=mask;
    c=0;NZ(mask);sp+=2;
}
#endif
static void source_contact_classes(void){
    DETAIL_BEGIN(BL_PERF_CONTACT_CLASSES);
#if defined(__m68k__)
    unsigned char mask=(unsigned char)bl_contact_classify_full(m,(unsigned long)sp);
    x=m[0x50];a=0;m[0xb6+x]=mask;c=0;NZ(mask);sp+=2;
#else
    source_contact_classes_c();
#endif
    DETAIL_END(BL_PERF_CONTACT_CLASSES);
}
SOURCE_INLINE void source_contact_frame(unsigned short ret){
    m[0x100+sp--]=(unsigned char)(ret>>8);m[0x100+sp--]=(unsigned char)ret;
}
#if BL_CONTACT_C_REFERENCE
/* $55C5-$55D6 and $55D7/$5649/$56BB are internal to the binary
 * pointer path below. No service observes their intermediate registers.
 * The original actor entries still execute their instruction translation. */
SOURCE_INLINE void source_contact_table(unsigned char row){
    m[4]=m[0x50e7+row];m[0x12]=m[4];m[5]=m[0x50ff+row];
    m[0x13]=m[0x5117+row];sp+=2;
}
SOURCE_INLINE void source_contact_attribute(unsigned short base,unsigned short flag){
    unsigned char nonzero=(unsigned char)(m[(unsigned short)(W(0x12)+y)]&7),toggle=m[flag];
    if(nonzero?!toggle:toggle!=0){
        if(nonzero)++m[flag];else --m[flag];
        source_contact_swap_c(base);
    }else sp+=2;
}
/* Keep every source RAM/JSR write in lane order, including stack aliases.
 * Only the third ADC's virtual A/C/N/Z/V survive the complete routine.
 * Earlier flags cannot feed a branch or arithmetic in the next lane. */
SOURCE_INLINE void source_contact_column(unsigned short operand,unsigned short ret,unsigned char blank,unsigned char publish){
    unsigned char value=blank?0:m[(unsigned short)(W(4)+y)],high,low;unsigned short sum;
    m[0x43bc]=value;source_contact_frame(ret);
    m[0x43bc]=(unsigned char)(value<<3);m[0x43bb]=(unsigned char)(value>>5);sp+=2;
    low=m[0x43bc];high=(unsigned char)(m[0x43bb]-(low<m[0x52]));
    m[operand]=(unsigned char)(low-m[0x52]);sum=(unsigned short)high+m[0x7c];m[operand+1]=(unsigned char)sum;
    if(publish){v=((~(high^m[0x7c])&(high^sum)&128)!=0);c=sum>255;a=(unsigned char)sum;NZ(a);}
}
/* $530A-$537D, binary-mode path. Table, attributes, glyphs and operand
 * aliases remain ordered; only unobserved virtual register stores fold. */
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static void source_contact_pointers_c(void){
    unsigned char blank,row=m[0xe9+m[0x50]];
    source_contact_frame(0x5311);source_contact_table(row);
    x=m[0x50];y=m[0xe6+x];source_contact_frame(0x5318);source_contact_attribute(0x4eed,0x4f32);
    source_contact_column(0x5381,0x5320,0,0);
    ++y;source_contact_frame(0x5338);source_contact_attribute(0x4f04,0x4f33);
    source_contact_column(0x539b,0x5340,0,0);
    ++y;blank=(unsigned char)(y>=40);
    if(!blank){source_contact_frame(0x5360);source_contact_attribute(0x4f1b,0x4f34);}
    source_contact_column(0x53b5,0x5368,blank,1);sp+=2;
}
#endif
/* Eight-byte result ABI, independent of the module's -mshort setting.
 * No I/O seam is crossed by the original pointer preparation. */
typedef struct {unsigned char aa,xx,yy,cc,zz,nn,vv,stack;} SourceContactRegisters;
typedef char SourceContactRegistersLayout[(sizeof(SourceContactRegisters)==8 && offsetof(SourceContactRegisters,stack)==7)?1:-1];
#if defined(__m68k__)
extern void bl_contact_pointers3(unsigned char *ram,SourceContactRegisters *result);
#endif
static void source_contact_pointers(void){
#if defined(__m68k__)
    SourceContactRegisters result;result.stack=sp;
    bl_contact_pointers3(m,&result);
    a=result.aa;x=result.xx;y=result.yy;c=result.cc;z=result.zz;n=result.nn;v=result.vv;sp=result.stack;
#else
    source_contact_pointers_c();
#endif
}
/* $53E0-$5428 body classification: no service inside these ordered
 * snapshots, class reduction and conditional lane reversals. */
#if BL_CONTACT_C_REFERENCE
static void source_contact_body_c(void){
for(x=2;;--x){a=m[0x4f32 + x];m[0x4f35 + x]=a;if(!x)break;}
x=255;NZ(x);source_contact_frame(0x53f1);
if(m[0x50]<3)source_contact_classes_c();else actor_code(0x5431);
a=m[0xb6 + x];m[0xa7 + x]=a;NZ(a);
a=m[0x4f32];c=a>=m[0x4f35];NZ((unsigned char)(a-m[0x4f35]));
if(!z){a^=1;m[0x4f32]=a;NZ(a);source_contact_frame(0x5405);source_contact_swap_c(0x4eed);}
a=m[0x4f33];c=a>=m[0x4f36];NZ((unsigned char)(a-m[0x4f36]));
if(!z){a^=1;m[0x4f33]=a;NZ(a);source_contact_frame(0x5415);source_contact_swap_c(0x4f04);}
a=m[0x4f34];c=a>=m[0x4f37];NZ((unsigned char)(a-m[0x4f37]));
if(!z){a^=1;m[0x4f34]=a;NZ(a);source_contact_frame(0x5425);source_contact_swap_c(0x4f1b);}
}
#endif
#if defined(__m68k__)
extern void bl_contact_body(unsigned char *ram,SourceContactRegisters *result);
#endif
static void source_contact_body(void){
#if defined(__m68k__)
    SourceContactRegisters result;result.stack=sp;
    bl_contact_body(m,&result);
    a=result.aa;x=result.xx;c=result.cc;z=result.zz;n=result.nn;
#else
    source_contact_body_c();
#endif
}
/* The three source lanes stay ordered: a glyph pointer may alias flags
 * written by an earlier lane. CPY overwrites N/Z/C before any observation. */
#define CONTACT_LANE(pointer,bitmap,flags) do{ \
    value=(unsigned char)(m[(unsigned short)((pointer)+yy)]&m[(bitmap)+yy]);aa=value; \
    if(value){m[0x4e]=value;xx=(unsigned char)(value>>4);m[(flags)+xx]=xx; \
        aa=(unsigned char)(value&15);xx=aa;m[(flags)+xx]=aa;} \
}while(0)
typedef struct {
    unsigned short lane0,lane1,lane2;
    unsigned char aa,xx,yy,count;
} SourceContactBatch;
typedef char SourceContactBatchLayout[(sizeof(SourceContactBatch)==10 &&
    offsetof(SourceContactBatch,aa)==6 && offsetof(SourceContactBatch,xx)==7 &&
    offsetof(SourceContactBatch,yy)==8 && offsetof(SourceContactBatch,count)==9)?1:-1];
#if defined(__m68k__)
extern void bl_contact_rows8(unsigned char *ram,SourceContactBatch *batch);
#endif
static void source_contact_scan_c(SourceContactBatch *batch){
    unsigned char value,aa=batch->aa,xx=batch->xx,yy=batch->yy,count=batch->count;
    while(count--){
        CONTACT_LANE(batch->lane0,0xcae0,0x4eed);
        CONTACT_LANE(batch->lane1,0xcb00,0x4f04);
        CONTACT_LANE(batch->lane2,0xcb20,0x4f1b);
        ++yy;
    }
    batch->aa=aa;batch->xx=xx;batch->yy=yy;
}
SOURCE_INLINE void source_contact_scan(SourceContactBatch *batch){
#if defined(__m68k__)
    if(batch->lane0<=0xff00 && batch->lane1<=0xff00 && batch->lane2<=0xff00 &&
       (unsigned short)batch->yy+batch->count<=256){bl_contact_rows8(m,batch);return;}
#endif
    source_contact_scan_c(batch);
}
#if defined(__m68k__) && defined(BL_AUTOTEST) && BL_AUTOTEST
#if defined(BL_SOURCE_PERF_TEST) && BL_SOURCE_PERF_TEST && (!defined(BL_C64_PROFILE) || !BL_C64_PROFILE)
/* Separate native kernel controls fit in the benchmark image without
 * duplicating the portable references in the full53-fixture game image. */
#if BL_C64_CONTACT_PREPARE_CASES
static void source_prepare_image(unsigned char *out,unsigned char restore){
    static const unsigned short operands[8]={0x43bb,0x43bc,0x5381,0x5382,0x539b,0x539c,0x53b5,0x53b6};
    unsigned short i,at=0;
    for(i=0;i<512;i++,at++){if(restore)m[i]=out[at];else out[at]=m[i];}
    for(i=0;i<85;i++,at++){if(restore)m[0x4eec+i]=out[at];else out[at]=m[0x4eec+i];}
    for(i=0;i<8;i++,at++){if(restore)m[operands[i]]=out[at];else out[at]=m[operands[i]];}
}
#endif
static void source_prepare_registers(unsigned short test,unsigned char classes,unsigned char stack){
    a=(unsigned char)(test*3);x=(unsigned char)(test*7);y=(unsigned char)(test*11);
    c=test&1;z=(test>>1)&1;n=(test>>2)&1;v=(test>>3)&1;d=classes?((test>>4)&1):0;sp=stack;
}
#if BL_C64_CONTACT_PREPARE_CASES
static unsigned short source_prepare_selftest(void){
    static const unsigned short glyphs[8]={0xa000,0x0100,0x43bb,0x5381,0x539b,0x4eed,0xfff0,0x0040};
    static const unsigned char stacks[4]={0,1,254,255},ys[4]={0,38,254,255};
    unsigned char before[605],wanted[605],got[605],want_regs[13],got_regs[13],actor,stack,classes;
    unsigned short test,i,errors=0,pointer;
    for(test=0;test<BL_C64_CONTACT_POINTER_CASES+BL_C64_CONTACT_PREPARE_CLASS_CASES+BL_C64_CONTACT_BODY_CASES;test++){
        classes=(unsigned char)(test>=BL_C64_CONTACT_POINTER_CASES);actor=(unsigned char)(test%3);
        stack=stacks[((test%BL_C64_CONTACT_POINTER_CASES)/24)&3];
        for(i=0;i<512;i++)m[i]=(unsigned char)(i*17+test*13);
        for(i=0;i<85;i++)m[0x4eec+i]=(unsigned char)(i*23+test*7);
        for(i=0;i<96;i++)m[0xa000+i]=(unsigned char)(i*37+test*19);
        for(i=0;i<96;i++)m[0x43a0+i]=(unsigned char)(i*31+test*11);
        for(i=0;i<128;i++){m[0x5300+i]=(unsigned char)(i*11+test*43);m[0xff80+i]=(unsigned char)(i*29+test*5);}
        m[0x50]=actor;m[0x52]=(unsigned char)(test&31);m[0x7c]=(unsigned char)(test*59);
        m[0xe6+actor]=ys[(test/96)&3];m[0xe9+actor]=10;
        pointer=glyphs[(test/3)&7];m[0x50e7+10]=(unsigned char)pointer;
        m[0x50ff+10]=(unsigned char)(pointer>>8);m[0x5117+10]=(unsigned char)((test&1)?(pointer>>8):0x4f);
        if(classes)for(i=0;i<3;i++)m[0x4f32+i]=(unsigned char)((((test-BL_C64_CONTACT_POINTER_CASES)/3)>>i)&1?((test&1)?255:1):0);
        source_prepare_registers(test,classes,stack);source_prepare_image(before,0);
        if(test>=BL_C64_CONTACT_POINTER_CASES+BL_C64_CONTACT_PREPARE_CLASS_CASES)source_contact_body_c();else if(classes)source_contact_classes_c();else source_contact_pointers_c();
        source_prepare_image(wanted,0);bl_c64_actor_registers(want_regs);
        source_prepare_image(before,1);source_prepare_registers(test,classes,stack);
        if(test>=BL_C64_CONTACT_POINTER_CASES+BL_C64_CONTACT_PREPARE_CLASS_CASES)source_contact_body();else if(classes)source_contact_classes();else source_contact_pointers();
        source_prepare_image(got,0);bl_c64_actor_registers(got_regs);
        for(i=0;i<605;i++)if(got[i]!=wanted[i])++errors;
        for(i=0;i<13;i++)if(got_regs[i]!=want_regs[i])++errors;
    }
    for(test=0;test<BL_C64_CONTACT_CLEAR_CASES;test++){
        m[0x4eec]=0xa5;m[0x4f35]=0x5a;
        for(i=0;i<72;i++)m[0x4eed+i]=(unsigned char)((i*13+test*17)|1);
        bl_contact_clear72(m);
        for(i=0;i<72;i++)if(m[0x4eed+i])++errors;
        if(m[0x4eec]!=0xa5 || m[0x4f35]!=0x5a)++errors;
    }
    return errors;
}
#endif
#endif
#if defined(BL_SPRITE_COPY_TEST) && BL_SPRITE_COPY_TEST
static unsigned short source_sprite_copy_selftest(void);
#endif
unsigned short bl_c64_contact_kernel_selftest(void){
    unsigned short test,i,errors=0;unsigned char before[70],expected[70];
    SourceContactBatch batch,initial,wanted;
    /* Every source phase/offset, aligned/odd/overlapping source copies.
     * Compare the full writable span plus both canaries and all registers. */
    for(test=0;test<BL_C64_CONTACT_ALIGN_CASES;test++){
        unsigned char saved[194],want[194],want_regs[13],got_regs[13];
        unsigned char phase=(unsigned char)(test&3),offset=(unsigned char)((test>>2)&7);
        unsigned short pointer,kind=(unsigned short)(test>>5);
        switch(kind){
        case 0:pointer=0xa000;break;case 1:pointer=0xa001;break;
        case 2:pointer=(unsigned short)(0xcae0+offset);break;
        case 3:pointer=(unsigned short)(0xcae0+offset-1);break;
        case 4:pointer=(unsigned short)(0xcae0+offset+1);break;
        case 5:pointer=0xcb00;break;case 6:pointer=0xffa0;break;
        default:pointer=0xcad0;break;
        }
        for(i=0;i<194;i++)m[0xcadf+i]=(unsigned char)((i*17+test*31)^(i>>2));
        for(i=0;i<96;i++)m[(unsigned short)(pointer+i)]=(unsigned char)(i*29+test*7);
        m[0x1b]=phase;m[0x1c]=offset;m[0x52cc]=(unsigned char)pointer;m[0x52cd]=(unsigned char)(pointer>>8);
        for(i=0;i<194;i++)saved[i]=m[0xcadf+i];
        a=17;x=23;y=41;c=0;z=0;n=1;v=1;d=1;sp=251;
        source_contact_align_c();
        for(i=0;i<194;i++)want[i]=m[0xcadf+i];
        bl_c64_actor_registers(want_regs);
        for(i=0;i<194;i++)m[0xcadf+i]=saved[i];
        a=17;x=23;y=41;c=0;z=0;n=1;v=1;d=1;sp=251;
        source_contact_align();
        for(i=0;i<194;i++)if(m[0xcadf+i]!=want[i])++errors;
        bl_c64_actor_registers(got_regs);
        for(i=0;i<13;i++)if(got_regs[i]!=want_regs[i])++errors;
    }
    for(test=0;test<BL_C64_CONTACT_ROW_CASES;test++){
        for(i=0;i<320;i++)m[0xcae0+i]=(unsigned char)((test*17+i*13)^(i>>2));
        for(i=0;i<128;i++){m[0xa000+i]=(unsigned char)(i*37+test*19);m[0xff00+i]=(unsigned char)(i*23+test);}
        for(i=0;i<96;i++)m[0x10+i]=(unsigned char)(test+i*7);
        for(i=0;i<69;i++)m[0x4eed+i]=(unsigned char)(i*11+test*3);
        m[0x4e]=(unsigned char)test;m[0x4eec]=0xa5;m[0x4f32]=0x5a;
        batch.lane0=0xa000;batch.lane1=0xa020;batch.lane2=0xa040;
        batch.yy=(unsigned char)(((test>>3)&3)*8);batch.count=(unsigned char)(1+(test&7));
        if(test>=32 && test<64){batch.lane0=0x4eed;batch.lane1=0x4f04;batch.lane2=0x4f1b;}
        if(test>=64 && test<96){batch.lane0=0x10;batch.lane1=(unsigned short)(0x4e - batch.yy);batch.lane2=0x4eed;}
        if(test>=96){batch.yy=(unsigned char)(248+(test&7));batch.count=(unsigned char)(256-batch.yy);
            batch.lane0=0xff00;batch.lane1=0x4f04;batch.lane2=0x4eed;
            for(i=128;i<256;i++)m[0xff00+i]=(unsigned char)(i*31+test);}
        if(!test)batch.count=0;
        batch.aa=(unsigned char)(test*3);batch.xx=(unsigned char)(test*7);initial=batch;
        before[0]=m[0x4e];for(i=0;i<69;i++)before[i+1]=m[0x4eed+i];
        source_contact_scan_c(&batch);wanted=batch;
        expected[0]=m[0x4e];for(i=0;i<69;i++)expected[i+1]=m[0x4eed+i];
        m[0x4e]=before[0];for(i=0;i<69;i++)m[0x4eed+i]=before[i+1];batch=initial;
        bl_contact_rows8(m,&batch);
        for(i=0;i<sizeof(batch);i++)if(((unsigned char*)&batch)[i]!=((unsigned char*)&wanted)[i])++errors;
        if(m[0x4e]!=expected[0] || m[0x4eec]!=0xa5 || m[0x4f32]!=0x5a)++errors;
        for(i=0;i<69;i++)if(m[0x4eed+i]!=expected[i+1])++errors;
    }
    /* One nonzero byte in each original class slot, plus all-zero. */
    for(test=0;test<BL_C64_CONTACT_CLASS_CASES;test++){
        unsigned char wanted_mask;
        for(i=0;i<69;i++)m[0x4eed+i]=0;
        if(test<69)m[0x4eed+test]=1;
        m[0x4eec]=m[0x4f32]=m[0x4f3b]=255;
        wanted_mask=source_contact_summary_c();
        if(bl_contact_classes4(m)!=wanted_mask)++errors;
    }
#if defined(BL_SOURCE_PERF_TEST) && BL_SOURCE_PERF_TEST && (!defined(BL_C64_PROFILE) || !BL_C64_PROFILE)
#if BL_C64_CONTACT_PREPARE_CASES
    errors+=source_prepare_selftest();
#endif
#if defined(BL_SPRITE_COPY_TEST) && BL_SPRITE_COPY_TEST
    errors+=source_sprite_copy_selftest();
#endif
#endif
    return errors;
}
#endif

#if defined(__m68k__) && defined(BL_SPRITE_COPY_TEST) && BL_SPRITE_COPY_TEST
static unsigned short source_sprite_copy_selftest(void){
    static const unsigned char ys[8]={0,1,62,63,127,128,254,255};
    unsigned char before[256],wanted[256],wr[13],gr[13],scratch,wanted_scratch,height;
    unsigned short test,i,errors=0,dest,glyph;
    for(test=0;test<BL_C64_SPRITE_COPY_CASES;test++){
        dest=(unsigned short)(0xa000+((test>>2)&1));
        for(i=0;i<1024;i++)m[0xa000+i]=(unsigned char)(i*37+test*19);
        for(i=0;i<256;i++)m[0xff00+i]=(unsigned char)(i*23+test);
        glyph=test<64?0xa200:test<128?dest:test<192?0x2770:0xff00;
        height=(unsigned char)((test>>1)&31);
        m[0x0e]=(unsigned char)dest;m[0x0f]=(unsigned char)(dest>>8);
        m[0x26ab]=m[0x26e4]=m[0x26ee]=(unsigned char)glyph;
        m[0x26ac]=m[0x26e5]=m[0x26ef]=(unsigned char)(glyph>>8);
        m[0x277f]=(unsigned char)(test*13);scratch=m[0x277f];
        source_prepare_registers(test,0,(unsigned char)(test*17));x=(unsigned char)(test&7);
        m[0xe0+x]=height;z=(unsigned char)(test&1);y=z?ys[(test>>3)&7]:(unsigned char)(height*3);
        for(i=0;i<256;i++)before[i]=m[dest+i];
        source_sprite_copy_c();for(i=0;i<256;i++)wanted[i]=m[dest+i];wanted_scratch=m[0x277f];bl_c64_actor_registers(wr);
        for(i=0;i<256;i++)m[dest+i]=before[i];
        m[0x277f]=scratch;
        source_prepare_registers(test,0,(unsigned char)(test*17));x=(unsigned char)(test&7);z=(unsigned char)(test&1);y=z?ys[(test>>3)&7]:(unsigned char)(height*3);
        if(!source_sprite_copy())++errors;
        bl_c64_actor_registers(gr);for(i=0;i<256;i++)if(m[dest+i]!=wanted[i])++errors;
        if(m[0x277f]!=wanted_scratch)++errors;
        for(i=0;i<13;i++)if(gr[i]!=wr[i])++errors;
    }
    return errors;
}
#endif
/* Virtual registers remain local until a source helper, service or return. */
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static unsigned char source_contact_rows_inner(void){
    unsigned char count,distance,aa=a,xx=x,yy=m[0x52],cc=c,zz=(unsigned char)(yy==0),nn=(unsigned char)((yy&128)!=0);
    unsigned short lane0=W(0x5381),lane1=W(0x539b),lane2=W(0x53b5);SourceContactBatch batch;
    for(;;){
        if(actor_world_enabled && io_service && !(yy&7)){
            a=aa;x=xx;y=yy;c=cc;z=zz;n=nn;io_service();
            aa=a;xx=x;yy=y;cc=c;zz=z;nn=n;
            lane0=W(0x5381);lane1=W(0x539b);lane2=W(0x53b5);
        }
        /* No pixel write can change $4F38/$4F39/$4F3A. Stop at the
         * earliest body/foot/part boundary or next original8-row service. */
        count=(unsigned char)(8-(yy&7));
        distance=(unsigned char)(m[0x4f38]-yy);if(distance && distance<count)count=distance;
        distance=(unsigned char)(m[0x4f39]-yy);if(distance && distance<count)count=distance;
        distance=(unsigned char)(m[0x4f3a]-yy);if(distance && distance<count)count=distance;
        batch.lane0=lane0;batch.lane1=lane1;batch.lane2=lane2;
        batch.aa=aa;batch.xx=xx;batch.yy=yy;batch.count=count;
        DETAIL_BEGIN(BL_PERF_CONTACT_LANES);source_contact_scan(&batch);DETAIL_END(BL_PERF_CONTACT_LANES);
        aa=batch.aa;xx=batch.xx;yy=batch.yy;
        if(yy==m[0x4f38]){
            a=aa;x=xx;y=yy;c=1;z=1;n=0;
            source_contact_body();
            aa=a;xx=x;yy=y;
        }
        if(yy==m[0x4f39]){
            a=aa;x=xx;y=yy;c=1;z=1;n=0;source_contact_frame(0x542b);
            if(m[0x50]<3)source_contact_classes();else actor_code(0x5431);
            a=m[0x100 + (unsigned char)++sp];a=m[0x100 + (unsigned char)++sp];NZ(a);
            return 1; /* $542C/$542D discard this row frame; driver advances actor. */
        }
        cc=yy>=m[0x4f3a];zz=(unsigned char)(yy==m[0x4f3a]);nn=(unsigned char)(((unsigned char)(yy-m[0x4f3a])&128)!=0);
        if(zz){a=aa;x=xx;y=yy;c=cc;z=zz;n=nn;m[0x52]=yy;sp+=2;return 0;}
    }
}
#undef CONTACT_LANE
static void source_contact_rows(void){
    if(source_contact_rows_inner())actor_code(0x52a4);
}
/* $31D5-$31F3 / $32EE-$330C: 24 binary shifts and decimal doubling
 * produce four packed-BCD bytes. Both callers clear the decimal buffer.
 * PHP/PLP retain all entry flags; the popped status byte remains in RAM. */
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static void source_score_decimal(void){
    unsigned long value=((unsigned long)m[0x4398]<<16)|((unsigned long)m[0x4399]<<8)|m[0x439a],quotient;
    unsigned char digit,pair,part;
    m[0x100+sp]=(unsigned char)(0x30|c|(z<<1)|(actor_i<<2)|(d<<3)|(v<<6)|(n<<7));
    for(part=4;part--;){
        quotient=value/100;pair=(unsigned char)(value-quotient*100);digit=pair/10;
        m[0x439b+part]=(unsigned char)((digit<<4)|(pair-digit*10));value=quotient;
    }
    m[0x4398]=m[0x4399]=m[0x439a]=0;a=m[0x439b];x=y=255;
}
/* $2E89-$2EE9: ordered object dispatch. Fold intermediate CMP flags;
 * publish exactly the last executed comparison at each original branch.
 * $53 is still shifted on every eligible cell, including empty cells. */
static unsigned short source_object_classify(void){
    unsigned char value=a,threshold,old;unsigned short target;
    if(value==5){threshold=5;target=0x2f7b;}
    else if(value==2){threshold=2;target=0x2f3c;}
    else if(value==3){threshold=3;target=0x2f51;}
    else if(value==4){threshold=4;target=0x2f66;}
    else if(value==0x62){threshold=0x62;target=0x310c;}
    else if(value==0x2d){threshold=0x2d;target=0x2eea;}
    else if(value==0x2e){threshold=0x2e;target=0x2eea;}
    else{
        old=m[0x53];m[0x53]=(unsigned char)(old<<1);
        if(!m[0x53]){c=old>>7;NZ(m[0x53]);return 0x2ee9;}
        if(value==0x13){threshold=0x13;target=0x2f04;}
        else if(value==0x14){threshold=0x14;target=0x2f04;}
        else if(value==0x31){threshold=0x31;target=0x2f04;}
        else if(value==0x64){threshold=0x64;target=0x2f01;}
        else if(value==0x66){threshold=0x66;target=0x2efa;}
        else if(value==0x0f){threshold=0x0f;target=0x2f01;}
        else if(value==0x40){threshold=0x40;target=0x2f01;}
        else if(value!=0x57 && value<0x54){threshold=0x54;target=0x2ee9;}
        else if(value!=0x57 && value<0x5b){threshold=0x5b;target=0x2f01;}
        else if(value>=0x71 && value<0x7d){threshold=0x7d;target=0x2f01;}
        else{threshold=0x60;target=value==0x60?0x2ef7:0x2ee9;}
    }
    c=value>=threshold;NZ((unsigned char)(value-threshold));return target;
}
/* $55AB-$55C4 has no service/alias seam inside its fixed 72-byte
 * clear. Preserve final DEX flags, A=0 and the source RTS frame. */
SOURCE_INLINE void source_contact_clear(void){
#if defined(__m68k__)
    bl_contact_clear72(m);
#else
    unsigned char at;for(at=0;at<72;at++)m[0x4eed+at]=0;
#endif
    a=0;x=255;NZ(x);sp+=2;
}
/* Native object pass ($2E39-$2E88), keeping the original handler for each
 * source cell and each non-local lifetime/room return. Empty cells do not
 * need a recursive trip through the large actor entry dispatcher. */
SOURCE_INLINE unsigned char source_object_returned(unsigned short expected){
    return (unsigned char)(!transition_pending && !actor_delay_pending && !actor_gameover_pending &&
        !actor_reset_pending && !actor_irq_stop && !source_fault && actor_return==expected);
}
static unsigned char source_object_row(void){
    unsigned short target;
    a=m[(unsigned char)(0xe9+x)];x=a;NZ(x);source_contact_frame(0x2e73);
    m[4]=m[0x4338+x];m[5]=m[0x434c+x];m[8]=m[0x4360+x];m[9]=m[0x4374+x];
    a=m[0x100];NZ(a);if(a){m[8]=0;a=0xce;m[9]=a;NZ(a);}sp+=2;
    x=m[0x51];NZ(x);y=m[(unsigned char)(0xe6+x)];NZ(y);a=2;m[0x4c]=a;NZ(a);
    for(;;){
        a=(unsigned char)(m[(unsigned short)(W(4)+y)]&127);NZ(a);
        source_contact_frame(0x2e82);target=source_object_classify();
        if(target==0x2ee9){sp+=2;actor_return=source_stack_return();}
        else{actor_code(target);if(!source_object_returned(0x2e83))return 0;}
        ++y;NZ(y);--m[0x4c];NZ(m[0x4c]);
        if(n){sp+=2;actor_return=source_stack_return();return 1;}
    }
}
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static unsigned char source_object_driver(void){
    a=0;m[0x100]=0;x=2;NZ(x);
    for(;;){
        m[0x51]=x;a=(unsigned char)(m[(unsigned char)(0x95+x)]&1);NZ(a);
        if(a){
            a=m[(unsigned char)(0xbf+x)];c=a>=25;NZ((unsigned char)(a-25));
            if(!z){
                c=a>=23;NZ((unsigned char)(a-23));
                if(z){source_contact_frame(0x2e54);actor_code(0x2e10);if(!source_object_returned(0x2e55))return 0;}
                a=(unsigned char)(m[(unsigned char)(0xb6+x)]&2);m[0x53]=a;NZ(a);
                source_contact_frame(0x2e5d);actor_code(0x1c39);if(!source_object_returned(0x2e5e))return 0;
                source_contact_frame(0x2e60);if(!source_object_row() || !source_object_returned(0x2e61))return 0;
                x=m[0x51];NZ(x);++m[(unsigned char)(0xe9+x)];NZ(m[(unsigned char)(0xe9+x)]);
                source_contact_frame(0x2e67);if(!source_object_row() || !source_object_returned(0x2e68))return 0;
            }
        }
        x=(unsigned char)(m[0x51]-1);NZ(x);if(n){sp+=2;return 1;}
    }
}
/* $5212-$52AC, binary path. Keep the actual mask/table order and all JSR
 * bytes. A completed foot mask discards only its row frame, then continues
 * the same driver frame with the next actor ($542C -> $52A4).
 * Services occur at the original $5214 and row checkpoints. */
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static void source_contact_driver(void){
    static const unsigned short pointer_return[4]={0x5273,0x5282,0x5291,0x52a0};
    static const unsigned short row_return[4]={0x5276,0x5285,0x5294,0x52a3};
    unsigned char part,actor,pose;
    x=2;NZ(x);
    for(;;){
        if(actor_world_enabled && io_service)io_service();
        m[0x50]=x;a=(unsigned char)(m[(unsigned char)(0x95+x)]&1);NZ(a);
        if(a){
            /* All entry arithmetic is binary. Intermediate virtual flags
             * have no reader before $530A's final ADC publishes them at
             * the first row/service boundary. Keep every RAM write. */
            actor=m[0x50];
            m[0xe6+actor]=(unsigned char)(m[0x9e + actor]-12);m[0x1b]=m[0xe6+actor]&3;
            m[0xe9+actor]=(unsigned char)(m[0xa1+actor]-29);m[0x1c]=m[0xe9+actor]&7;
            pose=m[0x4f4e + actor];m[0x52cc]=m[0x1167+pose];m[0x52cd]=m[0x1239+pose];
            source_contact_frame(0x5247);PERF_BEGIN(BL_PERF_ALIGN);
            source_contact_align();PERF_END(BL_PERF_ALIGN);
            m[0x4f39]=(unsigned char)(m[0x1c]+21);m[0x4f38]=(unsigned char)(m[0x1c]+15);
            source_contact_frame(0x5258);source_contact_clear();
            m[0xe6+actor]>>=2;m[0xe9+actor]>>=3;
            y=0;m[0x52]=0;
            for(part=0;part<4;part++){
                if(part)++m[0xe9+m[0x50]];
                m[0x4f3a]=(unsigned char)((part+1)*8);
                source_contact_frame(pointer_return[part]);source_contact_pointers();
                source_contact_frame(row_return[part]);PERF_BEGIN(BL_PERF_ROWS);
                if(source_contact_rows_inner()){PERF_END(BL_PERF_ROWS);break;}
                PERF_END(BL_PERF_ROWS);
            }
        }
        x=(unsigned char)(m[0x50]-1);NZ(x);
        if(n){sp+=2;return;}
    }
}
#include "c64_actor_programs.h"
/* IRQ I/O seam. The two source fragments retain all source timer, palette,
 * quota and input-mode work. CIA keyboard scanning is replaced only by the
 * sampled Amiga joysticks; no movement or combat rule is supplied here. */
static unsigned char source_direction(unsigned char input){
    return (unsigned char)(15^((input&BL_UP?1:0)|(input&BL_DOWN?2:0)|
        (input&BL_LEFT?4:0)|(input&BL_RIGHT?8:0)));
}
static unsigned char source_vic_same(unsigned char sprite,unsigned short pointer,unsigned char multi,unsigned char wide){
    unsigned char i,layout=(unsigned char)((multi?1:0)|(wide?2:0));
    if((vic_valid&(1<<sprite)) && vic_layout[sprite]==layout){
        if(pointer<=0xffc1){
            const unsigned char *before=vic_bytes[sprite],*current=m+pointer;
#if defined(__m68k__)
            if(!(pointer&1))return bl_vic_equal63(before,current);
#endif
            for(i=0;i<60;i+=4,before+=4,current+=4){
                if(before[0]!=current[0] || before[1]!=current[1] ||
                   before[2]!=current[2] || before[3]!=current[3])return 0;
            }
            return (unsigned char)(before[0]==current[0] && before[1]==current[1] && before[2]==current[2]);
        }
        /* The final63 bytes can straddle $FFFF, including an aliased
         * pointer from an injected or self-modified source state. */
        for(i=0;i<63;i++)if(vic_bytes[sprite][i]!=m[(unsigned short)(pointer+i)])return 0;
        return 1;
    }
    return 0;
}
static void source_vic_cache(unsigned char sprite,unsigned short pointer,unsigned char multi,unsigned char wide){
    unsigned char row,j,b,*raw=vic_bytes[sprite];unsigned short expanded;
    unsigned long high,low,*out_high=vic_high[sprite],*out_low=vic_low[sprite];
    /* One read per source byte; raw cache retains original bits before
     * opacity/width conversion. Pointer wraps at16 bits; pad63 untouched. */
    for(row=0;row<21;row++){
        high=low=0;
        for(j=0;j<3;j++){
            b=m[(unsigned short)(pointer+row*3+j)];*raw++=b;
            if(multi)b=(unsigned char)(((b|(b>>1))&85)*3);
            if(wide){
                expanded=b;expanded=(unsigned short)((expanded|(expanded<<4))&0x0f0f);
                expanded=(unsigned short)((expanded|(expanded<<2))&0x3333);
                expanded=(unsigned short)((expanded|(expanded<<1))&0x5555);expanded|=(unsigned short)(expanded<<1);
                if(j==0)high=(unsigned long)expanded<<16;else if(j==1)high|=expanded;else low=(unsigned long)expanded<<16;
            }else high|=(unsigned long)b<<(24-j*8);
        }
        *out_high++=high;*out_low++=low;
    }
    vic_layout[sprite]=(unsigned char)((multi?1:0)|(wide?2:0));vic_valid|=(unsigned char)(1<<sprite);
}
/* Opaque source VIC sprite pixels, including component sprites and sai.
 * The collision latch accumulates until $D01E is read. Raster/border timing
 * is still a separate hardware acceptance item; no attack boxes or wall ray
 * is introduced at this seam. */
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static void source_vic_latch_slow(void){
    unsigned char i,j,row,prepared=0,candidates=0;
    unsigned char active=m[0xd015],multi=m[0xd01c],wide=m[0xd01d],tall=m[0xd017],bits=0;
    unsigned char same=(unsigned char)(vic_collision_valid && vic_last_active==active && vic_last_tall==tall && vic_last_wide==wide);
    unsigned short bank=(unsigned short)(((~m[0xdd00])&3)<<14),matrix,pointer[8],sx[8],sy[8],height[8],width[8],top,bottom,dy;
    unsigned long ah,al,bh,bl;short dx;
    matrix=(unsigned short)(bank+((unsigned short)(m[0xd018]>>4)<<10));
    for(i=0;i<8;i++)if(active&(1<<i)){
        sx[i]=(unsigned short)(m[0xd000 + i*2]+((m[0xd010]&(1<<i))?256:0));sy[i]=m[0xd001 + i*2];
        width[i]=(unsigned short)((wide&(1<<i))?48:24);height[i]=(unsigned short)((tall&(1<<i))?42:21);
        pointer[i]=(unsigned short)(bank+((unsigned short)m[(unsigned short)(matrix+0x3f8 + i)]<<6));
        if(sx[i]!=vic_last_x[i] || sy[i]!=vic_last_y[i])same=0;
        vic_last_x[i]=sx[i];vic_last_y[i]=sy[i];
    }
    /* A nonoverlapping bounding rectangle cannot set a VIC collision bit,
     * whatever its 63 bitmap bytes contain. Keep all active positions so the
     * result cache is invalidated when a sprite later moves into range. */
    /* Geometry depends only on active bits, both sizes and positions.
     * Reuse its pair set only on that exact key. Bitmap bytes, bank and
     * pointers are still validated below on every candidate field. */
    if(same)candidates=vic_last_candidates;
    else{
        for(i=0;i<8;i++)vic_last_pairs[i]=0;
        for(i=0;i<7;i++)if(active&(1<<i))for(j=(unsigned char)(i+1);j<8;j++)if(active&(1<<j)){
            if(sx[i]+width[i]<=sx[j] || sx[j]+width[j]<=sx[i])continue;
            top=sy[i]>sy[j]?sy[i]:sy[j];bottom=sy[i]+height[i]<sy[j]+height[j]?sy[i]+height[i]:sy[j]+height[j];
            if(top>=bottom)continue;
            vic_last_pairs[i]|=(unsigned char)(1<<j);candidates|=(unsigned char)((1<<i)|(1<<j));
        }
        vic_last_candidates=candidates;
    }
    if(!candidates){vic_last_bits=0;vic_last_active=active;vic_last_tall=tall;vic_last_wide=wide;vic_collision_valid=1;return;}
    for(i=0;i<8;i++)if(candidates&(1<<i)){
        /* Compare effective bitmap bytes, not source write counters. A
         * noncandidate sprite is checked when it next becomes a candidate. */
        if(source_vic_same(i,pointer[i],(unsigned char)(multi&(1<<i)),(unsigned char)(wide&(1<<i))))prepared|=(unsigned char)(1<<i);
        else same=0;
    }
    /* $D01E is an accumulating latch. A cached overlap must be ORed back
     * after every field, even if source code read/cleared it in between. */
    if(same){m[0xd01e]|=vic_last_bits;return;}
    for(i=0;i<7;i++)if(vic_last_pairs[i])for(j=(unsigned char)(i+1);j<8;j++)if(vic_last_pairs[i]&(1<<j)){
        top=sy[i]>sy[j]?sy[i]:sy[j];bottom=sy[i]+height[i]<sy[j]+height[j]?sy[i]+height[i]:sy[j]+height[j];
        if(!(prepared&(1<<i))){source_vic_cache(i,pointer[i],(unsigned char)(multi&(1<<i)),(unsigned char)(wide&(1<<i)));prepared|=(unsigned char)(1<<i);}
        if(!(prepared&(1<<j))){source_vic_cache(j,pointer[j],(unsigned char)(multi&(1<<j)),(unsigned char)(wide&(1<<j)));prepared|=(unsigned char)(1<<j);}
        dx=(short)(sx[j]-sx[i]);
        for(dy=top;dy<bottom;dy++){
            row=(unsigned char)((dy-sy[i])>>((tall&(1<<i))?1:0));ah=vic_high[i][row];al=vic_low[i][row];
            row=(unsigned char)((dy-sy[j])>>((tall&(1<<j))?1:0));bh=vic_high[j][row];bl=vic_low[j][row];
            if(dx>=32){bl=bh>>(dx-32);bh=0;}else if(dx>0){bl=(bl>>dx)|(bh<<(32-dx));bh>>=dx;}
            else if(dx<=-32){bh=bl<<(-dx-32);bl=0;}else if(dx<0){bh=(bh<<-dx)|(bl>>(32+dx));bl<<=-dx;}
            if((ah&bh)||(al&bl)){bits|=(unsigned char)((1<<i)|(1<<j));break;}
        }
    }
    vic_last_bits=bits;vic_last_active=active;vic_last_tall=tall;vic_last_wide=wide;vic_collision_valid=1;m[0xd01e]|=bits;
}
/* Keep the repeat entry outside the slow function's large stack frame.
 * It reads actual sprite bytes each field; source writes need no barriers. */
static void source_vic_latch(void){
#if defined(__m68k__)
    if(bl_vic_repeat(m,&vic_repeat))return;
#else
    if(source_vic_repeat_c(m,&vic_repeat))return;
#endif
    source_vic_latch_slow();
}
static void source_actor_field(void){
    unsigned char saved[10]={a,x,y,c,z,n,v,d,sp,actor_i};
    unsigned short saved_return=actor_return,saved_stop=actor_stop_pc;
    if(actor_i)return; /* Actual SEI/CLI controls the native IRQ seam. */
    /* $14A4 player announcement and $152C/$1574 Game Over use another
     * raster chain. Their game-facing effect is the $48 field wait. */
    if(actor_delay_pending || actor_gameover_pending){if(m[0x48])--m[0x48];return;}
    PERF_BEGIN(BL_PERF_FIELD);
    m[0x44]=0;d=0;
    actor_irq_stop=0;actor_code(0x15b8);
    m[0x98]=source_direction(actor_input);m[0x9b]=(unsigned char)!(actor_input&BL_FIRE);
    if(m[0x42ca]){m[0x99]=source_direction(actor_yamo_input);m[0x9c]=(unsigned char)!(actor_yamo_input&BL_FIRE);}
    m[0xdc00]=m[0xdc01]=255;
    actor_irq_stop=0;actor_code(0x1703);actor_irq_stop=0;
    PERF_BEGIN(BL_PERF_VIC);source_vic_latch();PERF_END(BL_PERF_VIC);
    a=saved[0];x=saved[1];y=saved[2];c=saved[3];z=saved[4];n=saved[5];v=saved[6];d=saved[7];sp=saved[8];actor_i=saved[9];
    actor_return=saved_return;actor_stop_pc=saved_stop;
    PERF_END(BL_PERF_FIELD);
}
void bl_c64_actor_seed(void){actor_reset_pending=actor_life_pending=actor_preparing=actor_i=actor_gameover_pending=actor_irq_stop=0;}
void bl_c64_actor_test_call(long entry,long actor){
    a=y=c=z=n=v=d=0;x=(unsigned char)actor;sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    actor_return=actor_stop_pc=0;actor_delay_pending=0;actor_i=0;actor_irq_stop=0;actor_reset_pending=actor_life_pending=actor_gameover_pending=0;
    actor_life_events=0;actor_preparing=(unsigned char)(entry!=0x1bc2 && entry!=0x1bee);
    actor_code((unsigned short)entry);actor_preparing=0;source_actor_loading_end();flush_glyph_changes();++revision;
}
unsigned char bl_c64_actor_life_pending(void){return actor_life_pending;}
unsigned long bl_c64_actor_ram_hash(void){unsigned long i,h=2166136261UL;for(i=0;i<65536;i++)h=(h^m[i])*16777619UL;return h;}
unsigned short bl_c64_actor_return(void){return actor_return;}
void bl_c64_actor_registers(unsigned char *out){
    out[0]=a;out[1]=x;out[2]=y;out[3]=c;out[4]=z;out[5]=n;out[6]=v;out[7]=d;out[8]=sp;
    out[9]=(unsigned char)actor_life_events;out[10]=actor_reset_pending;out[11]=actor_i;out[12]=actor_gameover_pending;
}
static void execute(unsigned short entry){
    a=x=y=c=z=n=v=d=0;sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    actor_return=0;actor_i=0;actor_irq_stop=0;actor_reset_pending=actor_gameover_pending=0;
    actor_legacy_load=(unsigned char)(entry==0x0a9b);
    room_code(entry);actor_legacy_load=0;
}
void bl_c64_test_execute(long entry){execute((unsigned short)entry);flush_glyph_changes();++revision;}

static unsigned short charset(void){
    return m[0xf2]==0x38?0xa000:m[0xf2]==0x3a?0xa800:m[0xf2]==0x3c?0xb000:0xb800;
}
void bl_c64_reset(void){
    audio_requests_mask=0;audio_faults=0;audio_gates=0;
    unsigned long i;for(i=0;i<65536;i++)m[i]=0;
    seed_actor_memory();a=x=y=c=z=n=v=d=sp=0;loaded=255;++revision;source_fault=0;
    actor_loading_pending=actor_life_pending=actor_reset_pending=actor_gameover_pending=actor_legacy_load=actor_delay_pending=0;actor_stop_pc=0;
    actor_preparing=actor_i=actor_infinite=actor_invincible=0;actor_life_events=actor_spawn_events=0;
    actor_world_enabled=actor_irq_stop=0;actor_logic_steps=actor_loading_epoch=0;actor_debug_target=255;vic_valid=vic_collision_valid=0;
    for(i=0;i<256;i++)glyph_tracking[i]=0;
    glyph_tracking[0x93]=glyph_tracking[0x94]=glyph_tracking[0xb1]=3;
    glyph_tracking[0x86]=glyph_tracking[0xe7]=1;
    for(i=0x61;i<=0x63;i++)glyph_tracking[i]=glyph_tracking[i|128]=3;
    transition_pending=0;contact_bank=0;index_ready=0;paint_count=paint_cursor=0;animation_pending=0;animation_fallback_count=0;animation_fallback_dirty=0;
    glyph_changed_count=0;for(i=0;i<256;i++)glyph_changes[i]=0;
    {unsigned short k;for(k=0;k<1000;k++){contact_cells[k]=0;paint_queued[k]=0;dirty_cells[k]=0;}}
    {unsigned short row,col;for(row=0;row<25;row++)for(col=0;col<40;col++){
        unsigned short cell=(unsigned short)(row*40+col);
        cell_offsets[cell]=(unsigned short)(row*320+col);cell_y[cell]=(unsigned char)(row*8);
        cell_word_mask[cell]=1UL<<(col>>1);
    }}
    m[2]=50; /* PAL $1703/$3428 guard: selected PAL target, not a raster wait. */
    m[0x104]=1;m[0x105]=0;m[0x16]=0;m[0x17]=0;m[3]=0;m[0x40]=0;
    for(i=0x8a;i<=0x90;i++)m[i]=0; /* $0F72 cold-start pending arrivals. */
    execute(0x10c5);execute(0x33ca);
}
void bl_c64_load(long room){
    if(loaded==255 && !m[0x104])bl_c64_reset();
    if(room<0 || room>=20){source_fault=0xffff;return;}
    bl_c64_load_at(room,(long)m[0x4bae + room]*2-24,m[0x4bc2 + room]);
}
void bl_c64_load_at(long room_arg,long px,long py){
    unsigned char room=(unsigned char)room_arg;unsigned short i;
    if(room>=20){source_fault=0xffff;return;}
    if(loaded==255 && !m[0x104])bl_c64_reset();
    /* Original full loader $09F3 calls $255E before room init. */
    if(load_service)load_service(1);
    bl_c64_audio_reset();
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;m[0xb6]=1;m[0xce]=4;
    loaded=m[0x29]=room;transition_pending=0;sp=0;d=0;++contact_generation;index_ready=0;paint_count=paint_cursor=0;animation_pending=0;animation_fallback_count=0;animation_fallback_dirty=0;
    /* $0A34-$0A69, omitted by the old loader boundary at $0A9B. */
    m[0x87]=m[0x88]=0;m[0x7a]=m[0x4c9e + room];
    if(m[0x7a])m[0x8b]=m[0x8c]=0;
    m[0x5d]=m[0x130b + room];m[0x5e]=m[0x1347 + room];
    if(m[0x40])m[0x5d]=m[0x5e]=3;
    if(m[0x42ca])m[0x5e]=8;
    animation_count=0;animation_started=0;
    glyph_changed_count=0;for(i=0;i<256;i++)glyph_changes[i]=0;
    for(i=0;i<1024;i++){character_cache[i].generation=0;cache_references[i]=0;}
    for(i=0;i<1000;i++){cell_cache[i]=65535;cell_stamp[i]=0;paint_queued[i]=0;dirty_cells[i]=0;}
    for(i=0;i<1000;i++){m[0x8c00 + i]=6;m[0xd800 + i]=m[0x47a0 + room];}
    for(i=0;i<132;i++)m[0x4f57 + i]=0;
    m[0x65]=0;m[0x4321]=7;m[0x100]=0;m[0x106]=0;m[0xbf]=0;
    m[0x4fde]=m[0x4fdf]=m[0x4fe0]=0;
    m[0xf2]=(unsigned char)(room<10?0x38:room==18?0x3c:0x3a);
    execute(0x0a9b);
    for(i=0;i<5;i++)m[0x4e97 + i]=0;
    /* $336E restores collected cells, then $33B3 dispatches room init. */
    execute(0x336e);execute(W((unsigned short)(0x4ec4 + 2*room))+1);prepare_palette();index_screen();
    for(i=0;i<1000;i++){flash_cells[i]=0;paint_rows[i]=0;}
    if(room==19){unsigned short row,col;for(row=17;row<25;row++)for(col=4;col<=32;col++)flash_cells[row*40+col]=1;}
    flash_changed=0;
    old_bank=m[0xf2];contact_bank=0;
    for(i=120;i<1000;i++){dirty_cells[i]=paint_queued[i]=1;paint_rows[i]=255;paint_list[paint_count++]=i;}
    ++revision;
    if(load_service)load_service(0);
}
/* Renderer bookkeeping around the actual $09BC loader. No source RAM is
 * synthesized here: RLE, colors, actor reset, lamps and init/loop dispatch
 * all execute from the original instruction chain. */
static void source_actor_loading_begin(void){
    unsigned short i;
    if(load_service)load_service(1);
    loaded=m[0x29];if(loaded>=20){source_fault=0xfffd;return;}
    ++contact_generation;index_ready=0;paint_count=paint_cursor=0;
    animation_pending=0;animation_fallback_count=0;animation_fallback_dirty=0;
    animation_count=0;animation_started=0;glyph_changed_count=0;
    for(i=0;i<256;i++)glyph_changes[i]=0;
    for(i=0;i<1024;i++){character_cache[i].generation=0;cache_references[i]=0;}
    for(i=0;i<1000;i++){cell_cache[i]=65535;cell_stamp[i]=0;paint_queued[i]=0;dirty_cells[i]=0;}
    actor_loading_pending=1;++actor_loading_epoch;++revision;
}
static void source_actor_loading_end(void){
    unsigned short i;
    if(!actor_loading_pending)return;
    loaded=m[0x29];if(loaded>=20){source_fault=0xfffc;return;}
    prepare_palette();index_screen();paint_count=paint_cursor=0;
    for(i=0;i<1000;i++){flash_cells[i]=0;paint_rows[i]=0;paint_queued[i]=0;}
    if(loaded==19){unsigned short row,col;for(row=17;row<25;row++)for(col=4;col<=32;col++)flash_cells[row*40+col]=1;}
    flash_changed=0;old_bank=m[0xf2];contact_bank=0;
    for(i=120;i<1000;i++){dirty_cells[i]=paint_queued[i]=1;paint_rows[i]=255;paint_list[paint_count++]=i;}
    actor_loading_pending=0;++revision;
    if(load_service)load_service(0);
}
void bl_c64_world_start(long players,long human_yamo){
    unsigned char high[3],had_world=actor_world_enabled,i;
    for(i=0;i<3;i++)high[i]=m[0x4388 + i];
    bl_c64_reset();
    if(had_world)for(i=0;i<3;i++)m[0x4388 + i]=high[i];
    m[0x42c9]=(unsigned char)(players==2);m[0x42ca]=(unsigned char)(human_yamo!=0);
    m[0x42cb]=m[0x42c9];m[0x42cc]=m[0x42ca];
    actor_world_enabled=1;actor_input=actor_yamo_input=0;
    a=x=y=c=z=n=v=d=0;sp=253;actor_return=0;actor_preparing=1;
    actor_code(0x0743);actor_preparing=0;source_actor_loading_end();flush_glyph_changes();
}
void bl_c64_world_input(long input,long yamo_input){actor_input=(unsigned char)input;actor_yamo_input=(unsigned char)yamo_input;}
unsigned char bl_c64_world_ready(void){return (unsigned char)(actor_world_enabled && !m[0x48]);}
void bl_c64_world_step(long infinite_lives,long invincible){
    if(!bl_c64_world_ready() || actor_reset_pending || source_fault)return;
    PERF_BEGIN(BL_PERF_GAME);
    actor_infinite=(unsigned char)(infinite_lives!=0);actor_invincible=(unsigned char)(invincible!=0);
    actor_stop_pc=0;
    a=0;NZ(a); /* Every suspended wait reads its now-zero $48. */
    if(actor_delay_pending){actor_delay_pending=0;actor_code(0x0f71);}
    else if(actor_gameover_pending){
        unsigned char stage=actor_gameover_pending;actor_gameover_pending=0;
        actor_code(stage==1?0x196c:0x1981);
    }else{
        /* $1C32-$1C36 exits its wait with A=0/Z=1. Other flags and stack
         * retain the source context, including non-local lifetime returns. */
        a=0;NZ(a);actor_code(0x1bc2);
    }
    /* A source JSR may have yielded at a field wait. Resume its real
     * return address, rather than inventing a lifetime/turn transition. */
    while(!actor_stop_pc && !actor_delay_pending && !actor_gameover_pending && !actor_reset_pending && !source_fault){
        actor_code(actor_return);
    }
    source_actor_loading_end();flush_glyph_changes();
    if(display_dirty || old_bank!=m[0xf2])++revision;
    PERF_END(BL_PERF_GAME);
}
void bl_c64_world_jump(long room){
    unsigned char i;
    if(room<0 || room>=20)return;
    bl_c64_debug_complete_before(room);
    for(i=1;i<3;i++){x=i;actor_code(0x3001);}
    m[0x8b]=m[0x8c]=0;m[0xd1]=36;m[0x51]=0;m[0x4e]=(unsigned char)room;
    a=m[0x4bae + room];y=m[0x4bc2 + room];
    actor_debug_target=(unsigned char)room;actor_preparing=1;actor_delay_pending=actor_gameover_pending=actor_reset_pending=0;
    actor_code(0x2f9a);actor_preparing=0;actor_debug_target=255;source_actor_loading_end();flush_glyph_changes();
}
void bl_c64_world_actor(long actor,BlC64Actor *out){
    unsigned char i=(unsigned char)actor;
    out->active=m[0x95 + i];out->x=m[0x9e + i];out->y=m[0xa1 + i];out->facing=m[0xa4 + i];
    out->state=m[0xbf + i];out->counter=m[0xce + i];out->previous=m[0xc2 + i];out->animation=m[0xcb + i];out->wait=m[0x106 + i];
    out->contact=m[0xb6 + i];out->body_contact=m[0xa7 + i];out->net_delay=m[0xad + i];out->net_hold=m[0xaa + i];out->fall_push=m[0xb0 + i];
    out->pose=m[0x4f48 + i];out->mask=m[0x4f4e + i];out->quota=m[0x4f45 + i];out->health=m[0xd1 + i];
    out->respawn=i==1?m[0x5e]:i==2?m[0x5d]:0;
}
unsigned long bl_c64_world_stat(long index){
    switch(index){
    case 0:return actor_logic_steps;case 1:return actor_spawn_events;case 2:return actor_life_events;
    case 3:return actor_gameover_pending;case 4:return actor_reset_pending;case 5:return m[3];
    case 6:return m[0x28];case 7:return ((unsigned long)m[0x41]<<16)|((unsigned long)m[0x42]<<8)|m[0x43];
    case 8:return m[0x40];case 9:return actor_loading_epoch;default:return 0;
    }
}
unsigned char bl_c64_read(long address){return m[address];}
void bl_c64_test_write(long address,long value){
    m[(unsigned short)address]=(unsigned char)value;
    if(address>=0x9000 && address<0x9a20)reset_contact_masks();
}
unsigned short bl_c64_fault(void){return source_fault;}
unsigned char bl_c64_room(void){return loaded;}
unsigned short bl_c64_revision(void){return revision;}
unsigned char bl_c64_screen(long cell){return m[0x8c00 + cell];}
unsigned char bl_c64_screen_color(long cell){return m[0xd800 + cell]&7;}
unsigned char bl_c64_glyph(long code,long row){return m[charset()+((unsigned short)code<<3)+row];}
unsigned char bl_c64_cell_dirty(long cell){return (unsigned char)(dirty_cells[cell]||dirty_glyphs[m[0x8c00 + cell]]||old_bank!=m[0xf2]);}
void bl_c64_clear_dirty(void){
    unsigned short i,keep=0,cell;invalidate_contacts();
    for(i=0;i<paint_count;i++){
        cell=paint_list[i];
        if(paint_queued[cell]==3){paint_queued[cell]=1;paint_list[keep++]=cell;}
        else{dirty_cells[cell]=paint_queued[cell]=0;paint_rows[cell]=0;}
    }
    paint_count=keep;paint_cursor=0;animation_pending=0;animation_started=0;
    old_bank=m[0xf2];display_dirty=(unsigned char)(keep!=0);flash_changed=0;
}

unsigned char bl_c64_tile(long column,long row){
    if(column>=40||row<2||row>12)return 6;
    return m[0x8c00 + (row*2-1)*40+column]&127;
}
unsigned char bl_c64_attribute(long column,long row){
    if(column>=40||row<2||row>12)return 8;
    return m[0xd800 + (row*2-1)*40+column]&15;
}
unsigned char bl_c64_charset_row(long tile,long row){
    return m[charset()+((unsigned short)(tile|(row>=8?128:0))<<3)+(row&7)];
}
unsigned char bl_c64_pixel(long px,long py){
    unsigned short cell;unsigned char bits,color;
    if(px<0||px>=320||py<24||py>=200)return 0;
    cell=(unsigned short)((py>>3)*40+(px>>3));
    bits=m[charset()+((unsigned short)m[0x8c00 + cell]<<3)+(py&7)];
    bits=(unsigned char)((bits>>(6-(px&6)))&3);
    color=m[0xd800 + cell]&7;
    return bits==3?(unsigned char)(color?4:8):bits;
}
static void contact_cell(unsigned short cell,unsigned short bank){
    unsigned short base=cell_offsets[cell],glyph=(unsigned short)(bank+((unsigned short)m[0x8c00 + cell]<<3));
    const unsigned char *src=m+glyph;unsigned char *bitmap=contact_bitmap+base;
    const unsigned short *lookup=coverage_table[(m[0xd800 + cell]&7)!=0];
    unsigned short *coverage=contact_coverage+base;
#define CONTACT_ROW(r) do{unsigned char bits=src[r];bitmap[(r)*40]=bits;coverage[(r)*40]=lookup[bits];}while(0)
    CONTACT_ROW(0);CONTACT_ROW(1);CONTACT_ROW(2);CONTACT_ROW(3);
    CONTACT_ROW(4);CONTACT_ROW(5);CONTACT_ROW(6);CONTACT_ROW(7);
#undef CONTACT_ROW
    contact_cells[cell]=0;contact_epoch[cell]=glyph_epoch[m[0x8c00 + cell]];
}
static void prepare_contact_view(int px,int py){
    unsigned short bank=charset(),cell;int row,col,first=px>=0?px>>3:-((-px+7)>>3);
    if(contact_bank!=bank){for(cell=120;cell<1000;cell++)contact_cells[cell]=1;contact_bank=bank;}
    for(row=(py-21)>>3;row<=((py-1)>>3);row++)if(row>=3&&row<25)
        for(col=first;col<=first+3;col++)if(col>=0&&col<40){
            cell=(unsigned short)(row*40+col);
            if(contact_cells[cell] || contact_epoch[cell]!=glyph_epoch[indexed_screen[cell]])contact_cell(cell,bank);
        }
}
static unsigned char constant_mask_slot(unsigned char pose,unsigned short pointer,unsigned char band){
    unsigned char i,slot=0,row,column,kind,shift=(unsigned char)(band*2);
    unsigned short oldest=0,age;
    if(pose>68)return 255;
    kind=constant_classes[pose>>1];
    if(!kind){
        kind=1;
        for(column=0;column<3;column++)for(row=0;row<21;row++){
            unsigned char bits=m[pointer+column*32+row];
            if((column==2 && bits) || (bits&0x55)!=((bits>>1)&0x55))kind=2;
        }
        constant_classes[pose>>1]=kind;
    }
    if(kind==2)return 255; /* Keep partial pairs and a third column exact. */
    if(pose!=2){
        for(i=1;i<5;i++){
            if(constant_poses[i]==pose){slot=i;goto found;}
            if(constant_poses[i]==255){slot=i;oldest=65535;}
            else if(oldest!=65535){age=(unsigned short)(contact_use-constant_ages[i]);if(age>=oldest){oldest=age;slot=i;}}
        }
    }else if(constant_poses[0]==2)goto found;
    constant_poses[slot]=pose;constant_bands[slot]=0;
found:
    constant_ages[slot]=contact_use;
    if(constant_bands[slot]&(1<<band))return slot;
    /* Build only the requested even-X shift. Eagerly building all four
     * bands made short-lived kick/jump poses exceed the 68000 budget. */
    for(row=0;row<21;row++){
        unsigned char left=m[pointer+row],right=m[pointer+32+row];
        constant_masks[slot][band][row][0]=(unsigned char)(left>>shift);
        constant_masks[slot][band][row][1]=shift?(unsigned char)((right>>shift)|(left<<(8-shift))):right;
        constant_masks[slot][band][row][2]=shift?(unsigned char)(right<<(8-shift)):0;
    }
    constant_bands[slot]|=(unsigned char)(1<<band);return slot;
}
unsigned char bl_c64_contact(long px_arg,long py_arg,long pose_arg,long body_arg){
    if(io_service)io_service();
    PROFILE_START(query_start);
    int px=(int)px_arg,py=(int)py_arg;unsigned char pose=(unsigned char)pose_arg,body_only=(unsigned char)body_arg;
    unsigned char slot,probe,constant_slot;unsigned short oldest=0,age;
    unsigned short ptr,cell;
    unsigned char all=0,body=0,yy,cc,shift,bits,previous,mask,hit,flag,fast,columns;
    int column,sy,first;
    pose&=254;
    invalidate_contacts();++contact_use;
    for(probe=0;probe<8;probe++){
        slot=(unsigned char)(probe==0?contact_last:probe<=contact_last?probe-1:probe);
        if(contact_cache[slot].valid && px==contact_cache[slot].x && py==contact_cache[slot].y &&
           pose==contact_cache[slot].pose && loaded==contact_cache[slot].room && contact_generation==contact_cache[slot].generation){
            contact_cache[slot].used=contact_use;contact_last=slot;
            PROFILE_END(query_start,6);
            return body_only?contact_cache[slot].body:contact_cache[slot].all;
        }
    }
    PROFILE_START(contact_start);++profile[0];
    prepare_contact_view(px,py);
    ptr=(unsigned short)(m[0x1167 + pose]|((unsigned short)m[0x1239 + pose]<<8));
    first=px>=0?px>>3:-((-px+7)>>3);shift=(unsigned char)(px&7);
    constant_slot=constant_mask_slot(pose,ptr,(unsigned char)(shift>>1));
    if(constant_slot<5 && !(shift&1) && px>=0 && px<=302 && loaded!=19){
        unsigned short all_hit=0,body_hit=0,hit;
        const unsigned char *masks;
        const unsigned short *background;
        int begin=0,end=21;
        sy=py-21;if(sy<24)begin=24-sy;if(sy+end>200)end=200-sy;
        if(begin<end){
        masks=constant_masks[constant_slot][shift>>1][begin];background=contact_coverage+(sy+begin)*40+first;
        for(yy=(unsigned char)begin;yy<end;yy++,masks+=3,background+=40){
            if(yy==15)body_hit=all_hit;
            hit=(background[0]&spread_masks[masks[0]])|(background[1]&spread_masks[masks[1]]);
            if(shift)hit|=background[2]&spread_masks[masks[2]];
            all_hit|=hit;
        }
        if(end<=15)body_hit=all_hit;
        }
        if(all_hit&0xf000)all|=1;
        if(all_hit&0x0f00)all|=2;
        if(all_hit&0x00f0)all|=4;
        if(all_hit&0x000f)all|=8;
        if(body_hit&0xf000)body|=1;
        if(body_hit&0x0f00)body|=2;
        if(body_hit&0x00f0)body|=4;
        if(body_hit&0x000f)body|=8;
        goto cache_result;
    }
    fast=(unsigned char)(pose==2 && constant_slot==0 && !(shift&1));columns=(unsigned char)(fast?(shift?3:2):(shift?4:3));
    for(yy=0;yy<21;yy++){
        sy=py-21+yy;if(sy<24||sy>=200)continue;
        cell=(unsigned short)(sy*40);previous=0;
        if(first>=0 && first+3<40 && !(contact_bitmap[cell+first]|contact_bitmap[cell+first+1]|contact_bitmap[cell+first+2]|contact_bitmap[cell+first+3]))continue;
        for(cc=0;cc<columns;cc++){
            if(fast)mask=constant_masks[0][shift>>1][yy][cc];
            else{
                bits=cc<3?m[(unsigned short)(ptr+cc*32+yy)]:0;
                mask=shift?(unsigned char)((bits>>shift)|(previous<<(8-shift))):bits;
                previous=bits;
            }
            if(!mask)continue;
            column=first+cc;if(column<0||column>=40)continue;
            {unsigned short at=(unsigned short)(cell+column);
            hit=(unsigned char)(mask&contact_bitmap[at]);
            if(!hit)continue;
            flag=contact_classes[(m[0xd800 + ((sy>>3)*40)+column]&7)!=0][hit];
            all|=flag;if(yy<15)body|=flag;}
        }
    }
cache_result:
    slot=0;
    for(probe=0;probe<8;probe++){
        if(!contact_cache[probe].valid || contact_cache[probe].generation!=contact_generation){slot=probe;break;}
        age=(unsigned short)(contact_use-contact_cache[probe].used);if(age>=oldest){oldest=age;slot=probe;}
    }
    contact_cache[slot].valid=1;contact_last=slot;contact_cache[slot].used=contact_use;
    contact_cache[slot].x=px;contact_cache[slot].y=py;contact_cache[slot].pose=pose;contact_cache[slot].room=loaded;
    contact_cache[slot].generation=contact_generation;contact_cache[slot].all=all;contact_cache[slot].body=body;
    {int row,column,top=(py-21)>>3,bottom=(py-1)>>3;contact_cache[slot].view_count=0;
    for(row=top;row<=bottom;row++)for(column=first;column<=first+3;column++)
        if(row>=3&&row<25&&column>=0&&column<40){
            unsigned char index=contact_cache[slot].view_count++;unsigned short at=(unsigned short)(row*40+column);
            contact_cache[slot].view[index]=at;contact_cache[slot].view_epoch[index]=glyph_epoch[indexed_screen[at]];
        }}
    PROFILE_END(contact_start,3);
    PROFILE_END(query_start,6);
    return body_only?body:all;
}
unsigned char bl_c64_has_dirty(void){return display_dirty || old_bank!=m[0xf2];}

static void prepare_palette(void){
    unsigned short palette=W((unsigned short)(0x480b + 2*loaded));
    unsigned short raster=W((unsigned short)(0x4833 + 2*loaded));
    unsigned short py,band,color,bits;unsigned char j;
    /* These coverage/spread tables depend only on the byte value. */
    if(!BL_ROOM_REUSE || !coverage_ready){for(bits=0;bits<256;bits++){
        unsigned char low=bits&0x55,high=(bits>>1)&0x55,flag=0;
        unsigned char one=(unsigned char)(low&~high),two=(unsigned char)(high&~low),three=(unsigned char)(low&high);
        unsigned short base;unsigned char pairs;
#define CONTACT_PAIRS(b) (((b)&1)|(((b)>>1)&2)|(((b)>>2)&4)|(((b)>>3)&8))
        one=(unsigned char)CONTACT_PAIRS(one);two=(unsigned char)CONTACT_PAIRS(two);three=(unsigned char)CONTACT_PAIRS(three);
        base=((unsigned short)one<<12)|((unsigned short)two<<8);
        coverage_table[0][bits]=base|three;coverage_table[1][bits]=base|((unsigned short)three<<4);
        pairs=(unsigned char)CONTACT_PAIRS(bits);
#undef CONTACT_PAIRS
        spread_masks[bits]=((unsigned short)pairs<<12)|((unsigned short)pairs<<8)|((unsigned short)pairs<<4)|pairs;
        if(low&(unsigned char)~high)flag|=1;
        if(high&(unsigned char)~low)flag|=2;
        contact_classes[0][bits]=(unsigned char)(flag|((low&high)?8:0));
        contact_classes[1][bits]=(unsigned char)(flag|((low&high)?4:0));
#if BL_ROOM_REUSE
        {unsigned long value=(unsigned char)((low&high)|((low&high)<<1));
        unsigned long mask=(value<<24)|(value<<16)|(value<<8)|value;
        for(color=0;color<9;color++)planar_foreground[color][bits]=mask&source_color_planes[color==8?15:color];}
#endif
    }coverage_ready=1;}
    reset_contact_masks();
    for(py=0;py<200;py++){
        band=0;
        for(j=0;j<3;j++){
            unsigned char line=m[raster+j];if(line==253)break;
            if(py+51 >= (unsigned short)line+3)++band;else break;
        }
        line_band[py]=(unsigned char)band;
        for(j=0;j<3;j++)line_colors[py][j]=m[palette+band*3+j]&15;
    }
    /* Raster bands are always refreshed. Only the pixel-to-plane LUT is
     * reusable, and only after comparing all twelve effective colors. */
    if(BL_ROOM_REUSE && palette_ready){
        for(j=0;j<12;j++)if(palette_key[j]!=(m[palette+j]&15))break;
        if(j==12){++reuse_stats[0];return;}
    }
    ++reuse_stats[1];palette_ready=1;
    for(j=0;j<12;j++)palette_key[j]=m[palette+j]&15;
    {
#if BL_ROOM_REUSE
    const unsigned long *color_planes=source_color_planes;
#else
    unsigned long color_planes[16];
    for(color=0;color<16;color++){
        unsigned long packed=0;unsigned char plane;
        for(plane=0;plane<4;plane++)packed=(packed<<8)|((color&(1<<plane))?255:0);
        color_planes[color]=packed;
    }
#endif
    for(band=0;band<4;band++)for(bits=0;bits<256;bits++){
        unsigned char low=bits&0x55,high=(bits>>1)&0x55,j;
        unsigned char masks[4];unsigned long spread[4],base;
        masks[0]=(unsigned char)(~low&~high&0x55);masks[1]=(unsigned char)(low&~high);
        masks[2]=(unsigned char)(high&~low);masks[3]=(unsigned char)(low&high);
        for(j=0;j<(BL_ROOM_REUSE?3:4);j++){
            unsigned long value=(unsigned char)(masks[j]|(masks[j]<<1));
            spread[j]=(value<<24)|(value<<16)|(value<<8)|value;
        }
        base=(spread[0]&color_planes[m[palette+band*3]&15])|
             (spread[1]&color_planes[m[palette+band*3+1]&15])|
             (spread[2]&color_planes[m[palette+band*3+2]&15]);
#if BL_ROOM_REUSE
        planar_base[band][bits]=base;
#else
        for(color=0;color<9;color++)planar_lut[band][color][bits]=base|(spread[3]&color_planes[color==8?15:color]);
#endif
    }}
}
void bl_c64_colors(long py,unsigned char *out){unsigned char i;for(i=0;i<3;i++)out[i]=line_colors[py][i];}
unsigned long bl_c64_planar(long bits,long color,long py){return PLANAR_WORD(line_band[py],color&7,bits);}

#if defined(__m68k__)
#define COPY_ROW(r) "move.b " #r "(%0)," #r "*40(%1)\n\t" \
    "move.b " #r "+8(%0)," #r "*40+10240(%1)\n\t" \
    "move.b " #r "+16(%0)," #r "*40+20480(%1)\n\t" \
    "move.b " #r "+24(%0)," #r "*40+30720(%1)\n\t"
static __inline__ __attribute__((always_inline)) void copy_character(const unsigned char *src,unsigned char *target){
        __asm__ volatile(COPY_ROW(0) COPY_ROW(1) COPY_ROW(2) COPY_ROW(3)
                         COPY_ROW(4) COPY_ROW(5) COPY_ROW(6) COPY_ROW(7)
                         : : "a"(src),"a"(target) : "memory","cc");
}
#undef COPY_ROW
#endif

static void paint_cell(unsigned char *planes,unsigned short cell,unsigned short scene_top,unsigned char rows){
    unsigned short base=cell_offsets[cell];
    unsigned char code=m[0x8c00 + cell],row;
    unsigned short index=cell_cache[cell];unsigned char changed=0;CharacterCache *entry;
    if(index==65535){
        unsigned short cy=cell_y[cell];
        unsigned char color=(unsigned char)(loaded==19&&flash_cells[cell]?8:m[0xd800 + cell]&7);
        unsigned char phase=(unsigned char)(line_band[cy]==line_band[cy+7]?line_band[cy]:4+(cy>>3));
        unsigned long tag=(unsigned long)code|((unsigned long)color<<8)|((unsigned long)phase<<12);
        index=(unsigned short)((code+((unsigned short)color<<5)+((unsigned short)phase<<7))&1023);
        while(character_cache[index].generation==contact_generation && character_cache[index].tag!=tag && cache_references[index])index=(unsigned short)((index+1)&1023);
        entry=&character_cache[index];
        if(entry->generation!=contact_generation || entry->tag!=tag){entry->tag=tag;entry->generation=contact_generation;entry->epoch=(unsigned short)(glyph_epoch[code]-1);}
        cell_cache[cell]=index;cell_stamp[cell]=entry->planes[0];++cache_references[index];
    }else entry=&character_cache[index];
    if(entry->epoch!=glyph_epoch[code]){
        changed=1;
        unsigned short cy=cell_y[cell];unsigned char color=(unsigned char)((entry->tag>>8)&15);
        unsigned short glyph=(unsigned short)(charset()+((unsigned short)code<<3));
        for(row=0;row<8;row++){
            unsigned char bits=m[glyph+row];unsigned long packed=PLANAR_WORD(line_band[cy+row],color,bits);
            entry->planes[0][row]=(unsigned char)(packed>>24);entry->planes[1][row]=(unsigned char)(packed>>16);
            entry->planes[2][row]=(unsigned char)(packed>>8);entry->planes[3][row]=(unsigned char)packed;
        }
        entry->epoch=glyph_epoch[code];
    }
    if(tile_painter){
        paint_request.bitmap=planes;paint_request.scene_top=scene_top;paint_request.cell=cell;
        paint_request.slot=index;paint_request.planes=entry->planes[0];paint_request.changed=changed;
        tile_painter(&paint_request);return;
    }
    {unsigned char *target=planes+scene_top*40+base;const unsigned char *src=entry->planes[0];
#if defined(__m68k__)
    (void)rows;
    copy_character(src,target);
#else
    for(row=0;row<8;row++,target+=40,src++)if(rows&(1u<<row)){
        target[0]=src[0];target[10240]=src[8];target[20480]=src[16];target[30720]=src[24];
    }
#endif
    }
}
static void ensure_paint_bank(void){
    unsigned short cell;
    if(paint_bank==m[0xf2])return;
    for(cell=0;cell<1024;cell++){character_cache[cell].generation=0;cache_references[cell]=0;}
    for(cell=0;cell<1000;cell++){cell_cache[cell]=65535;cell_stamp[cell]=0;}
    for(cell=0;cell<2048;cell++)indexed_glyph[cell]=m[charset()+cell];
    paint_bank=m[0xf2];
}
unsigned char bl_c64_needs_full_paint(void){return paint_bank!=m[0xf2];}
void bl_c64_paint_room(unsigned char *planes,long scene_top){
    unsigned short cell;ensure_paint_bank();for(cell=120;cell<1000;cell++)paint_cell(planes,cell,(unsigned short)scene_top,255);
}
const unsigned short *bl_c64_paint_changes(unsigned char *planes,long scene_top,unsigned short *count){
    unsigned short item,cell;unsigned char bank_changed=old_bank!=m[0xf2];
    if(bank_changed){
        ensure_paint_bank();
        for(cell=0;cell<2048;cell++)indexed_glyph[cell]=m[charset()+cell];
        for(cell=120;cell<1000;cell++){release_cell_cache(cell);mark_cell(cell,1,255);}
    }
    if(animation_pending){unsigned char code;for(code=0x61;code<=0x63;code++){
        for(cell=glyph_first(code);cell!=65535;cell=glyph_next[cell])mark_cell(cell,0,255);
        for(cell=glyph_first(code|128);cell!=65535;cell=glyph_next[cell])mark_cell(cell,0,255);
    }}
    *count=paint_count;
    for(item=0;item<paint_count;item++){
        cell=paint_list[item];paint_queued[cell]=2;
        paint_cell(planes,cell,(unsigned short)scene_top,paint_rows[cell]);
    }
    return paint_list;
}
/* Source $2CF1-$2D54: three8x16 glyphs, each source row duplicated.
 * Cache only that exact eight-phase byte sequence. A runtime byte comparison
 * and per-rectangle screen/attribute checks guard every accelerated draw. */
static unsigned char animation_bits(unsigned char code,unsigned char row,unsigned char phase){
    return animation_pattern[((code&127)-0x61)*8+((phase+(row>>1)+(code&128?4:0))&7)];
}
static unsigned char animated_code(unsigned char code){return (code&127)>=0x61 && (code&127)<=0x63;}
static unsigned char animation_reusable(unsigned char *cache,long capacity){
    unsigned short i,palette=W((unsigned short)(0x480b + 2*loaded));
    if(!BL_ROOM_REUSE || !cache || cache!=animation_cache || !animation_saved_count ||
       capacity<(long)animation_saved_bytes || (charset()!=0xa000 && charset()!=0xa800))return 0;
    for(i=0;i<24;i++)if(animation_pattern[i]!=m[(loaded<10?0x42f1:0x4309)+i])return 0;
    for(i=0;i<12;i++)if(animation_saved_palette[i]!=(m[palette+i]&15))return 0;
    for(i=0;i<200;i++)if(animation_saved_bands[i]!=line_band[i])return 0;
    for(i=120;i<1000;i++){
        unsigned char code=m[0x8c00 + i];
        if(animated_code(code)){
            if(animation_cell[i]==65535 || animation_code[i]!=code ||
               animation_color[i]!=(m[0xd800 + i]&7))return 0;
        }else if(animation_cell[i]!=65535)return 0;
    }
    return 1;
}
long bl_c64_build_animation_cache(unsigned char *cache,long capacity){
    unsigned short row,col,item,cell;unsigned long used=0,total=0,groups[2]={0,0};
    unsigned char reuse=animation_reusable(cache,capacity);
    animation_count=0;animation_cache=cache;animation_fallback_count=0;animation_fallback_dirty=0;
    animation_checked_revision=(unsigned short)(revision-1);animation_phase_valid=0;
    if(reuse){
        ++reuse_stats[2];animation_count=animation_saved_count;
        for(cell=0;cell<1000;cell++)animation_mismatch[cell]=0;
        for(item=0;item<128;item++)animation_differences[item]=0;
        return (long)animation_saved_bytes;
    }
    ++reuse_stats[3];animation_saved_count=0;
    for(item=0;item<24;item++)animation_pattern[item]=m[(loaded<10?0x42f1:0x4309)+item];
    {unsigned short phase,code,dy;for(phase=0;phase<8;phase++)for(code=0;code<6;code++)for(dy=0;dy<8;dy++)
        animation_variants[phase][code*8+dy]=animation_bits((unsigned char)(0x61 + code%3+(code>=3?128:0)),(unsigned char)dy,(unsigned char)phase);}
    for(cell=0;cell<1000;cell++){animation_cell[cell]=65535;animation_mismatch[cell]=0;}
    for(item=0;item<128;item++)animation_differences[item]=0;
    if(!cache || (charset()!=0xa000 && charset()!=0xa800))return 0;
    for(row=3;row<25;row++)for(col=0;col<40;){
        unsigned short left=col,right,found=65535;
        if(!animated_code(m[0x8c00 + row*40+col])){++col;continue;}
        do{++col;}while(col<40 && animated_code(m[0x8c00 + row*40+col]));right=col;
        for(item=0;item<animation_count;item++)if(animation_rects[item].bottom==row && animation_rects[item].left==left && animation_rects[item].right==right){found=item;break;}
        if(found==65535){
            if(animation_count==128){animation_count=0;return 0;}
            found=animation_count++;animation_rects[found].left=left;animation_rects[found].right=right;animation_rects[found].top=row;
        }
        animation_rects[found].bottom=row+1;
    }
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];
        total+=(unsigned long)(((rect->right+1)&~1)-(rect->left&~1))*(rect->bottom-rect->top)*32;
    }
    /* Balance presentation work over two fields. Split a tall dominant
     * rectangle on an exact character-row boundary before assigning groups. */
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];
        unsigned long size=(unsigned long)(((rect->right+1)&~1)-(rect->left&~1))*(rect->bottom-rect->top)*32;
        if(size>total/2 && rect->bottom-rect->top>1){
            unsigned short middle=(unsigned short)((rect->top+rect->bottom)/2);
            if(animation_count==128){animation_count=0;return 0;}
            animation_rects[animation_count]=*rect;animation_rects[animation_count++].top=middle;rect->bottom=middle;
        }
    }
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];rect->group=255;
        rect->size=(unsigned long)(((rect->right+1)&~1)-(rect->left&~1))*(rect->bottom-rect->top)*32;
    }
    for(item=0;item<animation_count;item++){
        unsigned short probe,largest=65535;unsigned char group=(unsigned char)(groups[0]>groups[1]);
        for(probe=0;probe<animation_count;probe++)if(animation_rects[probe].group==255 &&
            (largest==65535 || animation_rects[probe].size>animation_rects[largest].size))largest=probe;
        animation_rects[largest].group=group;groups[group]+=animation_rects[largest].size;
    }
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];unsigned short left=rect->left&~1,right=(rect->right+1)&~1,width=right-left;
        unsigned char phase,dy,plane;
        rect->offset=used;rect->size=(unsigned long)width*(rect->bottom-rect->top)*32;
        used+=rect->size*8;if(used>(unsigned long)capacity){animation_count=0;return 0;}
        rect->words=((1UL<<(right>>1))-1)^((1UL<<(left>>1))-1);
        for(row=rect->top;row<rect->bottom;row++)for(col=rect->left;col<rect->right;col++){
            cell=row*40+col;animation_cell[cell]=item;animation_code[cell]=m[0x8c00 + cell];animation_color[cell]=m[0xd800 + cell]&7;
        }
        if(BL_ROOM_REUSE){
            unsigned char *dest=animation_cache+rect->offset;
            for(phase=0;phase<8;phase++)for(row=rect->top;row<rect->bottom;row++)for(dy=0;dy<8;dy++){
                unsigned char *p0=dest,*p1=dest+width,*p2=dest+width*2,*p3=dest+width*3;
                unsigned char band=line_band[row*8+dy];cell=row*40+left;
                /* The exact eight source variants are already computed.
                 * Advance pointers instead of multiplying an offset for
                 * each output byte on the68000. */
                for(col=left;col<right;col++,cell++){
                    unsigned long packed=0;
                    if(col>=rect->left && col<rect->right){
                        unsigned char code=animation_code[cell];
                        unsigned char at=(unsigned char)(((code&127)-0x61)*8+(code&128?24:0)+dy);
                        packed=PLANAR_WORD(band,animation_color[cell],animation_variants[phase][at]);
                    }
                    *p0++=(unsigned char)(packed>>24);*p1++=(unsigned char)(packed>>16);
                    *p2++=(unsigned char)(packed>>8);*p3++=(unsigned char)packed;
                }
                dest+=width*4;
            }
        }else for(phase=0;phase<8;phase++)for(row=rect->top;row<rect->bottom;row++)for(dy=0;dy<8;dy++)for(col=left;col<right;col++){
            unsigned long packed=0,at;cell=row*40+col;
            if(col>=rect->left && col<rect->right)packed=PLANAR_WORD(line_band[row*8+dy],animation_color[cell],animation_bits(animation_code[cell],dy,phase));
            at=rect->offset+(unsigned long)phase*rect->size+((row-rect->top)*8+dy)*4*width+col-left;
            for(plane=0;plane<4;plane++){animation_cache[at+plane*width]=(unsigned char)(packed>>24);packed<<=8;}
        }
    }
    animation_saved_count=animation_count;animation_saved_bytes=used;
    {unsigned short palette=W((unsigned short)(0x480b + 2*loaded));
    for(item=0;item<12;item++)animation_saved_palette[item]=m[palette+item]&15;}
    for(item=0;item<200;item++)animation_saved_bands[item]=line_band[item];
    return (long)used;
}
void bl_c64_prepare_paint(void){
    unsigned char count,phase=m[0x64]&7;const unsigned char *actual,*expected;
    if(animation_fallback_dirty){
        unsigned short item;rebuild_animation_fallback();
        if(animation_pending)for(item=0;item<animation_fallback_count;item++)mark_cell(animation_fallback[item],0,255);
    }
    if(!animation_count || animation_checked_revision==revision)return;
    animation_checked_revision=revision;animation_phase_valid=0;
    actual=m+charset()+0x308;expected=animation_variants[phase];
    for(count=0;count<24;count++,actual++,expected++)
        if(actual[0]!=expected[0] || actual[1024]!=expected[24]){
            unsigned char code;unsigned short cell;for(code=0x61;code<=0x63;code++){
                for(cell=glyph_first(code);cell!=65535;cell=glyph_next[cell])mark_cell(cell,0,255);
                for(cell=glyph_first(code|128);cell!=65535;cell=glyph_next[cell])mark_cell(cell,0,255);
            }
            return;
        }
    animation_phase_valid=1;
}
/* A displayed frame must not mix the two background-work groups. Only
 * verified cache rectangles are overlaid, using one source $64 phase.
 * Whole covered words may bypass the background-copy budget; masked edge
 * words still need their normal copy for the adjacent non-animated byte. */
static void paint_animation_rect(unsigned char *planes,unsigned short scene_top,unsigned short item,unsigned char phase){
    AnimationRect *rect=&animation_rects[item];BlC64Block request;
    request.bitmap=planes;request.pixels=animation_cache+rect->offset+(unsigned long)phase*rect->size;
    request.left=rect->left&~1;request.top=scene_top+rect->top*8;
    request.width=((rect->right+1)&~1)-request.left;request.height=(rect->bottom-rect->top)*8;
    request.first_mask=(rect->left&1)?0x00ff:0xffff;request.last_mask=(rect->right&1)?0xff00:0xffff;
    block_painter(&request);
}
const unsigned long *bl_c64_animation_coverage(void){
    unsigned short item,row;
    if(!block_painter || !animation_phase_valid || !animation_count)return 0;
    /* The caller has consumed this paint-part metadata before presentation.
     * Reuse it as coverage scratch; no additional Chip/slow allocation. */
    for(row=0;row<25;row++)part_priority_words[row]=0;
    for(item=0;item<animation_count;item++)if(!animation_differences[item]){
        AnimationRect *rect=&animation_rects[item];
        unsigned short first=(rect->left+1)>>1,last=rect->right>>1;
        unsigned long words=((1UL<<last)-1)^((1UL<<first)-1);
        for(row=rect->top;row<rect->bottom;row++)part_priority_words[row]|=words;
    }
    return part_priority_words;
}
void bl_c64_paint_animation_frame(unsigned char *planes,long scene_top){
    unsigned short item;unsigned char phase=m[0x64]&7;
    if(!block_painter || !animation_phase_valid)return;
    for(item=0;item<animation_count;item++)if(!animation_differences[item])
        paint_animation_rect(planes,(unsigned short)scene_top,item,phase);
}
static void paint_animation_blocks(unsigned char *planes,unsigned short scene_top){
    PROFILE_START(bulk_start);
    unsigned short item,row;unsigned char phase=m[0x64]&7,needed=0;
    profile[4]=0;
    if(!animation_started){
        animation_started=1;animation_ready=0;animation_part=0;
        for(item=0;item<animation_count;item++)animation_done[item]=0;
        if(!block_painter || !animation_count)return;
        for(item=0;item<paint_count;item++)if(animation_cell[paint_list[item]]!=65535){needed=1;break;}
        if(!needed && !animation_pending)return;
        bl_c64_prepare_paint();if(!animation_phase_valid)return;
        animation_ready=1;
    }
    if(!animation_ready || animation_part>=2)return;
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];
        if(animation_done[item] || animation_differences[item] || rect->group!=animation_part)continue;
        animation_done[item]=1;
        {PROFILE_START(t);paint_animation_rect(planes,scene_top,item,phase);PROFILE_END(t,0);}
        for(row=rect->top;row<rect->bottom;row++){part_words[row]|=rect->words;part_rows[row]=255;}
    }
    ++animation_part;
    PROFILE_END(bulk_start,7);
}
const unsigned short *bl_c64_paint_part(unsigned char *planes,long scene_top,long limit,unsigned short *count){
    unsigned short start=paint_cursor,cell,row,work=0;
    unsigned char *field=planes+scene_top*40;
    for(row=0;row<25;row++){part_words[row]=part_priority_words[row]=0;part_rows[row]=part_priority_rows[row]=0;}
    if(!start && old_bank!=m[0xf2]){
        ensure_paint_bank();
        for(cell=0;cell<2048;cell++)indexed_glyph[cell]=m[charset()+cell];
        for(cell=120;cell<1000;cell++){release_cell_cache(cell);mark_cell(cell,1,255);}
    }
    if(paint_count || animation_pending)paint_animation_blocks(planes,(unsigned short)scene_top);
    while(paint_cursor<paint_count){
        unsigned char rows,*stamp;
        cell=paint_list[paint_cursor];
        if(animation_ready && animation_cell[cell]!=65535 && !animation_differences[animation_cell[cell]]){
            if(!animation_done[animation_cell[cell]])break;
            ++paint_cursor;paint_queued[cell]=2;continue;
        }
        if(work++>=limit)break;
        ++paint_cursor;paint_queued[cell]=2;rows=paint_rows[cell];stamp=cell_stamp[cell];
#if defined(__m68k__)
        if(stamp && *(unsigned short*)(stamp-2)==glyph_epoch[indexed_screen[cell]]){
            if(tile_painter){
                paint_request.bitmap=planes;paint_request.scene_top=scene_top;paint_request.cell=cell;
                paint_request.slot=cell_cache[cell];paint_request.planes=stamp;paint_request.changed=0;
                tile_painter(&paint_request);
            }else copy_character(stamp,field+cell_offsets[cell]);
        }
        else
#endif
        {++profile[4];paint_cell(planes,cell,(unsigned short)scene_top,rows);}
        row=cell_y[cell]>>3;part_rows[row]|=rows;part_words[row]|=cell_word_mask[cell];
        /* Direct cell/glyph changes (moving traps, doors, lamps) must reach
         * the display before the much larger cached scrolling rectangles.
         * This changes presentation scheduling only, never source state. */
        part_priority_rows[row]|=rows;part_priority_words[row]|=cell_word_mask[cell];
    }
    *count=(unsigned short)(paint_cursor-start);return paint_list+start;
}
unsigned char bl_c64_paint_done(void){return paint_cursor==paint_count && (!animation_pending || !animation_phase_valid || animation_part>=2);}
const unsigned long *bl_c64_part_words(void){return part_words;}
const unsigned char *bl_c64_part_rows(void){return part_rows;}
const unsigned long *bl_c64_part_priority_words(void){return part_priority_words;}
const unsigned char *bl_c64_part_priority_rows(void){return part_priority_rows;}
long bl_c64_check_interleaved(const unsigned char *bitmap,long scene_top){
    unsigned short cell,row,plane,bank=charset();long mismatches=0;
    for(cell=120;cell<1000;cell++){
        unsigned char code=m[0x8c00 + cell],color=(unsigned char)(loaded==19&&flash_cells[cell]?8:m[0xd800 + cell]&7);
        unsigned short at=(unsigned short)((scene_top+cell_y[cell])*160+cell-(cell_y[cell]>>3)*40);
        for(row=0;row<8;row++){
            unsigned long packed=PLANAR_WORD(line_band[cell_y[cell]+row],color,m[bank+((unsigned short)code<<3)+row]);
            for(plane=0;plane<4;plane++){if(bitmap[at+row*160+plane*40]!=(unsigned char)(packed>>24))++mismatches;packed<<=8;}
        }
    }
    return mismatches;
}

void bl_c64_field(void){
    if(actor_world_enabled){source_actor_field();return;}
    /* $15A8/$1678: PAL field counters used by final-room wait. */
    ++m[0x16];
    m[0x44]=0; /* $15A9-$15AB interrupt handshake. */
    /* $15BD-$15CD: refill all source fall-hit quotas on the counter's zero
     * phase, then decrement it. This counter is not a three-step timer. */
    if(!m[0x4eec])m[0x4f45]=m[0x4f46]=m[0x4f47]=2;
    --m[0x4eec];
    /* $15D0-$15EC selects the contact charset every interrupt. */
    m[0x7c]=(unsigned char)(charset()>>8);
    if(m[0x48])--m[0x48]; /* $1672-$1676, main and Game Over waits. */
    /* Actual $1614-$1626 room clock: one increment per modeled PAL field,
     * paused/inactive gate, low-byte carry and high-byte saturation at128. */
    if(m[0x104] && !(m[0x105]&128)){
        if(!++m[0x87] && !(m[0x88]&128))++m[0x88];
    }
    if(m[0x49])--m[0x49];else if(m[0x4a]){--m[0x4a];--m[0x49];}
}
void bl_c64_tick_begin(long px,long py){
    if(io_service)io_service();
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;
    m[0x7c]=(unsigned char)(charset()>>8);m[2]=50;m[0x100]=0;
    /* Original main-loop $1BEE and $1BFE-$1C0A precede the room loop. */
    {PROFILE_START(t);execute(0x40bc);PROFILE_END(t,1);}
}
void bl_c64_tick_room(void){
    m[0x7b]=m[0x7b]?(unsigned char)(m[0x7b]-1):1;
    {PROFILE_START(t);execute(W((unsigned short)(0x4ec4 + 2*loaded))+1);PROFILE_END(t,2);}
    flush_glyph_changes();
    if(display_dirty || old_bank!=m[0xf2])++revision;
}
void bl_c64_tick(long px,long py){bl_c64_tick_begin(px,py);bl_c64_tick_room();}
unsigned char bl_c64_changed_rows(long cell){return paint_rows[cell];}
unsigned char bl_c64_flash_color(void){return loaded==19?(m[0xdaac]&7):15;}
const unsigned short *bl_c64_offsets(void){return cell_offsets;}
const unsigned char *bl_c64_cell_y(void){return cell_y;}
unsigned char bl_c64_remaining(long room){return room<20?m[0x2a + room]:0;}
void bl_c64_debug_complete_before(long room){
    unsigned char i;unsigned short p;
    if(room<0 || room>=20)return;
    /* Cheat only. $335F-$3365 clears a lamp's first record byte and its
     * room counter; $336E restores replacement glyphs on the next load.
     * Complete the skipped records without invoking $2F2D score/audio. */
    for(i=0;i<room;i++){
        p=W((unsigned short)(0x4ce2 + 2*i));
        /* R14/R20 have a live-looking placeholder at(0,0), but count0.
         * Preserve it: only consume records while real lamps remain. */
        while(m[0x2a + i] && !(m[p]&128)){
            if(m[p]){m[p]=0;--m[0x2a + i];}
            p+=4;
        }
    }
}
SOURCE_INLINE unsigned short source_collected_mask(long room){
    unsigned short table=(unsigned short)(0x4ce2 + room*2),p,bits=0,mask=1;
    /* Presentation query only: same live records, terminator and13-bit cap.
     * Read the little-endian pointer inline; advance a one-bit mask rather
     * than repeating a variable68000 shift for each collected record. */
    p=(unsigned short)(m[table]|((unsigned short)m[(unsigned short)(table+1)]<<8));
    while(!(m[p]&128) && mask<8192){if(!m[p])bits|=mask;mask=(unsigned short)(mask<<1);p+=4;}
    return bits;
}
/* One read-only projection call replaces20 cross-module calls. Records
 * remain live, in room order; no progress cache or competing game state. */
unsigned short bl_c64_collected(long room){
    unsigned short p,bits=0;unsigned char bit=0;
    p=W((unsigned short)(0x4ce2 + room*2));
    while(!(m[p]&128) && bit<13){if(!m[p])bits|=(unsigned short)(1u<<bit);++bit;p+=4;}
    return bits;
}
void bl_c64_collected_all(unsigned short *out){
    unsigned short room;for(room=0;room<20;room++)out[room]=source_collected_mask(room);
}
static unsigned char object_base_pose(const BlGame *g){
    /* $2780 consumes the actor state BEFORE the next object pass ($1C0D/10).
     * These states have no animation-counter ambiguity. Do not derive source
     * walk/jump/climb masks from the unrelated AI-art animation frame. */
    if(g->wall.state==24)return g->wall.pose;
    if(g->attack==BL_SAI)
        return (unsigned char)(g->facing?(g->attack_phase>=11?52:54):(g->attack_phase>=11?48:50));
    if(g->state==BL_CLIMB && !g->attack && !g->prone)return g->wall.pose;
    if(g->attack==BL_FLYING_KICK){
        /* $288B-$28B2: counter12..10 versus9..0, not the AI art frame. */
        return (unsigned char)(g->facing?(g->attack_phase<=2?26:28):(g->attack_phase<=2?22:24));
    }
    if(g->attack==BL_PUNCH)return (unsigned char)(g->facing?6:4);
    if(g->prone)return (unsigned char)(g->facing?0x42:0x40);
    if(g->state==BL_AIR){
        unsigned char counter=(unsigned char)(g->jump_phase<16?16-g->jump_phase:0);
        if(g->jump_phase==255)return (unsigned char)((g->wall.contact&8)?8:68);
        if(!g->jump_direction)return (unsigned char)(counter>=15?8:counter>=12?30:counter>=2?32:counter==1?30:8);
        if(g->jump_direction<0)return (unsigned char)(counter>=12||counter<3?34:36);
        return (unsigned char)(counter>=12||counter<3?38:40);
    }
    if(g->state==BL_GROUND && !g->walk_steps &&
       !(bl_c64_contact((long)(g->x/16),(long)(g->y/16),2+g->source_actor*70,0)&4))
        return (unsigned char)(g->facing?2:0); /* $2974: net-idle is phase-dependent. */
    if(g->state==BL_GROUND && g->walk_steps && g->wall.pose>=14 && g->wall.pose<=20)
        return g->wall.pose;
    return 2; /* Existing provisional adapter for unported source actor phases. */
}
unsigned char bl_c64_object_pose(const BlGame *g){
    if(g->source_canonical)return g->source_mask;
    /* $29AB-$29BA: $95 flags -> $59A5={0,140,70}; component/mask index
     * differs from the base animation pose $4F48. */
    return (unsigned char)(object_base_pose(g)+g->source_actor*70);
}
unsigned char bl_c64_recovery_pose(long pose){
    /* $27C1-$27D7, $2719-$274C records these two source width flags. */
    return (unsigned char)(pose%70==68 || m[0x5cbf + pose] || m[0x5cc0 + pose]?pose/70*70+8:pose);
}
long bl_c64_collect(long col,long row){
    unsigned short p=W((unsigned short)(0x4ce2 + 2*loaded)),screen;
    while(!(m[p]&128)){
        if(m[p] && m[p+2]==col && m[p+3]==row){
            m[p]=0;--m[0x2a + loaded];screen=(unsigned short)(0x8c00 + (row*2-1)*40+col);
            m[screen]=m[p+1]&127;m[screen+40]=m[p+1]|128;
            source_written(screen);source_written((unsigned short)(screen+40));++revision;
            bl_c64_audio_request(0x8e); /* $2F34-$2F36, only on successful pickup. */
            return 1;
        }p+=4;
    }return 0;
}
long bl_c64_door(long tile,long px,long py,long falling){
    unsigned char slot=(unsigned char)(tile==2?0:tile==3?1:tile==4?2:3);
    /* $30D4-$310B: carry set rejects contact; no invented DOWN trigger.
     * Edge movement latches $4F57/5D/60 are bridged from current position. */
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;m[0xbf]=(unsigned char)(falling?14:0);
    execute(0x30d4);if(c)return 0;
    source_transition(m[0x4bfe + slot*40+loaded],m[0x4c12 + slot*40+loaded],m[0x4b5e + slot*20+loaded]);
    return 1;
}
void bl_c64_motion(const BlGame *g){
    int dx=g->x-g->previous_x,dy=g->y-g->previous_y;
    /* $1DF2/$1E39/$1E86/$1EC4 record the four movement directions.
     * Bridge the old actor motor's most recent displacement for door gates. */
    if(g->wall.tracked){
        m[0x4f57]=g->wall.moves[0][0];m[0x4f5a]=g->wall.moves[0][1];
        m[0x4f5d]=g->wall.moves[0][2];m[0x4f60]=g->wall.moves[0][3];
    }else{
        m[0x4f57]=(unsigned char)(dy<0);m[0x4f5a]=(unsigned char)(dy>0);
        m[0x4f5d]=(unsigned char)(dx<0);m[0x4f60]=(unsigned char)(dx>0);
    }
}
void bl_c64_reenter(void){
    source_transition(m[0x4bae + loaded],m[0x4bc2 + loaded],loaded);
}
long bl_c64_transition(long *px,long *py,unsigned char *room){
    if(!transition_pending)return 0;
    if(target_room>=20){source_fault=0xfffe;transition_pending=0;return 0;}
    *px=(long)target_x*2-24;*py=target_y;*room=target_room;transition_pending=0;return 1;
}
void bl_c64_object(long tile,long col,long row){
    unsigned short address;
    if((tile==0x2d||tile==0x2e) && loaded==16){execute(0x2fd6);return;}
    if(tile==0x60){
        address=(unsigned short)(0xd800 + (row*2-1)*40+col);
        if((m[address]&7)!=5){unsigned char i;
            for(i=0;i<3;i++)if(!m[0x4fde + i]){
                m[0x4fde + i]=1;m[0x4fe1 + i]=(unsigned char)(col-1);m[0x4fe4 + i]=(unsigned char)(row-1);
                m[address]=0xfd;++revision;break;
            }
        }
    }
}
unsigned char bl_c64_dead(void){return m[0xbf]==0x19;}
void bl_c64_enemy_entry(long actor,long *px,long *py,long *health){
    if(actor<1 || actor>2)return;
    m[0xd1 + actor]=(unsigned char)*health;
    a=c=z=n=v=d=0;x=m[0x51]=(unsigned char)actor;y=m[0x52]=(unsigned char)(3-actor);
    sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    /* $0B8E has already selected $52=2(Yamo)/1(Kage) before $0BFA.
     * Execute the real selection, saved-entry clear and VIC shadow writes. */
    room_code(0x0bfa);
    *px=(long)m[0x9e + actor]*2-24;*py=m[0xa1 + actor];*health=m[0xd1 + actor];
}
unsigned char bl_c64_spawn_cold_counter(long actor){
    return (unsigned char)(actor==1?BL_C64_COLD_YAMO:BL_C64_COLD_KAGE);
}
unsigned char bl_c64_spawn_counter(long actor){return m[actor==1?0x5e:0x5d];}
void bl_c64_set_opponent_mode(long human_yamo){m[0x42ca]=(unsigned char)(human_yamo!=0);}
void bl_c64_spawn_sync(long actor,long active,long px,long py,long health,long counter){
    if(actor<1 || actor>2)return;
    m[0x95 + actor]=(unsigned char)((m[0x95 + actor]&254)|(active?1:0));
    m[0x9e + actor]=(unsigned char)((px+24)/2);m[0xa1 + actor]=(unsigned char)py;
    m[0xd1 + actor]=(unsigned char)health;m[actor==1?0x5e:0x5d]=(unsigned char)counter;
}
void bl_c64_spawn_services(long px,long py){
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;
    a=m[0x7a];NZ(a);if(a)return;
    /* $1BF5-$1BFB: decrement BOTH counters, Yamo, then Kage. Includes
     * $0DB1's conditional16-step postponement and actual $1159 reads. */
    m[0x100 + sp--]=0x1b;m[0x100 + sp--]=0xf7;room_code(0x0da4);
    m[0x100 + sp--]=0x1b;m[0x100 + sp--]=0xfa;room_code(0x0d0f);
    m[0x100 + sp--]=0x1b;m[0x100 + sp--]=0xfd;room_code(0x0db1);
}
void bl_c64_spawn_result(long actor,BlC64Spawn *r){
    r->active=m[0x95 + actor]&1;r->x=m[0x9e + actor];r->y=m[0xa1 + actor];r->facing=m[0xa4 + actor];
    r->state=m[0xbf + actor];r->counter=m[0xce + actor];r->pose=m[0x4f48 + actor];
    r->mask=m[0x4f4e + actor];r->health=m[0xd1 + actor];r->wait=m[0x106 + actor];
}
long bl_c64_enemy_remove(long actor){
    if(actor<1 || actor>2)return 0;
    x=m[0x51]=(unsigned char)actor;a=y=c=z=n=v=d=0;
    sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;room_code(0x3001);
    return bl_c64_spawn_counter(actor);
}
long bl_c64_enemy_door(long actor,long px,long py,long falling,long up,long down,long left,long right){
    unsigned char state;
    if(actor<1 || actor>2)return 0;
    m[0x9e + actor]=(unsigned char)((px+24)/2);m[0xa1 + actor]=(unsigned char)py;
    state=m[0xbf + actor];m[0xbf + actor]=(unsigned char)(falling?14:0);
    m[0x4f57 + actor]=(unsigned char)up;m[0x4f5a + actor]=(unsigned char)down;
    m[0x4f5d + actor]=(unsigned char)left;m[0x4f60 + actor]=(unsigned char)right;
    a=y=c=z=n=v=d=0;x=(unsigned char)actor;sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    room_code(0x30d4);m[0xbf + actor]=state;return !c;
}
void bl_c64_enemy_follow(long actor,long active,long px,long py,long health){
    if(actor<1 || actor>2)return;
    m[0x8a + actor]=(unsigned char)(active?(px+24)/2:0);
    m[0x8c + actor]=(unsigned char)(active?py:0);
    if(active)m[0x8e + actor]=(unsigned char)health;
}
void bl_c64_enemy_entries_clear(void){m[0x8b]=m[0x8c]=0;}
long bl_c64_enemy_hazard(long actor){
    if(actor<1 || actor>2)return 0;
    m[0x51]=x=(unsigned char)actor;m[0x95 + actor]=(unsigned char)(actor==1?0x81:0x41);
    a=y=c=z=n=v=d=0;sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    room_code(0x304b);
    return m[actor==1?0x5e:0x5d];
}
void bl_c64_clear_death(void){m[0xbf]=m[0xce]=0;}
void bl_c64_set_lives(long lives){m[0x28]=(unsigned char)lives;}
void bl_c64_save_progress(unsigned char *state){
    unsigned char i;for(i=0;i<28;i++)state[i]=m[0x28 + i];
}
void bl_c64_restore_progress(const unsigned char *state,const unsigned short *collected){
    unsigned char i,bit;unsigned short p;
    /* $1856-$186E swaps $28..$43. $1870->$0FED reconstructs lantern
     * records for the selected player. Native masks retain their identity
     * even after the source record's original tile byte has been cleared. */
    bl_c64_reset();
    for(i=0;i<28;i++)m[0x28 + i]=state[i];
    for(i=0;i<20;i++){
        p=W((unsigned short)(0x4ce2 + i*2));bit=0;
        while(!(m[p]&128) && bit<13){if(collected[i]&(1u<<bit))m[p]=0;++bit;p+=4;}
    }
}
void bl_c64_projectile(long index,BlC64Projectile *sprite){
    unsigned char i,bit=(unsigned char)(0x40<<index);
    sprite->active=(unsigned char)(loaded==18 && (m[0xd015]&bit)!=0);
    if(!sprite->active)return;
    sprite->x=(signed short)((m[0xd00c + index*2]|((m[0xd010]&bit)?256:0))-24);
    sprite->y=(signed short)((int)m[0xd00d + index*2]-51);
    sprite->width=(unsigned char)((m[0xd01d]&bit)?2:1);sprite->color=m[0xd02d + index]&15;
    for(i=0;i<63;i++)sprite->bits[i]=m[0x8340 + index*64+i];
}
void bl_c64_player_sprite_contact(long px,long py,long pose){
    unsigned char i,row,col,pair;unsigned short mask;
    m[0xd01e]=0;if(loaded!=18)return;
    pose&=254;mask=(unsigned short)(m[0x1167 + pose]|((unsigned short)m[0x1239 + pose]<<8));
    for(i=0;i<2;i++){
        BlC64Projectile sprite;bl_c64_projectile(i,&sprite);if(!sprite.active)continue;
        if(px+24<=sprite.x||px>=sprite.x+24*sprite.width||py<=sprite.y||py-21>=sprite.y+21)continue;
        for(row=0;row<21;row++)for(col=0;col<3;col++){
            unsigned char bits=m[mask+col*32+row];if(!bits)continue;
            for(pair=0;pair<4;pair++)if((bits>>(6-pair*2))&3){
                int dx,sy=py-21+row-sprite.y;
                if(sy<0||sy>=21)continue;
                for(dx=0;dx<2;dx++){
                    int sx=px+col*8+pair*2+dx-sprite.x;
                    if(sx<0||sx>=24*sprite.width)continue;
                    sx/=sprite.width;
                    if(sprite.bits[sy*3+sx/8]&(0x80>>(sx&7)))m[0xd01e]|=(unsigned char)(3|(0x40<<i));
                }
            }
        }
    }
}

unsigned long bl_d7_probe_abi(long p0,long p1,long p2,long p3,long p4,long p5,long p6,long p7){
    unsigned long value=(unsigned long)p0^((unsigned long)p1<<1)^((unsigned long)p2<<2)^((unsigned long)p3<<3)^((unsigned long)p4<<4)^((unsigned long)p5<<5)^((unsigned long)p6<<6)^((unsigned long)p7<<7);
    a=(unsigned char)(value>>7);return value;
}
