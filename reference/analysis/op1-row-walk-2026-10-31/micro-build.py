import subprocess
from build import HERE, ROOT, OBJECTS, GCC, FLAGS, TOOLS
out=HERE/'micro'
out.mkdir(exist_ok=True)
old=(ROOT/'amiga/contact_rows.s').read_text().split('/* GENERATED_CONTACT_CLASSES_BEGIN */')[0]
(out/'parent.s').write_text(old.replace('bl_contact_rows8','parent_rows'))
for source in [out/'parent.s',HERE/'micro.c']:
    subprocess.run([GCC,*FLAGS,'-c',source,'-o',out/(source.stem+'.o')],check=True)
elf=out/'bruce_amiga.elf'
subprocess.run([GCC,*FLAGS,'-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start',OBJECTS/'start.o',out/'micro.o',out/'parent.o',HERE/'light/contact_rows.o',OBJECTS/'runtime.o','-o',elf],check=True)
subprocess.run([TOOLS/'elf2hunk.exe',elf,out/'bruce_amiga.exe'],check=True)
