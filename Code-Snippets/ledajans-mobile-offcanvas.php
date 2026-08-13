<?php
/**
 * LEDAJANS — Mobil sol menü (offcanvas) görünüm
 * Code Snippets → Run everywhere / front-end → Aktif
 */
if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_head', static function () {
    static $done = false;
    if ($done) {
        return;
    }
    $done = true;
    echo '<style id="ledajans-mobile-offcanvas">';
    echo '#gva-overlay{background:rgba(15,23,42,.55)!important;backdrop-filter:blur(8px)!important;-webkit-backdrop-filter:blur(8px)!important}';
    echo '.gva-offcanvas-content.mobile{background:#f8fafc!important;width:min(340px,88vw)!important;max-width:340px!important;height:100%!important;height:100dvh!important;overflow:hidden!important;display:flex!important;flex-direction:column!important;border-radius:0 20px 20px 0!important;box-shadow:12px 0 40px rgba(15,23,42,.22)!important;padding:0!important}';
    echo '.gva-offcanvas-content.mobile .top-canvas{background:linear-gradient(135deg,#f46f2c 0%,#e25a1a 100%)!important;border-bottom:0!important;padding:12px 14px!important;padding-top:max(12px,env(safe-area-inset-top))!important;display:flex!important;align-items:center!important;justify-content:space-between!important}';
    echo '.gva-offcanvas-content.mobile .top-canvas .logo-mm img{height:28px!important;width:auto!important;max-width:180px!important;filter:brightness(0) invert(1)!important}';
    echo '.gva-offcanvas-content.mobile .top-canvas .control-close-mm{width:40px!important;height:40px!important;min-width:40px!important;border-radius:12px!important;background:rgba(255,255,255,.18)!important;color:#fff!important;font-size:0!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important}';
    echo '.gva-offcanvas-content.mobile .top-canvas .control-close-mm i{display:none!important}';
    echo '.gva-offcanvas-content.mobile .top-canvas .control-close-mm svg{width:18px!important;height:18px!important;display:block!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu{flex:1 1 auto!important;min-height:0!important;display:flex!important;flex-direction:column!important;overflow:hidden!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu{padding:10px!important;margin:0!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch!important;flex:1 1 auto!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li{border-bottom:0!important;margin:0 0 4px!important;border-radius:14px!important;background:#fff!important;overflow:hidden!important;width:auto!important;display:block!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open,.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active{background:#fff7ed!important;box-shadow:inset 3px 0 0 #f46f2c!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li>a,.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li a{display:flex!important;align-items:center!important;justify-content:space-between!important;width:100%!important;padding:13px 12px 13px 14px!important;color:#111827!important;font-size:.9375rem!important;font-weight:700!important;min-height:48px!important;box-sizing:border-box!important;text-decoration:none!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children>a:after{content:none!important;display:none!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children .caret,.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children a .caret{display:inline-block!important;background:#f3f4f6 none!important;background-image:none!important;width:28px!important;height:28px!important;min-width:28px!important;position:relative!important;top:auto!important;right:auto!important;margin:0 0 0 auto!important;border:0!important;border-radius:8px!important;z-index:2!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children .caret:after{content:""!important;display:block!important;position:absolute!important;left:10px!important;top:9px!important;width:7px!important;height:7px!important;border:0!important;border-right:2px solid #6b7280!important;border-bottom:2px solid #6b7280!important;transform:rotate(45deg)!important;background:none!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open .caret,.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active .caret{background:rgba(244,111,44,.16) none!important;background-image:none!important}';
    echo '.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open .caret:after,.gva-offcanvas-content #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active .caret:after{top:12px!important;transform:rotate(-135deg)!important;border-color:#f46f2c!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-header-mobile-contact{display:flex!important;flex-direction:column!important;gap:8px!important;margin:0!important;padding:12px 12px calc(14px + env(safe-area-inset-bottom))!important;background:#fff!important;border-top:1px solid rgba(15,23,42,.06)!important;flex-shrink:0!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-mm-cta{display:flex!important;align-items:center!important;justify-content:center!important;min-height:46px!important;border-radius:12px!important;background:#f46f2c!important;color:#fff!important;font-weight:800!important;text-decoration:none!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-mm-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-mm-wa,.gva-offcanvas-content.mobile .ledajans-mm-call{display:flex!important;align-items:center!important;justify-content:center!important;min-height:44px!important;border-radius:12px!important;font-size:.8125rem!important;font-weight:800!important;text-decoration:none!important;color:#fff!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-mm-wa{background:#25d366!important}';
    echo '.gva-offcanvas-content.mobile .ledajans-mm-call{background:#111827!important}';
    echo '</style>';
}, 99);

add_action('wp_footer', static function () {
    static $done = false;
    if ($done) {
        return;
    }
    $done = true;
    ?>
<script id="ledajans-mobile-offcanvas-js">
(function(){
  function extras(){
    var boxes=document.querySelectorAll('.gva-offcanvas-content.mobile');
    Array.prototype.forEach.call(boxes,function(box){
      var close=box.querySelector('.control-close-mm');
      if(close&&!close.querySelector('svg')){
        close.innerHTML='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
      }
      var host=box.querySelector('#gva-mobile-menu')||box;
      if(host.querySelector('.ledajans-mm-cta')) return;
      var wrap=document.createElement('div');
      wrap.className='ledajans-header-mobile-contact';
      wrap.innerHTML='<a class="ledajans-mm-cta" href="https://ledajans.com/iletisim/">Ücretsiz Teklif Al</a><div class="ledajans-mm-actions"><a class="ledajans-mm-wa" href="https://wa.me/905438795108" target="_blank" rel="noopener noreferrer">WhatsApp</a><a class="ledajans-mm-call" href="tel:+902122204004">Ara</a></div>';
      host.appendChild(wrap);
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', extras);
  else extras();
})();
</script>
    <?php
}, 99);
