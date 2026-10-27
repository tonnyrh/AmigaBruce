#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char UBYTE;
typedef unsigned short UWORD;
typedef unsigned long ULONG;
#define BITMAP_BYTES 40960
static void source_audio_service(void){}
#include "packed_capture.h"
static UBYTE original[BITMAP_BYTES],restored[BITMAP_BYTES+16],packed[BL_CAPTURE_BYTES+16];
int main(int argc,char **argv){
    FILE *file;ULONG size,hash;unsigned int i,random=20261025;
    if(argc!=2)return 1;
    file=fopen(argv[1],"rb");if(!file)return 2;
    if(fread(original,1,BITMAP_BYTES,file)!=BITMAP_BYTES)return 3;
    fclose(file);memset(packed,0xa5,sizeof(packed));memset(restored,0x5a,sizeof(restored));
    capture_pack(packed,original);if(capture_fault)return 4;
    size=capture_bytes;capture_unpack(restored,packed);if(capture_fault)return 5;
    if(memcmp(original,restored,BITMAP_BYTES))return 6;
    hash=capture_decoded_hash;
    for(i=0;i<16;i++)if(packed[BL_CAPTURE_BYTES+i]!=0xa5 || restored[BITMAP_BYTES+i]!=0x5a)return 7;
    /* Incompressible input must fail without writing beyond the CPU buffer. */
    for(i=0;i<BITMAP_BYTES;i++){random=random*1664525U+1013904223U;original[i]=(UBYTE)(random>>24);}
    capture_fault=0;capture_pack(packed,original);if(capture_fault!=1)return 8;
    for(i=0;i<16;i++)if(packed[BL_CAPTURE_BYTES+i]!=0xa5)return 9;
    printf("PASS capture round-trip bytes=%lu packed=%lu hash=%lu; incompressible capacity/guard case\n",(ULONG)BITMAP_BYTES,size,hash);
    return 0;
}
