/* Host-only exact before/after cache comparison; not VIC raster certification. */
#include <string.h>
#include "../core/c64_rooms.c"
#include "baseline_cache.h"
static unsigned long cases;
static unsigned char ram_before[65536];
static SourceVicRepeat initial,wanted;
static unsigned long want_high[8][21],want_low[8][21];
static long compare_cache(unsigned char sprite,unsigned short pointer,unsigned char multi,unsigned char wide){
 unsigned short j;
 memset(&vic_repeat,0xa5,sizeof(vic_repeat));
 for(j=0;j<8*21;j++){((unsigned long *)vic_high)[j]=0x12340000UL+j;((unsigned long *)vic_low)[j]=0x56780000UL+j;}
 initial=vic_repeat;reference_vic_cache(sprite,pointer,multi,wide);wanted=vic_repeat;
 memcpy(want_high,vic_high,sizeof(vic_high));memcpy(want_low,vic_low,sizeof(vic_low));
 vic_repeat=initial;
 for(j=0;j<8*21;j++){((unsigned long *)vic_high)[j]=0x12340000UL+j;((unsigned long *)vic_low)[j]=0x56780000UL+j;}
 source_vic_cache(sprite,pointer,multi,wide);++cases;
 if(memcmp(&wanted,&vic_repeat,sizeof(wanted)))return 1;
 if(memcmp(want_high,vic_high,sizeof(vic_high)))return 2;
 if(memcmp(want_low,vic_low,sizeof(vic_low)))return 3;
 return 0;
}
long bl_vic_cache_contract(void){
 unsigned long i;unsigned short value,position,mode,sprite,pointer,pass,j;long result;
 cases=0;
 for(i=0;i<65536;i++)m[i]=(unsigned char)(i*37+(i>>8)*13);
 for(sprite=0;sprite<8;sprite++)for(mode=0;mode<4;mode++)for(position=0;position<3;position++)for(value=0;value<256;value++){
  pointer=(value&1)?0xfffc:0x2000;
  for(j=0;j<63;j++)m[(unsigned short)(pointer+j)]=(unsigned char)(j*53+value*7);
  for(j=position;j<63;j+=3)m[(unsigned short)(pointer+j)]=(unsigned char)value;
  result=compare_cache((unsigned char)sprite,pointer,(unsigned char)(mode&1),(unsigned char)(mode&2));if(result)return 100+result;
 }
 for(pass=0;pass<1024;pass++){
  pointer=(unsigned short)(pass*73+0xffc0);
  for(j=0;j<63;j++)m[(unsigned short)(pointer+j)]=(unsigned char)(pass*19+j*31+(pass>>3));
  memcpy(ram_before,m,65536);
  result=compare_cache((unsigned char)(pass&7),pointer,(unsigned char)(pass&0x55),(unsigned char)(pass&0xaa));if(result)return 200+result;
  if(memcmp(ram_before,m,65536))return 204;
 }
 return 0;
}
unsigned long bl_vic_cache_cases(void){return cases;}
