'use strict';
document.addEventListener('DOMContentLoaded', () => {
  const source=document.querySelector('#bi-data');if(!source||!window.Chart)return;
  const data=JSON.parse(source.textContent),colors=['#7b263d','#a98643','#62747a','#298075','#967494','#b86535'];
  function chart(name,rows,sets,type='bar') {
    const canvas=document.querySelector('#chart-'+name);if(!canvas)return;
    new Chart(canvas,{type,data:{labels:rows.map(r=>r.label||r.folio),datasets:sets.map(([label,key],i)=>({label,data:rows.map(r=>r[key]),backgroundColor:type==='doughnut'?colors:colors[i%colors.length],borderColor:colors[i%colors.length],borderWidth:1,borderRadius:type==='bar'?3:0,maxBarThickness:40}))},options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:sets.length>1||type==='doughnut'}},scales:type==='doughnut'?{}:{y:{beginAtZero:true,ticks:{precision:0}},x:{grid:{display:false},ticks:{maxRotation:45,maxTicksLimit:16}}}}});
  }
  chart('stages',data.stages,[['Expedientes','value']]);chart('coding',data.coding,[['TIFF','value']],'doughnut');
  chart('quality',data.quality,[['Registros','value']]);chart('frequent',data.frequent,[['TIFF','value']]);
  chart('reception',data.reception,[['Cotejados','received'],['Pendientes','pending'],['Faltantes','missing'],['Discrepancias','discrepancy']]);
  chart('series',data.series,[['Iniciales','initial'],['Adicionales','additional']],'line');
  chart('volume',data.volume,[['Páginas digitales','value']]);
});
