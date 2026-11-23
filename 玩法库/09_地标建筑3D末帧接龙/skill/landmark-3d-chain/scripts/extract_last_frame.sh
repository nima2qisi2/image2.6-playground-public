#!/usr/bin/env bash
# extract_last_frame.sh —— 提取一段视频的最后一帧，作为下一段图生视频的唯一参考图。
#
# 末帧接龙的铁律：下一段只喂这一帧，不再喂静止画或任何其他参考图。
#
# 用法：
#   ./extract_last_frame.sh <输入视频.mp4> <输出末帧.png>
#
# 示例：
#   ./extract_last_frame.sh seg1-orbit.mp4 chain/seg1_last.png
set -euo pipefail

IN="${1:?用法: extract_last_frame.sh <输入视频.mp4> <输出末帧.png>}"
OUT="${2:?用法: extract_last_frame.sh <输入视频.mp4> <输出末帧.png>}"

mkdir -p "$(dirname "$OUT")"

# -sseof -0.05：从文件结尾前 0.05 秒处开始解码，只取 1 帧，即视频的最后一帧。
ffmpeg -v error -sseof -0.05 -i "$IN" -frames:v 1 "$OUT"

echo "末帧已提取 -> $OUT"
