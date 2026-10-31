"""Private scheduling experiment: poll audio after a complete native field."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30'
def main():
    folder=BASE/'boundary';folder.mkdir(parents=True,exist_ok=True)
    main=(ROOT/'.tmp/compact-delivery/math-main.c').read_text(encoding='utf-8-sig')
    anchor='game_field_busy=1;while(gap--)bl_c64_field();game_field_busy=0;'
    assert main.count(anchor)==1
    main=main.replace(anchor,'game_field_busy=1;while(gap--){bl_c64_field();source_audio_service();}game_field_busy=0;')
    (folder/'main.c').write_text(main,encoding='utf-8')
    builder=(ROOT/'.tmp/compact-delivery/math-build.ps1').read_text(encoding='utf-8-sig')
    builder=builder.replace("'.tmp/compact-delivery/math-main.c'","'reference/analysis/audio-service-2026-10-30/boundary/main.c'")
    (BASE/'boundary-build.ps1').write_text(builder,encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'boundary-scope.json').write_text(json.dumps(dict(status='private_complete_field_audio_poll_candidate',production_changed=False,
        change='Same precomputed game-field gap and same field calls; extra existing audio poll only after each complete field. Existing active/busy/same-field gates retained; no catch-up SID bursts.',
        inputs=[item(ROOT/p) for p in ['amiga/main.c','amiga/source_audio.h','core/c64_rooms.c','core/c64_actor_programs.h','.tmp/compact-delivery/math-main.c','.tmp/compact-delivery/math-build.ps1']],
        generated=[item(folder/'main.c'),item(BASE/'boundary-build.ps1')],
        limits=['Not integrated','Natural C64 IRQ/PC mapping remains open','Must measure cost, source/control results and missed ticks']),indent=2)+'\n')
    print('Generated complete-field audio-poll candidate; production unchanged')
if __name__=='__main__':main()
