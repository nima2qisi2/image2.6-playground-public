#!/usr/bin/env bash
# concat_exact_30s.sh —— 把 3 段各 10 秒的视频硬拼成精确 30.000s / 720 帧的成片。
#
# 为什么必须截帧数：三段直接 concat 会多出 1 帧，成片变成 30.07s，不合格。
# 本脚本重编码并用 -frames:v 720 锁死总帧数，音轨用 atrim 截到 30 秒。
#
# 前提：三段同为 1280×720、24fps（不同规格请先各自转码统一）。
#
# 用法：
#   ./concat_exact_30s.sh <第1段.mp4> <第2段.mp4> <第3段.mp4> <输出成片.mp4>
#
# 示例：
#   ./concat_exact_30s.sh seg1.mp4 seg2.mp4 seg3.mp4 final-30s.mp4
set -euo pipefail

SEG1="${1:?用法: concat_exact_30s.sh <第1段> <第2段> <第3段> <输出>}"
SEG2="${2:?用法: concat_exact_30s.sh <第1段> <第2段> <第3段> <输出>}"
SEG3="${3:?用法: concat_exact_30s.sh <第1段> <第2段> <第3段> <输出>}"
OUT="${4:?用法: concat_exact_30s.sh <第1段> <第2段> <第3段> <输出>}"

LIST="$(mktemp -t concat_list.XXXXXX.txt)"
trap 'rm -f "$LIST"' EXIT

# concat demuxer 需要绝对路径的文件清单。
for f in "$SEG1" "$SEG2" "$SEG3"; do
  printf "file '%s'\n" "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" >> "$LIST"
done

ffmpeg -v error -f concat -safe 0 -i "$LIST" \
  -c:v libx264 -pix_fmt yuv420p -r 24 -frames:v 720 \
  -af "atrim=0:30,asetpts=N/SR/TB" -c:a aac \
  -video_track_timescale 24000 \
  "$OUT" -y

echo "成片已生成 -> $OUT"
echo "请再用 verify_frames.sh 实测：应为 1280x720 / 24fps / 720 帧 / 30.000s。"
