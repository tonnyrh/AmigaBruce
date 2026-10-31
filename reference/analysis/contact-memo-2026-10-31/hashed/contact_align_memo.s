/* Private exact-result cache for $52AD-$5309. Caller requires phase1..3,
 * offset0..7, even nonwrapping source and no source/output overlap.
 * ABI: ram,pointer,phase,offset,240-byte cache; all args32bit.
 * Cache: valid,phase,offset,carry, u16 pointer,pad;96 input;136 output.
 * Compare every input byte on a hit. Replay only96+offset+(phase3?32:0)
 * output bytes; no service exists inside the replaced original routine. */
    .section .text.bl_contact_align_memo,"ax"
    .globl bl_contact_align_memo
bl_contact_align_memo:
    movem.l %d2-%d7/%a2-%a5,-(%sp)
    move.l 44(%sp),%a2
    move.l 48(%sp),%d2
    move.l 52(%sp),%d3
    move.l 56(%sp),%d4
    move.l 60(%sp),%a3
    move.l %a2,%a4
    adda.l %d2,%a4
    move.l %a2,%a5
    adda.l #0xcae0,%a5
    moveq #96,%d5
    add.w %d4,%d5
    cmpi.w #3,%d3
    bne.s 1f
    addi.w #32,%d5
1:
    tst.b (%a3)
    beq .Lmemo_miss
    cmp.b 1(%a3),%d3
    bne .Lmemo_miss
    cmp.b 2(%a3),%d4
    bne .Lmemo_miss
    cmp.w 4(%a3),%d2
    bne .Lmemo_miss
    move.l %a4,%a0
    lea 8(%a3),%a1
    .rept 24
    cmpm.l (%a0)+,(%a1)+
    bne .Lmemo_miss
    .endr
    lea 104(%a3),%a0
    move.l %a5,%a1
    move.w %d5,%d7
    lsr.w #2,%d7
    subq.w #1,%d7
2:
    move.l (%a0)+,(%a1)+
    dbra %d7,2b
    move.w %d5,%d7
    andi.w #3,%d7
    beq.s 4f
    subq.w #1,%d7
3:
    move.b (%a0)+,(%a1)+
    dbra %d7,3b
4:
    moveq #0,%d0
    move.b 3(%a3),%d0
    bra .Lmemo_return
.Lmemo_miss:
    move.l %d4,-(%sp)
    move.l %d3,-(%sp)
    move.l %d2,-(%sp)
    move.l %a2,-(%sp)
    jsr bl_contact_align4
    lea 16(%sp),%sp
    move.l %d0,%d6
    move.b %d3,1(%a3)
    move.b %d4,2(%a3)
    move.b %d6,3(%a3)
    move.w %d2,4(%a3)
    move.l %a4,%a0
    lea 8(%a3),%a1
    .rept 24
    move.l (%a0)+,(%a1)+
    .endr
    move.l %a5,%a0
    lea 104(%a3),%a1
    move.w %d5,%d7
    lsr.w #2,%d7
    subq.w #1,%d7
5:
    move.l (%a0)+,(%a1)+
    dbra %d7,5b
    move.w %d5,%d7
    andi.w #3,%d7
    beq.s 7f
    subq.w #1,%d7
6:
    move.b (%a0)+,(%a1)+
    dbra %d7,6b
7:
    move.b #1,(%a3)
    move.l %d6,%d0
.Lmemo_return:
    movem.l (%sp)+,%d2-%d7/%a2-%a5
    rts
