#!/usr/bin/env python3
"""HTML katalog sayfalarını PNG'ye render edip InDesign IDML paketi üretir."""
import json
import re
import uuid
import zipfile
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "katalog-data.json").read_text(encoding="utf-8"))
OUT = ROOT / "indesign"
LINKS = OUT / "Links"
PAGES_DIR = ROOT / "pages"

# A4 points @ 72dpi
W = 595.276
H = 841.89
BLEED = 8.504  # 3mm


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
            url = html.as_uri()
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(800)
            out = LINKS / f"page-{i:02d}.png"
            page.locator(".page").screenshot(path=str(out))
            paths.append(out)
            print(f"  render {out.name}")
        browser.close()
    return paths


def preferences_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0">
  <DocumentPreference PageWidth="{W}" PageHeight="{H}"
    PagesPerDocument="15" FacingPages="false" DocumentBleedTopOffset="{BLEED}"
    DocumentBleedBottomOffset="{BLEED}" DocumentBleedInsideOrLeftOffset="{BLEED}"
    DocumentBleedOutsideOrRightOffset="{BLEED}" DocumentBleedUniformSize="true"
    SlugTopOffset="0" SlugBottomOffset="0" SlugInsideOrLeftOffset="0" SlugRightOrOutsideOffset="0"/>
</idPkg:Preferences>"""


def graphic_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Graphic xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0">
  <Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" Name="Black"/>
  <Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" Name="Paper"/>
  <Color Self="Color/Orange" Model="Process" Space="RGB" ColorValue="244 111 44" Name="LEDAJANS Orange"/>
</idPkg:Graphic>"""


def fonts_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0">
  <FontFamily Self="di6" Name="Minion Pro">
    <Font Self="di6FontnMinion Pro Regular" FontFamily="Minion Pro" Name="Minion Pro Regular" PostScriptName="MinionPro-Regular" Status="Installed"/>
  </FontFamily>
</idPkg:Fonts>"""


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0">
  <RootParagraphStyleGroup Self="Pandora">
    <ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle"/>
  </RootParagraphStyleGroup>
  <RootCharacterStyleGroup Self="Pandora">
    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>
  </RootCharacterStyleGroup>
</idPkg:Styles>"""


def spread_xml(idx: int, page_name: str, img_name: str, spread_id: str, page_id: str, rect_id: str, img_id: str) -> str:
    bx = W + BLEED * 2
    by = H + BLEED * 2
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0" Self="{spread_id}">
  <Spread Self="{spread_id}" PageCount="1" ShowMasterItems="true" PageTransitionType="None" FlattenerOverride="Default">
    <FlattenerPreference LineArtAndTextResolution="300" GradientAndMeshResolution="150"/>
    <Page Self="{page_id}" Name="{page_name}" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName"
      GeometricBounds="0 0 {H} {W}" ItemTransform="1 0 0 1 0 0"
      MasterPageTransform="1 0 0 1 0 0" AppliedMaster="n" OverrideList="">
      <Properties>
        <PageColor type="enumeration">UseMasterColor</PageColor>
      </Properties>
      <MarginPreference ColumnCount="1" ColumnGutter="12" Top="36" Bottom="36" Left="36" Right="36"/>
    </Page>
    <Rectangle Self="{rect_id}" ContentType="GraphicType" StoryTitle="$ID/" ItemTransform="1 0 0 1 {-BLEED} {-BLEED}"
      GeometricBounds="0 0 {by} {bx}" Visible="true" Name="$ID/">
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
      <Image Self="{img_id}" Space="$ID/#Links_RGB" ActualPpi="300 300" EffectivePpi="300 300" ImageTypeName="$ID/Portable Network Graphics (PNG)"
        ItemTransform="1 0 0 1 0 0" GeometricBounds="0 0 {by} {bx}" Visible="true" LocalDisplaySetting="Default">
        <Properties>
          <Profile type="string">$ID/Embedded</Profile>
          <GraphicBounds Left="0" Top="0" Right="{bx}" Bottom="{by}"/>
        </Properties>
        <Link Self="Link_{img_id}" AssetURL="$ID/" AssetID="$ID/" LinkResourceURI="file:Links/{img_name}"
          StoredState="Normal" LinkResourceFormat="$ID/Portable Network Graphics (PNG)"
          LinkImportStamp="file {img_name}" LinkImportModificationTime="2026-01-01T00:00:00"
          LinkImportTime="2026-01-01T00:00:00" LinkResourceModified="false" ShowInUI="true"/>
      </Image>
    </Rectangle>
  </Spread>
</idPkg:Spread>"""


def build_idml(images: list[Path]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    spread_refs = []
    spread_files: dict[str, str] = {}

    names = [
        "01 Kapak", "02 Tanıtım", "03 İçindekiler",
        *[f"{p['page']} {p['title']}" for p in DATA["products"]],
        "14 Referanslar", "15 İletişim",
    ]

    for i, (img, name) in enumerate(zip(images, names), 1):
        sid, pid, rid, iid = f"Spread_{uid()}", f"Page_{uid()}", f"Rect_{uid()}", f"Image_{uid()}"
        fname = img.name
        xml = spread_xml(i, name, fname, sid, pid, rid, iid)
        path = f"Spreads/Spread_{i:02d}.xml"
        spread_files[path] = xml
        spread_refs.append(f'  <idPkg:Spread src="{path}"/>')

    spread_list = " ".join(re.findall(r'Spread_[a-f0-9]+', " ".join(spread_files.values()))[:1])
    # rebuild spread list from file paths
    spread_ids = []
    for path, xml in spread_files.items():
        m = re.search(r'Self="(Spread_[^"]+)"', xml)
        if m:
            spread_ids.append(m.group(1))

    designmap = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?aid style="50" type="document" readerVersion="6.0" featureSet="257" product="18.0" ?>
<Document xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0"
  Self="d" StoryList="" SpreadList="{' '.join(spread_ids)}"
  Name="LEDAJANS Katalog 2026" ZeroPoint="0 0" ActiveLayer="ub3" CMYKProfile="$ID/None" RGBProfile="$ID/sRGB IEC61966-2.1"
  SolidColorIntent="UseColorSettings" AfterBlendingIntent="UseColorSettings" DefaultImageIntent="UseColorSettings"
  RGBPolicy="PreserveEmbeddedProfiles" CMYKPolicy="CombinationOfPreserveAndSafeCmyk" AccurateLABSpots="false">
{chr(10).join(spread_refs)}
  <idPkg:Preferences src="Resources/Preferences.xml"/>
  <idPkg:Graphic src="Resources/Graphic.xml"/>
  <idPkg:Fonts src="Resources/Fonts.xml"/>
  <idPkg:Styles src="Resources/Styles.xml"/>
  <Language Self="Language/$ID/Turkish" Name="$ID/Turkish" SingleQuotes="&#8216;&#8217;" DoubleQuotes="&#8220;&#8221;" PrimaryLanguageName="$ID/Turkish"/>
  <Language Self="Language/$ID/English%3a USA" Name="$ID/English: USA" SingleQuotes="&#8216;&#8217;" DoubleQuotes="&#8220;&#8221;" PrimaryLanguageName="$ID/English"/>
  <idPkg:MasterSpread src="MasterSpreads/MasterSpread_ub6.xml"/>
  <idPkg:BackingStory src="XML/BackingStory.xml"/>
</Document>"""

    master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0" Self="MasterSpread_ub6">
  <MasterSpread Self="MasterSpread_ub6" Name="A-Master" PageCount="1" BaseName="A" OverriddenPageItemProps="" ShowMasterItems="true">
    <Page Self="ub6" Name="A" AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName"
      GeometricBounds="0 0 841.89 595.276" ItemTransform="1 0 0 1 0 0" MasterPageTransform="1 0 0 1 0 0">
      <Properties><PageColor type="enumeration">UseMasterColor</PageColor></Properties>
      <MarginPreference ColumnCount="1" ColumnGutter="12" Top="36" Bottom="36" Left="36" Right="36"/>
    </Page>
  </MasterSpread>
</idPkg:MasterSpread>"""

    backing = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:BackingStory xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="18.0">
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

## Hızlı kullanım (3 adım)

1. **LEDAJANS-Katalog-2026.idml** dosyasını InDesign ile aç
2. Eksik link uyarısı çıkarsa: `Links/` klasörünü seç (aynı klasörde)
3. **Dosya → Dışa Aktar → Adobe PDF (Baskı)** → [Baskı Kalitesi] → Kaydet

## İçerik
- 15 sayfa A4 + 3mm taşma (bleed)
- 300 DPI sayfa görselleri (HTML katalogdan render)

## Yeniden üret
```bash
python3 Katalog/generate-katalog.py
python3 Katalog/generate-indesign.py
```
"""
    (OUT / "OKU-BENI.md").write_text(text, encoding="utf-8")


def main():
    print("1/2 Sayfalar render ediliyor...")
    images = render_pages()
    print("2/2 IDML paketi oluşturuluyor...")
    idml = build_idml(images)
    write_readme()
    print(f"OK: {idml}")
    print(f"Links: {LINKS}")


if __name__ == "__main__":
    main()
