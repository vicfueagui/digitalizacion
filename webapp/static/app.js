'use strict';
document.addEventListener('DOMContentLoaded', () => {
  if (window.htmx) { htmx.config.allowEval = false; htmx.config.allowScriptTags = false; htmx.config.historyCacheSize = 0; htmx.config.selfRequestsOnly = true; }
  document.body.addEventListener('htmx:beforeRequest', () => { const s = document.querySelector('#search-status'); if (s) s.textContent = 'Buscando…'; });
  document.body.addEventListener('htmx:afterRequest', e => { const s = document.querySelector('#search-status'); if (s) s.textContent = e.detail.successful ? 'Resultados actualizados.' : 'No se pudo actualizar. Usa Buscar para volver a intentar.'; });
  document.querySelectorAll('.action-form').forEach(form => form.addEventListener('submit', () => {
    if (!form.checkValidity()) return;
    form.querySelectorAll('button[type=submit]').forEach(b => b.disabled = true);
    form.querySelector('.form-progress').hidden = false;
  }));
  document.querySelectorAll('[data-delivery-preview]').forEach(row => row.querySelector('input').addEventListener('input', event => {
    const page = Number(event.target.value);
    if (Number.isInteger(page) && page >= 1 && page <= Number(event.target.max)) row.querySelector('a').href = row.dataset.base + page + '/';
  }));
  const desk = document.querySelector('[data-viewer]');
  if (!desk) return;
  const work = desk.dataset.work, image = desk.querySelector('#tiff-image'), buttons = Array.from(desk.querySelectorAll('.file-open'));
  let selected = null, page = 1, zoom = 1;
  const visible = () => buttons.filter(b => b.dataset.active === '1' || desk.querySelector('#show-retired').checked);
  function show(button, newPage = 1) {
    if (!button) return;
    selected = button; page = Math.max(1, Math.min(Number(button.dataset.pages), newPage));
    buttons.forEach(b => b.closest('.file-row').classList.toggle('active-file', b === button));
    image.hidden = false; image.src = `/expedientes/${work}/imagen/${button.dataset.file}/${page}/`;
    desk.querySelector('#page-label').textContent = `Página ${page} / ${button.dataset.pages}`;
    desk.querySelector('#image-caption').textContent = button.dataset.name;
    desk.querySelectorAll('[data-file-action]').forEach(a => {
      a.href = a.dataset.fileAction === 'code' ? `/expedientes/${work}/codificacion/?archivo=${button.dataset.file}` : `/expedientes/${work}/accion/${a.dataset.fileAction}/?archivo=${button.dataset.file}&pagina=${page}`;
      a.classList.toggle('disabled', button.dataset.active !== '1'); a.setAttribute('aria-disabled', button.dataset.active !== '1');
    });
  }
  function resize(type) {
    zoom = type === 'fit' ? 1 : Math.max(.5, Math.min(4, zoom + (type === 'in' ? .25 : -.25)));
    desk.querySelector('.image-stage').classList.toggle('zoomed', zoom !== 1);
    image.style.width = zoom === 1 ? '' : `${image.naturalWidth * zoom}px`;
  }
  function batch(type) {
    const ids = Array.from(desk.querySelectorAll('.file-select:checked')).filter(c => c.closest('.file-row').dataset.active === (type === 'retirar' ? '1' : '0')).map(c => c.value);
    if (!ids.length) { desk.querySelector('#image-caption').textContent = `Selecciona TIFF ${type === 'retirar' ? 'activos' : 'retirados'} para continuar.`; return; }
    const query = new URLSearchParams({tipo: type}); ids.forEach(id => query.append('seleccion', id));
    location.href = `/expedientes/${work}/accion/batch/?${query}`;
  }
  buttons.forEach(b => b.addEventListener('click', () => show(b)));
  desk.querySelector('[data-page-prev]').addEventListener('click', () => show(selected, page - 1));
  desk.querySelector('[data-page-next]').addEventListener('click', () => show(selected, page + 1));
  desk.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => resize(b.dataset.zoom)));
  desk.querySelectorAll('[data-batch]').forEach(b => b.addEventListener('click', () => batch(b.dataset.batch)));
  desk.querySelector('#show-retired').addEventListener('change', e => { desk.classList.toggle('show-retired', e.target.checked); if (selected && !visible().includes(selected)) show(visible()[0]); });
  desk.querySelector('#select-all').addEventListener('change', e => visible().forEach(b => b.closest('.file-row').querySelector('input').checked = e.target.checked));
  image.addEventListener('error', () => { desk.querySelector('#image-caption').textContent = 'No se pudo mostrar la página. Valida el expediente y revisa el archivo.'; image.hidden = true; });
  document.addEventListener('keydown', event => {
    if (event.target.closest('input,textarea,select,[contenteditable=true]')) return;
    const rect = desk.getBoundingClientRect(); if (rect.bottom < 0 || rect.top > window.innerHeight) return;
    const key = event.key, list = visible(); let handled = true;
    if (key === 'F7' || key === 'F8') show(list[Math.max(0, Math.min(list.length - 1, list.indexOf(selected) + (key === 'F7' ? -1 : 1)))]);
    else if (key === 'PageUp' || key === 'PageDown') show(selected, page + (key === 'PageUp' ? -1 : 1));
    else if (key === '+' || key === '=') resize('in');
    else if (key === '-') resize('out');
    else if (key.toLowerCase() === 'f' && !event.ctrlKey) resize('fit');
    else if (key === 'F2' && selected && selected.dataset.active === '1') desk.querySelector('[data-file-action=rename]').click();
    else if (key === 'Delete') batch('retirar');
    else if (event.ctrlKey && key.toLowerCase() === 'o') desk.querySelector('[data-shortcut-upload]').click();
    else if (event.ctrlKey && key.toLowerCase() === 'a') { const all = desk.querySelector('#select-all'); all.checked = true; all.dispatchEvent(new Event('change')); }
    else handled = false;
    if (handled) event.preventDefault();
  });
  show(visible()[0]);
});
