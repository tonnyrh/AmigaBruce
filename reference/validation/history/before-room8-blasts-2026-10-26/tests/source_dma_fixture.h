#ifndef BRUCE_SOURCE_DMA_FIXTURE_H
#define BRUCE_SOURCE_DMA_FIXTURE_H
#include "../core/source_dma.h"
#define BL_SOURCE_DMA_FIXTURE_CASES 7
static unsigned short source_dma_fixture_run(unsigned char *workspace){
    unsigned char *bank=workspace,*images=workspace+1024;
    static const unsigned short lengths[5]={4,8,16,32,1024};
    BlSourceDma state;BlPaulaVoice v[3];unsigned short i,c,at,code;
    for(at=0;at<1024;at++)bank[at]=(unsigned char)(at*37+at/7);
    bl_source_dma_reset(&state);
    for(i=0;i<5;i++){
        for(c=0;c<3;c++){v[c].offset=0;v[c].length=lengths[(i+c)%5];v[c].volume=64;}
        code=bl_source_dma_update(&state,images,bank,1024,v);
        if(code!=7)return i+1;
        for(c=0;c<3;c++)for(at=0;at<1024;at++)
            if(images[c*1024+at]!=bank[at%v[c].length])return i+1;
    }
    if(bl_source_dma_update(&state,images,bank,1024,v))return 6;
    v[0].length=6;if(bl_source_dma_update(&state,images,bank,1024,v)!=0x8000)return 7;
    return 0;
}
#endif
