"""Decode every GIF frame and check declared technical expectations."""
from pathlib import Path
import argparse,json
from PIL import Image

def validate(path,size=None,frames=None,duration=None,loop=None,motion=None):
    with Image.open(path) as im:
        count=getattr(im,'n_frames',1);actual_size=im.size;actual_loop=im.info.get('loop')
        if count<2:raise ValueError('Input is not an animated image')
        durations=[]
        for j in range(count):
            im.seek(j);im.convert('RGB').load()
            delay=im.info.get('duration',0)
            if delay<=0:raise ValueError(f'Missing or zero frame delay at {j}')
            durations.append(delay)
    total=sum(durations)/1000
    if size and actual_size!=tuple(size):raise ValueError(f'Size mismatch: {actual_size}')
    if frames is not None and count!=frames:raise ValueError(f'Frame count mismatch: {count}')
    if duration is not None and abs(total-duration)>.001:raise ValueError(f'Duration mismatch: {total}')
    if loop is not None and actual_loop!=loop:raise ValueError(f'Loop mismatch: {actual_loop}')
    result={'size':actual_size,'frames':count,'duration_seconds':total,'loop':actual_loop,'all_frames_decoded':True,
            'visual_acceptance':'not established by technical checks'}
    if motion:
        rows=json.loads(Path(motion).read_text(encoding='utf8'))
        if len(rows)!=count:raise ValueError('Motion log does not cover every decoded frame')
        visible=[r for r in rows if r.get('opacity',1)>1e-4]
        if not visible:raise ValueError('No visible motion samples')
        values=[float(r['growth_percent']) for r in visible]
        if any(b<a-1e-8 for a,b in zip(values,values[1:])):raise ValueError('Growth regresses while visible')
        if abs(values[0])>1e-6 or abs(max(values)-100)>1e-6:raise ValueError('Growth must visibly cover 0 through 100')
        if any(not 0<=v<=100 for v in values):raise ValueError('Growth outside declared bounds')
        result['visible_progress_0_to_100_monotonic']=True
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path)
    ap.add_argument('--size');ap.add_argument('--frames',type=int);ap.add_argument('--duration',type=float)
    ap.add_argument('--loop',type=int);ap.add_argument('--motion',type=Path);ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    size=tuple(map(int,args.size.lower().split('x'))) if args.size else None
    report=validate(args.input,size,args.frames,args.duration,args.loop,args.motion)
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(text,encoding='utf8')
    print(text)

if __name__=='__main__':main()
