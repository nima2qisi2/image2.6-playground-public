"""Create paged contact sheets from all decoded animation frames."""
from pathlib import Path
import argparse,json,math
from PIL import Image,ImageDraw

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--per-page',type=int,default=50)
    ap.add_argument('--crop',help='left,top,right,bottom');args=ap.parse_args()
    if not 1<=args.per_page<=100:raise SystemExit('--per-page must be 1 through 100')
    crop=tuple(map(int,args.crop.split(','))) if args.crop else None
    if crop and (len(crop)!=4 or crop[0]<0 or crop[1]<0 or crop[2]<=crop[0] or crop[3]<=crop[1]):raise SystemExit('Invalid crop rectangle')
    args.out.mkdir(parents=True,exist_ok=True)
    pages=[];elapsed=0;cols=5;cellw,cellh=180,260
    with Image.open(args.input) as im:
        if crop and (crop[2]>im.width or crop[3]>im.height):raise SystemExit('Crop exceeds the image')
        for j in range(im.n_frames):
            if j%args.per_page==0:
                sheet=Image.new('RGB',(cols*cellw,math.ceil(args.per_page/cols)*cellh),(4,13,13));pages.append(sheet)
            im.seek(j);thumb=im.convert('RGB')
            if crop:thumb=thumb.crop(crop)
            thumb.thumbnail((cellw-4,cellh-23),Image.Resampling.LANCZOS)
            local=j%args.per_page;x=local%cols*cellw;y=local//cols*cellh
            sheet.paste(thumb,(x+(cellw-thumb.width)//2,y+21))
            ImageDraw.Draw(sheet).text((x+5,y+4),f'{j:03d} / {elapsed/1000:.2f}s',fill='white')
            elapsed+=im.info.get('duration',0)
        count=im.n_frames
    for i,sheet in enumerate(pages):sheet.save(args.out/f'review-{i+1:02d}.jpg',quality=95)
    (args.out/'coverage.json').write_text(json.dumps({'frames_represented':count,'pages':len(pages),'crop':crop,'visual_review':'pending'},indent=2),encoding='utf8')
    print(f'{count} frames represented in {len(pages)} pages')

if __name__=='__main__':main()
