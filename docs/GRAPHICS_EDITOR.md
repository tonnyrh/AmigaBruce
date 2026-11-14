# Bruce Graphics Editor

Double-click **GraphicsEditor.cmd** in the project folder or run `.\edit-amiga-graphics.ps1`. The editor runs on Windows with Python 3.10 or later, Tkinter and Pillow. You can install Pillow with `python -m pip install Pillow`.

## Edit a fighter

1. Search for **Bruce · Strike** and select **right** or **left**. Use the Up and Down arrows in the asset list to move one row at a time. Choose **Brick wall** or **Slate** to judge contrast. The C64 preview below shows the corresponding pose and facing at the same pixel scale. Try **Yamo · Run D · left** or **Kage · Strike · right**.
2. Choose a palette color and draw with the left mouse button. Right-click to pick a color. Shift-click fills a connected area. To copy a region, choose **Select**, drag a rectangle, click **Copy**, then **Paste** and click its destination. **Animate** previews a sequence such as climbing or kicking.
3. **Save** writes the selected asset to [enhanced-edits](../assets/graphics/enhanced-edits). **Pack graphics** updates the graphics bank. **Build Amiga** packs the assets and builds the executable and the disk image at `amiga/out/bruce_amiga.adf`. Start that disk, press **F4** in the main menu to select **Enhanced**, then start the game.

With the canvas focused, use **Ctrl+S** to save, **Ctrl+Z/Y** to undo or redo, **Ctrl+C/V** to copy or paste and **Esc** to cancel a selection. The editor keeps previous PNG versions in `.tmp/graphics-history`. If another window saves the same asset, export your draft before you click **Reload**.

## Assets and colors

The library contains 70 fighter views, 160 shared structure tiles and three backgrounds. Editing a shared tile updates every place that uses it. Left and right poses can be edited individually. Climbing poses have one facing.

In the game, Yamo and Kage use the original bounds for all 35 C64 poses in both directions. The editor exposes their Enhanced animation slots. Other source states can reuse the same cropped picture at another position. [Compare C64 and Enhanced poses](../reference/analysis/enhanced-2026-11-01/enemy-original-size.png).

The game uses a 16-color OCS palette. Fighters reserve one value for transparency. Opaque backgrounds can use all 16 colors. Black remains visible because the editor PNGs store transparency separately. The canvas and silhouette are locked to keep artwork aligned with the game.

## AI suggestions and image import

Select an asset and click **AI suggestions**. For a fighter, the prompt includes both the 48×21 canvas and the visible size of the selected pose. Ask for connected blocks that read at 1×, for example “Keep Yamo’s belly green and give the belt one continuous pale stripe.” Both **Import image** and **AI suggestions** sample the center of each enlarged pixel when importing fighter artwork.

The fighter artwork uses enlarged C64 pose templates. Bruce and Yamo use four inks each, and Kage uses five. After replacing a generated sheet, run `python tools/build_fighter_ink_masters.py --actor bruce` (or `yamo` or `kage`). Choose **Pack graphics** or **Build Amiga** to use the resulting native master. [Bruce prompt and source](../assets/graphics/enhanced-study/coarse-bruce-generation.json) · [Enemy prompts and sources](../assets/graphics/enhanced-study/coarse-enemy-generation.json).

When an edit was saved on the first Bruce artwork, the editor and packer keep the pixels you changed and draw the rest from the new master. Opening the old PNG preserves the file. The next **Save** records the new base and backs up the previous version.

- **Generate with OpenRouter** sends the prompt, palette instructions and selected reference image to the model. The default is FLUX.2 Pro. You can select another model that accepts image references. Enter the key in the **API key** field or set `OPENROUTER_API_KEY` before launch. The key is kept in memory. Generation can use account credit.
- **Export prompt and reference** creates a local folder under `.tmp/graphics-ai` with the prompt, palette, mask and reference PNG. Use these in another image tool and bring the result back with **Import image**.

The review window shows the current and suggested images side by side at game resolution. Choose **Apply suggestion** to keep working on it, or **Discard** to return to your draft. **Save** makes the edit available to the next build. For OpenRouter suggestions, the original response image and prompt are also kept in `.tmp/graphics-ai`.

## Check the graphics bank

Run `.\edit-amiga-graphics.ps1 -Check` to validate the edited PNGs and compare them with the packaged graphics bank. Run `python tests/test_graphics_editor.py` to exercise editing, saving, packing, the Windows build button and the AI workflow with a local test response.
