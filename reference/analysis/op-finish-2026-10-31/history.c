/* $1C79..$1C8D, binary addition and one of the three source actors.
 * Four history slots per step, actors interleaved at a three-byte stride. */
static void source_shift_history(void){
    unsigned char *base=m+0x4f57+x;
    unsigned short end=120;
    do{
        end-=12;
        base[end+21]=base[end+9];
        base[end+18]=base[end+6];
        base[end+15]=base[end+3];
        base[end+12]=base[end];
    }while(end);
    a=base[0];y=(unsigned char)(x-3);m[0x4e]=255;
    c=0;v=0;z=0;n=1;
}
