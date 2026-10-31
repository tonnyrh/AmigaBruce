/* $537E-$542E: complete ordered row run, actor0..2.
 * ABI: RAM, eight-byte AA/XX/YY/CC/ZZ/NN/VV/SP context, service callback.
 * Callbacks may change registers/pointer operands; reload them afterwards.
 * Arbitrary16-bit lane pointers retain byte-wrap semantics. */
    .macro RUN_LOAD_LANES
    moveq #0,%d7
    moveq #0,%d0
    move.b 0x5382(%a6),%d0
    lsl.w #8,%d0
    move.b 0x5381(%a6),%d0
    movea.l %d0,%a0
    cmpi.w #0xff00,%d0
    bls.s .Llane1_\@
    moveq #1,%d7
.Llane1_\@:
    moveq #0,%d0
    move.b 0x539c(%a6),%d0
    lsl.w #8,%d0
    move.b 0x539b(%a6),%d0
    movea.l %d0,%a1
    cmpi.w #0xff00,%d0
    bls.s .Llane2_\@
    moveq #1,%d7
.Llane2_\@:
    moveq #0,%d0
    move.b 0x53b6(%a6),%d0
    lsl.w #8,%d0
    move.b 0x53b5(%a6),%d0
    movea.l %d0,%a2
    cmpi.w #0xff00,%d0
    bls.s .Llane_ready_\@
    moveq #1,%d7
.Llane_ready_\@:
    tst.w %d7
    bne.s .Llane_wrap_\@
    adda.l %a6,%a0
    adda.l %a6,%a1
    adda.l %a6,%a2
.Llane_wrap_\@:
    lea 0x7fff(%a6),%a3
    adda.w #0x4ae1,%a3
    lea 0x4eed(%a6),%a4
    .endm

    .macro RUN_PIXEL pointer, mask, flags, wrap=0
    moveq #0,%d4
    .if \wrap
    move.l \pointer,%d0
    add.w %d2,%d0
    move.b (%a6,%d0.l),%d4
    .else
    move.b (\pointer,%d2.w),%d4
    .endif
    and.b \mask(%a3,%d2.w),%d4
    beq.s .Lpixel_done_\@
    move.b %d4,0x4e(%a6)
    move.l %d4,%d1
    lsr.w #4,%d1
    move.b %d1,\flags(%a4,%d1.w)
    andi.w #15,%d4
    move.b %d4,%d3
    move.b %d4,\flags(%a4,%d4.w)
.Lpixel_done_\@:
    .endm

    .macro RUN_PUBLISH
    move.b %d4,0(%a5)
    move.b %d3,1(%a5)
    move.b %d2,2(%a5)
    .endm

    .section .text.bl_contact_run_rows,"ax"
    .globl bl_contact_run_rows
bl_contact_run_rows:
    movem.l %d2-%d7/%a2-%a6,-(%sp)
    move.l 48(%sp),%a6
    move.l 52(%sp),%a5
    moveq #0,%d2
    move.b 2(%a5),%d2
    moveq #0,%d3
    move.b 1(%a5),%d3
    moveq #0,%d4
    move.b 0(%a5),%d4
    RUN_LOAD_LANES
.Lrun_top:
    move.w %d2,%d0
    andi.w #7,%d0
    bne .Lrun_bound
    tst.l 56(%sp)
    beq .Lrun_bound
    move.l 56(%sp),%a4
    RUN_PUBLISH
    move.l %a5,-(%sp)
    jsr (%a4)
    addq.l #4,%sp
    moveq #0,%d2
    move.b 2(%a5),%d2
    moveq #0,%d3
    move.b 1(%a5),%d3
    moveq #0,%d4
    move.b 0(%a5),%d4
    RUN_LOAD_LANES
.Lrun_bound:
    moveq #8,%d5
    move.w %d2,%d0
    andi.w #7,%d0
    sub.w %d0,%d5
    move.b 0x4f38(%a6),%d0
    sub.b %d2,%d0
    beq.s .Lbound_foot
    cmp.b %d5,%d0
    bcc.s .Lbound_foot
    move.b %d0,%d5
.Lbound_foot:
    move.b 0x4f39(%a6),%d0
    sub.b %d2,%d0
    beq.s .Lbound_part
    cmp.b %d5,%d0
    bcc.s .Lbound_part
    move.b %d0,%d5
.Lbound_part:
    move.b 0x4f3a(%a6),%d0
    sub.b %d2,%d0
    beq.s .Lbound_ready
    cmp.b %d5,%d0
    bcc.s .Lbound_ready
    move.b %d0,%d5
.Lbound_ready:
    subq.w #1,%d5
    tst.w %d7
    bne .Lrun_wrap
.Lrun_fast:
    RUN_PIXEL %a0,0,0
    RUN_PIXEL %a1,32,23
    RUN_PIXEL %a2,64,46
    addq.w #1,%d2
    dbra %d5,.Lrun_fast
    bra .Lrun_compare
.Lrun_wrap:
    RUN_PIXEL %a0,0,0,1
    RUN_PIXEL %a1,32,23,1
    RUN_PIXEL %a2,64,46,1
    addq.w #1,%d2
    dbra %d5,.Lrun_wrap
.Lrun_compare:
    andi.w #255,%d2
    cmp.b 0x4f38(%a6),%d2
    bne .Lrun_foot_compare
    RUN_PUBLISH
    move.b #1,3(%a5)
    move.b #1,4(%a5)
    clr.b 5(%a5)
    move.l %a5,-(%sp)
    move.l %a6,-(%sp)
    jsr bl_contact_body
    addq.l #8,%sp
    moveq #0,%d2
    move.b 2(%a5),%d2
    moveq #0,%d3
    move.b 1(%a5),%d3
    moveq #0,%d4
    move.b 0(%a5),%d4
    RUN_LOAD_LANES
.Lrun_foot_compare:
    cmp.b 0x4f39(%a6),%d2
    beq .Lrun_foot
    cmp.b 0x4f3a(%a6),%d2
    scc %d0
    seq %d1
    smi %d6
    neg.b %d0
    neg.b %d1
    neg.b %d6
    move.b %d0,3(%a5)
    move.b %d1,4(%a5)
    move.b %d6,5(%a5)
    tst.b %d1
    beq .Lrun_top
    RUN_PUBLISH
    move.b %d2,0x52(%a6)
    addq.b #2,7(%a5)
    moveq #0,%d0
    bra.s .Lrun_return
.Lrun_foot:
    RUN_PUBLISH
    moveq #0,%d0
    move.b 7(%a5),%d0
    lea 0x100(%a6),%a0
    move.b #0x54,(%a0,%d0.w)
    subq.b #1,%d0
    move.b #0x2b,(%a0,%d0.w)
    subq.b #1,%d0
    move.l %d0,-(%sp)
    move.l %a6,-(%sp)
    jsr bl_contact_classify_full
    addq.l #8,%sp
    moveq #0,%d1
    move.b 0x50(%a6),%d1
    lea 0xb6(%a6),%a0
    move.b %d0,(%a0,%d1.w)
    move.b %d1,1(%a5)
    clr.b 3(%a5)
    moveq #0,%d0
    move.b 7(%a5),%d0
    addq.b #2,%d0
    move.b %d0,7(%a5)
    lea 0x100(%a6),%a0
    move.b (%a0,%d0.w),%d0
    move.b %d0,0(%a5)
    seq 4(%a5)
    neg.b 4(%a5)
    lsr.b #7,%d0
    move.b %d0,5(%a5)
    moveq #1,%d0
.Lrun_return:
    movem.l (%sp)+,%d2-%d7/%a2-%a6
    rts
