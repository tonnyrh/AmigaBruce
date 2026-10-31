/* Host-only occupancy probe through the actual source-world start/jump/step. */
#include "../../../tests/source_paint_bridge.c"
static unsigned short result[20][5];
static void measure(unsigned short room){
 unsigned short i,slots=0,total=0,largest=0;
 for(i=0;i<1024;i++)if(cache_references[i]){++slots;total+=cache_references[i];if(cache_references[i]>largest)largest=cache_references[i];}
 if(slots>result[room][0])result[room][0]=slots;
 if(total>result[room][1])result[room][1]=total;
 if(largest>result[room][2])result[room][2]=largest;
}
long bl_cache_probe(void){
 unsigned short room,step,cell;
 bl_c64_set_painter(interleaved_tile);bl_c64_set_block_painter(block_copy);bl_c64_reset();bl_c64_world_start(1,0);
 for(room=0;room<20;room++){
  bl_c64_world_jump(room);bl_c64_paint_room(bitmap,0);measure(room);
  if(bl_c64_check_interleaved(bitmap,0))return 100+room;
  for(step=0;step<120;step++){
   bl_c64_field();bl_c64_field();bl_c64_field();bl_c64_world_step(1,1);bl_c64_prepare_paint();
   bl_c64_paint_room(bitmap,0);measure(room);
   if(bl_c64_check_interleaved(bitmap,0))return 200+room;
   if(bl_c64_fault())return 300+room;
  }
  result[room][3]=(unsigned short)bl_c64_world_stat(0);result[room][4]=m[0x29]+1;
 }
 return 0;
}
unsigned short *bl_cache_probe_data(void){return result[0];}
