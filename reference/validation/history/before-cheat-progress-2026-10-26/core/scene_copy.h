#ifndef BRUCE_SCENE_COPY_H
#define BRUCE_SCENE_COPY_H
/* Presentation work only. Coordinates, source RAM and contacts are untouched.
 * A rotating scan prevents continuously animated upper rows from indefinitely
 * postponing lower rows when the bitmap-copy budget is exhausted. */
typedef struct {
    unsigned long words;
    unsigned short first,last;
    unsigned char rows;
} BlSceneSlice;
static unsigned char bl_scene_take(unsigned long *words,unsigned char *rows,
    unsigned char *cursor,unsigned short *budget,BlSceneSlice *slice){
    unsigned short row=*cursor,visited,last,cost,word_count=0,scan_count=0;
    unsigned long value;unsigned char mask;
    if(row<3 || row>24)row=3;
    for(visited=0;visited<22;visited++){
        if(rows[row] && words[row])break;
        row=(unsigned short)(row==24?3:row+1);
    }
    if(visited==22)return 0;
    value=words[row];mask=rows[row];
    while(value){++word_count;value&=value-1;}
    while(mask){++scan_count;mask&=(unsigned char)(mask-1);}
    cost=(unsigned short)(word_count*scan_count*8);
    *cursor=(unsigned char)row;
    if(cost>*budget)return 0;
    last=row;
    if(rows[row]==255)while(last<24 && rows[last+1]==255 && words[last+1]==words[row] &&
        (unsigned long)cost*(last-row+2)<=*budget)++last;
    *budget=(unsigned short)(*budget-cost*(last-row+1));
    slice->first=row;slice->last=last;slice->words=words[row];slice->rows=rows[row];
    do{words[row]=0;rows[row]=0;}while(row++<last);
    *cursor=(unsigned char)(last==24?3:last+1);return 1;
}
#endif
