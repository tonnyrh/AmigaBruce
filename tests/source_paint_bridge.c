/* Host-only painter regression; all data are from the source room engine. */
#include "../core/c64_rooms.c"
static unsigned char bitmap[40960];
static void interleaved_tile(const BlC64Paint *q){
 unsigned short r,p,cy=cell_y[q->cell],column=(unsigned short)(q->cell%40);
 for(r=0;r<8;r++)if(q->rows&(1u<<r))for(p=0;p<4;p++)q->bitmap[(q->scene_top+cy+r)*160+p*40+column]=q->planes[p*8+r];
}
#define CHECK(q) do{if(!(q))return __LINE__;}while(0)
long bl_paint_requeue_contract(void){
 unsigned short cell=403,other=600,count,i,loops;unsigned char original;
 bl_c64_reset();bl_c64_load(5);bl_c64_set_painter(interleaved_tile);
 for(i=0;i<40960;i++)bitmap[i]=0;
 bl_c64_paint_room(bitmap,0);bl_c64_clear_dirty();
 CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 original=m[0x8c00+cell];m[0x8c00+cell]^=1;source_written((unsigned short)(0x8c00+cell));
 m[0x8c00+other]^=1;source_written((unsigned short)(0x8c00+other));
 (void)bl_c64_paint_part(bitmap,0,1,&count);CHECK(count==1 && !bl_c64_paint_done());
 m[0x8c00+cell]=original;source_written((unsigned short)(0x8c00+cell));
 (void)bl_c64_paint_part(bitmap,0,160,&count);CHECK(bl_c64_paint_done());
 bl_c64_clear_dirty();
 CHECK(bl_c64_has_dirty() && !bl_c64_paint_done());
 for(loops=0;loops<8 && bl_c64_has_dirty();loops++){
  (void)bl_c64_paint_part(bitmap,0,160,&count);
  if(bl_c64_paint_done())bl_c64_clear_dirty();
 }
 CHECK(!bl_c64_has_dirty() && bl_c64_paint_done());
 CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 /* A full880-cell queue must coalesce repeated mutations and retain all
  * already consumed cells without appending duplicates or overflowing. */
 for(i=120;i<1000;i++){m[0x8c00+i]^=1;source_written((unsigned short)(0x8c00+i));}
 (void)bl_c64_paint_part(bitmap,0,160,&count);CHECK(paint_count==880);
 for(i=120;i<280;i++){m[0x8c00+i]^=1;source_written((unsigned short)(0x8c00+i));mark_cell(i,1,255);}
 CHECK(paint_count<=880);
 for(loops=0;loops<32 && bl_c64_has_dirty();loops++){
  (void)bl_c64_paint_part(bitmap,0,160,&count);
  if(bl_c64_paint_done())bl_c64_clear_dirty();
 }
 CHECK(loops<32 && !bl_c64_has_dirty());
 CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 return 0;
}

static void block_copy(const BlC64Block *q){
 unsigned long y,p,c,w=q->width;
 for(y=0;y<q->height;y++)for(p=0;p<4;p++)for(c=0;c<w;c++){
  unsigned char mask=255;unsigned long dst=(q->top+y)*160+p*40+q->left+c,src=(y*4+p)*w+c;
  if(c<2)mask&=(unsigned char)(q->first_mask>>(c?0:8));
  if(c>=w-2)mask&=(unsigned char)(q->last_mask>>((c==w-2)?8:0));
  q->bitmap[dst]=(q->bitmap[dst]&~mask)|(q->pixels[src]&mask);
 }
}

static unsigned char animation_test_cache[106496];
static long room14_trap_contract(void){
 unsigned short step,i,count,cell;
 unsigned char saw_top=0,saw_bottom=0,saw_identical=0;
 bl_c64_reset();bl_c64_load(13);bl_c64_set_trap_row_reuse(1);
 bl_c64_paint_room(bitmap,0);bl_c64_clear_dirty();
 for(step=0;step<96;step++){
  for(i=120;i<1000;i++)contact_cells[i]=0;
  execute(0x104b);
  for(i=0;i<paint_count;i++){
   cell=paint_list[i];
   CHECK(contact_cells[cell]);
   switch(paint_rows[cell]){
    case 3:saw_top=1;break;
    case 192:saw_bottom=1;break;
    case 0:saw_identical=1;break;
    default:CHECK(0);
   }
  }
  do{(void)bl_c64_paint_part(bitmap,0,5,&count);}while(!bl_c64_paint_done());
  CHECK(bl_c64_check_interleaved(bitmap,0)==0);
  bl_c64_clear_dirty();
 }
 bl_c64_set_trap_row_reuse(0);
 CHECK(saw_top && saw_bottom && saw_identical);
 return 0;
}

long bl_paint_frame_contract(void){
 unsigned short room,step,i,count,loops;unsigned long before;unsigned char saw_split=0;
 bl_c64_set_block_painter(block_copy);bl_c64_set_painter(interleaved_tile);
 /* Full loads and same-room reloads must produce exact source pixels. */
 bl_c64_reset();
 for(room=0;room<20;room++)for(step=0;step<3;step++){
  bl_c64_load(room);
  for(i=0;i<40960;i++)bitmap[i]=0xa5;
  bl_c64_paint_room(bitmap,0);CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 }
 bl_c64_world_start(1,0);bl_c64_world_jump(11);
 for(i=0;i<40960;i++)bitmap[i]=0;
 bl_c64_paint_room(bitmap,0);bl_c64_clear_dirty();
 CHECK(bl_c64_build_animation_cache(animation_test_cache,sizeof(animation_test_cache))==52224);
 for(step=0;step<96;step++){
  const unsigned long *coverage;
  bl_c64_field();bl_c64_field();bl_c64_field();bl_c64_world_step(1,1);bl_c64_prepare_paint();
  (void)bl_c64_paint_part(bitmap,0,160,&count);
  if(animation_part==1 && bl_c64_check_interleaved(bitmap,0))saw_split=1;
  before=bl_c64_actor_ram_hash();coverage=bl_c64_animation_coverage();
  for(i=0;i<25;i++)CHECK(!(coverage[i]&~0xfffffUL));
  bl_c64_paint_animation_frame(bitmap,0);
  CHECK(before==bl_c64_actor_ram_hash());
  CHECK(bl_c64_check_interleaved(bitmap,0)==0);
  if(bl_c64_paint_done())bl_c64_clear_dirty();
 }
 CHECK(saw_split);
 /* A changed cell invalidates its cache rectangle, including word coverage. */
 for(i=120;i<1000;i++)if(animation_cell[i]!=65535)break;
 CHECK(i<1000);m[0x8c00+i]=0;source_written(0x8c00+i);bl_c64_prepare_paint();
 {unsigned short item=animation_cell[i],word=(i%40)>>1;
  CHECK(animation_differences[item]);
  CHECK(!(bl_c64_animation_coverage()[i/40]&(1UL<<word)));
 }
 for(loops=0;loops<32 && bl_c64_has_dirty();loops++){
  (void)bl_c64_paint_part(bitmap,0,160,&count);bl_c64_paint_animation_frame(bitmap,0);
  if(bl_c64_paint_done())bl_c64_clear_dirty();
 }
 CHECK(!bl_c64_has_dirty());CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 return room14_trap_contract();
}
