/**
 * LEDAJANS — Elementor sticky placeholder (beyaz kuşak) JS düzeltmesi
 *
 * Kurulum: WP Code Snippets → Add New → bu kodu yapıştır → "Run snippet everywhere"
 * veya "Only run on site front-end". Önbellek temizle.
 *
 * Ek CSS (Ek-CSS-final.css Bölüm 12) ile birlikte kullan.
 */
(function () {
  'use strict';

  function killSpacers() {
    document.querySelectorAll('.elementor-sticky__spacer, [class*="sticky__spacer"]').forEach(function (el) {
      el.style.setProperty('display', 'none', 'important');
      el.style.setProperty('height', '0', 'important');
      el.style.setProperty('min-height', '0', 'important');
      el.style.setProperty('max-height', '0', 'important');
      el.style.setProperty('margin', '0', 'important');
      el.style.setProperty('padding', '0', 'important');
      el.style.setProperty('border-width', '0', 'important');
      el.style.setProperty('overflow', 'hidden', 'important');
      el.style.setProperty('line-height', '0', 'important');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', killSpacers);
  } else {
    killSpacers();
  }

  window.addEventListener('scroll', killSpacers, { passive: true });
  window.addEventListener('resize', killSpacers);

  try {
    var mo = new MutationObserver(killSpacers);
    mo.observe(document.body, { childList: true, subtree: true });
  } catch (e) {}
})();
