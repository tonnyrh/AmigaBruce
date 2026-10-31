/* Test-only seam. Run the entire real driver. Check all 64 KiB and visible
 * registers at its second service and return, including forced post-service
 * changes. No test API is present in either measured timing binary. */
static unsigned char *wanted_first,*wanted_regs;
static unsigned short inject_at,seen;
static unsigned char inject_value;
static unsigned long witness_errors;
unsigned char *pilot_ram(void){return m;}
static unsigned long pilot_compare(unsigned char *wanted,unsigned char *r){
    unsigned long at;
    if(a!=r[0] || x!=r[1] || y!=r[2] || c!=r[3] || z!=r[4] || n!=r[5] ||
       v!=r[6] || d!=r[7] || sp!=r[8] || actor_i!=r[9])return 1;
    for(at=0;at<65536UL;at++)if(m[at]!=wanted[at])return at+2;
    return 0;
}
static void witness_service(void){
    if(++seen==2){
        witness_errors=pilot_compare(wanted_first,wanted_regs);
        if(inject_value)m[inject_at]^=inject_value;
    }
}
unsigned long pilot_witness(unsigned char *r,unsigned char *first,unsigned char *last){
    unsigned long error;
#ifdef KAGE_COUNTS
    unsigned long before[3],i;
#endif
    a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];actor_i=r[9];
    if(d)return 0x40000UL;
    wanted_first=first;wanted_regs=r+10;inject_at=(unsigned short)(((unsigned short)r[30]<<8)|r[31]);inject_value=r[32];
#ifdef KAGE_COUNTS
    for(i=0;i<3;i++)before[i]=kage_counts[i];
#endif
    witness_errors=0;seen=0;actor_world_enabled=1;io_service=witness_service;
    source_contact_driver();
    if(witness_errors)return witness_errors;
    error=pilot_compare(last,r+20);if(error)return 0x10000UL+error;
    if(seen!=r[34])return 0x30004UL;
#ifdef KAGE_COUNTS
    for(i=0;i<3;i++)if(kage_counts[i]-before[i]!=(unsigned long)(r[33]==i))return 0x30000UL+i;
#endif
    return 0;
}
