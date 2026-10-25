/* Host-only scalar bridge: no Python guesses about -mshort structure layout. */
#include "contact_fixture.h"
static BlProgress probe_progress;
static BlCombat probe_world;
long bl_contact_fixture_count(void){return BL_CONTACT_CASE_COUNT;}
long bl_contact_fixture_value(long index,long field){return contact_cases[index][field];}
void bl_contact_prepare(long index){contact_fixture_prepare(&probe_progress,&probe_world,(unsigned short)index);}
void bl_contact_run(void){bl_progress_contacts(&probe_progress,&probe_world,0);}
long bl_contact_result(long field){
    if(field==0)return probe_progress.room;
    if(field==1)return bl_x(&probe_world.player.body);
    if(field==2)return bl_y(&probe_world.player.body);
    if(field==3)return probe_progress.pickups;
    if(field==4)return probe_progress.score;
    if(field==5)return bl_c64_object_pose(&probe_world.player.body);
    if(field==6)return bl_c64_audio_requests();
    return contact_fixture_run();
}
