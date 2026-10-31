"""Strict historical view: mapped files are the frozen preceding artifacts.

Every mapping is hash-checked. Unmapped files retain normal live validation;
original archives and C64 bytes are unchanged. This does not relabel old runs
as current runs. It replays the preceding stage's validator on its own files.
"""
import hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30/parent'
class FrozenView:
    def __init__(self,entries):self.files={e['path']:BASE/e['path'] for e in entries}
    def __fspath__(self):return os.fspath(ROOT)
    def __truediv__(self,p):return self.files.get(Path(p).as_posix(),ROOT/p)
def verify_parent():
    import verify_compact_actor_delivery as parent
    manifest=json.loads((BASE/'manifest.json').read_text())
    for e in manifest['files']:assert hashlib.sha256((BASE/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
    saved=parent.ROOT;flag=getattr(parent,'_audio_parent_replay',False)
    try:
        parent.ROOT=FrozenView(manifest['files']);parent._audio_parent_replay=True
        report=parent.verify()
        assert report==json.loads((BASE/'reference/validation/compact-actor-delivery.json').read_text())
    finally:parent.ROOT=saved;parent._audio_parent_replay=flag
    return report
if __name__=='__main__':verify_parent();print('PASS strict replay of frozen pre-audio delivery')
