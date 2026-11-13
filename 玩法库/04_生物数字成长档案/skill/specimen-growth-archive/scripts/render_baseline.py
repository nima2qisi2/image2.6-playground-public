"""Run the self-contained five-stage seahorse baseline."""
from pathlib import Path
import argparse,importlib,os,sys,json,shutil,subprocess,time

def dependencies():
    extra=os.environ.get('SPECIMEN_CV2_PATH')
    if extra:sys.path.insert(0,extra)
    for module in ['numpy','PIL','cv2']:
        try:importlib.import_module(module)
        except ImportError as exc:raise SystemExit(f'Missing dependency {module}; use the existing environment or configure SPECIMEN_CV2_PATH.') from exc

def find_ffmpeg(explicit):
    candidate=explicit or os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
    if not candidate:
        try:
            import imageio_ffmpeg
            candidate=imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:pass
    if not candidate or not Path(candidate).is_file():raise SystemExit('Provide an existing FFmpeg binary with --ffmpeg.')
    subprocess.run([str(candidate),'-version'],check=True,stdout=subprocess.DEVNULL)
    return str(candidate)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--mode',choices=['preview','keyframes','full'],default='preview')
    ap.add_argument('--ffmpeg');ap.add_argument('--font-dir',type=Path,default=Path('C:/Windows/Fonts'))
    args=ap.parse_args();dependencies()
    import numpy as np
    from PIL import Image,ImageDraw
    import archive_layout as g
    root=Path(__file__).resolve().parents[1];out=args.out.resolve()
    if out==root or root in out.parents:raise SystemExit('Output must be outside the skill installation.')
    for name in ['arial.ttf','arialbd.ttf','msyhl.ttc']:
        if not (args.font_dir/name).is_file():raise SystemExit(f'Missing baseline font: {name}; configure --font-dir.')
    ffmpeg=find_ffmpeg(args.ffmpeg) if args.mode=='full' else None
    out.mkdir(parents=True,exist_ok=True);g.FONT_DIR=args.font_dir
    layout=g.Layout()
    if args.mode=='preview':
        times=[.32,1.6,3.8,5.8,7.8,8.2,8.6,9,9.8,10.5]
        sheet=Image.new('RGB',(5*216,2*310),(4,13,13));d=ImageDraw.Draw(sheet)
        for j,t in enumerate(times):
            im=layout.render(t,True);im.save(out/f'preview-{t:05.2f}.png')
            x=j%5*216;y=j//5*310
            sheet.paste(im.resize((216,288),Image.Resampling.LANCZOS),(x,y));d.text((x+5,y+291),f'{t:.2f}s',fill='white')
        sheet.save(out/'preview-sheet.jpg',quality=95)
        (out/'motion-samples.json').write_text(json.dumps(layout.checks),encoding='utf8')
        print(out/'preview-sheet.jpg');return
    if args.mode=='keyframes':
        result=[]
        for p in range(5):
            rgb,a,_=layout.m.frame(p)
            assert np.array_equal(rgb,layout.m.rgb[p]) and np.array_equal(a,layout.m.alpha[p])
            layout.phase=lambda t,p=p:(float(p),1.)
            layout.render(10.5).save(out/f'keyframe-{p+1:02d}.png')
            limits=[]
            for q in [p-1e-4,p+1e-4]:
                if not 0<=q<=4:continue
                c,b,_=layout.m.frame(q);fg=(a>.1)|(b>.1)
                changed=int(np.count_nonzero(np.abs(a-b)>.5))
                assert changed==0,f'Endpoint discontinuity at {q}'
                limits.append({'phase':q,'alpha_mae':float(np.abs(a-b)[fg].mean()),'rgb_mae':float(np.abs(rgb-c)[fg].mean()),'alpha_jump_pixels_gt_half':changed})
            result.append({'phase':p,'exact_endpoint':True,'limits':limits})
        (out/'endpoint-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('5 source endpoints and adjacent-phase limits passed');return
    frames=out/'frames';frames.mkdir(exist_ok=True);start=time.time()
    mp4=out/'specimen-growth.mp4';gif=out/'specimen-growth.gif'
    command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','720x960','-framerate','25','-i','-','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for j in range(300):
            t=j/25;im=layout.render(t,True)
            if t>11.45:im=Image.blend(Image.new('RGB',(720,960),(4,13,13)),im,1-g.reveal(t,11.45,.51))
            if 1.6<t<11.1:
                a=np.array(im).astype(int)
                assert np.max(np.ptp(a[774],axis=0))==0
                assert np.max(np.ptp(a[775],axis=0))==0
                assert np.max(np.ptp(a[920,36:685],axis=0))==0
            im.save(frames/f'{j:04d}.png',compress_level=2);encoder.stdin.write(im.tobytes())
            if j%25==0:print(f'{j}/300, {time.time()-start:.1f}s',flush=True)
        encoder.stdin.close()
        if encoder.wait():raise RuntimeError('MP4 encoding failed')
    except BaseException:
        encoder.kill();encoder.wait();raise
    log=out/'motion-samples.json';log.write_text(json.dumps(layout.checks),encoding='utf8')
    graph='split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle'
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','25','-i',str(frames/'%04d.png'),'-vf',graph,'-loop','0',str(gif)],check=True)
    from validate_animation import validate
    report=validate(gif,size=(720,960),frames=300,duration=12,loop=0,motion=log)
    report['preencode_integer_pixel_rules']='passed at all full-opacity frames'
    report['visual_review']='pending; inspect full-frame and enlarged contact sheets plus decoded GIF'
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(gif)

if __name__=='__main__':main()
