# 包内海马基准复跑

## 范围与状态

本基准取自 2026-11-11 的 v21 海马复测：五个独立摄影风格阶段，720×960、25 fps、12 秒。原案例已经技术检查和视觉自检；用户随后要求先制作 Skill，**没有明确表示对最终视觉验收通过**。

素材属于属级艺术发育示意。确切物种、真实天龄、物理尺寸及同一个体连续发育均未被本基准证明。

包内包括预乘摄影端点数组、原始 UI 模板、对应点／尾中心线／鳍区配置和成熟期对照图。运行不依赖本地 v4、v8、v13、v14、v21 等历史工程目录。

## 依赖

Python 3.10+；`numpy`、`Pillow`、`opencv-python`；完整导出还需 FFmpeg（libx264、palettegen、paletteuse）。当前基准使用 Windows 的 Arial、Arial Bold 和微软雅黑细体，不随包分发字体。

先检查现有环境，不要静默安装或下载替代环境。`--font-dir` 指向含 `arial.ttf`、`arialbd.ttf`、`msyhl.ttc` 的字体目录；移植至其他字体时需调整字体映射并重新检查中文、字宽与基线。

脚本优先使用当前 Python 的 OpenCV。已有单独依赖目录时，可用环境变量 `SPECIMEN_CV2_PATH` 加入模块搜索路径；这只定位依赖，不导入旧版形变工程。

使用当前机器已有的 Python 和依赖；如使用独立 OpenCV 目录，将其路径传给 `SPECIMEN_CV2_PATH`。

## 命令

以下 `<skill>` 表示此技能文件夹的绝对路径，`<out>` 为独立输出目录。不要把缓存或生成文件写进安装目录。

```powershell
python <skill>/scripts/render_baseline.py --out <out> --mode preview
python <skill>/scripts/render_baseline.py --out <out> --mode keyframes
python <skill>/scripts/render_baseline.py --out <out> --mode full --ffmpeg <ffmpeg.exe>
python <skill>/scripts/validate_animation.py <out>/specimen-growth.gif --size 720x960 --frames 300 --duration 12 --loop 0 --motion <out>/motion-samples.json --report <out>/verification.json
python <skill>/scripts/contact_sheet.py <out>/specimen-growth.gif --out <out>/gif-review --per-page 50 --crop 138,61,686,775
```

FFmpeg 也可来自 `FFMPEG_BINARY`、PATH 或现有 `imageio_ffmpeg` 包；脚本不会下载。

- `preview`：10 个实际时间点的版式与动效入场采样，生成单图与联系表。
- `keyframes`：五个摄影端点静帧和阶段两侧极限报告；断言精确返回摄影数组，并检查邻近阶段的 alpha 变化。
- `full`：300 张源帧、MP4、GIF、进度日志以及技术检查。编码完成后逐帧解码 GIF。

`contact_sheet.py` 的裁切矩形为左、上、右、下，不是宽高。另以适合主体当前位置的局部裁切检查尾鳍，不能只用整版缩略图验收。

## 不能直接泛化的部分

`project.json` 与 `faithful_motion.py` 共同限定了海马的 15 个结构点、卷尾传输和背鳍对应。`archive_layout.py` 是此版式的固定像素坐标，不是任意分辨率响应式模板。

新主体请沿用视觉原则与检查流程，另建项目素材、遮罩、关键点和必要的局部形变器。新主体有不同阶段数、横长轮廓或拓扑改变时，重新设计版面与对应关系；不能编辑 `names` 就宣称已支持其他生物。

## 历史错误的边界

更早版本曾用圆管和单张成年背鳍纹理替代原结构；这些实现不在本包中。当前包保留 v21 原图像素搬运方案。原素材已带的白色网络线有部分随主体保留；为新案例准备无标注干净素材更便于维护。

包内 `mature-reference.png` 用于对照当前成熟期版面；它是本案例的回归参照，不是所有主体都必须模仿的形态。
