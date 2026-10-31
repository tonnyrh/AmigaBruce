/* Host-only saturation/reference checks; synthetic graphics states are not gameplay rules. */
#include <string.h>
#include "source_paint_bridge.c"
static unsigned short capacity_metrics[20][3];
static unsigned char before_paint[65536];
static long references_valid(void){
 unsigned short cell,i,counts[BL_CHARACTER_CACHE_SLOTS];
 for(i=0;i<BL_CHARACTER_CACHE_SLOTS;i++)counts[i]=0;
 for(cell=120;cell<1000;cell++){
  i=cell_cache[cell];
  if(i==65535){CHECK(cell_stamp[cell]==0);continue;}
  CHECK(i<BL_CHARACTER_CACHE_SLOTS);CHECK(cell_stamp[cell]==character_cache[i].planes[0]);++counts[i];
 }
 for(i=0;i<BL_CHARACTER_CACHE_SLOTS;i++)CHECK(counts[i]==cache_references[i]);
 return 0;
}
static long exact_paint(void){
 long failure;memcpy(before_paint,m,65536);bl_c64_paint_room(bitmap,0);
 CHECK(!memcmp(before_paint,m,65536));CHECK(bl_c64_check_interleaved(bitmap,0)==0);
 failure=references_valid();if(failure)return failure;return 0;
}
long bl_cache_capacity_contract(void){
 unsigned short room,step,cell,i,slots,uncached,count,loops,code,glyph;long failure;
 failure=bl_paint_requeue_contract();if(failure)return 10000+failure;
 failure=bl_paint_frame_contract();if(failure)return 20000+failure;
 bl_c64_set_painter(interleaved_tile);bl_c64_set_block_painter(block_copy);bl_c64_reset();bl_c64_world_start(1,0);
 for(room=0;room<20;room++){
  bl_c64_world_jump(room);
  for(step=0;step<=120;step++){
   failure=exact_paint();if(failure)return 30000+failure;
   slots=uncached=0;
   for(i=0;i<BL_CHARACTER_CACHE_SLOTS;i++)if(cache_references[i])++slots;
   for(cell=120;cell<1000;cell++)if(cell_cache[cell]==65535)++uncached;
   if(slots>capacity_metrics[room][0])capacity_metrics[room][0]=slots;
   if(uncached>capacity_metrics[room][1])capacity_metrics[room][1]=uncached;
   capacity_metrics[room][2]=m[0x29]+1;
   if(step==120)break;
   bl_c64_field();bl_c64_field();bl_c64_field();bl_c64_world_step(1,1);bl_c64_prepare_paint();CHECK(!bl_c64_fault());
  }
 }
 /*880 distinct code/color keys force saturation even in512 slots. */
 bl_c64_world_jump(0);bl_c64_paint_room(bitmap,0);bl_c64_clear_dirty();
 for(cell=120;cell<1000;cell++){
  m[0x8c00+cell]=(unsigned char)(cell-120);source_written(0x8c00+cell);
  m[0xd800+cell]=(unsigned char)((cell-120)>>8);source_written(0xd800+cell);
 }
 bl_c64_prepare_paint();failure=exact_paint();if(failure)return 40000+failure;
 uncached=0;for(cell=120;cell<1000;cell++)if(cell_cache[cell]==65535)++uncached;
 CHECK(uncached>=880-BL_CHARACTER_CACHE_SLOTS);
 /*Glyph epoch wrap, one-cell budgets and cache invalidation with full tables. */
 for(i=0;i<16;i++){
  code=(unsigned short)(i*17);glyph=(unsigned short)(charset()+code*8);
  flush_glyph_changes();glyph_epoch[code]=65535;
  m[glyph]^=255;source_written(glyph);CHECK(glyph_epoch[code]==0);
  flush_glyph_changes();bl_c64_prepare_paint();memcpy(before_paint,m,65536);
  for(loops=0;loops<2000 && bl_c64_has_dirty();loops++){
   (void)bl_c64_paint_part(bitmap,0,(i&1)?1:160,&count);
   if(bl_c64_paint_done())bl_c64_clear_dirty();
  }
  CHECK(!bl_c64_has_dirty());CHECK(!memcmp(before_paint,m,65536));CHECK(bl_c64_check_interleaved(bitmap,0)==0);
  failure=references_valid();if(failure)return 50000+failure;
 }
 return 0;
}
unsigned short *bl_cache_capacity_metrics(void){return capacity_metrics[0];}
unsigned long bl_cache_capacity_slots(void){return BL_CHARACTER_CACHE_SLOTS;}
