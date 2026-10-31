"""ELF2Hunk starts the first CODE hunk; reject a displaced main entry."""
import sys
from pathlib import Path
from capture_paula_stream import elf_symbols

def verify(path):
    _,symbols=elf_symbols(Path(path))
    assert symbols['main']==0 or symbols['_start']==0, 'First CODE hunk would start a different function: main='+hex(symbols['main'])+', _start='+hex(symbols['_start'])
    print('PASS AmigaDOS CODE entry:', 'main' if symbols['main']==0 else '_start')
if __name__=='__main__':verify(sys.argv[1])
