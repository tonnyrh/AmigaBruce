"""Read actual HUNK placement and task stack bounds in an owned normal build.
No source-memory writes; sampled USP is not a full call-chain high-water mark.
"""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from audit_vic_native_kernels import sections
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
 def cmd(q):return command(pipe,q,expected_pid=a.pid)
 def read(at,n):
  s=cmd('DBG m %x %x'%(at,(n+15)//16));data=bytearray()
  for line in s.splitlines():
   m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
   if m:data.extend(bytes.fromhex(m[1]))
  assert len(data)>=n,(hex(at),s);return bytes(data[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 obj=ROOT/'.tmp/native-layout/offsets.o';data,ss=sections(obj);q=next(q for name,q in ss if name=='.rodata.br_mem_offsets');offsets=struct.unpack('>10I',data[q[4]:q[4]+q[5]])
 assert offsets[:4]==(276,54,58,62) and offsets[7]==172,offsets
 def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.1)
 pause()
 try:
  registers=cmd('DBG r');usp=int(re.search(r'USP\s+([0-9A-Fa-f]+)',registers)[1],16)
  task=long(long(4)+offsets[0]);saved_sp=long(task+offsets[1]);lower=long(task+offsets[2]);upper=long(task+offsets[3]);covers=lower<=usp<upper
  process_stack=dict(size=long(task+offsets[4]),high_end_bptr=long(task+offsets[5]),previous_frame=hex(long(task+offsets[6])))
  cli=long(task+offsets[7])*4;process_stack['cli_default_stack_words']=long(cli+offsets[8]);node=long(cli+60)*4;hunks=[]
  while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
  assert len(hunks)==4
 finally:pause()
 elf=ROOT/'amiga/out/bruce_amiga.elf';raw,ss=sections(elf);bss,symbols=elf_symbols(elf)
 sections_by_name=dict(ss);order=['.text','.rodata','.data','.bss']
 def memory(at):return 'slow' if 0xc00000<=at<0xc80000 else 'chip' if 0<=at<0x80000 else 'other'
 mapped=[]
 for i,name in enumerate(order):
  q=sections_by_name[name];mapped.append(dict(section=name,bytes=q[5],address=hex(hunks[i]),memory=memory(hunks[i])))
 objects={}
 for name in ['m','character_cache','constant_masks','vic_bytes','source_audio','actor_seed_packed','bl_source_frequencies','bl_source_waves','source_actor_field','source_final_colors']:
  if name not in symbols:continue
  value=symbols[name];i=next(i for i,label in enumerate(order) if sections_by_name[label][3]<=value<sections_by_name[label][3]+sections_by_name[label][5]);address=hunks[i]+value-sections_by_name[order[i]][3]
  objects[name]=dict(address=hex(address),memory=memory(address),section=order[i])
 report=dict(status='mapped_owned_native_memory'+('' if covers else '_task_stack_bounds_do_not_cover_usp'),method='Paused read-only KS1.3 CLI HUNK chain, ELF symbol/section offsets and SDK-compiled Exec/Task offsets; no source-memory mutation',normal_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),sections=mapped,objects=objects,
  stack=dict(lower=hex(lower),upper=hex(upper),reported_span=upper-lower,sampled_usp=hex(usp),sampled_unused_below_usp=(usp-lower if covers else None),task_bounds_cover_current_usp=covers,process_fields=process_stack,saved_task_sp=hex(saved_sp),full_call_chain_high_water_verified=False),
  sdk_offsets=dict(this_task=offsets[0],saved_sp=offsets[1],lower=offsets[2],upper=offsets[3],object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest()),physical_a500=False,realtime_accepted=False)
 out=ROOT/'reference/analysis/native-memory-2026-10-30';out.mkdir(parents=True,exist_ok=True);(out/(a.label+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
