#!/usr/bin/env python3
# make_depth_hud.py —— 逐帧渲染深海下潜深度监控 UI（带透明通道的面板帧序列）。
#
# 为什么不用视频模型画 UI：模型画的数字必错、还会乱码。深度读数必须程序渲染，
# 再由 overlay_hud.sh 叠到成片上。本脚本只依赖 Pillow。
#
# 核心规则：深度按 KEYPOINTS 分段计速（段内线性插值），不是全程匀速——
# 匀速会和画面内容对不上（10s 时画面还在阳光带，读数不能是总深度的 1/6）。
#
# 改新案例只改下面三张表：KEYPOINTS（每段起止时间→深度）、ZONES（分带名）、
# STATUS_STOPS（状态灯变色的时间点）。其余不用动。
#
# 用法：
#   python3 make_depth_hud.py [输出目录] [总帧数] [帧率]
# 默认：输出到 ./hud，1440 帧，24fps（即 60 秒）。
import os
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "hud"
TOTAL_FRAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 24
os.makedirs(OUT, exist_ok=True)

# —— 可填空区（8000m 案例的实际取值）——
# (时间秒, 深度m)：六段的起止深度，与分镜表一致
KEYPOINTS = [(0, 0), (10, 200), (20, 1000), (30, 2500), (40, 4000), (50, 6000), (60, 8000)]
TARGET = 8000
# (结束时间秒, 分带名)：该时间之前显示此名
ZONES = [(10, "SUNLIGHT ZONE"), (20, "TWILIGHT ZONE"), (30, "MIDNIGHT ZONE"),
         (40, "ABYSSAL CANYON"), (50, "UNKNOWN CONTACT"), (60, "HADAL TRENCH")]
# (结束时间秒, 状态文本, 颜色)：状态灯随深度推进变色
STATUS_STOPS = [(20, "STATUS: CALM", (110, 255, 150, 255)),
                (40, "STATUS: CAUTION", (255, 190, 90, 255)),
                (60, "STATUS: DANGER", (255, 95, 85, 255))]
GAUGE_TICKS = [0, 2000, 4000, 6000, 8000]
# —— 填空区结束 ——

W, H = 280, 450
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def fb(size): return ImageFont.truetype(FONT_B, size)
def fr(size): return ImageFont.truetype(FONT_R, size)

f_title, f_num, f_unit = fb(19), fb(54), fb(26)
f_small, f_zone, f_tick, f_status = fr(14), fb(20), fr(13), fb(17)

def depth_at(t):
    for (t0, d0), (t1, d1) in zip(KEYPOINTS, KEYPOINTS[1:]):
        if t <= t1:
            return d0 + (d1 - d0) * (t - t0) / (t1 - t0)
    return float(TARGET)

def rate_at(t):
    for (t0, d0), (t1, d1) in zip(KEYPOINTS, KEYPOINTS[1:]):
        if t < t1:
            return int(round((d1 - d0) / (t1 - t0)))
    return 0

def pick(table, t, default):
    for end, *rest in table:
        if t < end:
            return rest[0] if len(rest) == 1 else tuple(rest)
    return default

CYAN = (90, 225, 255, 255)
WHITE = (240, 250, 255, 255)
DIM = (160, 200, 215, 255)
AMBER = (255, 190, 90, 255)

for n in range(TOTAL_FRAMES):
    t = n / FPS
    d = depth_at(t)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([2, 2, W - 3, H - 3], radius=16, fill=(3, 20, 32, 178),
                         outline=(90, 225, 255, 200), width=2)
    dr.text((W // 2, 16), "DEPTH", font=f_title, fill=DIM, anchor="ma")
    num = f"{int(round(d)):,}"
    dr.text((24, 48), num, font=f_num, fill=CYAN, anchor="la")
    tw = dr.textlength(num, font=f_num)
    dr.text((24 + tw + 8, 80), "m", font=f_unit, fill=WHITE, anchor="la")
    dr.line([20, 128, W - 20, 128], fill=(90, 225, 255, 120), width=1)
    # 深度标尺
    gx, gy, gw, gh = 34, 148, 16, 200
    dr.rounded_rectangle([gx, gy, gx + gw, gy + gh], radius=7, fill=(10, 40, 55, 220),
                         outline=(120, 210, 235, 160), width=1)
    fill_h = int(gh * d / TARGET)
    if fill_h > 4:
        dr.rounded_rectangle([gx, gy, gx + gw, gy + fill_h], radius=7, fill=CYAN)
    for val in GAUGE_TICKS:
        y = gy + gh * val / TARGET
        dr.line([gx + gw + 6, y, gx + gw + 16, y], fill=DIM, width=1)
        dr.text((gx + gw + 20, y), f"{val} m", font=f_tick, fill=DIM, anchor="lm")
    dr.text((168, 205), "DESCENT RATE", font=f_small, fill=DIM, anchor="ma")
    dr.text((168, 228), f"{rate_at(t)} m/s", font=fb(19), fill=WHITE, anchor="ma")
    dr.text((168, 272), "TARGET", font=f_small, fill=DIM, anchor="ma")
    dr.text((168, 295), f"{TARGET} m", font=fb(19), fill=WHITE, anchor="ma")
    st, sc = pick(STATUS_STOPS, t, (STATUS_STOPS[-1][1], STATUS_STOPS[-1][2]))
    dr.text((W // 2, 356), st, font=f_status, fill=sc, anchor="ma")
    dr.line([20, 386, W - 20, 386], fill=(90, 225, 255, 120), width=1)
    dr.text((W // 2, 398), pick(ZONES, t, ZONES[-1][1]), font=f_zone, fill=AMBER, anchor="ma")
    img.save(f"{OUT}/hud_{n:04d}.png")
print(f"done {TOTAL_FRAMES} frames -> {OUT}")
