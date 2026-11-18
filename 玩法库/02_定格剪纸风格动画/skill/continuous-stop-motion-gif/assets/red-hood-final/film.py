"""Render the 22-second paper puppet film from its local source assets."""
import argparse
import math
from pathlib import Path
import subprocess
import wave

import cv2 as cv
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import base_story as stage
import render_extended as puppets


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT, FPS, SECONDS = 1600, 900, 24, 22
Q = stage.Q
SHOTS = [
    (0.00, '01 Sneak'), (2.75, '02 Disguise'), (4.25, '03 Approach'),
    (5.50, '04 Knock'), (7.375, '05 Peek'), (9.00, '06 Door'),
    (11.625, '07 Shadow'), (13.625, '08 Reveal'),
    (16.375, '09 Reaction'), (18.25, '10 Reverse angle'), (22.00, 'End'),
]
KNOCKS = (5.92, 6.42, 6.63)
STEPS = (.55, .87, 1.19, 1.51, 1.8, 2.1, 2.40, 4.47, 4.75, 5.07, 5.30)


def plate(name):
    return Image.open(ROOT/'资产'/f'{name}.png').convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


GLASSES = plate('眼镜特写')
PEEK = plate('屋内偷看')
REVERSE = plate('巨兽反打')
DOOR_RECT = (978, 354, 1269, 768)
DOOR = np.asarray(stage.door.crop(tuple(Q*x for x in DOOR_RECT)))
FG_DOOR = np.float32([[0,0],[DOOR.shape[1]-1,0],[DOOR.shape[1]-1,DOOR.shape[0]-1],[0,DOOR.shape[0]-1]])
MASK_GIRL = stage.girl.getchannel('A')
MASK_MONSTER = stage.monster.getchannel('A')
GRID_Y, GRID_X = np.mgrid[:HEIGHT,:WIDTH].astype(np.float32)
DOOR_LIGHT = Image.new('RGBA',stage.SIZE,(225,133,57,0))
DOOR_LIGHT.putalpha(stage.dm.point(lambda a:round(a*.58)))


def ease(t, start, end):
    return stage.ramp(t, start, end)


def mix(a, b, r):
    return a + (b-a)*r


def plate_camera(img, scale=1., cx=800, cy=450, angle=0.):
    matrix = cv.getRotationMatrix2D((cx,cy), angle, scale)
    matrix[0,2] += 800 - cx
    matrix[1,2] += 450 - cy
    return Image.fromarray(cv.warpAffine(np.asarray(img), matrix, (WIDTH,HEIGHT), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REFLECT_101))


def light_mask(size, center, radius):
    w,h = size
    y,x = np.ogrid[:h,:w]
    return np.exp(-((x-center[0])/radius[0])**2-((y-center[1])/radius[1])**2).astype(np.float32)


def glint(img, xy, amount):
    rgb = np.asarray(img,dtype=np.float32)
    highlight = light_mask(img.size, xy, (20,13)) + .27*light_mask(img.size, xy, (64,28))
    rgb += highlight[:,:,None] * np.array([89,67,27]) * amount
    return Image.fromarray(np.uint8(np.clip(rgb,0,255)))


def pose_warp(img, regions):
    """Move selected paper surface regions while the surrounding camera plate stays still."""
    x,y = GRID_X.copy(),GRID_Y.copy()
    for xy, radius, dx, dy in regions:
        influence = light_mask(img.size, xy, radius)
        x -= influence * dx
        y -= influence * dy
    return Image.fromarray(cv.remap(np.asarray(img),x,y,cv.INTER_CUBIC,borderMode=cv.BORDER_REFLECT_101))


def sneak(t):
    # Distance carries through the pause and resumes on the next footfall.
    distance = 185*ease(t,.05,1.18)+220*ease(t,1.34,2.61)
    x = 62+distance
    out = stage.bg.copy()
    actor = puppets.bare_actor(distance)
    ground = 470-3*abs(math.sin(distance/100*math.tau))
    puppets.add_floor(out,x,801,190)
    stage.shadow_place(out,actor,(x,ground),.16)
    stage.shadow_place(out,puppets.tree,(442,-105),.17)
    box = stage.lerp((0,297,965,839.8125),(78,274,1043,816.8125),ease(t,0,2.7))
    return stage.crop_camera(out,box)


def disguise(t):
    settle = ease(t,2.83,3.48)
    img = pose_warp(GLASSES,[((1172,430),(174,102),-8*settle,6*settle),((1054,442),(106,62),-4*settle,4*settle)])
    img = glint(img,(1131,392),math.exp(-((t-3.38)/.09)**2))
    return plate_camera(img,1.10+.045*settle,830,464)


def approach(t):
    moment = mix(4.64,5.86,ease(t,4.20,5.50))
    return puppets.intro_frame(moment)


def knock(t):
    # The same event clock drives the pose, the contact cut and the foley.
    k = max(math.exp(-((t-event)/.085)**2) for event in KNOCKS)
    out = stage.bg.copy()
    actor = stage.cores[0].copy()
    arm = stage.arms[0].rotate(-15*k,Image.Resampling.BICUBIC,center=stage.wpivot)
    actor.alpha_composite(arm)
    puppets.add_floor(out,771,801)
    stage.shadow_place(out,actor,(771+8*k,460),.22)
    if t<6.13:
        box = stage.lerp((480,285,1530,875.625),(566,332,1466,838.25),ease(t,5.5,6.13))
    else:
        box = stage.lerp((822,428,1302,698),(856,434,1336,704),ease(t,6.13,7.375))
    return stage.crop_camera(out,box)


def peek(t):
    rise = ease(t,7.375,7.78)*(1-ease(t,8.64,9.0))
    look = ease(t,7.93,8.20)
    # Keep the sill locked while the paper hood lifts and the gaze shifts left.
    img = pose_warp(PEEK,[((1090,473),(433,260),-12*rise,-25*rise),
                          ((973,667),(70,43),-7*look,-3*rise),
                          ((1213,700),(78,48),-6*look,-3*rise)])
    return plate_camera(img,1.035+.04*ease(t,7.375,9.0),815,456)


def glow_on_floor(t, amount):
    layer = Image.new('RGBA',stage.SIZE)
    mask = stage.maskpoly([(1030,761),(1240,761),(1385,890),(868,878)])
    mask = mask.filter(ImageFilter.GaussianBlur(14*Q))
    layer.paste((255,159,62,0),(0,0,*stage.SIZE))
    layer.putalpha(mask.point(lambda x:round(x*amount)))
    return layer


def hinged_panel(t):
    angle = math.radians(76*ease(t,9.13,10.64))
    # The right hinge stays fixed; the leading edge recedes toward the camera's vanishing direction.
    left = (DOOR.shape[1]-1)*(1-math.cos(angle))
    recess = 22*Q*math.sin(angle)
    right, bottom = DOOR.shape[1]-1, DOOR.shape[0]-1
    quad = np.float32([[left,recess],[right,0],[right,bottom],[left,bottom-recess*.82]])
    matrix = cv.getPerspectiveTransform(FG_DOOR,quad)
    return Image.fromarray(cv.warpPerspective(DOOR,matrix,(DOOR.shape[1],DOOR.shape[0]),flags=cv.INTER_CUBIC))


def cast_on_wall(t):
    growth = ease(t,11.52,13.38)
    h = round(mix(123,343,growth)*Q)
    w = round(mix(88,238,growth)*Q)
    mask = Image.new('L',stage.SIZE)
    girl_mask = MASK_GIRL.resize((w,h),Image.Resampling.BILINEAR)
    monster_mask = MASK_MONSTER.resize((w,h),Image.Resampling.BILINEAR)
    shape = Image.blend(girl_mask,monster_mask,ease(t,12.2,12.48))
    shadow_x = round(mix(1078,994,growth)*Q)
    mask.paste(shape,(shadow_x,756*Q-h))
    mask = ImageChops.multiply(mask.filter(ImageFilter.GaussianBlur(mix(2,4,growth)*Q)),stage.dm)
    opacity = (.48+.40*growth)*ease(t,11.46,11.83)*(1-ease(t,13.60,14.45))
    shadow = Image.new('RGBA',stage.SIZE,(20,15,29,0))
    shadow.putalpha(mask.point(lambda x:round(x*opacity)))
    return shadow


def doorway(t):
    out = stage.bg.copy()
    out.alpha_composite(stage.interior)
    strength = ease(t,9.24,10.7)*(1-.49*ease(t,12.15,13.43))
    out.alpha_composite(glow_on_floor(t,.19*strength))
    if 11.18<t<14.65:
        lamp = DOOR_LIGHT.copy()
        lamp_amount = ease(t,11.18,11.71)*(1-ease(t,13.61,14.65))
        lamp.putalpha(lamp.getchannel('A').point(lambda a:round(a*lamp_amount)))
        out.alpha_composite(lamp)
    out.alpha_composite(cast_on_wall(t))
    # The projection anticipates Red's physical transformation by almost a second.
    transform_t = 5.45+1.0*ease(t,9.43,11.16)
    if 13.625<=t:
        transform_t = mix(6.42,9.12,ease(t,13.625,15.82))
    red,pos = stage.girl_layer(transform_t)
    if t<10.95:
        behind = Image.new('RGBA',stage.SIZE)
        stage.place(behind,red,pos)
        behind.putalpha(ImageChops.multiply(behind.getchannel('A'),stage.dm))
        out.alpha_composite(behind)
    stage.place(out,hinged_panel(t),DOOR_RECT[:2])
    fear_time = mix(7.23,9.15,ease(t,12.65,16.2)) if t>=12.65 else 2.65
    wolf,wolf_pos = stage.wolf_layer(fear_time)
    puppets.add_floor(out,wolf_pos[0],801)
    stage.shadow_place(out,wolf,wolf_pos,.20)
    if t>=10.95:
        stage.shadow_place(out,red,pos,.24)
    return out


def threshold(t):
    out = doorway(t)
    if t<11.625:
        box = stage.lerp((775,410,1415,770),(591,293,1571,844.25),ease(t,9.0,11.36))
    elif t<13.625:
        box = stage.lerp((759,355,1459,748.75),(726,325,1466,741.25),ease(t,11.625,13.625))
    elif t<16.375:
        box = stage.lerp((415,206,1585,864.125),(85,45,1600,897.1875),ease(t,13.625,15.87))
    else:
        box = stage.lerp((615,393,1175,708),(630,405,1158,702),ease(t,16.375,18.25))
    return stage.crop_camera(out,box)


def finale(t):
    lean = ease(t,18.32,19.52)
    breath = math.sin((t-19.6)*2.8)*ease(t,19.52,20.0)
    # Keep the giant's lower body anchored and let the two optical planes move differently.
    img = pose_warp(REVERSE,[((870,270),(435,270),-16*lean,23*lean+3*breath),
                             ((235,600),(225,360),-27*lean,7*lean),
                             ((1270,585),(253,201),2*breath,3*breath)])
    return plate_camera(img,1.028+.055*ease(t,18.25,21.58),811,445,-.55*lean)


MOTIONS = [sneak,disguise,approach,knock,peek,threshold,threshold,threshold,threshold,finale]


def finish(img, index, t):
    # Grade the original stage toward the new inserts while preserving its red and gold paper.
    arr = np.asarray(img,dtype=np.float32)/255
    vignette = 1-.18*np.minimum(1,((GRID_X-800)/990)**2+((GRID_Y-445)/610)**2)
    shadow = (1-arr.max(2))**2
    if index in (0,2,3,5,6,7,8):
        arr *= np.array([.96,.94,1.005],dtype=np.float32)
        arr[:,:,2] += shadow*.034
        arr[:,:,0] -= shadow*.018
    arr = np.clip((arr-.025)*1.042,0,1)*vignette[:,:,None]
    if 11.6<t<14.0:
        arr *= 1-.085*math.sin(math.pi*ease(t,11.6,14.0))
    if t>=21.48:
        arr *= 1-ease(t,21.48,21.95)
    return Image.fromarray(np.uint8(np.clip(arr*255,0,255)))


def frame(i):
    t = i/FPS
    idx = next(j for j in range(len(MOTIONS)) if t<SHOTS[j+1][0])
    # Pose updates at 12 Hz: a consistent two-frame exposure in a 24 fps master.
    pose = (i//2)*2/FPS
    return finish(MOTIONS[idx](max(SHOTS[idx][0],pose)),idx,max(SHOTS[idx][0],pose))


def soundtrack(path):
    sr = 48000
    rng = np.random.default_rng(62)
    t = np.arange(sr*SECONDS)/sr
    wind = np.interp(t,np.arange(0,SECONDS+.2,.2),rng.normal(0,1,111))
    breeze = np.sin(2*np.pi*t*41.2)*.006 + np.sin(2*np.pi*t*61.83+.5*np.sin(t))* .004
    ambience=(breeze+wind*.0024)*(.30+.70*(1-np.exp(-((t-9.7)/2.45)**2)))
    stereo = np.column_stack((ambience,ambience*.88))

    def cue(start,duration,frequency,volume,pan,noise=.15,decay=7.,bend=0.,rise=.015):
        u = np.arange(round(duration*sr))/sr
        at = round(start*sr)
        f = frequency*u+.5*bend*u*u
        envelope = np.minimum(1,u/rise)*np.minimum(1,(duration-u)/.025)*np.exp(-decay*u)
        grit = rng.standard_normal(len(u))
        grit = np.convolve(grit,np.ones(8)/8,mode='same')
        signal = (np.sin(2*np.pi*f)+.23*np.sin(2*np.pi*2.51*f)+noise*grit)*envelope*volume
        stereo[at:at+len(u),0] += signal*math.sqrt((1-pan)/2)
        stereo[at:at+len(u),1] += signal*math.sqrt((1+pan)/2)

    for j,start in enumerate(STEPS):
        cue(start,.16,75+j%3*11,.087,-.5+j*.065,2.8,26.,-130.,.004)
    cue(2.91,.24,164,.04,-.3,7,10.,-170.)
    cue(3.38,.33,880,.092,.15,.24,14.,-450.,.004)
    for j,start in enumerate(KNOCKS):
        cue(start,.32,149-j*8,.29 if j==0 else .22,.28,1.25,23.,-80.,.003)
        cue(start+.075,.24,223,.037,-.04,.7,26.,-90.)
    cue(9.17,.21,270,.11,.24,.6,19.,-220.,.005)
    cue(9.36,1.26,112,.075,.3,1.9,1.45,110.,.10)
    cue(10.96,.22,79,.077,.36,1.7,18.,-70.)
    cue(11.78,1.34,68,.07,-.05,.16,.85,-5.,.32)
    cue(12.62,2.29,49,.12,0,.86,.43,-8.,.33)
    cue(13.65,.86,105,.09,.25,6.7,3.3,-47.,.03)
    cue(15.18,.85,65,.28,.16,1.3,6.3,-46.,.005)
    cue(16.48,.34,471,.096,-.5,.05,12.,-270.,.006)
    cue(17.23,.22,95,.094,-.45,3.0,21.,-62.)
    cue(18.32,1.12,57,.12,.30,1.6,2.8,-11.,.02)
    for start,note in [(18.61,220),(19.12,261.63),(19.70,329.63),(20.23,246.94)]:
        cue(start,1.22,note,.042,.22,.02,3.8,0.,.007)
    stereo *= np.clip((22-t)/.52,0.,1.)[:,None] * np.clip(t/.18,0.,1.)[:,None]
    stereo = np.tanh(stereo*1.28)*.88
    with wave.open(str(path),'wb') as wav:
        wav.setparams((2,2,sr,len(t),'NONE','not compressed'))
        wav.writeframes(np.int16(stereo*32767).tobytes())


def contact_sheet(path):
    points = [1.38,3.45,4.95,6.42,8.18,10.32,12.72,14.42,15.88,17.25,19.58,21.02]
    grid = Image.new('RGB',(1440,1152),'#120f13')
    draw = ImageDraw.Draw(grid)
    for j,t in enumerate(points):
        x,y = j%3*480,j//3*288
        grid.paste(frame(round(t*FPS)).resize((464,261),Image.Resampling.LANCZOS),(x+8,y+6))
        draw.text((x+10,y+273),f'{t:05.2f}s',fill='#f7dfc6')
    grid.save(path,quality=93)


def render(ffmpeg):
    wav = ROOT/'拟音与环境.wav'
    soundtrack(wav)
    out = ROOT/'小红帽_门后的影子_6.2重制.mp4'
    args = [ffmpeg,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{WIDTH}x{HEIGHT}',
            '-r',str(FPS),'-i','-','-i',str(wav),'-c:v','libx264','-preset','fast','-crf','17',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(out)]
    with subprocess.Popen(args,stdin=subprocess.PIPE) as encoder:
        last_key, pixels = None,None
        cuts = {round(t*FPS) for t,_ in SHOTS}
        for i in range(FPS*SECONDS):
            key = (i//2,i if i in cuts or i-1 in cuts and i%2==0 else 0)
            if key!=last_key:
                pixels = frame(i).tobytes()
                last_key = key
            encoder.stdin.write(pixels)
            if i%48==0:
                print(f'{i/FPS:04.1f}s rendered',flush=True)
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('FFmpeg could not encode the video')
    print(out,flush=True)


if __name__=='__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--ffmpeg',help='Path to FFmpeg. Without it, only render the story contact sheet.')
    options = args.parse_args()
    contact_sheet(ROOT/'镜头检查.jpg')
    if options.ffmpeg:
        render(options.ffmpeg)
