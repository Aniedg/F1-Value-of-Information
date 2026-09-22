"""Typeset manuscript Markdown into an embedded-font, single-column PDF."""
from pathlib import Path
import re,os,html
import markdown
from bs4 import BeautifulSoup,NavigableString
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,KeepTogether,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
import matplotlib.font_manager as fm
FONT=Path(fm.findfont('DejaVu Serif')).parent
for name,file in [('Article','DejaVuSerif.ttf'),('ArticleBold','DejaVuSerif-Bold.ttf'),('ArticleItalic','DejaVuSerif-Italic.ttf'),('ArticleBoldItalic','DejaVuSerif-BoldItalic.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Article',normal='Article',bold='ArticleBold',italic='ArticleItalic',boldItalic='ArticleBoldItalic')
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage


def main():
    out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    tmp=ROOT/'tmp/pdfs';tmp.mkdir(parents=True,exist_ok=True)
    text=(ROOT/'paper/manuscript.md').read_text()
    equation_count=0
    def equation(match):
        nonlocal equation_count
        equation_count+=1
        fig=plt.figure(figsize=(7,.5));fig.text(.5,.5,'$'+match.group(1)+'$',fontsize=13,ha='center',va='center')
        path=tmp/f'equation-{equation_count}.png';fig.savefig(path,dpi=240,bbox_inches='tight',pad_inches=.06);plt.close(fig)
        return f'<p><img src="{path}" alt="Equation {equation_count}" class="equation"/></p>'
    text=re.sub(r'^\$\$(.*?)\$\$$',equation,text,flags=re.M)
    rendered=markdown.markdown(text,extensions=['tables'])
    # HTML is a convenience preview; PDF remains the publication artifact.
    (ROOT/'paper/manuscript.html').write_text('<!doctype html><meta charset="utf-8"><style>body{max-width:850px;margin:50px auto;font:17px/1.65 Georgia;color:#222}img{max-width:100%}table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ccc}h1,h2,h3{line-height:1.25}</style>'+rendered)
    soup=BeautifulSoup(rendered,'html.parser')
    styles=getSampleStyleSheet()
    body=ParagraphStyle('ArticleBody',fontName='Article',fontSize=10.0,leading=13.6,alignment=TA_JUSTIFY,spaceAfter=6,allowWidows=0,allowOrphans=0)
    title=ParagraphStyle('ArticleTitle',parent=body,fontName='ArticleBold',fontSize=21,leading=26,alignment=TA_CENTER,spaceAfter=10,keepWithNext=True)
    subtitle=ParagraphStyle('Subtitle',parent=body,fontSize=12.1,leading=16,alignment=TA_CENTER,spaceAfter=10,keepWithNext=True)
    h2=ParagraphStyle('Section',parent=body,fontName='ArticleBold',fontSize=12.5,leading=17,spaceBefore=12,spaceAfter=7,keepWithNext=True)
    h3=ParagraphStyle('Subsection',parent=body,fontName='ArticleBold',fontSize=10.6,leading=15,spaceBefore=8,spaceAfter=5,keepWithNext=True)
    caption=ParagraphStyle('Caption',parent=body,fontSize=8.5,leading=11.5,alignment=0,spaceAfter=10)
    cell=ParagraphStyle('Cell',parent=body,fontSize=8.4,leading=11,alignment=0,spaceAfter=0)
    reference=ParagraphStyle('Reference',parent=body,fontSize=8.8,leading=11.7,alignment=0,spaceAfter=7)
    width=A4[0]-104
    def inline(node):
        if isinstance(node,NavigableString):return html.escape(str(node))
        inner=''.join(inline(x) for x in node.children)
        if node.name in ['strong','b']:return '<b>'+inner+'</b>'
        if node.name in ['em','i']:return '<i>'+inner+'</i>'
        if node.name=='code':return '<font name="Mono" size="8.5">'+inner+'</font>'
        if node.name=='a':return '<link href="'+html.escape(node.get('href',''),quote=True)+'" color="#225e75">'+inner+'</link>'
        if node.name=='br':return '<br/>'
        return inner
    story=[];first_h2=True;in_refs=False;table_count=0
    table_captions=['Parameter grid for the protocol-locked synthetic study.','Equal-state mean costs and regret on the 2,187-state grid.','Robust forecasting on the three-event test group.','Adaptive and recalibrated static intervals on the final three-event group.']
    for node in soup.children:
        if isinstance(node,NavigableString):continue
        if node.name=='h1':story.append(Paragraph(inline(node),title))
        elif node.name=='h2':
            if first_h2:story.append(Paragraph(inline(node),subtitle));first_h2=False
            else:
                in_refs=node.get_text()=='References'
                if in_refs:story.append(PageBreak())
                story.append(Paragraph(inline(node),h2))
        elif node.name=='h3':story.append(Paragraph(inline(node),h3))
        elif node.name=='p':
            img=node.find('img')
            if img:
                p=Path(img['src']);p=p if p.is_absolute() else ROOT/'paper'/p
                with PILImage.open(p) as im:w,h=im.size
                iseq='equation' in img.get('class',[])
                scaled=min(width,w*72/240) if iseq else width
                artifact=Image(str(p),width=scaled,height=scaled*h/w)
                if iseq:story.append(KeepTogether([Spacer(1,3),artifact,Spacer(1,7)]))
                else:story.append(KeepTogether([Spacer(1,5),artifact,Spacer(1,5),Paragraph(html.escape(img.get('alt','')),caption)]))
            else:story.append(Paragraph(inline(node),reference if in_refs else body))
        elif node.name=='table':
            table_count+=1;rows=[]
            for tr in node.find_all('tr'):
                cells=[]
                for td in tr.find_all(['th','td']):
                    value=inline(td)
                    if td.name=='th':value='<b>'+value+'</b>'
                    cells.append(Paragraph(value,cell))
                rows.append(cells)
            cols=len(rows[0])
            widths=([width*.40,width*.60] if cols==2 else ([width*.46,width*.27,width*.27] if cols==3 else [width*.24]+[width*.76/(cols-1)]*(cols-1)))
            t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf1f3')),('LINEABOVE',(0,0),(-1,0),.7,colors.HexColor('#65717b')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#65717b')),('LINEBELOW',(0,-1),(-1,-1),.7,colors.HexColor('#65717b')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            cap=f'Table {table_count}. '+table_captions[table_count-1]
            story.append(KeepTogether([Paragraph(cap,caption),t,Spacer(1,10)]))
    def page(canvas,doc):
        canvas.saveState();canvas.setFont('Article',8);canvas.setFillColor(colors.HexColor('#52616b'))
        if doc.page>1:canvas.drawString(52,A4[1]-31,'The Value of Information in Formula One Pit Strategy')
        canvas.drawString(52,27,'Research manuscript | Version 1.0 | 22 September 2026')
        canvas.drawRightString(A4[0]-52,27,str(doc.page));canvas.restoreState()
    output=out/'value-of-information-f1-paper.pdf'
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=48,bottomMargin=46,title='The Value of Information in Formula One Pit Strategy',author='',subject='Bayesian stopping with uncertain baseline pace and replacement tyres')
    doc.build(story,onFirstPage=page,onLaterPages=page)
    print(output)

if __name__=='__main__':main()
