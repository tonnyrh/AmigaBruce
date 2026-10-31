"""Keep source-visible writes, hold dead intermediate CPU values locally."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
BODY=r'''
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
'''
def main():
    folder=BASE/'image-driver-v2';folder.mkdir(exist_ok=True)
    old=BASE/'image-driver'
    helper=(old/'image_driver.h').read_text(encoding='utf-8-sig').split('static void image_pointer(')[0]+BODY
    for name in ['c64_rooms.c','c64_actor_programs.h']:(folder/name).write_bytes((old/name).read_bytes())
    (folder/'image_driver.h').write_text(helper,encoding='utf-8')
    bridge=(BASE/'image-driver-bridge.c').read_text().replace('image-driver/c64_rooms.c','image-driver-v2/c64_rooms.c')
    (BASE/'image-driver-v2-bridge.c').write_text(bridge,encoding='utf-8')
    builder=(BASE/'image-driver-build.ps1').read_text().replace('/image-driver/c64_rooms.c','/image-driver-v2/c64_rooms.c')
    (BASE/'image-driver-v2-build.ps1').write_text(builder,encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'image-driver-v2-scope.json').write_text(json.dumps(dict(production_changed=False,method='Source-visible stores and same copy primitive; source CPU intermediate values are local until exit. No I/O observers inside original image driver.',inputs=[item(old/'image_driver.h'),item(ROOT/'core/c64_actor_programs.h')],generated=[item(p) for p in list(folder.iterdir())+[BASE/'image-driver-v2-bridge.c',BASE/'image-driver-v2-build.ps1']]),indent=2)+'\n')
    print('Generated private local-register image driver')
if __name__=='__main__':main()
