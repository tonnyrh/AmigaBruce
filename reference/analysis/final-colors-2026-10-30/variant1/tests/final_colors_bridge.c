/* Host-only slice and renderer-state controls; source bytes run independently. */
#include "../core/c64_rooms.c"
static unsigned char fc_bitmap[40960],fc_cache[106496];
static void fc_tile(const BlC64Paint *q){
 unsigned long row,p,col=q->cell%40,top=q->scene_top+cell_y[q->cell];
 for(row=0;row<8;row++)for(p=0;p<4;p++)q->bitmap[(top+row)*160+p*40+col]=q->planes[p*8+row];
}
static void fc_block(const BlC64Block *q){
 unsigned long y,p,c,w=q->width;
 for(y=0;y<q->height;y++)for(p=0;p<4;p++)for(c=0;c<w;c++){
  unsigned char mask=255;unsigned long dst=(q->top+y)*160+p*40+q->left+c,src=(y*4+p)*w+c;
  if(c<2)mask&=(unsigned char)(q->first_mask>>(c?0:8));
  if(c>=w-2)mask&=(unsigned char)(q->last_mask>>((c==w-2)?8:0));
  q->bitmap[dst]=(q->bitmap[dst]&~mask)|(q->pixels[src]&mask);
 }
}
static void fc_run(void){
#if FINAL_COLORS_FAST
 source_final_colors();
#else
 unsigned short address;do{
  address=(unsigned short)(0xdaac+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdad4+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdafc+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdb24+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdb4c+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdb74+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdb9c+x);m[address]=a;source_written(address);
  address=(unsigned short)(0xdbc4+x);m[address]=a;source_written(address);--x;NZ(x);
 }while(!n);
#endif
}
void bl_fc_seed(const unsigned char *ram,const unsigned char *r){
 unsigned long i;index_ready=0;for(i=0;i<65536;i++)m[i]=ram[i];
 a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
}
void bl_fc_slice(void){fc_run();}
void bl_fc_copy(unsigned char *out){unsigned long i;for(i=0;i<65536;i++)out[i]=m[i];}
void bl_fc_regs(unsigned char *out){out[0]=a;out[1]=x;out[2]=y;out[3]=c;out[4]=z;out[5]=n;out[6]=v;out[7]=d;out[8]=sp;out[9]=actor_i;}
long bl_fc_renderer(long variant){
 unsigned short i,count,loops;bl_c64_reset();bl_c64_load(variant&1?5:19);
 bl_c64_set_block_painter(fc_block);bl_c64_set_painter(fc_tile);bl_c64_paint_room(fc_bitmap,0);bl_c64_clear_dirty();
 (void)bl_c64_build_animation_cache(fc_cache,sizeof(fc_cache));
 for(i=0;i<1000;i++)if((i+variant)%13==0){m[0xd800+i]=(unsigned char)(variant+i);source_written((unsigned short)(0xd800+i));}
 for(loops=0;loops<32 && bl_c64_has_dirty();loops++){bl_c64_paint_part(fc_bitmap,0,160,&count);if(bl_c64_paint_done())bl_c64_clear_dirty();}
 a=(unsigned char)(variant*17);x=(unsigned char)(variant%29);y=33;c=z=n=v=d=0;sp=253;fc_run();
 for(loops=0;loops<32 && bl_c64_has_dirty();loops++){bl_c64_paint_part(fc_bitmap,0,160,&count);if(bl_c64_paint_done())bl_c64_clear_dirty();}
 return bl_c64_check_interleaved(fc_bitmap,0);
}
unsigned long bl_fc_metadata(unsigned char *out){
 unsigned long size=0,i;const unsigned char *p;
#define FC_COPY(q) do{p=(const unsigned char*)&q;for(i=0;i<sizeof(q);i++)out[size++]=p[i];}while(0)
 FC_COPY(indexed_screen);FC_COPY(indexed_color);FC_COPY(flash_cells);FC_COPY(flash_changed);FC_COPY(display_dirty);
 FC_COPY(dirty_cells);FC_COPY(paint_rows);FC_COPY(paint_queued);FC_COPY(paint_list);FC_COPY(paint_count);FC_COPY(paint_cursor);
 FC_COPY(contact_cells);FC_COPY(cell_cache);
 {unsigned short k,offset;for(k=0;k<1000;k++){
  if(cell_stamp[k] && (cell_cache[k]>=1024 || cell_stamp[k]!=character_cache[cell_cache[k]].planes[0]))return 200000;
  offset=cell_stamp[k]?(unsigned short)(cell_stamp[k]-(unsigned char*)character_cache):65535;
  out[size++]=(unsigned char)(offset>>8);out[size++]=(unsigned char)offset;
 }}
 FC_COPY(cache_references);FC_COPY(character_cache);
 FC_COPY(animation_fallback_dirty);FC_COPY(animation_mismatch);FC_COPY(animation_differences);FC_COPY(fc_bitmap);
 return size;
}
