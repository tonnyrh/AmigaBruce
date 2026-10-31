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
/* GENERATED_CONTACT_CLASSES_BEGIN */
/* Fixed byte sets from $545C-$558B; no extra byte is read. */
    .section .text.bl_contact_classes4,"ax"
    .globl bl_contact_classes4
bl_contact_classes4:
    move.l 4(%sp),%a0
    moveq #0,%d0
/* $4F3C */
    moveq #0,%d1
    or.b 0x4eee(%a0),%d1
    or.b 0x4ef1(%a0),%d1
    or.w 0x4ef2(%a0),%d1
    or.b 0x4ef4(%a0),%d1
    or.b 0x4ef6(%a0),%d1
    or.b 0x4efa(%a0),%d1
    or.b 0x4efe(%a0),%d1
    or.b 0x4f01(%a0),%d1
    or.b 0x4f05(%a0),%d1
    or.l 0x4f08(%a0),%d1
    or.b 0x4f0d(%a0),%d1
    or.b 0x4f11(%a0),%d1
    or.b 0x4f18(%a0),%d1
    or.b 0x4f1c(%a0),%d1
    or.b 0x4f1f(%a0),%d1
    or.w 0x4f20(%a0),%d1
    or.b 0x4f22(%a0),%d1
    or.b 0x4f24(%a0),%d1
    or.b 0x4f28(%a0),%d1
    or.b 0x4f2c(%a0),%d1
    or.b 0x4f2f(%a0),%d1
    tst.l %d1
    beq.s 1f
    ori.b #1,%d0
1:
/* $4F3D */
    moveq #0,%d1
    or.b 0x4eef(%a0),%d1
    or.b 0x4ef3(%a0),%d1
    or.b 0x4ef5(%a0),%d1
    or.w 0x4ef6(%a0),%d1
    or.b 0x4ef8(%a0),%d1
    or.b 0x4efb(%a0),%d1
    or.b 0x4eff(%a0),%d1
    or.b 0x4f02(%a0),%d1
    or.b 0x4f06(%a0),%d1
    or.b 0x4f0a(%a0),%d1
    or.l 0x4f0c(%a0),%d1
    or.b 0x4f12(%a0),%d1
    or.b 0x4f16(%a0),%d1
    or.b 0x4f19(%a0),%d1
    or.b 0x4f1d(%a0),%d1
    or.b 0x4f21(%a0),%d1
    or.b 0x4f23(%a0),%d1
    or.w 0x4f24(%a0),%d1
    or.b 0x4f26(%a0),%d1
    or.b 0x4f29(%a0),%d1
    or.b 0x4f2d(%a0),%d1
    or.b 0x4f30(%a0),%d1
    tst.l %d1
    beq.s 2f
    ori.b #2,%d0
2:
/* $4F3E */
    moveq #0,%d1
    or.b 0x4efd(%a0),%d1
    or.l 0x4efe(%a0),%d1
    or.w 0x4f02(%a0),%d1
    or.l 0x4f14(%a0),%d1
    or.w 0x4f18(%a0),%d1
    or.b 0x4f1a(%a0),%d1
    or.b 0x4f2b(%a0),%d1
    or.l 0x4f2c(%a0),%d1
    or.w 0x4f30(%a0),%d1
    tst.l %d1
    beq.s 3f
    ori.b #4,%d0
3:
/* $4F3F */
    moveq #0,%d1
    or.b 0x4ef0(%a0),%d1
    or.b 0x4ef4(%a0),%d1
    or.l 0x4ef8(%a0),%d1
    or.b 0x4efc(%a0),%d1
    or.b 0x4f07(%a0),%d1
    or.b 0x4f0b(%a0),%d1
    or.b 0x4f0f(%a0),%d1
    or.l 0x4f10(%a0),%d1
    or.b 0x4f1e(%a0),%d1
    or.b 0x4f22(%a0),%d1
    or.l 0x4f26(%a0),%d1
    or.b 0x4f2a(%a0),%d1
    tst.l %d1
    beq.s 4f
    ori.b #8,%d0
4:
    rts
