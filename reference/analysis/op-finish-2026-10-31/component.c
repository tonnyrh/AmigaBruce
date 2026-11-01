/* One active component. $2586 still services every actor, including
 * inactive actors. Read the active actor again after that callback. */
static unsigned char source_image_component(unsigned char secondary){
    unsigned char actor=x,pose,index,height,color,width,stack=sp;
    unsigned short dest,first;
    if(d || actor>=3 || actor!=m[0x51])return 0;
    index=(unsigned char)(a*2+(m[0x277d]?10:0));dest=W(0x274f+index);
    pose=(unsigned char)(m[0x4f4e + actor]+secondary);
    height=m[0x5b61+pose];first=m[0x59bd+pose]|((unsigned short)m[0x5a8f+pose]<<8);
    if(height>=32 || dest<0x8000 || dest>0xff00 || first>0xff00)return 0;
    /* $2704 and $2719 use no deeper calls. The two calls have the
     * same stack depth as the copy call below and leave its bytes. */
    m[0x0e]=(unsigned char)dest;m[0x0f]=(unsigned char)(dest>>8);
    m[0x26ab]=m[0x26e4]=m[0x26ee]=(unsigned char)first;
    m[0x26ac]=m[0x26e5]=m[0x26ef]=(unsigned char)(first>>8);
    color=actor==2?0xf0:m[0x5c33+pose];width=m[0x5cbf+pose];
    m[0x100+(unsigned char)(stack-2)]=color;m[0x100+(unsigned char)(stack-3)]=width;
    m[0xe0+actor]=height;m[(secondary?0xd7:0xd4)+actor]=width;
    m[(secondary?0xdd:0xda)+actor]=color;
    source_contact_frame(secondary?0x25d6:0x25ad);
    c=v=0;
    PERF_BEGIN(BL_PERF_SPRITE_COPY);
#if defined(__m68k__)
    SourceSpriteCopy q;
    q.dest=dest;q.first=q.left=q.right=first;q.xx=height;q.yy=(unsigned char)(height*3);
    q.wide=(width!=0);q.carry=0;bl_sprite_copy(m,&q);
    x=q.xx;y=q.yy;c=q.carry;a=0;z=0;n=1;sp+=2;
#else
    z=(width==0);y=(unsigned char)(height*3);source_sprite_copy_c();
#endif
    PERF_END(BL_PERF_SPRITE_COPY);
    actor_return=source_stack_return();
    return 1;
}
