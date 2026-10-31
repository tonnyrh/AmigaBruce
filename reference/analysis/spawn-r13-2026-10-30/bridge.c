/* Test-only live field entry; production sources are unchanged. */
#include "../../../tests/source_contact_bridge.c"
void bl_r13_field(void){actor_world_enabled=1;source_actor_field();actor_world_enabled=0;}
