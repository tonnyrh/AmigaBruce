"""Replay the existing object oracle on the isolated neutral-row candidate."""
import ctypes
import hashlib
import json
import sys
from check_images import ROOT,WORK,dll

def main():
    source=(ROOT/"tests/source_contact_bridge.c").read_text().replace("../core/c64_rooms.c",(WORK/"neutral/c64_rooms.c").as_posix())
    source+='\n__declspec(dllexport) unsigned long bl_object_classify(void){return source_object_classify();}\n'
    for n in ("bl_contact_seed","bl_contact_run","bl_contact_copy","bl_contact_regs","bl_contact_return","bl_contact_fault"):
        source=source.replace("void "+n+"(","__declspec(dllexport) void "+n+"(")
        source=source.replace("unsigned long "+n+"(","__declspec(dllexport) unsigned long "+n+"(")
    dll("object-row-proof",source)
    original=ROOT/"tools/verify_source_object.py"
    program=original.read_text().replace(".tmp/source-object-test/objects.dll",".tmp/op-finish/object-row-proof/bridge.dll")
    program=program.replace("reference/validation/source-object-host.json",".tmp/op-finish/object-row-proof/result.json")
    exec(compile(program,str(original),"exec"),{"__file__":str(original),"__name__":"__main__"})
    result=WORK/"object-row-proof/result.json";report=json.loads(result.read_text())
    paths=[WORK/"object-row-proof/bridge.c",WORK/"neutral/c64_rooms.c",WORK/"neutral/c64_actor_programs.h",original]
    report["source_files"]=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    result.write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":main()
