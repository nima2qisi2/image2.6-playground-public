"""Transport each stage's own photograph, including its real alpha silhouette.

The tail field moves original 2D pixels. It creates neither a cylindrical
surface, a replacement texture atlas, nor a replacement fin.
"""
import json
import numpy as np
import cv2
from source_faithful import SourceMorph

def spline(points,s):
    s=np.clip(np.asarray(s,dtype=np.float32),0,len(points)-1)
    k=np.floor(s).astype(np.int32);t=(s-k)[...,None]
    a=points[np.maximum(k-1,0)];b=points[k]
    c=points[np.minimum(k+1,len(points)-1)];d=points[np.minimum(k+2,len(points)-1)]
    v1=-a+c;v2=2*a-5*b+4*c-d;v3=-a+3*b-3*c+d
    return (.5*(2*b+v1*t+v2*t*t+v3*t*t*t),
            .5*(v1+2*v2*t+3*v3*t*t),v2+3*v3*t)

def poly_resample(points,n):
    a=np.float32(points);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))]
    q=np.linspace(0,arc[-1],n)
    return np.column_stack([np.interp(q,arc,a[:,j]) for j in range(2)]).astype(np.float32)

def basis(t):
    t=t/np.maximum(np.linalg.norm(t,axis=-1,keepdims=True),1e-5)
    return t,np.stack([-t[...,1],t[...,0]],axis=-1)

class FaithfulMorph(SourceMorph):
    def __init__(self,g):
        super().__init__(g)
        self.m=g.m;self.v8=g.v8
        self.m.CW=360;self.m.CH=480
        self.m.YY,self.m.XX=np.mgrid[:480,:360].astype(np.float32)
        self.xx=self.m.XX;self.yy=self.m.YY
        self.bounds=np.float32([(0,0),(179,0),(359,0),(359,239),(359,479),(179,479),(0,479),(0,239)])
        self.curves=np.float32([g.m.resample_curve(a,128)*g.K*.5 for a in g.TAILS])
        self.widths=[];self.p=[];self.fin_keys=[]
        self.body_rgb=[];self.body_a=[];self.fin_rgb=[];self.fin_a=[]
        for i in range(5):
            curve=self.curves[i]
            mask=cv2.resize(self.alpha[i],(360,480),interpolation=cv2.INTER_AREA)
            dist=cv2.distanceTransform(np.uint8(mask>.5),cv2.DIST_L2,5)
            # Refine the transport centerline against the actual photograph's
            # medial ridge. This affects coordinates, never the source alpha.
            for _ in range(3):
                tangent=np.gradient(curve,axis=0);_,normal=basis(tangent)
                offsets=np.linspace(-4,4,33,dtype=np.float32)
                q=curve[:,None,:]+normal[:,None,:]*offsets[None,:,None]
                score=cv2.remap(dist,q[:,:,0],q[:,:,1],cv2.INTER_LINEAR)-.12*offsets[None,:]**2
                shift=offsets[np.argmax(score,axis=1)]
                shift=cv2.GaussianBlur(shift[:,None],(1,9),1.3).ravel()
                shift[:3]*=np.linspace(0,1,3);shift[-5:]*=np.linspace(1,0,5)
                curve+=normal*shift[:,None]
            self.curves[i]=curve
            # A scale estimate affects only the deformation; alpha remains the
            # actual photographed contour, including spines and irregularities.
            dist=cv2.dilate(dist,np.ones((5,5),np.uint8))
            radius=cv2.remap(dist,curve[:,0,None],curve[:,1,None],cv2.INTER_LINEAR).ravel()
            radius=np.maximum(cv2.GaussianBlur(radius[:,None],(1,13),2).ravel(),1.2)
            self.widths.append(radius)
            f=np.float32(g.FEATURES[i])*.5*g.K
            eye=f[1];r=[12,16,16,23,25][i]*g.K*.5
            ring=eye+np.float32([[-r,0],[0,-r],[r,0],[0,r]])
            # Corresponding outer fin landmarks align the native ray fan;
            # unlike v17-v19, no new fin geometry or texture is rendered.
            poly=np.float32(g.FINS[i])*g.K*.5
            outer=poly_resample(poly[1:-1],10)
            root0=poly[0];root1=poly[-1]
            root=np.linspace(root0,root1,10).astype(np.float32)
            radial=(root+outer)*.5
            self.fin_keys.append(np.stack([root,outer]))
            extra=np.vstack([ring,root,self.bounds])
            self.p.append(np.vstack([f,extra]))
            # Partition the original pixels into layers; no new fin image is
            # drawn. Keep warm bone/skin pixels in the foreground body layer.
            Y,X=np.mgrid[:960,:720].astype(np.float32)
            root_x=np.interp(Y[:,0],root[:,1]*2,root[:,0]*2)[:,None]
            region=np.zeros((960,720),np.uint8)
            cv2.fillPoly(region,[np.round(poly*2).astype(np.int32)],255)
            region=cv2.dilate(region,np.ones((7,7),np.uint8)).astype(np.float32)/255
            rgb=self.rgb[i]/np.maximum(self.alpha[i][...,None],.01)
            warm=(rgb[:,:,0]-rgb[:,:,2]>35)&(rgb[:,:,0]>70)
            mask=region*np.clip((X-root_x+1)/3,0,1)*(1-warm)
            self.body_rgb.append(self.rgb[i]*(1-mask[...,None]))
            self.body_a.append(self.alpha[i]*(1-mask))
            self.fin_rgb.append(self.rgb[i]*mask[...,None]);self.fin_a.append(self.alpha[i]*mask)
        self.widths=np.float32(self.widths);self.wm=g.v8.slopes(self.widths)
        self.curve_slopes=g.v8.slopes(self.curves)
        self.p=np.float32(self.p);self.pm=g.v8.slopes(self.p)
        self.fin_keys=np.float32(self.fin_keys);self.fm=g.v8.slopes(self.fin_keys)
        self.tris=[];self.metrics=[]
        for i in range(4):
            mid=(self.p[i]+self.p[i+1])*.5
            self.tris.append(self.m.triangulate(mid))

    def fin_frame(self,p,i,w):
        key=self.v8.cubic(self.fin_keys,p,self.fm).astype(np.float32)
        root,outer=key
        x0=max(0,int(key[:,:,0].min()-6));x1=min(360,int(key[:,:,0].max()+7))
        y0=max(0,int(key[:,:,1].min()-6));y1=min(480,int(key[:,:,1].max()+7))
        xx=self.xx[y0:y1,x0:x1];yy=self.yy[y0:y1,x0:x1]
        q=np.stack([xx.ravel(),yy.ravel()],axis=1)
        v=np.clip((q[:,1]-root[0,1])/max(root[-1,1]-root[0,1],1)*9,0,9)
        u=np.ones(len(q),np.float32)*.5
        for _ in range(12):
            r,rt,_=spline(root,v);o,ot,_=spline(outer,v)
            point=r+u[:,None]*(o-r);du=o-r;dv=rt+u[:,None]*(ot-rt)
            e=point-q;det=du[:,0]*dv[:,1]-du[:,1]*dv[:,0]
            delta_u=np.divide(e[:,0]*dv[:,1]-e[:,1]*dv[:,0],det,out=np.zeros_like(u),where=np.abs(det)>1e-5)
            delta_v=np.divide(du[:,0]*e[:,1]-du[:,1]*e[:,0],det,out=np.zeros_like(v),where=np.abs(det)>1e-5)
            u=np.clip(u-np.clip(delta_u,-.3,.3),-.3,1.3)
            v=np.clip(v-np.clip(delta_v,-1,1),0,9)
        r,_,_=spline(root,v);o,_,_=spline(outer,v);point=r+u[:,None]*(o-r)
        layers=[]
        for j in [i,i+1]:
            sr,_,_=spline(self.fin_keys[j,0],v);so,_,_=spline(self.fin_keys[j,1],v)
            mapped=q+(sr+u[:,None]*(so-sr)-point)
            dx=np.zeros((480,360),np.float32);dy=dx.copy()
            dx[y0:y1,x0:x1]=(mapped[:,0]-q[:,0]).reshape(xx.shape)
            dy[y0:y1,x0:x1]=(mapped[:,1]-q[:,1]).reshape(xx.shape)
            Y,X=np.mgrid[:960,:720].astype(np.float32)
            mp=(X+cv2.resize(dx,(720,960),interpolation=cv2.INTER_CUBIC)*2,
                Y+cv2.resize(dy,(720,960),interpolation=cv2.INTER_CUBIC)*2)
            c=cv2.remap(self.fin_rgb[j],*mp,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
            a=np.clip(cv2.remap(self.fin_a[j],*mp,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT),0,1)
            support=np.zeros((480,360),np.float32);support[y0:y1,x0:x1]=1
            support=cv2.resize(support,(720,960),interpolation=cv2.INTER_LINEAR)
            layers.append((c*support[...,None],a*support))
        c=(1-w)*layers[0][0]+w*layers[1][0];a=(1-w)*layers[0][1]+w*layers[1][1]
        return c,a

    def inverse_tail(self,dest,source,dw,sw,projection):
        q,dt,dn,coordinate=projection
        sc,st,_=spline(source,coordinate);st,sn=basis(st)
        longitudinal=np.sum((q-dest)*dt,axis=1)
        lateral=np.sum((q-dest)*dn,axis=1)
        ratio=np.interp(coordinate,np.arange(128),sw)/np.maximum(np.interp(coordinate,np.arange(128),dw),1)
        return sc+st*longitudinal[:,None]+sn*(lateral*ratio)[:,None]

    def maps(self,p):
        i=min(3,int(p));u=p-i
        dst=self.v8.cubic(self.p,p,self.pm).astype(np.float32)
        ca=self.curves[i];cb=self.curves[i+1]
        curve=self.v8.cubic(self.curves,p,self.curve_slopes).astype(np.float32)
        width=np.maximum(self.v8.cubic(self.widths,p,self.wm),1)
        # Project only the tail region. Newton refinement keeps the coordinate
        # continuous across the original centerline's sample boundaries.
        y0=max(0,int(curve[0,1]-20));x0=max(0,int(curve[:,0].min()-60));x1=min(360,int(curve[:,0].max()+60))
        xx=self.xx[y0:,x0:x1];yy=self.yy[y0:,x0:x1]
        best=np.full(xx.shape,1e10,np.float32);s=np.zeros(xx.shape,np.float32)
        for k in range(127):
            d=curve[k+1]-curve[k];den=max(float(np.dot(d,d)),1e-8)
            f=np.clip(((xx-curve[k,0])*d[0]+(yy-curve[k,1])*d[1])/den,0,1)
            dist=(xx-curve[k,0]-f*d[0])**2+(yy-curve[k,1]-f*d[1])**2
            update=dist<best;best[update]=dist[update];s[update]=k+f[update]
        q=np.stack([xx.ravel(),yy.ravel()],axis=1);s=s.ravel();initial=s.copy()
        for _ in range(7):
            center,tangent,second=spline(curve,s);delta=center-q
            val=np.sum(delta*tangent,axis=1)
            der=np.sum(tangent*tangent+delta*second,axis=1)
            step=np.divide(val,der,out=np.zeros_like(val),where=np.abs(der)>1e-5)
            s=np.clip(s-np.clip(step,-.5,.5),np.maximum(0,initial-1.5),np.minimum(127,initial+1.5))
        center,tangent,_=spline(curve,s);dt,dn=basis(tangent)
        projection=(q,dt,dn,s)
        by=self.v8.smooth((yy-curve[0,1]+6)/36)
        radius=np.interp(s,np.arange(128),width).reshape(xx.shape)
        # This generous support only prevents sampling unrelated image regions.
        # It does not draw the tail's outline or fill its interior.
        corridor=np.clip((radius*3+16-np.sqrt(best))/6,0,1)
        maps=[]
        for j,source in [(i,ca),(i+1,cb)]:
            mx,my=self.m.mesh_maps(self.p[j],dst,self.tris[i])
            tail=self.inverse_tail(center,source,width,self.widths[j],projection).reshape(*xx.shape,2)
            mx[y0:,x0:x1]=mx[y0:,x0:x1]*(1-by)+tail[:,:,0]*by
            my[y0:,x0:x1]=my[y0:,x0:x1]*(1-by)+tail[:,:,1]*by
            # Upsample displacement rather than absolute coordinates: an
            # identity transform stays exactly identity at every resolution.
            dx=cv2.resize(mx-self.xx,(720,960),interpolation=cv2.INTER_CUBIC)*2
            dy=cv2.resize(my-self.yy,(720,960),interpolation=cv2.INTER_CUBIC)*2
            Y,X=np.mgrid[:960,:720].astype(np.float32)
            maps.append((X+dx,Y+dy))
        support=np.ones((480,360),np.float32)
        support[y0:,x0:x1]=1-by*(1-corridor)
        # The specimen has no tail outside the mapped corridor at low y.
        low=self.yy>curve[0,1]+45
        support[low & ((self.xx<x0)|(self.xx>=x1))]=0
        return maps,dst[:15]*2,cv2.resize(support,(720,960),interpolation=cv2.INTER_LINEAR)

    def frame(self,p):
        p=float(np.clip(p,0,4));nearest=round(p)
        if abs(p-nearest)<1e-7:
            return self.rgb[nearest].copy(),self.alpha[nearest].copy(),self.points[nearest].copy()
        i=min(3,int(p));u=p-i;w=u*u*(3-2*u)
        maps,points,support=self.maps(p)
        colors=[];alphas=[]
        for j,mp in zip([i,i+1],maps):
            colors.append(cv2.remap(self.body_rgb[j],*mp,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
            alphas.append(np.clip(cv2.remap(self.body_a[j],*mp,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT),0,1))
        aa,ab=alphas
        # One contour, with no two translucent outer silhouettes. Preserve
        # subpixel/transparent coverage wherever the two sources already agree.
        da=self.m.sdf(aa);db=self.m.sdf(ab)
        shape=np.clip(((1-w)*da+w*db)*.9+.5,0,1)
        linear=(1-w)*aa+w*ab
        agreement=np.clip(1-np.abs(aa-ab)*2,0,1)
        edge_blend=4*w*(1-w)
        alpha=((shape*(1-agreement)+linear*agreement)*edge_blend+linear*(1-edge_blend))*support
        # The photographed body is one connected specimen. Disconnected
        # remnants produced by a warp must not become a second faint tail.
        n,labels,stats,_=cv2.connectedComponentsWithStats(np.uint8(alpha>.07))
        if n>1:
            keep=np.uint8(labels==(1+np.argmax(stats[1:,cv2.CC_STAT_AREA])))
            keep=cv2.dilate(keep,np.ones((3,3),np.uint8))
            fk=self.v8.cubic(self.fin_keys,p,self.fm)*2
            x0=max(0,int(fk[:,:,0].min())-8);x1=min(720,int(fk[:,:,0].max())+9)
            y0=max(0,int(fk[:,:,1].min())-8);y1=min(960,int(fk[:,:,1].max())+9)
            keep[y0:y1,x0:x1]=1
            alpha*=keep
        denominator=np.maximum(linear,.02)
        color=np.clip(((1-w)*colors[0]+w*colors[1])/denominator[...,None],0,255)
        rgb=color*alpha[...,None]
        fc,fa=self.fin_frame(p,i,w)
        # Add complementary partitions. They are exact source pixels at the
        # endpoint, including the original fin ray count and opacity.
        combined=alpha+fa
        rgb=(rgb+fc)/np.maximum(combined[...,None],1.)
        alpha=np.clip(combined,0,1)
        return np.clip(rgb,0,255),alpha,points
