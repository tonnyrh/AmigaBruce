"""Native C continuations for the frozen actor translation.

Preserves guest stack bytes and source guards. A full local continuation
array uses the original recursive C call. This is not guest opcode decode.
"""
import hashlib,re

def compact_actor_calls(program,source):
 original_hash=hashlib.sha256(program.encode('utf-8')).hexdigest()
 assert [l for l in program.splitlines() if 'entry' in l]==['static void actor_code(unsigned short entry){','switch(entry){','default:source_fault=entry;return;']
 # Every original labelled instruction assigns each C-only scratch local
 # before reading it. Nothing in these three locals survives a JSR.
 blocks=re.split(r'(?m)^L[0-9a-f]+:;[^\n]*\n',program)[1:]
 for b in blocks:
  for name in ['q','old','address']:
   m=re.search(r'\b'+name+r'\b',b)
   assert not m or re.match(r'\s*=',b[m.end():]),(name,b[:180])
 program=program.replace('unsigned short address;unsigned char q,old;','unsigned short address;unsigned char q,old;\nunsigned short native_calls[16],native_depth=0,native_id=0;\nNATIVE_TABLE_PLACEHOLDER')
 program=program.replace('return;','goto actor_native_unwind;')
 flags='transition_pending || actor_delay_pending || actor_gameover_pending || actor_reset_pending || actor_irq_stop || source_fault'
 pattern=re.compile(r'^m\[0x100 \+ sp--\]=0x([0-9a-f]+);m\[0x100 \+ sp--\]=0x([0-9a-f]+);actor_code\(0x([0-9a-f]+)\);if\('+re.escape(flags)+r' \|\| actor_return!=0x([0-9a-f]+)\)goto actor_native_unwind;',re.M)
 calls=[]
 def convert(m):
  hi,lo,target,ret=(int(q,16) for q in m.groups());assert ((((hi<<8)|lo)+1)&65535)==ret
  idx=len(calls);calls.append(dict(target=target,ret=ret,index=idx))
  return ('m[0x100 + sp--]=0x%02x;m[0x100 + sp--]=0x%02x;\n'%(hi,lo)+
   'if(native_depth==16){native_id=%d;goto actor_native_overflow;}\nnative_calls[native_depth++]=%d;goto L%04x;'%(idx,idx,target))
 program=pattern.sub(convert,program);assert len(calls)==444
 tables='static const unsigned short native_returns[444]={'+','.join('0x%04x'%r['ret'] for r in calls)+'};\n'
 tables+='static const unsigned short native_targets[444]={'+','.join('0x%04x'%r['target'] for r in calls)+'};'
 program=program.replace('NATIVE_TABLE_PLACEHOLDER',tables)
 assert program.endswith('}\n')
 tail='actor_native_overflow:;\nactor_code(native_targets[native_id]);\nif('+flags+' || actor_return!=native_returns[native_id])goto actor_native_unwind;\ngoto actor_native_resume;\n'
 tail+='actor_native_unwind:;\nwhile(native_depth){\nnative_id=native_calls[--native_depth];\nif('+flags+' || actor_return!=native_returns[native_id])continue;\ngoto actor_native_resume;\n}\nreturn;\nactor_native_resume:;\nswitch(native_id){\n'
 tail+=''.join('case %d:goto L%04x;\n'%(r['index'],r['ret']) for r in calls)
 tail+='default:source_fault=0xffff;return;\n}\n'
 program=program[:-2]+tail+'}\n'
 for row in calls:
  assert source[row['ret']-3:row['ret']]==bytes([32,row['target']&255,row['target']>>8]),row
 return program,dict(version=1,converted_jsrs=len(calls),native_capacity=16,
  original_program_sha256=original_hash,generated_program_sha256=hashlib.sha256(program.encode('utf-8')).hexdigest(),
  source_stack_stores_retained=True,source_return_guards_retained=True,
  overflow='Original recursive call and original return/error guards')
