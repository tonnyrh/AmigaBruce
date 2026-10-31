/* Presentation query compatibility, not a model of C64 gameplay. */
#include "../core/c64_rooms.c"
#include "baseline_collected.h"
#include <string.h>
static unsigned char preserved[65536];
static unsigned long view_mask_cases,view_bulk_cases;
#define CHECK(q) do{if(!(q))return __LINE__;}while(0)
long bl_view_mask_contract(void){
 unsigned short room,length,mask,i,p,expected,got,all[20],j;unsigned long before;
 static const unsigned short pointers[]={0,1,0xffc0,0xfffc,0xffff,0x4ce2,0x4ce3,0x8c00};
 bl_c64_reset();view_mask_cases=view_bulk_cases=0;
 for(room=0;room<20;room++){
  p=W((unsigned short)(0x4ce2+room*2));
  for(length=0;length<=13;length++)for(mask=0;mask<8192;mask++){
   unsigned char full=(unsigned char)(mask==0 || mask==8191 || mask==0x1555 || mask==0x0aaa);
   for(i=0;i<13;i++)m[(unsigned short)(p+i*4)]=(mask&(1u<<i))?0:(unsigned char)(1+i+room);
   m[(unsigned short)(p+length*4)]=0x80;
   expected=(unsigned short)(mask&((1u<<length)-1));
   if(full)memcpy(preserved,m,65536);
   CHECK(bl_view_mask_reference(room)==expected);
   got=source_collected_mask(room);CHECK(got==expected && bl_c64_collected(room)==expected);
   if(full){
    bl_c64_collected_all(all);++view_bulk_cases;
    for(j=0;j<20;j++)CHECK(all[j]==bl_view_mask_reference(j));
    CHECK(memcmp(preserved,m,65536)==0);
   }
   ++view_mask_cases;
  }
 }
 for(room=0;room<20;room++)for(i=0;i<sizeof(pointers)/sizeof(pointers[0]);i++){
  unsigned short at=(unsigned short)(0x4ce2+room*2),j;p=pointers[i];
  for(j=0;j<64;j++)m[(unsigned short)(p+j)]=(unsigned char)(j*71+room*13);
  m[at]=(unsigned char)p;m[at+1]=(unsigned char)(p>>8);
  memcpy(preserved,m,65536);expected=bl_view_mask_reference(room);got=source_collected_mask(room);
  bl_c64_collected_all(all);++view_bulk_cases;for(j=0;j<20;j++)CHECK(all[j]==bl_view_mask_reference(j));
  CHECK(got==expected && memcmp(preserved,m,65536)==0);++view_mask_cases;
 }
 before=bl_c64_actor_ram_hash();(void)bl_c64_collected(0);CHECK(before==bl_c64_actor_ram_hash());
 return 0;
}
unsigned long bl_view_mask_case_count(void){return view_mask_cases;}

unsigned long bl_view_bulk_case_count(void){return view_bulk_cases;}
