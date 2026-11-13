"""Cut equally sized visible windows, reserving the hidden columns between them."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from PIL import Image, ImageOps, ImageDraw

def export(source, destination, width, height, gap):
    if min(width, height) < 1 or gap < 0:
        raise ValueError("Invalid window geometry")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    size = (20 * width + 19 * gap, height)
    with Image.open(source) as image:
        master = ImageOps.fit(ImageOps.exif_transpose(image).convert("RGB"), size, method=Image.Resampling.LANCZOS)
    preview = Image.new("RGB", size, "white")
    mask = Image.new("L", (width, height))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width-1, height-1), radius=width//2, fill=255)
    with TemporaryDirectory(dir=destination.parent) as tmp:
        root = Path(tmp) / "result"
        tiles = root / "切片"
        tiles.mkdir(parents=True)
        master.save(root / "取景整图.png")
        with ZipFile(root / "20张PNG.zip", "w") as archive:
            for i in range(20):
                start = i * (width + gap)
                part = master.crop((start, 0, start + width, height))
                name = f"{i+1:02d}.png"
                part.save(tiles / name)
                archive.write(tiles / name, name)
                preview.paste(part, (start, 0), mask)
        preview.save(root / "带间隔预览.png")
        with ZipFile(root / "20张PNG.zip") as archive:
            assert len(archive.namelist()) == 20 and archive.testzip() is None
        root.rename(destination)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--window", type=int, default=73)
    parser.add_argument("--height", type=int, default=2572)
    parser.add_argument("--gap", type=int, default=16)
    args = parser.parse_args()
    export(args.source, args.destination, args.window, args.height, args.gap)
