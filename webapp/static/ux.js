'use strict';
document.addEventListener('DOMContentLoaded',()=>{
  function bind(){document.querySelectorAll('[data-reception-selection]').forEach(form=>{if(form.dataset.bound)return;form.dataset.bound='1';
    const boxes=()=>Array.from(form.querySelectorAll('input[name=seleccion]'));
    const update=()=>form.querySelector('[data-selection-count]').textContent=boxes().filter(c=>c.checked).length+' seleccionados';
    form.querySelector('[data-select-visible]').addEventListener('change',e=>{boxes().forEach(c=>c.checked=e.target.checked);update();});let anchor=0;
    boxes().forEach((c,i)=>c.addEventListener('click',e=>{if(e.shiftKey)boxes().slice(Math.min(i,anchor),Math.max(i,anchor)+1).forEach(b=>b.checked=c.checked);anchor=i;update();}));
  });}
  bind();document.body.addEventListener('htmx:afterSwap',bind);
  document.querySelectorAll('[data-count-add]').forEach(form=>{
    form.querySelector('[name=cantidad]').focus();
    form.addEventListener('submit',()=>{if(form.checkValidity())form.querySelector('button').disabled=true;});
  });
});

document.addEventListener("DOMContentLoaded",()=>{const p=new URLSearchParams(location.search),back=p.get("volver");if(back&&back.startsWith("/expedientes/")&&!back.startsWith("//")){document.querySelectorAll("[data-back-works]").forEach(a=>a.href=back);document.querySelectorAll("a[href*=codificacion]").forEach(a=>{const u=new URL(a.href);u.searchParams.set("volver",back);a.href=u;});}const o=document.querySelector("#orden");if(o&&p.get("orden"))o.value=p.get("orden");});
