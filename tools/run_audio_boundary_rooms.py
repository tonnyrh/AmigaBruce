"""Prepare a retry runner from completed menu stage; do not redo passed menu."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30'
text=(BASE/'ui-run.ps1').read_text(encoding='utf-8-sig')
first=text.index('$menu=Start-Process');end=text.index('# Menu controls leave')
text=text[:first]+text[end:]
(BASE/'ui-rooms-retry.ps1').write_text(text,encoding='utf-8')
print('Prepared fresh room/clock/death/ADF retry; completed menu audit retained')
