// LEDAJANS Katalog — InDesign Otomatik Import
// Kullanım: InDesign → Pencere → Yardımcı Programlar → LEDAJANS-Katalog-Import.jsx çift tık
// veya Dosya → Komut Dosyası Çalıştır

#target indesign

(function () {
    var linksFolder = Folder.selectDialog(
        "Links klasorunu secin\n(page-01.png ... page-15.png iceren klasor)"
    );
    if (!linksFolder) return;

    var pngFiles = [];
    var all = linksFolder.getFiles("*.png");
    for (var i = 0; i < all.length; i++) {
        if (all[i].name.match(/^page-\d+\.png$/i)) {
            pngFiles.push(all[i]);
        }
    }

    pngFiles.sort(function (a, b) {
        var na = parseInt(a.name.match(/\d+/), 10);
        var nb = parseInt(b.name.match(/\d+/), 10);
        return na - nb;
    });

    if (pngFiles.length === 0) {
        alert("Hata: page-01.png ... page-15.png bulunamadi.\nZip icindeki Links klasorunu secin.");
        return;
    }

    var doc = app.documents.add(true);

    with (doc.documentPreferences) {
        pageWidth = "210mm";
        pageHeight = "297mm";
        facingPages = false;
        documentBleedTopOffset = "3mm";
        documentBleedBottomOffset = "3mm";
        documentBleedInsideOrLeftOffset = "3mm";
        documentBleedOutsideOrRightOffset = "3mm";
    }

    for (var p = 0; p < pngFiles.length; p++) {
        var page = (p === 0) ? doc.pages[0] : doc.pages.add(LocationOptions.AT_END);
        var pb = page.bounds; // [y1, x1, y2, x2] points

        var frame = page.rectangles.add();
        frame.geometricBounds = [pb[0], pb[1], pb[2], pb[3]];
        frame.strokeWeight = 0;
        frame.fillColor = doc.swatches.itemByName("Paper");

        frame.place(pngFiles[p]);
        frame.fit(FitOptions.CONTENT_TO_FRAME);
        frame.fit(FitOptions.PROPORTIONALLY);
        frame.fit(FitOptions.CENTER_CONTENT);
    }

    alert(
        "LEDAJANS Katalog hazir!\n\n" +
        pngFiles.length + " sayfa yerlestirildi.\n\n" +
        "Simdi: Dosya > Disa Aktar > Adobe PDF (Baski)"
    );
})();
