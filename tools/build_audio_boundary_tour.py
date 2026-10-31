"""Paired tours using production core and one isolated Amiga poll change."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30'
def main():
    original=(ROOT/'test-source-room-tour.ps1').read_text(encoding='utf-8-sig')
    for variant in ['before','after']:
        text=original.replace('$taskRoot=$PSScriptRoot\n',"$taskRoot='"+str(ROOT)+"'\n",1)
        if variant=='after':
            anchor='[IO.File]::WriteAllText($generated,$text)';assert text.count(anchor)==1
            extra="$pollOld='game_field_busy=1;while(gap--)bl_c64_field();game_field_busy=0;'\n$pollNew='game_field_busy=1;while(gap--){bl_c64_field();source_audio_service();}game_field_busy=0;'\nif([regex]::Matches($text,[regex]::Escape($pollOld)).Count -ne 1){throw 'Audio boundary anchor changed'}\n$text=$text.Replace($pollOld,$pollNew)\n"
            text=text.replace(anchor,extra+anchor)
        (BASE/(variant+'-tour.ps1')).write_text(text,encoding='utf-8')
    print('Generated paired audio-boundary tours; only diagnostic main differs')
if __name__=='__main__':main()
