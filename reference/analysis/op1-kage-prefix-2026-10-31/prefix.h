/* Candidate only. Binary $5214 to the first $5380 service with Y=0.
 * The following row code always samples current glyph pixels. */
typedef struct {
    unsigned short pointer,screen,attributes;
    unsigned char source[96],aligned[136];
    unsigned char valid,room,px,py,pose,charset,row,col;
    unsigned char tile[3],attribute[3],flags[3],operands[6];
    unsigned char scratch[2],aa,carry,overflow;
} KagePrefix;
static KagePrefix kage_prefix;
#ifdef KAGE_COUNTS
unsigned long kage_counts[3];
#define KAGE_COUNT(slot) (++kage_counts[slot])
#else
#define KAGE_COUNT(slot) ((void)0)
#endif

static void first_part(unsigned char actor){
    unsigned char pose;
/* ORIGINAL_PREFIX */
    m[0x4f3a]=8;source_contact_frame(0x5273);source_contact_pointers();
}
static unsigned char prefix_equal96(const unsigned char *p,const unsigned char *q){
#if defined(__m68k__)
    unsigned long equal;
    __asm__ volatile("moveq #0,%0\n\t.rept 24\n\tcmpm.l (%1)+,(%2)+\n\tbne.s 1f\n\t.endr\n\tmoveq #1,%0\n1:"
        :"=&d"(equal),"+a"(p),"+a"(q)::"cc","memory");
    return (unsigned char)equal;
#else
    unsigned short i;for(i=0;i<96;i++)if(p[i]!=q[i])return 0;return 1;
#endif
}
static void prefix_copy(unsigned char *dst,const unsigned char *src,unsigned char phase,unsigned char tail){
#if defined(__m68k__)
    __asm__ volatile(".rept 24\n\tmove.l (%1)+,(%0)+\n\t.endr":"+a"(dst),"+a"(src)::"cc","memory");
    if(phase==3)
        __asm__ volatile(".rept 8\n\tmove.l (%1)+,(%0)+\n\t.endr":"+a"(dst),"+a"(src)::"cc","memory");
#else
    unsigned short i,count=phase==3?128:96;
    for(i=0;i<count;i++)*dst++=*src++;
#endif
    while(tail--)*dst++=*src++;
}
static unsigned short prefix_screen(unsigned char row){
    return (unsigned short)(m[0x50e7+row]|((unsigned short)m[0x50ff+row]<<8));
}
static unsigned short prefix_attributes(unsigned char row){
    return (unsigned short)(m[0x50e7+row]|((unsigned short)m[0x5117+row]<<8));
}
static unsigned short prefix_pose(unsigned char pose){
    return (unsigned short)(m[0x1167+pose]|((unsigned short)m[0x1239+pose]<<8));
}
static unsigned char prefix_matches(const KagePrefix *q){
    unsigned char i;
    if(!q->valid || q->px!=m[0xa0] || q->py!=m[0xa3] || q->pose!=m[0x4f50] ||
       q->room!=m[0x29] || q->charset!=m[0x7c] || q->pointer!=prefix_pose(q->pose) ||
       q->screen!=prefix_screen(q->row) || q->attributes!=prefix_attributes(q->row))return 0;
    for(i=0;i<3;i++)
        if(m[q->screen+q->col+i]!=q->tile[i] || m[q->attributes+q->col+i]!=q->attribute[i])return 0;
    return prefix_equal96(q->source,m+q->pointer);
}
static void prefix_fill(KagePrefix *q){
    unsigned short pointer=W(0x52cc),screen=W(4),attr=W(0x12);
    unsigned char i,row=m[0xeb],col=m[0xe8];
    q->valid=0;
    /* Restrict to three in-range cells, ordinary disjoint map/color RAM
     * and aligned source bytes disjoint from every prefix destination. */
    if(row>=24 || col>37 || screen<0x8000 || screen>0x9fd8 || attr<0xd800 || attr>0xdbd8 ||
       pointer<0x6000 || pointer>0xca80 || (pointer&1)){KAGE_COUNT(2);return;}
    q->pointer=pointer;q->screen=screen;q->attributes=attr;q->row=row;q->col=col;
    q->px=m[0xa0];q->py=m[0xa3];q->pose=m[0x4f50];q->room=m[0x29];q->charset=m[0x7c];
    for(i=0;i<3;i++){
        q->tile[i]=m[screen+col+i];q->attribute[i]=m[attr+col+i];q->flags[i]=m[0x4f32+i];
    }
    q->operands[0]=m[0x5381];q->operands[1]=m[0x5382];q->operands[2]=m[0x539b];q->operands[3]=m[0x539c];
    q->operands[4]=m[0x53b5];q->operands[5]=m[0x53b6];
    q->scratch[0]=m[0x43bb];q->scratch[1]=m[0x43bc];q->aa=a;q->carry=c;q->overflow=v;
    prefix_copy(q->source,m+pointer,0,0);prefix_copy(q->aligned,m+0xcae0,m[0x1b],m[0x1c]);
    q->valid=1;KAGE_COUNT(1);
}
static void kage_first_part(void){
    KagePrefix *q=&kage_prefix;
    unsigned char phase,offset;
    if(!prefix_matches(q)){first_part(2);prefix_fill(q);return;}
    KAGE_COUNT(0);
    phase=(unsigned char)((q->px-12)&3);offset=(unsigned char)((q->py-29)&7);
    m[0xe8]=q->col;m[0xeb]=q->row;m[0x1b]=phase;m[0x1c]=offset;
    m[0x52cc]=(unsigned char)q->pointer;m[0x52cd]=(unsigned char)(q->pointer>>8);
    prefix_copy(m+0xcae0,q->aligned,phase,offset);
    m[0x4f38]=(unsigned char)(offset+15);m[0x4f39]=(unsigned char)(offset+21);m[0x4f3a]=8;m[0x52]=0;
    source_contact_frame(0x5258);source_contact_clear();
    m[0x4f32]=q->flags[0];m[0x4f33]=q->flags[1];m[0x4f34]=q->flags[2];
    m[4]=m[0x12]=(unsigned char)q->screen;m[5]=(unsigned char)(q->screen>>8);m[0x13]=(unsigned char)(q->attributes>>8);
    m[0x43bb]=q->scratch[0];m[0x43bc]=q->scratch[1];
    m[0x5381]=q->operands[0];m[0x5382]=q->operands[1];m[0x539b]=q->operands[2];m[0x539c]=q->operands[3];
    m[0x53b5]=q->operands[4];m[0x53b6]=q->operands[5];
    source_contact_frame(0x5273);source_contact_frame(0x5368);sp+=4;
    a=q->aa;x=2;y=(unsigned char)(q->col+2);c=q->carry;v=q->overflow;NZ(a);
}
