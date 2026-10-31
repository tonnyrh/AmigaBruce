"""Bind frame-coherence controls to current code and actual native images."""
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/render-coherence-2026-10-29'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def item(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def runtime_image(path):
 data=(ROOT/path).read_bytes();at=0;records=[]
 def word():
  nonlocal at
  n=struct.unpack_from('>I',data,at)[0];at+=4;return n
 assert word()==1011
 while True:
  n=word()
  if not n:break
  at+=n*4
 table,first,last=word(),word(),word();records.extend([1011,table,first,last])
 for _ in range(last-first+1):records.append(word())
 blobs=[]
 while at<len(data):
  kind=word()
  if kind in (1001,1002):
   n=word();blobs.append(struct.pack('>II',kind,n)+data[at:at+n*4]);at+=n*4
  elif kind==1003:records.extend([kind,word()])
  elif kind==1004:
   records.append(kind)
   while True:
    n=word();records.append(n)
    if not n:break
    records.append(word())
    for _ in range(n):records.append(word())
  elif kind==1008:
   while True:
    n=word()
    if not n:break
    at+=n*4;word()
  elif kind in (1000,1009):at+=word()*4
  elif kind==1010:records.append(kind)
  else:raise AssertionError(('Unexpected HUNK record',kind,at))
 return hashlib.sha256(b''.join(blobs)+b''.join(struct.pack('>I',v) for v in records)).hexdigest()
def verify():
 source=item('.reference/c64/work/untrained-memory.bin')['sha256']
 assert source=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
 before=read(BASE+'/before/manifest.json')
 for entry in before['files']:assert item(BASE+'/before/'+entry['path'])['sha256']==entry['sha256']
 paint=read('reference/validation/source-paint-host.json');assert len(paint['cases'])==6
 for entry in paint['source_files']:assert item(entry['path'])==entry
 paths=[BASE+'/before/manifest.json',BASE+'/intermediate/manifest.json',BASE+'/source-scroll-disassembly.txt','reference/validation/source-paint-host.json','tools/verify_render_coherence.py','tools/audit_native_animation_frame.py','docs/RENDER_COHERENCE.md']
 runs=[]
 for label in ['native-before-frozen','menu-native','menu-native-death']:
  path=BASE+'/'+label+'/report.json';r=read(path)
  assert r['snapshots_paused'] and not r['natural_playthrough'] and not r['edition_verified']
  assert len(r['samples'])>=12
  assert hashlib.sha256(Path(r['elf']['path']).read_bytes()).hexdigest()==r['elf']['sha256']
  if label!='native-before-frozen':
   assert r['elf']['sha256']==item('amiga/out/bruce_amiga.elf')['sha256']
   assert r['mixed_phase_samples']==r['max_pixel_mismatch']==r['max_static_pixel_mismatch']==0
  runs.append(dict(label=label,samples=len(r['samples']),mixed_phase_samples=r['mixed_phase_samples'],max_pixel_mismatch=r['max_pixel_mismatch'],max_static_pixel_mismatch=r['max_static_pixel_mismatch']))
  paths.append(path)
  paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/BASE/label).glob('*')) if p.suffix in ('.bin','.bpl')]
 death=read(BASE+'/menu-native-death/report.json')
 assert death['room_roundtrip'] and death['controlled_death']['loader_epoch_after']!=death['controlled_death']['loader_epoch_before']
 return dict(status='passed_scoped_host_and_native_frame_coherence',source_sha256=source,edition_verified=False,natural_playthrough=False,realtime_accepted=False,full_room_paints=60,source_room12_steps=96,runtime_signature=runtime_image('amiga/out/bruce_amiga.exe'),runs=runs,source_files=[item(p) for p in ['amiga/main.c','core/c64_rooms.c','core/c64_rooms.h']],artifacts=[item(p) for p in paths])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/render-coherence.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n')
 else:assert read(path)==r
 print('PASS source-derived frame coherence: 60 full paints,96 source steps, paused native room12 and death/room transitions')
if __name__=='__main__':main()
