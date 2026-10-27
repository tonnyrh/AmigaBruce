/* Test-only lossless snapshot. Keep the saved image in CPU RAM and unpack
 * into a detached bitmap after OS restoration; avoid a40KiB Chip spill. */
#if BL_COMBAT_TEST && !BL_ROOM_TEST && !BL_ROOM_TOUR && !BL_GATE_TEST && !BL_ENEMY_EDGE_TEST && !BL_ROOM_LOAD_TEST && !BL_ELECTRIC_TEST
/* R01 combat capture is about10KiB. Bound this diagnostic buffer to16KiB;
 * retain full decoded-image/hash checks and larger room-tour capacity. */
#define BL_CAPTURE_BYTES 16384
#else
#define BL_CAPTURE_BYTES 24576
#endif
static ULONG capture_bytes,capture_original_hash,capture_decoded_hash;static UWORD capture_fault;
static void capture_pack(UBYTE *out,const UBYTE *src){
    ULONG at=0,used=0;
    while(at<BITMAP_BYTES){
        ULONG end=at+1,start;
        while(end<BITMAP_BYTES && src[end]==src[at] && end-at<127)++end;
        if(end-at>=3){
            if(used+2>BL_CAPTURE_BYTES){capture_fault=1;return;}
            out[used++]=(UBYTE)(128+end-at);out[used++]=src[at];at=end;
        }else{
            start=at;at=end;
            while(at<BITMAP_BYTES && at-start<127){
                if(at+2<BITMAP_BYTES && src[at]==src[at+1] && src[at]==src[at+2])break;
                ++at;
            }
            if(used+1+at-start>BL_CAPTURE_BYTES){capture_fault=1;return;}
            out[used++]=(UBYTE)(at-start);
            while(start<at)out[used++]=src[start++];
        }
        source_audio_service();
    }
    capture_bytes=used;
    capture_original_hash=2166136261UL;
    for(at=0;at<BITMAP_BYTES;at++){
        capture_original_hash=(capture_original_hash^src[at])*16777619UL;
        if(!(at&255))source_audio_service();
    }
}
static void capture_unpack(UBYTE *out,const UBYTE *src){
    ULONG at=0,used=0;UBYTE code,value;UWORD count;
    while(at<capture_bytes && used<BITMAP_BYTES){
        code=src[at++];count=code&127;
        if(!count || used+count>BITMAP_BYTES){capture_fault=2;return;}
        if(code&128){value=src[at++];while(count--)out[used++]=value;}
        else while(count--)out[used++]=src[at++];
    }
    if(used!=BITMAP_BYTES || at!=capture_bytes)capture_fault=3;
    capture_decoded_hash=2166136261UL;
    for(at=0;at<BITMAP_BYTES;at++)capture_decoded_hash=(capture_decoded_hash^out[at])*16777619UL;
    if(capture_decoded_hash!=capture_original_hash)capture_fault=4;
}
