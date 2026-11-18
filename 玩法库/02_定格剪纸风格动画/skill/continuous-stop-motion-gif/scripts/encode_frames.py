"""Encode complete numbered PNG frames. This script does not create motion."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from PIL import Image, ImageChops, ImageStat


def record(path, hashes=False):
    digests, duration = [], 0
    with Image.open(path) as gif:
        size, loop, count = gif.size, gif.info.get('loop'), gif.n_frames
        first = last = None
        for i in range(count):
            gif.seek(i)
            duration += gif.info.get('duration', 0)
            rgb = gif.convert('RGB')
            if first is None:
                first = rgb.copy()
            last = rgb.copy()
            if hashes:
                digests.append(hashlib.sha256(rgb.tobytes()).hexdigest())
        seam = sum(ImageStat.Stat(ImageChops.difference(first, last)).mean) / 3
    return dict(size=list(size), frames=count, duration_ms=duration, loop=loop,
                bytes=path.stat().st_size, seam_mae=seam), digests


def executable(explicit, name, imageio=False):
    if explicit:
        if not Path(explicit).is_file():
            raise ValueError(f'Executable does not exist: {explicit}')
        return str(Path(explicit).resolve())
    found = shutil.which(name)
    if not found and imageio:
        try:
            import imageio_ffmpeg
            found = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--frames', type=Path, required=True)
    ap.add_argument('--gif', type=Path, required=True)
    ap.add_argument('--fps', type=float, required=True)
    ap.add_argument('--width', type=int)
    ap.add_argument('--mp4', type=Path)
    ap.add_argument('--ffmpeg')
    ap.add_argument('--gifsicle')
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    if not math.isfinite(args.fps) or not 0 < args.fps <= 100:
        ap.error('fps must be finite and in (0, 100]; GIF uses centiseconds')
    if args.width is not None and args.width < 1:
        ap.error('width must be positive')
    natural = lambda p: [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', p.name)]
    files = sorted(args.frames.glob('*.png'), key=natural)
    if not files:
        ap.error('No PNG frames found')
    outputs = [args.gif, args.gif.with_suffix('.json')] + ([args.mp4] if args.mp4 else [])
    if len({p.resolve() for p in outputs}) != len(outputs):
        ap.error('Output paths must be distinct')
    for out in outputs:
        if out.exists() and not args.overwrite:
            ap.error(f'Output exists; choose a new path or use --overwrite: {out}')
    if any(p.resolve() in {f.resolve() for f in files} for p in outputs):
        ap.error('Outputs must not overwrite input frames')
    ffmpeg = executable(args.ffmpeg, 'ffmpeg', True) if args.mp4 else None
    if args.mp4 and not ffmpeg:
        ap.error('MP4 needs existing FFmpeg or imageio-ffmpeg; use --ffmpeg')
    gifsicle = executable(args.gifsicle, 'gifsicle')
    images, original = [], None
    for path in files:
        with Image.open(path) as im:
            if original is None:
                original = im.size
            if im.size != original:
                ap.error(f'Inconsistent frame dimensions: {path}')
            if 'A' in im.getbands() and im.getchannel('A').getextrema()[0] < 255:
                ap.error(f'Composite transparent frames onto a background first: {path}')
            w = args.width or im.width
            h = max(1, round(im.height * w / im.width))
            images.append(im.convert('RGB').resize((w, h), Image.Resampling.LANCZOS))
    sample_count = min(16, len(images))
    ids = [round(i*(len(images)-1)/max(1, sample_count-1)) for i in range(sample_count)]
    thumbs = []
    for i in ids:
        thumb = images[i].copy(); thumb.thumbnail((320, 320)); thumbs.append(thumb)
    tw, th = thumbs[0].size
    atlas = Image.new('RGB', (tw*4, th*math.ceil(len(thumbs)/4)))
    for i in range(4*math.ceil(len(thumbs)/4)):
        atlas.paste(thumbs[min(i, len(thumbs)-1)], ((i%4)*tw, (i//4)*th))
    palette = atlas.quantize(256, method=Image.Quantize.MEDIANCUT)
    indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]
    durations = [(round((i+1)*100/args.fps)-round(i*100/args.fps))*10 for i in range(len(images))]
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    with tempfile.TemporaryDirectory(prefix='stop-motion-', dir=args.gif.parent) as tmp:
        temp = Path(tmp)/'encoded.gif'
        indexed[0].save(temp, save_all=True, append_images=indexed[1:], duration=durations,
                        loop=0, disposal=1, optimize=True)
        before, before_hashes = record(temp, bool(gifsicle))
        if gifsicle:
            optimized = Path(tmp)/'optimized.gif'
            subprocess.run([gifsicle, '-O3', '--careful', str(temp), '-o', str(optimized)],
                           check=True, creationflags=flags)
            after, after_hashes = record(optimized, True)
            if (before_hashes != after_hashes or before['duration_ms'] != after['duration_ms']
                    or before['loop'] != after['loop']):
                raise RuntimeError('Optimization changed decoded frames, timing, or loop')
            shutil.copy2(optimized, args.gif)
        else:
            shutil.copy2(temp, args.gif)
    if args.mp4:
        w, h = images[0].size
        proc = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo',
            '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(args.fps), '-i', '-',
            '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-crf', '17',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(args.mp4)],
            stdin=subprocess.PIPE, creationflags=flags)
        try:
            for im in images:
                proc.stdin.write(im.tobytes())
        finally:
            proc.stdin.close()
        if proc.wait():
            raise RuntimeError('FFmpeg encoding failed')
    info, _ = record(args.gif)
    info.update(input_frames=len(images), source_size=list(original), requested_fps=args.fps,
                optimized_losslessly=bool(gifsicle), mp4=str(args.mp4.resolve()) if args.mp4 else None,
                visual_acceptance='not established by encoding checks')
    args.gif.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
