#ifndef BRUCE_SOURCE_PERF_H
#define BRUCE_SOURCE_PERF_H
/* Diagnostic only. Public scalar ABI is long across the -mshort boundary.
 * Nested samples subtract child time; no source RAM/register is modified. */
#ifndef BL_C64_PROFILE
#define BL_C64_PROFILE 0
#endif
enum {
    BL_PERF_LOOP, BL_PERF_FIELD, BL_PERF_VIC, BL_PERF_GAME,
    BL_PERF_ROOM, BL_PERF_CONTACT, BL_PERF_OBJECTS, BL_PERF_COMBAT,
    BL_PERF_ACTORS, BL_PERF_SPRITES, BL_PERF_ALIGN, BL_PERF_ROWS,
    BL_PERF_SPRITE_COPY, BL_PERF_AUDIO_SOURCE, BL_PERF_AUDIO_RENDER,
    BL_PERF_AUDIO_DMA, BL_PERF_AUDIO_PUBLISH, BL_PERF_VIEW,
    BL_PERF_BACKGROUND, BL_PERF_RESTORE, BL_PERF_DRAW, BL_PERF_LOAD,
    BL_PERF_WAIT, BL_PERF_SLOTS
};
#define BL_PERF_BINS 40
#if BL_C64_PROFILE && defined(__m68k__)
void bl_perf_begin(long slot);
void bl_perf_end(long slot);
void bl_perf_reset(void);
unsigned long bl_perf_value(long slot,long field);
#define PERF_BEGIN(id) bl_perf_begin(id)
#define PERF_END(id) bl_perf_end(id)
#else
#define PERF_BEGIN(id) ((void)0)
#define PERF_END(id) ((void)0)
#define bl_perf_reset() ((void)0)
#define bl_perf_value(slot,field) 0UL
#endif
#endif
