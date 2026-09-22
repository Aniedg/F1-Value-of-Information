"""Convert the checked manuscript HTML into a portable authoring payload."""
from pathlib import Path
import json
from bs4 import BeautifulSoup,NavigableString
ROOT=Path(__file__).resolve().parents[1]
soup=BeautifulSoup((ROOT/'paper/manuscript-v2.html').read_text(),'html.parser')
def runs(node,bold=False,italic=False,subscript=False):
 if isinstance(node,NavigableString):return [{'text':str(node),'bold':bold,'italic':italic,'subscript':subscript}]
 out=[]
 for child in node.children:out+=runs(child,bold or node.name in ['strong','b'],italic or node.name in ['em','i'],subscript or node.name=='sub')
 return out
out=[]
for node in soup.children:
 if isinstance(node,NavigableString) or node.name in ['meta','style']:continue
 if node.name in ['h1','h2','h3']:out.append({'type':node.name,'text':node.get_text()})
 elif node.name=='p':
  img=node.find('img')
  if img:
   p=Path(img['src']);p=p if p.is_absolute() else ROOT/'paper'/p
   out.append({'type':'image','path':str(p),'caption':img.get('alt',''),'equation':'equation' in img.get('class',[])})
  else:out.append({'type':'p','runs':runs(node)})
 elif node.name=='table':out.append({'type':'table','rows':[[cell.get_text() for cell in row.find_all(['td','th'])] for row in node.find_all('tr')]})
(ROOT/'tmp/docx-payload.json').write_text(json.dumps(out))
