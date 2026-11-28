#!/usr/bin/env bash
# concat_exact_60s.sh —— 把 6 段各 10 秒的视频硬拼成精确 60.000s / 1440 帧的成片。
#
# 做法：concat demuxer 流复制拼接（不重编码，画质无损、速度快），
# 用 -frames:v 1440 锁死总帧数。前提：六段同为 1280×720、24fps、同编码（h264+aac）。
# 若六段规格不一致，先各自转码统一，或改走重编码拼接：
#   -c:v libx264 -pix_fmt yuv420p -r 24 -frames:v 1440 -af "atrim=0:60" -c:a aac
#
# 用法：
#   ./concat_exact_60s.sh <输出成片.mp4> <第1段.mp4> <第2段.mp4> ... <第6段.mp4>
#
# 示例：
#   ./concat_exact_60s.sh final-60s.mp4 seg1.mp4 seg2.mp4 seg3.mp4 seg4.mp4 seg5.mp4 seg6.mp4
set -euo pipefail

OUT="${1:?用法: concat_exact_60s.sh <输出> <第1段> ... <第6段>}"
shift
[ "$#" -eq 6 ] || { echo "需要恰好 6 段视频，收到 $# 段" >&2; exit 1; }

LIST="$(mktemp -t concat60_list.XXXXXX.txt)"
trap 'rm -f "$LIST"' EXIT

# concat demuxer 需要绝对路径的文件清单。
for f in "$@"; do
  printf "file '%s'\n" "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" >> "$LIST"
done

ffmpeg -v error -f concat -safe 0 -i "$LIST" \
  -map 0:v:0 -map 0:a? -c copy -frames:v 1440 \
  "$OUT" -y

echo "成片已生成 -> $OUT"
echo "请再用 verify_frames.sh 实测：应为 1280x720 / 24fps / 1440 帧 / 60.000s / AAC。"
