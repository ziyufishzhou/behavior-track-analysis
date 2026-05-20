from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "毕业设计论文初稿_格式修正版.docx"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix if prefix != "rel" else "", uri)


def qn(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def set_font(run_props: ET.Element, east_asia: str, ascii_font: str, size_half_points: str) -> None:
    fonts = run_props.find(qn("w", "rFonts"))
    if fonts is None:
        fonts = ET.SubElement(run_props, qn("w", "rFonts"))
    fonts.set(qn("w", "eastAsia"), east_asia)
    fonts.set(qn("w", "ascii"), ascii_font)
    fonts.set(qn("w", "hAnsi"), ascii_font)

    size = run_props.find(qn("w", "sz"))
    if size is None:
        size = ET.SubElement(run_props, qn("w", "sz"))
    size.set(qn("w", "val"), size_half_points)

    size_cs = run_props.find(qn("w", "szCs"))
    if size_cs is None:
        size_cs = ET.SubElement(run_props, qn("w", "szCs"))
    size_cs.set(qn("w", "val"), size_half_points)


def paragraph(text: str, align: str, east_asia: str, ascii_font: str, size_half_points: str) -> ET.Element:
    p = ET.Element(qn("w", "p"))
    p_pr = ET.SubElement(p, qn("w", "pPr"))
    jc = ET.SubElement(p_pr, qn("w", "jc"))
    jc.set(qn("w", "val"), align)
    r = ET.SubElement(p, qn("w", "r"))
    r_pr = ET.SubElement(r, qn("w", "rPr"))
    set_font(r_pr, east_asia, ascii_font, size_half_points)
    t = ET.SubElement(r, qn("w", "t"))
    t.text = text
    return p


def page_number_footer() -> ET.Element:
    p = ET.Element(qn("w", "p"))
    p_pr = ET.SubElement(p, qn("w", "pPr"))
    jc = ET.SubElement(p_pr, qn("w", "jc"))
    jc.set(qn("w", "val"), "right")

    for field_type, text in [
        ("begin", None),
        (None, "PAGE"),
        ("separate", None),
        ("end", None),
    ]:
        r = ET.SubElement(p, qn("w", "r"))
        r_pr = ET.SubElement(r, qn("w", "rPr"))
        set_font(r_pr, "楷体", "Times New Roman", "21")
        if field_type:
            fld = ET.SubElement(r, qn("w", "fldChar"))
            fld.set(qn("w", "fldCharType"), field_type)
        else:
            instr = ET.SubElement(r, qn("w", "instrText"))
            instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            instr.text = f" {text} "

        if field_type == "separate":
            display = ET.SubElement(p, qn("w", "r"))
            display_pr = ET.SubElement(display, qn("w", "rPr"))
            set_font(display_pr, "楷体", "Times New Roman", "21")
            t = ET.SubElement(display, qn("w", "t"))
            t.text = "1"

    return p


def ensure_relationship(rels_root: ET.Element, rid: str, rel_type: str, target: str) -> None:
    for rel in rels_root.findall(qn("rel", "Relationship")):
        if rel.get("Id") == rid:
            rel.set("Type", rel_type)
            rel.set("Target", target)
            return
    rel = ET.SubElement(rels_root, qn("rel", "Relationship"))
    rel.set("Id", rid)
    rel.set("Type", rel_type)
    rel.set("Target", target)


def ensure_content_type(types_root: ET.Element, part_name: str, content_type: str) -> None:
    override_tag = "{http://schemas.openxmlformats.org/package/2006/content-types}Override"
    for override in types_root.findall(override_tag):
        if override.get("PartName") == part_name:
            override.set("ContentType", content_type)
            return
    override = ET.SubElement(types_root, override_tag)
    override.set("PartName", part_name)
    override.set("ContentType", content_type)


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        with zipfile.ZipFile(DOCX, "r") as zf:
            zf.extractall(tmp)

        header = ET.Element(qn("w", "hdr"))
        header.append(paragraph("吉林大学 计算机科学与技术学院 毕业论文", "center", "楷体", "Times New Roman", "24"))
        ET.ElementTree(header).write(tmp / "word" / "header1.xml", encoding="utf-8", xml_declaration=True)

        footer = ET.Element(qn("w", "ftr"))
        footer.append(page_number_footer())
        ET.ElementTree(footer).write(tmp / "word" / "footer1.xml", encoding="utf-8", xml_declaration=True)

        rels_path = tmp / "word" / "_rels" / "document.xml.rels"
        rels_tree = ET.parse(rels_path)
        rels_root = rels_tree.getroot()
        ensure_relationship(
            rels_root,
            "rIdThesisHeader",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
            "header1.xml",
        )
        ensure_relationship(
            rels_root,
            "rIdThesisFooter",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
            "footer1.xml",
        )
        rels_tree.write(rels_path, encoding="utf-8", xml_declaration=True)

        content_types_path = tmp / "[Content_Types].xml"
        types_tree = ET.parse(content_types_path)
        types_root = types_tree.getroot()
        ensure_content_type(
            types_root,
            "/word/header1.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
        )
        ensure_content_type(
            types_root,
            "/word/footer1.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
        )
        types_tree.write(content_types_path, encoding="utf-8", xml_declaration=True)

        doc_path = tmp / "word" / "document.xml"
        doc_tree = ET.parse(doc_path)
        body = doc_tree.getroot().find(qn("w", "body"))
        if body is None:
            raise RuntimeError("word/document.xml has no body")

        sect_pr = body.find(qn("w", "sectPr"))
        if sect_pr is None:
            sect_pr = ET.SubElement(body, qn("w", "sectPr"))

        for old in list(sect_pr):
            if old.tag in {qn("w", "headerReference"), qn("w", "footerReference")}:
                sect_pr.remove(old)

        header_ref = ET.Element(qn("w", "headerReference"))
        header_ref.set(qn("w", "type"), "default")
        header_ref.set(qn("r", "id"), "rIdThesisHeader")
        sect_pr.insert(0, header_ref)

        footer_ref = ET.Element(qn("w", "footerReference"))
        footer_ref.set(qn("w", "type"), "default")
        footer_ref.set(qn("r", "id"), "rIdThesisFooter")
        sect_pr.insert(1, footer_ref)

        pg_mar = sect_pr.find(qn("w", "pgMar"))
        if pg_mar is None:
            pg_mar = ET.SubElement(sect_pr, qn("w", "pgMar"))
        pg_mar.set(qn("w", "top"), "1134")
        pg_mar.set(qn("w", "bottom"), "1134")
        pg_mar.set(qn("w", "left"), "1701")
        pg_mar.set(qn("w", "right"), "1701")
        pg_mar.set(qn("w", "header"), "851")
        pg_mar.set(qn("w", "footer"), "851")

        doc_tree.write(doc_path, encoding="utf-8", xml_declaration=True)

        fixed = DOCX.with_name("毕业设计论文初稿_学院格式版.docx")
        for i in range(0, 20):
            candidate = fixed if i == 0 else DOCX.with_name(f"毕业设计论文初稿_学院格式版_更新版{i}.docx")
            try:
                if candidate.exists():
                    candidate.unlink()
                fixed = candidate
                break
            except PermissionError:
                continue
        else:
            raise PermissionError("所有候选输出文件都被占用，请关闭 Word/WPS 后重试。")
        with zipfile.ZipFile(fixed, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in tmp.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmp).as_posix())

    print(fixed)


if __name__ == "__main__":
    main()
