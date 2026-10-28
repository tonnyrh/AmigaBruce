/* Host-only painter regression; all data are from the source room engine. */
#include "../core/c64_rooms.c"
static unsigned char bitmap[40960];
static void interleaved_tile(const BlC64Paint *q){
 unsigned short r,p,cy=cell_y[q->cell],column=(unsigned short)(q->cell%40);
 for(r=0;r<8;r++)for(p=0;p<4;p++)q->bitmap[(q->scene_top+cy+r)*160+p*40+column]=q->planes[p*8+r];
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
