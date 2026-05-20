
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET

SRC = Path('pandoc-reference-default.docx')
DST = Path('论文模板-pandoc.docx')
TMP = Path('tmp_ref_docx')
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
ET.register_namespace('w', W)

if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir()
with zipfile.ZipFile(SRC) as z:
    z.extractall(TMP)

styles_path = TMP / 'word' / 'styles.xml'
root = ET.parse(styles_path).getroot()

def q(tag):
    return f'{{{W}}}{tag}'

def child(parent, tag):
    node = parent.find(f'w:{tag}', NS)
    if node is None:
        node = ET.SubElement(parent, q(tag))
    return node

def set_val(el, val):
    el.set(q('val'), str(val))

def set_style(style_id, east_font, ascii_font, size_half_pt, bold=False, center=False, line=None):
    style = None
    for s in root.findall('w:style', NS):
        if s.get(q('styleId')) == style_id:
            style = s
            break
    if style is None:
        return
    ppr = child(style, 'pPr')
    if center:
        jc = child(ppr, 'jc')
        set_val(jc, 'center')
    else:
        jc = ppr.find('w:jc', NS)
        if jc is not None:
            ppr.remove(jc)
    if line:
        spacing = child(ppr, 'spacing')
        spacing.set(q('line'), str(line))
        spacing.set(q('lineRule'), 'auto')
    rpr = child(style, 'rPr')
    fonts = child(rpr, 'rFonts')
    fonts.set(q('eastAsia'), east_font)
    fonts.set(q('ascii'), ascii_font)
    fonts.set(q('hAnsi'), ascii_font)
    sz = child(rpr, 'sz')
    set_val(sz, size_half_pt)
    szcs = child(rpr, 'szCs')
    set_val(szcs, size_half_pt)
    b = rpr.find('w:b', NS)
    if bold and b is None:
        ET.SubElement(rpr, q('b'))
    if not bold and b is not None:
        rpr.remove(b)

# Normal text: 宋体，小四，1.5倍行距；英文 Times New Roman
for sid in ['Normal', 'BodyText']:
    set_style(sid, '宋体', 'Times New Roman', 24, bold=False, center=False, line=360)

# 标题：一级黑体三号居中；二级黑体四号；三级黑体小四
set_style('Heading1', '黑体', 'Times New Roman', 32, bold=True, center=True, line=360)
set_style('Heading2', '黑体', 'Times New Roman', 28, bold=True, center=False, line=360)
set_style('Heading3', '黑体', 'Times New Roman', 24, bold=True, center=False, line=360)
set_style('TOCHeading', '黑体', 'Times New Roman', 32, bold=True, center=True, line=360)

ET.ElementTree(root).write(styles_path, encoding='utf-8', xml_declaration=True)

# Page setup: top/bottom 2cm, left/right 3cm, header/footer 1.5cm
for doc_name in ['document.xml']:
    doc_path = TMP / 'word' / doc_name
    tree = ET.parse(doc_path)
    doc_root = tree.getroot()
    body = doc_root.find('w:body', NS)
    sect = body.find('w:sectPr', NS)
    if sect is None:
        sect = ET.SubElement(body, q('sectPr'))
    pgmar = child(sect, 'pgMar')
    pgmar.set(q('top'), '1134')
    pgmar.set(q('bottom'), '1134')
    pgmar.set(q('left'), '1701')
    pgmar.set(q('right'), '1701')
    pgmar.set(q('header'), '851')
    pgmar.set(q('footer'), '851')
    tree.write(doc_path, encoding='utf-8', xml_declaration=True)

if DST.exists():
    DST.unlink()
with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as z:
    for file in TMP.rglob('*'):
        if file.is_file():
            z.write(file, file.relative_to(TMP).as_posix())
shutil.rmtree(TMP)
print(DST)
