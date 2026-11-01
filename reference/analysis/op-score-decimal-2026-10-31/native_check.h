
unsigned long check_decimal(const unsigned char *record){
    unsigned short i;
    const unsigned char *r=record+3,*end=record+21;
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    for(i=0;i<256;i++)m[0x100+i]=(unsigned char)(i^0xa5);
    m[0x4397]=0x5a;m[0x439f]=0xa5;
    for(i=0;i<7;i++)m[0x4398+i]=i<3?record[i]:0;
    source_score_decimal();
    if(a!=end[0] || x!=end[1] || y!=end[2] || c!=end[3] || z!=end[4] ||
       n!=end[5] || v!=end[6] || d!=end[7] || sp!=end[8] || actor_i!=end[9])return 1;
    for(i=0;i<7;i++)if(m[0x4398+i]!=record[13+i])return 2;
    if(m[0x4397]!=0x5a || m[0x439f]!=0xa5)return 3;
    for(i=0;i<256;i++)if(m[0x100+i]!=(i==sp?record[20]:(unsigned char)(i^0xa5)))return 4;
    return 0;
}
