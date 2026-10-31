
static unsigned short image_destination(unsigned char sprite){
    unsigned char yy=(unsigned char)(sprite*2);if(m[0x277d])yy+=10;
    return W((unsigned short)(0x274f+yy));
}
static unsigned char image_driver_safe(void){
    short actor;unsigned char part,pose,sprite,height;unsigned short pointer,dest;
    if(d)return 0;
    for(actor=2;actor>=0;--actor)if(m[0x95+actor]&1){
        for(part=0;part<2;part++){
            if(part && (actor==2 || (m[0x2770+actor]&128)))break;
            sprite=m[(part?0x2770:0x276d)+actor];dest=image_destination(sprite);
            pose=(unsigned char)(m[0x4f4e + actor]+part);height=m[0x5b61+pose];
            pointer=(unsigned short)(m[0x59bd+pose]|((unsigned short)m[0x5a8f+pose]<<8));
            if(height>=32 || pointer>0xff00 || dest<0x8000 || dest>0xff00)return 0;
        }
    }
    return 1;
}
static void image_pointer(unsigned char sprite){
    y=(unsigned char)(sprite*2);if(m[0x277d])y+=10;
    a=m[0x274f+y];m[0x0e]=a;a=m[0x2750+y];m[0x0f]=a;sp+=2;
}
static void image_glyph(unsigned char pose){
    a=m[0x59bd+pose];m[0x26ab]=a;m[0x26e4]=a;m[0x26ee]=a;
    a=m[0x5a8f+pose];m[0x26ac]=a;m[0x26e5]=a;m[0x26ef]=a;
    y=m[0x5b61+pose];a=m[0x51]==2?0xf0:m[0x5c33+pose];
    m[0x100+sp--]=a;a=m[0x5cbf+pose];m[0x100+sp--]=a;
    x=m[0x51];a=y;m[0xe0+x]=a;
    a=m[0x100+(unsigned char)++sp];x=a;a=m[0x100+(unsigned char)++sp];sp+=2;
}
static void image_component(unsigned char second){
    /* Source PHA/TXA/LDX/STA/PLA order, including unused stack bytes. */
    m[0x100+sp--]=a;a=x;x=m[0x51];m[(second?0xd7:0xd4)+x]=a;
    a=m[0x100+(unsigned char)++sp];m[(second?0xdd:0xda)+x]=a;
    /* h<32: ASL h then ADC h produces 3*h with C=V=0. */
    y=(unsigned char)(y*3);c=v=0;a=m[(second?0xd7:0xd4)+x];NZ(a);
    source_contact_frame(second?0x25d6:0x25ad);
    PERF_BEGIN(BL_PERF_SPRITE_COPY);source_sprite_copy();PERF_END(BL_PERF_SPRITE_COPY);
}
static unsigned char source_image_driver(void){
    if(!image_driver_safe())return 0;
    x=2;
    for(;;){
        m[0x51]=x;
        if(m[0x95+x]&1){
            a=m[0x276d+x];source_contact_frame(0x2593);image_pointer(a);
            a=m[0x4f4e + x];source_contact_frame(0x259a);image_glyph(a);image_component(0);
            x=m[0x51];c=(unsigned char)(x>=2);
            if(x!=2 && !(m[0x2770+x]&128)){
                a=m[0x2770+x];source_contact_frame(0x25bb);image_pointer(a);
                a=(unsigned char)(m[0x4f4e + x]+1);source_contact_frame(0x25c3);image_glyph(a);image_component(1);
            }
        }
        x=(unsigned char)(m[0x51]-1);if(x&128)break;
    }
    a=0;z=1;n=0;m[0x277e]=0;sp+=2;return 1;
}
