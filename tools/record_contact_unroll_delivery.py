"""Record the tested, assembly-only contact alignment optimization."""
import hashlib,json
from pathlib import Path
from verify_contact_unroll_delivery import verify_current
ROOT=Path(__file__).resolve().parents[1]
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    r=verify_current();target='reference/validation/contact-unroll.json'
    report=dict(date='2026-10-31',status='passed_scoped_native_contact_alignment_unroll',source_sha256=r['source_sha256'],
      normal_build=r['normal_build'],contact_unroll=r['contact_unroll'],largest_chip_block=r['largest_chip_block'],
      edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,limitations=r['open_gates'],artifacts=r['artifacts']+[item('tools/record_contact_unroll_delivery.py')])
    (ROOT/target).write_text(json.dumps(report,indent=2)+'\n')
    evidence=dict(id='CONTACT-UNROLL-0001',date='2026-10-31',status='unchanged_source_rule_native_implementation_optimized',source_sha256=r['source_sha256'],source_addresses=['$52AD-$5309'],
      source_condition='Prefix clear, phase3 extra32-byte clear, ordered96-byte copy, then phase-specific shifts; C64 rule and native alias guards unchanged.',
      amiga_effect='Unroll fixed clear/copy loops only; +296 CODE bytes, no extra buffers, same RAM access order and service boundaries.',
      controls=dict(fresh_native_fixtures=53,fresh_native_loops=1200,separate_native_reference_cases=710,align_cases_per_reference_image=256),
      edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,artifacts=[item(target),item('reference/validation/source-world-delivery.json')],limitations=r['open_gates'])
    (ROOT/'docs/parity/evidence/CONTACT-UNROLL-0001.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('PASS recorded bounded contact alignment optimization')
if __name__=='__main__':main()
