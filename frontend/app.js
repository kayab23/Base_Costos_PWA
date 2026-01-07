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
    filterTransporte: document.getElementById('filter-transporte'),
    skuList: document.getElementById('sku-list'),
    skuInputsContainer: document.getElementById('sku-inputs-container'),
    clearSkusBtn: document.getElementById('clear-skus'),
    productDetailsCard: document.getElementById('product-details-card'),
    productDetails: document.getElementById('product-details'),
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
        const skuInputs = document.querySelectorAll('.sku-input');
        const skus = Array.from(skuInputs)
            .map(input => input.value.trim())
            .filter(Boolean);
        
        if (skus.length === 0) {
            selectors.landedTable.innerHTML = '<tr><td colspan="5">Ingrese al menos un SKU para consultar</td></tr>';
            hideProductDetails();
            return;
        }

        const transporte = selectors.filterTransporte.value.trim();
        
        // Hacer consultas para todos los SKUs
        const promises = skus.map(sku => {
            const params = new URLSearchParams();
            params.append('sku', sku);
            if (transporte) params.append('transporte', transporte);
            return apiFetch(`/pricing/landed?${params.toString()}`);
        });

        const results = await Promise.all(promises);
        const allData = results.flat();
        
        selectors.landedTable.innerHTML = allData
            .slice(0, 100)
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
        
        // Mostrar detalles de los productos consultados
        if (skus.length > 0) {
            showProductDetails(skus);
        } else {
            hideProductDetails();
        }
    } catch (error) {
        selectors.status.textContent = error.message;
    }
}

function showProductDetails(skus) {
    const productos = skus
        .map(sku => state.productos.find(p => p.sku === sku))
        .filter(Boolean);
    
    if (productos.length > 0) {
        selectors.productDetails.innerHTML = productos
            .map(producto => `
                <div class="product-detail-card">
                    <div class="product-detail-header">${producto.sku}</div>
                    <div class="details-grid">
                        <div class="detail-item">
                            <span class="detail-label">Descripción:</span>
                            <span class="detail-value">${producto.descripcion || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Proveedor:</span>
                            <span class="detail-value">${producto.proveedor || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Origen:</span>
                            <span class="detail-value">${producto.origen || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Categoría:</span>
                            <span class="detail-value">${producto.categoria || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Moneda Base:</span>
                            <span class="detail-value">${producto.moneda_base || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Activo:</span>
                            <span class="detail-value">${producto.activo ? 'Sí' : 'No'}</span>
                        </div>
                    </div>
                </div>
            `)
            .join('');
        selectors.productDetailsCard.style.display = 'block';
    } else {
        hideProductDetails();
    }
}

function hideProductDetails() {
    selectors.productDetailsCard.style.display = 'none';
}

function addSkuInput() {
    const newRow = document.createElement('div');
    newRow.className = 'sku-input-row';
    newRow.innerHTML = `
        <input type="text" class="sku-input" placeholder="Ingrese SKU" list="sku-list" autocomplete="off">
        <button class="icon-btn remove" title="Quitar SKU">×</button>
    `;
    selectors.skuInputsContainer.appendChild(newRow);
}

function removeSkuInput(button) {
    const row = button.closest('.sku-input-row');
    const remainingRows = selectors.skuInputsContainer.querySelectorAll('.sku-input-row');
    if (remainingRows.length > 1) {
        row.remove();
    }
}

function clearAllSkus() {
    selectors.skuInputsContainer.innerHTML = `
        <div class="sku-input-row">
            <input type="text" class="sku-input" placeholder="Ingrese SKU" list="sku-list" autocomplete="off">
            <button class="icon-btn add-sku" title="Agregar otro SKU">+</button>
        </div>
    `;
    selectors.landedTable.innerHTML = '';
    hideProductDetails();
}

function formatCurrency(value) {
    return (value ?? 0).toLocaleString('es-MX', { minimumFractionDigits: 2 });
}

// Event listeners
selectors.filterTransporte.addEventListener('change', loadLanded);
selectors.clearSkusBtn.addEventListener('click', clearAllSkus);

// Event delegation para botones dinámicos
selectors.skuInputsContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-sku')) {
        addSkuInput();
    } else if (e.target.classList.contains('remove')) {
        removeSkuInput(e.target);
    }
});

// Debounce en inputs de SKU
selectors.skuInputsContainer.addEventListener('input', (e) => {
    if (e.target.classList.contains('sku-input')) {
        clearTimeout(state.debounceTimer);
        state.debounceTimer = setTimeout(loadLanded, 500);
    }
});

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
    loadProductos();
}

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW error', err));
    });
}
