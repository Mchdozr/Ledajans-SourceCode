/* LEDAJANS görünüm katmanı — ortak JS. Metin değiştirmez, sadece sınıf ekler. */
(function () {
  function ready(fn){ document.readyState !== "loading" ? fn() : document.addEventListener("DOMContentLoaded", fn); }
  ready(function () {
    // "Teknik rehberler" başlığından sonraki link listesini etiket görünümüne al
    document.querySelectorAll('[data-elementor-type="wp-page"] h2, [data-elementor-type="wp-page"] h3').forEach(function (h) {
      if (!/Teknik rehberler/i.test(h.textContent)) return;
      var el = h.nextElementSibling;
      for (var i = 0; i < 3 && el; i++, el = el.nextElementSibling) {
        if (el.tagName === "UL") { el.classList.add("lj-g-chips"); break; }
      }
    });
  });
})();
