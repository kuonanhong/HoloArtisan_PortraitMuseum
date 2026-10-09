/* Holo-Artisan portrait response renderer. Original painting pixels are warped,
 * never represented as diffusion synthesis or measured optical holography. */
(function(global){'use strict';
const EMOTIONS={joy:{smile:1,brow:-.2,open:.15,tilt:.012},anger:{smile:-.35,brow:.8,open:.04,tilt:-.008},sadness:{smile:-.8,brow:-.65,open:.03,tilt:-.018},delight:{smile:1.5,brow:-.6,open:.6,tilt:.016}};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function gauss(x,y,cx,cy,rx,ry){return Math.exp(-(((x-cx)/rx)**2+((y-cy)/ry)**2)*2)}
function create(canvas){
const ctx=canvas.getContext('2d',{alpha:false});
let art=null,img=null,face=null,response={emotion:'joy',gesture:'still',text:'',gaze:{x:.5,y:.4}},gaze={x:.5,y:.4},active=false,lastTime=0,lastW=0,lastH=0,dirty=true,disposed=false,start=0;
const base=document.createElement('canvas'),bctx=base.getContext('2d',{alpha:false});
let fit={x:0,y:0,w:1,h:1},blend=0;
function defaultBox(a){
 const t=(a?.title||'').toLowerCase();
 if(/mona lisa|joconde/.test(t))return {x:.33,y:.10,w:.32,h:.31};
 if(/pearl earring/.test(t))return {x:.29,y:.23,w:.45,h:.47};
 return {x:.29,y:.14,w:.42,h:.42};
}
function resize(){const r=canvas.getBoundingClientRect(),d=Math.min(global.devicePixelRatio||1,1.5),w=Math.max(1,Math.round((r.width||400)*d)),h=Math.max(1,Math.round((r.height||500)*d));if(w!==lastW||h!==lastH){canvas.width=w;canvas.height=h;base.width=w;base.height=h;lastW=w;lastH=h;dirty=true}}
function background(){
 const w=canvas.width,h=canvas.height;bctx.fillStyle='#171b1a';bctx.fillRect(0,0,w,h);
 if(img&&img.complete&&img.naturalWidth){const scale=Math.min(w/img.naturalWidth,h/img.naturalHeight);fit={w:img.naturalWidth*scale,h:img.naturalHeight*scale};fit.x=(w-fit.w)/2;fit.y=(h-fit.h)/2;bctx.drawImage(img,fit.x,fit.y,fit.w,fit.h)}
 dirty=false;
}
function point(x,y,t){
 const f=face||defaultBox(art),fx=fit.x+fit.w*f.x,fy=fit.y+fit.h*f.y,fw=fit.w*f.w,fh=fit.h*f.h;
 const u=(x-fx)/fw,v=(y-fy)/fh,p=EMOTIONS[response.emotion]||EMOTIONS.joy;
 if(u<-.2||u>1.2||v<-.2||v>1.2||!active)return [x,y];
 const landmarks=art?.faceLandmarks;const coord=(p,axis,fallback)=>p?(p[axis]??p[axis==='x'?0:1]):fallback;const mp=landmarks?.mouth;const mx=mp?(coord(mp,'x',f.x+f.w*.5)-f.x)/f.w:.5,my=mp?(coord(mp,'y',f.y+f.h*.77)-f.y)/f.h:.77;
 const strength=blend,ex=clamp(gaze.x??.5,0,1)-.5,ey=clamp(gaze.y??.5,0,1)-.5;
 let dx=0,dy=0;
 // Soft local deformation keeps frame, clothing and museum background fixed.
 const mask=gauss(u,v,.5,.5,.66,.66);
 dx+=ex*fw*.038*mask;dy+=ey*fh*.024*mask;
 const mouth=gauss(u,v,mx,my,.24,.10);
 const leftCorner=gauss(u,v,mx-.17,my-.01,.12,.09),rightCorner=gauss(u,v,mx+.17,my-.01,.12,.09);
 dy-=p.smile*fh*.035*(leftCorner+rightCorner);
 dx+=(u-mx)*p.smile*fw*.065*mouth;
 dy+=(v>my+.01?1:-1)*fh*.014*p.open*mouth*(.65+.35*Math.sin(t*5));
 const brows=gauss(u,v,.31,.34,.16,.05)+gauss(u,v,.69,.34,.16,.05);
 dy+=fh*.025*p.brow*brows;
 const eyes=gauss(u,v,.32,.42,.14,.055)+gauss(u,v,.68,.42,.14,.055);
 dx+=fw*.023*ex*eyes;dy+=fh*.018*ey*eyes;
 const nod=response.gesture==='nod'?Math.sin(t*2.2)*.014:response.gesture==='tilt'?.012:0;
 dx+=(v-.5)*fw*(p.tilt+nod)*mask;dy-=(u-.5)*fh*(p.tilt+nod)*mask;
 return [x+dx*strength,y+dy*strength];
}
function triangle(s0,s1,s2,d0,d1,d2){
 const x0=s0[0],y0=s0[1],x1=s1[0],y1=s1[1],x2=s2[0],y2=s2[1];
 const det=x0*(y1-y2)+x1*(y2-y0)+x2*(y0-y1);if(Math.abs(det)<.001)return;
 const A=(d0[0]*(y1-y2)+d1[0]*(y2-y0)+d2[0]*(y0-y1))/det;
 const C=(d0[0]*(x2-x1)+d1[0]*(x0-x2)+d2[0]*(x1-x0))/det;
 const E=(d0[0]*(x1*y2-x2*y1)+d1[0]*(x2*y0-x0*y2)+d2[0]*(x0*y1-x1*y0))/det;
 const B=(d0[1]*(y1-y2)+d1[1]*(y2-y0)+d2[1]*(y0-y1))/det;
 const D=(d0[1]*(x2-x1)+d1[1]*(x0-x2)+d2[1]*(x1-x0))/det;
 const F=(d0[1]*(x1*y2-x2*y1)+d1[1]*(x2*y0-x0*y2)+d2[1]*(x0*y1-x1*y0))/det;
 ctx.save();ctx.beginPath();const mx=(d0[0]+d1[0]+d2[0])/3,my=(d0[1]+d1[1]+d2[1])/3;
 // A subpixel overlap prevents hairline triangle seams on HiDPI canvases.
 const expand=p=>[p[0]+Math.sign(p[0]-mx)*.38,p[1]+Math.sign(p[1]-my)*.38];
 [d0,d1,d2].map(expand).forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.clip();ctx.setTransform(A,B,C,D,E,F);ctx.drawImage(base,0,0);ctx.restore();
}
function draw(now){if(disposed)return;resize();if(dirty)background();let t=(Number(now)||performance.now())/1000;if(t>1e7)t=performance.now()/1000;
 if(!active||!img||art?.portrait===false){ctx.drawImage(base,0,0);return}
 if(t-lastTime<1/18&&blend>=.99)return;lastTime=t;blend=Math.min(1,blend+.07);ctx.drawImage(base,0,0);
 const f=face||defaultBox(art);const x0=clamp(fit.x+fit.w*(f.x-f.w*.2),0,canvas.width),y0=clamp(fit.y+fit.h*(f.y-f.h*.2),0,canvas.height),x1=clamp(fit.x+fit.w*(f.x+f.w*1.2),0,canvas.width),y1=clamp(fit.y+fit.h*(f.y+f.h*1.2),0,canvas.height);
 const cols=14,rows=18,pts=[];for(let j=0;j<=rows;j++){pts[j]=[];for(let i=0;i<=cols;i++){const p=[x0+(x1-x0)*i/cols,y0+(y1-y0)*j/rows];pts[j][i]={s:p,d:point(...p,t-start)}}}
 for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){const a=pts[j][i],b=pts[j][i+1],c=pts[j+1][i],d=pts[j+1][i+1];triangle(a.s,b.s,c.s,a.d,b.d,c.d);triangle(b.s,d.s,c.s,b.d,d.d,c.d)}
}
return {setArtwork(a,image){art=a;face=a?.faceBox||null;active=false;blend=0;img=image||new Image();if(!image){img.onload=()=>{dirty=true;draw(performance.now())};img.src=a?.image||''}dirty=true;draw(performance.now())},setResponse(r){response={...response,...r};if(r.gaze)gaze={...r.gaze};active=!!r.text;blend=0;start=performance.now()/1000;dirty=true},setGaze(g){gaze={...g};dirty=true},setFaceBox(f){face={x:clamp(f.x,0,.95),y:clamp(f.y,0,.95),w:clamp(f.w,.04,1),h:clamp(f.h,.04,1)};dirty=true},draw,dispose(){disposed=true;img=null},getInfo(){return {method:'local piecewise-affine expression animation',neuralImageSynthesis:false,faceBox:face||defaultBox(art),active,artworkId:art?.id}}};
}
global.HoloPortraitRenderer={create};
})(window);
