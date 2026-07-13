(function () {
  function initLaCounter() {
    var root = document.getElementById("la-fuar-popup");
    if (!root) return;

    var dayEl = document.getElementById("laDays");
    var hourEl = document.getElementById("laHours");
    var minEl = document.getElementById("laMinutes");
    var secEl = document.getElementById("laSeconds");
    var wrap = document.getElementById("laCountWrap");
    if (!dayEl || !hourEl || !minEl || !secEl || !wrap) return;

    var target = new Date("2026-06-06T10:00:00Z").getTime();

    function pad(value) {
      return value < 10 ? "0" + value : String(value);
    }

    function tick() {
      var now = Date.now();
      var diff = target - now;

      if (diff <= 0) {
        wrap.innerHTML =
          '<div style="grid-column:1 / -1; text-align:center; font-size:14px; font-weight:700; color:#fed7aa;">Etkinlik başladı. Sizi standımıza bekliyoruz.</div>';
        return;
      }

      var days = Math.floor(diff / 86400000);
      var hours = Math.floor((diff % 86400000) / 3600000);
      var minutes = Math.floor((diff % 3600000) / 60000);
      var seconds = Math.floor((diff % 60000) / 1000);

      dayEl.textContent = pad(days);
      hourEl.textContent = pad(hours);
      minEl.textContent = pad(minutes);
      secEl.textContent = pad(seconds);
    }

    tick();
    if (window.__laFairTimer) {
      clearInterval(window.__laFairTimer);
    }
    window.__laFairTimer = setInterval(tick, 1000);
  }

  document.addEventListener("DOMContentLoaded", initLaCounter);
  document.addEventListener("pumAfterOpen", initLaCounter);
})();
