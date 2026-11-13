"""Export a panorama as twenty contiguous PNGs and a checked ZIP."""
from pathlib import Path
import argparse
import tempfile
from zipfile import ZipFile
from PIL import Image


def export(source, destination, x_gap=False, window=73.0, gap=16.0):
    if not (window > 0 and gap >= 0):
        raise ValueError("Window must be positive and gap nonnegative")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    with Image.open(source) as original:
        image = original.convert("RGBA" if "A" in original.getbands() or "transparency" in original.info else "RGB")
        profile = original.info.get("icc_profile")
    padding = 0 if x_gap else -image.width % 20
    canvas = Image.new(image.mode, (image.width + padding, image.height))
    left = padding // 2
    canvas.paste(image, (left, 0))
    for x in range(left):
        canvas.paste(image.crop((0, 0, 1, image.height)), (x, 0))
    for x in range(left + image.width, canvas.width):
        canvas.paste(image.crop((image.width - 1, 0, image.width, image.height)), (x, 0))
    width = canvas.width // 20
    if x_gap:
        width = round(canvas.width * window / (20 * window + 19 * gap))
        if width < 1 or 20 * width > canvas.width:
            raise ValueError("Image too narrow for the requested window geometry")
        preview_width = min(3000, canvas.width)
        preview_height = max(1, round(canvas.height * preview_width / canvas.width))
        preview = Image.new("RGB", (preview_width, preview_height), "white")
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        root = Path(staging) / "export"
        tiles = root / "切片"
        tiles.mkdir(parents=True)
        canvas.save(root / "整图.png", icc_profile=profile)
        archive = root / "20张PNG.zip"
        with ZipFile(archive, "w") as bundle:
            for i in range(20):
                start = round(i * (canvas.width - width) / 19) if x_gap else i * width
                part = canvas.crop((start, 0, start + width, canvas.height))
                if x_gap:
                    left_edge = round(start * preview_width / canvas.width)
                    right_edge = round((start + width) * preview_width / canvas.width)
                    thumb = part.resize((max(1, right_edge-left_edge), preview_height), Image.Resampling.LANCZOS)
                    preview.paste(thumb, (left_edge, 0), thumb.getchannel("A") if thumb.mode == "RGBA" else None)
                file = tiles / f"{i+1:02}.png"
                part.save(file, icc_profile=profile)
                with Image.open(file) as check:
                    assert check.size == part.size and check.tobytes() == part.tobytes()
                bundle.write(file, file.name)
        with ZipFile(archive) as bundle:
            assert bundle.namelist() == [f"{i:02}.png" for i in range(1, 21)]
            assert bundle.testzip() is None
        if x_gap:
            preview.save(root / "间隔预览.png")
        root.rename(destination)
    print(f"20 PNGs, {width} x {canvas.height}, padding {padding}px")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--x-gap", action="store_true")
    parser.add_argument("--window", type=float, default=73)
    parser.add_argument("--gap", type=float, default=16)
    args = parser.parse_args()
    export(args.source, args.destination, args.x_gap, args.window, args.gap)
