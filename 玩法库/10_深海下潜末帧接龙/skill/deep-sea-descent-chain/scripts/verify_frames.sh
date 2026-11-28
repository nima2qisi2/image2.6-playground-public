#!/usr/bin/env bash
# verify_frames.sh —— 深海下潜成片技术校验 + 接点抽帧 + 构图验收门抽帧。
#
# 三种模式：
#   final  （默认）成片校验：ffprobe 实测规格 + 音轨音量 + 五个接点前后帧 + 每段中点帧。
#   gate   单段构图门：抽一段视频的 0/2.5/5/7.5/9.9s 五帧，人工查机舱版舷窗是否五帧全在
#          （艇外版查主体形状/数量是否增生）。任一帧不合格，该段先重滚再进拼接。
#   ui     UI 读数核对：抽成片每段中点帧（5/15/25/35/45/55s），人工核对面板读数
#          与该段深度区间中点是否一致。
#
# 用法：
#   ./verify_frames.sh final <成片.mp4> [输出目录]
#   ./verify_frames.sh gate  <单段.mp4> [输出目录]
#   ./verify_frames.sh ui    <成片.mp4> [输出目录]
set -euo pipefail

MODE="${1:?用法: verify_frames.sh <final|gate|ui> <视频.mp4> [输出目录]}"
IN="${2:?用法: verify_frames.sh <final|gate|ui> <视频.mp4> [输出目录]}"
OUTDIR="${3:-frames/verify}"
mkdir -p "$OUTDIR"

extract() {
  for t in "$@"; do
    ffmpeg -v error -ss "$t" -i "$IN" -frames:v 1 "$OUTDIR/f_${t}.png"
    echo "  $OUTDIR/f_${t}.png"
  done
}

case "$MODE" in
  final)
    echo "== ffprobe 实测（目标：1280x720 / 24fps / 1440 帧 / 60.000s / AAC）=="
    ffprobe -v error -count_frames \
      -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames \
      -show_entries format=duration \
      -of default=noprint_wrappers=1 "$IN"
    echo "== 音轨音量实测（有数值即有声；实测有声 ≠ 试听过）=="
    ffmpeg -i "$IN" -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume" || true
    echo "== 抽帧（接点前后 + 每段中点）=="
    extract 5 9.9 10.1 15 19.9 20.1 25 29.9 30.1 35 39.9 40.1 45 49.9 50.1 55 59.9
    echo "人工检查要点："
    echo "  - 五组接点帧（9.9/10.1 … 49.9/50.1）构图应连续，无跳帧感；"
    echo "  - 中点帧里主体（潜艇/舷窗/生物）不得增生、不得变形。"
    ;;
  gate)
    echo "== 构图门抽帧（0/2.5/5/7.5/9.9s）=="
    extract 0 2.5 5 7.5 9.9
    echo "人工检查要点（机舱版）：舷窗必须五帧全在，且形状/大小/位置一致；任一帧丢窗 -> 该段重滚。"
    echo "人工检查要点（艇外版）：潜艇形状、大小、数量五帧一致，不得多出其他载具。"
    ;;
  ui)
    echo "== UI 读数核对抽帧（每段中点 5/15/25/35/45/55s）=="
    extract 5 15 25 35 45 55
    echo "人工检查要点：各帧面板 DEPTH 读数应约等于该段深度区间的中点（按分镜表核对）。"
    ;;
  *)
    echo "未知模式：$MODE（应为 final|gate|ui）" >&2; exit 1 ;;
esac
