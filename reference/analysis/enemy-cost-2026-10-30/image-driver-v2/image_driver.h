
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

SOURCE_INLINE void image_push_local(unsigned char *s,unsigned short ret){
    m[0x100+(*s)--]=(unsigned char)(ret>>8);m[0x100+(*s)--]=(unsigned char)ret;
}
static unsigned char source_image_driver(void){
    short actor;unsigned char part,pose,sprite,h,color,width,s=sp,yy=y,cc=c,vv=v;
    unsigned short dest,first;SourceSpriteCopy q;
    if(!image_driver_safe())return 0;
    for(actor=2;actor>=0;--actor){
        m[0x51]=(unsigned char)actor;
        if(!(m[0x95+actor]&1))continue;
        for(part=0;part<2;part++){
            if(part && (actor==2 || (m[0x2770+actor]&128)))break;
            sprite=m[(part?0x2770:0x276d)+actor];dest=image_destination(sprite);
            image_push_local(&s,part?0x25bb:0x2593);
            m[0x0e]=(unsigned char)dest;m[0x0f]=(unsigned char)(dest>>8);s+=2;
            pose=(unsigned char)(m[0x4f4e + actor]+part);
            image_push_local(&s,part?0x25c3:0x259a);
            first=(unsigned short)(m[0x59bd+pose]|((unsigned short)m[0x5a8f+pose]<<8));
            m[0x26ab]=(unsigned char)first;m[0x26e4]=(unsigned char)first;m[0x26ee]=(unsigned char)first;
            m[0x26ac]=(unsigned char)(first>>8);m[0x26e5]=(unsigned char)(first>>8);m[0x26ef]=(unsigned char)(first>>8);
            h=m[0x5b61+pose];color=actor==2?0xf0:m[0x5c33+pose];
            m[0x100+s--]=color;width=m[0x5cbf+pose];m[0x100+s--]=width;m[0xe0+actor]=h;
            s+=4; /* Two PLAs followed by the glyph RTS; all stored bytes stay. */
            m[0x100+s--]=color;m[(part?0xd7:0xd4)+actor]=width;++s;
            m[(part?0xdd:0xda)+actor]=color;
            image_push_local(&s,part?0x25d6:0x25ad);
            PERF_BEGIN(BL_PERF_SPRITE_COPY);
#if defined(__m68k__)
            q.dest=dest;q.first=q.left=q.right=first;q.xx=h;q.yy=(unsigned char)(h*3);q.wide=(unsigned char)(width!=0);q.carry=0;
            bl_sprite_copy(m,&q);yy=q.yy;cc=q.carry;s+=2;
#else
            a=width;x=(unsigned char)actor;y=(unsigned char)(h*3);z=(unsigned char)(width==0);c=v=0;sp=s;
            source_sprite_copy_c();yy=y;cc=c;s=sp;
#endif
            PERF_END(BL_PERF_SPRITE_COPY);
            vv=0;if(!part)cc=(unsigned char)(actor>=2);
        }
    }
    a=0;x=255;y=yy;c=cc;v=vv;z=1;n=0;sp=(unsigned char)(s+2);m[0x277e]=0;return 1;
}
