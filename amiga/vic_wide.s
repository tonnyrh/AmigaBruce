/* 21 rows of three source bytes. $D01D expands every source bit into two
 * output bits. Each Amiga high/low pair is a big-endian 48-bit row and 16
 * trailing clear bits. The raw cache keeps exactly the 63 source bytes. */
    .section .text.bl_vic_decode_wide,"ax"
    .globl bl_vic_decode_wide
bl_vic_decode_wide:
    movem.l %a2-%a4,-(%sp)
    movea.l 16(%sp),%a0
    movea.l 20(%sp),%a1
    movea.l 24(%sp),%a2
    movea.l 28(%sp),%a3
    lea .Lwide_words(%pc),%a4
    moveq #20,%d1
.Lwide_row:
    .rept 2
    moveq #0,%d0
    move.b (%a0)+,%d0
    move.b %d0,(%a1)+
    add.w %d0,%d0
    move.w (%a4,%d0.w),(%a2)+
    .endr
    moveq #0,%d0
    move.b (%a0)+,%d0
    move.b %d0,(%a1)+
    add.w %d0,%d0
    move.w (%a4,%d0.w),(%a3)+
    clr.w (%a3)+
    dbra %d1,.Lwide_row
    movem.l (%sp)+,%a2-%a4
    rts

    /* Input bit j sets output bits 2*j and 2*j+1. */
.Lwide_words:
    .set byte_no,0
    .rept 256
    .word ((byte_no&1)*3)+((byte_no&2)*6)+((byte_no&4)*12)+((byte_no&8)*24)+((byte_no&16)*48)+((byte_no&32)*96)+((byte_no&64)*192)+((byte_no&128)*384)
    .set byte_no,byte_no+1
    .endr
