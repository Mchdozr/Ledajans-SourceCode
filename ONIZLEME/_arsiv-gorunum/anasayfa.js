/* Anasayfa görünüm katmanı. Metin değiştirmez.
   1) "Hemen her sektördeyiz" bölümündeki dev logo görselini, sayfadaki GERÇEK
      proje fotoğraflarından 4'lü bir kolajla değiştirir (aynı sayfada zaten var).
   2) "Ürünlerimiz" kartlarında kategoriyle eşleşen, aynı oranlı görseller kullanır
      (sitede yüklü, TEMSİLÎ görseller; canlıdan önce gerçek fotoğraf önerilir). */
(function () {
  var U = "https://ledajans.com/wp-content/uploads/";
  var KART = {
    "/cob-ekran/": U + "2026/09/cob-led-lobi.webp",
    "/dis-mekan-rgb-panel/": U + "2026/09/dis-mekan-rgb-panel-1.webp",
    "/ic-mekan-rgb-panel/": U + "2026/09/ic-mekan-rgb-panel-1.webp",
    "/kontrol-kartlari/": U + "2026/09/colorlight-a60-player.webp",
    "/dis-mekan-led-ekran/": U + "2026/09/dis-mekan-led-ekran-1.webp",
    "/rental-ekran/": U + "2026/09/rental-led-sahne.webp",
    "/ic-mekan-led-ekran/": U + "2026/09/ic-mekan-led-ekran.webp"
  };
  function ready(fn){ document.readyState !== "loading" ? fn() : document.addEventListener("DOMContentLoaded", fn); }
  ready(function () {
    // 1) Sektör kolajı
    var box = document.querySelector(".ledajans-about-image-container");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".ledajans-project-card"));
    if (box && cards.length >= 4) {
      // Proje kartlarındaki medya (gerçek saha videoları); farklı sektörlerden 4 tane seç
      var all = cards.map(function (c) {
        var m = c.querySelector(".ledajans-project-image"), t = c.querySelector(".ledajans-project-title");
        var srcEl = m && (m.querySelector("source") || m);
        var s = srcEl && (srcEl.getAttribute("data-src") || srcEl.getAttribute("src") || m.currentSrc);
        if (s && s.indexOf("data:") === 0) s = null;
        return { src: s, video: !!(m && m.tagName === "VIDEO"), alt: (m && m.getAttribute("alt")) || "", cap: t ? t.textContent.trim() : "" };
      }).filter(function (x) { return x.src; });
      var want = [/küre/i, /^iç mekan/i, /rental/i, /mağaza/i], picks = [], used = {};
      want.forEach(function (re) {
        for (var i = 0; i < all.length; i++) if (!used[i] && re.test(all[i].cap)) { used[i] = 1; picks.push(all[i]); return; }
      });
      for (var j = 0; j < all.length && picks.length < 4; j++) if (!used[j]) { used[j] = 1; picks.push(all[j]); }
      if (picks.length === 4) {
        var g = document.createElement("div"); g.className = "lj-g-kolaj";
        picks.forEach(function (p) {
          var f = document.createElement("figure"), fc = document.createElement("figcaption"), el;
          if (p.video) {
            el = document.createElement("video");
            el.muted = true; el.loop = true; el.autoplay = true; el.playsInline = true; el.preload = "metadata";
            el.setAttribute("muted", ""); el.setAttribute("playsinline", ""); el.setAttribute("aria-label", p.cap);
            el.src = p.src;
          } else { el = document.createElement("img"); el.src = p.src; el.alt = p.alt; el.loading = "lazy"; }
          fc.textContent = p.cap;
          f.appendChild(el); f.appendChild(fc); g.appendChild(f);
        });
        var old = box.querySelector(".ledajans-about-image"); if (old) old.style.display = "none";
        box.classList.add("lj-g-kolaj-var"); box.appendChild(g);
      }
    }
    // 2) Ürün kartı görselleri
    document.querySelectorAll("a.products-card").forEach(function (a) {
      var path = a.getAttribute("href").replace(/^https?:\/\/[^/]+/, "");
      var frame = a.querySelector(".products-card-inner > div:first-child"), img = frame && frame.querySelector("img");
      if (!img) return;
      if (KART[path]) { img.src = KART[path]; img.removeAttribute("srcset"); }
      else frame.classList.add("lj-g-urun-kesik"); // ör. güç kaynağı: dekupe ürün görseli, kutuya sığdır
    });
  });
})();
