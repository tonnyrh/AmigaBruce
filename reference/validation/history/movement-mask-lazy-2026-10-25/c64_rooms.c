#include "c64_rooms.h"

/* Sparse source data + state in CPU RAM. No C64 instruction fetch/decode.
 * Original IRQs/SID/VIC registers have no access to Amiga hardware here. */
static unsigned char m[65536];
static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;
static unsigned char target_x,target_y,target_room;
static unsigned short revision,source_fault;
static unsigned short audio_requests_mask;
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
static void animation_cell_changed(unsigned short cell){
    unsigned short item;unsigned char mismatch;
    if(!animation_count)return;
    if((m[0x8c00+cell]&127)>=0x61 && (m[0x8c00+cell]&127)<=0x63)animation_fallback_dirty=1;
    if((item=animation_cell[cell])==65535)return;
    animation_fallback_dirty=1;
    mismatch=(unsigned char)(m[0x8c00+cell]!=animation_code[cell] || (m[0xd800+cell]&7)!=animation_color[cell]);
    if(mismatch!=animation_mismatch[cell]){
        if(mismatch)++animation_differences[item];else --animation_differences[item];
        animation_mismatch[cell]=mismatch;
    }
}
static void rebuild_animation_fallback(void){
    unsigned short cell;animation_fallback_count=0;animation_fallback_dirty=0;
    if(!animation_count)return;
    for(cell=120;cell<1000;cell++){
        unsigned char code=m[0x8c00+cell]&127;unsigned short item=animation_cell[cell];
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
static unsigned long planar_lut[4][9][256];
static unsigned char line_band[200],line_colors[200][3];
static void prepare_palette(void);
static unsigned char contact_bitmap[8000],contact_cells[1000];
static unsigned long contact_coverage[8000],coverage_table[2][256],spread_masks[256];
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
#include "c64_room_data.h"
#if defined(__GNUC__)
#define SOURCE_INLINE static inline __attribute__((always_inline))
#else
#define SOURCE_INLINE static __forceinline
#endif
/* Native decoding of $17E2-$1817 and its $1A67 helper. Preserve source RAM,
 * source stack bytes, registers and terminating CMP flags, without paying a
 * generic native subroutine dispatch for every character in a room string. */
SOURCE_INLINE void source_string(void){
    PROFILE_START(string_start);
    unsigned char original=a,yy=y;unsigned short pointer,address,upper,lower;
    m[0x100+sp--]=a;m[0x100+sp--]=0x17;m[0x100+sp--]=0xe5;
    m[4]=m[0x4338+x];m[5]=m[0x434c+x];m[8]=m[0x4360+x];m[9]=m[0x4374+x];
    if(m[0x100]){m[8]=0;m[9]=0xce;}
    sp+=2;a=m[0x100+(unsigned char)++sp];
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
                x=y&15;a=m[0x2572+x];NZ(a);
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
    m[queue]=y;x=y&15;a=m[0x2572+x];m[priority]=a;NZ(a);sp+=2;PROFILE_END(sound_start,10);
}
#include "c64_sfx.h"
/* Decoded $104B-$10B4 + $404E-$407C. Original moving-cell positions,
 * wrapping tests, string IDs, call-return bytes and final flags are retained. */
static void source_movers(void){
    PROFILE_START(movers_start);
    unsigned char reverse,special;unsigned short ret;
    x=8;
    do{
        a=m[0x10f+x];NZ(a);
        if(a){
            reverse=a&128;
            m[0x100+sp--]=x;
            m[0x12d+x]=m[0x70]=m[0x119+x];m[0x6f]=m[0x123+x];
            if(reverse){
                a=++m[0x119+x];c=a>=m[0x141+x];
                if(c)a=m[0x119+x]=m[0x137+x];
            }else{
                a=--m[0x119+x];c=a>=m[0x137+x];
                if(!c)a=m[0x119+x]=m[0x141+x];
            }
            m[0x6e]=a;special=(unsigned char)(m[0x6f]==5 || m[0x6f]==10);
            ret=special?0x108b:reverse?0x10ae:0x1085;
            m[0x100+sp--]=(unsigned char)(ret>>8);m[0x100+sp--]=(unsigned char)ret;
            ret=special?0x4065:0x4050;
            m[0x100+sp--]=(unsigned char)(ret>>8);m[0x100+sp--]=(unsigned char)ret;
            y=0x89;source_sound();
            a=special?0x55:0x1c;x=m[0x6f];y=m[0x70];ret=special?0x406e:0x4059;
            m[0x100+sp--]=(unsigned char)(ret>>8);m[0x100+sp--]=(unsigned char)ret;
            source_string();
            a=special?0x54:0x1b;x=m[0x6f];y=m[0x6e];source_string();
            a=m[0x100+(unsigned char)++sp];x=a;
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
        code=(unsigned char)(0x61+column%3+(column>=3?128:0));changed=0;
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
    m[0x100+sp]=0x2d;m[0x100+(unsigned char)(sp-1)]=0x40;sp+=2;
    a=m[(unsigned short)(table+((m[0x64]+7)&7))];x=255;y=8;c=1;z=0;n=1;
    v=(unsigned char)((~(high^4)&(high^(unsigned char)(high+4))&128)!=0);
}
#include "c64_room_programs.h"
static void execute(unsigned short entry){
    a=x=y=c=z=n=v=d=0;sp=253;m[0x1fe]=0xfe;m[0x1ff]=0xff;
    room_code(entry);
}
void bl_c64_test_execute(long entry){execute((unsigned short)entry);flush_glyph_changes();++revision;}

static unsigned short charset(void){
    return m[0xf2]==0x38?0xa000:m[0xf2]==0x3a?0xa800:m[0xf2]==0x3c?0xb000:0xb800;
}
void bl_c64_reset(void){
    audio_requests_mask=0;audio_faults=0;audio_gates=0;
    unsigned long i;for(i=0;i<65536;i++)m[i]=0;
    seed_memory();a=x=y=c=z=n=v=d=sp=0;loaded=255;++revision;source_fault=0;
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
    bl_c64_audio_reset();
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;m[0xb6]=1;m[0xce]=4;
    loaded=m[0x29]=room;transition_pending=0;sp=0;d=0;++contact_generation;index_ready=0;paint_count=paint_cursor=0;animation_pending=0;animation_fallback_count=0;animation_fallback_dirty=0;
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
    unsigned short i;invalidate_contacts();
    for(i=0;i<paint_count;i++){dirty_cells[paint_list[i]]=paint_queued[paint_list[i]]=0;paint_rows[paint_list[i]]=0;}
    paint_count=paint_cursor=0;animation_pending=0;animation_started=0;old_bank=m[0xf2];display_dirty=0;flash_changed=0;
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
    const unsigned long *lookup=coverage_table[(m[0xd800 + cell]&7)!=0];
    unsigned long *coverage=contact_coverage+base;
#define CONTACT_ROW(r) do{unsigned char bits=src[r];bitmap[(r)*40]=bits;coverage[(r)*40]=lookup[bits];}while(0)
    CONTACT_ROW(0);CONTACT_ROW(1);CONTACT_ROW(2);CONTACT_ROW(3);
    CONTACT_ROW(4);CONTACT_ROW(5);CONTACT_ROW(6);CONTACT_ROW(7);
#undef CONTACT_ROW
    contact_cells[cell]=0;contact_epoch[cell]=glyph_epoch[m[0x8c00+cell]];
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
        unsigned long all_hit=0,body_hit=0,hit;
        const unsigned char *masks;
        const unsigned long *background;
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
        if(all_hit&0xff000000UL)all|=1;
        if(all_hit&0x00ff0000UL)all|=2;
        if(all_hit&0x0000ff00UL)all|=4;
        if(all_hit&0x000000ffUL)all|=8;
        if(body_hit&0xff000000UL)body|=1;
        if(body_hit&0x00ff0000UL)body|=2;
        if(body_hit&0x0000ff00UL)body|=4;
        if(body_hit&0x000000ffUL)body|=8;
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
    for(bits=0;bits<256;bits++){
        unsigned char low=bits&0x55,high=(bits>>1)&0x55,flag=0;
        unsigned char one=(unsigned char)(low&~high),two=(unsigned char)(high&~low),three=(unsigned char)(low&high);
        unsigned long base;
        one|=(unsigned char)(one<<1);two|=(unsigned char)(two<<1);three|=(unsigned char)(three<<1);
        base=((unsigned long)one<<24)|((unsigned long)two<<16);
        coverage_table[0][bits]=base|three;coverage_table[1][bits]=base|((unsigned long)three<<8);
        spread_masks[bits]=((unsigned long)bits<<24)|((unsigned long)bits<<16)|((unsigned long)bits<<8)|bits;
        if(low&(unsigned char)~high)flag|=1;
        if(high&(unsigned char)~low)flag|=2;
        contact_classes[0][bits]=(unsigned char)(flag|((low&high)?8:0));
        contact_classes[1][bits]=(unsigned char)(flag|((low&high)?4:0));
    }
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
    {unsigned long color_planes[16];
    for(color=0;color<16;color++){
        unsigned long packed=0;unsigned char plane;
        for(plane=0;plane<4;plane++)packed=(packed<<8)|((color&(1<<plane))?255:0);
        color_planes[color]=packed;
    }
    for(band=0;band<4;band++)for(bits=0;bits<256;bits++){
        unsigned char low=bits&0x55,high=(bits>>1)&0x55,j;
        unsigned char masks[4];unsigned long spread[4],base;
        masks[0]=(unsigned char)(~low&~high&0x55);masks[1]=(unsigned char)(low&~high);
        masks[2]=(unsigned char)(high&~low);masks[3]=(unsigned char)(low&high);
        for(j=0;j<4;j++){
            unsigned long value=(unsigned char)(masks[j]|(masks[j]<<1));
            spread[j]=(value<<24)|(value<<16)|(value<<8)|value;
        }
        base=(spread[0]&color_planes[m[palette+band*3]&15])|
             (spread[1]&color_planes[m[palette+band*3+1]&15])|
             (spread[2]&color_planes[m[palette+band*3+2]&15]);
        for(color=0;color<9;color++)planar_lut[band][color][bits]=base|(spread[3]&color_planes[color==8?15:color]);
    }}
}
void bl_c64_colors(long py,unsigned char *out){unsigned char i;for(i=0;i<3;i++)out[i]=line_colors[py][i];}
unsigned long bl_c64_planar(long bits,long color,long py){return planar_lut[line_band[py]][color&7][bits];}

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
            unsigned char bits=m[glyph+row];unsigned long packed=planar_lut[line_band[cy+row]][color][bits];
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
    for(item=0;item<paint_count;item++)paint_cell(planes,paint_list[item],(unsigned short)scene_top,paint_rows[paint_list[item]]);
    return paint_list;
}
/* Source $2CF1-$2D54: three8x16 glyphs, each source row duplicated.
 * Cache only that exact eight-phase byte sequence. A runtime byte comparison
 * and per-rectangle screen/attribute checks guard every accelerated draw. */
static unsigned char animation_bits(unsigned char code,unsigned char row,unsigned char phase){
    return animation_pattern[((code&127)-0x61)*8+((phase+(row>>1)+(code&128?4:0))&7)];
}
static unsigned char animated_code(unsigned char code){return (code&127)>=0x61 && (code&127)<=0x63;}
long bl_c64_build_animation_cache(unsigned char *cache,long capacity){
    unsigned short row,col,item,cell;unsigned long used=0,total=0,groups[2]={0,0};
    animation_count=0;animation_cache=cache;animation_fallback_count=0;animation_fallback_dirty=0;
    animation_checked_revision=(unsigned short)(revision-1);animation_phase_valid=0;
    for(item=0;item<24;item++)animation_pattern[item]=m[(loaded<10?0x42f1:0x4309)+item];
    {unsigned short phase,code,dy;for(phase=0;phase<8;phase++)for(code=0;code<6;code++)for(dy=0;dy<8;dy++)
        animation_variants[phase][code*8+dy]=animation_bits((unsigned char)(0x61+code%3+(code>=3?128:0)),(unsigned char)dy,(unsigned char)phase);}
    for(cell=0;cell<1000;cell++){animation_cell[cell]=65535;animation_mismatch[cell]=0;}
    for(item=0;item<128;item++)animation_differences[item]=0;
    if(!cache || (charset()!=0xa000 && charset()!=0xa800))return 0;
    for(row=3;row<25;row++)for(col=0;col<40;){
        unsigned short left=col,right,found=65535;
        if(!animated_code(m[0x8c00+row*40+col])){++col;continue;}
        do{++col;}while(col<40 && animated_code(m[0x8c00+row*40+col]));right=col;
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
            cell=row*40+col;animation_cell[cell]=item;animation_code[cell]=m[0x8c00+cell];animation_color[cell]=m[0xd800+cell]&7;
        }
        for(phase=0;phase<8;phase++)for(row=rect->top;row<rect->bottom;row++)for(dy=0;dy<8;dy++)for(col=left;col<right;col++){
            unsigned long packed=0,at;cell=row*40+col;
            if(col>=rect->left && col<rect->right)packed=planar_lut[line_band[row*8+dy]][animation_color[cell]][animation_bits(animation_code[cell],dy,phase)];
            at=rect->offset+(unsigned long)phase*rect->size+((row-rect->top)*8+dy)*4*width+col-left;
            for(plane=0;plane<4;plane++){animation_cache[at+plane*width]=(unsigned char)(packed>>24);packed<<=8;}
        }
    }
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
static void paint_animation_blocks(unsigned char *planes,unsigned short scene_top){
    PROFILE_START(bulk_start);
    unsigned short item,row;unsigned char phase=m[0x64]&7,needed=0;BlC64Block request;
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
    request.bitmap=planes;
    for(item=0;item<animation_count;item++){
        AnimationRect *rect=&animation_rects[item];
        if(animation_done[item] || animation_differences[item] || rect->group!=animation_part)continue;
        animation_done[item]=1;
        request.pixels=animation_cache+rect->offset+(unsigned long)phase*rect->size;
        request.left=rect->left&~1;request.top=scene_top+rect->top*8;
        request.width=((rect->right+1)&~1)-request.left;request.height=(rect->bottom-rect->top)*8;
        request.first_mask=(rect->left&1)?0x00ff:0xffff;request.last_mask=(rect->right&1)?0xff00:0xffff;
        {PROFILE_START(t);block_painter(&request);PROFILE_END(t,0);}
        for(row=rect->top;row<rect->bottom;row++){part_words[row]|=rect->words;part_rows[row]=255;}
    }
    ++animation_part;
    PROFILE_END(bulk_start,7);
}
const unsigned short *bl_c64_paint_part(unsigned char *planes,long scene_top,long limit,unsigned short *count){
    unsigned short start=paint_cursor,cell,row,work=0;
    unsigned char *field=planes+scene_top*40;
    for(row=0;row<25;row++){part_words[row]=0;part_rows[row]=0;}
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
            ++paint_cursor;continue;
        }
        if(work++>=limit)break;
        ++paint_cursor;rows=paint_rows[cell];stamp=cell_stamp[cell];
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
    }
    *count=(unsigned short)(paint_cursor-start);return paint_list+start;
}
unsigned char bl_c64_paint_done(void){return paint_cursor==paint_count && (!animation_pending || !animation_phase_valid || animation_part>=2);}
const unsigned long *bl_c64_part_words(void){return part_words;}
const unsigned char *bl_c64_part_rows(void){return part_rows;}
long bl_c64_check_interleaved(const unsigned char *bitmap,long scene_top){
    unsigned short cell,row,plane,bank=charset();long mismatches=0;
    for(cell=120;cell<1000;cell++){
        unsigned char code=m[0x8c00+cell],color=(unsigned char)(loaded==19&&flash_cells[cell]?8:m[0xd800+cell]&7);
        unsigned short at=(unsigned short)((scene_top+cell_y[cell])*160+cell-(cell_y[cell]>>3)*40);
        for(row=0;row<8;row++){
            unsigned long packed=planar_lut[line_band[cell_y[cell]+row]][color][m[bank+((unsigned short)code<<3)+row]];
            for(plane=0;plane<4;plane++){if(bitmap[at+row*160+plane*40]!=(unsigned char)(packed>>24))++mismatches;packed<<=8;}
        }
    }
    return mismatches;
}

void bl_c64_field(void){
    /* $15A8/$1678: PAL field counters used by final-room wait. */
    ++m[0x16];
    if(m[0x49])--m[0x49];else if(m[0x4a]){--m[0x4a];--m[0x49];}
}
void bl_c64_tick(long px,long py){
    m[0x9e]=(unsigned char)((px+24)/2);m[0xa1]=(unsigned char)py;
    m[0x7c]=(unsigned char)(charset()>>8);m[2]=50;m[0x100]=0;
    /* Original main-loop $1BEE and $1BFE-$1C0A precede the room loop. */
    {PROFILE_START(t);execute(0x40bc);PROFILE_END(t,1);}
    m[0x7b]=m[0x7b]?(unsigned char)(m[0x7b]-1):1;
    {PROFILE_START(t);execute(W((unsigned short)(0x4ec4 + 2*loaded))+1);PROFILE_END(t,2);}
    flush_glyph_changes();
    if(display_dirty || old_bank!=m[0xf2])++revision;
}
unsigned char bl_c64_changed_rows(long cell){return paint_rows[cell];}
unsigned char bl_c64_flash_color(void){return loaded==19?(m[0xdaac]&7):15;}
const unsigned short *bl_c64_offsets(void){return cell_offsets;}
const unsigned char *bl_c64_cell_y(void){return cell_y;}
unsigned char bl_c64_remaining(long room){return room<20?m[0x2a + room]:0;}
unsigned short bl_c64_collected(long room){
    unsigned short p,bits=0;unsigned char bit=0;
    p=W((unsigned short)(0x4ce2 + room*2));
    while(!(m[p]&128) && bit<13){if(!m[p])bits|=(unsigned short)(1u<<bit);++bit;p+=4;}
    return bits;
}
unsigned char bl_c64_object_pose(const BlGame *g){
    /* $2780 consumes the actor state BEFORE the next object pass ($1C0D/10).
     * These states have no animation-counter ambiguity. Do not derive source
     * walk/jump/climb masks from the unrelated AI-art animation frame. */
    if(g->wall.state==24)return g->wall.pose;
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
       !(bl_c64_contact((long)(g->x/16),(long)(g->y/16),2,0)&4))
        return (unsigned char)(g->facing?2:0); /* $2974: net-idle is phase-dependent. */
    return 2; /* Existing provisional adapter for unported source actor phases. */
}
unsigned char bl_c64_recovery_pose(long pose){
    /* $27C1-$27D7, $2719-$274C records these two source width flags. */
    return (unsigned char)(pose==68 || m[0x5cbf+pose] || m[0x5cc0+pose]?8:pose);
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
void bl_c64_projectile(long index,BlC64Projectile *sprite){
    unsigned char i,bit=(unsigned char)(0x40<<index);
    sprite->active=(unsigned char)(loaded==18 && (m[0xd015]&bit)!=0);
    if(!sprite->active)return;
    sprite->x=(signed short)((m[0xd00c+index*2]|((m[0xd010]&bit)?256:0))-24);
    sprite->y=(signed short)((int)m[0xd00d+index*2]-51);
    sprite->width=(unsigned char)((m[0xd01d]&bit)?2:1);sprite->color=m[0xd02d+index]&15;
    for(i=0;i<63;i++)sprite->bits[i]=m[0x8340+index*64+i];
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
