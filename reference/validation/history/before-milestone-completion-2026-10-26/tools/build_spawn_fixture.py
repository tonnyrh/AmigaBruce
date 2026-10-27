"""Select executed original6502 results for the host/68000 regression fixture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/spawn-audit-2026-10-26'
def main():
    r=json.loads((BASE/'report.json').read_text());w=json.loads((BASE/'world-controls.json').read_text())
    for report in (r,w):
        for x in report['source_files']:
            assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
    # Three actual service paths per room: cold due, saved arrivals, aged/mode.
    selected=[x for x in r['services'] if (x['inputs'][1:]==[0,0,0,0,1,2,0,0] or
        x['inputs'][1:]==[0,0,0,0,1,1,192,3] or x['inputs'][1:]==[25,1,1,0,0,0,255,3])]
    assert len(selected)==60
    lines=['/* Generated from actual source calls, injected RAM/register seams.',
        ' * Frozen SHA256 '+r['source_sha256']+'. Not a natural playthrough. */',
        '#ifndef BRUCE_SPAWN_FIXTURE_H','#define BRUCE_SPAWN_FIXTURE_H',
        '#include "../core/c64_rooms.h"','#include "../core/rooms.h"',
        '#define SPAWN_FIXTURE_CASES 223',
        'static const unsigned char spawn_service_rows[60][33]={']
    for x in selected:lines.append('{'+','.join(map(str,x['inputs']+x['output']+x['counters']+x['saved_x']))+'},')
    lines+=['};','static const unsigned char spawn_initial_rows[80][6]={']
    for x in r['initial']:lines.append('{'+','.join(map(str,[x['room'],x['round'],x['mode'],*x['counters'],x['disabled']]))+'},')
    lines+=['};','static const unsigned char spawn_remove_rows[40][3]={']
    for x in r['removal']:
        if x['age']==31 and x['round']==1 and x['mode']==1:lines.append('{'+','.join(map(str,[x['room'],x['actor'],x['delay']]))+'},')
    lines+=['};','static const unsigned char spawn_bomb_rows[30][6]={']
    for x in w['birth_bombs']:lines.append('{'+','.join(map(str,[x['actor'],*x['bomb'],x['phase'],x['active'],x['delay']]))+'},')
    lines+=['};','typedef struct {unsigned char actor,bits,cross,steps;unsigned char expected[28][5];} BlSpawnEntryFixture;',
        'static const BlSpawnEntryFixture spawn_entry_rows[8]={']
    for x in r['entry']:
        if x['bits'] not in (0x55,0xff) or x['color']!=1 or x['history']!=1:continue
        stages=['{'+','.join(map(str,[*s['position'],s['state'],s['counter']]))+'}' for s in x['stages']]
        lines.append('{'+','.join(map(str,[x['actor'],x['bits'],int(x['cross']),len(stages)]))+',{'+','.join(stages)+'}},')
    lines+=['};',r'''
#define SPAWN_CHECK(q) do{if(!(q))return __LINE__;}while(0)
static unsigned short spawn_fixture_run(void){
    int i,j,k;long a;BlCombat w;BlProgress p;
    static const unsigned short watch[10]={0x95,0x9e,0xa1,0xa4,0xbf,0xce,0xd1,0x4f48,0x4f4e,0x106};
    for(i=0;i<80;i++){
        const unsigned char *r=spawn_initial_rows[i];
        bl_c64_reset();bl_c64_test_write(0x40,r[1]);bl_c64_set_opponent_mode(r[2]);bl_c64_load(r[0]);
        SPAWN_CHECK(bl_c64_spawn_counter(2)==r[3] && bl_c64_spawn_counter(1)==r[4] && bl_c64_read(0x7a)==r[5]);
        SPAWN_CHECK(!bl_c64_read(0x87) && !bl_c64_read(0x88));
    }
    for(i=0;i<60;i++){
        const unsigned char *r=spawn_service_rows[i];
        bl_c64_reset();bl_c64_load(r[0]);bl_c64_test_execute(0x10c5);
        bl_c64_test_write(0x88,r[1]);bl_c64_test_write(0x40,r[2]);bl_c64_set_opponent_mode(r[3]);
        bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);
        for(a=0x6000;a<0x6300;a++)bl_c64_test_write(a,r[7]);
        bl_c64_spawn_sync(1,r[4]&1,56,98,20,r[6]);bl_c64_spawn_sync(2,r[4]&2,120,98,7,r[5]);
        for(j=1;j<=2;j++)if(r[8]&(1<<(j-1)))bl_c64_enemy_follow(j,1,84,130,6);
        bl_c64_spawn_services(80,196);
        for(j=1;j<=2;j++)for(k=0;k<10;k++)SPAWN_CHECK(bl_c64_read(watch[k]+j)==r[9+(j-1)*10+k]);
        SPAWN_CHECK(bl_c64_spawn_counter(2)==r[29] && bl_c64_spawn_counter(1)==r[30]);
        SPAWN_CHECK(bl_c64_read(0x8b)==r[31] && bl_c64_read(0x8c)==r[32]);
        SPAWN_CHECK(!bl_c64_fault());
    }
    for(i=0;i<40;i++){
        const unsigned char *r=spawn_remove_rows[i];
        bl_c64_reset();bl_c64_load(r[0]);bl_c64_test_write(0x88,31);bl_c64_test_write(0x40,1);bl_c64_set_opponent_mode(1);
        bl_c64_spawn_sync(r[1],1,84,130,6,0);
        SPAWN_CHECK(bl_c64_enemy_remove(r[1])==r[2] && !(bl_c64_read(0x95+r[1])&1));
    }
    for(i=0;i<8;i++){
        const BlSpawnEntryFixture *r=&spawn_entry_rows[i];BlFighter *f;int target=80;
        bl_combat_reset(&w);bl_progress_reset(&p);w.player.active=0;w.player.body.x=target*16;
        w.enemy[0].respawn=w.enemy[1].respawn=200;w.enemy[r->actor-1].respawn=1;
        bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);
        for(a=0x6000;a<0x6300;a++)bl_c64_test_write(a,0);
        f=&w.enemy[r->actor-1];f->body.wall.moves[0][2]=1;f->body.wall.previous=19;f->body.wall.animation=5;
        bl_c64_test_write(0x4f5d+r->actor,1);bl_c64_test_write(0xc2+r->actor,19);bl_c64_test_write(0xcb+r->actor,5);
        bl_combat_spawn_service(&w);w.spawn_ready=0;bl_c64_test_write(0x7a,1);bl_c64_test_write(0x7c,0xa0);
        for(a=120;a<1000;a++){bl_c64_test_write(0x8c00+a,0);bl_c64_test_write(0xd800+a,1);}
        for(a=0;a<8;a++)bl_c64_test_write(0xa000+a,r->bits);
        f->body.wall.contact=0;
        for(j=0;j<r->steps;j++){
            const unsigned char *e=r->expected[j];if(r->cross && j==9)target=320;
            w.player.body.x=target*16;bl_combat_step(&w,0);
            SPAWN_CHECK((bl_x(&f->body)+24)/2==e[0] && bl_y(&f->body)==e[1] && f->body.facing==e[2]);
            if(f->entering)SPAWN_CHECK(f->entry_state==e[3] && f->timer==e[4]);
        }
    }
    /* Cold R01 integration: fixed inactive target at X302, controlled
     * reader page filled with1; full native room/object/actor calls. */
    bl_combat_reset(&w);bl_progress_reset(&p);w.player.active=0;w.player.body.x=302*16;bl_c64_test_write(0x95,0);
    bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);
    for(a=0x6000;a<0x6300;a++)bl_c64_test_write(a,1);
    for(i=1;i<=123;i++){
        bl_c64_field();bl_c64_field();bl_c64_field();bl_progress_step(&p,&w,0);
        if(i==103)SPAWN_CHECK(!w.enemy[1].active && w.enemy[1].respawn==1);
        if(i==104)SPAWN_CHECK(w.enemy[1].active && w.enemy[1].entering && w.enemy[1].timer==15 && bl_x(&w.enemy[1].body)==294);
        if(i==119)SPAWN_CHECK(w.enemy[1].active && !w.enemy[1].timer && bl_x(&w.enemy[1].body)==294);
        if(i==120)SPAWN_CHECK(w.enemy[1].active && bl_x(&w.enemy[1].body)==298);
        if(i==122)SPAWN_CHECK(!w.enemy[1].active && w.enemy[1].respawn==160 && bl_x(&w.enemy[1].body)==302);
    }
    for(i=0;i<30;i++){
        const unsigned char *r=spawn_bomb_rows[i];
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,7);
        w.player.active=0;bl_c64_test_write(0x95,0);
        w.enemy[0].respawn=w.enemy[1].respawn=200;w.enemy[r[0]-1].respawn=1;
        bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);bl_c64_test_write(0x7c,0xa0);
        for(a=0x6000;a<0x6300;a++)bl_c64_test_write(a,1);
        bl_c64_enemy_follow(r[0],1,r[1]*8+4,r[2]*16+4,6);
        bl_c64_test_write(0x4fde,r[3]);bl_c64_test_write(0x4fe1,r[1]-1);bl_c64_test_write(0x4fe4,r[2]-1);bl_c64_test_execute(0x3228);
        bl_progress_step(&p,&w,0);
        SPAWN_CHECK(w.enemy[r[0]-1].active==r[4] && w.enemy[r[0]-1].respawn==r[5] && !bl_c64_fault());
    }
    return 0;
}
#undef SPAWN_CHECK
#endif
''']
    (ROOT/'tests/spawn_fixture.h').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Generated spawn fixture:80 initial,60 services,40 returns,8 entry routes,5 edge checkpoints,30 birth blasts')
if __name__=='__main__':main()
