/* $5380-$53CE. Enter with up to eight rows and non-wrapping glyph spans.
 * Keep three glyph cursors and a mask cursor at the current row.
 * a0 addresses class lane 0; its signed displacement also reaches $4E. */
    .section .text.bl_contact_rows8,"ax"
    .globl bl_contact_rows8
bl_contact_rows8:
    movea.l 4(%sp),%a0
    movea.l 8(%sp),%a1
    moveq #0,%d0
    move.b 9(%a1),%d0
    beq .Ldone
    movem.l %d2-%d3/%a2-%a5,-(%sp)
    move.w %d0,%d2
    subq.w #1,%d2
    move.b 8(%a1),%d0
    lea (%a0,%d0.w),%a2
    movea.l %a2,%a3
    movea.l %a2,%a4
    movea.l %a2,%a5
    adda.l #0xcb20,%a5
    moveq #0,%d1
    move.w (%a1),%d1
    adda.l %d1,%a2
    move.w 2(%a1),%d1
    adda.l %d1,%a3
    move.w 4(%a1),%d1
    adda.l %d1,%a4
    lea 0x4eed(%a0),%a0
    move.b 7(%a1),%d3
    moveq #0,%d0
.Lrow:
    move.b (%a2)+,%d0
    and.b -64(%a5),%d0
    beq.s .Lmiddle
    move.b %d0,0x4e-0x4eed(%a0)
    move.w %d0,%d1
    lsr.w #4,%d1
    move.b %d1,(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,(%a0,%d0.w)
    move.b %d0,%d3
.Lmiddle:
    move.b (%a3)+,%d0
    and.b -32(%a5),%d0
    beq.s .Lright
    move.b %d0,0x4e-0x4eed(%a0)
    move.w %d0,%d1
    lsr.w #4,%d1
    move.b %d1,23(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,23(%a0,%d0.w)
    move.b %d0,%d3
.Lright:
    move.b (%a4)+,%d0
    and.b (%a5)+,%d0
    beq.s .Lnext
    move.b %d0,0x4e-0x4eed(%a0)
    move.w %d0,%d1
    lsr.w #4,%d1
    move.b %d1,46(%a0,%d1.w)
    andi.w #15,%d0
    move.b %d0,46(%a0,%d0.w)
    move.b %d0,%d3
.Lnext:
    dbra %d2,.Lrow
    move.b %d0,6(%a1)
    move.b %d3,7(%a1)
    move.b 9(%a1),%d1
    add.b %d1,8(%a1)
    movem.l (%sp)+,%d2-%d3/%a2-%a5
.Ldone:
    rts
