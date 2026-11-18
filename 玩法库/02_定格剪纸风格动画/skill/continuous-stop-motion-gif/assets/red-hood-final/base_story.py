from pathlib import Path
import argparse, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

ROOT=Path(__file__).resolve().parent
Q=2
W,H=1600,900
SIZE=(W*Q,H*Q)
AS=ROOT/'资产'
bg=Image.open(AS/'森林木屋.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
windowbg=Image.open(AS/'窗边近景.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
wolf0=Image.open(AS/'狼外婆_狡黠.png').convert('RGBA')
wolf1=Image.open(AS/'狼外婆_惊恐.png').convert('RGBA').resize(wolf0.size,Image.Resampling.LANCZOS)

def smooth(x):
 x=max(0,min(1,float(x)));return x*x*(3-2*x)
def ramp(t,a,b):return smooth((t-a)/(b-a))
def lerp(a,b,v):return tuple(x+(y-x)*v for x,y in zip(a,b))
def place(dst,src,xy):dst.alpha_composite(src,(round(xy[0]*Q),round(xy[1]*Q)))
def maskpoly(points,size=SIZE,logical=True):
 m=Image.new('L',size);ImageDraw.Draw(m).polygon([(round(x*(Q if logical else 1)),round(y*(Q if logical else 1))) for x,y in points],fill=255);return m
def cut(im,m):
 r=im.copy();r.putalpha(ImageChops.multiply(r.getchannel('A'),m));return r
def shadow_place(dst,src,xy,strength=.23):
 s=Image.new('RGBA',src.size,(30,20,23,0));s.putalpha(src.getchannel('A').filter(ImageFilter.GaussianBlur(1.4*Q)).point(lambda x:round(x*strength)))
 place(dst,s,(xy[0]+1.5,xy[1]+2));place(dst,src,xy)
def normalize_sprite(name):
 im=Image.open(AS/name).convert('RGBA');a=im.getchannel('A')
 box=a.point(lambda p:255 if p>20 else 0).getbbox()
 im=im.crop(box);aa=im.getchannel('A').point(lambda p:0 if p<6 else min(255,round(p*1.008)));im.putalpha(aa)
 return im
girl=normalize_sprite('小红帽.png')
middle=normalize_sprite('小红帽_半变身.png')
monster=normalize_sprite('小红帽_巨兽.png')

# The arm is isolated from the original paper puppet, keeping the sleeve's
# floral paper layers attached to that limb during the three knocks.
armpts=[(574,514),(615,536),(669,580),(693,600),(744,561),(776,541),(798,508),(820,459),(851,428),(905,420),(938,444),(943,482),(918,516),(867,540),(842,574),(830,614),(798,662),(759,691),(708,711),(667,700),(628,669),(609,623),(585,574)]
am=maskpoly(armpts,wolf0.size,False)
cores=[];arms=[]
for raw in [wolf0,wolf1]:
 ar=cut(raw,am);co=raw.copy();co.putalpha(ImageChops.subtract(co.getchannel('A'),ImageChops.multiply(co.getchannel('A'),am)))
 # Small shoulder backing under the rotating paper joint.
 joint=raw.crop((563,535,626,598));jm=Image.new('L',joint.size);ImageDraw.Draw(jm).ellipse((0,0,62,62),fill=255);joint.putalpha(ImageChops.multiply(joint.getchannel('A'),jm));co.alpha_composite(joint,(563,535))
 factor=350/1536*Q
 target=(round(raw.width*factor),round(raw.height*factor))
 cores.append(co.resize(target,Image.Resampling.LANCZOS));arms.append(ar.resize(target,Image.Resampling.LANCZOS))
wpivot=(590*350/1536*Q,550*350/1536*Q)
wfeet=(500*350/1536*Q,349*Q)

doorpts=[(980,766),(980,501),(983,459),(997,420),(1026,389),(1064,366),(1107,356),(1151,361),(1190,381),(1229,410),(1254,451),(1267,492),(1267,766)]
dm=maskpoly(doorpts)
door=cut(bg,dm)
# Preserve some paper fibers inside the opening, rather than using a flat fill.
sample=np.array(Image.open(AS/'森林木屋.png').convert('RGB').crop((810,480,920,575)).resize(SIZE,Image.Resampling.BILINEAR),float)
texture=sample.mean(2);texture=np.clip(texture/max(1,texture.mean()),.91,1.09)
x=np.arange(W*Q)[None,:]/Q;g=np.exp(-((x-1110)/115)**2)
col=np.stack([np.broadcast_to(54+35*g,(H*Q,W*Q)),np.broadcast_to(28+26*g,(H*Q,W*Q)),np.broadcast_to(21+15*g,(H*Q,W*Q))],2)
interior=Image.fromarray(np.uint8(np.clip(col*texture[:,:,None],0,255))).convert('RGBA');interior.putalpha(dm)
del sample,texture,col,g,x

windowmask=maskpoly([(527,141),(1069,141),(1067,649),(516,649)])
widewindowmask=maskpoly([(766,442),(901,442),(902,579),(765,579)])

def sprite_height(im,h):
 h=max(1,round(h*Q));return im.resize((max(1,round(im.width*h/im.height)),h),Image.Resampling.LANCZOS)

def knocking(t):
 return max([math.exp(-((t-hit)/.105)**2) for hit in [.72,1.38,2.05]]) if t<2.65 else 0.

def wolf_layer(t):
 k=knocking(t);fear=ramp(t,7.15,7.4);back=ramp(t,7.35,9.05)
 core=Image.blend(cores[0],cores[1],fear)
 arm=Image.blend(arms[0],arms[1],fear)
 angle=-12*k+30*back
 ar=arm.rotate(angle,Image.Resampling.BICUBIC,center=wpivot)
 core.alpha_composite(ar)
 lean=9*back
 core=core.rotate(lean,Image.Resampling.BICUBIC,center=wfeet)
 return core,(771+7*k-132*back,460)

def girl_layer(t):
 # Three paper states expand continuously on one shared ground anchor.
 grow=ramp(t,6.4,8.55)
 h=250+460*grow
 if t>8.55:h+=5*math.exp(-(t-8.55)*3)*math.sin((t-8.55)*12)
 if t<6.68:weights=[1.,0.,0.]
 elif t<7.22:
  z=ramp(t,6.68,7.15);weights=[1-z,z,0.]
 else:
  z=ramp(t,7.22,7.8);weights=[0.,1-z,z]
 sprites=[sprite_height(im,h) for im in [girl,middle,monster]]
 bw=max(s.width for s in sprites);bh=max(s.height for s in sprites)
 # Blend premultiplied RGBA to avoid dark fringes around the reveal.
 accum=np.zeros((bh,bw,4),np.float32)
 for im,weight in zip(sprites,weights):
  if weight<=0:continue
  a=np.array(im,np.float32)/255; a[:,:,:3]*=a[:,:,3:4]
  left=(bw-im.width)//2;accum[bh-im.height:bh,left:left+im.width]+=a*weight
 alpha=accum[:,:,3:4];accum[:,:,:3]=np.divide(accum[:,:,:3],np.maximum(alpha,1e-6))
 im=Image.fromarray(np.uint8(np.clip(accum*255,0,255)))
 step=ramp(t,5.25,6.1)
 ground=768+35*step
 if 5.25<t<6.1:ground-=3*abs(math.sin((t-5.25)/.85*math.pi*2))
 return im,(1125-im.width/(2*Q),ground-im.height/Q)

def world(t):
 out=bg.copy();op=ramp(t,4.35,5.4)
 if op>0:
  out.alpha_composite(interior)
 if t>=4.3:
  gl,pos=girl_layer(t)
  if t<5.65:
   glayer=Image.new('RGBA',SIZE);place(glayer,gl,pos)
   glayer.putalpha(ImageChops.multiply(glayer.getchannel('A'),dm));out.alpha_composite(glayer)
 if op>0:
  panel=door.crop((978*Q,354*Q,1269*Q,768*Q))
  width=max(3,round(291*(1-.85*op)))
  panel=panel.resize((width*Q,414*Q),Image.Resampling.BICUBIC)
  shadow_place(out,panel,(1269-width,354),.25)
 if t>=5.65:
  # Once she steps outside, the opened door must stay behind the cape.
  gl,pos=girl_layer(t);shadow_place(out,gl,pos,.20)
 # The wolf is in the foreground until the monster grows in front of him.
 wl,pos=wolf_layer(t)
 floor=Image.new('RGBA',(250*Q,22*Q));fd=ImageDraw.Draw(floor);fd.ellipse((0,3*Q,250*Q,18*Q),fill=(28,20,20,48));floor=floor.filter(ImageFilter.GaussianBlur(4*Q));place(out,floor,(pos[0]-5,801))
 shadow_place(out,wl,pos,.19)
 return out

def peek(t):
 out=windowbg.copy()
 emerge=ramp(t,2.92,3.43)*(1-ramp(t,3.72,4.18))
 im=sprite_height(ImageOps.mirror(girl),1180)
 px=1050+(420-1050)*emerge
 layer=Image.new('RGBA',SIZE);place(layer,im,(px,146+2*math.sin(emerge*math.pi)))
 layer.putalpha(ImageChops.multiply(layer.getchannel('A'),windowmask));out.alpha_composite(layer)
 return out

def crop_camera(scene,box):
 b=tuple(round(v*Q) for v in box)
 return scene.crop(b).resize((1600,900),Image.Resampling.LANCZOS).convert('RGB')

def raw_frame(t):
 if 2.8<=t<4.3:
  return crop_camera(peek(t),(0,0,1600,900))
 sc=world(t)
 if t<2.8:
  box=lerp((480,285,1530,875.625),(570,340,1470,846.25),ramp(t,0,2.65))
 elif t<8.55:
  box=lerp((590,285,1590,847.5),(0,0,1600,900),ramp(t,6.4,8.55))
 elif t<9.35:box=(570,380,1146,704)
 else:box=(0,0,1600,900)
 return crop_camera(sc,box)

FIRST=None
def frame(t):
 global FIRST
 if FIRST is None:FIRST=raw_frame(0)
 result=raw_frame(t)
 if t>=11.55:result=Image.blend(result,FIRST,ramp(t,11.55,11.9))
 return result

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--render',action='store_true');args=ap.parse_args()
 samples=[0,.72,2.05,2.9,3.45,4.6,5.6,6.5,7.05,7.65,8.45,8.9,9.8,11.2,11.99]
 board=Image.new('RGB',(5*384,3*238),'#eee8de');bd=ImageDraw.Draw(board)
 for i,t in enumerate(samples):
  f=frame(t);f.save(ROOT/f'检查_{i:02d}.png')
  board.paste(f.resize((384,216),Image.Resampling.LANCZOS),((i%5)*384,(i//5)*238));bd.text(((i%5)*384+6,(i//5)*238+220),f'{t:.2f}s',fill='#222222')
 board.save(ROOT/'镜头与动作检查.png')
 if args.render:
  out=ROOT/'frames';out.mkdir(exist_ok=True)
  for i in range(144):
   frame(i/12).save(out/f'{i:04d}.png')
   if i%24==0:print(f'rendered {i}/144',flush=True)
  print('rendered 144/144',flush=True)
 report={'duration_seconds':12,'poses_per_second':12,'frames':144,'output_frame_size':[1600,900],'logical_wolf_height':350,'logical_monster_height':710,'monster_wolf_height_ratio':710/350,'loop':'ending dissolve into replay, not a reverse transformation','method':'photographed-style paper assets, isolated arm, three-state paper silhouette transformation, multi-shot camera'}
 (ROOT/'制作参数.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
