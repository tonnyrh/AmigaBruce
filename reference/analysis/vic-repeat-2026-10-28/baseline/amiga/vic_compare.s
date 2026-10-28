    .section .text.bl_vic_equal63,"ax"
    .globl bl_vic_equal63
bl_vic_equal63:
    move.l 4(%sp),%a0
    move.l 8(%sp),%a1
    moveq #14,%d0
1:
    cmpm.l (%a0)+,(%a1)+
    bne.s 2f
    dbra %d0,1b
    cmpm.b (%a0)+,(%a1)+
    bne.s 2f
    cmpm.b (%a0)+,(%a1)+
    bne.s 2f
    cmpm.b (%a0)+,(%a1)+
    bne.s 2f
    moveq #1,%d0
    rts
2:
    moveq #0,%d0
    rts
