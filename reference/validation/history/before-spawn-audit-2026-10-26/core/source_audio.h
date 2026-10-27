#ifndef BRUCE_SOURCE_AUDIO_H
#define BRUCE_SOURCE_AUDIO_H
/* Pointer-only public ABI. This module uses the regular32-bit-int build. */
typedef struct {unsigned short offset,length,period,volume;} BlPaulaVoice;
typedef struct {
    unsigned long level[3];
    unsigned char phase[3],gate[3],music_regs[26],music_wait;
    unsigned short music_cursor;
} BlSourceAudio;
unsigned long bl_source_audio_chip_bytes(void);
void bl_source_audio_copy(unsigned char *chip);
void bl_source_audio_reset(BlSourceAudio *audio);
void bl_source_audio_music(BlSourceAudio *audio,unsigned char *registers);
void bl_source_audio_render(BlSourceAudio *audio,const unsigned char *registers,BlPaulaVoice *voices);
unsigned short bl_source_audio_faults(void);
#endif
