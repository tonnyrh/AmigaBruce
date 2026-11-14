"""Offline integration checks: artist PNG -> real packed game data.

No test writes production masters or calls a billed image service.
"""
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import bruce_editor_data as ed
import bruce_editor_ai as ai
from build_enhanced_art import compile_art
from build_fighter_dma import unpack


def bank(header,name):
    return bytes(map(int,re.findall(r'\d+',re.search(name+r'\[\][^=]*=\{([^}]+)\}',header)[1])))

def stamp_bank(header):
    pairs=bank(header,'enhanced_arch_pairs')
    offsets=list(map(int,re.search(r'enhanced_pair_offsets\[\]=\{([^}]+)\}',header)[1].split(',')))
    return bytes(pairs[offsets[at+y//2]+p*2+y%2]
                 for at in range(0,len(offsets),4) for p in range(6) for y in range(8))


def fighter(header,kind,slot,face):
    from enhanced_enemies import reference_pose, source_shape
    def table(name):
        entries=re.search(name+r'\[\]=\{(.*?)\};',header,re.S)[1]
        return [tuple(map(int,row.split(','))) for row in re.findall(r'\{([\d,]+)\}',entries)]
    if kind==2:
        words,x0,y0,_,_=table('enhanced_bruce_views')[slot*2+face]
    else:
        pose=reference_pose(kind,slot,face)
        lookup='enhanced_alt_run_words' if slot in (3,4) else 'enhanced_npc_words'
        numbers=list(map(int,re.search(lookup+r'\[\]=\{([^}]+)\}',header)[1].strip().split(',')))
        words=numbers[(kind*2+face)*4+pose//2-7 if slot in (3,4) else (kind*2+face)*35+pose//2]
        (x0,y0,_,_),_=source_shape(kind,pose,face)
    start,_,w,h=next(b for b in table('enhanced_blocks') if b[1]==words)
    raw=unpack(bank(header,'enhanced_packed'))
    out=[ed.ALPHA]*1008
    for y in range(h):
        for x in range(w):
            byte=raw[start+y*((w+1)//2)+x//2];v=byte&15 if x%2 else byte>>4
            out[(y0+y)*48+x0+x]=ed.ALPHA if v==15 else v
    return out


class EditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.by_key={a.key:a for a in ed.catalog()}

    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.edits=self.root/'edits';self.history=self.root/'history'

    def store(self,asset,old=None):
        pixels=list(asset.pixels);i=next(i for i,v in enumerate(pixels) if v not in (ed.ALPHA,0))
        pixels[i]=0  # opaque black, never an erase
        raw=ed.save(asset,pixels,old,directory=self.edits,history=self.history)
        return pixels,raw

    def test_left_fighter_stamp_and_wall_reach_real_packer(self):
        baseline,_,report0=compile_art(None)
        self.assertEqual(baseline,compile_art(self.edits)[0])
        kage=self.by_key['fighter-1-00-0'];left,_=self.store(kage)
        bruce=self.by_key['fighter-2-08-0'];punch,_=self.store(bruce)
        wall=self.by_key['wall-warm'];masonry=list(wall.pixels);masonry[0]=15
        ed.save(wall,masonry,None,directory=self.edits,history=self.history)
        stamp=next(a for a in self.by_key.values() if a.group=='Structures' and ed.ALPHA in a.pixels and any(0<v<16 for v in a.pixels))
        ink,_=self.store(stamp)
        header,_,report=compile_art(self.edits)
        self.assertEqual(fighter(header,1,0,0),left)
        self.assertEqual(fighter(header,2,8,0),punch)
        self.assertEqual(fighter(header,1,0,1),fighter(baseline,1,0,1))
        self.assertEqual(fighter(header,2,8,1),fighter(baseline,2,8,1))
        self.assertLessEqual(report['actor_bytes']+report['tile_bytes'],73680)
        self.assertEqual(report['tile_bytes'],report0['tile_bytes'])
        tiles=bank(header,'enhanced_wall_tiles')
        wall_bytes=b''.join(tiles[i*32:i*32+32] for i in bank(header,'enhanced_wall_map')[32:])
        self.assertEqual(ed.planar_pixels(64,32,wall_bytes),masonry)
        i=(int(stamp.key.split('-')[1])-1)*48
        normalized=stamp_bank(header)[i:i+48]
        self.assertEqual(normalized[:16],stamp_bank(baseline)[i:i+16])
        self.assertEqual(list(ed.stamp_asset(i//48+1,normalized).pixels),ink)

    def test_bomb_frames_and_restored_floor_in_both_charsets(self):
        from enhanced_architecture import stamps
        header,_,_=compile_art(None)
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        self.assertEqual(art,stamps((ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes())[1])
        for group,floor,deck in ((1,0x11,10),(2,0x0d,4)):
            def pixels(code):
                sid=index[group*256+code]
                self.assertGreater(sid,0)
                return ed.stamp_asset(sid,art[(sid-1)*48:sid*48]).pixels
            charge=pixels(0x60)+pixels(0xe0)
            self.assertTrue({0,2,10,12}<=set(charge))
            # The requested half-buried charge has a flat casing at the lip,
            # warm fuse/highlights above it, and no round underside.
            self.assertEqual(charge[deck*8:(deck+1)*8],(0,)*8)
            self.assertTrue({7,10}<=set(charge[:deck*8]))
            if group==2:
                # The vault fuse stays visible in the first row, with the
                # lower floor tile restored beneath the flat casing.
                self.assertTrue({2,10}<=set(charge[:8]))
                self.assertEqual(charge[64:],pixels(0x70|128))
            for half in (0,128):
                self.assertEqual(index[group*256+0x7d+half],index[group*256+floor+half])
                if group==2:self.assertEqual(pixels(0x70+half),pixels(floor+half))
            counts=[]
            for start,first_ink in ((0x71,deck),(0x77,0)):
                tiles=[pixels(c)+pixels(c|128) for c in range(start,start+6)]
                above_floor=[tiles[y//16*3+x//8][(y%16)*8+x%8]
                             for y in range(16+deck) for x in range(24)]
                self.assertEqual(next(i//24 for i,p in enumerate(above_floor) if p!=ed.ALPHA),first_ink)
                opaque=[p for p in above_floor if p!=ed.ALPHA]
                self.assertTrue({1,2,7,10}<=set(opaque))
                self.assertLess(opaque.count(1)*8,len(opaque))
                counts.append(len(opaque))
            self.assertGreater(counts[1],counts[0])

    def test_room3_relief_has_both_mouth_positions(self):
        header,_,_=compile_art(None)
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        charset=(ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes()

        def mouth(tile):
            pixels=()
            for code in (tile,tile|128):
                sid=index[code]
                self.assertGreater(sid,0)
                stamp=art[(sid-1)*48:sid*48]
                self.assertEqual(stamp[:8],charset[code*8:code*8+8])
                pixels+=ed.stamp_asset(sid,stamp).pixels
            return pixels

        resting,lowered=mouth(0x46),mouth(0x47)
        self.assertEqual(resting[:6*8],lowered[:6*8])  # muzzle above the moving jaw
        self.assertEqual(resting[12*8:],lowered[12*8:])  # plinth below it
        self.assertEqual(resting[10*8:12*8],(ed.ALPHA,)*16)
        self.assertIn(10,lowered[10*8:12*8])  # lit bronze edge two scanlines lower

    def test_room16_roof_respects_source_edges_and_has_copper_highlights(self):
        from enhanced_architecture import PAGODA_TILES
        header=compile_art(None)[0]
        # The roof table can address stamps beyond the original byte-sized banks.
        roof=list(map(int,re.search(r'enhanced_pagoda_index\[\]=\{([^}]+)\}',header)[1].split(',')))
        art=stamp_bank(header)
        charset=(ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes()
        for tile in PAGODA_TILES:
            colors=set()
            for half in (0,1):
                code=tile|(half<<7)
                sid=roof[2*tile+half]
                self.assertGreater(sid,0)
                stamp=art[(sid-1)*48:sid*48]
                self.assertEqual(stamp[:8],charset[2048+code*8:2056+code*8])
                pixels=ed.stamp_asset(sid,stamp).pixels
                for i,pen in enumerate(pixels):
                    pair=(stamp[i//8]>>(6-2*((i%8)//2)))&3
                    self.assertEqual(pen!=ed.ALPHA,bool(pair))
                colors.update(pixels)
            self.assertTrue({2,10}<=colors)
        self.assertEqual(roof[0:2],[0,0])  # an open gate exposes the wall

    def test_room4_tower_masks_and_shared_skyline_glyphs(self):
        from enhanced_architecture import TOWER_INDEX,TOWER_TILES
        header,_,_=compile_art(None)
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        charset=(ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes()
        for tile in TOWER_TILES:
            for code in (tile,tile|128):
                self.assertEqual(index[256+code],0)  # original gallery / skyline
                sid=index[TOWER_INDEX+code]
                self.assertGreater(sid,0)
                stamp=art[(sid-1)*48:sid*48]
                self.assertEqual(stamp[:8],charset[code*8:code*8+8])
                pixels=ed.stamp_asset(sid,stamp).pixels
                for i,p in enumerate(pixels):
                    bits=stamp[i//8]
                    self.assertEqual(p!=ed.ALPHA,bool((bits>>(6-2*((i%8)//2)))&3))
                self.assertNotIn(1,pixels)  # reserve white for the hazards
        for code in (0x0f,0x8f,0x16,0x96,0x40,0xc0):
            self.assertEqual(index[TOWER_INDEX+code],index[256+code])

    def test_gallery_post_meets_the_floor(self):
        header,_,_=compile_art(None)
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        def stamp(code):
            sid=index[256+code]
            self.assertGreater(sid,0)
            return ed.stamp_asset(sid,art[(sid-1)*48:sid*48]).pixels
        joint,post,floor=map(stamp,(0x2e,0x32,0x3e))
        self.assertEqual(joint[:48],post[:48])
        self.assertEqual(set(joint[7::8]),{0})  # the dark outer edge reaches the floor
        for row in (6,7):
            for x in (0,1,4,5):
                self.assertEqual(joint[row*8+x],floor[row*8+x])

    def test_gallery_spears_keep_live_inks_unless_repainted(self):
        from enhanced_architecture import stamps
        library,_=stamps((ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes())
        upper,lower=(256+code for code in (0x40,0xc0))
        top=self.by_key[f'stamp-{library[upper]:03}']
        tip=self.by_key[f'stamp-{library[lower]:03}']
        # Room 5 preview: six black cap pixels per row, then the white collar and blade.
        cap=(ed.ALPHA,ed.ALPHA,0,0,0,0,0,0)
        collar=(ed.ALPHA,ed.ALPHA,1,1,1,1,1,1)
        blade=(ed.ALPHA,)*4+(1,1)+(ed.ALPHA,)*2
        self.assertEqual(top.pixels,cap*2+collar*2+blade*4)
        self.assertEqual(tip.pixels,blade*8)
        default=bank(compile_art(None)[0],'enhanced_arch_index')
        self.assertEqual((default[upper],default[lower]),(0,0))
        ed.save(top,list(top.pixels),None,directory=self.edits,history=self.history)
        pens=list(tip.pixels);pens[4]=7
        ed.save(tip,pens,None,directory=self.edits,history=self.history)
        header,_,_=compile_art(self.edits)
        index=bank(header,'enhanced_arch_index')
        self.assertEqual((index[upper],index[lower]),(0,library[lower]))
        offset=(index[lower]-1)*48
        packed=stamp_bank(header)[offset:offset+48]
        self.assertEqual(list(ed.stamp_asset(index[lower],packed).pixels),pens)

    def test_bruce_vertical_and_prone_frames_keep_the_source_anchor(self):
        header,_,_=compile_art(None)
        for slot,left,right in ((14,8,8),(15,30,30),(16,32,32),(17,64,66)):
            for face,pose in enumerate((left,right)):
                pens=fighter(header,2,slot,face)
                with Image.open(ROOT/f'assets/c64/sprites-v1/bruce-{pose:02x}-f{face}.png') as original:
                    mask=original.getchannel('A').tobytes()
                self.assertEqual(bytes(255 if c!=ed.ALPHA else 0 for c in pens),mask)
                self.assertNotIn(1,pens)  # keep the established amber skin ink
        self.assertNotEqual(fighter(header,2,17,1),fighter(header,2,11,1))

    def test_gallery_lanterns_have_matching_lit_dim_and_collected_art(self):
        header=compile_art(None)[0]
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        def stamp(sid):
            self.assertGreater(sid,0)
            return art[(sid-1)*48:sid*48]
        def pixels(sid):
            return ed.stamp_asset(sid,stamp(sid)).pixels
        for lit,dark,collected in ((0x13,0x66,0x1e),(0x14,0x67,0x1f)):
            def cell(code):
                return pixels(index[256+code])+pixels(index[256+(code|128)])
            on,off,empty=map(cell,(lit,dark,collected))
            self.assertEqual(on[:48],off[:48])
            self.assertEqual(off[:48],empty[:48])
            self.assertEqual([p==ed.ALPHA for p in on],[p==ed.ALPHA for p in off])
            self.assertIn(7,on[48:])
            self.assertTrue({4,9}<=set(off[48:])<={0,4,8,9,ed.ALPHA})
            self.assertEqual(set(empty[48:]),{ed.ALPHA})
        for phase,sid in enumerate(index[776:780]):
            self.assertEqual(stamp(sid)[2:4],bytes([0x22|(phase<<2)])*2)
            for row in (2,3):
                self.assertEqual(pixels(sid)[row*8+4:row*8+6],((0,4,9,8)[phase],)*2)

    def test_vault_lantern_contrast_flicker_and_pickup(self):
        from enhanced_architecture import VAULT_LAMP_INDEX
        header=compile_art(None)[0]
        index=bank(header,'enhanced_arch_index')
        art=stamp_bank(header)
        for side,(lit,spent,shift) in enumerate(((0x13,0x1e,4),(0x14,0x1f,2))):
            def stamp(sid):
                self.assertGreater(sid,0)
                return art[(sid-1)*48:sid*48]
            def pixels(sid):
                return ed.stamp_asset(sid,stamp(sid)).pixels
            def cell(code):
                return pixels(index[512+code])+pixels(index[512+(code|128)])
            on,empty=cell(lit),cell(spent)
            self.assertEqual(on[:48],empty[:48])
            self.assertEqual(set(empty[48:]),{ed.ALPHA})
            wick_x=2 if side==0 else 4
            for phase in range(4):
                sid=index[VAULT_LAMP_INDEX+4*side+phase]
                self.assertEqual(stamp(sid)[2:4],bytes([phase<<shift])*2)
                image=pixels(sid)
                self.assertGreaterEqual(image.count(7),10)  # gold even at minimum flame
                for y in (2,3):
                    self.assertEqual(image[y*8+wick_x:y*8+wick_x+2],((2,10,7,1)[phase],)*2)

    def test_conflict_mask_palette_identity_and_export(self):
        asset=self.by_key['fighter-2-08-1'];pixels,raw=self.store(asset)
        self.assertEqual(ed.load(asset,self.edits)[0],pixels)
        with self.assertRaisesRegex(ValueError,'changed on disk'):self.store(asset,None)
        self.assertEqual(ed.load(asset,self.edits)[1],raw)
        self.store(asset,raw);self.assertEqual(len(list(self.history.glob('*.png'))),1)
        for index,pen in [(pixels.index(ed.ALPHA),0),(pixels.index(0),ed.ALPHA),(pixels.index(0),15)]:
            invalid=pixels.copy();invalid[index]=pen
            with self.assertRaises(ValueError):ed.encode(asset,invalid)
        other=self.by_key['fighter-2-08-0']
        with self.assertRaises(ValueError):ed.decode(other,raw)
        with self.assertRaises(ValueError):ed.check_export_path(ROOT/'assets/c64/sprites-v1/bruce-00-f0.png')
        with self.assertRaises(ValueError):ed.check_export_path(ROOT/'.reference/a.png')
        ed.check_export_path(self.root/'allowed.png')

    def test_known_bruce_v1_edit_retains_only_hand_painted_pixels(self):
        from dataclasses import replace
        from enhanced_bruce_strikes import strike_pixels
        asset=self.by_key['fighter-2-08-0']
        original=tuple(ed.ALPHA if pen==15 else pen for pen in ed.flip(strike_pixels(6,0),48))
        legacy=replace(asset,pixels=original)
        custom=list(original)
        i=next(i for i,pen in enumerate(original) if pen!=ed.ALPHA)
        custom[i]=5
        raw=ed.encode(legacy,custom,{'method':'manual pixel editor'})
        expected=list(asset.pixels)
        expected[i]=5
        self.assertNotEqual(expected,custom)
        self.assertEqual(ed.decode(asset,raw),expected)
        # A different old painting with the same silhouette is not our
        # historical master; keep the editor's stale-file protection.
        unknown=list(original)
        unknown[i]=13
        with self.assertRaisesRegex(ValueError,'original image has changed'):
            ed.decode(asset,ed.encode(replace(asset,pixels=tuple(unknown)),custom))

    def test_ai_proposal_has_reviewable_native_pixels_and_no_secret_in_files(self):
        asset=self.by_key['fighter-2-08-1'];fake=BytesIO();Image.new('RGB',(384,168),'#111111').save(fake,format='PNG')
        def provider(req,timeout):
            self.assertEqual(req.full_url,ai.API);payload=json.loads(req.data)
            self.assertEqual(payload['model'],ai.MODEL);self.assertEqual(payload['n'],1)
            self.assertEqual(len(payload['input_references']),1);self.assertIn('48x21',payload['prompt'])
            return BytesIO(json.dumps({'data':[{'b64_json':base64.b64encode(fake.getvalue()).decode()}],'usage':{'cost':0}}).encode())
        values,meta,folder=ai.generate(asset,list(asset.pixels),'Test colors',key='test-key-never-save',
                                       opener=provider,directory=self.root/'proposal')
        self.assertTrue(all(v==(ed.ALPHA if old==ed.ALPHA else 0) for v,old in zip(values,asset.pixels)))
        self.assertFalse(self.edits.exists());self.assertEqual(meta['cost_usd'],0)
        self.assertTrue((folder/'reference.png').is_file() and (folder/'source.png').is_file())
        self.assertTrue(all(b'test-key-never-save' not in f.read_bytes() for f in folder.iterdir()))
        self.assertEqual(ed.decode(asset,ed.encode(asset,values,meta)),values)

    def test_coarse_sprite_import_preserves_two_source_inks(self):
        asset = self.by_key['fighter-0-00-1']
        # A square with black and pale halves has no midtone ink. Resampling
        # with a box filter would paint midtones into the original silhouette.
        image = Image.new('RGB',(asset.width*4,asset.height*4),ed.palette()[1][0])
        for x in range(0,image.width,4):
            image.paste(ed.palette()[1][1],(x,0,x+2,image.height))
        result = ed.convert_candidate(asset,image,asset.pixels)
        self.assertLessEqual(set(result),{0,1,ed.ALPHA})
        self.assertEqual([p==ed.ALPHA for p in result],[p==ed.ALPHA for p in asset.pixels])
        self.assertIn('16x21 logical pixels',ai.prompt_for(asset,'Keep the belt.'))

    def test_tk_edit_undo_paste_and_save(self):
        import bruce_graphics_editor as ui
        with patch.object(ui,'load',lambda a:ed.load(a,self.edits)),patch.object(ui,'save',
                lambda a,p,e,origin:ed.save(a,p,e,origin,self.edits,self.history)):
            app=ui.GraphicsEditor();app.root.withdraw()
            try:
                asset=self.by_key['fighter-2-00-1'];app.load_asset(asset)
                old=list(asset.pixels);i=next(i for i,c in enumerate(old) if 0<c<15)
                app.select_pen(0);app.snapshot();app.paint(i%48,i//48)
                self.assertTrue(app.dirty);app.undo();self.assertEqual(app.pixels,old)
                app.redo();self.assertEqual(app.pixels[i],0)
                app.selection=(i%48,i//48,i%48,i//48);app.copy();app.paste()
                app.place_paste(0,0);self.assertEqual(app.pixels[0],ed.ALPHA)
                self.assertTrue(app.save());self.assertEqual(ed.load(asset,self.edits)[0],app.pixels)
                result=app.candidate(asset,old,{'method':'UI test'})
                def click(dialog,label):
                    items=list(dialog.winfo_children())
                    while items:
                        w=items.pop();items.extend(w.winfo_children())
                        if isinstance(w,ui.ttk.Button) and w.cget('text')==label:
                            w.invoke();return
                    self.fail(label)
                click(result,'Discard');self.assertEqual(app.pixels,ed.load(asset,self.edits)[0])
                result=app.candidate(asset,old,{'method':'UI test'})
                click(result,'Apply suggestion');self.assertTrue(app.dirty);self.assertEqual(app.pixels,old)
                self.assertNotEqual(ed.load(asset,self.edits)[0],old)
                app.undo();self.assertFalse(app.dirty)
                dialog=app.ai_dialog();self.assertTrue(dialog.winfo_exists());dialog.destroy()
            finally:app.closed=True;app.root.destroy()

    def test_arrow_keys_keep_selection_cursor_and_view_together(self):
        import bruce_graphics_editor as ui
        app=ui.GraphicsEditor()
        try:
            app.root.update_idletasks()
            app.list.selection_clear(0,'end')
            app.list.selection_set(50)
            app.choose_asset()
            view=app.list.yview()
            for direction,index in ((1,51),(-1,50)):
                app.step_asset(direction)
                self.assertEqual(app.asset,app.visible_assets[index])
                self.assertEqual(app.list.index('active'),index)
                self.assertEqual(app.list.curselection(),(index,))
                self.assertIsNotNone(app.list.bbox(index))
            self.assertGreaterEqual(app.list.yview()[0],view[0])
            app.group.set('Yamo');app.filter_assets()
            app.search.set('Run D');app.step_asset(1)
            self.assertEqual(app.asset.key,'fighter-0-04-1')
            app.pixels[next(i for i,p in enumerate(app.pixels) if p!=ed.ALPHA)]=13
            with patch.object(app,'confirm_dirty',return_value=False):
                app.step_asset(1)
            self.assertEqual(app.asset.key,'fighter-0-04-1')
            self.assertEqual(app.list.index('active'),0)
            self.assertEqual(app.list.curselection(),(0,))
        finally:
            app.closed=True;app.root.destroy()

    @unittest.skipUnless(os.name == 'nt', 'Windows desktop build')
    def test_build_from_pythonw_uses_matching_console_python(self):
        import bruce_graphics_editor as ui
        from types import SimpleNamespace

        # Exercise the real PowerShell handoff without rebuilding the game.
        (self.root / 'amiga-build.ps1').write_text(
            "param([Parameter(Mandatory)][string]$PythonExecutable)\n"
            "& $PythonExecutable -c 'import sys; print(sys.executable)'\n"
            "exit $LASTEXITCODE\n", encoding='ascii')
        console_python = Path(sys.executable).with_name('python.exe')
        window_python = console_python.with_name('pythonw.exe')
        results = []
        editor = SimpleNamespace(busy=False, dirty=False,
                                 status=SimpleNamespace(set=results.append),
                                 start_job=lambda label, work, done: done(work()))
        with patch.object(ui, 'ROOT', self.root), patch.object(sys, 'executable', str(window_python)):
            ui.GraphicsEditor.build(editor)
        self.assertEqual(len(results), 1)
        log, = (self.root / '.tmp/graphics-editor').glob('build-*.log')
        self.assertEqual(Path(log.read_text().strip()), console_python)


if __name__=='__main__':unittest.main(verbosity=2)
