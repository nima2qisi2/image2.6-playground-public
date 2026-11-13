"""Fixed 3:4 seahorse archive layout, extracted from the v21 baseline."""
from pathlib import Path
import sys,json,math
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
import motion_core as v8
m=v8
BASELINE=Path(__file__).resolve().parents[1]/'assets'/'seahorse-baseline'
PROJECT=json.loads((BASELINE/'project.json').read_text(encoding='utf8'))
W,H,FPS,N=720,960,25,300
WHITE=(230,233,222);GRAY=(141,157,150);ORANGE=(248,126,38)
K=W/1086
NAMES=PROJECT['names'];ENG=PROJECT['english']
FEATURES=PROJECT['features'];TAILS=PROJECT['tail_paths'];FINS=PROJECT['fins']
UI_BACKGROUND=None
GRID_X=np.arange(154,683,88,dtype=int);GRID_Y=np.arange(94,743,108,dtype=int)
GRID_COLOR=(12,23,23);SEPARATOR_Y=774;BASELINE_Y=920
FONT_DIR=Path('C:/Windows/Fonts')

def reveal(t,delay,duration):return float(v8.smooth((t-delay)/duration))

def trace(v,points,amount,fill=WHITE,opacity=1):
    if amount<=0:return
    if amount>=1:
        v.line(tuple(z for p in points for z in p),fill=fill,a=opacity);return
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:])]
    remaining=sum(lengths)*amount
    for a,b,length in zip(points,points[1:],lengths):
        if remaining<=0:break
        q=min(1,remaining/max(length,1e-6));end=(a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q)
        v.line((*a,*end),fill=fill,a=opacity);remaining-=length

def intro_region(canvas,box,amount,wipe=False):
    x0,y0,x1,y1=box
    if amount>=1:return
    tile=canvas[y0:y1,x0:x1]
    if wipe:
        x=np.arange(x1-x0,dtype=np.float32)
        mask=np.clip((amount*(x1-x0+12)-x)/12,0,1)[None,:,None]
    else:mask=amount
    background=UI_BACKGROUND[y0:y1,x0:x1].astype(np.float32)
    canvas[y0:y1,x0:x1]=background+(tile-background)*mask


def font(n,bold=False,cn=False):
    return ImageFont.truetype(str(FONT_DIR/('msyhl.ttc' if cn else 'arialbd.ttf' if bold else 'arial.ttf')),n)

class Layout:
    def __init__(self):
        from faithful_motion import FaithfulMorph
        self.m=FaithfulMorph(sys.modules[__name__])
        reg=PROJECT['registration']
        self.sizes=np.float32(reg['heights'])*K;self.sm=v8.slopes(self.sizes)
        self.centers=np.float32(reg['centers'])*K;self.cm=v8.slopes(self.centers)
        base=np.array(Image.open(BASELINE/'ui-template.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS))
        # Preserve raster header, narrow chronology, and main title exactly.
        base[61:775,138:]=[4,13,13]
        # Neutralize the old orange highlight before recoloring the active row.
        self.rows=[]
        for i,(top,bottom) in enumerate([(918,1000),(760,842),(604,687),(437,529),(270,358)]):
            y0=round(top*K);y1=round(bottom*K);x0=round(53*K);x1=round(198*K)
            arr=base[y0:y1,x0:x1].astype(np.float32)
            fg=np.clip((arr.max(axis=2)-24)/210,0,1)
            selected=arr.max(axis=2)>48
            original=arr.copy()
            # One canonical outline and text per row, no five drifting bitmap UIs.
            neutral=original.copy();neutral[selected]=(np.array(GRAY)*fg[selected,None]+np.array([4,13,13])*(1-fg[selected,None]))
            base[y0:y1,x0:x1]=np.uint8(neutral)
            self.rows.append((x0,y0,fg,selected,original))
        # Erase only changing stage readouts, using local flat footer background.
        erase=np.zeros((H,W),np.uint8)
        erase[793:910,540:682]=np.uint8(base[793:910,540:682].max(axis=2)>48)*255
        erase=cv2.dilate(erase,np.ones((3,3),np.uint8))
        base=cv2.inpaint(base,erase,4,cv2.INPAINT_TELEA)
        # Remove the old raster badge's inpainting shadows from its empty
        # background before drawing the single live stage readout.
        left=base[790:914,536].astype(np.float32)
        right=base[790:914,688].astype(np.float32)
        for x in range(540,684):
            u=(x-536)/152
            base[790:914,x]=np.uint8(left*(1-u)+right*u)
        # Replace the raster-generated sloping rules with single-source integer
        # pixel geometry. Interpolate the background across the old rule bands.
        for y0,y1,x0,x1 in [(770,780,0,W),(916,925,24,696)]:
            above=base[y0-1,x0:x1].astype(np.float32)
            below=base[y1,x0:x1].astype(np.float32)
            for y in range(y0,y1):
                u=(y-y0+1)/(y1-y0+1)
                base[y,x0:x1]=np.uint8(above*(1-u)+below*u)
        # Clean the old divider's antialiasing and its footer overhang.
        for x in range(134,139):
            u=(x-133)/6
            base[60:780,x]=np.uint8(base[60:780,133].astype(np.float32)*(1-u)+base[60:780,139].astype(np.float32)*u)
        self.base=Image.fromarray(base)
        d=ImageDraw.Draw(self.base)
        d.line((136,60,136,SEPARATOR_Y-1),fill=(31,47,44),width=1)
        d.rectangle((0,SEPARATOR_Y,W-1,SEPARATOR_Y+1),fill=ORANGE)
        d.line((36,BASELINE_Y,684,BASELINE_Y),fill=(156,170,157),width=1)
        # 36 cells: seven integer verticals and horizontals. These are painted
        # into the background before the specimen alpha and every data overlay.
        for x in GRID_X:d.line((int(x),int(GRID_Y[0]),int(x),int(GRID_Y[-1])),fill=GRID_COLOR,width=1)
        for y in GRID_Y:d.line((int(GRID_X[0]),int(y),int(GRID_X[-1]),int(y)),fill=GRID_COLOR,width=1)
        # Remove static type/line ink once to reveal its actual local background,
        # instead of exposing dark glyph edges or flat rectangular masks.
        global UI_BACKGROUND
        raster=np.array(self.base)
        removal=np.zeros((H,W),np.uint8)
        boxes=[(0,0,W,61),(20,77,130,127),(27,165,50,718),
               (22,746,132,770),(20,786,530,811),(20,816,360,877),
               (20,881,360,912),(20,916,690,951)]
        boxes.extend((x,y,x+mask.shape[1],y+mask.shape[0]) for x,y,mask,_,_ in self.rows)
        for x0,y0,x1,y1 in boxes:
            removal[y0:y1,x0:x1]=np.uint8(raster[y0:y1,x0:x1].max(axis=2)>25)*255
        removal=cv2.dilate(removal,np.ones((3,3),np.uint8))
        UI_BACKGROUND=cv2.inpaint(raster,removal,4,cv2.INPAINT_TELEA)
        UI_BACKGROUND=cv2.GaussianBlur(UI_BACKGROUND,(0,0),8)
        self.checks=[]

    def phase(self,t):
        q=np.clip((t-.38)/9.55,0,1)
        # Mostly uniform middle velocity, continuous soft start and end.
        s=.72*q+.28*(q*q*(3-2*q))
        p=float(4*s)
        opacity=float(v8.smooth(t/.32))*(1-float(v8.smooth((t-11.1)/.45)))
        if t>=11.55:p=0.
        return p,opacity

    def render(self,t,record=False):
        p,opacity=self.phase(t)
        rgb,a,pts=self.m.frame(p)
        xl,yt,xr,yb=v8.subpixel_bounds(a)
        height=float(v8.cubic(self.sizes,p,self.sm))
        cx,cy=v8.cubic(self.centers,p,self.cm)
        scale=1.;ox=0.;oy=0.
        image=rgb;alpha=a
        canvas=np.array(self.base,np.float32)
        intro_region(canvas,(0,0,W,61),.07+.93*reveal(t,0,.40))
        intro_region(canvas,(20,77,130,127),reveal(t,.18,.36))
        intro_region(canvas,(27,165,50,718),reveal(t,.28,.72),wipe=False)
        intro_region(canvas,(22,746,132,770),reveal(t,.90,.35))
        intro_region(canvas,(20,786,530,811),reveal(t,.31,.34))
        intro_region(canvas,(20,816,360,877),reveal(t,.34,.52),wipe=True)
        intro_region(canvas,(20,881,360,912),reveal(t,.62,.38),wipe=True)
        intro_region(canvas,(20,916,690,951),reveal(t,.86,.30))
        for i,(x0,y0,mask,selected,original) in enumerate(self.rows):
            amount=max(0,1-abs(p-i))*opacity
            col=np.array(GRAY)*(1-amount)+np.array(ORANGE)*amount
            h,w=mask.shape
            tile=original.copy()
            tile[selected]=np.array([4,13,13])*(1-mask[selected,None])+col*mask[selected,None]
            entry=reveal(t,.28+i*.10,.32)
            backdrop=UI_BACKGROUND[y0:y0+h,x0:x0+w].astype(np.float32)
            tile=backdrop+(tile-backdrop)*entry
            canvas[y0:y0+h,x0:x0+w]=tile
        canvas=canvas*(1-alpha[...,None]*opacity)+image*opacity
        out=Image.fromarray(np.uint8(np.clip(canvas,0,255)))
        xy=pts;v=v8.AA()
        # Compact progress readout requested in the upper-left specimen field.
        progress_alpha=reveal(t,.10,.18)*(1-reveal(t,11.10,.40))
        percent=float(np.clip(p*25,0,100))
        progress_text='100.0%' if percent>=99.9995 else f'{percent:.3f}%'
        v.text((158,84),'成长 / GROWTH',font=font(9,cn=True),fill=GRAY,a=progress_alpha)
        v.text((158,99),progress_text,font=font(18),fill=WHITE,a=progress_alpha)
        groups=[[(2,-20),(7,-5),(11,10),(13,10)],[(0,-35),(4,-10),(6,15),(10,20),(14,35)]]
        leftlane=float(np.clip(ox+xl*scale-124,158,340))
        for side,group in enumerate(groups):
            prev=None
            for j,(fid,dy) in enumerate(group):
                px,py=xy[fid]
                by=85+np.logaddexp(0,(py+dy-85)/5)*5
                if prev is not None:by=prev+38+np.logaddexp(0,(by-prev-38)/4)*4
                prev=by
                bx=leftlane if side==0 else float(np.clip(px+54,475,605))
                # Tail labels stay beyond the moving full specimen boundary,
                # including the strongly curled mature tail.
                if side==1 and fid==14:
                    bx=max(bx,float(np.clip(ox+xr*scale+14,475,605)))
                label=f'X {px/W:.3f} / Y {py/H:.3f}'
                f=font(9);tw=ImageDraw.Draw(out).textlength(label,font=f)
                end=bx+tw+3 if side==0 else bx-3
                elbow=end+12 if side==0 else end-12
                delay=.48+j*.11+(.04 if side==0 else 0)
                node=reveal(t,delay,.14);line=reveal(t,delay+.04,.30)
                frame=reveal(t,delay+.17,.27);digits=reveal(t,delay+.27,.30)
                trace(v,[(px,py),(elbow,by+17),(end,by+17)],line,fill=(186,198,185),opacity=opacity)
                radius=2.3*(.65+.35*node)
                v.ellipse((px-radius,py-radius,px+radius,py+radius),outline=WHITE,a=opacity*node)
                pid=f'P{fid+1:02d}'
                v.text((bx,by),pid[:math.ceil(len(pid)*frame)],font=font(9),a=opacity*frame)
                if frame>=1:v.rectangle((bx-3,by+11,bx+tw+3,by+25),outline=(167,183,170),a=opacity)
                else:trace(v,[(bx-3,by+11),(bx+tw+3,by+11),(bx+tw+3,by+25),(bx-3,by+25),(bx-3,by+11)],frame,fill=(167,183,170),opacity=opacity)
                v.text((bx,by+12),label[:math.ceil(len(label)*digits)],font=f,a=opacity*digits)
        # Anatomy topology is independently rendered, with no opaque labels.
        for aa,bb in [(0,4),(4,6),(6,9),(9,10),(5,7),(7,11),(11,12),(12,13),(13,14)]:
            amount=reveal(t,.65,.55)
            trace(v,[tuple(xy[aa]),tuple(xy[bb])],amount,fill=(113,132,115),opacity=opacity*.8)
        for fid in [0,2,4,7,9,10,11,12,13,14]:
            px,py=xy[fid];v.ellipse((px-1.8,py-1.8,px+1.8,py+1.8),outline=WHITE,a=opacity*reveal(t,.58,.35))
        # Angle readouts are derived from tracked projected vectors.
        for aidx,bidx,dx,dy in [(2,1,-45,32),(4,10,110,22)]:
            aa,bb=xy[aidx],xy[bidx];vec=bb-aa
            angle=abs(math.degrees(math.atan2(vec[1],vec[0])))
            tx=float(np.clip(aa[0]+dx,160,630));ty=float(np.clip(aa[1]+dy,85,745))
            angle_entry=reveal(t,.86,.40)
            label=f'θ {angle:.1f}°'
            v.text((tx,ty),label[:math.ceil(len(label)*angle_entry)],font=font(10),a=opacity*angle_entry)
            trace(v,[(tx,ty+15),(tx+34,ty+15)],angle_entry,fill=GRAY,opacity=opacity)
        # Fixed typography: only active numeral/name changes, never photo-warped.
        stage=min(4,max(0,int(p+.5)))
        i=min(3,int(p));fraction=p-i
        # A discrete stage is a single stable readout. Continuous progress and
        # coordinates animate separately; numerals never overlap or go blank.
        cards=[(stage,1)]
        color=np.zeros((240,290,3),np.float32);coverage=np.zeros((240,290),np.float32)
        for idx,weight in cards:
            tile=Image.new('RGBA',(290,240));td=ImageDraw.Draw(tile)
            td.text((50,10),f'STAGE {idx+1:02d} OF 05',font=font(18),fill=WHITE+(255,))
            td.text((16,52),f'{idx+1:02d}',font=font(148,True),fill=ORANGE+(255,))
            en=ENG[idx];f=font(22);tw=td.textlength(en,font=f)
            td.text((106-tw/2,208),en,font=f,fill=WHITE+(255,))
            arr=np.array(tile,np.float32);a=arr[...,3]/255*weight
            color+=arr[...,:3]*a[...,None];coverage+=a
        straight=color/np.maximum(coverage[...,None],1e-5)
        card=Image.fromarray(np.uint8(np.clip(np.dstack([straight,coverage*255*opacity*reveal(t,.46,.40)]),0,255)))
        v.image.alpha_composite(card,(1080,1580))
        out=v.finish(out)
        # Restore the small upright specimen caption without a bitmap patch.
        text=Image.new('RGBA',(220,18));td=ImageDraw.Draw(text)
        td.text((0,0),'HIPPOCAMPUS  ·  SPECIMEN PROFILE',font=font(8),fill=WHITE+(round(170*reveal(t,.90,.35)),))
        text=text.rotate(90,expand=True)
        out.paste(text,(689,276),text)
        if record:self.checks.append({'t':t,'p':p,'height_px':height,'opacity':opacity,'growth_percent':percent,'growth_text':progress_text})
        return out
