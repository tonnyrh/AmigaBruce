/* Frozen $26A0-$2702, sprite image expansion.
 * ABI: RAM,12-byte context (u16 dest/first/left/right; u8 X/Y/wide/C).
 * X input is the already read source height; output is final virtual X.
 * Bases<=FF00, destination>=8000. Wide Y=3*height, height<32. Byte reads/writes
 * remain ordered, including overlapping glyphs and count-scratch reads. */
    .section .text.bl_sprite_copy,"ax"
    .globl bl_sprite_copy
bl_sprite_copy:
    movem.l %d2-%d5/%a2-%a6,-(%sp)
    move.l 40(%sp),%a6
    move.l 44(%sp),%a4
    moveq #0,%d0
    move.w 0(%a4),%d0
    move.l %a6,%a0
    adda.l %d0,%a0
    move.w 2(%a4),%d0
    move.l %a6,%a1
    adda.l %d0,%a1
    move.w 4(%a4),%d0
    move.l %a6,%a2
    adda.l %d0,%a2
    move.w 6(%a4),%d0
    move.l %a6,%a3
    adda.l %d0,%a3
    lea 0x277f(%a6),%a5
    moveq #0,%d2
    move.b 8(%a4),%d2
    moveq #0,%d3
    move.b 9(%a4),%d3

    /* The conservative source window excludes code operands, count scratch,
     * destination, wraparound and mapped I/O. All other cases keep ordering. */
    move.w 0(%a4),%d0
    btst #0,%d0
    bne .Lsprite_ordered
    cmpi.w #0xcf00,%d0
    blo.s .Lfast_dest_ok
    cmpi.w #0xe000,%d0
    blo .Lsprite_ordered
.Lfast_dest_ok:
    move.w 2(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w 4(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w 6(%a4),%d0
    cmpi.w #0x3000,%d0
    blo .Lsprite_ordered
    cmpi.w #0x7f00,%d0
    bhi .Lsprite_ordered
    move.w %d2,%d0
    add.w %d0,%d0
    add.w %d2,%d0
    cmp.w %d3,%d0
    bne .Lsprite_ordered
    tst.b 10(%a4)
    bne.s .Lfast_wide_guard
    cmpi.w #20,%d2
    bhi .Lsprite_ordered
    bra.s .Lfast_clear
.Lfast_wide_guard:
    tst.w %d2
    beq .Lsprite_ordered
    cmpi.w #21,%d2
    bhi .Lsprite_ordered
.Lfast_clear:
    move.l %a0,%a5
    .rept 16
    clr.l (%a5)+
    .endr
    tst.b 10(%a4)
    bne.s .Lfast_wide
.Lfast_narrow_loop:
    move.b (%a1)+,(%a0)
    addq.l #3,%a0
    dbra %d2,.Lfast_narrow_loop
    bra.s .Lfast_done
.Lfast_wide:
    clr.b 11(%a4)
    addq.l #1,%a2
    subq.w #1,%d2
.Lfast_wide_loop:
    move.b (%a3),(%a0)+
    move.b (%a2),(%a0)
    addq.l #2,%a0
    addq.l #2,%a2
    addq.l #2,%a3
    dbra %d2,.Lfast_wide_loop
.Lfast_done:
    move.b #-1,0x277f(%a6)
    move.b #-1,8(%a4)
    move.b #64,9(%a4)
    movem.l (%sp)+,%d2-%d5/%a2-%a6
    rts
.Lsprite_ordered:
    moveq #63,%d4
    move.b %d4,(%a5)
    tst.b 10(%a4)
    bne.s .Lsprite_wide
.Lsprite_narrow:
    move.b (%a1,%d2.w),(%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d2
    bmi.s .Lsprite_tail
    subq.b #1,%d3
    clr.b (%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d3
    clr.b (%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d3
    bpl.s .Lsprite_narrow
    bra.s .Lsprite_tail
.Lsprite_wide:
    clr.b 11(%a4)
    add.b %d2,%d2
    subq.b #1,%d2
    subq.b #2,%d3
.Lsprite_pair:
    move.b (%a2,%d2.w),(%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d2
    subq.b #1,%d3
    move.b (%a3,%d2.w),(%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d2
    bmi.s .Lsprite_tail
    subq.b #1,%d3
    clr.b (%a0,%d3.w)
    subq.b #1,%d4
    move.b %d4,(%a5)
    subq.b #1,%d3
    bra.s .Lsprite_pair
.Lsprite_tail:
    move.w %d4,%d3
    eori.w #63,%d3
    tst.b %d4
    bmi.s .Lsprite_one
    /* No source byte is read after this point. The high destination cannot
     * alias $277F or pointer operands, so the zero suffix can use longs. */
    move.w %d4,%d5
    addq.w #1,%d5
    move.l %a0,%a1
    adda.w %d3,%a1
    add.w %d5,%d3
    move.l %a1,%d0
    btst #0,%d0
    beq.s .Lsprite_aligned
    clr.b (%a1)+
    subq.w #1,%d5
.Lsprite_aligned:
    move.w %d5,%d0
    lsr.w #2,%d0
    beq.s .Lsprite_bytes
    subq.w #1,%d0
.Lsprite_longs:
    clr.l (%a1)+
    dbra %d0,.Lsprite_longs
.Lsprite_bytes:
    andi.w #3,%d5
    beq.s .Lsprite_filled
    subq.w #1,%d5
.Lsprite_remainder:
    clr.b (%a1)+
    dbra %d5,.Lsprite_remainder
.Lsprite_filled:
    moveq #-1,%d4
    bra.s .Lsprite_done
.Lsprite_one:
    clr.b (%a0,%d3.w)
    addq.b #1,%d3
    subq.b #1,%d4
.Lsprite_done:
    move.b %d4,(%a5)
    move.b %d2,8(%a4)
    move.b %d3,9(%a4)
    movem.l (%sp)+,%d2-%d5/%a2-%a6
    rts
