"""Derive a boot checker with separate output paths; keep prior UI proof."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30'
def main():
    code=(ROOT/'tools/check_compact_boot.py').read_text()
    code=code.replace('ROOT=Path(__file__).resolve().parents[1]',f'ROOT=Path({str(ROOT)!r})')
    code=code.replace('reference/analysis/flat-control-compact-2026-10-30/normal-ui','reference/analysis/audio-service-2026-10-30/normal-ui')
    code='import sys\nsys.path.insert(0,'+repr(str(ROOT/'tools'))+')\n'+code
    (BASE/'check-boot.py').write_text(code,encoding='utf-8')
    print('Prepared separate current-stage boot output paths')
if __name__=='__main__':main()
