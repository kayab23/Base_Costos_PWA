const state = {
    baseUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
    auth: localStorage.getItem('authToken') || null,
};

const selectors = {
    apiUrl: document.getElementById('api-url'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    status: document.getElementById('status-msg'),
    connectBtn: document.getElementById('connect-btn'),
    productsTable: document.querySelector('#productos-table tbody'),
    landedTable: document.querySelector('#landed-table tbody'),
    filterSku: document.getElementById('filter-sku'),
    listaTable: document.querySelector('#lista-table tbody'),
    listaSku: document.getElementById('filter-precio-sku'),
    listaCliente: document.getElementById('filter-precio-cliente'),
    recalcForm: document.getElementById('recalc-form'),
    recalcOutput: document.getElementById('recalc-output'),
    recalcTransporte: document.getElementById('recalc-transporte'),
    recalcMonedas: document.getElementById('recalc-monedas'),
};

if (state.baseUrl) selectors.apiUrl.value = state.baseUrl;
if (state.auth) selectors.status.textContent = 'Sesión guardada (reautenticar si es necesario).';

async function apiFetch(path, options = {}) {
    if (!state.auth) {
        throw new Error('No hay sesión activa');
    }
    const response = await fetch(`${state.baseUrl}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Basic ${state.auth}`,
            ...(options.headers || {}),
        },
    });
    if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Error ${response.status}: ${detail}`);
    }
    return response.json();
}

selectors.connectBtn.addEventListener('click', async () => {
    try {
        state.baseUrl = selectors.apiUrl.value.trim();
        const token = btoa(`${selectors.username.value}:${selectors.password.value}`);
        state.auth = token;
        localStorage.setItem('apiUrl', state.baseUrl);
        localStorage.setItem('authToken', token);
        const health = await apiFetch('/health');
        selectors.status.textContent = `Conectado. API v${health.version || '0.1'} lista.`;
        loadProductos();
        loadLanded();
        loadListaPrecios();
    } catch (error) {
        selectors.status.textContent = error.message;
        state.auth = null;
        localStorage.removeItem('authToken');
    }
});

async function loadProductos() {
    try {
        const data = await apiFetch('/catalog/productos');
        selectors.productsTable.innerHTML = data
            .slice(0, 25)
            .map(
                (p) => `
                <tr>
                    <td>${p.sku}</td>
                    <td>${p.descripcion || ''}</td>
                    <td>${p.proveedor || ''}</td>
                    <td>${p.moneda_base || ''}</td>
                </tr>`
            )
            .join('');
    } catch (error) {
        selectors.status.textContent = error.message;
    }
}

async function loadLanded() {
    try {
        const sku = selectors.filterSku.value.trim();
        const query = sku ? `?sku=${encodeURIComponent(sku)}` : '';
        const data = await apiFetch(`/pricing/landed${query}`);
        selectors.landedTable.innerHTML = data
            .slice(0, 25)
            .map(
                (row) => `
                <tr>
                    <td>${row.sku}</td>
                    <td>${row.transporte}</td>
                    <td>${(row.tc_mxn ?? 0).toFixed(2)}</td>
                    <td>${(row.landed_cost_mxn ?? 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                </tr>`
            )
            .join('');
    } catch (error) {
        selectors.status.textContent = error.message;
    }
}

async function loadListaPrecios() {
    try {
        const params = new URLSearchParams();
        const sku = selectors.listaSku.value.trim();
        const cliente = selectors.listaCliente.value.trim();
        if (sku) params.append('sku', sku);
        if (cliente) params.append('tipo_cliente', cliente);
        const query = params.toString() ? `?${params.toString()}` : '';
        const data = await apiFetch(`/pricing/lista${query}`);
        const rows = data.slice(0, 25);
        if (!rows.length) {
            selectors.listaTable.innerHTML = '<tr><td colspan="10">Sin resultados</td></tr>';
            return;
        }
        selectors.listaTable.innerHTML = rows
            .map(
                (row) => `
                <tr>
                    <td>${row.sku}</td>
                    <td>${row.tipo_cliente}</td>
                    <td>${row.moneda_precio}</td>
                    <td>${formatNumber(row.tc_mxn, 4)}</td>
                    <td>${formatCurrency(row.landed_cost_mxn)}</td>
                    <td>${formatPercent(row.margen_pct)}</td>
                    <td>${formatCurrency(row.precio_venta_mxn)}</td>
                    <td>${formatCurrency(row.precio_venta_moneda)}</td>
                    <td>${formatCurrency(row.precio_min_mxn)}</td>
                    <td>${row.notas || ''}</td>
                </tr>`
            )
            .join('');
    } catch (error) {
        selectors.status.textContent = error.message;
    }
}

function formatCurrency(value) {
    const amount = Number(value ?? 0);
    return amount.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(value, digits = 2) {
    const amount = Number(value ?? 0);
    return amount.toLocaleString('es-MX', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function formatPercent(value) {
    const pct = Number(value ?? 0) * 100;
    return `${pct.toFixed(2)}%`;
}

selectors.recalcForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        const monedas = selectors.recalcMonedas.value
            .split(',')
            .map((c) => c.trim().toUpperCase())
            .filter(Boolean);
        const payload = {
            transporte: selectors.recalcTransporte.value,
            monedas,
        };
        const result = await apiFetch('/pricing/recalculate', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        selectors.recalcOutput.textContent = `Listo. Landed: ${result.landed_rows} | Precios: ${result.price_rows}`;
        loadLanded();
        loadListaPrecios();
    } catch (error) {
        selectors.recalcOutput.textContent = error.message;
    }
});

const actions = {
    'load-products': loadProductos,
    'load-landed': loadLanded,
    'load-precios': loadListaPrecios,
};

document.addEventListener('click', (event) => {
    const action = event.target.dataset?.action;
    if (action && actions[action]) {
        actions[action]();
    }
});

if (state.auth) {
    loadProductos();
    loadLanded();
    loadListaPrecios();
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW error', err));
}
