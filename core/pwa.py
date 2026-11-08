# Hoàng Anh Coaching v1.5 (2026-10-31) — biểu tượng app trên điện thoại (Thêm vào màn hình chính)
# Streamlit không cho sửa <head>, nên chèn thẻ icon / manifest bằng 1 khung ẩn (cùng tên miền) vào trang cha và trang ngoài cùng.
# Ảnh icon lấy từ kho GitHub công khai của web (raw.githubusercontent.com).
# v2.0.1: máy còn mở trang cũ sau khi web cập nhật → lỗi "Importing a module script failed" → tự tải lại trang 1 lần.
from __future__ import annotations

import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

RAW = "https://raw.githubusercontent.com/daohoanggiaanh-coder/hoang-anh-coaching/main/assets/app/"
APP = Path(__file__).resolve().parent.parent / "assets" / "app"

_JS = """<script>
(function(){
 var R=%r;
 function chen(d){ try{
   if(!d||!d.head||d.getElementById('hac-pwa'))return;
   d.querySelectorAll('link[rel="apple-touch-icon"],link[rel="manifest"],meta[name="apple-mobile-web-app-title"]').forEach(function(e){e.remove();});
   var add=function(tag,at){var e=d.createElement(tag);for(var k in at)e.setAttribute(k,at[k]);d.head.appendChild(e);return e;};
   add('meta',{id:'hac-pwa',name:'apple-mobile-web-app-capable',content:'yes'});
   add('meta',{name:'mobile-web-app-capable',content:'yes'});
   add('meta',{name:'apple-mobile-web-app-title',content:'HA Coaching'});
   add('meta',{name:'apple-mobile-web-app-status-bar-style',content:'black-translucent'});
   add('meta',{name:'theme-color',content:'#14120F'});
   add('link',{rel:'apple-touch-icon',sizes:'180x180',href:R+'apple-touch-icon.png'});
   add('link',{rel:'manifest',href:R+'manifest.json',crossorigin:'anonymous'});
   d.querySelectorAll('link[rel*="icon"]:not([rel="apple-touch-icon"])').forEach(function(l){l.href=R+'icon-192.png';});
   d.title='Hoàng Anh Coaching';
 }catch(e){} }
 try{chen(window.parent.document);}catch(e){}
 // giao diện tối: đọc màu nền thật của app → đặt html[data-hac-theme] cho CSS riêng của web (đổi ngay khi khách chuyển sáng / tối)
 try{ var P=window.parent.document; if(!P.getElementById('hac-theme-js')){ var sc=P.createElement('script'); sc.id='hac-theme-js';
   sc.textContent="(function(){function f(){try{var a=document.querySelector('.stApp')||document.body;var c=getComputedStyle(a).backgroundColor.match(/[0-9]+/g);"+
   "if(!c)return;var l=(0.299*c[0]+0.587*c[1]+0.114*c[2]);var t=l<110?'dark':'light';"+
   "if(document.documentElement.getAttribute('data-hac-theme')!==t)document.documentElement.setAttribute('data-hac-theme',t);}catch(e){}}"+
   "function g(){try{var n=document.querySelectorAll('[data-testid=stException],[data-testid=stAlert]');for(var i=0;i<n.length;i++){var x=n[i].textContent||'';"+
   "if(/Importing a module script failed|dynamically imported module|Loading chunk/i.test(x)){var k='hac-reload',t0=+(sessionStorage.getItem(k)||0);"+
   "if(Date.now()-t0>60000){sessionStorage.setItem(k,Date.now());location.reload();}return;}}}catch(e){}}"+
   "f();setInterval(function(){f();g();},700);})();";
   P.head.appendChild(sc);} }catch(e){}
 // v3.2: nền sáng / tối tự động theo giờ (6h–18h sáng) hoặc theo lựa chọn khách — nhớ trên máy (localStorage)
 try{ var P2=window.parent.document; if(!P2.getElementById('hac-nen-js')){ var s2=P2.createElement('script'); s2.id='hac-nen-js';
   s2.textContent=%s;
   P2.head.appendChild(s2);} }catch(e){}
 try{chen(window.top.document);}catch(e){}
})();
</script>"""


NEN_JS = r"""(function(){
if(window.hacNenOK)return;window.hacNenOK=1;var prev=null,t0=Date.now();
function want(){var p=localStorage.getItem('hac-nen')||'auto';if(p==='light'||p==='dark')return p;var h=new Date().getHours();return(h>=6&&h<18)?'light':'dark';}
function cur(){return document.documentElement.getAttribute('data-hac-theme');}
function ghi(w){var v=JSON.stringify(w==='dark'?'Dark':'Light');document.querySelectorAll('a[href]').forEach(function(a){try{var u=new URL(a.href,location.href);
 if(u.origin===location.origin)localStorage.setItem('stActiveTheme-'+u.pathname+'-v2',v);}catch(e){}});}
function ap(){try{var c=cur();if(!c)return;var w=want();if(c===w)ghi(w);
 if(prev&&c!==prev&&Date.now()-t0>6000&&sessionStorage.getItem('hac-nen-dang')!=='1'){localStorage.setItem('hac-nen',c);localStorage.setItem('hac-nen-ts',Date.now());prev=c;return;}
 prev=c;sessionStorage.removeItem('hac-nen-dang');
 if(c!==w){var r=+(sessionStorage.getItem('hac-nen-r'+location.pathname)||0);if(Date.now()-r<30000)return;
  var v=JSON.stringify(w==='dark'?'Dark':'Light');var ks=Object.keys(localStorage).filter(function(k){return /^stActiveTheme-.*-v2$/.test(k);});
  ks.push('stActiveTheme-'+location.pathname+'-v2');ks.forEach(function(k){localStorage.setItem(k,v);});
  sessionStorage.setItem('hac-nen-r'+location.pathname,Date.now());sessionStorage.setItem('hac-nen-dang','1');location.reload();}}catch(e){}}
window.hacNenSet=function(p,ts){try{var t0=+(localStorage.getItem('hac-nen-ts')||0);if(ts>t0){localStorage.setItem('hac-nen',p);localStorage.setItem('hac-nen-ts',ts);sessionStorage.removeItem('hac-nen-r'+location.pathname);ap();}}catch(e){}};
setTimeout(ap,3500);setInterval(ap,2000);})();"""


def chen_icon():
    if st.session_state.get("_pwa"):
        return
    components.html(_JS % (RAW, json.dumps(NEN_JS)), height=0)
    st.session_state["_pwa"] = True


def logo_b64() -> str:
    p = APP / "icon-192.png"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""
