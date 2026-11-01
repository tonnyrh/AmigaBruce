/* D-only zero minterm. As in copy_room_bitmap, BLTSIZE encodes 1024
 * rows of 20 words. Complete the write before any CPU tile painting. */
hw->bltcon0=0x0100;hw->bltcon1=0;hw->bltdmod=0;
hw->bltdpt=(APTR)background;hw->bltsize=20;wait_blitter();
