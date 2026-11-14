"""Exercise the normal game on a dedicated WinUAE instance already at the menu.

Tests real keyboard input and displayed bitplanes. Deaths are injected at
the source death counter so the transition can be repeated deterministically.
"""
import argparse
import hashlib
import json
import re
import struct
import time
from pathlib import Path
from build_title_art import ROOT, COLORS
from capture_paula_stream import elf_symbols
from title_reference import notice_reference, reference
from winuae_ipc import command
from PIL import Image


def check(pid, log, out, boot):
    out.mkdir(parents=True,exist_ok=True)
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",log.read_text(errors='replace'))[-1]
    def cmd(s):
        return command(pipe,s,expected_pid=pid)
    def read(at,n):
        reply=cmd(f'DBG m {at:x} {(n+15)//16:x}')
        lines=re.findall(r'^[\da-fA-F]{8}\s+((?:[\da-fA-F]{4}\s+){1,8})',reply,re.M)
        data=b''.join(bytes.fromhex(line) for line in lines)
        assert len(data)>=n,(hex(at),n,reply)
        return data[:n]
    def num(at,n):
        return int.from_bytes(read(at,n),'big')
    def dump(name,at,n):
        p=out/name
        assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {n:x}')
        return p.read_bytes()
    def capture():
        cop=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',cmd('DBG c'))[1],16)
        words=struct.unpack('>66H',dump('copper.bin',cop,132))
        if words[0]!=0x100 or words[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):
            return 0,(),b''
        front=words[19]*65536+words[21]
        if not front or front+40960>524288:return 0,(),b''
        return words[1],words[35:66:2],dump('front.bpl',front,40960)
    def key(name,down):
        cmd(f'EVT KEY_{name} {int(down)}')
    def tap(name):
        key(name,True);time.sleep(.32);key(name,False)
    def until(test,label,seconds=45):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            result=test()
            if result:return result
            time.sleep(.08)
        raise AssertionError(label)
    def menu(**options):
        want=reference(**options)
        until(lambda: capture()==(0x4200,COLORS,want),f'menu {options}')
        if not options:(out/'menu.bpl').write_bytes(want)
    def preview(name,bitmap):
        image=Image.new('P',(320,256))
        image.putpalette([((c>>s)&15)*17 for c in COLORS for s in (8,4,0)]+[0]*720)
        image.putdata([sum(1<<p for p in range(4) if bitmap[160*y+40*p+x//8]&(128>>(x&7)))
                       for y in range(256) for x in range(320)])
        image.resize((640,512),Image.Resampling.NEAREST).save(out/(name+'.png'))
    if boot:
        loading=reference(loading=True);normal=reference();seen_loading=False
        def startup():
            nonlocal seen_loading
            try:
                control,palette,bitmap=capture()
            except TimeoutError:  # WinUAE can open IPC before the chipset is running.
                return False
            if control!=0x4200 or palette!=COLORS:return False
            if not seen_loading and bitmap==loading:
                preview('loading',bitmap);seen_loading=True
            return bitmap==normal
        until(startup,'title boot',150)
        preview('menu',normal)
    task=num(num(4,4)+276,4);cli=num(task+172,4)*4;node=num(cli+60,4)*4;hunks=[]
    while node:
        hunks.append(node+4);node=num(node,4)*4
        assert len(hunks)<=4
    assert len(hunks)==4
    bss,symbols=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
    def addr(name):
        return hunks[3]+symbols[name]-bss
    m=addr('m')
    def stat(name,n=1):
        return num(addr(name),n)
    def start():
        tap('RETURN')
        until(lambda:stat('game_field_active') and stat('actor_logic_steps',2)>2,'game start')
    def stable_pause():
        key('P',True)
        until(lambda:not stat('source_audio_active'),'P did not pause')
        # Hold the key, then release it. Neither action may advance the game.
        frozen=dump('paused-ram.bin',m,65536);steps=stat('actor_logic_steps',2)
        time.sleep(1.1);key('P',False);time.sleep(.3)
        assert dump('paused-ram.bin',m,65536)==frozen and stat('actor_logic_steps',2)==steps
        assert not stat('source_audio_active')
        return steps
    lists=[num(addr('copper')+4*i,4) for i in range(2)]
    menu()
    tap('F3');menu(players=2)
    tap('F5');menu(players=2,human=True);tap('F5');menu(players=2)
    key('SHIFT_LEFT',True);tap('D');key('SHIFT_LEFT',False);menu(debug=True)
    tap('F10');menu(debug=True,room=1,room_select=True);tap('F3');menu(debug=True)
    tap('F5');menu(players=2)
    def death(last_life,kind,players):
        old_epoch=stat('actor_loading_epoch',2)
        old_steps=stat('actor_logic_steps',2)
        # Limit the injection to the owned instance and the victim's state.
        cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.08)
        try:
            if last_life:
                cmd(f'DBG W {m+0x28:x} 00')
                cmd(f'DBG W {m+0x439f:x} ff') # No reserve turn for the other player.
            for at,value in [(0xd1,255),(0xbf,25),(0xce,1)]:
                cmd(f'DBG W {m+at:x} {value:02x}')
        finally:
            cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0')
        until(lambda:stat('interlude')==kind,'transition did not start')
        # Sample both lists as soon as we see the source's DEN-off event.
        # If the new card was already published it is checked below.
        if not stat('interlude_painted'):
            if not stat('interlude_painted') and any(num(at+2,2) for at in lists):
                assert stat('interlude_painted'), 'visible room while announcement is being prepared'
        until(lambda:stat('interlude_painted')!=0,'announcement not published')
        control,_,bitmap=capture()
        assert control==0x4200
        assert bitmap==notice_reference('GAME OVER' if last_life else f'PLAYER {players}')
        (out/('game-over.bpl' if last_life else f'player-turn-{players}p.bpl')).write_bytes(bitmap)
        if not last_life:
            until(lambda:stat('actor_loading_epoch',2)!=old_epoch and not stat('interlude'),'respawn')
            until(lambda:capture()[0]==0x4200 and stat('actor_logic_steps',2)>old_steps+3,'room visible')
        else:
            until(lambda:not stat('game_field_active'),'game over to menu',90)
            menu(players=players,game_over=True)

    start()
    steps=stable_pause();tap('P')
    until(lambda:stat('actor_logic_steps',2)>steps and stat('source_audio_active'),'resume')
    assert not stat('source_fault',2)
    death(False,2,2)
    death(True,3,2)
    start();stable_pause();tap('F10');menu(players=2)
    tap('F3');menu();start();death(False,2,1);tap('F10');menu()
    start();stable_pause();tap('ESC')
    def exited():
        cop=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',cmd('DBG c'))[1],16)
        return cop not in lists
    until(exited,'Esc did not restore the OS display')
    if boot and not seen_loading:
        time.sleep(1)
        for char in 'START':tap(char)
        tap('RETURN')
        until(startup,'AmigaDOS restart',120)
        assert seen_loading,'No complete loading screen observed on CLI restart'
    report={'exe_sha256':hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest(),
            'menu_controls':True,'paused_64k_unchanged':True,'resume':True,
            'one_player_respawn':True,'two_player_turn':True,'game_over':True,'pause_to_menu':True,
            'pause_to_os':True,'natural_playthrough':False,
            'complete_transition_images':['PLAYER 1','PLAYER 2','GAME OVER'],
            'source_sha256':hashlib.sha256((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()).hexdigest(),
            'adf_sha256':hashlib.sha256((ROOT/'amiga/out/bruce_amiga.adf').read_bytes()).hexdigest(),
            'loading_and_menu_exact':bool(boot)}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS keyboard pause, source RAM freeze, resume, two-player death, Game Over and F10')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--boot',action='store_true',help='Attach at boot and verify both title screens')
    args=p.parse_args();check(args.pid,args.log,args.out.resolve(),args.boot)
