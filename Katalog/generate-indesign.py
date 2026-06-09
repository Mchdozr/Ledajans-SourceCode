#!/usr/bin/env python3
"""HTML katalog → PNG render → InDesign IDML + PDF + JSX import paketi."""
import json
import re
import uuid
import xml.sax.saxutils as xml_escape
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "katalog-data.json").read_text(encoding="utf-8"))
OUT = ROOT / "indesign"
LINKS = OUT / "Links"
PAGES_DIR = ROOT / "pages"

W = 595.276
H = 841.89
BLEED = 8.504  # 3mm


def esc_attr(s: str) -> str:
    return xml_escape.escape(s, {'"': "&quot;", "'": "&apos;"})


def uid() -> str:
    return uuid.uuid4().hex[:6]


def page_files() -> list[Path]:
    files = [
        PAGES_DIR / "01-kapak.html",
        PAGES_DIR / "02-tanitim.html",
        PAGES_DIR / "03-icindekiler.html",
    ]
    for p in DATA["products"]:
        files.append(PAGES_DIR / p["file"])
    files += [
        PAGES_DIR / "14-referanslar.html",
        PAGES_DIR / "15-arka-kapak.html",
    ]
    return files


def render_pages() -> list[Path]:
    LINKS.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 794, "height": 1123},
            device_scale_factor=3,
        )
        page = ctx.new_page()
        for i, html in enumerate(page_files(), 1):
            page.goto(html.as_uri(), wait_until="networkidle")
            page.wait_for_timeout(800)
            out = LINKS / f"page-{i:02d}.png"
            page.locator(".page").screenshot(path=str(out))
            paths.append(out)
            print(f"  render {out.name}")
        browser.close()
    return paths


def render_pdf() -> Path:
    pdf_path = OUT / "LEDAJANS-Katalog-2026-Baski.pdf"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        index = (ROOT / "index.html").as_uri()
        page.goto(index, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()
    print(f"  pdf {pdf_path.name}")
    return pdf_path


def preferences_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <DocumentPreference PageWidth="{W}" PageHeight="{H}"
    PagesPerDocument="15" FacingPages="false"
    DocumentBleedTopOffset="{BLEED}" DocumentBleedBottomOffset="{BLEED}"
    DocumentBleedInsideOrLeftOffset="{BLEED}" DocumentBleedOutsideOrRightOffset="{BLEED}"
    DocumentBleedUniformSize="true"/>
</idPkg:Preferences>"""


def graphic_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Graphic xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" Name="Black"/>
  <Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" Name="Paper"/>
</idPkg:Graphic>"""


def fonts_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <FontFamily Self="di6" Name="Minion Pro">
    <Font Self="di6FontnMinion Pro Regular" FontFamily="Minion Pro" Name="Minion Pro Regular"
      PostScriptName="MinionPro-Regular" Status="Installed"/>
  </FontFamily>
</idPkg:Fonts>"""


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <RootParagraphStyleGroup Self="Pandora">
    <ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle"/>
  </RootParagraphStyleGroup>
  <RootCharacterStyleGroup Self="Pandora">
    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>
  </RootCharacterStyleGroup>
</idPkg:Styles>"""


def spread_xml(page_name: str, img_name: str, spread_id: str, page_id: str, rect_id: str, img_id: str, link_id: str) -> str:
    safe_name = esc_attr(page_name)
    bx = W + BLEED * 2
    by = H + BLEED * 2
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <Spread Self="{spread_id}" PageCount="1" ShowMasterItems="true" PageTransitionType="None" FlattenerOverride="Default" BindingLocation="0">
    <FlattenerPreference LineArtAndTextResolution="300" GradientAndMeshResolution="150"/>
    <Page Self="{page_id}" Name="{safe_name}" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName"
      GeometricBounds="0 0 {H} {W}" ItemTransform="1 0 0 1 0 0"
      MasterPageTransform="1 0 0 1 0 0" AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopLeft">
      <Properties>
        <PageColor type="enumeration">UseMasterColor</PageColor>
      </Properties>
      <MarginPreference ColumnCount="1" ColumnGutter="12" Top="0" Bottom="0" Left="0" Right="0"/>
    </Page>
    <Rectangle Self="{rect_id}" ContentType="GraphicType" StoryTitle="$ID/"
      ItemTransform="1 0 0 1 {-BLEED} {-BLEED}" Visible="true" Name="$ID/">
      <Properties>
        <PathGeometry>
          <GeometryPathType PathOpen="false">
            <PathPointArray>
              <PathPointType Anchor="0 0" LeftDirection="0 0" RightDirection="0 0"/>
              <PathPointType Anchor="0 {by}" LeftDirection="0 {by}" RightDirection="0 {by}"/>
              <PathPointType Anchor="{bx} {by}" LeftDirection="{bx} {by}" RightDirection="{bx} {by}"/>
              <PathPointType Anchor="{bx} 0" LeftDirection="{bx} 0" RightDirection="{bx} 0"/>
            </PathPointArray>
          </GeometryPathType>
        </PathGeometry>
      </Properties>
      <Image Self="{img_id}" Space="$ID/#Links_RGB" ActualPpi="300 300" EffectivePpi="300 300"
        ImageTypeName="$ID/Portable Network Graphics (PNG)" ItemTransform="1 0 0 1 0 0"
        GeometricBounds="0 0 {by} {bx}" Visible="true" LocalDisplaySetting="Default">
        <Properties>
          <Profile type="string">$ID/Embedded</Profile>
          <GraphicBounds Left="0" Top="0" Right="{bx}" Bottom="{by}"/>
        </Properties>
        <Link Self="{link_id}" AssetURL="$ID/" AssetID="$ID/"
          LinkResourceURI="file:Links/{img_name}"
          StoredState="Normal" LinkResourceFormat="$ID/Portable Network Graphics (PNG)"
          LinkImportStamp="file {img_name}" LinkImportModificationTime="2026-01-01T00:00:00"
          LinkImportTime="2026-01-01T00:00:00" LinkResourceModified="false" ShowInUI="true"/>
      </Image>
    </Rectangle>
  </Spread>
</idPkg:Spread>"""


def build_idml(images: list[Path]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    spread_refs: list[str] = []
    spread_files: dict[str, str] = {}
    spread_ids: list[str] = []

    names = [
        "01 Kapak", "02 Tanitim", "03 Icindekiler",
        *[f"{p['page']} {p['title'].replace('&', 'and')}" for p in DATA["products"]],
        "14 Referanslar", "15 Iletisim",
    ]

    for i, (img, name) in enumerate(zip(images, names), 1):
        sid = f"Spread_{uid()}"
        pid = f"Page_{uid()}"
        rid = f"Rect_{uid()}"
        iid = f"Image_{uid()}"
        lid = f"Link_{uid()}"
        spread_ids.append(sid)
        path = f"Spreads/Spread_{i:02d}.xml"
        spread_files[path] = spread_xml(name, img.name, sid, pid, rid, iid, lid)
        spread_refs.append(f'  <idPkg:Spread src="{path}"/>')

    designmap = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?aid style="50" type="document" readerVersion="6.0" featureSet="257" product="17.0" ?>
<Document xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0"
  Self="d" StoryList="" SpreadList="{' '.join(spread_ids)}"
  Name="LEDAJANS Katalog 2026" ZeroPoint="0 0" ActiveLayer="ub3"
  CMYKProfile="$ID/None" RGBProfile="$ID/sRGB IEC61966-2.1"
  SolidColorIntent="UseColorSettings" AfterBlendingIntent="UseColorSettings"
  DefaultImageIntent="UseColorSettings" RGBPolicy="PreserveEmbeddedProfiles"
  CMYKPolicy="CombinationOfPreserveAndSafeCmyk" AccurateLABSpots="false">
  <Layer Self="ub3" Name="Layer 1" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true"
    LockGuides="false" UI="true" Expendable="true" Printable="true"/>
{chr(10).join(spread_refs)}
  <idPkg:Preferences src="Resources/Preferences.xml"/>
  <idPkg:Graphic src="Resources/Graphic.xml"/>
  <idPkg:Fonts src="Resources/Fonts.xml"/>
  <idPkg:Styles src="Resources/Styles.xml"/>
  <idPkg:MasterSpread src="MasterSpreads/MasterSpread_ub6.xml"/>
  <idPkg:BackingStory src="XML/BackingStory.xml"/>
</Document>"""

    master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <MasterSpread Self="MasterSpread_ub6" Name="A-Master" PageCount="1" BaseName="A"
    OverriddenPageItemProps="" ShowMasterItems="true" BindingLocation="0">
    <Page Self="ub6" Name="A" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName"
      GeometricBounds="0 0 841.89 595.276" ItemTransform="1 0 0 1 0 0"
      MasterPageTransform="1 0 0 1 0 0" AppliedMaster="n">
      <Properties><PageColor type="enumeration">UseMasterColor</PageColor></Properties>
      <MarginPreference ColumnCount="1" ColumnGutter="12" Top="0" Bottom="0" Left="0" Right="0"/>
    </Page>
  </MasterSpread>
</idPkg:MasterSpread>"""

    backing = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:BackingStory xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="17.0">
  <XmlStory Self="u98" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"/>
    </ParagraphStyleRange>
  </XmlStory>
</idPkg:BackingStory>"""

    container = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="designmap.xml" media-type="text/xml"/>
  </rootfiles>
</container>"""

    idml_path = OUT / "LEDAJANS-Katalog-2026.idml"
    with zipfile.ZipFile(idml_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        zf.writestr(zi, "application/vnd.adobe.indesign-idml-package")
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("designmap.xml", designmap)
        zf.writestr("Resources/Preferences.xml", preferences_xml())
        zf.writestr("Resources/Graphic.xml", graphic_xml())
        zf.writestr("Resources/Fonts.xml", fonts_xml())
        zf.writestr("Resources/Styles.xml", styles_xml())
        zf.writestr("MasterSpreads/MasterSpread_ub6.xml", master)
        zf.writestr("XML/BackingStory.xml", backing)
        for path, xml in spread_files.items():
            zf.writestr(path, xml)
        for img in images:
            zf.write(img, f"Links/{img.name}")
    return idml_path


def write_readme():
    text = """# LEDAJANS Katalog — InDesign Paketi

## YONTEM 1 — JSX Script (ONERILEN, %100 calisir)

1. Zip'i ac
2. InDesign'i ac
3. **Pencere → Yardimci Programlar → LEDAJANS-Katalog-Import.jsx** cift tik
   - Bulamazsan: **Dosya → Komut Dosyasi Calistir** → jsx dosyasini sec
4. **Links** klasorunu sec (page-01.png ... page-15.png)
5. 15 sayfa otomatik yerlesir
6. **Dosya → Disa Aktar → Adobe PDF (Baski)** → Kaydet

## YONTEM 2 — IDML dosyasi

1. **LEDAJANS-Katalog-2026.idml** dosyasini InDesign ile ac
2. Link uyarisi: **Links** klasorunu sec

## YONTEM 3 — Hazir PDF (InDesign gerekmez)

**LEDAJANS-Katalog-2026-Baski.pdf** dosyasini direkt matbaaya ver.

## Sorun giderme

- IDML "iyi olusturulmamis" hatasi → Yontem 1 (JSX) kullan
- Cift tik acmiyorsa → InDesign icinden Dosya → Ac
- OneDrive senkronu bozabilir → dosyayi yerel Masaustu'ne kopyala
"""
    (OUT / "OKU-BENI.md").write_text(text, encoding="utf-8")


def build_zip():
    zip_path = OUT / "LEDAJANS-Katalog-InDesign-Paket.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "LEDAJANS-Katalog-2026.idml", "LEDAJANS-Katalog-2026.idml")
        zf.write(OUT / "LEDAJANS-Katalog-Import.jsx", "LEDAJANS-Katalog-Import.jsx")
        zf.write(OUT / "OKU-BENI.md", "OKU-BENI.md")
        pdf = OUT / "LEDAJANS-Katalog-2026-Baski.pdf"
        if pdf.exists():
            zf.write(pdf, pdf.name)
        for img in sorted(LINKS.glob("page-*.png")):
            zf.write(img, f"Links/{img.name}")
    return zip_path


def main():
    print("1/3 Sayfalar render...")
    images = render_pages()
    print("2/3 PDF + IDML...")
    render_pdf()
    build_idml(images)
    write_readme()
    print("3/3 Zip paketi...")
    zf = build_zip()
    print(f"OK: {zf}")


if __name__ == "__main__":
    main()
