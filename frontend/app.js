const state = {
    baseUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
    auth: localStorage.getItem('authToken') || null,
    productos: [], // Cache de productos para búsqueda rápida
};

const selectors = {
    apiUrl: document.getElementById('api-url'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    status: document.getElementById('status-msg'),
    connectBtn: document.getElementById('connect-btn'),
    landedTable: document.querySelector('#landed-table tbody'),
    filterSku: document.getElementById('filter-sku'),
    filterTransporte: document.getElementById('filter-transporte'),
    skuList: document.getElementById('sku-list'),
    productDetailsCard: document.getElementById('product-details-card'),
    detailSku: document.getElementById('detail-sku'),
    detailDescripcion: document.getElementById('detail-descripcion'),
    detailProveedor: document.getElementById('detail-proveedor'),
    detailOrigen: document.getElementById('detail-origen'),
    detailCategoria: document.getElementById('detail-categoria'),
    detailMoneda: document.getElementById('detail-moneda'),
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
        await loadProductos();
        loadLanded();
    } catch (error) {
        selectors.status.textContent = error.message;
        state.auth = null;
        localStorage.removeItem('authToken');
    }
});

async function loadProductos() {
    try {
        const data = await apiFetch('/catalog/productos');
        state.productos = data;
        // Poblar datalist para autocompletado
        selectors.skuList.innerHTML = data
            .map((p) => `<option value="${p.sku}">${p.descripcion || p.sku}</option>`)
            .join('');
    } catch (error) {
        console.error('Error cargando productos:', error);
    }
}

async function loadLanded() {
    try {
        const sku = selectors.filterSku.value.trim();
        const transporte = selectors.filterTransporte.value.trim();
        const params = new URLSearchParams();
        if (sku) params.append('sku', sku);
        if (transporte) params.append('transporte', transporte);
        const query = params.toString() ? `?${params.toString()}` : '';
        const data = await apiFetch(`/pricing/landed${query}`);
        selectors.landedTable.innerHTML = data
            .slice(0, 25)
            .map(
                (row) => `
                <tr>
                    <td>${row.sku}</td>
                    <td>${row.transporte}</td>
                    <td>${formatCurrency(row.costo_base_mxn)}</td>
                    <td>${formatCurrency(row.landed_cost_mxn)}</td>
                    <td>${formatCurrency(row.mark_up)}</td>
                </tr>`
            )
            .join('');
        
        // Mostrar detalles del producto si se filtró por SKU
        if (sku) {
            showProductDetails(sku);
        } else {
            hideProductDetails();
        }
    } catch (error) {
        selectors.status.textContent = error.message;
    }() => {
    // Debounce para evitar múltiples llamadas
    clearTimeout(selectors.filterSku.debounce);
    selectors.filterSku.debounce = setTimeout(loadLanded, 300);
}
}

function showProductDetails(sku) {
    const producto = state.productos.find((p) => p.sku === sku);
    if (producto) {
        selectors.detailSku.textContent = producto.sku || '-';
        selectors.detailDescripcion.textContent = producto.descripcion || '-';
        selectors.detailProveedor.textContent = producto.proveedor || '-';
        selectors.detailOrigen.textContent = producto.origen || '-';
        selectors.detailCategoria.textContent = producto.categoria || '-';
        selectors.detailMoneda.textContent = producto.moneda_base || '-';
        selectors.productDetailsCard.style.display = 'block';
    } else {
        hideProductDetails();
    }
}

function hideProductDetails() {
    selectors.productDetailsCard.style.display = 'none';
}

function formatCurrency(value) {
    return (value ?? 0).toLocaleString('es-MX', { minimumFractionDigits: 2 });
}

selectors.filterSku.addEventListener('input', () => {
    // Debounce para evitar múltiples llamadas
    clearTimeout(selectors.filterSku.debounce);
    selectors.filterSku.debounce = setTimeout(loadLanded, 300);
});
selectors.filterTransporte.addEventListener('change', loadLanded);

const actions = {
    'load-landed': loadLanded,
};

document.addEventListener('click', (event) => {
    const action = event.target.dataset?.action;
    if (action && actions[action]) {
        actions[action]();
    }
});

if (state.auth) {
    loadProductos().then(() => loadLanded());
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW error', err));
}
