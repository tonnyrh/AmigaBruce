"""Recover one nested prior proof only if its already-recorded SHA matches."""
import hashlib,json
from pathlib import Path
import audit_contact_kernel_images as comparator
from verify_loader_blank_delivery import FrozenView,BASE,ROOT
def main():
 parent=ROOT/BASE/'parent';manifest=json.loads((parent/'manifest.json').read_text())
 link=json.loads((parent/'reference/analysis/flat-control-compact-2026-10-30/delivery-kernels.json').read_text())
 relative='reference/analysis/flat-control-compact-2026-10-30/delivery-contact-kernels.json'
 expected=next(e['sha256'] for e in link['artifacts'] if e['path']==relative)
 old_native=json.loads((parent/'reference/validation/source-world-native.json').read_text())
 paths=['amiga/out/bruce_amiga.elf',next(e['path'] for e in old_native['build'] if e['path'].endswith('.elf')),
  'reference/analysis/optimization-2026-10-27/compact-call-r01/bruce_test.elf',
  'reference/analysis/flat-control-compact-2026-10-30/delivery-before/amiga/out/bruce_amiga.elf']
 saved=comparator.ROOT
 try:
  comparator.ROOT=FrozenView(manifest['files']);proof=comparator.verify(paths)
 finally:comparator.ROOT=saved
 text=json.dumps(proof,indent=2)+'\n';variants=[text.encode(),text.replace('\n','\r\n').encode()]
 data=next((b for b in variants if hashlib.sha256(b).hexdigest()==expected),None)
 assert data is not None,'Reconstructed report differs from the recorded original hash'
 dest=parent/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 if not any(e['path']==relative for e in manifest['files']):manifest['files'].append(dict(path=relative,sha256=expected))
 for e in link['artifacts']:
  if any(q['path']==e['path'] for q in manifest['files']):continue
  p=ROOT/e['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],e['path']
  dest=parent/e['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());manifest['files'].append(e)
 manifest['recoveries']=[dict(path=relative,sha256=expected,method='Unchanged original comparator replayed on frozen original images; exact previously recorded hash required. Added nested linked-proof inputs to historical archive; no gate relaxed.')]
 (parent/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS exact-hash recovery of prior nested contact proof',expected)
if __name__=='__main__':main()
