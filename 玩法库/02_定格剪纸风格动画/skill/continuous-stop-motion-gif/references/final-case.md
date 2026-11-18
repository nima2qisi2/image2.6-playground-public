# 小红帽 · 门后的影子：定稿工程

## 结构与规格

`assets/red-hood-final/film.py` 为唯一成片入口，调用同目录 `base_story.py`、`render_extended.py` 和 `资产/`。两份基础模块保留分层与动作函数，本包不提供旧版成片。

母版 1600×900，24 fps，22 秒，528 帧；大部分姿态以 12 Hz 更新。声音由 NumPy 合成，48 kHz 双声道，无对白。三个独立近景以局部像素位移和镜头运动为主。角色蒙版和关节坐标专用于包内资产。

## 运行

将 `assets/red-hood-final` 整个复制到项目的 `work/red-hood-final`，进入该副本，在 PowerShell 中运行：

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
$renderPython = (Resolve-Path './.venv/Scripts/python.exe').Path
$renderFFmpeg = & $renderPython -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'
& $renderPython film.py
& $renderPython film.py --ffmpeg $renderFFmpeg
```

第一条渲染命令只生成 `镜头检查.jpg`；第二条另外生成 `拟音与环境.wav` 和 `小红帽_门后的影子_6.2重制.mp4`。脚本会覆盖工作目录的同名输出，因此先复制工程，修改时保存新版本。

## GIF

使用已有 FFmpeg 从母版提取完整帧：

```powershell
New-Item -ItemType Directory -Path frames | Out-Null
& $renderFFmpeg -i '小红帽_门后的影子_6.2重制.mp4' -vf fps=12 -an 'frames/%04d.png'
```

随后运行本 Skill 的 `scripts/encode_frames.py`，传入 `--frames <完整帧目录> --gif <新输出路径> --fps 12 --width 640`。可通过 `--gifsicle <可执行文件>` 无损优化；编码器会检查优化前后解码像素和时序。GIF 为母版的缩小、256 色版本，结尾淡黑再重播，不宣称无缝循环。

这次 640×360 成片 GIF 无损优化后仍为 36,818,077 字节，未达到 15 MB。精确体积是既有版本实测，重新编码可能有差异。要求进一步缩小且画质、分辨率、时序均不变时，不能承诺一定达到目标。

## 已有检查范围

定稿完整音视频解码通过；检查过 56 个抽帧时间点。音频源峰值约 -4.81 dBFS，未检出削波，但未实际试听。用户指定本版为定稿不替代尚未进行的音频试听。后续修改需检查实际新输出，不沿用旧版结论。

十二张 PNG 为本项目生成素材：九张基础素材和三个新增机位。实际提示词保存在同目录其他参考文件中；底层生图模型版本未记录，未包含外部参考视频。
