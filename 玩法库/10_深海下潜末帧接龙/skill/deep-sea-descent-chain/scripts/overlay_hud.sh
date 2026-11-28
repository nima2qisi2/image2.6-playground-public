#!/usr/bin/env bash
# overlay_hud.sh —— 把 make_depth_hud.py 渲染的 UI 帧序列叠到成片右侧，并锁死精确 60s。
#
# 面板 280×450，叠在 1280×720 画面的 (980,135)，即右侧居中。
# 此步需要重编码视频（ultrafast 保证速度），音轨直接复制、各段环境声原样保留，
# 并用 atrim 把拼接时多出的零点几帧音频截回 60 秒。
#
# 用法：
#   ./overlay_hud.sh <无UI成片.mp4> <UI帧目录> <输出成片.mp4>
#
# 示例：
#   ./overlay_hud.sh raw-60s.mp4 hud final-60s.mp4
set -euo pipefail

IN="${1:?用法: overlay_hud.sh <无UI成片.mp4> <UI帧目录> <输出成片.mp4>}"
HUD="${2:?用法: overlay_hud.sh <无UI成片.mp4> <UI帧目录> <输出成片.mp4>}"
OUT="${3:?用法: overlay_hud.sh <无UI成片.mp4> <UI帧目录> <输出成片.mp4>}"

ffmpeg -v error -i "$IN" -framerate 24 -i "$HUD/hud_%04d.png" \
  -filter_complex "[0:v][1:v]overlay=980:135:format=auto[vout]" \
  -map "[vout]" -map 0:a \
  -af "atrim=0:60,asetpts=PTS-STARTPTS" \
  -c:v libx264 -preset ultrafast -crf 19 -pix_fmt yuv420p -r 24 -frames:v 1440 \
  -c:a aac -b:a 128k -t 60 \
  "$OUT" -y

echo "已叠加 UI -> $OUT"
echo "请再用 verify_frames.sh 实测规格，并抽帧核对 UI 读数（每段中点深度应与分镜表中点一致）。"
