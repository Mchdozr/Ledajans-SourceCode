// LEDAJANS bozuk gorsel yenileme — yerel onizleme proxy'si.
// Sayfalar canli ledajans.com'dan okunur; yalnizca assets/replacements altindaki 31 gorsel yerelden servis edilir.
// Canliya hicbir sey yazmaz. Calistir: node preview/server.mjs  ->  http://localhost:8090/__
import http from 'node:http';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const REP=path.join(ROOT,'assets','replacements','wp-content','uploads')+path.sep, MOB=path.join(ROOT,'assets','replacements','mobile-hero')+path.sep, PORT=Number(process.env.PORT||8090);
const ORIGIN='https://ledajans.com';
const types={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'};
const pages=[['/','Anasayfa'],['/projeler/','Projeler (proje kartları)'],['/kontrol-kartlari/','Kontrol kartları (banner + kart görselleri)'],['/program-indir/','Program indir (teknik destek banner)'],['/h1-25-ic-mekan-rgb-panel/','İç mekan RGB panel (turuncu banner)'],['/ofc-p8-dis-mekan-led-ekran/','OFC P8 dış mekan (banner)'],['/p1-25-cob-led-ekran/','P1.25 COB (sahne banner)'],['/dis-mekan-rgb-panel/','Dış mekan RGB panel (banner)'],['/p2-9-dis-mekan-rental-led-ekran/','Dış mekan rental (banner)'],['/p2-9-ic-mekan-rental-led-ekran/','İç mekan rental (banner)'],['/rental-ekran/','Rental ekran (kabin görselleri)'],['/guc-kaynaklari/','Güç kaynakları'],['/ic-mekan-rgb-panel/','İç mekan RGB panel (P1.53 modül)'],['/led-ekran-fiyatlari-2026/','Blog: LED ekran fiyatları 2026 (Basliksiz-5)'],['/led-ekran-nedir/','Blog: LED ekran nedir (kapak)'],['/huidu-wf1-wf2-wf4-led-kontrol-karti/','Blog: Huidu WF (A5-A4)'],['/pitch-led-nedir/','Pitch LED nedir (kontrolcü)']];
function index(){return `<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Yerel önizleme</title><style>body{font:15px system-ui;margin:0;background:#0d1220;color:#e8ecf3}main{max-width:760px;margin:auto;padding:24px 16px}a{color:#F46F2C}li{margin:8px 0}.n{color:#9aa4b5;font-size:13px}</style><main><h1>LEDAJANS — yerel önizleme</h1><p class=n>Sayfalar canlıdan çekiliyor; bozuk/eksik 31 görsel yerel yeni dosyalardan geliyor. Mobil banner'lar için 960px WebP yalnızca dar ekranda (?mobil=1 ile zorla). Canlıya hiçbir şey yazılmıyor.</p><ul>${pages.map(([p,t])=>`<li><a href="${p}">${t}</a> <span class=n>${p}</span></li>`).join('')}</ul><p><a href="/__onizleme">Önce/sonra karşılaştırma sayfası</a></p></main>`;}
const MOBMAP={'2026/04/dis-mekan-gorsel-scaled.png':'dis-mekan-gorsel-scaled-960.webp','2026/04/dis-mekan-rgb-scaled.png':'dis-mekan-rgb-scaled-960.webp','2026/04/Firefly_Gemini-Flash-1-scaled.png':'Firefly_Gemini-Flash-1-scaled-960.webp','2026/04/ic-mekan-gorsel-scaled.png':'ic-mekan-gorsel-scaled-960.webp','2026/04/Firefly_Gemini-Flash_LEDAJANS-yazisi-tamamen-turuncu-olsun-o-kadar-13541.png':'Firefly_Gemini-Flash_LEDAJANS-yazisi-tamamen-tur-960.webp','2026/04/Firefly_Gemini-Flash_LEDAJANS-sirketi-led-tabelalar-uretip-satip-montajini-yapiyor-harika-calisiyorlar-ve-535525-scaled.png':'Firefly_Gemini-Flash_LEDAJANS-sirketi-led-tabela-960.webp','2026/04/Kontrol-kartlari.png':'Kontrol-kartlari-960.webp','2026/04/teknik-destek-scaled.png':'teknik-destek-scaled-960.webp'};
http.createServer(async(req,res)=>{try{
 const u=new URL(req.url,'http://x');
 if(u.pathname==='/__index'||u.pathname==='/__'){res.writeHead(200,{'content-type':'text/html; charset=utf-8'});return res.end(index());}
 if(u.pathname==='/__onizleme'){res.writeHead(200,{'content-type':'text/html; charset=utf-8'});return res.end(fs.readFileSync(path.join(ROOT,'preview','onizleme.html')));}
 if(u.pathname.startsWith('/wp-content/uploads/')){const rel=decodeURIComponent(u.pathname.slice(20));const f=path.join(REP,rel);if(!f.startsWith(REP))return res.end();
   if(fs.existsSync(f)&&fs.statSync(f).isFile()){res.writeHead(200,{'content-type':types[path.extname(f).toLowerCase()]||'application/octet-stream','x-local':'replacement','cache-control':'no-store'});return fs.createReadStream(f).pipe(res);}}
 if(u.pathname.startsWith('/__m/')){const f=path.join(MOB,path.basename(decodeURIComponent(u.pathname.slice(5))));if(fs.existsSync(f)){res.writeHead(200,{'content-type':'image/webp'});return fs.createReadStream(f).pipe(res);}}
 const up=await fetch(ORIGIN+u.pathname+u.search,{headers:{'user-agent':req.headers['user-agent']||'Mozilla/5.0','accept':req.headers['accept']||'*/*'},redirect:'manual'});
 const h={};up.headers.forEach((v,k)=>{if(!['content-encoding','content-length','transfer-encoding','connection','strict-transport-security','content-security-policy'].includes(k))h[k]=v;});
 if(h.location)h.location=h.location.replace(/^https?:\/\/(www\.)?ledajans\.com/,'');
 const ct=h['content-type']||'';
 if(/text\/html|text\/css|javascript|json/.test(ct)){let t=await up.text();
   t=t.replace(/https?:\\?\/\\?\/(www\.)?ledajans\.com/g,'').replace(/(["'(])\/\/(www\.)?ledajans\.com/g,'$1');
   if(/text\/html/.test(ct)){const mob=/Mobile|Android|iPhone/i.test(req.headers['user-agent']||'')||u.searchParams.get('mobil')==='1';
     if(mob)for(const [k,v] of Object.entries(MOBMAP))t=t.split('/wp-content/uploads/'+k).join('/__m/'+v);
     t=t.replace('</body>','<div style="position:fixed;left:8px;bottom:8px;z-index:99999;background:#F46F2C;color:#fff;font:12px system-ui;padding:6px 10px;border-radius:8px"><a style="color:#fff" href="/__">YEREL ÖNİZLEME</a> · yeni görseller</div></body>');}
   res.writeHead(up.status,h);return res.end(t);}
 res.writeHead(up.status,h);res.end(Buffer.from(await up.arrayBuffer()));
}catch(e){res.writeHead(502,{'content-type':'text/plain'});res.end('proxy hata: '+e.message);}}).listen(PORT,'127.0.0.1',()=>console.log('LEDAJANS yerel onizleme: http://localhost:'+PORT+'/__  (durdurmak icin Ctrl+C)'));
