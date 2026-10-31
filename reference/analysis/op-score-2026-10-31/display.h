/* $315D-$3172 calls $1B17 twice and tail-jumps there for the last pair.
 * Keep the PHA and nested JSR bytes on the wrapping 6502 stack page.
 * $8C30-$8C35 are HUD RAM, below the first indexed playfield cell $8C78. */
static void source_score_display(void){
    unsigned char pair,part,frame;
    for(part=0;part<3;part++){
        frame=sp;
        if(part<2){
            m[0x100+frame--]=0x31;
            m[0x100+frame--]=part?0x6c:0x64;
        }
        y=(unsigned char)(0x30+part*2);
        pair=m[0x439c+part];
        m[0x100+frame--]=pair;
        m[0x100+frame--]=0x1b;
        m[0x100+frame]=0x1a;
        m[0x8c00+y]=(unsigned char)(0x10|(pair>>4));
        a=(unsigned char)(0x10|(pair&15));
        m[0x8c01+y]=a;
    }
    c=(pair>>3)&1; /* Carry after the fourth LSR at $3211. */
    z=n=0;
}
