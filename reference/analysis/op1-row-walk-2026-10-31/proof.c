#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>

struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
typedef struct { UWORD lane[3]; UBYTE a,x,y,count; } Batch;
typedef char CheckBatchSize[sizeof(Batch)==10 ? 1 : -1];
extern void bl_contact_rows8(UBYTE *ram, Batch *batch);
static UBYTE memory[65536], expected[65536], record[2048];

static UWORD take_word(const UBYTE **cursor) {
    UWORD value = ((UWORD)(*cursor)[0] << 8) | (*cursor)[1];
    *cursor += 2;
    return value;
}

/* Records are produced from committed deterministic vectors by vectors.py. */
static int patches(const UBYTE **cursor, const UBYTE *end, UBYTE *ram) {
    UWORD count, index;
    if (end-*cursor < 2) return 0;
    count = take_word(cursor);
    if (end-*cursor < 3L*count) return 0;
    for (index=0; index<count; ++index) {
        UWORD address = take_word(cursor);
        ram[address] = *(*cursor)++;
    }
    return 1;
}

static int run_case(UWORD length) {
    Batch actual, target;
    ULONG i;
    const UBYTE *cursor=record+20, *end=record+length;
    if (length<24) return 0;
    for (i=0; i<10; ++i) {
        ((UBYTE *)&actual)[i]=record[i];
        ((UBYTE *)&target)[i]=record[10+i];
    }
    for (i=0; i<65536; ++i) memory[i]=0;
    if (!patches(&cursor,end,memory)) return 0;
    for (i=0; i<65536; ++i) expected[i]=memory[i];
    if (!patches(&cursor,end,expected) || cursor!=end) return 0;
    bl_contact_rows8(memory,&actual);
    for (i=0; i<10; ++i)
        if (((UBYTE *)&actual)[i]!=((UBYTE *)&target)[i]) return 0;
    for (i=0; i<65536; ++i)
        if (memory[i]!=expected[i]) return 0;
    return 1;
}

int main(void) {
    BPTR file,report;
    UWORD cases=0, failures=0, length;
    UBYTE size[2];
    LONG n;
    SysBase=*(struct ExecBase **)4;
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if (!DOSBase) return 20;
    file=Open((CONST_STRPTR)"DH1:vectors.bin",MODE_OLDFILE);
    if (!file) { CloseLibrary((struct Library *)DOSBase); return 20; }
    while ((n=Read(file,size,2))==2) {
        length=((UWORD)size[0]<<8)|size[1];
        if (length>sizeof(record) || Read(file,record,length)!=length) { ++failures; break; }
        if (!run_case(length)) ++failures;
        ++cases;
    }
    if (n || cases!=192) ++failures;
    Close(file);
    report=Open((CONST_STRPTR)"DH1:proof-result.bin",MODE_NEWFILE);
    if (report) {
        Write(report,&cases,2);
        Write(report,&failures,2);
        Close(report);
    }
    CloseLibrary((struct Library *)DOSBase);
    return failures || !report ? 20 : 0;
}
