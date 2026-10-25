"""Check fall-contact instruction sites in the registered snapshot, read-only."""
import hashlib,json,argparse
from pathlib import Path
from vice_binary import Vice
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect(port):
 m=json.loads((ROOT/'reference/manifest.json').read_text());a=m['analysis_candidate'];p=ROOT/a['baseline_snapshot_path']
 assert sha(p)==a['baseline_snapshot_sha256']
 assert sha(ROOT/m['emulator']['executable_path'])==m['emulator']['executable_sha256']
 v=Vice(port)
 try:
  assert v.restore(p)==0x1bce
  checks={0x2afa:'b5a138f9a100c90a',0x2b06:'b9454f',0x2c0c:'b5d138e90595d1',0x15c2:'a9028d454f8d464f8d474f'}
  for address,hex_value in checks.items():
   expected=bytes.fromhex(hex_value);assert v.memory(address,address+len(expected)-1)==expected
  regions=[{'start':start,'end':end,'sha256':hashlib.sha256(v.memory(start,end)).hexdigest()} for start,end in ((0x15c2,0x15cc),(0x29c3,0x2c23))]
  report={'status':'static_instruction_sites_verified_in_registered_snapshot','primary_edition_verified':False,'runtime_fall_hit_observed':False,'snapshot_sha256':sha(p),'regions':regions,'checks_passed':True,'facts':['Falling-attacker branch compares victim minus attacker feet with ten','Contact allowance at $4F45,Y is read before registering falling contact','Fall-contact damage path subtracts five from $D1,X','IRQ refresh loads two into three actor contact allowances'],'source_files':[{'path':n,'sha256':sha(ROOT/n)} for n in ('tools/inspect_c64_contact.py','tools/vice_binary.py','inspect-c64-contact.ps1')]}
  (ROOT/'reference/validation/candidate-fall-contact-code.json').write_text(json.dumps(report,indent=2)+'\n')
  print('PASS: four contact-rule instruction sites match registered snapshot')
 finally:v.close(False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=6517);inspect(p.parse_args().port)
