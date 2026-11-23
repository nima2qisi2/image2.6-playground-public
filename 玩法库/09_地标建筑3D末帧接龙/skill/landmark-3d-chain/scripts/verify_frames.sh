#!/usr/bin/env bash
# verify_frames.sh —— 成片技术校验 + 接点抽帧。
#
# 做两件事：
#   1. ffprobe 实测分辨率、帧率、总帧数、时长与音轨（目标：1280x720 / 24fps / 720 帧 / 30.000s / AAC）。
#   2. 抽出两个接点前后的帧（9.9s vs 10.1s、19.9s vs 20.1s），供人工对比构图是否连续、有无跳帧。
#      另抽每段中点帧（5s / 15s / 25s），供检查运镜落点与结构是否增生（屋顶层数、台基层数）。
#
# 用法：
#   ./verify_frames.sh <成片.mp4> [抽帧输出目录]
#
# 示例：
#   ./verify_frames.sh final-30s.mp4 frames/final
set -euo pipefail

IN="${1:?用法: verify_frames.sh <成片.mp4> [抽帧输出目录]}"
OUTDIR="${2:-frames/verify}"
mkdir -p "$OUTDIR"

echo "== ffprobe 实测 =="
ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames \
  -show_entries format=duration \
  -of default=noprint_wrappers=1 "$IN"

echo "== 抽帧（接点对比 + 每段中点） =="
for t in 5 9.9 10.1 15 19.9 20.1 25 29.9; do
  ffmpeg -v error -ss "$t" -i "$IN" -frames:v 1 "$OUTDIR/f_${t}.png"
  echo "  $OUTDIR/f_${t}.png"
done

echo "人工检查要点："
echo "  - f_9.9 与 f_10.1、f_19.9 与 f_20.1 构图应几乎一致，无跳帧感；"
echo "  - 三个中点帧里屋顶层数、台基层数不得增减，画面不得多出不存在的建筑。"
