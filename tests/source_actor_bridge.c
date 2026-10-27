#include "../core/c64_rooms.h"
void bl_actor_copy(unsigned char *out){long i;for(i=0;i<65536;i++)out[i]=bl_c64_read(i);}
void bl_actor_prepare(long room){
    bl_c64_reset();bl_c64_actor_seed();bl_c64_actor_test_call(0x0f72,0);
    bl_c64_test_write(2,50);bl_c64_test_write(0x104,1);
    /* Injected entry after $182A-$1836, before the actual $1886/$0763.
     * This is a controlled life-start seam, not a title/menu playthrough. */
    bl_c64_test_write(0xd1,36);bl_c64_test_write(0xd2,36);bl_c64_test_write(0xd3,36);
    bl_c64_actor_test_call(0x0763,0);
    bl_c64_load(room);bl_c64_actor_test_call(0x0b30,0);
}
