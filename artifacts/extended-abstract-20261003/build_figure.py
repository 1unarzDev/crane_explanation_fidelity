"""Publication figure: unchanged recorded scene, vector annotations, exact counts."""
from pathlib import Path
import base64, html, json, math
import cairosvg
ROOT=Path(__file__).resolve().parents[2]; out=Path(__file__).resolve().parent
photo=ROOT/'artifacts/nav2-docking-reproduction-20261002/review-capsule/final-capture/mid.png'
D=json.loads((ROOT/'analysis/results/confirmation/b2-b4-frozen-claim-scores-2026-10-02.json').read_text())
W,H=1600,788; ink='#193545'; muted='#566d7b'; blue='#16748c'; rust='#b75a3a'
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><clipPath id="scene"><rect x="0" y="46" width="1000" height="470"/></clipPath><marker id="white" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="white"/></marker><marker id="ink" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="{ink}"/></marker></defs><rect width="100%" height="100%" fill="white"/>']
def txt(x,y,t,size=22,color=ink,bold=False):s.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="{color}" font-weight="{600 if bold else 400}">{html.escape(t)}</text>')
def rect(x,y,w,h,fill,rx=0):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>')
def line(x,y,u,v,color=ink,w=2,arrow=None):s.append(f'<line x1="{x}" y1="{y}" x2="{u}" y2="{v}" stroke="{color}" stroke-width="{w}"'+(f' marker-end="url(#{arrow})"' if arrow else '')+'/>')
def head(x,y,letter,title):txt(x,y,letter,24,blue,True);txt(x+42,y,title,24,ink,True)
head(0,28,'a','Recorded ASV navigation in CRANE')
s.append(f'<image clip-path="url(#scene)" x="0" y="46" width="1000" height="562.5" href="data:image/png;base64,{base64.b64encode(photo.read_bytes()).decode()}"/>')
# Opaque legend masks the historical UI; colored marks are recorded trace keys.
rect(14,57,286,163,'#122e3b',3);txt(30,85,'ASV NAVIGATION EVIDENCE',17,'white',True)
for i,(lab,col) in enumerate([('Planned route','#33cdd2'),('Observed trajectory','#ffe26c'),('Desired velocity twist','#fa50c8'),('Local costmap','#ff9866')]):
 y=112+i*24;line(30,y-6,52,y-6,col,3);txt(64,y,lab,17,'white')
def label(x,y,lab,u,v,side='left'):
 width=20+len(lab)*11;s.append(f'<rect x="{x}" y="{y}" width="{width}" height="34" rx="3" fill="#122e3b" fill-opacity="0.68"/>');txt(x+10,y+24,lab,19,'white',True)
 line(x-2 if side=='left' else x+width+2,y+17,u,v,'white',2,'white')
# Actual image anchors transform x*.625, y*.625+46.
label(276,306,'Dock',405,380,'right');label(665,408,'ASV',481,374)
label(699,259,'Local costmap',656,390)
# Right side: restrained aligned method paths instead of large padded cards.
head(1032,28,'','Evidence to explanation')
rect(1032,46,568,77,'#eef3f5',3);txt(1052,77,'Shared visible evidence',23,ink,True);txt(1052,106,'Relevant source + diagnostic computations',20,muted)
for y,name,color,rows in [(143,'B2  Tool-enabled agent',rust,['Inspect evidence and source','Compute diagnostics using tools','Generate natural-language answer']), (298,'B4  Diagnostic contract',blue,['Derive maximal supported diagnosis','Realize permitted claims + numeric slots','Verify claims against the evidence plan'])]:
 line(1032,y-17,1600,y-17,'#d4e0e5',1.5);rect(1032,y-4,4,113,color);txt(1052,y+15,name,23,color,True)
 for j,t in enumerate(rows):txt(1052,y+53+j*29,t,20)
line(1032,449,1600,449,'#d4e0e5',1.5);txt(1032,480,'Physical truth remains evaluator-only.',20,muted);txt(1032,508,'ASV demonstration; land/Nav2 evaluation.',20,muted)
# Common lower row: equal heading / baseline alignment, no excessive card padding.
s.append('<g transform="translate(0,-92)">')
head(0,646,'b','Same episode, nested evidence')
head(836,646,'c','Adverse-claim flags')
for i,(lev,title,sub) in enumerate([('E0','Outcome','action state'),('E1','Execution','recovery trace'),('E2','Command','delivered twist'),('E3','Response','odometry + test')]):
 x=i*197;rect(x,674,169,113,'#f1f5f6',3);rect(x,674,169,4,blue);txt(x+14,708,lev,24,blue,True);txt(x+14,741,title,21,ink,True);txt(x+14,769,sub,17,muted)
 if i<3:s.append(f'<path d="M{x+179} 726 L{x+184} 731 L{x+179} 736" fill="none" stroke="{muted}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
txt(0,825,'Evidence removal reverses this sequence.',20,ink,True)
txt(0,858,'More evidence supports deeper diagnosis, not a unique cause.',19,muted)
# Exact marginal rate CIs from the frozen artifact; grouped bars and whiskers.
left,right,base,top=890,1580,786,674
for tick in [0,.25,.5]:
 y=base-tick/.5*(base-top);line(left,y,right,y,'#dce5e9',1);txt(835,y+6,f'{tick*100:.0f}%',17,muted)
for i,l in enumerate(['E0','E1','E2','E3']):
 x=943+i*173
 for method,dx,col in [('B2',-19,rust),('B4',23,blue)]:
  r=D['method_level'][method+'_'+l];v=r['failure_rate'];lo,hi=r['wilson_95ci'];px=x+dx;yy=lambda q:base-q/.5*(base-top)
  if v:rect(px-15,yy(v),30,base-yy(v),col)
  else:line(px-12,base,px+12,base,col,3)
  line(px,yy(lo),px,yy(hi),ink,1.7);line(px-6,yy(hi),px+6,yy(hi),ink,1.7);line(px-6,yy(lo),px+6,yy(lo),ink,1.7)
 txt(x-13,815,l,18)
rect(891,834,15,15,rust);txt(916,847,'B2 agent',18);rect(1052,834,15,15,blue);txt(1077,847,'B4 contract',18)
txt(836,874,'95% Wilson CI; B4 upper bound 0.75%; n=507 (E1:509).',17,muted)
s.append('</g></svg>');svg='\n'.join(s);(out/'evidence-navigation-figure.svg').write_text(svg)
cairosvg.svg2pdf(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.pdf'))
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.png'))
