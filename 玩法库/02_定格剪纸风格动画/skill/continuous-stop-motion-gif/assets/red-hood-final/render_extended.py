from pathlib import Path
import argparse,math,json,shutil,hashlib
import numpy as np
import cv2 as cv
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import base_story as b

ROOT=Path(__file__).resolve().parent
Q=b.Q
AS=ROOT/'资产'
raw=Image.open(AS/'灰狼_未换装.png').convert('RGBA')
tree=Image.open(AS/'前景大树.png').convert('RGBA').resize((330*Q,940*Q),Image.Resampling.LANCZOS)
# Remove colored RGB remnants only where alpha is already nearly transparent.
ta=np.array(tree);ta[ta[:,:,3]<12]=0;tree=Image.fromarray(ta)

backpts=[(402,1100),(489,1102),(534,1168),(531,1217),(471,1262),(425,1305),(383,1380),(362,1424),(432,1422),(451,1450),(450,1488),(395,1504),(283,1504),(238,1490),(233,1461),(256,1390),(298,1300),(337,1254),(381,1220),(402,1166)]
frontpts=[(630,1057),(699,1060),(786,1091),(816,1129),(809,1180),(770,1228),(729,1268),(705,1294),(732,1318),(768,1345),(789,1377),(788,1417),(759,1444),(714,1440),(683,1410),(666,1375),(620,1343),(590,1309),(588,1272),(621,1229),(661,1182),(676,1151),(655,1130)]
masks=[b.maskpoly(backpts,raw.size,False),b.maskpoly(frontpts,raw.size,False)]
union=ImageChops.lighter(*masks)
body=raw.copy();body.putalpha(ImageChops.subtract(body.getchannel('A'),ImageChops.multiply(body.getchannel('A'),union)))
coords=[[(437,1120),(340,1300),(305,1450)],[(708,1103),(660,1270),(734,1380)]]
parts=[]
for m,(hip,knee,ankle) in zip(masks,coords):
 leg=b.cut(raw,m);a=np.array(leg)
 upper=a.copy();upper[round(knee[1])+24:,:,3]=0
 lower=a.copy();lower[:round(knee[1])-24,:,3]=0
 parts.append((upper,lower,np.array(hip,float),np.array(knee,float),np.array(ankle,float)))

def warp_segment(image,p,q,np_,nq):
 v=q-p;nv=nq-np_;perp=np.array([-v[1],v[0]])/np.linalg.norm(v);nperp=np.array([-nv[1],nv[0]])/max(.01,np.linalg.norm(nv))
 mat=cv.getAffineTransform(np.float32([p,q,p+perp*50]),np.float32([np_,nq,np_+nperp*50]))
 return Image.fromarray(cv.warpAffine(image,mat,raw.size,flags=cv.INTER_CUBIC,borderMode=cv.BORDER_CONSTANT,borderValue=(0,0,0,0)))

def bare_actor(distance):
 phase=distance/100*2*math.pi
 layers=[]
 for i,(upper,lower,hip,knee,ankle) in enumerate(parts):
  ph=phase+i*math.pi
  # A planted half-cycle travels back locally as the body advances.
  dx=105*math.cos(ph)
  lift=105*max(0,math.sin(ph))
  target=ankle+np.array([dx,-lift+(48 if i else 0)])
  delta=target-hip;dist=np.linalg.norm(delta);u=delta/max(dist,.01)
  l1=np.linalg.norm(knee-hip)*1.07;l2=np.linalg.norm(ankle-knee)*1.07
  dist=min(dist,l1+l2-.01)
  along=(l1*l1-l2*l2+dist*dist)/(2*dist)
  side=-np.array([u[1],-u[0]])
  nk=hip+u*along+side*math.sqrt(max(0,l1*l1-along*along))
  leg=warp_segment(upper,hip,knee,hip,nk);leg.alpha_composite(warp_segment(lower,knee,ankle,nk,target));layers.append(leg)
 out=Image.new('RGBA',raw.size)
 out.alpha_composite(layers[0]);out.alpha_composite(layers[1]);out.alpha_composite(body)
 # Keep the hunched torso and costume bundle stable, with restrained breathing.
 return out.resize((round(raw.width*350/1536*Q),350*Q),Image.Resampling.LANCZOS)

granny,unused=b.wolf_layer(0)
factor=350/1536*Q
gm=[]
for pts in [[(290,1392),(475,1392),(478,1534),(270,1534)],[(490,1392),(715,1392),(724,1534),(488,1534)]]:
 m=b.maskpoly([(x*factor,y*factor) for x,y in pts],granny.size,False);gm.append(m)
gu=ImageChops.lighter(*gm)
gbody=granny.copy();gbody.putalpha(ImageChops.subtract(gbody.getchannel('A'),ImageChops.multiply(gbody.getchannel('A'),gu)))
glegs=[b.cut(granny,m) for m in gm]

def granny_actor(t,x):
 moving=1-b.ramp(t,5.55,5.85)
 if moving<.0001:return granny.copy()
 phase=(x-480)/55*2*math.pi
 im=Image.new('RGBA',granny.size)
 for i,leg in enumerate(glegs):
  angle=16*math.sin(phase+i*math.pi)*moving
  pivot=((375 if i==0 else 596)*factor,1393*factor)
  im.alpha_composite(leg.rotate(angle,Image.Resampling.BICUBIC,center=pivot))
 im.alpha_composite(gbody)
 return im

# Reuse the actual lilac dress edge and lace bonnet from the approved disguise.
cloth=b.wolf0.crop((174,1000,753,1400)).resize((110*Q,76*Q),Image.Resampling.LANCZOS)
hat=b.wolf0.crop((293,40,765,380))
ha=np.array(hat);rgb=ha[:,:,:3].astype(float)
cream=(rgb[:,:,0]>rgb[:,:,1]*1.055)&(rgb[:,:,0]>155)&(rgb[:,:,1]>140)
ha[:,:,3]=np.where(cream,ha[:,:,3],0);hat=Image.fromarray(ha).resize((100*Q,72*Q),Image.Resampling.LANCZOS)

def add_floor(out,x,y,width=250):
 im=Image.new('RGBA',(width*Q,22*Q));ImageDraw.Draw(im).ellipse((0,3*Q,width*Q,18*Q),fill=(28,20,20,48));im=im.filter(ImageFilter.GaussianBlur(4*Q));b.place(out,im,(x-5,y))

def tree_xy(t):
 return (440-300*b.ramp(t,4.35,5.85),-105)

def intro_scene(t,return_layers=False):
 out=b.bg.copy()
 if t<3.5:
  x=20+460*b.ramp(t,.05,2.85)
  actor=bare_actor(x-20)
  bob=-2*abs(math.sin((x-20)/100*math.pi*2)) if t<2.85 else 0
  pos=(x,466+bob)
 else:
  x=480+291*b.ramp(t,4.35,5.85)
  actor=granny_actor(t,x)
  bob=-2*abs(math.sin((x-480)/55*math.pi*2))*(1-b.ramp(t,5.55,5.85))
  pos=(x,460+bob)
 add_floor(out,x,801)
 b.shadow_place(out,actor,pos,.19)
 # Glimpses beyond the opaque trunk communicate the hidden costume change.
 dressmove=math.exp(-((t-3.1)/.22)**2)
 hatmove=math.exp(-((t-3.85)/.20)**2)
 if dressmove>.008:
  piece=cloth.rotate(20*math.sin(t*16),Image.Resampling.BICUBIC,expand=True)
  piece.putalpha(piece.getchannel('A').point(lambda a:round(a*dressmove)))
  b.shadow_place(out,piece,(605+50*dressmove,635-12*dressmove),.16)
 if hatmove>.008:
  piece=hat.rotate(-20*math.sin(t*16),Image.Resampling.BICUBIC,expand=True)
  piece.putalpha(piece.getchannel('A').point(lambda a:round(a*hatmove)))
  b.shadow_place(out,piece,(620+45*hatmove,463-25*hatmove),.16)
 b.shadow_place(out,tree,tree_xy(t),.20)
 if return_layers:return out,actor,pos
 return out

def intro_frame(t):
 if t>=5.85:return b.raw_frame(0)
 box=b.lerp((0,260,1050,850.625),(100,270,1150,860.625),b.ramp(t,0,2.8))
 box=b.lerp(box,(480,285,1530,875.625),b.ramp(t,4.35,5.85))
 return b.crop_camera(intro_scene(t),box)

FIRST=None
def full_frame(i):
 global FIRST
 if FIRST is None:FIRST=intro_frame(0)
 if i<72:return intro_frame(i/12)
 t=(i-72)/12
 f=b.raw_frame(t)
 if t>=11.55:f=Image.blend(f,FIRST,b.ramp(t,11.55,11.9))
 return f

def occlusion_report(t):
 _,actor,pos=intro_scene(t,True)
 al=Image.new('RGBA',b.SIZE);b.place(al,actor,pos)
 tr=Image.new('RGBA',b.SIZE);b.place(tr,tree,tree_xy(t))
 a=np.array(al.getchannel('A'),float)/255;cover=np.array(tr.getchannel('A'),float)/255
 return float((a*(1-cover)).sum()/max(1,a.sum()))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--render',action='store_true');ap.add_argument('--reuse-frames',type=Path);args=ap.parse_args()
 times=[0,.55,1.25,1.9,2.6,3.1,3.85,4.35,4.75,5.2,5.65,5.92]
 board=Image.new('RGB',(4*400,3*247),'#eee9df');d=ImageDraw.Draw(board)
 for j,t in enumerate(times):
  im=intro_frame(t);im.save(ROOT/f'前奏检查_{j:02d}.png');board.paste(im.resize((400,225),Image.Resampling.LANCZOS),((j%4)*400,(j//4)*247));d.text(((j%4)*400+5,(j//4)*247+230),f'{t:.2f}s',fill='black')
 board.save(ROOT/'前奏动作检查.png')
 checks={'hidden_visibility_3s':occlusion_report(3.),'hidden_visibility_3_55s':occlusion_report(3.55),'duration_seconds':18,'prefix_frames':72,'original_story_frames':144,'input_frames':216,'render_size':[1600,900],'fps':12,'preserved_original_png_frames':0,'replay_transition_changed':5}
 if args.render:
  frames=ROOT/'frames';frames.mkdir(exist_ok=True)
  for i in range(216):
   target=frames/f'{i:04d}.png'
   # Copy original PNG bytes for the story itself; only replay dissolve changes.
   if args.reuse_frames and 72<=i<211:
    shutil.copy2(args.reuse_frames/f'{i-72:04d}.png',target);checks['preserved_original_png_frames']+=1
   else:full_frame(i).save(target)
   if i%24==0:print(f'rendered {i}/216',flush=True)
  print('rendered 216/216',flush=True)
 (ROOT/'制作参数.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(checks,ensure_ascii=False))
