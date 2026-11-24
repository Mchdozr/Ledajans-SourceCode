/* Ürün sayfaları — üst bant görselini sayfanın konusuyla eşleştirir.
   Sadece arka plan görselini değiştirir; metin, başlık ve linkler aynı kalır.
   Not: Bu görseller sitede zaten yüklü ama TEMSİLÎ (yapay zekâ ile üretilmiş).
   Canlıya almadan önce gerçek proje fotoğraflarıyla değiştirilmeleri önerilir. */
(function () {
  var U = "https://ledajans.com/wp-content/uploads/";
  var HERO = {
    "/dis-mekan-led-ekran/": U + "2026/09/dis-mekan-outdoor-led.webp",
    "/ic-mekan-led-ekran/":  U + "2026/09/ic-mekan-led-ekran.webp",
    "/rental-ekran/":        U + "2026/09/rental-led-sahne.webp",
    "/cob-ekran/":           U + "2026/09/cob-led-lobi.webp",
    "/ic-mekan-rgb-panel/":  U + "2026/09/ic-mekan-rgb-panel-1.webp",
    "/dis-mekan-rgb-panel/": U + "2026/09/dis-mekan-rgb-panel-1.webp"
  };
  var POS = { "/dis-mekan-led-ekran/": "center 30%" };
  function ready(fn){ document.readyState !== "loading" ? fn() : document.addEventListener("DOMContentLoaded", fn); }
  ready(function () {
    var p = location.pathname.replace(/^\/_once/, "");
    var src = HERO[p], hero = document.querySelector(".ledajans-blog-hero");
    if (src && hero) {
      hero.style.setProperty("background-image", "url('" + src + "')", "important");
      if (POS[p]) hero.style.setProperty("background-position", POS[p], "important");
    }
  });
})();
