/* $5380-$53DF pixel lanes, at most eight rows and no source service.
 * Context: three u16 offsets; bytes A,X,Y,count at 6,7,8,9.
 * Caller ensures count<=8, Y+count<=256 and offsets<=0xFF00.
 * Keep each read/flag write ordered, including aliases between lanes. */
    .section .text.parent_rows,"ax"
    .globl parent_rows
parent_rows:
    move.l 4(%sp),%a0
    move.l 8(%sp),%a1
    moveq #0,%d0
    move.b 9(%a1),%d0
    beq 9f
    movem.l %d2-%d3/%d5/%a2-%a6,-(%sp)
    move.l %d0,%d3
    subq.w #1,%d3
    moveq #0,%d2
    move.b 8(%a1),%d2
    moveq #0,%d5
    move.b 7(%a1),%d5
    move.l %a0,%a6
    move.l %a0,%a2
    move.l %a0,%a3
    move.l %a0,%a4
    move.l %a0,%a5
    moveq #0,%d1
    move.w 0(%a1),%d1
    adda.l %d1,%a2
    move.w 2(%a1),%d1
    adda.l %d1,%a3
    move.w 4(%a1),%d1
    adda.l %d1,%a4
    adda.l #0xcae0,%a5
    adda.w #0x4eed,%a0
1:
    moveq #0,%d0
    move.b (%a2,%d2.w),%d0
    and.b (%a5,%d2.w),%d0
    beq.s 2f
    move.b %d0,0x4e(%a6)
    move.l %d0,%d1
    lsr.w #4,%d1
    move.b %d1,(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,(%a0,%d0.w)
    move.b %d0,%d5
2:
    moveq #0,%d0
    move.b (%a3,%d2.w),%d0
    and.b 32(%a5,%d2.w),%d0
    beq.s 3f
    move.b %d0,0x4e(%a6)
    move.l %d0,%d1
    lsr.w #4,%d1
    move.b %d1,23(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,23(%a0,%d0.w)
    move.b %d0,%d5
3:
    moveq #0,%d0
    move.b (%a4,%d2.w),%d0
    and.b 64(%a5,%d2.w),%d0
    beq.s 4f
    move.b %d0,0x4e(%a6)
    move.l %d0,%d1
    lsr.w #4,%d1
    move.b %d1,46(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,46(%a0,%d0.w)
    move.b %d0,%d5
4:
    addq.w #1,%d2
    dbra %d3,1b
    move.b %d0,6(%a1)
    move.b %d5,7(%a1)
    move.b %d2,8(%a1)
    movem.l (%sp)+,%d2-%d3/%d5/%a2-%a6
9:
    rts
