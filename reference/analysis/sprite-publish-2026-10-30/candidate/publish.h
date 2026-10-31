/* Binary $25E2-$269F. The source guard and every RAM/stack store remain.
 * No I/O service observes the interiors. Decimal entries keep original code. */
SOURCE_INLINE void source_publish_component(unsigned char id,unsigned char color){
    unsigned char high=(unsigned char)(a>>7),old=m[0xa1+x];
    unsigned short total=(unsigned short)old+29;
    a=(unsigned char)(a<<1);m[0x100+sp--]=a;
    y=id;a=m[0xd010];
    if(high)a|=m[0x2773+y];else a&=m[0x2778+y];
    m[0xd010]=a;y=(unsigned char)(id<<1);
    a=m[0x100+(unsigned char)++sp];m[0xd000+y]=a;
    a=(unsigned char)total;m[0xd001+y]=a;
    c=(unsigned char)(total>255);v=(unsigned char)((~(old^29)&(old^a)&128)!=0);
    y=id;a=color;m[0xd027+y]=a;NZ(a);
}
#if defined(__m68k__) && defined(__GNUC__)
__attribute__((optimize("O2")))
#endif
static SOURCE_NOINLINE void source_sprite_publish(void){
    unsigned char pose;
    a=m[0x277e];NZ(a);if(a){sp+=2;return;}
    ++m[0x277e];x=2;
    for(;;){
        m[0x51]=x;a=(unsigned char)(m[0x95+x]&1);
        if(a){
            a=m[0x9e + x];m[0xb9+x]=a;
            if(m[0xd4+x] && m[0xa4+x]!=1)a=(unsigned char)(a-8);
            source_publish_component(m[0x276d+x],m[0xda+x]);
            if(x==2)c=1;
            else{
                pose=m[0x4f4b+x];a=m[0x9e + x];
                if(pose==5 || pose==0x3f || pose==0x43 || pose==0x19)a=(unsigned char)(a-8);
                source_publish_component(m[0x2770+x],m[0xdd+x]);
            }
        }
        x=(unsigned char)(m[0x51]-1);if(x&128)break;
    }
    x=4;y=m[0x277d]?9:4;
    do{a=m[0x2763+y];m[0x8ff8+x]=a;--y;--x;}while(!(x&128));
    a=(unsigned char)(m[0x277d]^1);m[0x277d]=a;NZ(a);sp+=2;
}
