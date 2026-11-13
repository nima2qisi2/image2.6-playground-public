"""Local numerical and drawing helpers; no historical project imports."""
import numpy as np
import cv2
from PIL import Image,ImageDraw
W,H=720,960
CW,CH=360,480
YY,XX=np.mgrid[:CH,:CW].astype(np.float32)
WHITE=(235,236,232)
cv2.setNumThreads(4)
def triangulate(pts):
    subdiv=cv2.Subdiv2D((0,0,CW,CH))
    for p in pts:subdiv.insert(tuple(map(float,p)))
    triangles=[]
    for row in subdiv.getTriangleList():
        t=np.array(row).reshape(3,2)
        ids=[np.argmin(np.sum((pts-p)**2,axis=1)) for p in t]
        if len(set(ids))==3 and all(np.linalg.norm(pts[idx]-p)<.1 for idx,p in zip(ids,t)):
            triangles.append(ids)
    return np.array(triangles)

def mesh_maps(src,dst,tris):
    mx=XX.copy();my=YY.copy()
    for tri in tris:
        s=np.float32(src[tri]);t=np.float32(dst[tri])
        x0=max(0,int(np.floor(t[:,0].min())));x1=min(CW,int(np.ceil(t[:,0].max()))+1)
        y0=max(0,int(np.floor(t[:,1].min())));y1=min(CH,int(np.ceil(t[:,1].max()))+1)
        if x1<=x0 or y1<=y0:continue
        m=cv2.getAffineTransform(t,s)
        mask=np.zeros((y1-y0,x1-x0),np.uint8)
        cv2.fillConvexPoly(mask,np.round((t-[x0,y0])*256).astype(np.int32),1,shift=8)
        sel=mask>0; px=XX[y0:y1,x0:x1];py=YY[y0:y1,x0:x1]
        rx=(m[0,0]*px+m[0,1]*py+m[0,2]).astype(np.float32)
        ry=(m[1,0]*px+m[1,1]*py+m[1,2]).astype(np.float32)
        mx[y0:y1,x0:x1][sel]=rx[sel];my[y0:y1,x0:x1][sel]=ry[sel]
    return mx,my

def sdf(a):
    b=np.uint8(a>.22)
    return cv2.distanceTransform(b,cv2.DIST_L2,5)-cv2.distanceTransform(1-b,cv2.DIST_L2,5)

def resample_curve(points,n=96):
    points=np.float32(points)
    # Smooth the hand-registered centerline before arc-length correspondence.
    pts=[]
    for i in range(len(points)-1):
        a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
        for t in np.linspace(0,1,12,endpoint=False):
            pts.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    pts=np.array(pts+[points[-1]])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    ss=np.linspace(0,arc[-1],n)
    return np.float32(np.stack([np.interp(ss,arc,pts[:,k]) for k in range(2)],axis=1))

def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)

def slopes(a):
    d=np.diff(a,axis=0)
    out=np.zeros_like(a)
    out[0]=d[0];out[-1]=d[-1]
    same=d[:-1]*d[1:]>0
    den=d[:-1]+d[1:]
    out[1:-1]=np.divide(2*d[:-1]*d[1:],den,out=np.zeros_like(den),where=same & (np.abs(den)>1e-6))
    return out

def cubic(a,p,derivatives=None):
    p=float(np.clip(p,0,4));i=min(3,int(p));u=p-i
    m=slopes(a) if derivatives is None else derivatives
    return ((2*u**3-3*u*u+1)*a[i]+(u**3-2*u*u+u)*m[i]
           +(-2*u**3+3*u*u)*a[i+1]+(u**3-u*u)*m[i+1])

class AA:
    """Subpixel vector overlay; downsample once after all independent layers."""
    def __init__(self):
        self.image=Image.new('RGBA',(W*2,H*2));self.d=ImageDraw.Draw(self.image);self.fonts={}
    def color(self,c,a=1):
        return tuple(c[:3])+(round(255*float(np.clip(a,0,1))),)
    def line(self,coords,fill=WHITE,width=1,a=1):
        if a<=0:return
        self.d.line(tuple(round(v*2) for v in coords),fill=self.color(fill,a),width=max(1,round(width*2)))
    def ellipse(self,box,outline=WHITE,fill=None,width=1,a=1):
        if a<=0:return
        self.d.ellipse(tuple(round(v*2) for v in box),outline=self.color(outline,a) if outline else None,
                       fill=self.color(fill,a) if fill else None,width=max(1,round(width*2)))
    def rectangle(self,box,outline=WHITE,width=1,a=1):
        if a<=0:return
        self.d.rectangle(tuple(round(v*2) for v in box),outline=self.color(outline,a),width=max(1,round(width*2)))
    def text(self,xy,text,font,fill=WHITE,a=1):
        if a<=0:return
        key=(font.path,font.size)
        if key not in self.fonts:self.fonts[key]=font.font_variant(size=font.size*2)
        self.d.text(tuple(round(v*2) for v in xy),text,font=self.fonts[key],fill=self.color(fill,a))
    def finish(self,out):
        return Image.alpha_composite(out.convert('RGBA'),self.image.resize((W,H),Image.Resampling.LANCZOS)).convert('RGB')

def subpixel_bounds(alpha):
    def limits(profile):
        ids=np.where(profile>.5)[0]
        lo,hi=ids[0],ids[-1]
        if lo>0:lo=lo-1+(.5-profile[lo-1])/max(profile[lo]-profile[lo-1],1e-5)
        if hi<len(profile)-1:hi=hi+(profile[hi]-.5)/max(profile[hi]-profile[hi+1],1e-5)
        return float(lo),float(hi)
    xl,xr=limits(alpha.max(axis=0));yt,yb=limits(alpha.max(axis=1))
    return xl,yt,xr,yb
