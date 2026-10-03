"""Vector annotation over the unchanged ASV capture; paired ladder/bar figure."""
from pathlib import Path
import base64,html
import cairosvg
ROOT=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent
photo=ROOT/'artifacts/nav2-docking-reproduction-20261002/review-capsule/final-capture/mid.png'
b64=base64.b64encode(photo.read_bytes()).decode()
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="880" viewBox="0 0 1600 880"><defs><marker id="white" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="white"/></marker><marker id="blue" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#146b86"/></marker></defs><rect width="1600" height="960" fill="white"/>']
def text(x,y,t,size=24,color='#173044',bold=False):s.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{html.escape(t)}</text>')
def line(x,y,u,v,color='#146b86',arrow=None,w=3):s.append(f'<line x1="{x}" y1="{y}" x2="{u}" y2="{v}" stroke="{color}" stroke-width="{w}" '+(f'marker-end="url(#{arrow})"' if arrow else '')+'/>')
def box(x,y,w,h,fill='#153747'):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}"/>')
text(10,29,'(a) CRANE platform: ASV navigation evidence',27,bold=True)
s.append(f'<image x="0" y="43" width="960" height="540" href="data:image/png;base64,{b64}"/>')
box(12,54,275,156)
text(24,80,'ASV • LIVE EVIDENCE',18,'white',True)
for i,(label,col) in enumerate([('Planned route','#33cdd2'),('Observed trajectory','#ffe26c'),('Desired velocity twist','#fa50c8'),('Local costmap','#ff9866')]):
 y=107+23*i;line(24,y-5,47,y-5,col);text(56,y,label,16,'white')
def callout(x,y,label,u,v,start='left'):
 width=max(75,len(label)*11+18);box(x,y,width,32);text(x+9,y+23,label,19,'white',True)
 line(x-2 if start=='left' else x+width+2,y+16,u,v,'white','white',2.5)
callout(290,324,'Dock',389,364,'right');callout(650,398,'ASV',461,354)
callout(668,260,'Local costmap',620,299)
callout(95,413,'Observed trajectory',366,390,'right')
callout(287,222,'Planned route',420,337,'right')
callout(642,475,'Desired velocity twist',445,348)
text(982,29,'One evidence boundary; two explainers',27,bold=True)
for y,title,col,lines in [(62,'B2 • tool-enabled LLM agent','#a6492d',['Visible evidence + source/configuration','Permitted diagnostic computations','Natural-language answer returned verbatim']), (266,'B4 • diagnostic-contract method','#146b86',['Same visible evidence and source access','Maximal supported diagnosis','Constrained clauses + exact numeric slots','Final claim verification'])]:
 box(980,y,603,175 if y==62 else 201,'#f0f5f7');text(998,y+34,title,23,col,True)
 for j,t in enumerate(lines):text(998,y+72+j*30,t,21)
text(990,518,'ASV illustration; results below: land/Nav2.',20,bold=True)
text(990,552,'Physical truth is evaluator-only.',22)
text(10,614,'(b) Same episode, nested evidence',25,bold=True)
# horizontal evidence accumulation; removal is reverse traversal
labels=[('E0',['Outcome / cutoff']),('E1',['+ action /','recovery trace']),('E2',['+ delivered','command']),('E3',['+ odometry /','computation'])]
for i,(lab,desc) in enumerate(labels):
 x=12+i*193;box(x,647,166,104,'#e8f1f5');text(x+11,675,lab,26,bold=True)
 for j,t in enumerate(desc):text(x+11,706+j*24,t,18)
 if i<3:line(x+169,697,x+189,697,arrow='blue')
text(15,792,'Evidence removed: E3 to E2 to E1 to E0.',20,bold=True)
text(15,823,'Commands + measured motion justify discrepancy,',19)
text(15,851,'not a unique motor, collision, or obstruction cause.',19)
text(825,614,'(c) Episodes flagged by evidence level',25,bold=True)
# bars with confidence whiskers, shared method key underneath
vals=[.4437823822,.04518664,.30571992,.07692308];ci=[(.4011239,.4872955),(.0302963,.0668905),(.2667526,.3471592),(.0567791,.10343)]
def yy(v):return 781-v*270
for v in [0,.25,.5]:
 y=yy(v);line(876,y,1575,y,'#d9e5eb',w=1.5);text(824,y+6,f'{v*100:.0f}%',17)
for i in range(4):
 x=932+i*170;lo,hi=ci[i];s.append(f'<rect x="{x-23}" y="{yy(vals[i])}" width="36" height="{vals[i]*270}" fill="#a6492d"/>');line(x-5,yy(lo),x-5,yy(hi),'#673020',w=2);line(x-12,yy(lo),x+2,yy(lo),'#673020',w=2);line(x-12,yy(hi),x+2,yy(hi),'#673020',w=2)
 line(x+32,yy(0),x+32,yy(.00752),'#146b86',w=3);line(x+24,yy(0),x+40,yy(0),'#146b86',w=4);text(x-8,810,f'E{i}',20)
box(879,827,18,18,'#a6492d');text(907,843,'B2 agent',19);box(1060,827,18,18,'#146b86');text(1088,843,'B4 contract',19)
text(830,871,'95% Wilson CI; B4 upper limit 0.75%. n=507 (E1:509).',18)
s.append('</svg>');svg='\n'.join(s);(out/'evidence-navigation-figure.svg').write_text(svg);cairosvg.svg2pdf(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.pdf'));cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out/'evidence-navigation-figure.png'))
