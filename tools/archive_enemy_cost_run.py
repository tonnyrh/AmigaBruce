"""Bind private compile inputs alongside the standard benchmark report."""
import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
def main():
    label,variant=sys.argv[1:];run=ROOT/'reference/analysis/optimization-2026-10-27'/label
    assert (run/'native.txt').exists()
    source=BASE/variant;builder=BASE/(variant+'-build.ps1')
    mainfile=source/'main.c' if (source/'main.c').exists() else BASE/'main.c'
    target=run/'compiled-inputs';target.mkdir(exist_ok=True)
    files=list(source.iterdir())+[builder,mainfile]
    entries=[]
    for p in dict.fromkeys(files):
        dest=target/p.name
        if dest.exists():assert dest.read_bytes()==p.read_bytes()
        else:shutil.copyfile(p,dest)
        entries.append(dict(path=p.relative_to(ROOT).as_posix(),archived=dest.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (run/'compile-overrides.json').write_text(json.dumps(dict(production_changed=False,variant=variant,actual_private_inputs=entries,note='These override the canonical production paths recorded by the generic benchmark harness. No original-playthrough claim.'),indent=2)+'\n')
    print('Archived',label,variant)
if __name__=='__main__':main()
