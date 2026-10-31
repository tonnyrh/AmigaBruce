/* 68000-only repeat check for the field-sampled source VIC latch.
 * SourceVicRepeat offsets are compile-time checked in c64_rooms.c.
 * Compare63 bytes; byte64 and noncandidate bitmaps have no effect.
 * Miss: no RAM/cache write. Hit: OR cached bits into emulated $D01E.
 * Source bitmap pointers are64-byte aligned and end at most at $FFFE. */
    .section .text.bl_vic_repeat,"ax"
    .globl bl_vic_repeat
bl_vic_repeat:
    movem.l %d2-%d3/%d5-%d7/%a2-%a4,-(%sp)
    move.l 36(%sp),%a0
    move.l 40(%sp),%a1
    move.l %a0,%a4
    adda.l #0xd000,%a4
    tst.b 553(%a1)
    beq .Lrepeat_miss
    moveq #0,%d7
    move.b 0x15(%a4),%d7
    cmp.b 554(%a1),%d7
    bne .Lrepeat_miss
    move.b 0x17(%a4),%d0
    cmp.b 555(%a1),%d0
    bne .Lrepeat_miss
    move.b 0x1d(%a4),%d0
    cmp.b 556(%a1),%d0
    bne .Lrepeat_miss
    move.l %a4,%a2
    lea 512(%a1),%a3
    moveq #0,%d5
.Lrepeat_positions:
    btst %d5,%d7
    beq.s .Lrepeat_position_next
    moveq #0,%d0
    move.b (%a2),%d0
    btst %d5,0x10(%a4)
    beq.s .Lrepeat_low_x
    addi.w #256,%d0
.Lrepeat_low_x:
    cmp.w (%a3),%d0
    bne .Lrepeat_miss
    moveq #0,%d0
    move.b 1(%a2),%d0
    cmp.w 16(%a3),%d0
    bne .Lrepeat_miss
.Lrepeat_position_next:
    addq.l #2,%a2
    addq.l #2,%a3
    addq.w #1,%d5
    cmpi.w #8,%d5
    bne.s .Lrepeat_positions
    moveq #0,%d6
    move.b 558(%a1),%d6
    beq .Lrepeat_hit
    move.b 552(%a1),%d0
    and.b %d6,%d0
    cmp.b %d6,%d0
    bne .Lrepeat_miss
    moveq #0,%d3
    move.b 0xd00(%a4),%d3
    not.b %d3
    andi.w #3,%d3
    ror.w #2,%d3
    moveq #0,%d2
    move.b 0x18(%a4),%d2
    andi.w #0xf0,%d2
    lsl.w #6,%d2
    add.w %d3,%d2
    addi.w #0x3f8,%d2
    moveq #0,%d5
.Lrepeat_sprites:
    btst %d5,%d6
    beq .Lrepeat_sprite_next
    moveq #0,%d0
    btst %d5,0x1c(%a4)
    beq.s .Lrepeat_hires
    moveq #1,%d0
.Lrepeat_hires:
    btst %d5,0x1d(%a4)
    beq.s .Lrepeat_narrow
    ori.b #2,%d0
.Lrepeat_narrow:
    lea 544(%a1),%a2
    cmp.b (%a2,%d5.w),%d0
    bne .Lrepeat_miss
    moveq #0,%d1
    move.w %d2,%d1
    add.w %d5,%d1
    moveq #0,%d0
    move.b (%a0,%d1.l),%d0
    lsl.w #6,%d0
    add.w %d3,%d0
    lea (%a0,%d0.l),%a3
    move.w %d5,%d1
    lsl.w #6,%d1
    lea (%a1,%d1.w),%a2
    .rept 15
    cmpm.l (%a2)+,(%a3)+
    bne.s .Lrepeat_bytes_miss
    .endr
    cmpm.b (%a2)+,(%a3)+
    bne.s .Lrepeat_bytes_miss
    cmpm.b (%a2)+,(%a3)+
    bne.s .Lrepeat_bytes_miss
    cmpm.b (%a2)+,(%a3)+
    beq.s .Lrepeat_sprite_next
.Lrepeat_bytes_miss:
    bra .Lrepeat_miss
.Lrepeat_sprite_next:
    addq.w #1,%d5
    cmpi.w #8,%d5
    bne .Lrepeat_sprites
.Lrepeat_hit:
    move.b 557(%a1),%d0
    or.b %d0,0x1e(%a4)
    moveq #1,%d0
    bra.s .Lrepeat_done
.Lrepeat_miss:
    moveq #0,%d0
.Lrepeat_done:
    movem.l (%sp)+,%d2-%d3/%d5-%d7/%a2-%a4
    rts

    .section .text.bl_vic_equal63,"ax"
    .globl bl_vic_equal63
bl_vic_equal63:
    move.l 4(%sp),%a0
    move.l 8(%sp),%a1
    .rept 15
    cmpm.l (%a0)+,(%a1)+
    bne.s 2f
    .endr
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
