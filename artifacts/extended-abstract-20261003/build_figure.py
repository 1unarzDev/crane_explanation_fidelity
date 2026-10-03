from pathlib import Path
import base64,html,json
import cairosvg
ROOT=Path(__file__).resolve().parents[2]; out=Path(__file__).resolve().parent
photo=ROOT/'artifacts/nav2-docking-reproduction-20261002/review-capsule/final-capture/mid.png'
b64=base64.b64encode(photo.read_bytes()).decode()
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="850" viewBox="0 0 1600 850"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#263746"/></marker></defs><rect width="1600" height="850" fill="white"/>']
def text(x,y,t,size=24,color='#162d40',bold=False):s.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{html.escape(t)}</text>')
def line(x,y,u,v,color='#263746',arrow=False):s.append(f'<line x1="{x}" y1="{y}" x2="{u}" y2="{v}" stroke="{color}" stroke-width="3" '+('marker-end="url(#arrow)"' if arrow else '')+'/>')
text(15,30,'(a) ASV docking: recorded navigation evidence',27,bold=True)
s.append(f'<image x="0" y="45" width="960" height="540" href="data:image/png;base64,{b64}"/>')
# Vector panel covers legacy UI label, preserving the raw captured image file.
s.append('<rect x="12" y="56" width="232" height="150" rx="5" fill="#102c38"/>')
text(24,81,'ASV • EVIDENCE VIEW',18,'white',True)
for i,(label,color) in enumerate([('Planned route','#33cdd2'),('Observed trajectory','#ffe26c'),('Command vector','#fa50c8'),('Local costmap','#ff9866')]):
 y=107+23*i;line(24,y-5,47,y-5,color);text(55,y,label,16,'white')
# important physical features, arrows are outside busy footprint
for x,y,t,u,v in [(300,340,'Dock',390,342),(660,412,'ASV',461,355),(680,276,'Costmap overlay',620,302),(120,420,'Observed trajectory',350,388)]:
 s.append(f'<rect x="{x-8}" y="{y-23}" width="{max(100,len(t)*13)}" height="31" rx="4" fill="white" fill-opacity="0.95"/>');text(x,y,t,21,bold=True);line(x-10 if t in ('ASV','Costmap overlay') else x+max(100,len(t)*13),y-9,u,v,arrow=True)
text(985,30,'(b) Same episode, evidence removed',27,bold=True)
steps=[('E0','Observed outcome / cutoff'),('E1','+ source-qualified execution trace'),('E2','+ delivered command'),('E3','+ synchronized odometry'),('','  + governed diagnostic computation')]
for i,(lab,desc) in enumerate(steps[:4]):
 y=65+i*112;s.append(f'<rect x="980" y="{y}" width="603" height="82" rx="8" fill="#edf4f8" stroke="#7797a9"/>');text(1000,y+32,lab,26,bold=True);text(1060,y+32,desc,21)
 if i==3:text(1000,y+64,'+ governed diagnostic computation',20)
 if i<3:line(1275,y+85,1275,y+108,arrow=True)
text(987,535,'Removal reverses the arrows.',22,bold=True)
text(987,564,'Hidden physical truth never enters the ladder.',19)
text(15,622,'(c) Episodes flagged at each evidence level',27,bold=True)
# marginal confidence intervals / actual denominators
vals=[.4437869822,.04518664,.30571992,.07692308];ci=[(.4011239,.4872955),(.0302963,.0668905),(.2672026,.3471592),(.0567791,.10343)]
def yy(v):return 800-v*300
for v in [0,.25,.5]:
 y=yy(v);line(75,y,940,y,'#d7e2e8');text(12,y+7,f'{v*100:.0f}%',18)
for i in range(4):
 x=180+i*220;lo,hi=ci[i];line(x-16,yy(lo),x-16,yy(hi),'#a6492d');line(x-23,yy(lo),x-9,yy(lo),'#a6492d');line(x-23,yy(hi),x-9,yy(hi),'#a6492d');s.append(f'<circle cx="{x-16}" cy="{yy(vals[i])}" r="7" fill="#a6492d"/>');line(x+16,yy(0),x+16,yy(.00752),'#146b86');s.append(f'<rect x="{x+10}" y="{yy(0)-6}" width="12" height="12" fill="#146b86"/>');text(x-32,833,f'E{i}',21)
text(993,636,'B2: tool-enabled agent (circles)',23,'#a6492d',True);text(993,671,'B4: diagnostic contract (squares)',23,'#146b86',True)
text(993,714,'Bars: marginal 95% Wilson intervals.',20);text(993,745,'Paired episodes; levels are repeated measures.',18);text(993,776,'E0/E2/E3: n = 507; E1: n = 509.',20);text(993,809,'B4 upper 95% limit: about 0.75% at all levels.',20)
s.append('</svg>');svg='\n'.join(s);(out/'evidence-navigation-figure.svg').write_text(svg);cairosvg.svg2pdf(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.pdf'));cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.png'))
