const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        state.auth = null;
        state.userRole = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userRole');
        selectors.status.textContent = 'Sesión cerrada correctamente.';
        selectors.userRole.style.display = 'none';
        selectors.connectBtn.style.display = '';
        logoutBtn.style.display = 'none';
        // Limpiar tablas y ocultar secciones sensibles
        if (selectors.landedTable) selectors.landedTable.innerHTML = '';
        if (selectors.productDetailsCard) selectors.productDetailsCard.style.display = 'none';
        // Ocultar secciones de autorizaciones y precios
        document.querySelectorAll('.card').forEach(card => {
            if (!card.classList.contains('login-card')) {
                card.style.display = 'none';
            }
        });
        // Mostrar solo login
        document.querySelector('.login-card').style.display = '';
        showToast('Sesión cerrada.', 'success');
    });
}
// --- Toast Notification System ---
function showToast(message, type = 'info', duration = 3500) {
    let toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '32px',
        right: '32px',
        background: type === 'error' ? '#d32f2f' : type === 'success' ? '#388e3c' : '#1976d2',
        color: 'white',
        padding: '14px 24px',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 9999,
        fontSize: '1rem',
        opacity: 0.95,
        transition: 'opacity 0.3s',
        pointerEvents: 'none',
    });
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = 0;
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

const getDefaultApiUrl = () => {
    // Detecta si está corriendo en Docker (hostname no es localhost ni 127.0.0.1)
    if (window.location.hostname === 'frontend' || window.location.hostname === '0.0.0.0') {
        return 'http://backend:8000';
    }
    // Si está en localhost o cualquier otro entorno
    return 'http://localhost:8000';
};

const state = {
    baseUrl: localStorage.getItem('apiUrl') || getDefaultApiUrl(),
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
            Authorization: `Bearer ${state.auth}`,
            ...(options.headers || {}),
        },
    });
    if (!response.ok) {
        let detail = '';
        let help = '';
        try {
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                const err = await response.json();
                detail = err.detail || JSON.stringify(err);
            } else {
                detail = await response.text();
            }
            help = response.headers.get('x-help') || '';
        } catch (e) {
            detail = 'Error inesperado al procesar la respuesta del servidor.';
        }
        let msg = `Error ${response.status}: ${detail}`;
        if (help) msg += `\nSugerencia: ${help}`;
        showToast(msg, 'error');
        throw new Error(msg);
    }
    return response.json();
}

selectors.connectBtn.addEventListener('click', async () => {
    // Mostrar todas las secciones tras login
    document.querySelectorAll('.card').forEach(card => {
        card.style.display = '';
    });
    console.log('Botón clickeado');
    try {
        selectors.status.textContent = 'Conectando...';
        selectors.connectBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = '';
        state.baseUrl = selectors.apiUrl.value.trim();
        const username = selectors.username.value.trim();
        const password = selectors.password.value;

        console.log('URL:', state.baseUrl);
        console.log('Usuario:', username);

        // Health check antes de login
        const healthResp = await fetch(`${state.baseUrl}/health`);
        if (!healthResp.ok) {
            throw new Error('No se pudo conectar al backend. Verifica la URL y que el backend esté corriendo.');
        }

        if (!username || !password) {
            selectors.status.textContent = 'Ingrese usuario y contraseña';
            selectors.connectBtn.style.display = '';
            return;
        }

        // Login JWT
        const loginResponse = await fetch(`${state.baseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password })
        });
        if (!loginResponse.ok) {
            const err = await loginResponse.json().catch(() => ({}));
            throw new Error(err.detail || 'Credenciales inválidas');
        }
        const { access_token } = await loginResponse.json();
        state.auth = access_token;
        localStorage.setItem('authToken', access_token);

        // Obtener productos y rol
        await loadProductos();
        showToast('Productos cargados correctamente.', 'success');
        const userInfo = await apiFetch('/auth/me');
        state.userRole = userInfo.rol;
        localStorage.setItem('userRole', userInfo.rol);

        localStorage.setItem('apiUrl', state.baseUrl);
        selectors.status.textContent = `Conectado. ${state.productos.length} productos cargados.`;
        selectors.userRole.textContent = `Rol: ${state.userRole}`;
        console.log('[LOGIN] Rol recibido:', state.userRole);
        selectors.userRole.style.display = 'block';
        console.log('[LOGIN] #user-role display:', selectors.userRole.style.display);
        selectors.connectBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = '';

        updateUIForRole();
        showToast('Inicio de sesión exitoso.', 'success');
        console.log('Autenticación exitosa');
        if (state.userRole === 'Vendedor') {
            const aprobacionesSection = document.getElementById('procesadas-section');
            if (aprobacionesSection) aprobacionesSection.style.display = 'none';
        } else {
            const aprobacionesSection = document.getElementById('procesadas-section');
            if (aprobacionesSection) aprobacionesSection.style.display = '';
        }
    } catch (error) {
        console.error('Error en autenticación:', error);
        selectors.status.textContent = `Error: ${error.message}`;
        showToast(error.message, 'error');
        state.auth = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userRole');
        selectors.connectBtn.style.display = '';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
});

// --- DEBUG: Mostrar catálogo completo en consola al cargar productos ---
async function loadProductos() {
    try {
        const data = await apiFetch('/catalog/productos');
        state.productos = data;
        console.log('[DEBUG] Catálogo productos:', data); // <-- Línea de depuración
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
        showToast(error.message, 'error');
    }
}
// --- FIN DEBUG ---

async function loadLanded() {
    try {
        const rows = document.querySelectorAll('.sku-input-row');
        const skuQueries = Array.from(rows)
            .map(row => {
                const sku = row.querySelector('.sku-input').value.trim();
                const cantidad = parseInt(row.querySelector('.cantidad-input')?.value) || 1;
                return { sku, cantidad };
            })
            .filter(q => q.sku);

        if (skuQueries.length === 0) {
            selectors.landedTable.innerHTML = '<tr><td colspan="8">Ingrese al menos un SKU para consultar</td></tr>';
            hideProductDetails();
            return;
        }

        // --- Mantener montos propuestos previos ---
        const prevRows = state.rowsCotizacion || [];
        // Consultar precios por SKU
        const promises = skuQueries.map(query => {
            const params = new URLSearchParams();
            params.append('sku', query.sku);
            return apiFetch(`/pricing/listas?${params.toString()}`);
        });

        const results = await Promise.all(promises);
        // Emparejar cantidad con cada resultado
        let allData = results.map((data, i) => {
            const cantidad = skuQueries[i].cantidad;
            return data.map(row => ({ ...row, cantidad }));
        }).flat();

        // --- Restaurar montos propuestos previos por SKU ---
        allData = allData.map(row => {
            const prev = prevRows.find(r => r.sku === row.sku);
            if (prev && prev.monto_propuesto !== undefined) {
                return { ...row, monto_propuesto: prev.monto_propuesto };
            }
            return row;
        });

        state.landedData = allData;

        if (allData.length === 0) {
            selectors.landedTable.innerHTML = '<tr><td colspan="8">No se encontraron resultados</td></tr>';
            hideProductDetails();
            return;
        }

        // Agrupar por SKU y categoría, y mostrar solo el registro con menor precio mínimo
        const agrupados = {};
        allData.forEach(row => {
            const key = row.sku + '|' + (row.categoria || '');
            if (!agrupados[key] || (row.precio_vendedor_min < agrupados[key].precio_vendedor_min)) {
                agrupados[key] = row;
            }
        });
        const rowsToShow = Object.values(agrupados);
        selectors.landedTable.innerHTML = rowsToShow
            .slice(0, 100)
            .map(row => renderPriceRow(row))
            .join('');
        // Forzar que los inputs de monto propuesto sean editables y no tengan valor fijo
        setTimeout(() => {
            document.querySelectorAll('.monto-propuesto-input').forEach(input => {
                input.removeAttribute('readonly');
                input.removeAttribute('disabled');
                input.type = 'text';
                input.value = input.value;
                input.style.background = '';
                input.style.pointerEvents = 'auto';
                input.style.userSelect = 'auto';
                input.tabIndex = 0;
                input.onfocus = function() { this.select(); };
            });
        }, 0);
        // Guardar para cotización
        state.rowsCotizacion = rowsToShow;

        const uniqueSkus = [...new Set(skuQueries.map(q => q.sku))];
        if (uniqueSkus.length > 0) {
            showProductDetails(uniqueSkus);
        } else {
            hideProductDetails();
        }
    } catch (error) {
        selectors.status.textContent = error.message;
        showToast(error.message, 'error');
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
        <div class="cantidad-stepper">
            <button type="button" class="stepper-btn stepper-minus">−</button>
            <input type="number" class="cantidad-input" min="1" value="1" style="width:60px" placeholder="Cantidad">
            <button type="button" class="stepper-btn stepper-plus">+</button>
        </div>
        <button class="icon-btn remove" title="Quitar SKU">×</button>
    `;
    selectors.skuInputsContainer.appendChild(newRow);
    attachStepperEvents(newRow);
}

function attachStepperEvents(row) {
    const minusBtn = row.querySelector('.stepper-minus');
    const plusBtn = row.querySelector('.stepper-plus');
    const input = row.querySelector('.cantidad-input');
    // Forzar habilitación
    if (input) {
        input.removeAttribute('readonly');
        input.removeAttribute('disabled');
        input.style.pointerEvents = 'auto';
        input.style.userSelect = 'auto';
    }
    if (minusBtn) {
        minusBtn.disabled = false;
        minusBtn.style.pointerEvents = 'auto';
        minusBtn.addEventListener('click', () => {
            let val = parseInt(input.value) || 1;
            if (val > 1) input.value = val - 1;
            input.dispatchEvent(new Event('input'));
        });
    }
    if (plusBtn) {
        plusBtn.disabled = false;
        plusBtn.style.pointerEvents = 'auto';
        plusBtn.addEventListener('click', () => {
            let val = parseInt(input.value) || 1;
            input.value = val + 1;
            input.dispatchEvent(new Event('input'));
        });
    }
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
            <div class="cantidad-stepper">
                <button type="button" class="stepper-btn stepper-minus">−</button>
                <input type="number" class="cantidad-input" min="1" value="1" style="width:60px" placeholder="Cantidad">
                <button type="button" class="stepper-btn stepper-plus">+</button>
            </div>
            <button class="icon-btn add-sku" title="Agregar otro SKU">+</button>
        </div>
    `;
    // Adjuntar eventos a los steppers
    // Adjuntar eventos a los steppers solo si no existen
    document.querySelectorAll('.sku-input-row').forEach(row => {
        attachStepperEvents(row);
    });
    selectors.landedTable.innerHTML = '';
    hideProductDetails();
}

function formatCurrency(value) {
    // Redondear a entero
    return Math.round(value ?? 0).toLocaleString('es-MX', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
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
    const downloadBtn = document.getElementById('download-excel');
    const sectionTitle = document.getElementById('section-title');
    const sectionDesc = document.getElementById('section-description');
    const solicitarAutSection = document.getElementById('solicitar-autorizacion-section');
    const misSolicitudesSection = document.getElementById('mis-solicitudes-section');
    const pendientesSection = document.getElementById('pendientes-section');
    const procesadasSection = document.getElementById('procesadas-section');

    if (role === 'Vendedor') {
        if (sectionTitle) sectionTitle.textContent = 'Mi Lista de Precios';
        if (sectionDesc) sectionDesc.textContent = 'Precios autorizados: 20% descuento desde Precio Máximo';
        // Ocultar y deshabilitar botón de descarga Excel
        if (downloadBtn) {
            downloadBtn.style.display = 'none';
            downloadBtn.disabled = true;
        }
        // Mostrar sección de solicitud de autorización
        if (solicitarAutSection) solicitarAutSection.style.display = 'block';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'block';
        if (pendientesSection) pendientesSection.style.display = 'none';
        loadMisSolicitudes();
    } else if (role === 'Gerencia_Comercial') {
        // Mostrar botón para otros roles
        if (downloadBtn) {
            downloadBtn.style.display = '';
            downloadBtn.disabled = false;
        }
        if (sectionTitle) sectionTitle.textContent = 'Lista de Precios Gerencia Comercial';
        if (sectionDesc) sectionDesc.textContent = 'Costos completos y precios autorizados (25% descuento desde Precio Máximo)';
        if (solicitarAutSection) solicitarAutSection.style.display = 'block';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'block';
        if (pendientesSection) pendientesSection.style.display = 'block';
        if (procesadasSection) procesadasSection.style.display = 'block';
        loadMisSolicitudes();
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Subdireccion') {
        if (sectionTitle) sectionTitle.textContent = 'Lista de Precios Subdirección';
        if (sectionDesc) sectionDesc.textContent = 'Costos completos y precios autorizados (30% descuento)';
        if (solicitarAutSection) solicitarAutSection.style.display = 'block';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'block';
        if (pendientesSection) pendientesSection.style.display = 'block';
        if (procesadasSection) procesadasSection.style.display = 'block';
        loadMisSolicitudes();
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Direccion') {
        if (sectionTitle) sectionTitle.textContent = 'Lista de Precios Dirección';
        if (sectionDesc) sectionDesc.textContent = 'Costos completos y precios autorizados (35% descuento)';
        if (solicitarAutSection) solicitarAutSection.style.display = 'none';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'none';
        if (pendientesSection) pendientesSection.style.display = 'block';
        if (procesadasSection) procesadasSection.style.display = 'block';
        loadPendientes();
        loadProcesadas();
    } else if (role === 'Gerencia') {
        if (sectionTitle) sectionTitle.textContent = 'Lista de Precios Gerencia';
        if (sectionDesc) sectionDesc.textContent = 'Costos completos y vista de todas las autorizaciones';
        if (solicitarAutSection) solicitarAutSection.style.display = 'none';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'none';
        if (pendientesSection) pendientesSection.style.display = 'block';
        if (procesadasSection) procesadasSection.style.display = 'block';
        loadPendientes();
        loadProcesadas();
    } else {
        // Admin puede ver todo
        if (sectionTitle) sectionTitle.textContent = 'Lista de Precios - Vista Administrativa';
        if (sectionDesc) sectionDesc.textContent = 'Todas las listas de precios y costos completos';
        if (solicitarAutSection) solicitarAutSection.style.display = 'none';
        if (misSolicitudesSection) misSolicitudesSection.style.display = 'none';
        if (pendientesSection) pendientesSection.style.display = 'block';
        if (procesadasSection) procesadasSection.style.display = 'block';
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
        precioMax = row.precio_maximo;
        precioMin = row.precio_direccion_min;
    }
    const montoPropuestoId = `monto-propuesto-${row.sku}`;
    // Usar el monto propuesto previo si existe
    let montoPropuesto = row.monto_propuesto !== undefined ? row.monto_propuesto : '';
    let html = `
        <tr>
            <td>${row.sku}</td>
            <td>${row.cantidad}</td>`;
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
    // En renderPriceRow, si no hay monto propuesto, dejar Total Negociado vacío
    let totalNegociado = '';
    if (montoPropuesto && !isNaN(parseFloat(montoPropuesto))) {
        totalNegociado = formatCurrency(parseFloat(montoPropuesto) * row.cantidad);
    }
    html += `
        <td class="price-col">${formatCurrency(precioMax)}</td>
        <td class="price-col">
            <input type="text" class="monto-propuesto-input" id="${montoPropuestoId}" value="${montoPropuesto}" style="width:100px;" autocomplete="off" placeholder="Escribe monto">
        </td>
        <td class="price-col">${formatCurrency(precioMin)}</td>
        <td class="price-col">${formatCurrency(precioMax * row.cantidad)}</td>
        <td class="price-col" id="total-negociado-${row.sku}">${totalNegociado}</td>
        <td class="price-col">${formatCurrency(precioMin * row.cantidad)}</td>
        <td class="price-col">
            <button class="pdf-cotizar-btn" data-sku="${row.sku}">PDF Cotización</button>
        </td>
    </tr>`;
    return html;
}


// Evento para generar y descargar PDF de cotización (multi-SKU)
document.addEventListener('click', async function(e) {
    if (e.target.classList.contains('pdf-cotizar-btn')) {
        // Leer el valor del campo cliente
        state.cliente = document.getElementById('input-cliente')?.value || '';

        // Tomar todos los SKUs cotizados actualmente
        const rows = (state.rowsCotizacion || []);
        if (!rows.length) {
            showToast('No hay productos para cotizar.', 'error');
            return;
        }
        // Construir payload multi-SKU
        const items = rows.map(row => {
            // Normalizar SKU para evitar problemas de espacios/casos
            const skuBuscado = (row.sku || '').toString().trim().toUpperCase();
            const prod = (state.productos || []).find(p => (p.sku || '').toString().trim().toUpperCase() === skuBuscado) || {};
            let descripcion = typeof prod.descripcion === 'string' && prod.descripcion.trim() ? prod.descripcion : '-';
            let proveedor = typeof prod.proveedor === 'string' && prod.proveedor.trim() ? prod.proveedor : '-';
            let origen = typeof prod.origen === 'string' && prod.origen.trim() ? prod.origen : '-';
            // Asegurar que monto_propuesto sea numérico
            let montoPropuesto = row.monto_propuesto !== undefined && row.monto_propuesto !== null ? Number(row.monto_propuesto) : Number(row.precio_vendedor_min);
            return {
                sku: row.sku,
                descripcion,
                cantidad: row.cantidad || 1,
                precio_maximo: row.precio_maximo,
                precio_vendedor_min: row.precio_vendedor_min,
                monto_propuesto: montoPropuesto,
                logo_path: row.logo_path || null,
                proveedor,
                origen
            };
        });
        const payload = {
            cliente: state.cliente || '',
            items
        };
        console.log('Payload enviado a /cotizacion/pdf:', JSON.stringify(payload, null, 2));
        try {
            const response = await fetch(`${state.baseUrl}/cotizacion/pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${state.auth}`
                },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                showToast('Error al generar PDF', 'error');
                return;
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `cotizacion_multiSKU.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showToast('PDF generado y descargado.', 'success');
        } catch (err) {
            showToast('Error al descargar PDF: ' + err.message, 'error');
        }
    }
});

// Escuchar cambios en monto propuesto y actualizar total negociado
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('monto-propuesto-input')) {
        const input = e.target;
        const sku = input.id.replace('monto-propuesto-', '');
        const row = (state.rowsCotizacion || []).find(r => r.sku === sku);
        if (!row) return;
        let monto = input.value.replace(',', '.');
        row.monto_propuesto = monto; // Guardar el monto digitado
        // Actualizar total negociado en tiempo real
        const cantidad = Math.round(row.cantidad);
        let montoNum = parseFloat(monto);
        if (isNaN(montoNum)) montoNum = 0;
        const total = montoNum * cantidad;
        const totalCell = document.getElementById(`total-negociado-${sku}`);
        if (totalCell) totalCell.textContent = formatCurrency(total);
    }
    // Actualizar Total Negociado si cambia la cantidad
    if (e.target.classList.contains('cantidad-input')) {
        const rowDiv = e.target.closest('.sku-input-row');
        const skuInput = rowDiv.querySelector('.sku-input');
        const sku = skuInput.value.trim();
        const row = (state.rowsCotizacion || []).find(r => r.sku === sku);
        if (!row) return;
        let cantidad = Math.round(parseFloat(e.target.value) || 1);
        row.cantidad = cantidad;
        // Obtener el monto propuesto actual
        const montoInput = document.getElementById(`monto-propuesto-${sku}`);
        let monto = montoInput ? parseFloat(montoInput.value.replace(',', '.')) : 0;
        if (isNaN(monto)) monto = 0;
        if (montoInput) montoInput.value = monto;
        // Actualizar total negociado
        const total = Math.round(monto) * cantidad;
        const totalCell = document.getElementById(`total-negociado-${sku}`);
        if (totalCell) totalCell.textContent = formatCurrency(total);
    }
});

// ...evento duplicado eliminado...

// =====================================
// FUNCIONALIDAD DE AUTORIZACIONES
// =====================================

// Formulario de solicitud
document.getElementById('solicitud-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const statusEl = document.getElementById('solicitud-status');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    // Prevenir múltiples envíos
    if (submitBtn.disabled) return;
    submitBtn.disabled = true;
    
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
    } finally {
        // Re-habilitar botón después de 1 segundo
        setTimeout(() => {
            submitBtn.disabled = false;
        }, 1000);
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
        
        const role = state.userRole || '';
        if (!solicitudes || solicitudes.length === 0) {
            let msg = 'No has procesado solicitudes';
            if (["admin", "Direccion", "Subdireccion"].includes(role)) {
                msg = 'No hay solicitudes procesadas en el sistema';
            }
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color: var(--muted);">${msg}</td></tr>`;
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
        console.log('AprobarSolicitud: method=PUT, Authorization:', state.auth);
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
        console.log('RechazarSolicitud: method=PUT, Authorization:', state.auth);
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

// --- Timeout de sesión por inactividad ---
let lastActivity = Date.now(); // Declare and initialize lastActivity
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutos
document.addEventListener('click', () => lastActivity = Date.now());
document.addEventListener('keypress', () => lastActivity = Date.now());
setInterval(() => {
    if (state.auth && Date.now() - lastActivity > SESSION_TIMEOUT) {
        alert('Sesión expirada por inactividad. Por favor, inicia sesión nuevamente.');
        localStorage.removeItem('authToken');
        localStorage.removeItem('userRole');
        window.location.reload();
    }
}, 60000);
// --- Fin timeout de sesión ---

// --- EVENTOS PARA ACTUALIZAR COTIZACIÓN DINÁMICAMENTE ---
// Actualizar cotización al cambiar SKU o cantidad
// Llama loadLanded() cuando se edita un SKU o cantidad
// (Evita loops infinitos: loadLanded solo actualiza la tabla)

// Delegación de eventos para toda la interfaz de cotización
document.addEventListener('click', function(e) {
    // Botón + cantidad
    if (e.target.classList.contains('stepper-plus')) {
        const input = e.target.closest('.cantidad-stepper')?.querySelector('.cantidad-input');
        if (input) {
            let val = parseInt(input.value) || 1;
            input.value = val + 1;
            input.dispatchEvent(new Event('input'));
        }
    }
    // Botón - cantidad
    if (e.target.classList.contains('stepper-minus')) {
        const input = e.target.closest('.cantidad-stepper')?.querySelector('.cantidad-input');
        if (input) {
            let val = parseInt(input.value) || 1;
            if (val > 1) input.value = val - 1;
            input.dispatchEvent(new Event('input'));
        }
    }
    // Botón agregar SKU
    if (e.target.classList.contains('add-sku')) {
        addSkuInput();
        setTimeout(loadLanded, 100);
    }
    // Botón quitar SKU
    if (e.target.classList.contains('remove')) {
        removeSkuInput(e.target);
        setTimeout(loadLanded, 100);
    }
    // Botón Consultar
    if (e.target.matches('[data-action="load-landed"]')) {
        e.preventDefault();
        loadLanded();
    }
    // Botón Limpiar
    if (e.target.id === 'clear-skus') {
        clearAllSkus();
    }
});

// Actualizar cotización al cambiar SKU o cantidad
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('sku-input') || e.target.classList.contains('cantidad-input')) {
        loadLanded();
    }
});

// Cierre automático de cualquier bloque abierto (por si acaso)
// (No se agrega código funcional, solo se asegura el cierre de bloques)
