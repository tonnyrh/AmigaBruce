/* At $2E7B the next three object cells are read from the decoded screen.
 * Short-circuit only when all three branches in $2E89..$2EE9 are RTS.
 * The narrow screen window excludes zero page, stack and I/O aliases. */
static unsigned char source_neutral_row(void){
    static const unsigned char handler[128]={
        [2]=1,[3]=1,[4]=1,[5]=1,[0x2d]=1,[0x2e]=1,[0x62]=1,
        [0x0f]=2,[0x13]=2,[0x14]=2,[0x31]=2,[0x40]=2,[0x54]=2,[0x55]=2,[0x56]=2,
        [0x58]=2,[0x59]=2,[0x5a]=2,[0x60]=2,[0x64]=2,[0x66]=2,
        [0x71]=2,[0x72]=2,[0x73]=2,[0x74]=2,[0x75]=2,[0x76]=2,
        [0x77]=2,[0x78]=2,[0x79]=2,[0x7a]=2,[0x7b]=2,[0x7c]=2
    };
    unsigned short at=(unsigned short)(W(4)+y),j;
    unsigned char flag=m[0x53],old=0,code=0;
    if(at<0x8c00 || at>0x8fe5 || y>253)return 0;
    for(j=0;j<3;j++){
        unsigned char action;
        code=m[at+j]&127;action=handler[code];
        old=flag;flag=(unsigned char)(flag<<1);
        if(action==1 || (action==2 && flag))return 0;
    }
    source_contact_frame(0x2e82);sp+=2;
    m[0x53]=flag;m[0x4c]=255;y+=3;a=code;
    c=flag?(code>=0x60):(old>>7);n=1;z=0;
    sp+=2;actor_return=source_stack_return();return 1;
}
