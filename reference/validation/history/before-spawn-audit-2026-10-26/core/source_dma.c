#include "source_dma.h"
void bl_source_dma_reset(BlSourceDma *s){
    unsigned short c;for(c=0;c<3;c++)s->offset[c]=s->length[c]=65535;
}
unsigned short bl_source_dma_update(BlSourceDma *s,unsigned char *images,
    const unsigned char *bank,unsigned long bytes,const BlPaulaVoice *voices){
    unsigned short c,changed=0;
    for(c=0;c<3;c++){
        const BlPaulaVoice *v=voices+c;unsigned short n,repeat;
        unsigned long *dst;const unsigned long *src;
        if(!v->length || v->length>1024 || (v->length&3) || (v->offset&3) ||
           (unsigned long)v->offset+v->length>bytes || (v->length&(v->length-1)))return 0x8000;
        /* A muted voice need not rewrite1024 bytes of inaudible RAM. Keep
         * its last image/cache; an audible change still replaces it fully. */
        if(!v->volume)continue;
        if(s->offset[c]==v->offset && s->length[c]==v->length)continue;
        dst=(unsigned long*)(images+c*1024);src=(const unsigned long*)(bank+v->offset);
        for(repeat=0;repeat<1024/v->length;repeat++)
            for(n=0;n<v->length/4;n++)*dst++=src[n];
        s->offset[c]=v->offset;s->length[c]=v->length;changed|=(unsigned short)(1<<c);
    }
    return changed;
}
