<?php
/**
 * LEDAJANS — Mobil sol menü (offcanvas) görünüm
 * Code Snippets → front-end → Aktif
 *
 * Canlıda `<?php` etiketi yok; ABSPATH koruması snippet sarmalayıcısıyla uyumlu.
 */
if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('ledajans_mobile_offcanvas_css')) {
/**
 * @return string
 */
function ledajans_mobile_offcanvas_css()
{
    return <<<'CSS'
#gva-overlay{background:rgba(15,23,42,.55)!important;backdrop-filter:blur(8px)!important;-webkit-backdrop-filter:blur(8px)!important}
.gva-offcanvas-content.mobile{background:#f8fafc!important;width:min(340px,88vw)!important;max-width:340px!important;height:100%!important;height:100dvh!important;overflow:hidden!important;display:flex!important;flex-direction:column!important;border-radius:0 20px 20px 0!important;box-shadow:12px 0 40px rgba(15,23,42,.22)!important;padding:0!important;float:none!important}
.gva-offcanvas-content.mobile .top-canvas{background:linear-gradient(135deg,#f46f2c 0%,#e25a1a 100%)!important;border-bottom:0!important;padding:12px 14px!important;padding-top:max(12px,env(safe-area-inset-top))!important;display:flex!important;align-items:center!important;justify-content:space-between!important;gap:12px!important;flex-shrink:0!important}
.gva-offcanvas-content.mobile .top-canvas .logo-mm{display:flex!important;align-items:center!important;min-width:0!important;flex:1 1 auto!important;min-height:32px!important;text-decoration:none!important;position:relative!important;background:transparent!important}
.gva-offcanvas-content.mobile .top-canvas .logo-mm:after{content:none!important;display:none!important}
.gva-offcanvas-content.mobile .top-canvas .logo-mm img{display:block!important;height:32px!important;width:auto!important;max-width:min(200px,62vw)!important;object-fit:contain!important;filter:none!important;mix-blend-mode:screen!important;background:transparent!important;opacity:1!important;visibility:visible!important}
.gva-offcanvas-content.mobile .top-canvas .control-close-mm{width:40px!important;height:40px!important;min-width:40px!important;border-radius:12px!important;background:rgba(255,255,255,.18)!important;color:#fff!important;font-size:0!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important}
.gva-offcanvas-content.mobile .top-canvas .control-close-mm i{display:none!important}
.gva-offcanvas-content.mobile .top-canvas .control-close-mm svg{width:18px!important;height:18px!important;display:block!important}
.gva-offcanvas-content.mobile .wp-sidebar,.gva-offcanvas-content.mobile .sidebar{display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-height:0!important;width:100%!important;margin:0!important;padding:0!important;overflow:hidden!important;float:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu{flex:1 1 auto!important;min-height:0!important;display:flex!important;flex-direction:column!important;overflow:hidden!important;width:100%!important;float:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul,
.gva-offcanvas-content.mobile ul.gva-mobile-menu,
.gva-offcanvas-content.mobile ul.gva-nav-menu{display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;align-items:stretch!important;justify-content:flex-start!important;float:none!important;width:100%!important;max-width:100%!important;padding:10px!important;margin:0!important;overflow-y:auto!important;list-style:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.submenu-inner,
.gva-offcanvas-content.mobile ul.gva-mobile-menu .submenu-inner,
.gva-offcanvas-content.mobile ul.gva-nav-menu .submenu-inner{display:none!important;flex-direction:column!important;width:100%!important;float:none!important;padding:0 10px 8px!important;margin:0!important;overflow:visible!important}
.gva-offcanvas-content.mobile #gva-mobile-menu li.open>.submenu-inner,
.gva-offcanvas-content.mobile #gva-mobile-menu li.menu-active>.submenu-inner{display:flex!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul>li,
.gva-offcanvas-content.mobile ul.gva-mobile-menu>li,
.gva-offcanvas-content.mobile ul.gva-nav-menu>li{display:block!important;float:none!important;clear:both!important;width:100%!important;max-width:100%!important;flex:0 0 auto!important;border-bottom:0!important;margin:0 0 4px!important;border-radius:14px!important;background:#fff!important;overflow:hidden!important;position:relative!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-nav-menu>li.menu-item-has-children{display:grid!important;grid-template-columns:1fr 44px!important;grid-template-rows:minmax(48px,auto) auto!important;align-items:stretch!important}
.gva-offcanvas-content.mobile ul.gva-mobile-menu>li.menu-item-has-children.open,
.gva-offcanvas-content.mobile ul.gva-mobile-menu>li.menu-item-has-children.menu-active,
.gva-offcanvas-content.mobile ul.gva-nav-menu>li.menu-item-has-children.open,
.gva-offcanvas-content.mobile ul.gva-nav-menu>li.menu-item-has-children.menu-active{background:#fff7ed!important;box-shadow:inset 3px 0 0 #f46f2c!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul>li>a,
.gva-offcanvas-content.mobile ul.gva-mobile-menu>li>a,
.gva-offcanvas-content.mobile ul.gva-nav-menu>li>a{display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;align-items:center!important;justify-content:space-between!important;width:100%!important;max-width:100%!important;padding:13px 14px!important;color:#111827!important;font-size:.9375rem!important;font-weight:700!important;min-height:48px!important;box-sizing:border-box!important;text-decoration:none!important;float:none!important;grid-column:1/2!important;grid-row:1/2!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul>li>a .item-content,
.gva-offcanvas-content.mobile ul.gva-mobile-menu>li>a .item-content{display:flex!important;flex-wrap:nowrap!important;align-items:center!important;flex:1 1 auto!important;min-width:0!important;width:auto!important;max-width:100%!important}
.gva-offcanvas-content.mobile #gva-mobile-menu .menu-title{flex:1 1 auto!important;min-width:0!important;white-space:normal!important;line-height:1.3!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul>li.menu-item-has-children>a:after{content:none!important;display:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children>a .caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-nav-menu>li.menu-item-has-children>a .caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children a .caret{display:none!important;width:0!important;height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;border:0!important;background:none!important;pointer-events:none!important;position:absolute!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children>.caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-nav-menu>li.menu-item-has-children>.caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children .caret{grid-column:2/3!important;grid-row:1/2!important;position:relative!important;top:auto!important;right:auto!important;left:auto!important;bottom:auto!important;float:none!important;justify-self:center!important;align-self:center!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#f3f4f6 none!important;background-image:none!important;width:28px!important;height:28px!important;min-width:28px!important;max-width:28px!important;margin:0!important;padding:0!important;border:0!important;border-radius:8px!important;z-index:4!important;box-sizing:border-box!important;line-height:0!important;font-size:0!important;cursor:pointer!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children>.caret:after,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children .caret:after{content:""!important;display:block!important;position:static!important;left:auto!important;top:auto!important;width:8px!important;height:8px!important;margin:-3px 0 0!important;border:0!important;border-right:2px solid #6b7280!important;border-bottom:2px solid #6b7280!important;transform:rotate(45deg)!important;background:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open>.caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active>.caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open .caret,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active .caret{background:rgba(244,111,44,.16) none!important;background-image:none!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open>.caret:after,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active>.caret:after,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.open .caret:after,
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children.menu-active .caret:after{margin:3px 0 0!important;transform:rotate(-135deg)!important;border-color:#f46f2c!important}
.gva-offcanvas-content.mobile #gva-mobile-menu ul.gva-mobile-menu>li.menu-item-has-children>.submenu-inner{grid-column:1/-1!important;grid-row:2/3!important}
.gva-offcanvas-content.mobile #gva-mobile-menu .submenu-inner>li{width:100%!important;float:none!important;background:transparent!important;margin:0!important;border-radius:10px!important}
.gva-offcanvas-content.mobile #gva-mobile-menu .submenu-inner>li>a{display:flex!important;width:100%!important;padding:9px 12px!important;min-height:42px!important;font-size:.875rem!important;font-weight:600!important;color:#4b5563!important}
.gva-offcanvas-content.mobile .ledajans-header-mobile-contact{display:flex!important;flex-direction:column!important;gap:8px!important;margin:0!important;padding:12px 12px calc(14px + env(safe-area-inset-bottom))!important;background:#fff!important;border-top:1px solid rgba(15,23,42,.06)!important;flex-shrink:0!important;width:100%!important;box-sizing:border-box!important}
.gva-offcanvas-content.mobile .ledajans-mm-cta{display:flex!important;align-items:center!important;justify-content:center!important;min-height:46px!important;border-radius:12px!important;background:#f46f2c!important;color:#fff!important;font-weight:800!important;text-decoration:none!important}
.gva-offcanvas-content.mobile .ledajans-mm-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}
.gva-offcanvas-content.mobile .ledajans-mm-wa,.gva-offcanvas-content.mobile .ledajans-mm-call{display:flex!important;align-items:center!important;justify-content:center!important;min-height:44px!important;border-radius:12px!important;font-size:.8125rem!important;font-weight:800!important;text-decoration:none!important;color:#fff!important}
.gva-offcanvas-content.mobile .ledajans-mm-wa{background:#25d366!important}
.gva-offcanvas-content.mobile .ledajans-mm-call{background:#111827!important}
CSS;
}
}

add_action('wp_head', static function () {
    static $done = false;
    if ($done) {
        return;
    }
    $done = true;
    echo '<style id="ledajans-mobile-offcanvas">';
    echo ledajans_mobile_offcanvas_css();
    echo '</style>';
}, 99);

add_action('wp_footer', static function () {
    static $done = false;
    if ($done) {
        return;
    }
    $done = true;
    echo '<style id="ledajans-mobile-offcanvas-late">';
    echo ledajans_mobile_offcanvas_css();
    echo '</style>';
    ?>
<script id="ledajans-mobile-offcanvas-js">
(function(){
  var busy=false;
  function extras(){
    if(busy) return;
    busy=true;
    try{
    var boxes=document.querySelectorAll('.gva-offcanvas-content.mobile');
    Array.prototype.forEach.call(boxes,function(box){
      var img=box.querySelector('.logo-mm img');
      if(img){
        img.src='https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png';
        img.removeAttribute('srcset');
        img.removeAttribute('sizes');
        img.removeAttribute('data-src');
        img.alt='LEDAJANS';
      }
      var close=box.querySelector('.control-close-mm');
      if(close&&!close.querySelector('svg')){
        close.innerHTML='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
      }
      var lis=box.querySelectorAll('#gva-mobile-menu li.menu-item-has-children');
      Array.prototype.forEach.call(lis,function(li){
        var a=li.querySelector(':scope > a');
        var sibling=li.querySelector(':scope > .caret');
        var inner=a?a.querySelector('.caret'):null;
        if(!sibling&&inner){
          li.insertBefore(inner, a?a.nextSibling:null);
        }
        if(a){
          Array.prototype.forEach.call(a.querySelectorAll('.caret'),function(c){
            if(c.parentNode) c.parentNode.removeChild(c);
          });
        }
        var extraCarets=li.querySelectorAll(':scope > .caret');
        for(var i=1;i<extraCarets.length;i++){
          if(extraCarets[i].parentNode) extraCarets[i].parentNode.removeChild(extraCarets[i]);
        }
      });
      var host=box.querySelector('#gva-mobile-menu')||box;
      if(host.querySelector('.ledajans-mm-cta')) return;
      var wrap=document.createElement('div');
      wrap.className='ledajans-header-mobile-contact';
      wrap.innerHTML='<a class="ledajans-mm-cta" href="https://ledajans.com/iletisim/">Ücretsiz Teklif Al</a><div class="ledajans-mm-actions"><a class="ledajans-mm-wa" href="https://wa.me/905438795108" target="_blank" rel="noopener noreferrer">WhatsApp</a><a class="ledajans-mm-call" href="tel:+902122204004">Ara</a></div>';
      host.appendChild(wrap);
    });
    }finally{busy=false;}
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', extras);
  else extras();
  window.addEventListener('load', extras);
  if(window.MutationObserver){
    var t=null;
    var mo=new MutationObserver(function(){
      clearTimeout(t);
      t=setTimeout(extras,40);
    });
    if(document.documentElement) mo.observe(document.documentElement,{childList:true,subtree:true});
  }
})();
</script>
    <?php
}, 999);
