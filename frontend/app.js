const state = {
    baseUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
    auth: localStorage.getItem('authToken') || null,
    userRole: localStorage.getItem('userRole') || null, // Nuevo: almacenar rol
    productos: [], // Cache de productos para búsqueda rápida
    landedData: [], // Almacenar últimos resultados para descarga
};

const selectors = {
    apiUrl: document.getElementById('api-url'),
    username: document.getElementById('username'),
    password: document.getElementById('password'),
    status: document.getElementById('status-msg'),
    userRole: document.getElementById('user-role'), // Nuevo: elemento para mostrar rol
    connectBtn: document.getElementById('connect-btn'),
    landedTable: document.querySelector('#landed-table tbody'),
    skuList: document.getElementById('sku-list'),
    skuInputsContainer: document.getElementById('sku-inputs-container'),
    clearSkusBtn: document.getElementById('clear-skus'),
    downloadExcelBtn: document.getElementById('download-excel'),
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
    console.log('Botón clickeado');
    try {
        selectors.status.textContent = 'Conectando...';
        state.baseUrl = selectors.apiUrl.value.trim();
        const username = selectors.username.value.trim();
        const password = selectors.password.value;
        
        console.log('URL:', state.baseUrl);
        console.log('Usuario:', username);
        
        if (!username || !password) {
            selectors.status.textContent = 'Ingrese usuario y contraseña';
            return;
        }
        
        const token = btoa(`${username}:${password}`);
        state.auth = token;
        
        // Primero probar la conexión
        console.log('Probando conexión...');
        const testResponse = await fetch(`${state.baseUrl}/health`);
        console.log('Respuesta health:', testResponse.status);
        
        if (!testResponse.ok) {
            throw new Error('No se puede conectar al servidor');
        }
        
        // Luego intentar autenticar y obtener datos de usuario
        console.log('Cargando productos...');
        await loadProductos();
        
        // Obtener información del usuario incluyendo rol
        console.log('Obteniendo información del usuario...');
        const userInfo = await apiFetch('/auth/me');
        state.userRole = userInfo.rol;
        localStorage.setItem('userRole', userInfo.rol);
        
        // Si todo salió bien, guardar credenciales
        localStorage.setItem('apiUrl', state.baseUrl);
        localStorage.setItem('authToken', token);
        
        selectors.status.textContent = `Conectado. ${state.productos.length} productos cargados.`;
        selectors.userRole.textContent = `Rol: ${state.userRole}`;
        selectors.userRole.style.display = 'block';
        
        // Actualizar interfaz según rol
        updateUIForRole();
        
        console.log('Autenticación exitosa');
    } catch (error) {
        console.error('Error en autenticación:', error);
        selectors.status.textContent = `Error: ${error.message}`;
        state.auth = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userRole');
    }
});

async function loadProductos() {
    try {
        const data = await apiFetch('/catalog/productos');
        state.productos = data;
        // Poblar datalist para autocompletado
        selectors.skuList.innerHTML = data
            .map((p) => {
                // Mostrar solo las primeras 60 caracteres de la descripción
                const desc = p.descripcion ? p.descripcion.substring(0, 60) + (p.descripcion.length > 60 ? '...' : '') : p.sku;
                return `<option value="${p.sku}">${desc}</option>`;
            })
            .join('');
    } catch (error) {
        console.error('Error cargando productos:', error);
    }
}

async function loadLanded() {
    try {
        const rows = document.querySelectorAll('.sku-input-row');
        const skuQueries = Array.from(rows)
            .map(row => {
                const sku = row.querySelector('.sku-input').value.trim();
                const transporte = row.querySelector('.transporte-select').value.trim();
                return { sku, transporte };
            })
            .filter(q => q.sku);
        
        if (skuQueries.length === 0) {
            selectors.landedTable.innerHTML = '<tr><td colspan="6">Ingrese al menos un SKU para consultar</td></tr>';
            hideProductDetails();
            return;
        }

        // Hacer consultas a /pricing/listas en lugar de /pricing/landed
        const promises = skuQueries.map(query => {
            const params = new URLSearchParams();
            params.append('sku', query.sku);
            if (query.transporte) {
                params.append('transporte', query.transporte);
            }
            return apiFetch(`/pricing/listas?${params.toString()}`);
        });

        const results = await Promise.all(promises);
        const allData = results.flat();
        
        // Guardar datos para descarga
        state.landedData = allData;
        
        if (allData.length === 0) {
            selectors.landedTable.innerHTML = '<tr><td colspan="6">No se encontraron resultados</td></tr>';
            hideProductDetails();
            return;
        }

        // Renderizar según rol
        selectors.landedTable.innerHTML = allData
            .slice(0, 100)
            .map(row => renderPriceRow(row))
            .join('');
        
        // Mostrar detalles de los productos consultados
        const uniqueSkus = [...new Set(skuQueries.map(q => q.sku))];
        if (uniqueSkus.length > 0) {
            showProductDetails(uniqueSkus);
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
        <select class="transporte-select">
            <option value="">Ambos transportes</option>
            <option value="Maritimo">Marítimo</option>
            <option value="Aereo">Aéreo</option>
        </select>
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
            <select class="transporte-select">
                <option value="">Ambos transportes</option>
                <option value="Maritimo">Marítimo</option>
                <option value="Aereo">Aéreo</option>
            </select>
            <button class="icon-btn add-sku" title="Agregar otro SKU">+</button>
        </div>
    `;
    selectors.landedTable.innerHTML = '';
    hideProductDetails();
}

function formatCurrency(value) {
    return (value ?? 0).toLocaleString('es-MX', { 
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatPercentage(value) {
    const pct = (value ?? 0) * 100;
    return pct.toFixed(2) + '%';
}

// Nueva función: Actualizar UI según rol del usuario
function updateUIForRole() {
    const role = state.userRole || 'Vendedor';
    const adminGerenCols = document.querySelectorAll('.admin-gerencia');
    
    // Mostrar columnas de costos para todos EXCEPTO Vendedor
    if (role === 'Vendedor') {
        adminGerenCols.forEach(col => col.style.display = 'none');
    } else {
        adminGerenCols.forEach(col => col.style.display = 'table-cell');
    }
    
    // Configurar UI según rol
    if (role === 'Vendedor') {
        document.getElementById('section-title').textContent = 'Mi Lista de Precios';
        document.getElementById('section-description').textContent = 'Precios autorizados para cotización (90% a 65% sobre Mark-up)';
        
        // Mostrar sección de solicitud de autorización
        document.getElementById('solicitar-autorizacion-section').style.display = 'block';
        document.getElementById('mis-solicitudes-section').style.display = 'block';
        document.getElementById('pendientes-section').style.display = 'none';
        
        loadMisSolicitudes();
    } else if (role === 'Gerencia_Comercial') {
        document.getElementById('section-title').textContent = 'Lista de Precios Gerencia Comercial';
        document.getElementById('section-description').textContent = 'Costos completos y precios autorizados (25% descuento desde Precio Máximo)';
        
        // Mostrar solicitud de autorización y pendientes
        document.getElementById('solicitar-autorizacion-section').style.display = 'block';
        document.getElementById('mis-solicitudes-section').style.display = 'block';
        document.getElementById('pendientes-section').style.display = 'block';
        document.getElementById('procesadas-section').style.display = 'block';
        
        loadMisSolicitudes();
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Subdireccion') {
        document.getElementById('section-title').textContent = 'Lista de Precios Subdirección';
        document.getElementById('section-description').textContent = 'Costos completos y precios autorizados (30% descuento)';
        
        // Puede solicitar y ver pendientes
        document.getElementById('solicitar-autorizacion-section').style.display = 'block';
        document.getElementById('mis-solicitudes-section').style.display = 'block';
        document.getElementById('pendientes-section').style.display = 'block';
        document.getElementById('procesadas-section').style.display = 'block';
        
        loadMisSolicitudes();
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Direccion') {
        document.getElementById('section-title').textContent = 'Lista de Precios Dirección';
        document.getElementById('section-description').textContent = 'Costos completos y precios autorizados (35% descuento)';
        
        // Solo ver pendientes, no puede solicitar
        document.getElementById('solicitar-autorizacion-section').style.display = 'none';
        document.getElementById('mis-solicitudes-section').style.display = 'none';
        document.getElementById('pendientes-section').style.display = 'block';
        document.getElementById('procesadas-section').style.display = 'block';
        
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Gerencia') {
        document.getElementById('section-title').textContent = 'Lista de Precios Gerencia';
        document.getElementById('section-description').textContent = 'Costos completos y precios autorizados (40% a 10% sobre Mark-up)';
        
        // Solo ver pendientes, no puede solicitar
        document.getElementById('solicitar-autorizacion-section').style.display = 'none';
        document.getElementById('mis-solicitudes-section').style.display = 'none';
        document.getElementById('pendientes-section').style.display = 'block';
        document.getElementById('procesadas-section').style.display = 'block';
        
        loadPendientes();
        loadProcesadas();
    } else {
        // Admin puede ver todo
        document.getElementById('section-title').textContent = 'Lista de Precios - Vista Administrativa';
        document.getElementById('section-description').textContent = 'Todas las listas de precios y costos completos';
        
        // Admin puede ver pendientes
        document.getElementById('solicitar-autorizacion-section').style.display = 'none';
        document.getElementById('mis-solicitudes-section').style.display = 'none';
        document.getElementById('pendientes-section').style.display = 'block';
        document.getElementById('procesadas-section').style.display = 'block';
        
        loadPendientes();
        loadProcesadas();
    }
}

// Nueva función: Renderizar fila según rol
function renderPriceRow(row) {
    const role = state.userRole || 'Vendedor';
    
    let precioMax, precioMin;
    
    if (role === 'Vendedor') {
        precioMax = row.precio_maximo;
        precioMin = row.precio_vendedor_min;
    } else if (role === 'Gerencia_Comercial') {
        precioMax = row.precio_maximo;
        precioMin = row.precio_gerente_com_min;
    } else if (role === 'Subdireccion') {
        precioMax = row.precio_maximo;
        precioMin = row.precio_subdireccion_min;
    } else if (role === 'Direccion') {
        precioMax = row.precio_maximo;
        precioMin = row.precio_direccion_min;
    } else {
        // Admin ve precio máximo y mínimo absoluto
        precioMax = row.precio_maximo;
        precioMin = row.precio_direccion_min;
    }
    
    let html = `
        <tr>
            <td>${row.sku}</td>
            <td>${row.transporte}</td>`;
    
    // Mostrar costos completos para roles administrativos (todos excepto Vendedor)
    if (role !== 'Vendedor') {
        html += `
            <td class="admin-gerencia">${formatCurrency(row.costo_base_mxn)}</td>
            <td class="admin-gerencia">${formatPercentage(row.flete_pct)}</td>
            <td class="admin-gerencia">${formatPercentage(row.seguro_pct)}</td>
            <td class="admin-gerencia">${formatPercentage(row.arancel_pct)}</td>
            <td class="admin-gerencia">${formatPercentage(row.dta_pct)}</td>
            <td class="admin-gerencia">${formatPercentage(row.honorarios_aduanales_pct)}</td>
            <td class="admin-gerencia">${formatCurrency(row.landed_cost_mxn)}</td>
            <td class="admin-gerencia">${formatCurrency(row.precio_base_mxn)}</td>`;
    }
    
    html += `
            <td class="price-col">${formatCurrency(precioMax)}</td>
            <td class="price-col">${formatCurrency(precioMin)}</td>
        </tr>`;
    
    return html;
}

function downloadExcel() {
    if (state.landedData.length === 0) {
        alert('No hay datos para descargar. Realiza una consulta primero.');
        return;
    }

    const role = state.userRole || 'Vendedor';
    
    // Headers según rol - INCLUIR DETALLES DE PRODUCTOS
    let headers, rows;
    
    if (role === 'Vendedor') {
        headers = ['SKU', 'Descripción', 'Proveedor', 'Categoría', 'Transporte', 'Precio Máximo', 'Precio Mínimo'];
        rows = state.landedData.map(row => {
            const producto = state.productos.find(p => p.sku === row.sku) || {};
            return [
                row.sku,
                producto.descripcion || '',
                producto.proveedor || '',
                producto.categoria || '',
                row.transporte,
                (row.precio_maximo ?? 0).toFixed(2),
                (row.precio_vendedor_min ?? 0).toFixed(2)
            ];
        });
    } else if (role === 'Gerencia_Comercial') {
        headers = ['SKU', 'Descripción', 'Proveedor', 'Categoría', 'Transporte', 'Precio Máximo', 'Precio Mínimo'];
        rows = state.landedData.map(row => {
            const producto = state.productos.find(p => p.sku === row.sku) || {};
            return [
                row.sku,
                producto.descripcion || '',
                producto.proveedor || '',
                producto.categoria || '',
                row.transporte,
                (row.precio_maximo ?? 0).toFixed(2),
                (row.precio_gerente_com_min ?? 0).toFixed(2)
            ];
        });
    } else if (role === 'Subdireccion' || role === 'Direccion' || role === 'Gerencia') {
        headers = ['SKU', 'Descripción', 'Proveedor', 'Categoría', 'Origen', 'Transporte', 
                   'Costo Base MXN', 'Flete %', 'Seguro %', 'Arancel %', 
                   'DTA %', 'Hon. Aduanales %', 'Landed Cost', 'Mark-up Base', 'Precio Máximo', 'Precio Mínimo'];
        rows = state.landedData.map(row => {
            const producto = state.productos.find(p => p.sku === row.sku) || {};
            const precioMin = role === 'Subdireccion' ? row.precio_subdireccion_min : 
                             role === 'Direccion' ? row.precio_direccion_min : 
                             row.precio_gerente_com_min;
            return [
                row.sku,
                producto.descripcion || '',
                producto.proveedor || '',
                producto.categoria || '',
                producto.origen || '',
                row.transporte,
                (row.costo_base_mxn ?? 0).toFixed(2),
                ((row.flete_pct ?? 0) * 100).toFixed(2),
                ((row.seguro_pct ?? 0) * 100).toFixed(2),
                ((row.arancel_pct ?? 0) * 100).toFixed(2),
                ((row.dta_pct ?? 0) * 100).toFixed(2),
                ((row.honorarios_aduanales_pct ?? 0) * 100).toFixed(2),
                (row.landed_cost_mxn ?? 0).toFixed(2),
                (row.precio_base_mxn ?? 0).toFixed(2),
                (row.precio_maximo ?? 0).toFixed(2),
                (precioMin ?? 0).toFixed(2)
            ];
        });
    } else {
        // Admin ve todo
        headers = ['SKU', 'Descripción', 'Proveedor', 'Categoría', 'Origen', 'Transporte',
                   'Costo Base MXN', 'Flete %', 'Seguro %', 'Arancel %', 
                   'DTA %', 'Hon. Aduanales %', 'Landed Cost', 'Mark-up Base',
                   'Precio Máximo', 'Vendedor Min', 'Ger.Com Min', 'Subdir Min', 'Dirección Min'];
        rows = state.landedData.map(row => {
            const producto = state.productos.find(p => p.sku === row.sku) || {};
            return [
                row.sku,
                producto.descripcion || '',
                producto.proveedor || '',
                producto.categoria || '',
                producto.origen || '',
                row.transporte,
                (row.costo_base_mxn ?? 0).toFixed(2),
                ((row.flete_pct ?? 0) * 100).toFixed(2),
                ((row.seguro_pct ?? 0) * 100).toFixed(2),
                ((row.arancel_pct ?? 0) * 100).toFixed(2),
                ((row.dta_pct ?? 0) * 100).toFixed(2),
                ((row.honorarios_aduanales_pct ?? 0) * 100).toFixed(2),
                (row.landed_cost_mxn ?? 0).toFixed(2),
                (row.precio_base_mxn ?? 0).toFixed(2),
                (row.precio_maximo ?? 0).toFixed(2),
                (row.precio_vendedor_min ?? 0).toFixed(2),
                (row.precio_gerente_com_min ?? 0).toFixed(2),
                (row.precio_subdireccion_min ?? 0).toFixed(2),
                (row.precio_direccion_min ?? 0).toFixed(2)
            ];
        });
    }

    // Generar CSV
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // Crear Blob y descargar
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    
    link.setAttribute('href', url);
    link.setAttribute('download', `Landed_Cost_${timestamp}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    selectors.status.textContent = `✅ Archivo descargado: Landed_Cost_${timestamp}.csv`;
}

// Event listeners
selectors.clearSkusBtn.addEventListener('click', clearAllSkus);
selectors.downloadExcelBtn.addEventListener('click', downloadExcel);

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

// =====================================
// FUNCIONALIDAD DE AUTORIZACIONES
// =====================================

// Formulario de solicitud
document.getElementById('solicitud-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const statusEl = document.getElementById('solicitud-status');
    const data = {
        sku: document.getElementById('sol-sku').value.trim(),
        transporte: document.getElementById('sol-transporte').value,
        precio_propuesto: parseFloat(document.getElementById('sol-precio').value),
        cliente: document.getElementById('sol-cliente').value.trim() || null,
        cantidad: parseInt(document.getElementById('sol-cantidad').value) || null,
        justificacion: document.getElementById('sol-justificacion').value.trim()
    };
    
    try {
        statusEl.textContent = 'Enviando solicitud...';
        statusEl.style.color = '#ffc107';
        
        const result = await apiFetch('/autorizaciones/solicitar', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        statusEl.textContent = `✅ Solicitud enviada. ID: ${result.id}`;
        statusEl.style.color = '#4caf50';
        
        // Limpiar formulario
        e.target.reset();
        
        // Recargar lista de mis solicitudes
        loadMisSolicitudes();
    } catch (error) {
        statusEl.textContent = `❌ Error: ${error.message}`;
        statusEl.style.color = '#f44336';
    }
});

// Cargar solicitudes pendientes
async function loadPendientes() {
    try {
        const solicitudes = await apiFetch('/autorizaciones/pendientes');
        const tbody = document.querySelector('#pendientes-table tbody');
        
        if (!solicitudes || solicitudes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color: var(--muted);">No hay solicitudes pendientes</td></tr>';
            return;
        }
        
        tbody.innerHTML = solicitudes.map(s => `
            <tr>
                <td>${s.solicitante || 'N/A'}</td>
                <td>${s.sku}</td>
                <td>${s.transporte}</td>
                <td>$${s.precio_minimo_actual.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>$${s.precio_propuesto.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>${s.descuento_adicional_pct.toFixed(2)}%</td>
                <td>${s.cliente || '-'}</td>
                <td>${s.cantidad || '-'}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${s.justificacion}">${s.justificacion}</td>
                <td>${new Date(s.fecha_solicitud).toLocaleDateString('es-MX')}</td>
                <td class="action-buttons">
                    <button class="btn-aprobar" onclick="aprobarSolicitud(${s.id})">✓ Aprobar</button>
                    <button class="btn-rechazar" onclick="rechazarSolicitud(${s.id})">✗ Rechazar</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando pendientes:', error);
    }
}

// Cargar mis solicitudes
async function loadMisSolicitudes() {
    try {
        const solicitudes = await apiFetch('/autorizaciones/mis-solicitudes');
        const tbody = document.querySelector('#mis-solicitudes-table tbody');
        
        if (!solicitudes || solicitudes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color: var(--muted);">No has creado solicitudes</td></tr>';
            return;
        }
        
        tbody.innerHTML = solicitudes.map(s => `
            <tr>
                <td>${s.sku}</td>
                <td>${s.transporte}</td>
                <td>$${s.precio_propuesto.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>${s.cliente || '-'}</td>
                <td class="estado-${s.estado.toLowerCase()}">${s.estado}</td>
                <td>${s.autorizador || '-'}</td>
                <td>${new Date(s.fecha_solicitud).toLocaleDateString('es-MX')}</td>
                <td>${s.fecha_respuesta ? new Date(s.fecha_respuesta).toLocaleDateString('es-MX') : '-'}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${s.comentarios_autorizador || ''}">${s.comentarios_autorizador || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando mis solicitudes:', error);
    }
}

// Cargar solicitudes procesadas (aprobadas o rechazadas por el usuario)
async function loadProcesadas() {
    try {
        const solicitudes = await apiFetch('/autorizaciones/procesadas');
        const tbody = document.querySelector('#procesadas-table tbody');
        
        if (!solicitudes || solicitudes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color: var(--muted);">No has procesado solicitudes</td></tr>';
            return;
        }
        
        tbody.innerHTML = solicitudes.map(s => `
            <tr>
                <td>${s.solicitante || 'N/A'}</td>
                <td>${s.sku}</td>
                <td>${s.transporte}</td>
                <td>$${s.precio_propuesto.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
                <td>${s.cliente || '-'}</td>
                <td class="estado-${s.estado.toLowerCase()}">${s.estado}</td>
                <td>${new Date(s.fecha_solicitud).toLocaleDateString('es-MX')}</td>
                <td>${s.fecha_respuesta ? new Date(s.fecha_respuesta).toLocaleDateString('es-MX') : '-'}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${s.comentarios_autorizador || ''}">${s.comentarios_autorizador || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando solicitudes procesadas:', error);
    }
}

// Aprobar solicitud
async function aprobarSolicitud(id) {
    const comentarios = prompt('Comentarios (opcional):');
    if (comentarios === null) return; // Usuario canceló
    
    try {
        await apiFetch(`/autorizaciones/${id}/aprobar`, {
            method: 'PUT',
            body: JSON.stringify({ comentarios })
        });
        
        alert('✅ Solicitud aprobada');
        loadPendientes();
        loadProcesadas();
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Rechazar solicitud
async function rechazarSolicitud(id) {
    const comentarios = prompt('Motivo del rechazo (opcional):');
    if (comentarios === null) return; // Usuario canceló
    
    try {
        await apiFetch(`/autorizaciones/${id}/rechazar`, {
            method: 'PUT',
            body: JSON.stringify({ comentarios })
        });
        
        alert('❌ Solicitud rechazada');
        loadPendientes();
        loadProcesadas();
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Exponer funciones globalmente
window.aprobarSolicitud = aprobarSolicitud;
window.rechazarSolicitud = rechazarSolicitud;

// Botones de actualizar
document.getElementById('refresh-pendientes')?.addEventListener('click', loadPendientes);
document.getElementById('refresh-procesadas')?.addEventListener('click', loadProcesadas);
document.getElementById('refresh-mis-solicitudes')?.addEventListener('click', loadMisSolicitudes);

if (state.auth) {
    loadProductos();
}

// Service Worker desactivado temporalmente
// if ('serviceWorker' in navigator) {
//     window.addEventListener('load', () => {
//         navigator.serviceWorker.register('./sw.js').catch((err) => console.warn('SW error', err));
//     });
// }
