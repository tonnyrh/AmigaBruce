/* $52AD-$5309 mask preparation; four independent bitmap rows per long.
 * ABI: ram, pointer, phase, offset are four 32-bit stack arguments.
 * Precondition phase<=3, offset<=7, pointer<=0xFFA0; source span cannot wrap.
 * Copy stays byte-forward for odd addresses or unsafe forward overlap.
 * Return D0 = original carry; C publishes remaining source registers.
 * D2-D7/A2-A4 preserved; D0-D1/A0-A1 are caller scratch. */
    .section .text.bl_contact_align4,"ax"
    .globl bl_contact_align4
bl_contact_align4:
    movem.l %d2-%d7/%a2-%a4,-(%sp)
    move.l 40(%sp),%a0
    move.l 44(%sp),%d2
    move.l 48(%sp),%d3
    move.l 52(%sp),%d4
    move.l %a0,%a2
    adda.l %d2,%a2
    adda.l #0xcae0,%a0
    move.l %a0,%a1
    move.w %d4,%d0
    beq.s 2f
    subq.w #1,%d0
1:
    clr.b (%a1)+
    dbra %d0,1b
2:
    cmpi.w #3,%d3
    bne.s 4f
    btst #0,%d4
    bne.s 20f
    .rept 8
    clr.l (%a1)+
    .endr
    bra.s 4f
20:
    moveq #31,%d0
21:
    clr.b (%a1)+
    dbra %d0,21b
4:
    /* Long copy only if both addresses are even and byte-forward
     * dependency cannot exist. Reads occur after all prefix zeroing. */
    move.l %a1,%d0
    or.l %d2,%d0
    btst #0,%d0
    bne 7f
    cmpa.l %a1,%a2
    bcc.s 5f
    move.l %a2,%a4
    adda.w #96,%a4
    cmpa.l %a4,%a1
    bcs 7f
5:
    .rept 24
    move.l (%a2)+,(%a1)+
    .endr
    bra.s 9f
7:
    moveq #95,%d0
8:
    move.b (%a2)+,(%a1)+
    dbra %d0,8b
9:
    moveq #1,%d7
    tst.w %d3
    beq 19f
    lea 28(%a0),%a3
    cmpi.w #3,%d3
    beq 14f
    add.w %d3,%d3
    moveq #8,%d1
    sub.w %d3,%d1
    moveq #0,%d7
    move.b 64(%a0),%d7
    move.w %d3,%d0
    subq.w #1,%d0
    lsr.l %d0,%d7
    andi.w #1,%d7
    move.l #0x3f3f3f3f,%d6
    cmpi.w #2,%d3
    beq 10f
    move.l #0x0f0f0f0f,%d6
10:
    .rept 8
    move.l (%a3),%d2
    move.l 32(%a3),%d4
    move.l 64(%a3),%d5
    lsr.l %d3,%d5
    and.l %d6,%d5
    move.l %d4,%d0
    lsl.l %d1,%d0
    not.l %d6
    and.l %d6,%d0
    not.l %d6
    or.l %d0,%d5
    move.l %d5,64(%a3)
    lsr.l %d3,%d4
    and.l %d6,%d4
    move.l %d2,%d0
    lsl.l %d1,%d0
    not.l %d6
    and.l %d6,%d0
    not.l %d6
    or.l %d0,%d4
    move.l %d4,32(%a3)
    lsr.l %d3,%d2
    and.l %d6,%d2
    move.l %d2,(%a3)
    subq.l #4,%a3
    .endr
    bra 19f
14:
    moveq #0,%d7
    move.b (%a0),%d7
    lsr.w #6,%d7
    andi.w #1,%d7
    move.l #0xfcfcfcfc,%d3
    move.l #0x03030303,%d6
    .rept 8
    move.l (%a3),%d2
    move.l 32(%a3),%d4
    move.l 64(%a3),%d5
    move.l 96(%a3),%d1
    lsl.l #2,%d2
    and.l %d3,%d2
    move.l %d4,%d0
    lsr.l #6,%d0
    and.l %d6,%d0
    or.l %d0,%d2
    move.l %d2,(%a3)
    lsl.l #2,%d4
    and.l %d3,%d4
    move.l %d5,%d0
    lsr.l #6,%d0
    and.l %d6,%d0
    or.l %d0,%d4
    move.l %d4,32(%a3)
    lsl.l #2,%d5
    and.l %d3,%d5
    move.l %d1,%d0
    lsr.l #6,%d0
    and.l %d6,%d0
    or.l %d0,%d5
    move.l %d5,64(%a3)
    lsl.l #2,%d1
    and.l %d3,%d1
    move.l %d1,96(%a3)
    subq.l #4,%a3
    .endr
19:
    move.l %d7,%d0
    movem.l (%sp)+,%d2-%d7/%a2-%a4
    rts
