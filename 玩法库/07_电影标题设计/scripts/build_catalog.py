"""Validate asset records, rebuild the offline gallery and README, and package the skill."""
from pathlib import Path
import hashlib
import html
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def build():
    styles = json.loads((ROOT / "catalog/styles.json").read_text("utf-8"))
    manifest = json.loads((ROOT / "assets/manifest.json").read_text("utf-8"))
    records = {row["id"]: row for row in manifest}
    assert len(styles) == len(records) == 32
    figures = []
    cells = []
    index = ["# 32 款成品选款表", "", "| 编号 | 风格 | 成品 | 提示词 |", "|---|---|---|---|"]
    for style in styles:
        key = style["id"]
        record = records[key]
        path = ROOT / record["file"]
        assert path.is_file(), path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], path
        image = html.escape(record["file"], quote=True)
        name = html.escape(style["name_zh"])
        figures.append(f'<figure><a href="{image}" target="_blank"><img loading="lazy" src="{image}" alt="{key} {name}"></a><figcaption>{key} · {name}</figcaption></figure>')
        cells.append(f'**{key} {style["name_zh"]}**<br>[![{key}]({record["file"]})]({record["file"]})')
        index.append(f'| {key} | {style["name_zh"]} · {style["name"]} | [查看](../{record["file"]}) | [提示词](../prompts/{key.lower()}.md) |')
    page = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DMIAO · 32 款电影标题</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111315;color:#eee;font-family:system-ui,sans-serif}header{padding:40px 3vw 28px}h1{font-size:32px;margin:0 0 12px}p{color:#c4b8a5;margin:0}main{padding:0 3vw 40px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px}figure{margin:0;background:#1e2226}img{display:block;width:100%;aspect-ratio:16/9;object-fit:contain}figcaption{padding:12px;font-size:15px;color:#eddbb9}@media(max-width:1100px){main{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){main{grid-template-columns:1fr}h1{font-size:24px}}@media print{main{grid-template-columns:repeat(4,1fr)}figure{break-inside:avoid}}</style>
<header><h1>DMIAO · 32 款电影标题</h1><p>点击图片查看原尺寸 · AI 生成视觉预览 · 按 CT 编号选款</p></header><main>""" + "".join(figures) + "</main></html>"
    (ROOT / "preview.html").write_text(page, encoding="utf-8")
    table = ["| " + " | ".join(cells[i:i+4]) + " |" for i in range(0,32,4)]
    table.insert(1, "|---|---|---|---|")
    readme = """# Cinematic Title Director

用 CT-01 至 CT-32 选择电影片头或品牌标题的字形、构图和光线，输入自己的文字，生成对应视觉。

[打开 32 款成品画廊](preview.html) · [按编号查提示词](catalog/index.md)

以下为以 DMIAO 为主题的 AI 生成预览，CT-27 沿用 DMIAO COFFEE 横稿。点击每张图片可看原图。生成字形以成图为准，用户可以选择后期用授权字体重新排字。

""" + "\n".join(table) + """

## 使用
将整个仓库目录命名为 cinematic-title-director，放入支持本地 Skill 的工具的技能目录。也可以直接复制 prompts 中的英文提示词，替换 TITLE、FORMAT 和 ASPECT_RATIO。

例如“CT-11 DMIAO”，沿用该款横幅日蚀构图。“CT-27，标题换成 DMIAO COFFEE，做 16:9 品牌海报”，按标题长度安排主副行。

[Skill 入口](SKILL.md) · [字体候选](fonts/verified-ofl-candidates.csv) · [素材及许可](NOTICE.md) · [生成记录](assets/manifest.json) · [MIT 许可](LICENSE)

维护时运行 python scripts/build_catalog.py，校验文件哈希并重建画廊、目录及 ZIP。
"""
    readme += "\n\n## 使用说明与案例\n\n[完整使用方法、素材来源和注意事项](使用与案例.md) · [5 秒案例轮播](assets/dmiao-32-styles-5s.gif)\n\n![32 款案例轮播](assets/dmiao-32-styles-5s.gif)\n"
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    (ROOT / "catalog/index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    for file in ROOT.rglob("*.md"):
        for link in re.findall(r"\]\(([^)]+)\)", file.read_text("utf-8")):
            if "://" not in link:
                assert (file.parent / link).exists(), (file, link)
    target = ROOT.with_suffix(".zip")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as package:
        for file in files:
            package.write(file, Path("cinematic-title-director") / file.relative_to(ROOT))
    with zipfile.ZipFile(target) as package:
        assert package.testzip() is None
    print(f"Validated {len(records)} images. Packaged {len(files)} files.")

if __name__ == "__main__":
    build()
