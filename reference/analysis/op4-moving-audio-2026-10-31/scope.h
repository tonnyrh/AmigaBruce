#define OP4_DO(id,stmt) do {unsigned long op4_old=op4_region(id);stmt;op4_region(op4_old);}while(0)
extern unsigned long op4_region(unsigned long);
extern unsigned short op4_origin;
enum { O_OTHER,O_SOUND,O_FIELD,O_PREFIX,O_TAIL,O_VIC,O_STEP,O_CONTACT,O_OBJECT,O_COMBAT,
       O_ACTOR,O_SPRITE,O_PREPARE,O_LOAD,O_PATCH,O_RESTORE,O_ANIMATE,O_PROJECTILE,
       O_FIGHTER,O_HEALTH,O_LIVES,O_SCORE,O_PRESENT,O_COUNT };
