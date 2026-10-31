/* Presentation-only experiment. Same ripped pixels and anchors as BOB.
 * Harrier references: setHardwareSpritePosition, copSetSprites and
 * updateHardwareProjectileChain. No gameplay or source collision changes.
 * Bruce uses <=36px and two opaque colours: three normal16px channels,
 * pen1=opaque black, pen2=C64 colour7. No attachment/multiplexing needed. */
#define BRUCE_HW_CHANNELS 3
#define BRUCE_HW_HEIGHT 21
#define BRUCE_HW_WORDS (2+BRUCE_HW_HEIGHT*2+2)
#define BRUCE_HW_BYTES ((2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS+2)*2)
static UWORD *bruce_hw_data,*bruce_hw_pointer[2][8];
static UBYTE bruce_hw_game;
static UWORD bruce_hw_key[2]={65535,65535};
static ULONG bruce_hw_builds,bruce_hw_draws,bruce_hw_hides,bruce_hw_cases,bruce_hw_errors;

static UWORD *bruce_hw_null(void){return bruce_hw_data+2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS;}
static void bruce_hw_pointer_set(int buffer,int channel,UWORD *data){
    ULONG at=(ULONG)data;UWORD *p=bruce_hw_pointer[buffer][channel];
    if(p){p[0]=(UWORD)(at>>16);p[2]=(UWORD)at;}
}
static void bruce_hw_blank(void){
    int buffer,ch;
    if(!BL_HW_BRUCE || !bruce_hw_data)return;
    hw->dmacon=DMAF_SPRITE;
    for(buffer=0;buffer<2;buffer++)for(ch=0;ch<8;ch++)bruce_hw_pointer_set(buffer,ch,bruce_hw_null());
    for(ch=0;ch<8;ch++)hw->spr[ch].dataa=hw->spr[ch].datab=0;
    ++bruce_hw_hides;
}
static void bruce_hw_copper(UWORD **out,int buffer){
    int ch;UWORD *p=*out;ULONG at=(ULONG)bruce_hw_null();
    for(ch=0;ch<8;ch++){
        *p++=(UWORD)(0x120+ch*4);bruce_hw_pointer[buffer][ch]=p;*p++=(UWORD)(at>>16);
        *p++=(UWORD)(0x122+ch*4);*p++=(UWORD)at;
    }
    /* Channels0/1 share17..19; channel2 uses21..23. */
    *p++=0x1a2;*p++=palette[0];*p++=0x1a4;*p++=palette[7];
    *p++=0x1aa;*p++=palette[0];*p++=0x1ac;*p++=palette[7];
    *out=p;
}
static void bruce_hw_position(UWORD *sprite,int height,int x,int y){
    UWORD hstart=(UWORD)(x+128),vstart=(UWORD)(y+44),vstop=(UWORD)(vstart+height);
    sprite[0]=(UWORD)((vstart<<8)|((hstart>>1)&255));
    sprite[1]=(UWORD)(((vstop&255)<<8)|((vstart&256)>>6)|((vstop&256)>>7)|(hstart&1));
}
static void bruce_hw_pack(int buffer,int index){
    int ch,row,height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
    const UWORD *source=(const UWORD *)(fighter_dma+fighter_dma_offsets[index]);
    for(ch=0;ch<BRUCE_HW_CHANNELS;ch++){
        UWORD *sprite=bruce_hw_data+(buffer*BRUCE_HW_CHANNELS+ch)*BRUCE_HW_WORDS;
        const UWORD *s=source+ch;
        for(row=0;row<height;row++,s+=24){
            UWORD mask=s[0],yellow=s[3];
            sprite[2+row*2]=(UWORD)(mask&~yellow);
            sprite[3+row*2]=yellow;
        }
        sprite[2+height*2]=sprite[3+height*2]=0;
    }
    bruce_hw_key[buffer]=(UWORD)index;++bruce_hw_builds;
}
static void bruce_hw_update(int buffer,int index,int left,int top,int visible){
    int ch,height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
    int width=c64_sprite_bounds[index][2]-c64_sprite_bounds[index][0];
    int columns=(width+15)>>4;
    if(!visible || height<=0 || top<0 || top+height>HEIGHT || left>=WIDTH || left+width<=0){
        for(ch=0;ch<BRUCE_HW_CHANNELS;ch++)bruce_hw_pointer_set(buffer,ch,bruce_hw_null());
        return;
    }
    if(bruce_hw_key[buffer]!=(UWORD)index)bruce_hw_pack(buffer,index);
    for(ch=0;ch<BRUCE_HW_CHANNELS;ch++){
        UWORD *sprite=bruce_hw_data+(buffer*BRUCE_HW_CHANNELS+ch)*BRUCE_HW_WORDS;
        bruce_hw_position(sprite,height,left+ch*16,top);
        bruce_hw_pointer_set(buffer,ch,ch<columns?sprite:bruce_hw_null());
    }
    ++bruce_hw_draws;
}
/* Executed only before the measured game loop. Test all70 source poses,
 * both DMA buffers, transparency/black/yellow and control-word carries. */
static void bruce_hw_selftest(void){
    int buffer,index,row,col,k;static const short xs[]={-36,-1,0,1,15,16,17,319,320};
    static const short ys[]={0,32,223,235};
    for(buffer=0;buffer<2;buffer++)for(index=140;index<210;index++){
        int height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
        const UBYTE *source=fighter_dma+fighter_dma_offsets[index];
        bruce_hw_pack(buffer,index);
        for(row=0;row<height;row++)for(col=0;col<48;col++){
            UWORD *sprite=bruce_hw_data+(buffer*BRUCE_HW_CHANNELS+(col>>4))*BRUCE_HW_WORDS;
            UWORD bit=(UWORD)(0x8000u>>(col&15));
            unsigned char pen=(unsigned char)((sprite[2+row*2]&bit?1:0)|(sprite[3+row*2]&bit?2:0));
            unsigned char mask=source[row*48+col/8]&(128>>(col&7)),color=0;
            for(k=0;k<4;k++)if(source[row*48+k*12+6+col/8]&(128>>(col&7)))color|=(unsigned char)(1<<k);
            if(pen!=(mask?(color==7?2:1):0) || (mask && color!=0 && color!=7))++bruce_hw_errors;
        }
        ++bruce_hw_cases;
    }
    for(row=0;row<9;row++)for(col=0;col<4;col++){
        UWORD q[2],h,v,stop;bruce_hw_position(q,21,xs[row],ys[col]);
        h=(UWORD)(((q[0]&255)<<1)|(q[1]&1));v=(UWORD)((q[0]>>8)|((q[1]&4)<<6));
        stop=(UWORD)((q[1]>>8)|((q[1]&2)<<7));
        if(h!=(UWORD)(xs[row]+128)||v!=(UWORD)(ys[col]+44)||stop!=v+21||(q[1]&128))++bruce_hw_errors;
        ++bruce_hw_cases;
    }
    bruce_hw_key[0]=bruce_hw_key[1]=65535;
    bruce_hw_builds=bruce_hw_draws=0;
}
