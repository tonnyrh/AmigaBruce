/* Decode one literal or repeated token at $0AD7, including $0B5F
 * and the row skip at $485B. Non-loader, overlapping and unusual
 * pointers continue in the instruction translation. */
static unsigned char source_room_token(void){
    unsigned short stream=W(6),upper=W(4),lower=W(8),paint=W(0x10),paint_lower=W(0x12);
    unsigned short count;
    unsigned char token,code=0,literal,remaining=m[0xf3];
    if(index_ready || !actor_loading_pending || d || y || remaining>39 ||
       stream<0x6800 || stream>=0x8200 || upper<0x8c78 || upper>=0x9000 ||
       lower!=upper+40 || paint!=upper+0x4c00 || paint_lower!=paint+40)return 0;
    token=m[stream++];count=token&127;
    if(!count)return 0; /* $80 terminates; $00 is the 256-copy case. */
    literal=token&128;
    do{
        code=m[stream];if(literal)++stream;
        if(code&128){m[paint]=0xf8;m[paint+40]=0xf8;}
        m[upper]=code&127;m[upper+40]=code|128;
        /* A 442-cell stream touches the first collision mask. */
        if(upper+40>=0x9000)reset_contact_masks();
        ++upper;++paint;
        if(!remaining){
            unsigned char before=(unsigned char)(paint+40);
            unsigned short sum=(unsigned short)before+40;
            c=sum>255;v=((~(before^40)&(before^sum)&128)!=0);
            remaining=39;upper+=40;paint+=40;
        }else --remaining;
    }while(--count);
    if(!literal)++stream;
    m[4]=(unsigned char)upper;m[5]=(unsigned char)(upper>>8);
    m[8]=(unsigned char)(upper+40);m[9]=(unsigned char)((upper+40)>>8);
    m[0x10]=(unsigned char)paint;m[0x11]=(unsigned char)(paint>>8);
    m[0x12]=(unsigned char)(paint+40);m[0x13]=(unsigned char)((paint+40)>>8);
    m[6]=(unsigned char)stream;m[7]=(unsigned char)(stream>>8);m[0xf3]=remaining;
    a=code|128;x=0;
    m[0x100+sp]=0x0b;m[0x100+(unsigned char)(sp-1)]=literal?1:0x2c;
    m[0x100+(unsigned char)(sp-2)]=a;
    actor_return=literal?0x0b02:0x0b27;
    if(literal){n=0;z=1;}else{unsigned char last=m[6]?m[6]:m[7];NZ(last);}
    return 1;
}
