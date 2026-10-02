from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
revision=sys.argv[1] if len(sys.argv)>1 else 'v002'
folder=ROOT/'Renders/Yard'/revision;files=sorted(folder.glob('SM_*.png'))
assert len(files)==17,len(files)
size=336;rows=(len(files)+3)//4
sheet=Image.new('RGB',(size*4,(size+28)*rows),(33,36,39));draw=ImageDraw.Draw(sheet)
for i,p in enumerate(files):
    x=(i%4)*size;y=(i//4)*(size+28)
    with Image.open(p) as im:
        im=im.convert('RGB');im.thumbnail((size,size));sheet.paste(im,(x,y+28))
    draw.text((x+10,y+8),p.stem.removeprefix('SM_').removesuffix('_A'),fill='white')
sheet.save(folder/'Contact_Sheet.jpg',quality=93)
print(folder/'Contact_Sheet.jpg')
