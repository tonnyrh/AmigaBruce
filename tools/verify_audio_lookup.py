"""Differential host audit of the Amiga SID-to-Paula lookup only.
The source SID drivers are untouched; this does not certify SID emulation.
"""
import argparse,ctypes,hashlib,itertools,json,re,random,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-lookup-2026-10-30'
class State(ctypes.Structure):
 _fields_=[('level',ctypes.c_ulong*3),('phase',ctypes.c_ubyte*3),('gate',ctypes.c_ubyte*3),('music_regs',ctypes.c_ubyte*26),('music_wait',ctypes.c_ubyte),('music_cursor',ctypes.c_ushort)]
class Voice(ctypes.Structure):
 _fields_=[('offset',ctypes.c_ushort),('length',ctypes.c_ushort),('period',ctypes.c_ushort),('volume',ctypes.c_ushort)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',default='candidate');args=parser.parse_args()
 assert args.candidate in ['candidate','candidate2']
 libs=[ctypes.CDLL(str(ROOT/'.tmp/audio-lookup-test'/v/'audio.dll')) for v in ['before',args.candidate]]
 states=[State(),State()];voices=[(Voice*3)(),(Voice*3)()]
 for lib in libs:
  lib.bl_source_audio_render.argtypes=[ctypes.POINTER(State),ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(Voice)]
  lib.bl_source_audio_faults.restype=ctypes.c_ushort
  lib.bl_source_audio_reset.argtypes=[ctypes.POINTER(State)]
  lib.bl_source_audio_reset(ctypes.byref(states[libs.index(lib)]))
 data=(ROOT/'core/source_audio_data.h').read_text(encoding='utf-8-sig')
 def table(name):
  body=re.search(r'static const unsigned short '+name+r'\[\]\[\d+\]=\{(.*?)\};',data)[1]
  return [tuple(map(int,re.findall(r'\d+',row))) for row in re.findall(r'\{([^}]+)\}',body)]
 waves=table('bl_source_waves');freq=table('bl_source_frequencies')
 assert [x[:3] for x in waves]==sorted(set(x[:3] for x in waves))
 representative={row[2]:row[0] for row in freq}
 assert set(representative)=={8,16,32}
 rng=random.Random(20261030);regs=(ctypes.c_ubyte*26)();cases=0
 def check(fn,wave,width):
  nonlocal cases
  for v in range(3):
   regs[v*7]=fn&255;regs[v*7+1]=fn>>8;regs[v*7+2]=width&255;regs[v*7+3]=width>>8
   regs[v*7+4]=wave|(rng.randrange(2))|(8 if cases%37==0 else 0)
   regs[v*7+5]=rng.randrange(256);regs[v*7+6]=rng.randrange(256)
  regs[24]=rng.randrange(256);regs[23]=rng.randrange(256);regs[25]=rng.randrange(8)
  # Carry envelope state between calls, covering retrigger/attack/release.
  for lib,state,out in zip(libs,states,voices):lib.bl_source_audio_render(ctypes.byref(state),regs,out)
  assert bytes(states[0])==bytes(states[1]),(cases,fn,wave,width,'state')
  assert bytes(voices[0])==bytes(voices[1]),(cases,fn,wave,width,'voices')
  assert libs[0].bl_source_audio_faults()==libs[1].bl_source_audio_faults(),(cases,'faults')
  cases+=1
 for fn in representative.values():
  for wave in range(0,256,16):
   for width in range(4096):check(fn,wave,width)
 for row in freq:
  for wave,width,length,offset in waves:check(row[0],wave,width)
 for fn in [0,1,65535]:
  for wave,width,length,offset in waves:check(fn,wave,width)
 # Interleave independent envelope instances; the global validated hint
 # must not become a second source of audio state or retain reset state.
 pools=[states,[State(),State()]]
 for lib,state in zip(libs,pools[1]):lib.bl_source_audio_reset(ctypes.byref(state))
 for case in range(10000):
  states=pools[case&1]
  if case%113==0:
   for lib,state in zip(libs,states):lib.bl_source_audio_reset(ctypes.byref(state))
  wave,width,length,offset=waves[rng.randrange(len(waves))]
  check(freq[rng.randrange(len(freq))][0],wave,width)
 files=['core/source_audio_data.h','core/source_audio.c','tools/verify_audio_lookup.py','test-audio-lookup.ps1']
 report=dict(status='passed_exact_existing_renderer_equivalence',cases=cases,sorted_wave_keys=len(waves),frequency_keys=len(freq),source_sid_logic_changed=False,natural_playthrough=False,
  files=[dict(path=name,sha256=sha(ROOT/name)) for name in files],candidate_sha256=sha(BASE/args.candidate/'source_audio.c'))
 (BASE/('host-'+args.candidate+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
