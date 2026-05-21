"""Build a draft PowerPoint deck for the capstone demo.

The script writes a minimal Office Open XML presentation using only the Python
standard library. This keeps the submission artifacts reproducible without
requiring python-pptx.
"""

from __future__ import annotations

import html
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SCREENSHOTS = DOCS / "screenshots"

SLIDE_W = 13_333_333
SLIDE_H = 7_500_000
MARGIN_X = 620_000
TITLE_Y = 320_000
TITLE_H = 620_000
BODY_Y = 1_090_000
FOOTER_Y = 7_050_000


@dataclass(frozen=True)
class Slide:
    title: str
    bullets: list[str]
    subtitle: str = ""
    image: str = ""
    note: str = ""


SLIDES = [
    Slide(
        title="Call Center Analytics and Workforce Optimization",
        subtitle="Магістерський інженерний проєкт",
        bullets=[
            "City service contact center analytics",
            "SQL Server warehouse, Streamlit dashboard, forecasting, Erlang C, OR-Tools scheduling",
            "Public NYC 311 demand data plus documented synthetic operational metadata",
        ],
        note="Denys Vartsab | Master of Science in Data Science | 2026",
    ),
    Slide(
        title="Проблема",
        bullets=[
            "Попит у contact center змінюється за часом доби, днем тижня, сезоном і категорією звернення.",
            "Недостатній staffing знижує service level і збільшує abandonment.",
            "Надмірний staffing створює зайві labor costs.",
            "Потрібне interval-level planning, а не тільки історичний dashboard.",
        ],
    ),
    Slide(
        title="Мета продукту",
        bullets=[
            "Побудувати end-to-end analytical product для workforce planning.",
            "Перетворити public-service demand data на forecast, staffing requirements і schedule.",
            "Зробити pipeline прозорим: data, SQL, model comparison, Erlang C, optimizer, dashboard.",
            "Показати не black-box WFM, а відтворювану engineering implementation.",
        ],
    ),
    Slide(
        title="Дані та synthetic enrichment",
        bullets=[
            "NYC 311 Service Requests, 2023-01-01 to 2025-12-31.",
            "10,336,480 source records loaded into SQL Server.",
            "Public data provides real demand pattern, complaint type, borough, status and timestamps.",
            "Call-center fields such as AHT, hold time, ACW, abandonment, SLA and agent assignment are generated and documented.",
        ],
    ),
    Slide(
        title="Архітектура",
        bullets=[
            "NYC 311 public data -> SQL raw landing table.",
            "Raw table -> synthetic call-center warehouse.",
            "Warehouse -> SQL views -> Streamlit dashboard.",
            "Forecasting -> Erlang C staffing -> OR-Tools schedule optimizer.",
            "The product mirrors enterprise WFM flow, but keeps every step inspectable.",
        ],
    ),
    Slide(
        title="SQL Server warehouse",
        bullets=[
            "Fact_Calls: 10,336,480 simulated calls.",
            "Dim_Date: 1,096 dates; Dim_Time: 48 half-hour intervals.",
            "Dim_Queue: 217 queues; Dim_Agent: 160 synthetic agents.",
            "Dashboard-ready views validate offered, answered and abandoned calls.",
        ],
    ),
    Slide(
        title="Dashboard overview",
        bullets=[
            "Executive KPIs over full 2023-2025 history.",
            "Service category filtering and operational summary.",
            "SQL-backed analytics with CSV fallback for local demo mode.",
        ],
        image="01_executive_summary.png",
    ),
    Slide(
        title="Forecasting and model comparison",
        bullets=[
            "Forecast target: 30-minute call volume.",
            "Features: time cycles, calendar fields, weekend, US federal holidays, previous-week lag.",
            "Selected model: histogram gradient boosting.",
            "Holdout metrics: MAE 34.8872, RMSE 49.7414, MAPE 22.16%.",
        ],
        image="03_forecasting.png",
    ),
    Slide(
        title="Model-aware planning",
        bullets=[
            "Forecasting models are registered, not hardcoded.",
            "Current models: histogram gradient boosting, random forest, gradient boosting, ridge, Poisson.",
            "Dashboard can compare holdout predictions and future planning scenarios.",
            "Planning pipeline supports model selection: .\\scripts\\run_planning_pipeline.ps1 -Model random_forest",
        ],
    ),
    Slide(
        title="Staffing with Erlang C",
        bullets=[
            "Forecasted calls and AHT are converted into required agents.",
            "Target service level: 80% answered within 20 seconds.",
            "Max occupancy: 85%; shrinkage: 30%.",
            "Peak shrinkage-adjusted requirement for January 2026: 189 agents.",
        ],
        image="04_staffing_requirements.png",
    ),
    Slide(
        title="Schedule optimization",
        bullets=[
            "OR-Tools CP-SAT creates a legal future roster.",
            "160-agent planning pool, 8-hour shifts, 30-minute break.",
            "Rules: one shift per day, max 5 shifts per week, 11-hour minimum rest.",
            "Planning insight: 160 agents are legal but insufficient for full 24/7 coverage; estimate is 462.",
        ],
        image="05_scheduling_coverage.png",
    ),
    Slide(
        title="Validation",
        bullets=[
            "SQL row counts reconcile from raw table to fact table and dashboard views.",
            "Forecasting models are compared on a 90-day holdout period.",
            "Schedule validation shows zero daily-shift, weekly-limit and rest violations.",
            "Automated tests: 13 passed; public dashboard smoke test passed.",
        ],
        image="07_methodology_validation.png",
    ),
    Slide(
        title="Public portfolio deployment",
        bullets=[
            "Public URL: https://wfm.vartsab.com:8443.",
            "Docker Compose runs PostgreSQL, Streamlit and Caddy on a small VPS.",
            "Caddy provides HTTPS on port 8443 while the existing VPN keeps port 443.",
            "The deployed dashboard uses compact Postgres seed tables and a simple password gate.",
        ],
    ),
    Slide(
        title="Why this is an engineering project",
        bullets=[
            "The project does not claim to invent WFM as a new market category.",
            "Its novelty is the transparent, reproducible, open-data implementation of an enterprise WFM workflow.",
            "Academic value: every layer can be inspected, changed, evaluated and extended.",
            "Market relevance: commercial WFM suites solve the same real operational problem.",
        ],
    ),
    Slide(
        title="Limitations",
        bullets=[
            "311 records are public-service demand records, not guaranteed calls.",
            "Operational call-center fields are synthetic and must be presented as assumptions.",
            "Skill-based routing is not yet enforced in the schedule optimizer.",
            "The public VPS demo uses compact seed tables, not the full SQL Server warehouse.",
        ],
    ),
    Slide(
        title="Future work",
        bullets=[
            "Compare Erlang C with Erlang A and discrete-event simulation.",
            "Add intraday re-forecasting and scenario controls.",
            "Extend the optimizer to multi-skill scheduling and agent preferences.",
            "Optional productization: MLflow tracking, managed database, monitoring and backups.",
        ],
    ),
    Slide(
        title="Conclusion",
        bullets=[
            "The project demonstrates a complete path from public demand data to workforce planning decisions.",
            "Implemented layers: SQL warehouse, dashboard, forecasting, staffing and schedule optimization.",
            "The result is a working analytical product, public portfolio demo and defensible capstone engineering artifact.",
        ],
    ),
]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return 1024, 768
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def fit_image(path: Path, x: int, y: int, max_w: int, max_h: int) -> tuple[int, int, int, int]:
    px_w, px_h = png_size(path)
    scale = min(max_w / px_w, max_h / px_h)
    w = int(px_w * scale)
    h = int(px_h * scale)
    return x + (max_w - w) // 2, y + (max_h - h) // 2, w, h


def text_box(
    x: int,
    y: int,
    cx: int,
    cy: int,
    text: str,
    *,
    size: int = 2800,
    bold: bool = False,
    color: str = "1f2937",
    align: str = "l",
) -> str:
    bold_xml = "<a:b/>" if bold else ""
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="Text"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square"/>
        <a:lstStyle/>
        <a:p>
          <a:pPr algn="{align}"/>
          <a:r><a:rPr lang="uk-UA" sz="{size}" dirty="0">{bold_xml}<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Aptos"/><a:cs typeface="Aptos"/></a:rPr><a:t>{esc(text)}</a:t></a:r>
        </a:p>
      </p:txBody>
    </p:sp>
    """


def bullet_box(x: int, y: int, cx: int, cy: int, bullets: list[str], *, size: int = 1850) -> str:
    paragraphs = []
    for bullet in bullets:
        paragraphs.append(
            f"""
            <a:p>
              <a:pPr marL="285750" indent="-171450"><a:buChar char="•"/></a:pPr>
              <a:r><a:rPr lang="uk-UA" sz="{size}" dirty="0"><a:solidFill><a:srgbClr val="263244"/></a:solidFill><a:latin typeface="Aptos"/><a:cs typeface="Aptos"/></a:rPr><a:t>{esc(bullet)}</a:t></a:r>
            </a:p>
            """
        )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="3" name="Bullets"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>
      <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(paragraphs)}</p:txBody>
    </p:sp>
    """


def image_shape(rel_id: str, path: Path, shape_id: int) -> str:
    x, y, w, h = fit_image(
        path,
        x=6_950_000,
        y=1_420_000,
        max_w=5_760_000,
        max_h=4_850_000,
    )
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{shape_id}" name="{esc(path.name)}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
    """


def slide_xml(slide: Slide, slide_number: int, rel_id: str | None) -> str:
    has_image = bool(slide.image)
    body_w = 5_950_000 if has_image else 11_950_000
    body_size = 1680 if has_image else 1900
    parts = [
        text_box(MARGIN_X, TITLE_Y, 12_000_000, TITLE_H, slide.title, size=3100, bold=True, color="111827"),
    ]
    if slide.subtitle:
        parts.append(text_box(MARGIN_X, 940_000, 12_000_000, 380_000, slide.subtitle, size=1750, color="dc2626"))
        bullet_y = 1_470_000
    else:
        bullet_y = BODY_Y
    parts.append(bullet_box(MARGIN_X, bullet_y, body_w, 4_950_000, slide.bullets, size=body_size))
    if slide.image and rel_id:
        parts.append(image_shape(rel_id, SCREENSHOTS / slide.image, 10))
    if slide.note:
        parts.append(text_box(MARGIN_X, 6_520_000, 12_000_000, 350_000, slide.note, size=1450, color="6b7280"))
    parts.append(text_box(11_880_000, FOOTER_Y, 820_000, 240_000, str(slide_number), size=1150, color="9ca3af", align="r"))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="ffffff"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(parts)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def slide_rels_xml(rel_id: str | None, image_name: str | None) -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    ]
    if rel_id and image_name:
        rels.append(
            f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{image_name}"/>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def presentation_xml() -> str:
    slide_ids = []
    for idx in range(1, len(SLIDES) + 1):
        slide_ids.append(f'<p:sldId id="{255 + idx}" r:id="rId{idx + 1}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{''.join(slide_ids)}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def presentation_rels_xml() -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    for idx in range(1, len(SLIDES) + 1):
        rels.append(
            f'<Relationship Id="rId{idx + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{idx}.xml"/>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def content_types_xml(media_names: list[str]) -> str:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for idx in range(1, len(SLIDES) + 1):
        overrides.append(
            f'<Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  {''.join(overrides)}
</Types>"""


def root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def slide_master_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def slide_master_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""


def slide_layout_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def slide_layout_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Call Center WFM">
  <a:themeElements>
    <a:clrScheme name="WFM"><a:dk1><a:srgbClr val="111827"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="263244"/></a:dk2><a:lt2><a:srgbClr val="F3F4F6"/></a:lt2><a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="DC2626"/></a:accent2><a:accent3><a:srgbClr val="059669"/></a:accent3><a:accent4><a:srgbClr val="7C3AED"/></a:accent4><a:accent5><a:srgbClr val="EA580C"/></a:accent5><a:accent6><a:srgbClr val="0891B2"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Default"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Call Center Workforce Optimization Presentation</dc:title>
  <dc:creator>Denys Vartsab</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


def app_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Python Standard Library</Application>
  <Slides>{len(SLIDES)}</Slides>
</Properties>"""


def build_pptx(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    media_map: dict[str, str] = {}
    image_counter = 1
    for slide in SLIDES:
        if slide.image and slide.image not in media_map:
            media_map[slide.image] = f"image{image_counter}.png"
            image_counter += 1

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", content_types_xml(list(media_map.values())))
        pptx.writestr("_rels/.rels", root_rels_xml())
        pptx.writestr("docProps/core.xml", core_xml())
        pptx.writestr("docProps/app.xml", app_xml())
        pptx.writestr("ppt/presentation.xml", presentation_xml())
        pptx.writestr("ppt/_rels/presentation.xml.rels", presentation_rels_xml())
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        pptx.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels_xml())
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        pptx.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels_xml())
        pptx.writestr("ppt/theme/theme1.xml", theme_xml())

        for idx, slide in enumerate(SLIDES, start=1):
            rel_id = "rId2" if slide.image else None
            media_name = media_map.get(slide.image) if slide.image else None
            pptx.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(slide, idx, rel_id))
            pptx.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels_xml(rel_id, media_name))

        for source_name, media_name in media_map.items():
            pptx.write(SCREENSHOTS / source_name, f"ppt/media/{media_name}")


def main() -> None:
    output = DOCS / "final" / "Презентація_чернетка.pptx"
    build_pptx(output)
    print(f"Built {output}")


if __name__ == "__main__":
    main()
