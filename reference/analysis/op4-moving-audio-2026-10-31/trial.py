"""Causal trial only: allow existing field/audio service at the lethal-fall back edge."""
from probe import HERE,ROOT,WORK,sources,compile_program,change

def build():
    f=WORK/"candidate";f.mkdir(exist_ok=True)
    main,core=sources("reference")
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    anchor="L2c51:; /* $2C51 */\ngoto L2bf9;"
    actor=change(actor,anchor,"""L2c51:; /* $2C51 */
if(actor_world_enabled && !actor_i && !d && x==2 && (m[0xbc+x]&0x10) && m[0xd1+x]>=133 && io_service)io_service();
goto L2bf9;""")
    (f/"main.c").write_text(main);(f/"c64_rooms.c").write_text(core);(f/"c64_actor_programs.h").write_text(actor)
    compile_program(f,ROOT/".tmp/op1-kage/reference")
if __name__=="__main__":build()
