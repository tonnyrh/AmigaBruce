"""Check every fixed DMA byte against the frozen renderer's waveform bank.

This validates RAM projection/cache only, not a model of OCS fetch timing.
"""
import ctypes
import hashlib
import json
from verify_source_audio import ROOT, SHA, State, Voice


class Dma(ctypes.Structure):
    _fields_=[('offset',ctypes.c_ushort*3),('length',ctypes.c_ushort*3)]


def main():
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-dma-test/dma.dll'))
    lib.bl_source_dma_update.restype=ctypes.c_ushort
    lib.bl_source_dma_update.argtypes=[ctypes.POINTER(Dma),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(Voice)]
    bank_bytes=(ROOT/'assets/audio/c64-equivalent-v1/waveforms.pcm').read_bytes()
    bank=(ctypes.c_ubyte*len(bank_bytes)).from_buffer_copy(bank_bytes)
    images=(ctypes.c_ulong*(3072//4))();data=json.loads((ROOT/'assets/audio/c64-equivalent-v1/source-registers.json').read_text())
    rows=data['music']+[r for effect in data['effects'] for r in effect]
    state=State();dma=Dma();voices=(Voice*3)();count=0;changes=0
    lib.bl_source_audio_reset(ctypes.byref(state));lib.bl_source_dma_reset(ctypes.byref(dma))
    for row in rows:
        previous=bytes(images)
        lib.bl_source_audio_render(ctypes.byref(state),(ctypes.c_ubyte*26)(*row),voices)
        result=lib.bl_source_dma_update(ctypes.byref(dma),images,bank,len(bank_bytes),voices)
        assert not result&0x8000
        changes+=result.bit_count()
        actual=bytes(images)
        for c,v in enumerate(voices):
            expected=(bank_bytes[v.offset:v.offset+v.length]*(1024//v.length)
                      if v.volume else previous[c*1024:(c+1)*1024])
            assert actual[c*1024:(c+1)*1024]==expected,(count,c)
        assert lib.bl_source_dma_update(ctypes.byref(dma),images,bank,len(bank_bytes),voices)==0
        count+=1
    assert not lib.bl_source_audio_faults()
    for length,offset in ((0,0),(6,0),(2048,0),(8,2),(8,len(bank_bytes))):
        voices[0].length=length;voices[0].offset=offset
        assert lib.bl_source_dma_update(ctypes.byref(dma),images,bank,len(bank_bytes),voices)==0x8000
    files=['core/source_dma.c','core/source_dma.h','core/source_audio.c','core/source_audio.h','core/source_audio_data.h',
           'assets/audio/c64-equivalent-v1/waveforms.pcm','assets/audio/c64-equivalent-v1/source-registers.json',
           'tools/verify_source_dma.py','test-source-dma.ps1']
    report=dict(status='verified_fixed_dma_ram_projection',source_sha256=SHA,fields=count,channel_images=count*3,
        bytes_checked=count*3072,wave_changes=changes,invalid_cases=5,dma_bytes=3072,native_fetch_timing_verified=False,
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-dma-host.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {count} fields/{count*3} fixed DMA images; byte comparison and cache/invalid cases')


if __name__=='__main__':main()
