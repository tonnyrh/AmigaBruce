/* Minimal freestanding C support, authored for this project. CLI startup. */
void *memset(void *dst, int value, unsigned long count) {
    unsigned char *d=dst;
    while(count--) *d++=(unsigned char)value;
    return dst;
}
void *memcpy(void *dst, const void *src, unsigned long count) {
    unsigned char *d=dst; const unsigned char *s=src;
    while(count--) *d++=*s++;
    return dst;
}

unsigned long __mulsi3(unsigned long a,unsigned long b) {
#if defined(__m68k__)
    unsigned long low=a&65535UL,ah=a>>16,bh=b>>16,cross=0;
    unsigned short al=(unsigned short)a,bl=(unsigned short)b;
    __asm__ volatile("mulu.w %1,%0" : "+d"(low) : "d"(bl) : "cc");
    if(ah){__asm__ volatile("mulu.w %1,%0" : "+d"(ah) : "d"(bl) : "cc");cross=ah;}
    if(bh){__asm__ volatile("mulu.w %1,%0" : "+d"(bh) : "d"(al) : "cc");cross+=bh;}
    return low+(cross<<16);
#else
    unsigned long result=0;
    while(b){if(b&1)result+=a;a<<=1;b>>=1;}
    return result;
#endif
}
static unsigned long divide(unsigned long a,unsigned long b,unsigned long *remainder) {
    unsigned long q=0,bit=1;
    if(!b){*remainder=a;return 0;}
#if defined(__m68k__)
    if(b<=65535UL){
        unsigned short divisor=(unsigned short)b;unsigned long packed=a;
        if((a>>16)<b){
            __asm__ volatile("divu.w %1,%0" : "+d"(packed) : "d"(divisor) : "cc");
            *remainder=packed>>16;return packed&65535UL;
        }else{
            unsigned long upper=a>>16,high;
            __asm__ volatile("divu.w %1,%0" : "+d"(upper) : "d"(divisor) : "cc");
            high=upper<<16;packed=(upper&0xffff0000UL)|(a&65535UL);
            __asm__ volatile("divu.w %1,%0" : "+d"(packed) : "d"(divisor) : "cc");
            *remainder=packed>>16;return high|(packed&65535UL);
        }
    }
#endif
    while(b<a && !(b&0x80000000UL)){b<<=1;bit<<=1;}
    while(bit){if(a>=b){a-=b;q|=bit;}b>>=1;bit>>=1;}
    *remainder=a;return q;
}
unsigned long __udivsi3(unsigned long a,unsigned long b){unsigned long r;return divide(a,b,&r);}
unsigned long __umodsi3(unsigned long a,unsigned long b){unsigned long r;divide(a,b,&r);return r;}
long __divsi3(long a,long b){
    unsigned long r,q=divide(a<0?0UL-(unsigned long)a:(unsigned long)a,
        b<0?0UL-(unsigned long)b:(unsigned long)b,&r);
    return (a<0)!=(b<0)?(long)(0UL-q):(long)q;
}
long __modsi3(long a,long b){
    unsigned long r;divide(a<0?0UL-(unsigned long)a:(unsigned long)a,
        b<0?0UL-(unsigned long)b:(unsigned long)b,&r);
    return a<0?(long)(0UL-r):(long)r;
}

/* Check hardware arithmetic against independent bit-serial references. */
unsigned long bruce_runtime_check(void){
    static const unsigned long values[]={0,1,2,3,19,255,256,65535,65536,65537,
        0x7fffffffUL,0x80000000UL,0xfffffffeUL,0xffffffffUL,0x12345678UL,0xfedcba98UL};
    unsigned long errors=0,i,j;
    for(i=0;i<16;i++)for(j=0;j<16;j++){
        unsigned long a=values[i],b=values[j],left=a,right=b,product=0,q=0,r=a,bit=1,divisor=b;
        long sa=(long)a,sb=(long)b;unsigned long abs_a=sa<0?0UL-a:a,abs_b=sb<0?0UL-b:b,sq=0,sr=abs_a;
        while(right){if(right&1)product+=left;left<<=1;right>>=1;}
        if(__mulsi3(a,b)!=product)++errors;
        if(divisor){while(divisor<r && !(divisor&0x80000000UL)){divisor<<=1;bit<<=1;}
            while(bit){if(r>=divisor){r-=divisor;q|=bit;}divisor>>=1;bit>>=1;}}
        if(__udivsi3(a,b)!=q || __umodsi3(a,b)!=r)++errors;
        divisor=abs_b;bit=1;
        if(divisor){while(divisor<sr && !(divisor&0x80000000UL)){divisor<<=1;bit<<=1;}
            while(bit){if(sr>=divisor){sr-=divisor;sq|=bit;}divisor>>=1;bit>>=1;}}
        if((unsigned long)__divsi3(sa,sb)!=((sa<0)!=(sb<0)?0UL-sq:sq) ||
           (unsigned long)__modsi3(sa,sb)!=(sa<0?0UL-sr:sr))++errors;
    }
    return errors;
}
