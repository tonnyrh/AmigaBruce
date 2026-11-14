"""Audit the actual candidate CIA slot against current native input buffers.
Fixed pins and explicit register/RAM states; not a natural IRQ/raster run.
Known mismatches are evidence to investigate, never accepted parity.
"""
import ctypes,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
SOURCE=ROOT/'.reference/c64/work/untrained-memory.bin'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
class Bus:
 def __init__(self,data):self.ram=list(data);self.writes=[]
 def __getitem__(self,k):return self.ram[k]
 def __setitem__(self,k,v):self.ram[k]=v;self.writes.append((k,v))
def decode(raw):
 return (0 if raw&4 else 1)|(0 if raw&8 else 2)|(0 if raw&1 else 4)|(0 if raw&2 else 8)|(0 if raw&16 else 16)
def full_irq_cases(lib):
 U=ctypes.c_ubyte;rows=[]
 class Pins(Bus):
  def __getitem__(self,address):
   if address==0xdc00:return self.pins[0]
   if address==0xdc01:return self.pins[1]
   value=self.ram[address]
   if address==0xd01e:self.ram[address]=0
   return value
 def category(address):
  if 0x153<=address<0x15f:return 'source_palette_buffer'
  if 0x100<=address<0x200:return 'source_stack_page'
  if address in [0xa,0xb,0xc,0xd]:return 'raster_palette_pointer_scratch'
  if address in [0x408,0x409] or 0x47f5<=address<0x47f9:return 'source_raster_schedule'
  if 0xd000<=address<0xe000:return 'modeled_hardware_registers'
  return 'other_requires_followup'
 for human,current,pins in itertools.product(range(2),range(2),[(31,31),(31,30),(15,31),(23,27)]):
  ram=(U*65536)();regs=(U*10)();out=(U*65536)();after_regs=(U*10)()
  lib.bl_irq_audit_prepare(human);lib.bl_irq_audit_copy(ram);lib.bl_irq_audit_regs(regs)
  assert (ram[0xfffe]|ram[0xffff]<<8)==0x1103
  assert (ram[0x408]|ram[0x409]<<8)==0x48c1
  ram[3]=current;ram[0x48]=3
  before=bytes(ram);bus=Pins(before);bus.pins=pins;cpu=MPU(memory=bus,pc=0x1c32)
  cpu.a,cpu.x,cpu.y,cpu.sp=regs[0],regs[1],regs[2],regs[8]
  cpu.p=0x20|regs[3]|regs[4]<<1|regs[7]<<3|regs[6]<<6|regs[5]<<7
  entry=(cpu.a,cpu.x,cpu.y,cpu.sp,cpu.p);cpu.irq();trace=[]
  for step in range(50000):
   if cpu.pc==0x1c32:break
   trace.append(cpu.pc);cpu.step()
  else:raise AssertionError(('Full IRQ did not return',hex(cpu.pc)))
  assert (cpu.a,cpu.x,cpu.y,cpu.sp,cpu.p&~0x10)==entry, (entry,(cpu.a,cpu.x,cpu.y,cpu.sp,cpu.p),human,current,pins)
  chosen=(pins[1],pins[0]) if not current else pins
  lib.bl_irq_audit_seed(ram,regs,decode(chosen[0]),decode(chosen[1]));lib.bl_irq_audit_field(1)
  lib.bl_irq_audit_copy(out);lib.bl_irq_audit_regs(after_regs)
  assert list(after_regs)==list(regs),'Native field changed caller context'
  diffs=[dict(address='$%04X'%i,before=before[i],source=bus.ram[i],native=out[i],category=category(i)) for i in range(65536) if bus.ram[i]!=out[i]]
  counts={}
  for diff in diffs:counts[diff['category']]=counts.get(diff['category'],0)+1
  rows.append(dict(human=human,current=current,cia_ports=list(pins),injected_pc='$1C32',hardware_irq_vector='$1103',raster_handler='$48C1',
   instructions=len(trace),trace=['$%04X'%pc for pc in trace],caller_context_restored=True,difference_categories=counts,differences=diffs))
 return dict(status='controlled_full_irq_differences_recorded_not_accepted',
  method='One MPU.irq() at explicit PC $1C32; actual $1103 vector and $48C1 handler through RTI, including original SID calls; fixed CIA pins and plain modeled VIC registers. Native audio+field comparison. No multi-raster PAL model or natural execution claim.',
  natural_playthrough=False,original_raster_phase_verified=False,cases=rows)
def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA
 lib=ctypes.CDLL(str(ROOT/'.tmp/source-irq-audit/audit.dll'))
 U=ctypes.c_ubyte;P=ctypes.POINTER(U)
 lib.bl_irq_audit_prepare.argtypes=[ctypes.c_long];lib.bl_irq_audit_seed.argtypes=[P,P,ctypes.c_long,ctypes.c_long]
 lib.bl_irq_audit_field.argtypes=[ctypes.c_long];lib.bl_irq_audit_copy.argtypes=[P];lib.bl_irq_audit_regs.argtypes=[P];lib.bl_irq_audit_inputs.argtypes=[P]
 ram=(U*65536)();regs=(U*10)();inputs=(U*4)()
 lib.bl_irq_audit_prepare(0);lib.bl_irq_audit_copy(ram);lib.bl_irq_audit_regs(regs)
 bus=Bus(bytes(ram))
 assert bytes(bus.ram[0x169d:0x1703])==SOURCE.read_bytes()[0x169d:0x1703]
 assert bus.ram[0x4a85:0x4a89]==[0,8,4,12]
 cpu=MPU(memory=bus,pc=0x169d);dis=Disassembler(cpu)
 out=ROOT/'reference/analysis/irq-input-2026-10-30';out.mkdir(parents=True,exist_ok=True)
 lines=[];pc=0x169d
 while pc<0x1703:
  n,text=dis.instruction_at(pc);lines.append('$%04X '%pc+text);pc+=n
 (out/'cia-slot.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 counts={};first={};cases=steps=0
 for active,current,human,flag0,flag1 in itertools.product(range(2),repeat=5):
  key='active%d/player%d/human%d/flags%d%d'%(active,current,human,flag0,flag1)
  matches=0
  for port0,port1 in itertools.product(range(32),repeat=2):
   values={0x104:active,3:current,0x42ca:human,0x1383:flag0,0x1384:flag1,
    0xdc00:port0,0xdc01:port1,0x98:10,0x9b:1,0x99:5,0x9c:0,0x7f:1,0x82:0,0x89:0,0x8a:0,2:50}
   for address,value in values.items():ram[address]=value;bus.ram[address]=value
   cpu.pc=0x169d;cpu.a=0x35;cpu.x=0x72;cpu.y=0x91;cpu.p=0x24;cpu.sp=0xed;bus.writes=[]
   for n in range(100):
    if cpu.pc==0x1703:break
    cpu.step();steps+=1
   else:raise AssertionError(('CIA slot escaped',hex(cpu.pc)))
   assert all(address in [0x98,0x99,0x9b,0x9c] or 0x100<=address<0x200 for address,_ in bus.writes)
   source=[bus.ram[a] for a in [0x98,0x9b,0x99,0x9c]]
   chosen=(port1,port0) if not current else (port0,port1)
   lib.bl_irq_audit_seed(ram,regs,decode(chosen[0]),decode(chosen[1]));lib.bl_irq_audit_field(0);lib.bl_irq_audit_inputs(inputs)
   native=list(inputs);cases+=1
   if native==source:matches+=1
   elif key not in first:first[key]=dict(port0=port0,port1=port1,source=source,native=native)
  counts[key]=dict(cases=1024,matches=matches,mismatches=1024-matches)
  assert matches==1024,(key,first.get(key))
 report=dict(status='all_input_buffer_cases_match_full_irq_phase_open',source_sha256=SHA,edition_verified=False,
  natural_playthrough=False,original_raster_phase_verified=False,scope='Original $169D-$1702 input slot, controlled fixed CIA values; native full field comparison restricted to $98/$9B/$99/$9C; no full IRQ stack or raster scheduling claim',
  cases=cases,instructions=steps,configs=counts,first_mismatches=first,
  source_findings=['$0104=0 branches directly to $1703 and preserves all four input buffers',
   '$03 selects active controller, $42CA gates the other controller',
   '$1383/X flag zero selects the $4A85 direction conversion; its device meaning is not inferred'],
  native_findings=['The game field retains the input buffers when $0104 is zero',
   'Both active player selections and $1383 controller conversions match in all 32768 cases'],
  unresolved=['Reachability of non-default selector flags in the exposed Amiga UI',
   'Full hardware IRQ stack, caller PC, palette/raster prologue and actual physical input phase'],
  source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in ['core/c64_rooms.c','tests/source_irq_audit_bridge.c','tools/audit_c64_irq_contract.py']])
 full=full_irq_cases(lib)
 (out/'full-irq.json').write_text(json.dumps(full,indent=2)+'\n',encoding='utf-8')
 report['controlled_full_irq_cases']=len(full['cases'])
 report['controlled_full_irq_sha256']=hashlib.sha256((out/'full-irq.json').read_bytes()).hexdigest()
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['configs','first_mismatches','source_files']},indent=2))
 print('mismatching input cases:',sum(v['mismatches'] for v in counts.values()))
if __name__=='__main__':main()
