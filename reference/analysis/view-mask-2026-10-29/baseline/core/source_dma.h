#ifndef BRUCE_SOURCE_DMA_H
#define BRUCE_SOURCE_DMA_H
#include "source_audio.h"
/* Permanent per-voice DMA address/length. Every source cycle divides1024. */
#define BL_SOURCE_DMA_VOICE_BYTES 1024
#define BL_SOURCE_DMA_BYTES (3*BL_SOURCE_DMA_VOICE_BYTES)
typedef struct {unsigned short offset[3],length[3];} BlSourceDma;
void bl_source_dma_reset(BlSourceDma *state);
unsigned short bl_source_dma_update(BlSourceDma *state,unsigned char *images,
    const unsigned char *bank,unsigned long bank_bytes,const BlPaulaVoice *voices);
#endif
