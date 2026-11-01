#!/usr/bin/env python3
"""Convert the upstream chinese-poetry repository data into downloadable PDFs."""
import os, re, json, html, zipfile, sqlite3
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

SOURCE = Path(os.environ.get("SOURCE_DIR", "source"))
OUT = Path("dist/pdfs")
OUT.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
base = getSampleStyleSheet()
title_style = ParagraphStyle("CNTitle", parent=base["Title"], fontName="STSong-Light",
    fontSize=17, leading=22, alignment=1, spaceAfter=8)
heading = ParagraphStyle("CNHeading", parent=base["Heading2"], fontName="STSong-Light",
    fontSize=10, leading=14, spaceBefore=7, spaceAfter=3, keepWithNext=True)
body = ParagraphStyle("CNBody", parent=base["BodyText"], fontName="STSong-Light",
    fontSize=8, leading=11, wordWrap="CJK", spaceAfter=2)
small = ParagraphStyle("CNSmall", parent=body, fontSize=6.5, leading=8)

def safe_name(value):
    value = value.replace("/", "__").replace("\\", "__")
    value = re.sub(r'[<>:"|?*]', "_", value)
    return value[:180]

def flatten(value, prefix=""):
    rows = []
    if isinstance(value, dict):
        for key, item in value.items():
            label = f"{prefix}{key}"
            if isinstance(item, (dict, list)):
                rows.extend(flatten(item, label + "/"))
            else:
                rows.append((label, str(item) if item is not None else ""))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            label = f"{prefix}[{index}]"
            if isinstance(item, (dict, list)):
                rows.extend(flatten(item, label + "/"))
            else:
                rows.append((label, str(item) if item is not None else ""))
    else:
        rows.append((prefix.rstrip("/"), str(value)))
    return rows

def record_flow(item, index):
    flow = []
    if isinstance(item, dict):
        title = item.get("title") or item.get("name") or item.get("chapter") or f"记录 {index}"
        flow.append(Paragraph(escape(str(title)), heading))
        author = item.get("author")
        if author:
            flow.append(Paragraph("作者：" + escape(str(author)), small))
        consumed = {"title", "name", "chapter", "author"}
        for key in ("paragraphs", "content", "text"):
            if key in item:
                consumed.add(key)
                value = item[key]
                if isinstance(value, list):
                    for line in value:
                        if isinstance(line, (dict, list)):
                            for k, v in flatten(line):
                                flow.append(Paragraph(escape(k) + "：" + escape(v), body))
                        else:
                            flow.append(Paragraph(escape(str(line)), body))
                elif isinstance(value, (dict, list)):
                    for k, v in flatten(value):
                        flow.append(Paragraph(escape(k) + "：" + escape(v), body))
                else:
                    flow.append(Paragraph(escape(str(value)), body))
        rest = {k: v for k, v in item.items() if k not in consumed}
        for key, value in flatten(rest):
            flow.append(Paragraph(escape(key) + "：" + escape(value), small))
    else:
        flow.append(Paragraph(escape(str(item)), body))
    flow.append(Spacer(1, 3))
    return flow

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawString(15*mm, 9*mm, "chinese-poetry 数据转换 PDF")
    canvas.drawRightString(A4[0]-15*mm, 9*mm, f"第 {doc.page} 页")
    canvas.restoreState()

def write_pdf(target, title, source_label, data):
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=15*mm,
        rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm, title=title)
    flow = [Paragraph(escape(title), title_style),
            Paragraph(escape(source_label), small), Spacer(1, 5)]
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            flow.extend(record_flow(item, i))
    else:
        flow.extend(record_flow(data, 1))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)

catalog = []
json_files = sorted(SOURCE.rglob("*.json"))
for number, path in enumerate(json_files, 1):
    relative = path.relative_to(SOURCE)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        data = {"原始文本": path.read_text(encoding="utf-8", errors="replace")}
    target = OUT / relative.parent / (safe_name(path.name) + ".pdf")
    write_pdf(target, path.name, str(relative), data)
    catalog.append((str(relative), str(target.relative_to(OUT))))
    if number % 100 == 0:
        print(f"JSON converted: {number}/{len(json_files)}", flush=True)

# Convert readable project text/source files too.
text_ext = {".md", ".txt", ".py", ".js", ".yml", ".yaml", ".log", ".html", ".css"}
for path in sorted(SOURCE.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in text_ext:
        continue
    relative = path.relative_to(SOURCE)
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = content.splitlines()
    data = {"文件内容": lines}
    target = OUT / relative.parent / (safe_name(path.name) + ".pdf")
    write_pdf(target, path.name, str(relative), data)
    catalog.append((str(relative), str(target.relative_to(OUT))))

# Export SQLite database tables to PDF, where present.
for path in sorted(SOURCE.rglob("*.db")):
    relative = path.relative_to(SOURCE)
    target = OUT / relative.parent / (safe_name(path.name) + ".pdf")
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    flow_data = []
    for table in tables:
        safe_table = table.replace('"', '""')
        columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{safe_table}")')]
        flow_data.append({"title": f"数据表：{table}", "columns": columns})
        cursor = conn.execute(f'SELECT * FROM "{safe_table}"')
        for row in cursor:
            flow_data.append({"record": [str(v) if v is not None else "" for v in row]})
    conn.close()
    write_pdf(target, path.name, str(relative), flow_data)
    catalog.append((str(relative), str(target.relative_to(OUT))))

# Put repository images in a separate PDF.
image_files = [p for p in SOURCE.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
if image_files:
    from reportlab.platypus import Image
    image_target = OUT / "项目图片资料.pdf"
    doc = SimpleDocTemplate(str(image_target), pagesize=A4, leftMargin=15*mm,
        rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm, title="项目图片资料")
    flow = [Paragraph("项目图片资料", title_style)]
    for p in image_files:
        flow.append(Paragraph(escape(str(p.relative_to(SOURCE))), heading))
        try:
            from PIL import Image as PILImage
            im = PILImage.open(p)
            w, h = im.size
            maxw, maxh = A4[0]-35*mm, A4[1]-55*mm
            scale = min(maxw/w, maxh/h, 1)
            flow.append(Image(str(p), width=w*scale, height=h*scale))
            flow.append(PageBreak())
        except Exception as exc:
            flow.append(Paragraph("无法嵌入此图片：" + escape(str(exc)), body))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    catalog.append(("图片文件集合", "项目图片资料.pdf"))

catalog_path = Path("dist/chinese_poetry_pdf_catalog.txt")
catalog_path.write_text(
    "chinese-poetry PDF 完整目录\n"
    f"PDF 文件数：{len(catalog)}\n\n" +
    "\n".join(f"{i}. {src} -> {pdf}" for i, (src, pdf) in enumerate(catalog, 1)),
    encoding="utf-8"
)
archive = Path("dist/chinese-poetry-pdf-library.zip")
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as z:
    for path in sorted(OUT.rglob("*.pdf")):
        z.write(path, path.relative_to(OUT))
    z.write(catalog_path, catalog_path.name)
print(f"Created {len(catalog)} PDFs; archive size {archive.stat().st_size} bytes", flush=True)
