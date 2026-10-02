"""Build a labelled review sheet from rendered cameras. Does not change renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
ROOT=Path(__file__).resolve().parents[1]
revision=sys.argv[1]
folder=ROOT/'Renders/Checkpoint_01'/revision
files=[p for p in sorted(folder.glob('*.png')) if p.name[:2] in [f'{i:02}' for i in range(1,10)]]
assert len(files)==9, 'Wait for all nine views before making the contact sheet'
im=Image.new('RGB',(1440,1536),(36,39,42));d=ImageDraw.Draw(im)
for i,p in enumerate(files):
    with Image.open(p) as src:
        src=src.convert('RGB');src.thumbnail((480,480))
        x=(i%3)*480;y=(i//3)*512
        im.paste(src,(x,y+28))
        d.text((x+12,y+8),p.stem.replace('_',' '),fill='white')
im.save(folder/'Contact_Sheet.jpg',quality=94)
print(folder/'Contact_Sheet.jpg')
