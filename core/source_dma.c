#include "source_dma.h"
#ifdef __m68k__
/* Refill a changed Paula image in 32-byte bursts. Short cycles are read
 * from Chip RAM once, then repeated from registers. */
static void source_dma_fill(unsigned long *dst,const unsigned long *src,unsigned short length){
    const unsigned long *end=dst+256;
    unsigned long block[8];
    if(length<=32){
        unsigned short i,mask=(unsigned short)((length>>2)-1);
        for(i=0;i<8;i++)block[i]=src[i&mask];
        __asm__ volatile("movem.l (%1),%%d0-%%d7\n"
            "1: movem.l %%d0-%%d7,(%0)\n lea 32(%0),%0\n cmpa.l %2,%0\n bne.s 1b"
            : "+&a"(dst) : "a"(block),"a"(end) : "d0","d1","d2","d3","d4","d5","d6","d7","cc","memory");
    }else{
        const unsigned long *limit=src+(length>>2);
        do{
            const unsigned long *from=src;
            __asm__ volatile("1: movem.l (%1)+,%%d0-%%d7\n movem.l %%d0-%%d7,(%0)\n"
                "lea 32(%0),%0\n cmpa.l %2,%1\n bne.s 1b"
                : "+&a"(dst),"+&a"(from) : "a"(limit) : "d0","d1","d2","d3","d4","d5","d6","d7","cc","memory");
        }while(dst!=end);
    }
}

#endif
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
#ifdef __m68k__
        source_dma_fill(dst,src,v->length);
#else
        for(repeat=0;repeat<1024/v->length;repeat++)
            for(n=0;n<v->length/4;n++)*dst++=src[n];
#endif
        s->offset[c]=v->offset;s->length[c]=v->length;changed|=(unsigned short)(1<<c);
    }
    return changed;
}
