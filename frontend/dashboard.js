async function fetchMetrics(periodDays=30, vendedor='all'){
  const q = new URLSearchParams({periodDays, vendedor});
  const res = await fetch('/api/dashboard/metrics?'+q.toString());
  if(!res.ok) throw new Error('metrics fetch failed');
  return res.json();
}

function renderSummary(m){
  document.getElementById('totalVentas').innerText = m.total_sales_formatted || '-';
  document.getElementById('avgValor').innerText = m.avg_value_formatted || '-';
  document.getElementById('winRate').innerText = (m.win_rate_percent? m.win_rate_percent+'%':'-');
  document.getElementById('avgMargin').innerText = (m.avg_margin_percent? m.avg_margin_percent+'%':'-');
}

function renderCharts(m){
  const ventasTrace = { x:m.sales_by_day.map(d=>d.date), y:m.sales_by_day.map(d=>d.amount), type:'scatter' };
  Plotly.newPlot('ventasChart',[ventasTrace],{margin:{t:10}});

  const clients = m.top_clients || [];
  const data = [{labels:clients.map(c=>c.name), values:clients.map(c=>c.amount), type:'pie'}];
  Plotly.newPlot('topClients', data, {margin:{t:10}});
}

function renderTable(rows){
  const tbody = document.querySelector('#cotTable tbody'); tbody.innerHTML = '';
  rows.forEach(r=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><a href="/api/cotizacion/pdf/${r.id}" target="_blank">${r.folio}</a></td><td>${r.fecha}</td><td>${r.cliente}</td><td>${r.vendedor}</td><td>${r.valor_formatted}</td><td>${r.estado}</td>`;
    tbody.appendChild(tr);
  });
  if(!$.fn.dataTable.isDataTable('#cotTable')){
    $('#cotTable').DataTable();
  }
}

async function refresh(){
  try{
    document.getElementById('refresh').disabled=true;
    const p = document.getElementById('period').value;
    const v = document.getElementById('vendedor').value;
    const m = await fetchMetrics(p,v);
    renderSummary(m);
    renderCharts(m);
    renderTable(m.recent_quotes || []);
    document.getElementById('refresh').disabled=false;
  }catch(e){
    console.error(e);
    alert('Error al cargar métricas');
    document.getElementById('refresh').disabled=false;
  }
}

async function init(){
  document.getElementById('refresh').addEventListener('click', refresh);
  // populate vendedores
  const res = await fetch('/api/vendedores');
  if(res.ok){
    const v = await res.json();
    const sel = document.getElementById('vendedor');
    v.forEach(x=>{ const o=document.createElement('option'); o.value=x.id; o.textContent=x.nombre; sel.appendChild(o); });
  }
  await refresh();
}

init();
