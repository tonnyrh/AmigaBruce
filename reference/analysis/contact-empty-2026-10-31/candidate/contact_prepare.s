/* Frozen $530A-$537D, $5431-$55AA and seven-exchange lane helpers.
 * All RAM operands are bytes, so odd C64 addresses are safe on 68000.
 * Pointer entry requires source actor0..2 and binary arithmetic; other
 * entries keep the generated source instruction path. */
    .macro C64_FRAME high, low
    move.b #\high,(%a5,%d3.w)
    subq.b #1,%d3
    move.b #\low,(%a5,%d3.w)
    addq.b #1,%d3
    .endm

    .macro CONTACT_ATTRIBUTE flag, base, ret
    C64_FRAME 0x53,\ret
    moveq #0,%d1
    move.w %d5,%d1
    add.w %d2,%d1
    move.b (%a0,%d1.l),%d0
    andi.b #7,%d0
    beq .Lattr_zero_\@
    tst.b \flag(%a0)
    bne .Lattr_done_\@
    addq.b #1,\flag(%a0)
    bra .Lattr_swap_\@
.Lattr_zero_\@:
    tst.b \flag(%a0)
    beq .Lattr_done_\@
    subq.b #1,\flag(%a0)
.Lattr_swap_\@:
    lea \base(%a0),%a1
    jsr .Lcontact_swap
.Lattr_done_\@:
    .endm

    .macro CONTACT_COLUMN operand, ret, final=0
    move.b %d0,0x43bc(%a0)
    C64_FRAME 0x53,\ret
    andi.l #255,%d0
    move.l %d0,%d1
    lsr.w #5,%d1
    lsl.w #3,%d0
    move.b %d0,0x43bc(%a0)
    move.b %d1,0x43bb(%a0)
    cmp.b %d6,%d0
    bcc .Lcolumn_no_borrow_\@
    subq.b #1,%d1
.Lcolumn_no_borrow_\@:
    sub.b %d6,%d0
    move.b %d0,\operand(%a0)
    move.b %d1,%d0
    add.w %d7,%d1
    move.b %d1,\operand+1(%a0)
    .if \final
    move.b %d1,0(%a2)
    /* V = ~(high^base) & (high^sum) & 0x80. The high byte
     * wraps before ADC; sum is kept wide only for the final carry. */
    move.w %d0,%d4
    eor.w %d7,%d4
    not.w %d4
    eor.w %d1,%d0
    and.w %d4,%d0
    andi.w #128,%d0
    sne 6(%a2)
    neg.b 6(%a2)
    move.b %d1,%d0
    lsr.b #7,%d0
    move.b %d0,5(%a2)
    tst.b %d1
    seq 4(%a2)
    neg.b 4(%a2)
    lsr.w #8,%d1
    move.b %d1,3(%a2)
    .endif
    .endm

    .section .text.bl_contact_pointers3,"ax"
    .globl bl_contact_pointers3
bl_contact_pointers3:
    movem.l %d2-%d7/%a2/%a5,-(%sp)
    move.l 36(%sp),%a0
    move.l 40(%sp),%a2
    lea 0x100(%a0),%a5
    moveq #0,%d3
    move.b 7(%a2),%d3
    moveq #0,%d0
    move.b 0x50(%a0),%d0
    lea 0xe9(%a0),%a1
    move.b (%a1,%d0.w),%d0
    C64_FRAME 0x53,0x11
    lea 0x50e7(%a0),%a1
    move.b (%a1,%d0.w),4(%a0)
    move.b 4(%a0),0x12(%a0)
    move.b 24(%a1,%d0.w),5(%a0)
    move.b 48(%a1,%d0.w),0x13(%a0)
    /* These two pointers and $52/$7C cannot be written by any
     * subsequent scratch, operand, stack or lane operation. */
    moveq #0,%d4
    move.b 5(%a0),%d4
    lsl.w #8,%d4
    move.b 4(%a0),%d4
    moveq #0,%d5
    move.b 0x13(%a0),%d5
    lsl.w #8,%d5
    move.b 0x12(%a0),%d5
    moveq #0,%d6
    move.b 0x52(%a0),%d6
    moveq #0,%d7
    move.b 0x7c(%a0),%d7
    moveq #0,%d1
    move.b 0x50(%a0),%d1
    move.b %d1,1(%a2)
    moveq #0,%d2
    lea 0xe6(%a0),%a1
    move.b (%a1,%d1.w),%d2
    CONTACT_ATTRIBUTE 0x4f32,0x4eed,0x18
    moveq #0,%d1
    move.w %d4,%d1
    add.w %d2,%d1
    move.b (%a0,%d1.l),%d0
    CONTACT_COLUMN 0x5381,0x20
    addq.b #1,%d2
    CONTACT_ATTRIBUTE 0x4f33,0x4f04,0x38
    moveq #0,%d1
    move.w %d4,%d1
    add.w %d2,%d1
    move.b (%a0,%d1.l),%d0
    CONTACT_COLUMN 0x539b,0x40
    addq.b #1,%d2
    cmpi.b #40,%d2
    bcc .Lthird_blank
    CONTACT_ATTRIBUTE 0x4f34,0x4f1b,0x60
    moveq #0,%d1
    move.w %d4,%d1
    add.w %d2,%d1
    move.b (%a0,%d1.l),%d0
    bra .Lthird_ready
.Lthird_blank:
    moveq #0,%d0
.Lthird_ready:
    CONTACT_COLUMN 0x53b5,0x68,1
    move.b %d2,2(%a2)
    addq.b #2,%d3
    move.b %d3,7(%a2)
    movem.l (%sp)+,%d2-%d7/%a2/%a5
    rts

    .section .text.bl_contact_classify_full_ordered,"ax"
    .globl bl_contact_classify_full_ordered
bl_contact_classify_full_ordered:
    movem.l %d3/%a5,-(%sp)
    move.l 12(%sp),%a0
    move.l 16(%sp),%d3
    lea 0x100(%a0),%a5
    clr.l 0x4f3c(%a0)
    clr.b 0x4f3b(%a0)
    tst.b 0x4f32(%a0)
    beq .Lclass_second
    subq.b #1,0x4f32(%a0)
    C64_FRAME 0x54,0x45
    lea 0x4eed(%a0),%a1
    jsr .Lcontact_swap
.Lclass_second:
    tst.b 0x4f33(%a0)
    beq .Lclass_third
    subq.b #1,0x4f33(%a0)
    C64_FRAME 0x54,0x50
    lea 0x4f04(%a0),%a1
    jsr .Lcontact_swap
.Lclass_third:
    tst.b 0x4f34(%a0)
    beq .Lclass_summary
    subq.b #1,0x4f34(%a0)
    C64_FRAME 0x54,0x5b
    lea 0x4f1b(%a0),%a1
    jsr .Lcontact_swap
.Lclass_summary:
    move.l %a0,-(%sp)
    jsr bl_contact_classes4
    addq.l #4,%sp
    movem.l (%sp)+,%d3/%a5
    rts

    .section .text.bl_contact_classify_full_zero,"ax"
    .globl bl_contact_classify_full_zero
bl_contact_classify_full_zero:
    movem.l %d3/%a5,-(%sp)
    move.l 12(%sp),%a0
    move.l 16(%sp),%d3
    lea 0x100(%a0),%a5
    clr.l 0x4f3c(%a0)
    clr.b 0x4f3b(%a0)
    tst.b 0x4f32(%a0)
    beq .Lclass_zero_second
    subq.b #1,0x4f32(%a0)
    C64_FRAME 0x54,0x45
    lea 0x4eed(%a0),%a1
    moveq #0,%d0
.Lclass_zero_second:
    tst.b 0x4f33(%a0)
    beq .Lclass_zero_third
    subq.b #1,0x4f33(%a0)
    C64_FRAME 0x54,0x50
    lea 0x4f04(%a0),%a1
    moveq #0,%d0
.Lclass_zero_third:
    tst.b 0x4f34(%a0)
    beq .Lclass_zero_summary
    subq.b #1,0x4f34(%a0)
    C64_FRAME 0x54,0x5b
    lea 0x4f1b(%a0),%a1
    moveq #0,%d0
.Lclass_zero_summary:
    moveq #0,%d0
    movem.l (%sp)+,%d3/%a5
    rts

    .section .text.bl_contact_swap_lane,"ax"
    .globl bl_contact_swap_lane
bl_contact_swap_lane:
    move.l 4(%sp),%a0
    move.l %a0,%a1
    move.l 8(%sp),%d0
    adda.l %d0,%a1
    moveq #0,%d0
.Lcontact_swap:
    move.b 3(%a1),%d0
    move.b 16(%a1),3(%a1)
    move.b %d0,16(%a1)
    move.b 7(%a1),%d0
    move.b 17(%a1),7(%a1)
    move.b %d0,17(%a1)
    move.b 11(%a1),%d0
    move.b 18(%a1),11(%a1)
    move.b %d0,18(%a1)
    move.b 12(%a1),%d0
    move.b 19(%a1),12(%a1)
    move.b %d0,19(%a1)
    move.b 13(%a1),%d0
    move.b 20(%a1),13(%a1)
    move.b %d0,20(%a1)
    move.b 14(%a1),%d0
    move.b 21(%a1),14(%a1)
    move.b %d0,21(%a1)
    move.b 15(%a1),%d0
    move.b 22(%a1),15(%a1)
    move.b %d0,22(%a1)
    rts

/* $55AB-$55C4: exactly72 cleared bytes, no reads or service boundary.
 * Initial byte aligns $4EEE; seventeen longs and the final word/byte
 * stop at $4F34. No additional byte is written. D0/A0 are scratch. */
    .section .text.bl_contact_clear72,"ax"
    .globl bl_contact_clear72
bl_contact_clear72:
    move.l 4(%sp),%a0
    adda.w #0x4eed,%a0
    clr.b (%a0)+
    moveq #16,%d0
1:
    clr.l (%a0)+
    dbra %d0,1b
    clr.w (%a0)+
    clr.b (%a0)
    rts

/* $53E0-$5428: body class snapshot/reduction and original XOR reversals.
 * Input context byte7 is virtual SP. Write only A/X/C/Z/N at0/1/3/4/5;
 * Y/V/D and virtual SP are preserved by the C seam. Actor is0..2. */
    .section .text.bl_contact_body_ordered,"ax"
    .globl bl_contact_body_ordered
bl_contact_body_ordered:
    movem.l %d3/%a2/%a5,-(%sp)
    move.l 16(%sp),%a0
    move.l 20(%sp),%a2
    lea 0x100(%a0),%a5
    moveq #0,%d3
    move.b 7(%a2),%d3
    move.b 0x4f34(%a0),0x4f37(%a0)
    move.b 0x4f33(%a0),0x4f36(%a0)
    move.b 0x4f32(%a0),0x4f35(%a0)
    C64_FRAME 0x53,0xf1
    move.l %d3,%d0
    subq.b #2,%d0
    move.l %d0,-(%sp)
    move.l %a0,-(%sp)
    jsr bl_contact_classify_full_ordered
    addq.l #8,%sp
    moveq #0,%d1
    move.b 0x50(%a0),%d1
    lea 0xb6(%a0),%a1
    move.b %d0,(%a1,%d1.w)
    lea 0xa7(%a0),%a1
    move.b %d0,(%a1,%d1.w)
    move.b 0x4f32(%a0),%d0
    cmp.b 0x4f35(%a0),%d0
    beq .Lbody_second
    eori.b #1,%d0
    move.b %d0,0x4f32(%a0)
    C64_FRAME 0x54,0x05
    lea 0x4eed(%a0),%a1
    jsr .Lcontact_swap
.Lbody_second:
    move.b 0x4f33(%a0),%d0
    cmp.b 0x4f36(%a0),%d0
    beq .Lbody_third
    eori.b #1,%d0
    move.b %d0,0x4f33(%a0)
    C64_FRAME 0x54,0x15
    lea 0x4f04(%a0),%a1
    jsr .Lcontact_swap
.Lbody_third:
    move.b 0x4f34(%a0),%d0
    cmp.b 0x4f37(%a0),%d0
    beq .Lbody_equal
    scc 3(%a2)
    neg.b 3(%a2)
    eori.b #1,%d0
    move.b %d0,0x4f34(%a0)
    C64_FRAME 0x54,0x25
    lea 0x4f1b(%a0),%a1
    jsr .Lcontact_swap
    move.b %d0,0(%a2)
    move.b 0x50(%a0),1(%a2)
    clr.b 5(%a2)
    tst.b 1(%a2)
    seq 4(%a2)
    neg.b 4(%a2)
    bra .Lbody_done
.Lbody_equal:
    move.b %d0,0(%a2)
    move.b 0x50(%a0),1(%a2)
    move.b #1,3(%a2)
    move.b #1,4(%a2)
    clr.b 5(%a2)
.Lbody_done:
    movem.l (%sp)+,%d3/%a2/%a5
    rts
    .section .text.bl_contact_body_zero,"ax"
    .globl bl_contact_body_zero
bl_contact_body_zero:
    movem.l %d3/%a2/%a5,-(%sp)
    move.l 16(%sp),%a0
    move.l 20(%sp),%a2
    lea 0x100(%a0),%a5
    moveq #0,%d3
    move.b 7(%a2),%d3
    move.b 0x4f34(%a0),0x4f37(%a0)
    move.b 0x4f33(%a0),0x4f36(%a0)
    move.b 0x4f32(%a0),0x4f35(%a0)
    C64_FRAME 0x53,0xf1
    move.l %d3,%d0
    subq.b #2,%d0
    move.l %d0,-(%sp)
    move.l %a0,-(%sp)
    jsr bl_contact_classify_full_zero
    addq.l #8,%sp
    moveq #0,%d1
    move.b 0x50(%a0),%d1
    lea 0xb6(%a0),%a1
    move.b %d0,(%a1,%d1.w)
    lea 0xa7(%a0),%a1
    move.b %d0,(%a1,%d1.w)
    move.b 0x4f32(%a0),%d0
    cmp.b 0x4f35(%a0),%d0
    beq .Lbody_zero_second
    eori.b #1,%d0
    move.b %d0,0x4f32(%a0)
    C64_FRAME 0x54,0x05
    lea 0x4eed(%a0),%a1
    moveq #0,%d0
.Lbody_zero_second:
    move.b 0x4f33(%a0),%d0
    cmp.b 0x4f36(%a0),%d0
    beq .Lbody_zero_third
    eori.b #1,%d0
    move.b %d0,0x4f33(%a0)
    C64_FRAME 0x54,0x15
    lea 0x4f04(%a0),%a1
    moveq #0,%d0
.Lbody_zero_third:
    move.b 0x4f34(%a0),%d0
    cmp.b 0x4f37(%a0),%d0
    beq .Lbody_zero_equal
    scc 3(%a2)
    neg.b 3(%a2)
    eori.b #1,%d0
    move.b %d0,0x4f34(%a0)
    C64_FRAME 0x54,0x25
    lea 0x4f1b(%a0),%a1
    moveq #0,%d0
    move.b %d0,0(%a2)
    move.b 0x50(%a0),1(%a2)
    clr.b 5(%a2)
    tst.b 1(%a2)
    seq 4(%a2)
    neg.b 4(%a2)
    bra .Lbody_zero_done
.Lbody_zero_equal:
    move.b %d0,0(%a2)
    move.b 0x50(%a0),1(%a2)
    move.b #1,3(%a2)
    move.b #1,4(%a2)
    clr.b 5(%a2)
.Lbody_zero_done:
    movem.l (%sp)+,%d3/%a2/%a5
    rts

/* Empty69-byte class table: exchanges of zero bytes and four OR
 * reductions have no RAM effect. Preserve every original conditional DEC,
 * XOR, snapshot, guest JSR byte and published register. No service inside.
 * Nonempty input executes the prior assembly unchanged. */
    .section .text.bl_contact_empty69,"ax"
.Lcontact_empty69:
    moveq #0,%d0
    move.b 0x4eed(%a0),%d0
    or.l 0x4eee(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4ef2(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4ef6(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4efa(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4efe(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f02(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f06(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f0a(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f0e(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f12(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f16(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f1a(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f1e(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f22(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f26(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f2a(%a0),%d0
    bne .Lcontact_empty_return
    or.l 0x4f2e(%a0),%d0
    bne .Lcontact_empty_return
.Lcontact_empty_return:
    rts
    .section .text.bl_contact_classify_full,"ax"
    .globl bl_contact_classify_full
bl_contact_classify_full:
    move.l 4(%sp),%a0
    jsr .Lcontact_empty69
    bne.s .Lbl_contact_classify_full_fallback
    jmp bl_contact_classify_full_zero
.Lbl_contact_classify_full_fallback:
    jmp bl_contact_classify_full_ordered
    .section .text.bl_contact_body,"ax"
    .globl bl_contact_body
bl_contact_body:
    move.l 4(%sp),%a0
    jsr .Lcontact_empty69
    bne.s .Lbl_contact_body_fallback
    jmp bl_contact_body_zero
.Lbl_contact_body_fallback:
    jmp bl_contact_body_ordered
