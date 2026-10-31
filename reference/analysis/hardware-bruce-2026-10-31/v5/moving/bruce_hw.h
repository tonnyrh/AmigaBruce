/* Private OCS presentation trial. No gameplay/core writes.
 * Original draw order: Kage, Yamo, Bruce. Lower sprite numbers win.
 * All pairs share pen1=black, pen2=yellow7, pen3=green5.
 * 248-byte Copper list; eight92-byte images +4-byte null at256..995.
 * The existing1024-byte allocation suffices for each buffer. */
#define BRUCE_HW_CHANNELS 8
#define BRUCE_HW_HEIGHT 21
#define BRUCE_HW_WORDS (2+BRUCE_HW_HEIGHT*2+2)
#define BRUCE_HW_BYTES ((2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS+4)*2)
static UWORD *bruce_hw_data[2],*bruce_hw_pointer[2][8];
static UBYTE bruce_hw_game;
static short bruce_hw_published=-1;
static UWORD bruce_hw_key[2][3]={{65535,65535,65535},{65535,65535,65535}};
static ULONG bruce_hw_builds,bruce_hw_draws,bruce_hw_hides,bruce_hw_cases,bruce_hw_errors;
static ULONG bruce_hw_samples,bruce_hw_overlap_samples,bruce_hw_missing,bruce_hw_extra;
static UWORD bruce_hw_expected_seen,bruce_hw_actual_seen;
static const UBYTE bruce_hw_first[3]={3,6,0},bruce_hw_count[3]={3,2,3};

static UWORD *bruce_hw_null(int buffer){return bruce_hw_data[buffer]+8*BRUCE_HW_WORDS;}
static void bruce_hw_pointer_set(int buffer,int channel,UWORD *data){
    ULONG at=(ULONG)data;UWORD *p=bruce_hw_pointer[buffer][channel];
    if(p){p[0]=(UWORD)(at>>16);p[2]=(UWORD)at;}
}
static void bruce_hw_blank(void){
    int buffer,ch;
    if(!BL_HW_BRUCE || !bruce_hw_data[0] || !bruce_hw_data[1])return;
    hw->dmacon=DMAF_SPRITE;bruce_hw_published=-1;
    for(buffer=0;buffer<2;buffer++)for(ch=0;ch<8;ch++)bruce_hw_pointer_set(buffer,ch,bruce_hw_null(buffer));
    for(ch=0;ch<8;ch++)hw->spr[ch].dataa=hw->spr[ch].datab=0;
    ++bruce_hw_hides;
}
static void bruce_hw_copper(UWORD **out,int buffer){
    int ch;UWORD *p=*out;ULONG at=(ULONG)bruce_hw_null(buffer);
    for(ch=0;ch<8;ch++){
        *p++=(UWORD)(0x120+ch*4);bruce_hw_pointer[buffer][ch]=p;*p++=(UWORD)(at>>16);
        *p++=(UWORD)(0x122+ch*4);*p++=(UWORD)at;
    }
    for(ch=0;ch<4;ch++){
        *p++=(UWORD)(0x1a2+ch*8);*p++=palette[0];
        *p++=(UWORD)(0x1a4+ch*8);*p++=palette[7];
        *p++=(UWORD)(0x1a6+ch*8);*p++=palette[5];
    }
    /* Include odd channels in pair collisions. Playfield matching disabled;
     * ignore bits0..8 because they do not encode C64 contact classes. */
    *p++=0x098;*p++=0xf000;
    if(p+2>copper[buffer]+128)++bruce_hw_errors;
    *out=p;
}
static void bruce_hw_position(UWORD *sprite,int height,int x,int y){
    UWORD hstart=(UWORD)(x+128),vstart=(UWORD)(y+44),vstop=(UWORD)(vstart+height);
    sprite[0]=(UWORD)((vstart<<8)|((hstart>>1)&255));
    sprite[1]=(UWORD)(((vstop&255)<<8)|((vstart&256)>>6)|((vstop&256)>>7)|(hstart&1));
}
static void bruce_hw_pack(int buffer,int index){
    int kind=index/70,ch,row,height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
    const UWORD *source=(const UWORD *)(fighter_dma+fighter_dma_offsets[index]);
    for(ch=0;ch<bruce_hw_count[kind];ch++){
        UWORD *sprite=bruce_hw_data[buffer]+(bruce_hw_first[kind]+ch)*BRUCE_HW_WORDS;
        const UWORD *s=source+ch;
        for(row=0;row<height;row++,s+=24){
            UWORD mask=s[0],colored=kind==1?0:s[3];
            sprite[2+row*2]=(UWORD)(kind==0?mask:mask&~colored);
            sprite[3+row*2]=colored;
        }
        sprite[2+height*2]=sprite[3+height*2]=0;
    }
    bruce_hw_key[buffer][kind]=(UWORD)index;++bruce_hw_builds;
}
static void bruce_hw_update(int buffer,int index,int left,int top,int visible){
    int kind=index/70,ch,height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
    int width=c64_sprite_bounds[index][2]-c64_sprite_bounds[index][0],columns=(width+15)>>4;
    if(!visible || height<=0 || top<0 || top+height>HEIGHT || left>=WIDTH || left+width<=0){
        for(ch=0;ch<bruce_hw_count[kind];ch++)bruce_hw_pointer_set(buffer,bruce_hw_first[kind]+ch,bruce_hw_null(buffer));
        return;
    }
    if(bruce_hw_key[buffer][kind]!=(UWORD)index)bruce_hw_pack(buffer,index);
    for(ch=0;ch<bruce_hw_count[kind];ch++){
        int channel=bruce_hw_first[kind]+ch;UWORD *sprite=bruce_hw_data[buffer]+channel*BRUCE_HW_WORDS;
        bruce_hw_position(sprite,height,left+ch*16,top);
        bruce_hw_pointer_set(buffer,channel,ch<columns?sprite:bruce_hw_null(buffer));
    }
    ++bruce_hw_draws;
}
/* Diagnostic only. Compare the last complete displayed frame with CLXDAT,
 * including same-actor channel pairs. Not an actor hit or a source$D01E
 * replacement: Amiga reports four groups and source uses eight components.
 * No source-state writes and no read of CLXDAT when observer is disabled. */
static void bruce_hw_observe(void){
    UWORD actual=hw->clxdat&0x7e00,expected=0;int i,j,row,buffer=bruce_hw_published;
    UWORD *s[8];short x[8],y[8],height[8];
    static const UWORD group_bits[4][4]={{0,512,1024,2048},{0,0,4096,8192},{0,0,0,16384},{0,0,0,0}};
    if(buffer<0)return;
    for(i=0;i<8;i++){
        UWORD *p=bruce_hw_pointer[buffer][i];ULONG at=((ULONG)p[0]<<16)|p[2];
        s[i]=(UWORD *)at;
        x[i]=(short)((((s[i][0]&255)<<1)|(s[i][1]&1))-128);
        y[i]=(short)(((s[i][0]>>8)|((s[i][1]&4)<<6))-44);
        height[i]=(short)(((s[i][1]>>8)|((s[i][1]&2)<<7))-y[i]-44);
        if(s[i]==bruce_hw_null(buffer))height[i]=0;
    }
    for(i=0;i<7;i++)for(j=i+1;j<8;j++)if((i>>1)!=(j>>1) && height[i]>0 && height[j]>0){
        int dx=x[j]-x[i],top=y[i]>y[j]?y[i]:y[j],bottom=y[i]+height[i]<y[j]+height[j]?y[i]+height[i]:y[j]+height[j];
        if(dx<=-16 || dx>=16)continue;
        for(row=top;row<bottom;row++){
            UWORD a=s[i][2+(row-y[i])*2]|s[i][3+(row-y[i])*2];
            UWORD b=s[j][2+(row-y[j])*2]|s[j][3+(row-y[j])*2];
            if(dx>=0)b>>=dx;else a>>=-dx;
            if(a&b){expected|=group_bits[i>>1][j>>1];break;}
        }
    }
    ++bruce_hw_samples;if(expected)++bruce_hw_overlap_samples;
    bruce_hw_expected_seen|=expected;bruce_hw_actual_seen|=actual;
    if(expected&~actual)++bruce_hw_missing;
    if(actual&~expected)++bruce_hw_extra;
}
/* Format and colour coverage: all210 ripped frames in both DMA buffers. */
static void bruce_hw_selftest(void){
    int buffer,index,row,col,k;static const short xs[]={-44,-1,0,1,15,16,17,319,320};
    static const short ys[]={0,32,223,235};
    for(buffer=0;buffer<2;buffer++)for(index=0;index<210;index++){
        int kind=index/70,height=c64_sprite_bounds[index][3]-c64_sprite_bounds[index][1];
        const UBYTE *source=fighter_dma+fighter_dma_offsets[index];
        bruce_hw_pack(buffer,index);
        for(row=0;row<height;row++)for(col=0;col<48;col++){
            UWORD bit=(UWORD)(0x8000u>>(col&15));unsigned char pen=0;
            unsigned char mask=source[row*48+col/8]&(128>>(col&7)),color=0;
            if((col>>4)<bruce_hw_count[kind]){
                UWORD *sprite=bruce_hw_data[buffer]+(bruce_hw_first[kind]+(col>>4))*BRUCE_HW_WORDS;
                pen=(unsigned char)((sprite[2+row*2]&bit?1:0)|(sprite[3+row*2]&bit?2:0));
            }
            for(k=0;k<4;k++)if(source[row*48+k*12+6+col/8]&(128>>(col&7)))color|=(unsigned char)(1<<k);
            if(pen!=(mask?(color==7?2:color==5?3:1):0) || (mask && color!=0 && color!=(kind==0?5:kind==2?7:0)))++bruce_hw_errors;
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
    for(buffer=0;buffer<2;buffer++)for(k=0;k<3;k++)bruce_hw_key[buffer][k]=65535;
    bruce_hw_builds=bruce_hw_draws=0;
}
