"""Render an explicit static-photo sequence with an optional final signature."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageOps


@contextmanager
def staging_directory(parent: Path):
    parent = parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / ('.photo-flash-gif-' + uuid.uuid4().hex)
    stage.mkdir()
    try:
        yield stage
    finally:
        if stage.resolve().parent != parent or not stage.name.startswith('.photo-flash-gif-'):
            raise RuntimeError('Refusing cleanup outside the selected staging parent')
        shutil.rmtree(stage)


def integer(value, field, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{field} must be an integer >= {minimum}')
    return value


def milliseconds(value, field):
    value = integer(value, field, 10)
    if value % 10:
        raise ValueError(f'{field} must be a multiple of 10 ms for GIF')
    return value


def load_job(manifest: Path):
    job = json.loads(manifest.read_text(encoding='utf-8-sig'))
    if not isinstance(job, dict):
        raise ValueError('Manifest must be a JSON object')
    images = job.get('images')
    if not isinstance(images, list) or len(images) < 2:
        raise ValueError('images must contain at least two static images')
    paths = {}
    for entry in images:
        if not isinstance(entry, dict):
            raise ValueError('Each image must contain id and path')
        key, raw_path = entry.get('id'), entry.get('path')
        if not isinstance(key, str) or not key.strip() or key in paths:
            raise ValueError('Every image needs a nonempty, unique string id')
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError(f'Invalid path for {key}')
        path = Path(raw_path).expanduser()
        path = (manifest.parent / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f'Missing image {key}: {path}')
        paths[key] = path
    order = job.get('order', list(paths))
    if (not isinstance(order, list) or any(not isinstance(k, str) for k in order)
            or len(order) != len(paths) or set(order) != set(paths)):
        raise ValueError('order must contain every image id exactly once')
    size = job.get('size')
    if not isinstance(size, list) or len(size) != 2:
        raise ValueError('size must be [width, height]')
    size = tuple(integer(v, 'size', 1) for v in size)
    fit = job.get('fit', 'contain')
    if fit not in ('contain', 'cover'):
        raise ValueError('fit must be contain or cover')
    background = ImageColor.getrgb(job.get('background', '#000000'))
    if len(background) != 3:
        raise ValueError('background must be an opaque RGB color')
    default_ms = milliseconds(job.get('duration_ms', 120), 'duration_ms')
    overrides = job.get('durations_ms', {})
    if not isinstance(overrides, dict) or set(overrides) - set(paths):
        raise ValueError('durations_ms must map existing image ids to milliseconds')
    durations = {k: milliseconds(overrides.get(k, default_ms), f'duration for {k}') for k in paths}
    signature = job.get('signature')
    if signature is not None:
        if not isinstance(signature, dict) or signature.get('image_id') not in paths:
            raise ValueError('signature.image_id must identify an existing image')
        signature_id = signature['image_id']
        if 'order' in job and order[-1] != signature_id:
            raise ValueError('Explicit order must put the signature at the end')
        order = [k for k in order if k != signature_id] + [signature_id]
        durations[signature_id] = milliseconds(signature.get('duration_ms', 600), 'signature duration')
    loop = integer(job.get('loop', 0), 'loop')
    if loop > 65535:
        raise ValueError('GIF loop must not exceed 65535')
    sources, frames = {}, []
    for key in order:
        path = paths[key]
        with Image.open(path) as source:
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError(f'{key} is animated; provide a static image')
            image = ImageOps.exif_transpose(source).convert('RGBA')
        source_size = image.size
        opaque = Image.new('RGBA', image.size, background + (255,))
        opaque.alpha_composite(image)
        image = opaque.convert('RGB')
        crop = None
        if fit == 'contain':
            resized = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
            frame = Image.new('RGB', size, background)
            frame.paste(resized, ((size[0]-resized.width)//2, (size[1]-resized.height)//2))
        else:
            frame = ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            width = min(image.width, image.height * size[0] / size[1])
            height = min(image.height, image.width * size[1] / size[0])
            crop = [(image.width-width)/2, (image.height-height)/2,
                    (image.width+width)/2, (image.height+height)/2]
        frames.append(frame)
        sources[key] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'source_size': source_size, 'center_crop_xyxy': crop}
    return {'order': order, 'size': size, 'fit': fit, 'background': background,
            'durations_ms': [durations[k] for k in order], 'loop': loop,
            'signature_id': signature['image_id'] if signature else None, 'sources': sources}, frames


def identical(a, b):
    return ImageChops.difference(a, b).getbbox() is None


def render(plan, frames, output_dir: Path, overwrite=False):
    targets = [output_dir / name for name in ('flash.gif', 'contact-sheet.jpg', 'report.json')]
    inputs = {Path(v['path']).resolve() for v in plan['sources'].values()}
    for target in targets:
        if target.resolve() in inputs:
            raise ValueError('An output would overwrite an input image')
        if target.exists() and not overwrite:
            raise FileExistsError(f'Output exists: {target}; use a new directory or --overwrite')
    indexed = [frame.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                             dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]
    expected, expected_ms = [], []
    for frame, duration in zip(indexed, plan['durations_ms']):
        rgb = frame.convert('RGB')
        if expected and identical(rgb, expected[-1]):
            expected_ms[-1] += duration
        else:
            expected.append(rgb)
            expected_ms.append(duration)
    if max(expected_ms) > 655350:
        raise ValueError('A merged GIF frame exceeds the 655350 ms format limit')
    with staging_directory(output_dir.parent) as temp:
        gif_path = temp / 'flash.gif'
        indexed[0].save(gif_path, save_all=True, append_images=indexed[1:],
                        duration=plan['durations_ms'], loop=plan['loop'], disposal=2, optimize=False)
        encoded_ms = []
        with Image.open(gif_path) as gif:
            if gif.size != plan['size'] or gif.info.get('loop') != plan['loop']:
                raise RuntimeError('GIF size or loop verification failed')
            if gif.n_frames != len(expected):
                raise RuntimeError('Unexpected encoded frame count')
            for i in range(gif.n_frames):
                gif.seek(i)
                encoded_ms.append(gif.info.get('duration'))
                if not identical(gif.convert('RGB'), expected[i]):
                    raise RuntimeError(f'GIF frame {i+1} differs from the expected image')
        if encoded_ms != expected_ms:
            raise RuntimeError('GIF timing verification failed')
        columns = min(5, len(frames))
        width = 180
        height = max(1, round(width * plan['size'][1] / plan['size'][0]))
        sheet = Image.new('RGB', (columns*width, ((len(frames)+columns-1)//columns)*(height+36)), '#181818')
        draw = ImageDraw.Draw(sheet)
        timeline, elapsed = [], 0
        for i, (key, frame, duration) in enumerate(zip(plan['order'], indexed, plan['durations_ms'])):
            x, y = i % columns * width, i // columns * (height+36)
            sheet.paste(frame.convert('RGB').resize((width, height), Image.Resampling.LANCZOS), (x, y))
            draw.text((x+5, y+height+4), f'{i+1:02d} | {duration} ms', fill='white')
            # Stable IDs remain intact in report.json; escape unusual glyphs on the contact sheet.
            label = key.encode('ascii', 'backslashreplace').decode('ascii')
            draw.text((x+5, y+height+19), label[:25], fill='white')
            timeline.append({'position': i+1, 'image_id': key, 'start_ms': elapsed,
                             'duration_ms': duration, 'signature': key == plan['signature_id']})
            elapsed += duration
        sheet.save(temp / 'contact-sheet.jpg', quality=94)
        report = {**plan, 'status': 'generated_and_file_checked', 'output': str(targets[0].resolve()),
                  'file_bytes': gif_path.stat().st_size, 'logical_display_count': len(frames),
                  'encoded_frame_count': len(expected), 'encoded_frame_durations_ms': encoded_ms,
                  'cycle_duration_ms': elapsed, 'timeline': timeline,
                  'verification': {'decoded_frames_match': True, 'timing_matches': True,
                                   'loop_matches': True, 'dimensions_match': True}}
        (temp / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        output_dir.mkdir(parents=True, exist_ok=True)
        for target in targets:
            shutil.copy2(temp / target.name, target)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        plan, frames = load_job(args.manifest.resolve())
        if args.plan_only:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0
        if args.output_dir is None:
            raise ValueError('--output-dir is required unless --plan-only is used')
        report = render(plan, frames, args.output_dir.resolve(), args.overwrite)
        print(json.dumps({k: report[k] for k in ('output', 'file_bytes', 'logical_display_count',
                                               'encoded_frame_count', 'cycle_duration_ms', 'signature_id')},
                         ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
