"""Build a Word-compatible explanatory note draft from the Markdown report.

This script intentionally uses only the Python standard library so the report can
be generated on a fresh machine without installing python-docx.
"""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"

EMU_PER_INCH = 914400
MAX_IMAGE_WIDTH_EMU = int(6.35 * EMU_PER_INCH)


@dataclass
class ImageRef:
    rel_id: str
    source: Path
    media_name: str
    width_emu: int
    height_emu: int


def escape(text: str) -> str:
    return html.escape(text, quote=False)


def strip_inline_markup(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return 1024, 768
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def image_dimensions(path: Path) -> tuple[int, int]:
    pixel_width, pixel_height = png_size(path)
    width = MAX_IMAGE_WIDTH_EMU
    height = int(width * pixel_height / pixel_width)
    return width, height


def run_xml(text: str, *, bold: bool = False, italic: bool = False, font: str = "Times New Roman") -> str:
    props = [
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>',
        '<w:sz w:val="24"/>',
        '<w:szCs w:val="24"/>',
    ]
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    return (
        "<w:r>"
        f"<w:rPr>{''.join(props)}</w:rPr>"
        f'<w:t xml:space="preserve">{escape(text)}</w:t>'
        "</w:r>"
    )


def paragraph_xml(
    text: str = "",
    *,
    style: str | None = None,
    bold: bool = False,
    italic: bool = False,
    center: bool = False,
    bullet: bool = False,
    numbered: bool = False,
    code: bool = False,
) -> str:
    text = strip_inline_markup(text)
    ppr: list[str] = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if center:
        ppr.append('<w:jc w:val="center"/>')
    if bullet or numbered:
        ppr.append('<w:ind w:left="720" w:hanging="360"/>')
    elif style not in {"Title", "Heading1", "Heading2", "Heading3"} and text:
        ppr.append('<w:ind w:firstLine="709"/>')
    if style not in {"Title", "Heading1", "Heading2", "Heading3"}:
        ppr.append('<w:spacing w:line="360" w:lineRule="auto" w:after="120"/>')
    else:
        ppr.append('<w:spacing w:before="240" w:after="160"/>')
    prefix = ""
    if bullet:
        prefix = "• "
    if numbered:
        prefix = ""
    font = "Courier New" if code else "Times New Roman"
    return (
        "<w:p>"
        f"<w:pPr>{''.join(ppr)}</w:pPr>"
        f"{run_xml(prefix + text, bold=bold, italic=italic, font=font)}"
        "</w:p>"
    )


def heading_xml(text: str, level: int) -> str:
    style = "Heading1" if level == 1 else "Heading2" if level == 2 else "Heading3"
    return paragraph_xml(strip_inline_markup(text), style=style, bold=True)


def table_xml(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    grid = "".join('<w:gridCol w:w="2400"/>' for _ in range(col_count))
    body_rows: list[str] = []
    for row_index, row in enumerate(rows):
        cells: list[str] = []
        padded = row + [""] * (col_count - len(row))
        for cell in padded:
            cells.append(
                "<w:tc>"
                '<w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
                f"{paragraph_xml(strip_inline_markup(cell), bold=row_index == 0)}"
                "</w:tc>"
            )
        body_rows.append(f"<w:tr>{''.join(cells)}</w:tr>")
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        "</w:tblBorders>"
    )
    return (
        "<w:tbl>"
        f"<w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/>{borders}</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{''.join(body_rows)}"
        "</w:tbl>"
    )


def image_xml(image: ImageRef, caption: str) -> str:
    return (
        "<w:p>"
        '<w:pPr><w:jc w:val="center"/><w:spacing w:before="160" w:after="80"/></w:pPr>'
        "<w:r><w:drawing>"
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{image.width_emu}" cy="{image.height_emu}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:docPr id="1" name="Dashboard screenshot"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        "<a:graphic>"
        f'<a:graphicData uri="{PIC_NS}">'
        "<pic:pic>"
        '<pic:nvPicPr><pic:cNvPr id="0" name="screenshot"/><pic:cNvPicPr/></pic:nvPicPr>'
        "<pic:blipFill>"
        f'<a:blip r:embed="{image.rel_id}"/>'
        '<a:stretch><a:fillRect/></a:stretch>'
        "</pic:blipFill>"
        "<pic:spPr>"
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{image.width_emu}" cy="{image.height_emu}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        "</pic:spPr>"
        "</pic:pic>"
        "</a:graphicData>"
        "</a:graphic>"
        "</wp:inline>"
        "</w:drawing></w:r>"
        "</w:p>"
        f"{paragraph_xml(caption, italic=True, center=True)}"
    )


def parse_markdown(markdown_path: Path) -> tuple[list[str], list[ImageRef]]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    blocks: list[str] = []
    images: list[ImageRef] = []
    table_buffer: list[list[str]] = []
    in_code = False
    image_index = 1

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            blocks.append(table_xml(table_buffer))
            table_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_table()
            in_code = not in_code
            continue
        if in_code:
            blocks.append(paragraph_xml(stripped, code=True))
            continue
        if not stripped:
            flush_table()
            blocks.append(paragraph_xml(""))
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            table_buffer.append(cells)
            continue
        flush_table()
        image_match = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
        if image_match:
            caption = image_match.group(1)
            source = (markdown_path.parent / image_match.group(2)).resolve()
            width, height = image_dimensions(source)
            suffix = source.suffix.lower() or ".png"
            media_name = f"image{image_index}{suffix}"
            image = ImageRef(
                rel_id=f"rId{image_index}",
                source=source,
                media_name=media_name,
                width_emu=width,
                height_emu=height,
            )
            images.append(image)
            blocks.append(image_xml(image, caption))
            image_index += 1
            continue
        if stripped.startswith("# "):
            blocks.append(heading_xml(stripped[2:], 1))
            continue
        if stripped.startswith("## "):
            blocks.append(heading_xml(stripped[3:], 2))
            continue
        if stripped.startswith("### "):
            blocks.append(heading_xml(stripped[4:], 3))
            continue
        if stripped.startswith("- "):
            blocks.append(paragraph_xml(stripped[2:], bullet=True))
            continue
        if re.match(r"^\d+\.\s+", stripped):
            blocks.append(paragraph_xml(stripped, numbered=True))
            continue
        blocks.append(paragraph_xml(stripped))
    flush_table()
    return blocks, images


def content_types(images: list[ImageRef]) -> str:
    image_defaults = {"png": '<Default Extension="png" ContentType="image/png"/>'}
    for image in images:
        ext = image.media_name.rsplit(".", 1)[-1]
        if ext == "jpg" or ext == "jpeg":
            image_defaults[ext] = f'<Default Extension="{ext}" ContentType="image/jpeg"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{''.join(image_defaults.values())}"
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )


def package_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def document_rels(images: list[ImageRef]) -> str:
    rels = [
        f'<Relationship Id="{image.rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{image.media_name}"/>'
        for image in images
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}"
        "</Relationships>"
    )


def styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W_NS}">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/>'
        '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Title">'
        '<w:name w:val="Title"/>'
        '<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="32"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Heading1">'
        '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="32"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Heading2">'
        '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="28"/></w:rPr>'
        "</w:style>"
        '<w:style w:type="paragraph" w:styleId="Heading3">'
        '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="26"/></w:rPr>'
        "</w:style>"
        "</w:styles>"
    )


def document_xml(blocks: list[str]) -> str:
    section = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}">'
        "<w:body>"
        f"{''.join(blocks)}"
        f"{section}"
        "</w:body>"
        "</w:document>"
    )


def core_props() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Call Center Workforce Optimization Explanatory Note</dc:title>"
        "<dc:creator>Denys Vartsab</dc:creator>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def app_props() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Python Standard Library</Application>"
        "</Properties>"
    )


def build_docx(markdown_path: Path, output_path: Path) -> None:
    blocks, images = parse_markdown(markdown_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types(images))
        docx.writestr("_rels/.rels", package_rels())
        docx.writestr("word/_rels/document.xml.rels", document_rels(images))
        docx.writestr("word/document.xml", document_xml(blocks))
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("docProps/core.xml", core_props())
        docx.writestr("docProps/app.xml", app_props())
        for image in images:
            docx.write(image.source, f"word/media/{image.media_name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="docs/explanatory_note_draft.md")
    parser.add_argument("--output", default="docs/final/Пояснювальна_записка_чернетка.docx")
    args = parser.parse_args()
    build_docx(Path(args.input), Path(args.output))
    print(f"Built {args.output}")


if __name__ == "__main__":
    main()
