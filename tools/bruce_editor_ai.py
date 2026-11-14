"""User-triggered image proposals. No game source or API key is persisted.

OpenRouter Image API: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
Uses the selected picture as reference; proposal acceptance and native-format
validation are separate from generation. No automatic request retries.
"""
import base64
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from uuid import uuid4
from PIL import Image
from bruce_editor_data import ROOT, ALPHA, image_for, palette, convert_candidate

API = 'https://openrouter.ai/api/v1/images'
MODEL = 'black-forest-labs/flux.2-pro'


def prompt_for(asset, instruction):
    palette_text=', '.join(f'#{v:03X}' for v in palette()[0][:asset.max_pen+1])
    style = 'Use flat patches of color with a single clear shadow per material. '
    if asset.key.startswith('fighter-'):
        left,top,right,bottom = image_for(asset,asset.pixels).convert('RGBA').getchannel('A').getbbox()
        style += (f'The visible fighter is only {right-left}x{bottom-top} logical pixels. '
                  'Use 4 or 5 inks by default. Group pixels into large connected shapes. '
                  'Keep the face, belt and weapon readable at 1x. ')
    return (f'Repaint this Amiga pixel art: {asset.label}. '
            f'Draw directly on a {asset.width}x{asset.height} logical pixel grid. '
            'The reference is magnified with nearest-neighbor scaling. Each logical pixel '
            'must be one square of solid ink. Preserve its canvas, silhouette, pose and position. '
            + style + 'Use hard stair-step edges. No antialiasing, gradients, dithering or fine texture. '
            f'Use only this Amiga OCS palette: {palette_text}. '
            + instruction.strip())


def bundle(asset, pixels, instruction, model=MODEL, seed=42, directory=None):
    directory=directory or ROOT/'.tmp/graphics-ai'/(
        datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    reference=image_for(asset,pixels).convert('RGBA')
    reference.save(directory/'reference.png')
    mask=Image.new('L',(asset.width,asset.height))
    mask.putdata([0 if p==ALPHA else 255 for p in asset.pixels]);mask.save(directory/'mask.png')
    prompt=prompt_for(asset,instruction)
    (directory/'prompt.txt').write_text(prompt,encoding='utf-8')
    (directory/'palette.txt').write_text('\n'.join(f'#{v:03X}' for v in palette()[0])+'\n')
    details=dict(asset=asset.key,base=asset.identity,model=model,seed=seed,prompt=prompt,
                 reference_sha256=sha256((directory/'reference.png').read_bytes()).hexdigest())
    (directory/'request.json').write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return directory,details


def generate(asset, pixels, instruction, key=None, model=MODEL, seed=42, opener=None, directory=None):
    key=(key or os.environ.get('OPENROUTER_API_KEY','')).strip()
    if not key:raise ValueError('Enter an OpenRouter API key or set OPENROUTER_API_KEY before starting the editor.')
    if not instruction.strip():raise ValueError('Describe the change you want to make.')
    folder,details=bundle(asset,pixels,instruction,model,seed,directory)
    reference=image_for(asset,pixels).convert('RGBA')
    scale=max(1,min(12,1024//max(asset.width,asset.height)))
    reference=reference.resize((asset.width*scale,asset.height*scale),Image.Resampling.NEAREST)
    encoded=BytesIO();reference.save(encoded,format='PNG')
    payload=dict(model=model,prompt=details['prompt'],n=1,seed=seed,
                 input_references=[dict(type='image_url',image_url=dict(
                     url='data:image/png;base64,'+base64.b64encode(encoded.getvalue()).decode('ascii')))])
    request=urllib.request.Request(API,data=json.dumps(payload).encode('utf-8'),method='POST',headers={
        'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Title':'Bruce Graphics Editor'})
    try:
        with (opener or urllib.request.urlopen)(request,timeout=180) as response:
            raw=response.read(48*1024*1024+1)
            if len(raw)>48*1024*1024:raise ValueError('The generated image is too large.')
            data=json.loads(raw)
    except urllib.error.HTTPError as exc:
        # Response bodies can echo request data. Do not log them or the key.
        raise ValueError(f'OpenRouter returned HTTP {exc.code}. Check the model, API key and account credit.') from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise ValueError('Could not retrieve the generated image. Your draft and prompt are saved locally. Retry when ready.') from None
    try:
        decoded=base64.b64decode(data['data'][0]['b64_json'],validate=True)
        with Image.open(BytesIO(decoded)) as image:
            suffix={'PNG':'png','JPEG':'jpg','WEBP':'webp'}[image.format]
            if image.width*image.height>16777216:raise ValueError('The generated image is too large.')
            image.load();image=image.convert('RGBA')
    except (KeyError,IndexError,TypeError,ValueError,OSError) as exc:
        raise ValueError('The service returned an invalid image.') from exc
    source_name='source.'+suffix
    (folder/source_name).write_bytes(decoded)
    result=convert_candidate(asset,image,pixels)
    image_for(asset,result).save(folder/'candidate.png',transparency=ALPHA)
    details.update(method='OpenRouter image proposal',source_file=source_name,source_sha256=sha256(decoded).hexdigest(),
                   cost_usd=data.get('usage',{}).get('cost'))
    (folder/'result.json').write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result,details,folder
