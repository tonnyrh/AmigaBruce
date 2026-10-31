/* Candidate only: frozen $169D-$1702 with fixed CIA pin reads.
 * Native registers/RAM retain the source instruction effects, including
 * PHA/PHP writes. No physical sampling policy or full IRQ claim here. */
static unsigned char input_slot_pin(unsigned short address,
        unsigned char port0,unsigned char port1){
    return address==0xdc00?port0:address==0xdc01?port1:m[address];
}
static void input_slot_convert(void){
    m[0x100+sp--]=a;
    a&=3;y=a;
    a=m[0x100+(unsigned char)++sp];
    c=(unsigned char)((a>>1)&1);
    a=(unsigned char)((a>>2)|m[0x4a85+y]);NZ(a);
}
static void input_slot_candidate(unsigned char port0,unsigned char port1){
    unsigned char flags;
    a=m[0x104];NZ(a);if(z)return;
    a=port1;x=m[3];NZ(x);if(!z)a=port0;
    a&=15;NZ(a);y=m[0x1383+x];NZ(y);
    if(z)input_slot_convert();
    m[0x98]=a;
    a=(unsigned char)(m[3]^1);x=a;NZ(x);
    a=input_slot_pin((unsigned short)(0xdc00+x),port0,port1);
    c=(unsigned char)((a>>3)&1);a=(unsigned char)((a>>4)&1);NZ(a);
    m[0x9b]=a;
    a=m[0x42ca];NZ(a);if(z)return;
    a=(unsigned char)(m[3]^1);x=a;NZ(x);
    m[0x100+sp--]=(unsigned char)(0x30|c|(z<<1)|(actor_i<<2)|(d<<3)|(v<<6)|(n<<7));
    a=port1;NZ(a);
    flags=m[0x100+(unsigned char)++sp];
    c=flags&1;z=(flags>>1)&1;actor_i=(flags>>2)&1;d=(flags>>3)&1;v=(flags>>6)&1;n=flags>>7;
    if(!z)a=port0;
    a&=15;NZ(a);y=m[0x1383+x];NZ(y);
    if(z)input_slot_convert();
    m[0x99]=a;
    x=m[3];NZ(x);
    a=input_slot_pin((unsigned short)(0xdc00+x),port0,port1);
    c=(unsigned char)((a>>3)&1);a=(unsigned char)((a>>4)&1);NZ(a);
    m[0x9c]=a;
}
