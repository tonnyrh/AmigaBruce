"""Bruce Enhanced pixel editor.

Adapted from Harrier's tools/amiga-graphics-editor.py: palette painting,
bounded undo/redo, rectangular copy/paste and optimistic save protection.
Bruce uses opaque pen 0, locked silhouettes and sparse build-time overrides.
"""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
from uuid import uuid4
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from bruce_editor_data import (ROOT, ALPHA, catalog, palette, load, save,
                               image_for, convert_candidate, check_files, encode, check_export_path)
from bruce_editor_ai import MODEL, bundle, generate


class GraphicsEditor:
    def __init__(self):
        self.root=tk.Tk();self.root.title('Bruce Graphics Editor')
        self.root.geometry('1280x820');self.root.minsize(1020,720)
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.assets=catalog();self.visible_assets=list(self.assets)
        self.asset=None;self.pixels=[];self.saved=[];self.saved_raw=None
        self.undo_stack=[];self.redo_stack=[];self.clipboard=None
        self.selection=None;self.selection_start=None;self.paste_pending=False
        self.stroke=None;self.pen=10;self.photo=None;self.reference_photo=None
        self.provenance={'method':'manual pixel editor'}
        self.busy=False;self.jobs=queue.Queue();self.closed=False
        self.search=tk.StringVar();self.group=tk.StringVar(value='All')
        self.zoom=tk.IntVar(value=14);self.tool=tk.StringVar(value='Draw')
        self.backdrop=tk.StringVar(value='Brick wall');self.animate=tk.BooleanVar()
        self.status=tk.StringVar(value='Select an asset. Right-click a pixel to pick its color.')
        self.search.trace_add('write',lambda *_:self.filter_assets())
        self._ui();self.filter_assets();self.load_asset(self.assets[0])
        self.root.after(150,self.poll_jobs);self.root.after(170,self.animation_tick)

    @property
    def dirty(self):return self.pixels!=self.saved

    def _ui(self):
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('TButton',padding=(7,5))
        top=ttk.Frame(self.root,padding=8);top.pack(fill='x')
        for label,fn in [('Save',self.save),('Undo',self.undo),('Redo',self.redo),
                         ('Reload',self.reload),('Import image…',self.import_png),
                         ('Export PNG…',self.export_png),('AI suggestions…',self.ai_dialog),
                         ('Pack graphics',self.pack),('Build Amiga',self.build)]:
            ttk.Button(top,text=label,command=fn).pack(side='left',padx=2)
        panes=ttk.Panedwindow(self.root,orient='horizontal');panes.pack(fill='both',expand=True,padx=10)
        side=ttk.Frame(panes,width=280);work=ttk.Frame(panes)
        panes.add(side,weight=1);panes.add(work,weight=4)
        ttk.Label(side,text='ENHANCED · ASSET LIBRARY',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(6,8))
        groups=ttk.Combobox(side,textvariable=self.group,state='readonly',values=('All','Bruce','Yamo','Kage','Structures','Backgrounds'))
        groups.pack(fill='x');groups.bind('<<ComboboxSelected>>',lambda _:self.filter_assets())
        ttk.Entry(side,textvariable=self.search).pack(fill='x',pady=6)
        lst=ttk.Frame(side);lst.pack(fill='both',expand=True)
        self.list=tk.Listbox(lst,exportselection=False,width=31,height=13,font=('Segoe UI',10))
        scroll=ttk.Scrollbar(lst,orient='vertical',command=self.list.yview)
        self.list.configure(yscrollcommand=scroll.set);self.list.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        self.list.bind('<<ListboxSelect>>',self.choose_asset)
        self.list.bind('<Up>', lambda event: self.step_asset(-1))
        self.list.bind('<Down>', lambda event: self.step_asset(1))
        ttk.Label(side,text='PREVIEW · UP TO 4×',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(12,4))
        previews=ttk.Frame(side);previews.pack(fill='x')
        bg=ttk.Combobox(previews,textvariable=self.backdrop,values=('Brick wall','Slate','Dark','Checkerboard'),width=11,state='readonly')
        bg.pack(side='left');bg.bind('<<ComboboxSelected>>',lambda _:self.redraw_preview())
        ttk.Checkbutton(previews,text='Animate',variable=self.animate,command=self.reset_preview).pack(side='left',padx=5)
        self.preview=tk.Canvas(side,width=260,height=130,bg='#253444',highlightthickness=0)
        self.preview.pack(fill='x',pady=6)
        self.ref_label=ttk.Label(side,text='');self.ref_label.pack(anchor='w')
        self.reference=tk.Canvas(side,width=260,height=95,bg='#253444',highlightthickness=0);self.reference.pack(fill='x',pady=(3,8))
        controls=ttk.Frame(work,padding=(10,3));controls.pack(fill='x')
        for name in ('Draw','Fill','Select'):
            ttk.Radiobutton(controls,text=name,value=name,variable=self.tool,command=self.cancel_selection).pack(side='left',padx=4)
        ttk.Button(controls,text='Copy',command=self.copy).pack(side='left',padx=4)
        ttk.Button(controls,text='Paste',command=self.paste).pack(side='left')
        ttk.Label(controls,text='Zoom').pack(side='left',padx=(15,5))
        zoom=ttk.Combobox(controls,textvariable=self.zoom,values=(2,4,6,8,12,14,18,24,32),width=3,state='readonly')
        zoom.pack(side='left');zoom.bind('<<ComboboxSelected>>',lambda _:self.redraw())
        self.title=ttk.Label(work,font=('Segoe UI',13,'bold'),padding=8);self.title.pack(anchor='w')
        frame=ttk.Frame(work);frame.pack(fill='both',expand=True,padx=8)
        frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
        self.canvas=tk.Canvas(frame,bg='#202b36',highlightthickness=0)
        hs=ttk.Scrollbar(frame,orient='horizontal',command=self.canvas.xview);vs=ttk.Scrollbar(frame,command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hs.set,yscrollcommand=vs.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');hs.grid(row=1,column=0,sticky='ew');vs.grid(row=0,column=1,sticky='ns')
        self.canvas.bind('<ButtonPress-1>',self.press);self.canvas.bind('<B1-Motion>',self.drag)
        self.canvas.bind('<ButtonRelease-1>',self.release);self.canvas.bind('<ButtonPress-3>',self.pick)
        self.canvas.bind('<Motion>',self.hover)
        colors=ttk.Frame(work,padding=8);colors.pack(fill='x');self.pens=[]
        for i,rgb in enumerate(palette()[1]):
            color='#%02x%02x%02x'%rgb
            button=tk.Button(colors,text=f'{i:X}',width=3,bg=color,activebackground=color,
                             fg='white' if sum(rgb)<350 else 'black',command=lambda p=i:self.select_pen(p))
            button.pack(side='left',padx=1);self.pens.append(button)
        self.detail=ttk.Label(work,padding=(8,0,8,8));self.detail.pack(anchor='w')
        ttk.Label(self.root,text='Ctrl+S Save · Ctrl+Z / Ctrl+Y Undo / Redo · Ctrl+C / Ctrl+V Copy / Paste · Esc Cancel selection',padding=(10,4)).pack(anchor='w')
        ttk.Label(self.root,textvariable=self.status,relief='sunken',padding=7).pack(fill='x')
        # Bind to the pixel canvas, not text inputs: Ctrl+C must still copy a prompt.
        for event,fn in [('<Control-s>',self.save),('<Control-z>',self.undo),('<Control-y>',self.redo),
                         ('<Control-c>',self.copy),('<Control-v>',self.paste),('<Escape>',self.cancel_selection)]:
            self.canvas.bind(event,lambda _,f=fn:(f(),'break')[1])
        self.select_pen(self.pen)

    def filter_assets(self):
        if not hasattr(self,'list'):return
        search=self.search.get().casefold();group=self.group.get()
        self.visible_assets=[a for a in self.assets if (group=='All' or a.group==group) and search in a.label.casefold()]
        self.list.delete(0,'end')
        for a in self.visible_assets:self.list.insert('end',a.label)
        self.sync_selection()

    def sync_selection(self):
        self.list.selection_clear(0, 'end')
        if self.asset in self.visible_assets:
            index = self.visible_assets.index(self.asset)
            self.list.selection_set(index)
            self.list.activate(index)
            self.list.selection_anchor(index)
            self.list.see(index)

    def step_asset(self, direction):
        rows = self.list.size()
        if rows:
            selected = self.list.curselection()
            if selected:
                index = max(0, min(rows - 1, selected[0] + direction))
            else:
                index = 0 if direction > 0 else rows - 1
            self.list.selection_clear(0, 'end')
            self.list.selection_set(index)
            self.choose_asset()
        return 'break'

    def confirm_dirty(self):
        if not self.dirty:return True
        answer=messagebox.askyesnocancel('Unsaved changes','Save your changes before continuing?',parent=self.root)
        return self.save() if answer else answer is False

    def choose_asset(self,_=None):
        selection=self.list.curselection()
        if not selection:return
        asset=self.visible_assets[selection[0]]
        if asset==self.asset:return
        if self.confirm_dirty():self.load_asset(asset)
        else:self.sync_selection()

    def load_asset(self,asset):
        issue=None
        try:pixels,raw=load(asset)
        except (OSError,ValueError) as exc:
            # Retain the exact old bytes for conflict detection and backup.
            # This also lets the artist re-import an override after a base change.
            try:raw=asset.path.read_bytes()
            except OSError:
                self.sync_selection();self.error(exc);return False
            pixels=list(asset.pixels);issue=str(exc)
        self.asset=asset;self.pixels=pixels;self.saved=pixels.copy();self.saved_raw=raw
        self.provenance={'method':'manual pixel editor'}
        if raw and not issue:
            with Image.open(BytesIO(raw)) as img:
                try:origin=json.loads(img.info.get('bruce.origin','{}'))
                except (ValueError,TypeError):origin=None
                if isinstance(origin,dict):self.provenance=origin
        self.undo_stack=[];self.redo_stack=[];self.cancel_selection();self.animate.set(False)
        self.zoom.set(2 if asset.width>100 else 8 if asset.width>48 else 14 if asset.width>16 else 32)
        self.canvas.xview_moveto(0);self.canvas.yview_moveto(0)
        if self.pen>asset.max_pen:self.select_pen(10)
        self.title.configure(text=asset.label)
        self.detail.configure(text=f'{asset.width} × {asset.height} · OCS palette · locked silhouette · black is opaque')
        for i,button in enumerate(self.pens):button.configure(state='normal' if i<=asset.max_pen else 'disabled')
        self.sync_selection();self.redraw();self.show_reference()
        self.status.set('Showing the original image. '+issue if issue else
                        'Saved edit loaded.' if raw else 'Original image. Save to create an Enhanced edit.')
        return True

    def select_pen(self,pen):
        self.pen=pen
        for i,b in enumerate(self.pens):b.configure(relief='sunken' if i==pen else 'raised')

    def redraw(self):
        if not self.asset:return
        z=self.zoom.get();w,h=self.asset.width,self.asset.height
        self.canvas.delete('all');self.items=[]
        self.canvas.configure(scrollregion=(0,0,w*z+24,h*z+24))
        if w*h>4096:
            display=self.composite(self.asset,self.pixels).resize((w*z,h*z),Image.Resampling.NEAREST)
            self.canvas_photo=ImageTk.PhotoImage(display,master=self.root)
            self.canvas.create_image(12,12,anchor='nw',image=self.canvas_photo)
        else:
            for i,pen in enumerate(self.pixels):
                x,y=i%w,i//w;color=self.color(pen,x,y)
                self.items.append(self.canvas.create_rectangle(12+x*z,12+y*z,12+(x+1)*z,12+(y+1)*z,
                                  fill=color,outline='#53606b' if z>=8 else color))
        self.draw_selection();self.redraw_preview()

    def color(self,pen,x,y):
        return ('#4a5560' if (x+y)%2 else '#35404b') if pen==ALPHA else '#%02x%02x%02x'%palette()[1][pen]

    def composite(self,asset,pixels):
        bg=Image.new('RGBA',(asset.width,asset.height),'#253444')
        choice=self.backdrop.get()
        if choice in ('Brick wall','Slate'):
            key='wall-warm' if choice=='Brick wall' else 'wall-cool'
            wall=next(a for a in self.assets if a.key==key)
            try:backdrop_pixels=load(wall)[0]
            except (OSError,ValueError):backdrop_pixels=wall.pixels
            tile=image_for(wall,backdrop_pixels).convert('RGBA')
            for y in range(0,asset.height,32):
                for x in range(0,asset.width,64):bg.paste(tile,(x,y))
        elif choice=='Checkerboard':
            bg.putdata([tuple(int(self.color(ALPHA,x,y)[i:i+2],16) for i in (1,3,5))+(255,)
                        for y in range(asset.height) for x in range(asset.width)])
        bg.alpha_composite(image_for(asset,pixels).convert('RGBA'))
        return bg

    def redraw_preview(self,asset=None,pixels=None):
        if not self.asset:return
        asset=asset or self.asset;pixels=self.pixels if pixels is None else pixels
        scale=min(4,260/asset.width,130/asset.height)
        image=self.composite(asset,pixels).resize((int(asset.width*scale),int(asset.height*scale)),Image.Resampling.NEAREST)
        self.photo=ImageTk.PhotoImage(image,master=self.root)
        self.preview.delete('all');self.preview.create_image(130,65,image=self.photo)

    def reset_preview(self):
        self.redraw_preview()
        self.show_reference()

    def show_reference(self,asset=None):
        self.reference.delete('all');asset=asset or self.asset
        self.ref_label.configure(text='C64 silhouette reference')
        if asset.group in ('Bruce','Yamo','Kage'):
            _,actor,slot,face=asset.key.split('-');actor,slot,face=map(int,(actor,slot,face))
            if actor==2:
                from enhanced_fighters import BRUCE_SOURCE_POSES
                pose=BRUCE_SOURCE_POSES[slot][face]
            else:
                from enhanced_enemies import reference_pose
                pose=reference_pose(actor,slot,face)
                self.ref_label.configure(text=f'C64 pose reference · ${pose:02X}')
            path=ROOT/f'assets/c64/sprites-v1/{asset.group.lower()}-{pose:02x}-f{face}.png'
            with Image.open(path) as src:image=src.convert('RGBA').resize((192,84),Image.Resampling.NEAREST)
        else:
            self.ref_label.configure(text='Original image')
            image=self.composite(asset,asset.pixels)
            image.thumbnail((250,90),Image.Resampling.NEAREST)
            if max(asset.width,asset.height)<40:image=image.resize((asset.width*5,asset.height*5),Image.Resampling.NEAREST)
        self.reference_photo=ImageTk.PhotoImage(image,master=self.root)
        self.reference.create_image(130,45,image=self.reference_photo)

    def animation_tick(self):
        if self.closed:return
        if self.animate.get() and self.asset and self.asset.group in ('Bruce','Yamo','Kage'):
            _,actor,slot,face=self.asset.key.split('-');slot=int(slot)
            slots=(5,6) if slot in (5,6) else (13,10) if actor=='2' and slot in (10,13) else (1,2)
            if actor=='2' and slot in (14,15,16):slots=(14,15,16,15,14)
            if actor=='2' and slot==17:slots=(17,)
            if actor!='2' and slot in (1,2,3,4):slots=(1,2,3,4)
            self.anim_step=getattr(self,'anim_step',0)+1;key=f'fighter-{actor}-{slots[self.anim_step%len(slots)]:02}-{face}'
            asset=next((a for a in self.assets if a.key==key),None)
            if asset:
                try:
                    self.redraw_preview(asset,self.pixels if asset==self.asset else load(asset)[0])
                    self.show_reference(asset)
                except (OSError,ValueError) as exc:self.animate.set(False);self.error(exc)
        self.root.after(170,self.animation_tick)

    def xy(self,event,clamp=False):
        if not self.asset:return None
        z=self.zoom.get();x=int((self.canvas.canvasx(event.x)-12)//z);y=int((self.canvas.canvasy(event.y)-12)//z)
        if clamp:return max(0,min(x,self.asset.width-1)),max(0,min(y,self.asset.height-1))
        return (x,y) if 0<=x<self.asset.width and 0<=y<self.asset.height else None

    def snapshot(self):
        self.undo_stack.append((self.pixels.copy(),self.provenance.copy()));self.undo_stack=self.undo_stack[-100:];self.redo_stack=[]

    def press(self,event):
        self.canvas.focus_set();point=self.xy(event)
        if not point:return
        if self.paste_pending:return self.place_paste(*point)
        if self.tool.get()=='Select':
            self.selection_start=point;self.selection=(*point,*point);return self.draw_selection()
        self.stroke=self.pixels.copy();self.snapshot()
        if self.tool.get()=='Fill' or event.state&1:self.fill(*point)
        else:self.paint(*point)

    def drag(self,event):
        if self.selection_start:
            x,y=self.xy(event,True);a,b=self.selection_start
            self.selection=(min(x,a),min(y,b),max(x,a),max(y,b));self.draw_selection()
        elif self.stroke is not None and self.tool.get()=='Draw':
            point=self.xy(event)
            if point:self.paint(*point)

    def release(self,_=None):
        self.selection_start=None
        if self.stroke is not None:
            if self.stroke==self.pixels:self.undo_stack.pop()
            self.stroke=None;self.redraw_preview()

    def paint(self,x,y):
        i=y*self.asset.width+x
        if self.pixels[i]==ALPHA or self.pixels[i]==self.pen:return
        self.pixels[i]=self.pen
        if self.items:self.canvas.itemconfigure(self.items[i],fill=self.color(self.pen,x,y))
        else:self.redraw()
        self.status.set(self.asset.label+' · unsaved')

    def fill(self,x,y):
        w,h=self.asset.width,self.asset.height;old=self.pixels[y*w+x]
        if old in (ALPHA,self.pen):return
        pending=[(x,y)]
        while pending:
            x,y=pending.pop()
            if not (0<=x<w and 0<=y<h) or self.pixels[y*w+x]!=old:continue
            self.pixels[y*w+x]=self.pen
            pending.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
        self.redraw();self.status.set('Fill complete · unsaved')

    def pick(self,event):
        point=self.xy(event)
        if point:
            pen=self.pixels[point[1]*self.asset.width+point[0]]
            if pen!=ALPHA:self.select_pen(pen)

    def copy(self):
        if not self.selection:return self.status.set('Select a rectangle first.')
        a,b,c,d=self.selection;w=self.asset.width
        self.clipboard=(c-a+1,d-b+1,[self.pixels[y*w+x] for y in range(b,d+1) for x in range(a,c+1)])
        self.status.set('Copied. Choose Paste, then click where the selection should go.')

    def paste(self):
        if self.clipboard:self.paste_pending=True;self.status.set('Click to place the top left corner. Press Esc to cancel.')

    def place_paste(self,x,y):
        w,h,pixels=self.clipboard
        if x+w>self.asset.width or y+h>self.asset.height:return self.status.set('The entire selection must fit on the canvas.')
        if any(v!=ALPHA and v>self.asset.max_pen for v in pixels):return self.status.set('The selection uses a color outside this asset’s palette.')
        self.snapshot()
        for i,pen in enumerate(pixels):
            at=(y+i//w)*self.asset.width+x+i%w
            if pen!=ALPHA and self.pixels[at]!=ALPHA:self.pixels[at]=pen
        self.paste_pending=False;self.selection=(x,y,x+w-1,y+h-1);self.redraw()

    def hover(self,event):
        if self.paste_pending and self.clipboard:
            point=self.xy(event)
            if point:
                x,y=point;w,h,_=self.clipboard;self.selection=(x,y,x+w-1,y+h-1);self.draw_selection()

    def draw_selection(self):
        self.canvas.delete('selection')
        if self.selection:
            a,b,c,d=self.selection;z=self.zoom.get()
            self.canvas.create_rectangle(12+a*z,12+b*z,12+(c+1)*z,12+(d+1)*z,outline='#efcc55',width=3,tags='selection')

    def cancel_selection(self):
        self.selection=self.selection_start=None;self.paste_pending=False
        if hasattr(self,'canvas'):self.canvas.delete('selection')

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append((self.pixels.copy(),self.provenance.copy()))
            self.pixels,self.provenance=self.undo_stack.pop();self.redraw()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append((self.pixels.copy(),self.provenance.copy()))
            self.pixels,self.provenance=self.redo_stack.pop();self.redraw()

    def save(self):
        if self.busy:return self.status.set('Wait for the current task to finish.')
        try:
            self.saved_raw=save(self.asset,self.pixels,self.saved_raw,self.provenance)
            self.saved=self.pixels.copy();self.status.set('Saved. Choose Pack graphics to update the assets or Build Amiga to create the executable and disk image.')
            return True
        except (OSError,ValueError) as exc:self.error(exc);return False

    def reload(self):
        if self.confirm_dirty():self.load_asset(self.asset)

    def export_png(self):
        path=filedialog.asksaveasfilename(parent=self.root,title='Export PNG',defaultextension='.png',initialfile=self.asset.key+'.png',filetypes=[('PNG','*.png')])
        if path:
            try:
                check_export_path(path)
                Path(path).write_bytes(encode(self.asset,self.pixels,self.provenance));self.status.set('PNG exported.')
            except (OSError,ValueError) as exc:self.error(exc)

    def import_png(self):
        path=filedialog.askopenfilename(parent=self.root,title='Import image',filetypes=[('Images','*.png *.jpg *.jpeg *.webp')])
        if not path:return
        try:
            with Image.open(path) as image:
                if image.width*image.height>16777216:raise ValueError('Choose an image of 16 megapixels or less.')
                image.load();pixels=convert_candidate(self.asset,image,self.pixels)
            self.candidate(self.asset,pixels,{'method':'image import','file':Path(path).name})
        except (OSError,ValueError) as exc:self.error(exc)

    def candidate(self,asset,pixels,provenance):
        win=tk.Toplevel(self.root);win.title('Review suggestion · '+asset.label);win.transient(self.root);win.grab_set()
        ttk.Label(win,text='Current image                         Suggested image',padding=10).pack()
        panel=ttk.Frame(win,padding=10);panel.pack();photos=[]
        old=self.pixels if asset==self.asset else load(asset)[0]
        for values in (old,pixels):
            image=self.composite(asset,values);z=min(8,460/asset.width)
            image=image.resize((int(asset.width*z),int(asset.height*z)),Image.Resampling.NEAREST)
            photo=ImageTk.PhotoImage(image,master=win);photos.append(photo)
            ttk.Label(panel,image=photo).pack(side='left',padx=6)
        win.photos=photos
        ttk.Label(win,text='The preview uses the game palette, size and silhouette. Apply it to continue editing.',padding=10).pack()
        def accept():
            if asset!=self.asset:
                if not self.confirm_dirty():return
                if not self.load_asset(asset):return
            self.snapshot();self.pixels=list(pixels);self.provenance=provenance
            self.redraw();self.status.set('Suggestion applied. Press Ctrl+Z to undo or Save to keep it.');win.destroy()
        row=ttk.Frame(win,padding=10);row.pack()
        ttk.Button(row,text='Apply suggestion',command=accept).pack(side='left',padx=5)
        ttk.Button(row,text='Discard',command=win.destroy).pack(side='left',padx=5)
        return win

    def start_job(self,label,work,finished):
        if self.busy:return self.status.set('A task is already running.')
        self.busy=True;self.status.set(label)
        def run():
            try:self.jobs.put((finished,work(),None))
            except Exception as exc:self.jobs.put((None,None,exc))
        threading.Thread(target=run,daemon=True).start()

    def poll_jobs(self):
        if self.closed:return
        try:
            fn,result,error=self.jobs.get_nowait();self.busy=False
            if error:self.error(error)
            else:fn(result)
        except queue.Empty:pass
        self.root.after(150,self.poll_jobs)

    def pack(self):
        if self.busy or (self.dirty and not self.save()):return
        def work():
            from build_enhanced_art import main
            main();return 'Enhanced graphics packed. Choose Build Amiga to try them in the game.'
        self.start_job('Packing graphics…',work,self.status.set)

    def build(self):
        if self.busy or (self.dirty and not self.save()):return
        def work():
            folder=ROOT/'.tmp/graphics-editor';folder.mkdir(parents=True,exist_ok=True)
            log=folder/('build-'+uuid4().hex[:8]+'.log')
            build_python = Path(sys.executable)
            if build_python.name.lower() == 'pythonw.exe':
                build_python = build_python.with_name('python.exe')
            command = [
                shutil.which('pwsh') or 'powershell', '-NoProfile', '-NonInteractive',
                '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'amiga-build.ps1'),
                '-PythonExecutable', str(build_python),
            ]
            with log.open('w',encoding='utf-8') as stream:
                result=subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                      creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode:raise ValueError(f'Build failed. See {log}')
            return 'Build complete. Start the game with amiga/out/bruce_amiga.adf to see your changes.'
        self.start_job('Building Amiga disk image…',work,self.status.set)

    def ai_dialog(self):
        if self.busy:return self.status.set('Wait for the current task to finish.')
        asset=self.asset;pixels=self.pixels.copy()
        win=tk.Toplevel(self.root);win.title('AI suggestions · '+asset.label);win.transient(self.root);win.grab_set()
        ttk.Label(win,text='Describe the change you want to make.',padding=10).pack(anchor='w')
        prompt=tk.Text(win,width=75,height=7,wrap='word');prompt.pack(padx=10)
        prompt.insert('1.0','Use broad blocks of color and one clear shadow. Keep the pose and proportions.')
        fields=ttk.Frame(win,padding=10);fields.pack(fill='x')
        model=tk.StringVar(value=MODEL);key=tk.StringVar();seed=tk.StringVar(value='42')
        for row,(label,var,mask) in enumerate([('Model',model,''),('API key',key,'•'),('Seed',seed,'')]):
            ttk.Label(fields,text=label).grid(row=row,column=0,sticky='w',padx=4,pady=4)
            ttk.Entry(fields,textvariable=var,width=55,show=mask).grid(row=row,column=1,sticky='ew')
        ttk.Label(win,text='Enter your API key here or set OPENROUTER_API_KEY. The editor does not store it.\nGenerate sends the prompt and selected image to OpenRouter and uses account credit.\nYou can review the result before applying it.',padding=10).pack(anchor='w')
        def args():
            text=prompt.get('1.0','end').strip()
            if not text:raise ValueError('Enter a description.')
            return text,model.get().strip(),int(seed.get())
        def export():
            try:
                text,m,s=args();folder,_=bundle(asset,pixels,text,m,s)
                self.status.set('Prompt bundle saved to '+str(folder));os.startfile(folder)
            except (OSError,ValueError) as exc:self.error(exc)
        def request():
            try:text,m,s=args()
            except ValueError as exc:return self.error(exc)
            api_key=key.get().strip() or os.environ.get('OPENROUTER_API_KEY','')
            if not api_key:return self.error(ValueError('Enter your OpenRouter API key or set OPENROUTER_API_KEY.'))
            win.destroy()
            def done(result):
                values,origin,folder=result;self.status.set('Suggestion ready. Original image and prompt saved to '+str(folder))
                self.candidate(asset,values,origin)
            self.start_job('Generating a suggestion…',lambda:generate(asset,pixels,text,api_key,m,s),done)
        buttons=ttk.Frame(win,padding=10);buttons.pack()
        ttk.Button(buttons,text='Generate with OpenRouter',command=request).pack(side='left',padx=5)
        ttk.Button(buttons,text='Export prompt and reference',command=export).pack(side='left',padx=5)
        ttk.Button(buttons,text='Close',command=win.destroy).pack(side='left',padx=5)
        return win

    def error(self,error):
        self.status.set(str(error));messagebox.showerror('Bruce Graphics Editor',str(error),parent=self.root)

    def close(self):
        if self.busy:
            self.status.set('Wait for the current task to finish before closing.');return
        if self.confirm_dirty():self.closed=True;self.root.destroy()


def main():
    p = argparse.ArgumentParser(description='Edit Enhanced fighters, tiles and backgrounds for Bruce.')
    p.add_argument('--check', action='store_true',
                   help='validate the saved edits and check that the graphics bank is up to date')
    args = p.parse_args()
    if args.check:
        from build_enhanced_art import compile_art
        count=check_files();header,_,report=compile_art()
        current=(ROOT/'amiga/enhanced_art.h').read_text()
        if header!=current:raise SystemExit('The PNG files passed validation. Run Pack graphics to update the game assets.')
        print(f'OK: {len(catalog())} assets, {count} saved edits. {report}')
    else:GraphicsEditor().root.mainloop()


if __name__=='__main__':main()
