"""Join two complete native runs after identical source/binary guard checks."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/spawn-audit-2026-10-26'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    first=read(BASE/'native-first-run.json');proof=read(BASE/'native-first-validation.json')
    assert proof['report_sha256']==sha(BASE/'native-first-run.json')
    assert proof['guard_sha256']==sha(ROOT/'test-amiga.ps1')
    assert proof['validator_sha256']==sha(ROOT/'tools/verify_spawn_native_report.ps1')
    path=ROOT/'reference/validation/a500-c64-combat-diagnostic.json';second=read(path)
    assert len(second['runs'])==1 and second['runs'][0]['frames']=='6000'
    assert first['executable_sha256']==second['executable_sha256']==sha(ROOT/'amiga/out/bruce_test.exe')
    assert first['adf_sha256']==second['adf_sha256']==sha(ROOT/'amiga/out/bruce_test.adf')
    a={x['path']:x['sha256'] for x in first['source_files']};b={x['path']:x['sha256'] for x in second['source_files']}
    assert a==b
    for p,h in a.items():assert sha(ROOT/p)==h,p
    raw=dict(line.split('=',1) for line in (BASE/'native-first-run.txt').read_text().splitlines() if '=' in line)
    assert raw==first['run']
    (BASE/'native-second-run.json').write_text(json.dumps(second,indent=2)+'\n')
    second['runs']=[first['run'],second['runs'][0]]
    second['execution']='filesystem CLI, two independent complete launches; captured first run validated with unchanged test-amiga guard body'
    second['batch_split_reason']='Native source fixtures made two launches exceed the combined startup allowance; no per-run guard was removed'
    second['independent_run_artifacts']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in
        (BASE/'native-first-run.json',BASE/'native-first-validation.json',BASE/'native-first-run.txt',BASE/'native-second-run.json')]
    path.write_text(json.dumps(second,indent=2)+'\n')
    print('Merged two complete6000 native runs; identical binary/source and all original per-run guards retained')
if __name__=='__main__':main()
