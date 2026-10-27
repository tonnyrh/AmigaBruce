"""Render this prototype's 4-plane A500 framebuffer (Pillow required)."""
import argparse
from pathlib import Path
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def render(source, destination, color15=None, interleaved=False):
    data = source.read_bytes()
    if len(data) != 40960:
        raise ValueError("Expected four 320x256 bitplanes")
    code = (ROOT / "amiga/main.c").read_text(encoding="utf-8")
    body = re.search(r"palette\[16\]=\{([^}]+)\}", code).group(1)
    colors = [int(value.strip(), 16) for value in body.split(",")]
    if color15 is not None:colors[15]=color15
    image = Image.new("RGB", (320, 256))
    pixels = image.load()
    for y in range(256):
        for x in range(320):
            color = sum(1 << plane for plane in range(4)
                        if data[(y*160+plane*40 if interleaved else plane*10240+y*40)+x//8] & (128 >> (x & 7)))
            value = colors[color]
            pixels[x, y] = (((value >> 8) & 15) * 17,
                            ((value >> 4) & 15) * 17, (value & 15) * 17)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.resize((960, 768), Image.Resampling.NEAREST).save(destination)
    print(destination.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--color15", type=int)
    parser.add_argument("--interleaved", action="store_true")
    args = parser.parse_args()
    render(args.source, args.destination,args.color15,args.interleaved)
