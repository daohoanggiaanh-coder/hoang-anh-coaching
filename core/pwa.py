# Hoàng Anh Coaching v1.5 (2026-10-31) — biểu tượng app trên điện thoại (Thêm vào màn hình chính)
# Streamlit không cho sửa <head>, nên chèn thẻ icon / manifest bằng 1 khung ẩn (cùng tên miền) vào trang cha và trang ngoài cùng.
# Ảnh icon lấy từ kho GitHub công khai của web (raw.githubusercontent.com).
from __future__ import annotations

import base64
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
   "f();setInterval(f,700);})();";
   P.head.appendChild(sc);} }catch(e){}
 try{chen(window.top.document);}catch(e){}
})();
</script>"""


def chen_icon():
    if st.session_state.get("_pwa"):
        return
    components.html(_JS % RAW, height=0)
    st.session_state["_pwa"] = True


def logo_b64() -> str:
    p = APP / "icon-192.png"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""
