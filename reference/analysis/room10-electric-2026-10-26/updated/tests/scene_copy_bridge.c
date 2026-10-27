#include "../core/scene_copy.h"
typedef unsigned char UBYTE;
typedef unsigned short UWORD;
typedef unsigned long ULONG;
typedef struct {short left,top,right,bottom;} BlDirty;
#define SCENE_TOP 32
static ULONG source_words[2][25],urgent_words[25];
static UBYTE source_rows[2][25],urgent_rows[25];
static unsigned long copied[25],step_number,copy_bytes,max_bytes;
static void restore_actor(UBYTE *unused,const BlDirty *strip){
    int row;(void)unused;
    for(row=(strip->top-SCENE_TOP)/8;row<=(strip->bottom-SCENE_TOP-1)/8;row++)copied[row]=step_number+1;
    copy_bytes+=(strip->right-strip->left)/16*(strip->bottom-strip->top)*8;
}
#include "scene_copy_legacy.h"
static unsigned long values[4];
void bl_copy_run(long legacy,long urgent,long steps){
    unsigned short i,row,age[25],max_age=0;unsigned char cursor=3,urgent_cursor=3;
    for(row=0;row<25;row++){source_words[0][row]=0;source_rows[0][row]=0;urgent_rows[row]=0;urgent_words[row]=0;copied[row]=age[row]=0;}
    max_bytes=0;
    for(step_number=0;step_number<(unsigned long)steps;step_number++){
        unsigned short budget=5000;BlSceneSlice slice;
        for(row=3;row<25;row++){source_words[0][row]|=0xfffffUL;source_rows[0][row]=255;}
        if(urgent){urgent_words[23]=1UL<<8;urgent_rows[23]=255;}
        copy_bytes=0;
        if(legacy)legacy_restore_source_cells(0,0);
        else{
            if(urgent)while(bl_scene_take(urgent_words,urgent_rows,&urgent_cursor,&budget,&slice))
                for(i=slice.first;i<=slice.last;i++)copied[i]=step_number+1;
            while(bl_scene_take(source_words[0],source_rows[0],&cursor,&budget,&slice))
                for(i=slice.first;i<=slice.last;i++)copied[i]=step_number+1;
            copy_bytes=5000-budget;
        }
        if(copy_bytes>max_bytes)max_bytes=copy_bytes;
        for(row=3;row<25;row++){
            age[row]=copied[row]==step_number+1?0:age[row]+1;
            if(age[row]>max_age)max_age=age[row];
        }
    }
    values[0]=max_age;values[1]=max_bytes;values[2]=copied[23];values[3]=copied[24];
}
unsigned long bl_copy_read(long field){return values[field&3];}
