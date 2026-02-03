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
    dashboardInitialized: false,
};

// Timers para debounce por SKU cuando se escribe el monto propuesto
const debounceTimers = {};
// Pending authorization request context
let pendingAuthRequest = null;
// Mapeo de descuento máximo permitido por rol (en %)
const allowedDiscountByRole = {
    'Vendedor': 20,
    'Gerencia_Comercial': 25,
    'Subdireccion': 30,
    'Direccion': 35,
    'Gerencia': 40,
    'Admin': 100
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
    clienteInput: document.getElementById('input-cliente'),
    vendedorInput: document.getElementById('input-vendedor'),
    skuInputsContainer: document.getElementById('sku-inputs-container'),
    clearSkusBtn: document.getElementById('clear-skus'),
    downloadExcelBtn: document.getElementById('download-excel'),
    productDetailsCard: document.getElementById('product-details-card'),
    productDetails: document.getElementById('product-details'),
};


if (state.baseUrl) selectors.apiUrl.value = state.baseUrl;
if (state.auth) selectors.status.textContent = 'Sesión guardada (reautenticar si es necesario).';

// Inicializar UI: ocultar todas las tarjetas excepto el login al iniciar o recargar
function initLoginOnlyView() {
    document.querySelectorAll('.card').forEach(card => {
        if (!card.classList.contains('login-card')) {
            card.style.display = 'none';
        } else {
            card.style.display = '';
        }
    });
    // Estado inicial: probar conexión al backend y mostrar 'Sin conexión' si falla
    selectors.status.textContent = 'Comprobando conexión...';
    (async () => {
        try {
            const url = (selectors.apiUrl && selectors.apiUrl.value) ? selectors.apiUrl.value.trim() : state.baseUrl;
            const resp = await fetch(`${url}/health`, { method: 'GET' });
            if (!resp.ok) throw new Error('no-ok');
            // Backend responde, indicar que está disponible pero aún no autenticado
            selectors.status.textContent = 'Conectado (autenticar)';
        } catch (e) {
            selectors.status.textContent = 'Sin conexión';
        }
    })();
}

// Ejecutar inicialización de vista al cargar el script
initLoginOnlyView();

async function apiFetch(path, options = {}) {
    // No lanzar aquí si no hay sesión: permitir que endpoints públicos funcionen
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    if (state.auth) {
        headers.Authorization = `Bearer ${state.auth}`;
    }
    const response = await fetch(`${state.baseUrl}${path}`, {
        ...options,
        headers,
    });
    try {
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
            const msg = `Error ${response.status}: ${detail}` + (help ? `\nSugerencia: ${help}` : '');
            showToast(msg, 'error');
            throw new Error(msg);
        }
        // Some endpoints may return empty body
        const ct = response.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
            // return text for non-json responses
            return await response.text();
        }
        return await response.json();
    } catch (netErr) {
        // Network or parsing error
        const errMsg = netErr && netErr.message ? netErr.message : String(netErr);
        showToast('Error de red o respuesta inválida: ' + errMsg, 'error');
        throw netErr;
    }
}

selectors.connectBtn.addEventListener('click', async () => {
    // Mostrar todas las secciones tras login
    document.querySelectorAll('.card').forEach(card => {
        card.style.display = '';
    });
    // Mostrar indicador inmediato para que los tests E2E detecten el elemento
    if (selectors.userRole) {
        selectors.userRole.textContent = 'Rol: Conectando...';
        selectors.userRole.style.display = 'block';
    }
    // login button clicked
    try {
        selectors.status.textContent = 'Conectando...';
        selectors.connectBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = '';
        state.baseUrl = selectors.apiUrl.value.trim();
        const username = selectors.username.value.trim();
        const password = selectors.password.value;

        // connecting to URL and attempting login

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
        selectors.userRole.style.display = 'block';
        selectors.connectBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = '';

        updateUIForRole();
        showToast('Inicio de sesión exitoso.', 'success');
        // autenticación exitosa
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
        // catálogo productos cargado (debug logs removed)
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
    // Validar que el campo Cliente esté lleno antes de consultar
    const clienteValCheck = (document.getElementById('input-cliente')?.value || '').trim();
    if (!clienteValCheck) {
        showToast('Ingrese el nombre del Cliente antes de consultar SKUs.', 'error');
        const cli = document.getElementById('input-cliente');
        if (cli) {
            cli.focus();
            cli.classList.add('invalid-input');
            setTimeout(() => cli.classList.remove('invalid-input'), 1500);
        }
        return;
    }
    try {
        const rows = document.querySelectorAll('.sku-input-row');
        const skuQueries = Array.from(rows)
            .map(row => {
                    const sku = row.querySelector('.sku-input').value.trim();
                    const cantidad = parseInt(row.querySelector('.cantidad-input')?.value) || 1;
                    const transporte = row.querySelector('.transporte-select')?.value || 'Maritimo';
                    return { sku, cantidad, transporte };
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
            params.append('transporte', query.transporte || 'Maritimo');
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
            const base = prev && prev.monto_propuesto !== undefined ? { ...row, monto_propuesto: prev.monto_propuesto } : row;
            // carry over transporte choice if user previously selected it
            if (prev && prev.transporte) base.transporte = prev.transporte;
            return base;
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

// --- Autocomplete for Cliente and Vendedor (debounced) ---
function debounce(fn, wait){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),wait);}; }

async function fetchClientes(q){
    if(!q) return [];
    try{
        // use apiFetch so it includes auth header
        const res = await apiFetch(`/api/clientes?q=${encodeURIComponent(q)}&limit=10`);
        return res;
    }catch(e){
        return [];
    }
}

async function fetchVendedores(q){
    if(!q) return [];
    try{
        const res = await apiFetch(`/api/vendedores?q=${encodeURIComponent(q)}&limit=10`);
        return res;
    }catch(e){
        return [];
    }
}

function attachAutocomplete(){
    if(!selectors.clienteInput || !selectors.vendedorInput) return;
    const cliDropdown = document.createElement('div');
    cliDropdown.className = 'typeahead-dropdown';
    selectors.clienteInput.parentNode.appendChild(cliDropdown);
    const vendDropdown = document.createElement('div');
    vendDropdown.className = 'typeahead-dropdown';
    selectors.vendedorInput.parentNode.appendChild(vendDropdown);

    const doSearchCli = debounce(async (e)=>{
        const q = e.target.value.trim();
        if(!q) { cliDropdown.innerHTML=''; return; }
        const items = await fetchClientes(q);
        cliDropdown.innerHTML = items.map(it => `<div class="ta-item" data-id="${it.id}" data-codigo="${it.codigo}">${it.nombre} ${it.codigo ? '('+it.codigo+')':''}</div>`).join('');
    }, 250);

    const doSearchVend = debounce(async (e)=>{
        const q = e.target.value.trim();
        if(!q) { vendDropdown.innerHTML=''; return; }
        const items = await fetchVendedores(q);
        vendDropdown.innerHTML = items.map(it => `<div class="ta-item" data-id="${it.id}" data-username="${it.username}">${it.nombre_completo} ${it.username ? '('+it.username+')':''}</div>`).join('');
    }, 250);

    selectors.clienteInput.addEventListener('input', doSearchCli);
    selectors.vendedorInput.addEventListener('input', doSearchVend);

    // click handlers
    document.addEventListener('click', (ev)=>{
        const t = ev.target;
        if(t.classList.contains('ta-item')){
            const parent = t.parentNode;
            if(parent === cliDropdown){
                selectors.clienteInput.value = t.textContent;
                selectors.clienteInput.dataset.id = t.dataset.id;
                cliDropdown.innerHTML = '';
            }else if(parent === vendDropdown){
                selectors.vendedorInput.value = t.textContent;
                selectors.vendedorInput.dataset.id = t.dataset.id;
                vendDropdown.innerHTML = '';
            }
        } else {
            // click outside -> close dropdowns
            if(!t.closest('.typeahead-dropdown')){
                cliDropdown.innerHTML=''; vendDropdown.innerHTML='';
            }
        }
    });
}

// Attach autocomplete after login (apiFetch available)
document.addEventListener('DOMContentLoaded', ()=>{
    attachAutocomplete();
});

function showProductDetails(skus) {
    const productos = skus
        .map(sku => state.productos.find(p => p.sku === sku))
        .filter(Boolean);
    
    if (productos.length > 0) {
        const hideMoneda = !!(state.user && state.user.rol === 'Vendedor');
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
                        ${((hideMoneda || ((producto.moneda_base||'').trim() === 'USD')) ? '' : `
                        <div class="detail-item">
                            <span class="detail-label">Moneda Base:</span>
                            <span class="detail-value">${producto.moneda_base || '-'}</span>
                        </div>
                        `)}
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
        <label style="display:flex;align-items:center;gap:6px;margin-left:8px;font-size:0.9rem;">
            Transporte:
            <select class="transporte-select">
                <option value="Maritimo">Marítimo</option>
                <option value="Aereo">Aéreo</option>
            </select>
        </label>
        <button class="icon-btn remove" title="Quitar SKU">×</button>
    `;
    selectors.skuInputsContainer.appendChild(newRow);
    // Reaplicar eventos a todas las filas para asegurar que todos los steppers funcionen
    document.querySelectorAll('.sku-input-row').forEach(row => {
        attachStepperEvents(row);
    });
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
    // Eliminar listeners previos usando cloneNode
    if (minusBtn) {
        const newMinusBtn = minusBtn.cloneNode(true);
        minusBtn.parentNode.replaceChild(newMinusBtn, minusBtn);
        newMinusBtn.disabled = false;
        newMinusBtn.style.pointerEvents = 'auto';
        newMinusBtn.addEventListener('click', () => {
            let val = parseInt(input.value) || 1;
            if (val > 1) input.value = val - 1;
            input.dispatchEvent(new Event('input'));
        });
    }
    if (plusBtn) {
        const newPlusBtn = plusBtn.cloneNode(true);
        plusBtn.parentNode.replaceChild(newPlusBtn, plusBtn);
        newPlusBtn.disabled = false;
        newPlusBtn.style.pointerEvents = 'auto';
        newPlusBtn.addEventListener('click', () => {
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
            <label style="display:flex;align-items:center;gap:6px;margin-left:8px;font-size:0.9rem;">
                Transporte:
                <select class="transporte-select">
                    <option value="Maritimo">Marítimo</option>
                    <option value="Aereo">Aéreo</option>
                </select>
            </label>
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
    if (sectionDesc) sectionDesc.textContent = '';
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
    // Mostrar/ocultar dashboard integrado según rol
    try {
        const dashboardSection = document.getElementById('dashboard-section');
        const allowedRoles = ['Vendedor','Gerencia_Comercial','Gerencia','Subdireccion','Direccion','Admin'];
        if (dashboardSection) {
                if (allowedRoles.includes(role)) {
                    dashboardSection.style.display = 'block';
                    // If the user is Vendedor we hide metric panels and recent quotes
                    if (role === 'Vendedor') {
                        // hide header (Panel de Métricas), main metric grid and charts
                        const headerEl = dashboardSection.querySelector('header'); if (headerEl) headerEl.style.display = 'none';
                        const gridEl = dashboardSection.querySelector('.grid'); if (gridEl) gridEl.style.display = 'none';
                        const ventasChart = document.getElementById('ventasChart'); if (ventasChart && ventasChart.parentElement) ventasChart.parentElement.style.display = 'none';
                        const topClients = document.getElementById('topClients'); if (topClients && topClients.parentElement) topClients.parentElement.style.display = 'none';
                        // hide resumen por vendedor and its search
                        const vendedorSearch = document.getElementById('vendedor-search'); if (vendedorSearch && vendedorSearch.parentElement) vendedorSearch.parentElement.style.display = 'none';
                        const vendedorTable = document.getElementById('vendedorTable'); if (vendedorTable) {
                            const wrapper = vendedorTable.closest('.table-wrapper'); if (wrapper) wrapper.style.display = 'none'; else vendedorTable.style.display = 'none';
                        }
                        // hide cotizaciones recientes
                        const cotTable = document.getElementById('cotTable'); if (cotTable) {
                            const cotWrap = cotTable.closest('.table-wrapper'); if (cotWrap) cotWrap.style.display = 'none'; else cotTable.style.display = 'none';
                        }
                        // hide specific heading texts inside dashboard to remove labels
                        ['Gráficas','Resumen por Vendedor','Cotizaciones Recientes'].forEach(t => {
                            try {
                                const headers = dashboardSection.querySelectorAll('h1,h2,h3,h4');
                                const h = Array.from(headers).find(el => (el.textContent||'').trim() === t);
                                if (h) h.style.display = 'none';
                            } catch (e) { /* ignore */ }
                        });
                        // Do not initialize full dashboard for vendedores
                    } else {
                        // Inicializar dashboard (permitir modo demo sin sesión para validación)
                        if (!state.dashboardInitialized) {
                            if (typeof initDashboard === 'function') {
                                try {
                                    initDashboard();
                                    state.dashboardInitialized = true;
                                } catch (err) {
                                    console.error('initDashboard failed', err);
                                }
                            } else {
                                // reintentar en breve si la función aún no fue definida
                                setTimeout(() => {
                                    if (typeof initDashboard === 'function' && !state.dashboardInitialized) {
                                        try { initDashboard(); state.dashboardInitialized = true; } catch (err) { console.error('initDashboard retry failed', err); }
                                    }
                                }, 200);
                            }
                        }
                    }
                } else {
                    dashboardSection.style.display = 'none';
                }
        }
    } catch (e) {
        console.error('dashboard visibility error', e);
    }
}

// Nueva función: Renderizar fila según rol
function renderPriceRow(row) {
    const role = state.userRole || 'Vendedor';
    // Prefer the new "lista" field names but fall back to legacy ones
    let precioMax = row.precio_maximo_lista ?? row.precio_maximo;
    let precioMin = row.precio_minimo_lista ?? (
        role === 'Vendedor' ? row.precio_vendedor_min :
        role === 'Gerencia_Comercial' ? row.precio_gerente_com_min :
        role === 'Subdireccion' ? row.precio_subdireccion_min :
        role === 'Direccion' ? row.precio_direccion_min : row.precio_direccion_min
    );
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
            <div class="row-warning" id="warning-${row.sku}" style="display:none;"></div>
        </td>
        <td class="price-col">${formatCurrency(precioMin)}</td>
        <td class="price-col">${formatCurrency(precioMax * row.cantidad)}</td>
        <td class="price-col" id="iva-cell-${row.sku}">${formatCurrency((montoPropuesto && !isNaN(parseFloat(montoPropuesto))) ? Math.round((parseFloat(montoPropuesto) * row.cantidad * 0.16)) : 0)}</td>
        <td class="price-col" id="descuento-cell-${row.sku}">${(montoPropuesto && !isNaN(parseFloat(montoPropuesto)) && precioMax) ? ((Math.max(0, (precioMax - parseFloat(montoPropuesto)) / precioMax) * 100).toFixed(2) + '%') : '-'}</td>
        <td class="price-col" id="total-negociado-${row.sku}">${totalNegociado}</td>
        <td class="price-col">${formatCurrency(precioMin * row.cantidad)}</td>
        <!-- Botón PDF Cotización por SKU eliminado. Usar solo el botón global para cotizar uno o varios SKUs. -->
    </tr>`;
    return html;
}


// Evento para generar y descargar PDF de cotización (multi-SKU)
document.addEventListener('click', async function(e) {
    if (e.target.classList.contains('pdf-cotizar-btn')) {
        // Leer el valor del campo cliente y validarlo
        state.cliente = (document.getElementById('input-cliente')?.value || '').trim();
        if (!state.cliente) {
            showToast('El campo Cliente es obligatorio antes de generar la cotización.', 'error');
            const cliInput = document.getElementById('input-cliente');
            if (cliInput) {
                cliInput.focus();
                cliInput.classList.add('invalid-input');
                setTimeout(() => cliInput.classList.remove('invalid-input'), 2000);
            }
            return;
        }

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
                let montoPropuesto = row.monto_propuesto !== undefined && row.monto_propuesto !== null ? Number(row.monto_propuesto) : Number(row.precio_vendedor_min || row.precio_minimo_lista || 0);
                return {
                    sku: row.sku,
                    descripcion,
                    cantidad: row.cantidad || 1,
                    precio_maximo: row.precio_maximo,
                    precio_maximo_lista: row.precio_maximo_lista ?? row.precio_maximo,
                    precio_vendedor_min: row.precio_vendedor_min,
                    precio_minimo_lista: row.precio_minimo_lista ?? row.precio_vendedor_min,
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
        // payload enviado a /cotizacion/pdf (logging removed)
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
        // Actualizar IVA (por unidad) y descuento%
        const ivaCell = document.getElementById(`iva-cell-${sku}`);
        const descuentoCell = document.getElementById(`descuento-cell-${sku}`);
        const precioMax = row.precio_maximo_lista ?? row.precio_maximo;
        const totalIva = Math.round(montoNum * cantidad * 0.16);
        if (ivaCell) ivaCell.textContent = formatCurrency(totalIva);
            if (descuentoCell) {
                if (montoNum > 0 && precioMax) {
                    const pct = Math.max(0, (precioMax - montoNum) / precioMax) * 100;
                    descuentoCell.textContent = pct.toFixed(2) + '%';
                    // Validar autorización según rol pero con debounce más amplio para evitar advertencias tempranas
                    scheduleCheckDiscount(row, sku, pct, 1200);
                } else {
                    descuentoCell.textContent = '-';
                    scheduleCheckDiscount(row, sku, 0, 1200);
                }
            }
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
        // También actualizar IVA y descuento cuando cambia la cantidad (IVA por unidad permanece)
        const ivaCellQty = document.getElementById(`iva-cell-${sku}`);
        const descuentoCellQty = document.getElementById(`descuento-cell-${sku}`);
        const precioMaxQty = row.precio_maximo_lista ?? row.precio_maximo;
        if (ivaCellQty) ivaCellQty.textContent = formatCurrency(Math.round(monto * cantidad * 0.16));
        if (descuentoCellQty) {
            if (monto > 0 && precioMaxQty) {
                const pct = Math.max(0, (precioMaxQty - monto) / precioMaxQty) * 100;
                descuentoCellQty.textContent = pct.toFixed(2) + '%';
                // Cuando cambia la cantidad, usar debounce más amplio para esperar interacciones del usuario
                scheduleCheckDiscount(row, sku, pct, 1200);
            } else {
                descuentoCellQty.textContent = '-';
                scheduleCheckDiscount(row, sku, 0, 1200);
            }
        }
    }
});

// Programar validación con debounce para evitar advertencias al teclear
function scheduleCheckDiscount(row, sku, pct, delay = 1200) {
    try {
        if (debounceTimers[sku]) clearTimeout(debounceTimers[sku]);
        // Esperar `delay` ms después del último carácter
        debounceTimers[sku] = setTimeout(() => {
            checkDiscountAuthorization(row, sku, pct);
            delete debounceTimers[sku];
        }, delay);
    } catch (e) {
        console.error('scheduleCheckDiscount error', e);
    }
}

// Validar inmediatamente cuando el usuario sale del campo (blur)
document.addEventListener('blur', function(e) {
    if (e.target && e.target.classList && e.target.classList.contains('monto-propuesto-input')) {
        const input = e.target;
        const sku = input.id.replace('monto-propuesto-', '');
        const row = (state.rowsCotizacion || []).find(r => r.sku === sku);
        if (!row) return;
        // cancelar debounce pendiente y validar ahora
        if (debounceTimers[sku]) {
            clearTimeout(debounceTimers[sku]);
            delete debounceTimers[sku];
        }
        let monto = input.value.replace(',', '.');
        let montoNum = parseFloat(monto);
        if (isNaN(montoNum)) montoNum = 0;
        const precioMax = row.precio_maximo_lista ?? row.precio_maximo;
        let pct = 0;
        if (montoNum > 0 && precioMax) {
            pct = Math.max(0, (precioMax - montoNum) / precioMax) * 100;
        }
        // Forzar validación al perder foco
        checkDiscountAuthorization(row, sku, pct, true);
    }
}, true);

    // Verifica si el descuento solicitado excede el permitido por el rol
    function checkDiscountAuthorization(row, sku, pct, force = false) {
        const role = state.userRole || 'Vendedor';
        const allowed = allowedDiscountByRole[role] ?? 0;
        const warningEl = document.getElementById(`warning-${sku}`);
        const pdfBtn = document.getElementById('pdf-cotizar-btn-global');
        if (!warningEl || !pdfBtn) return;

        // Evitar advertencias si el monto propuesto aún es muy corto (ej: el vendedor sigue tipeando)
        try {
            const inputEl = document.getElementById(`monto-propuesto-${sku}`);
            if (inputEl && !force) {
                const raw = (inputEl.value || '').replace(/[^0-9]/g, '');
                // Si quedan menos de 3 dígitos numéricos, asumimos que aún está tipeando
                if (raw.length < 3) return;
            }
        } catch (e) {
            // noop
        }

        if (pct > allowed) {
                    // Guardar contexto de solicitud pendiente
                    pendingAuthRequest = { sku, row, pct: Number(pct), allowed: Number(allowed), role };
                    // Mostrar modal de advertencia visual
                    const modal = document.getElementById('discount-modal');
                    const modalBody = document.getElementById('modal-body');
                    const modalTitle = document.getElementById('modal-title');
                    if (modal && modalBody && modalTitle) {
                        modalTitle.textContent = `Descuento no autorizado`;
                        modalBody.innerHTML = `El descuento solicitado de <strong>${Number(pct).toFixed(2)}%</strong> supera tu límite autorizado de <strong>${Number(allowed)}%</strong> para el rol <strong>${role}</strong>.<br>Si necesitas continuar, solicita autorización.`;
                        modal.style.display = 'flex';
                    }
                    // Resaltar la fila
                    const input = document.getElementById(`monto-propuesto-${sku}`);
                    if (input) input.classList.add('invalid-input');
                    // Mostrar advertencia inline en la fila
                    if (warningEl) {
                        warningEl.style.display = 'block';
                        warningEl.innerHTML = `Descuento ${Number(pct).toFixed(2)}% &gt; ${Number(allowed)}% (Tu rol: ${role})`;
                    }
                    // Bloquear botón global para avanzar
                    pdfBtn.disabled = true;
                    pdfBtn.classList.add('disabled');
                    showToast(`Descuento ${Number(pct).toFixed(2)}% supera tu límite de ${Number(allowed)}%. Debes solicitar autorización.`, 'error', 5000);
        } else {
            // Quitar advertencia
                if (warningEl) {
                    warningEl.style.display = 'none';
                    warningEl.innerHTML = '';
                }
            const input = document.getElementById(`monto-propuesto-${sku}`);
            if (input) input.classList.remove('invalid-input');
            // Habilitar botón solo si no hay otras advertencias activas
                const anyWarnings = document.querySelectorAll('.row-warning').length && Array.from(document.querySelectorAll('.row-warning')).some(w => w.style.display === 'block');
            if (!anyWarnings) {
                pdfBtn.disabled = false;
                pdfBtn.classList.remove('disabled');
                    // Limpiar contexto pendiente si aplica
                    if (pendingAuthRequest && pendingAuthRequest.sku === sku) pendingAuthRequest = null;
            }
        }
    }

    // Manejar click rápido en 'Solicitar autorización' dentro de la fila
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('request-auth')) {
            const sku = e.target.getAttribute('data-sku');
            // Abrir sección de solicitud y pre-llenar SKU y monto
            const solSection = document.getElementById('solicitar-autorizacion-section');
            if (solSection) solSection.style.display = 'block';
            const solSku = document.getElementById('sol-sku');
            const solPrecio = document.getElementById('sol-precio');
            const montoInput = document.getElementById(`monto-propuesto-${sku}`);
            if (solSku) solSku.value = sku;
            if (solPrecio && montoInput) solPrecio.value = montoInput.value;
            // Scroll to solicitar section
            solSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            showToast('Formulario de solicitud abierto. Completa la justificación y envía.', 'info');
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
        // Limpiar contexto pendiente y advertencias
        pendingAuthRequest = null;
        clearSolicitudForm();
        // Ocultar sección de solicitud después de enviar
        const solSectionHide = document.getElementById('solicitar-autorizacion-section');
        if (solSectionHide) solSectionHide.style.display = 'none';
        
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

// Modal handlers
document.getElementById('modal-close')?.addEventListener('click', () => {
    const modal = document.getElementById('discount-modal');
    if (modal) modal.style.display = 'none';
    // limpiar contexto y formulario cuando se cierra sin acción
    pendingAuthRequest = null;
    clearSolicitudForm();
});
document.getElementById('modal-cancel')?.addEventListener('click', () => {
    const modal = document.getElementById('discount-modal');
    if (modal) modal.style.display = 'none';
    pendingAuthRequest = null;
    clearSolicitudForm();
});
document.getElementById('modal-request-auth')?.addEventListener('click', () => {
    const modal = document.getElementById('discount-modal');
    if (modal) modal.style.display = 'none';
    // Abrir sección de solicitud y pre-llenar con el último SKU que causó la advertencia
    const solSection = document.getElementById('solicitar-autorizacion-section');
    if (solSection) solSection.style.display = 'block';
    const solSku = document.getElementById('sol-sku');
    const solPrecio = document.getElementById('sol-precio');
    const solCantidad = document.getElementById('sol-cantidad');
    const solCliente = document.getElementById('sol-cliente');
    // Preferir usar el contexto pendiente si existe
    if (pendingAuthRequest) {
        const ctx = pendingAuthRequest;
        if (solSku) solSku.value = ctx.sku || '';
        const montoInput = ctx.sku ? document.getElementById(`monto-propuesto-${ctx.sku}`) : null;
        if (solPrecio && montoInput) solPrecio.value = montoInput.value || '';
        if (solCantidad) solCantidad.value = (ctx.row && ctx.row.cantidad) ? ctx.row.cantidad : 1;
        if (solCliente) solCliente.value = document.getElementById('input-cliente')?.value || '';
    } else {
        const sku = document.querySelector('.invalid-input')?.id?.replace('monto-propuesto-', '');
        const montoInput = sku ? document.getElementById(`monto-propuesto-${sku}`) : null;
        if (sku && solSku) solSku.value = sku;
        if (solPrecio && montoInput) solPrecio.value = montoInput.value || '';
        if (solCantidad) solCantidad.value = 1;
        if (solCliente) solCliente.value = document.getElementById('input-cliente')?.value || '';
    }
    solSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Poner foco en justificación para agilizar envío
    const just = document.getElementById('sol-justificacion');
    if (just) just.focus();
    showToast('Formulario de solicitud abierto. Completa la justificación y envía.', 'info');
});

// Limpia los campos del formulario de solicitud y mensajes asociados
function clearSolicitudForm() {
    try {
        const solSku = document.getElementById('sol-sku');
        const solPrecio = document.getElementById('sol-precio');
        const solCantidad = document.getElementById('sol-cantidad');
        const solCliente = document.getElementById('sol-cliente');
        const solJust = document.getElementById('sol-justificacion');
        const statusEl = document.getElementById('solicitud-status');
        if (solSku) solSku.value = '';
        if (solPrecio) solPrecio.value = '';
        if (solCantidad) solCantidad.value = '';
        if (solCliente) solCliente.value = '';
        if (solJust) solJust.value = '';
        if (statusEl) statusEl.textContent = '';
    } catch (e) {
        // noop
    }
}

// Exponer función para pruebas automatizadas (Playwright)
try {
    window.checkDiscountAuthorization = checkDiscountAuthorization;
} catch (e) {
    // noop in non-browser contexts
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
        // aprobar solicitud (debug logging removed)
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
        // rechazar solicitud (debug logging removed)
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

// --- Cotizaciones: fetch and render recent/search results ---
async function fetchCotizaciones(q = '', limit = 20) {
    try {
        const params = new URLSearchParams();
        if (q) params.append('q', q);
        params.append('limit', String(limit));
        const data = await apiFetch(`/api/cotizaciones?${params.toString()}`);
        return data;
    } catch (e) {
        // If backend returns 404 for empty results, treat as empty list
        if (e && e.message && e.message.includes('404')) {
            return [];
        }
        console.error('Error fetching cotizaciones', e);
        showToast('No se pudieron obtener cotizaciones: ' + e.message, 'error');
        return [];
    }
}

function renderCotizaciones(list) {
    let section = document.getElementById('cotizaciones-section');
    if (!section) {
        section = document.createElement('section');
        section.id = 'cotizaciones-section';
        section.className = 'card';
        section.innerHTML = `
            <h3>Cotizaciones Recientes</h3>
            <div style="margin-bottom:8px;"><input id="cotizaciones-q" placeholder="Buscar por cliente o número" style="width:240px;margin-right:8px;"> <button id="refresh-cotizaciones">Actualizar</button></div>
            <div style="overflow:auto; max-height:240px;"><table id="cotizaciones-table" class="simple-table"><thead><tr><th>ID</th><th>Cliente</th><th>Vendedor</th><th>N° Cliente</th><th>N° Vendedor</th><th>Fecha</th></tr></thead><tbody></tbody></table></div>
        `;
        // insert after product details card if present, else append to body
        const anchor = document.getElementById('product-details-card') || document.querySelector('.login-card');
        if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(section, anchor.nextSibling);
        else document.body.appendChild(section);
        document.getElementById('refresh-cotizaciones')?.addEventListener('click', loadCotizaciones);
        document.getElementById('cotizaciones-q')?.addEventListener('keydown', (e)=>{ if(e.key==='Enter') loadCotizaciones(); });
    }
    const tbody = section.querySelector('table#cotizaciones-table tbody');
    tbody.innerHTML = (list || []).slice(0, 200).map(c => `
        <tr>
            <td>${c.id}</td>
            <td>${c.cliente || '-'}</td>
            <td>${c.vendedor || '-'}</td>
            <td>${c.numero_cliente || '-'}</td>
            <td>${c.numero_vendedor || '-'}</td>
            <td>${c.fecha_cotizacion ? new Date(c.fecha_cotizacion).toLocaleString('es-MX') : '-'}</td>
        </tr>
    `).join('');
}

async function loadCotizaciones() {
    try {
        const q = document.getElementById('cotizaciones-q')?.value || '';
        const rows = await fetchCotizaciones(q, 50);
        renderCotizaciones(rows);
    } catch (e) {
        console.error('loadCotizaciones error', e);
    }
}

// Try to populate cotizaciones after login if available
document.addEventListener('DOMContentLoaded', ()=>{
    if (state.auth) setTimeout(loadCotizaciones, 500);
});

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
    // (El manejo de los botones stepper se realiza solo en attachStepperEvents para evitar doble incremento)
    // Botón agregar SKU
    if (e.target.classList.contains('add-sku')) {
        const clienteVal = (document.getElementById('input-cliente')?.value || '').trim();
        if (!clienteVal) {
            showToast('Ingrese el nombre del Cliente antes de agregar SKUs.', 'error');
            const cli = document.getElementById('input-cliente');
            if (cli) {
                cli.focus();
                cli.classList.add('invalid-input');
                setTimeout(() => cli.classList.remove('invalid-input'), 1500);
            }
            return;
        }
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

// ------------------ Dashboard integrado ------------------
async function fetchDashboardMetrics(periodDays=30, vendedor='all'){
    const q = new URLSearchParams({ periodDays, vendedor });
    const url = `${state.baseUrl}/api/dashboard/metrics?${q.toString()}`;
    const resp = await fetch(url, { headers: { Authorization: state.auth ? `Bearer ${state.auth}` : '' } });
    if (!resp.ok) throw new Error('No se pudieron obtener métricas');
    return resp.json();
}

function renderSummary(m){
    document.getElementById('totalVentas').innerText = m.total_sales_formatted || '-';
    document.getElementById('avgValor').innerText = m.avg_value_formatted || '-';
    document.getElementById('winRate').innerText = m.win_rate_percent ? m.win_rate_percent + '%' : '-';
    document.getElementById('avgMargin').innerText = m.avg_margin_percent ? m.avg_margin_percent + '%' : '-';
}

function renderCharts(m){
    try{
        // Ventas por día: línea con área rellenada y colores pastel
        const days = m.sales_by_day || [];
        // Apply chart font and colors from CSS variables (compute before using)
        const __css = getComputedStyle(document.documentElement);
        const __chartFont = __css.getPropertyValue('--chart-font-family').trim() || "'Space Grotesk', 'Segoe UI', Arial, sans-serif";
        const __fontColor = __css.getPropertyValue('--text').trim() || '#f6f8ff';
        const __mutedColor = __css.getPropertyValue('--muted').trim() || '#9ea6c6';
        const accentColor = (__css.getPropertyValue('--chart-accent').trim() || '#89CFF0');
        const ventasTrace = {
            x: days.map(d=>d.date),
            y: days.map(d=>d.amount),
            type: 'bar',
            marker: { color: accentColor },
            hovertemplate: '%{x}<br>$%{y:,.0f}<extra></extra>'
        };
        const ventasLayout = {
            margin: { t: 40, l: 40, r: 20, b: 40 },
            title: { text: 'Ventas por día', font: { size: 16 } },
            xaxis: { title: 'Fecha', type: 'category', tickangle: -45 },
            yaxis: { title: 'Monto (MXN)' },
            hovermode: 'closest',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(255,255,255,0.02)',
            barmode: 'group'
        };
        ventasLayout.font = ventasLayout.font || {};
        ventasLayout.font.family = __chartFont;
        ventasLayout.title = ventasLayout.title || {};
        ventasLayout.title.font = ventasLayout.title.font || {};
        ventasLayout.title.font.family = __chartFont;
        ventasLayout.title.font.color = __fontColor;
        ventasLayout.xaxis = ventasLayout.xaxis || {};
        // xaxis.title can be a string or an object; normalize to object with `text` and `font`
        if (typeof ventasLayout.xaxis.title === 'string') {
            ventasLayout.xaxis.title = { text: ventasLayout.xaxis.title, font: { family: __chartFont, color: __mutedColor, size: 12 } };
        } else {
            ventasLayout.xaxis.title = ventasLayout.xaxis.title || {};
            ventasLayout.xaxis.title.font = ventasLayout.xaxis.title.font || { family: __chartFont, color: __mutedColor, size: 12 };
        }
        ventasLayout.xaxis.tickfont = { family: __chartFont, color: __fontColor, size: 11 };
        ventasLayout.yaxis = ventasLayout.yaxis || {};
        if (typeof ventasLayout.yaxis.title === 'string') {
            ventasLayout.yaxis.title = { text: ventasLayout.yaxis.title, font: { family: __chartFont, color: __mutedColor, size: 12 } };
        } else {
            ventasLayout.yaxis.title = ventasLayout.yaxis.title || {};
            ventasLayout.yaxis.title.font = ventasLayout.yaxis.title.font || { family: __chartFont, color: __mutedColor, size: 12 };
        }
        ventasLayout.yaxis.tickfont = { family: __chartFont, color: __fontColor, size: 11 };
        Plotly.newPlot('ventasChart', [ventasTrace], ventasLayout, { responsive: true, displayModeBar: false });
        // Ensure Plotly recalculates size (in case container was hidden when first rendered)
        try { if (window.Plotly && Plotly.Plots && document.getElementById('ventasChart')) Plotly.Plots.resize(document.getElementById('ventasChart')); } catch (rerr) { console.warn('resize ventasChart failed', rerr); }
        // Fallback: if no data, show a lightweight message so user knows nothing loaded
        if (!days || days.length === 0 || (Array.isArray(ventasTrace.y) && ventasTrace.y.every(v => !v))) {
            const c = document.getElementById('ventasChart');
            if (c) {
                c.innerHTML = '<div style="color:var(--muted);font-family:var(--chart-font-family);display:flex;align-items:center;justify-content:center;height:100%">No hay datos de ventas para el periodo seleccionado.</div>';
            }
        }

        // Top clientes OR ventas por vendedor
        const clients = m.top_clients || [];
        const vendedores = m.by_vendedor || [];
        const pastel = [
            __css.getPropertyValue('--chart-palette-1').trim() || '#FFD1DC',
            __css.getPropertyValue('--chart-palette-2').trim() || '#C8E7FF',
            __css.getPropertyValue('--chart-palette-3').trim() || '#D6F5D6',
            __css.getPropertyValue('--chart-palette-4').trim() || '#FFE7C6',
            __css.getPropertyValue('--chart-palette-5').trim() || '#E9D6FF',
            __css.getPropertyValue('--chart-palette-6').trim() || '#FDEBD0'
        ];
        // If backend provided vendedor aggregates, show ventas por vendedor (barra)
        if (vendedores && vendedores.length > 0) {
            const labels = vendedores.map(v=>v.vendedor);
            const values = vendedores.map(v=> (v.closed_total && v.closed_total>0) ? v.closed_total : v.total_value);
            const quotes = vendedores.map(v=>v.quotes_count||0);
            const closed = vendedores.map(v=>v.closed_count||0);
            const barTrace = {
                x: labels,
                y: values,
                type: 'bar',
                marker: { color: pastel.slice(0, Math.max(1, labels.length)) },
                hovertemplate: '%{x}<br>$%{y:,.0f}<br>Quotes: %{customdata[0]} Closed: %{customdata[1]}<extra></extra>',
                customdata: labels.map((_,i)=>[quotes[i], closed[i]])
            };
            const vLayout = {
                margin: { t: 36 },
                title: { text: 'Ventas por vendedor', font: { size: 16, family: __chartFont, color: __fontColor } },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(255,255,255,0.02)',
                font: { family: __chartFont, color: __fontColor },
                xaxis: { tickangle: -45 }
            };
            Plotly.newPlot('topClients', [barTrace], vLayout, { responsive: true, displayModeBar: false });
        } else {
            const data = [{
                labels: clients.map(c => c.name),
                values: clients.map(c => c.amount),
                type: 'pie',
                hole: 0.45,
                marker: { colors: pastel.slice(0, Math.max(1, clients.length)) },
                hovertemplate: '%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>'
            }];
            const clientesLayout = {
                margin: { t: 36 },
                title: { text: 'Top clientes', font: { size: 16, family: __chartFont, color: __fontColor } },
                showlegend: false,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(255,255,255,0.02)',
                font: { family: __chartFont, color: __fontColor }
            };
            Plotly.newPlot('topClients', data, clientesLayout, { responsive: true, displayModeBar: false });
        }
        try { if (window.Plotly && Plotly.Plots && document.getElementById('topClients')) Plotly.Plots.resize(document.getElementById('topClients')); } catch (rerr) { console.warn('resize topClients failed', rerr); }
        // If no clientes and no vendedores data, show fallback message
        const topClientsEl = document.getElementById('topClients');
        const hasClientData = Array.isArray(clients) && clients.length > 0 && clients.some(c => Number(c.amount));
        const hasVendedorData = Array.isArray(vendedores) && vendedores.length > 0 && vendedores.some(v => Number(v.total_value) || Number(v.closed_total));
        if (topClientsEl && !hasClientData && !hasVendedorData) {
            topClientsEl.innerHTML = '<div style="color:var(--muted);font-family:var(--chart-font-family);display:flex;align-items:center;justify-content:center;height:100%">No hay datos para el periodo seleccionado.</div>';
        }
    } catch (e) { console.error('renderCharts error', e); }
}

function renderTable(rows){
    const tbody = document.querySelector('#cotTable tbody');
    if (!tbody) return;
    try {
        tbody.innerHTML = '';
        rows.forEach(r=>{
            const tr = document.createElement('tr');
            tr.innerHTML = `<td><a href="/api/cotizacion/pdf/${r.id}" target="_blank">${r.folio}</a></td><td>${r.fecha}</td><td>${r.cliente}</td><td>${r.vendedor}</td><td>${r.valor_formatted}</td><td>${r.estado}</td>`;
            tbody.appendChild(tr);
        });
        // Try to initialize DataTable only if jQuery and DataTables are available
        if (typeof window.jQuery !== 'undefined' && window.jQuery.fn && window.jQuery.fn.dataTable) {
            try {
                if (!window.jQuery.fn.dataTable.isDataTable('#cotTable')) {
                    window.jQuery('#cotTable').DataTable();
                }
            } catch (dtErr) {
                console.warn('DataTable init failed', dtErr);
            }
        } else {
            // If DataTables not available, leave simple table and ensure no errors
        }
    } catch (err) {
        console.error('renderTable error', err);
        // Show a simple fallback message in the table
        tbody.innerHTML = '<tr><td colspan="6" style="color:var(--muted);">No fue posible renderizar la tabla de cotizaciones.</td></tr>';
    }
}

function renderVendedorTable(vendedores){
    const tbody = document.querySelector('#vendedorTable tbody');
    if (!tbody) return;
    try{
        tbody.innerHTML = '';
        // store latest for export
        state.latestVendedores = vendedores || [];
        const fmt = (v) => new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(v);
        const esc = s => String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        (vendedores || []).forEach(v=>{
            const tr = document.createElement('tr');
            const closeRate = (v.quotes_count && v.closed_count) ? Math.round((v.closed_count / v.quotes_count)*10000)/100 : null;
            // include a sparkline cell (series expected as array of numbers)
            const series = Array.isArray(v.series) ? v.series : [];
            tr.innerHTML = `<td>${esc(v.vendedor)}</td><td>${v.quotes_count||0}</td><td>${v.closed_count||0}</td><td>${v.total_value?fmt(v.total_value):'-'}</td><td>${v.closed_total?fmt(v.closed_total):'-'}</td><td>${closeRate!=null?closeRate+'%':'-'}</td><td>${v.avg_discount_percent!=null?v.avg_discount_percent+'%':'-'}</td><td>${v.avg_margin_percent!=null?v.avg_margin_percent+'%':'-'}</td><td class="sparkline-cell" data-series='${JSON.stringify(series)}' style="width:120px;"> </td>`;
            tbody.appendChild(tr);
        });
        if (typeof window.jQuery !== 'undefined' && window.jQuery.fn && window.jQuery.fn.dataTable) {
            try{
                if (!window.jQuery.fn.dataTable.isDataTable('#vendedorTable')) {
                    window.jQuery('#vendedorTable').DataTable({
                        columnDefs: [
                            { targets: -1, orderable: false, searchable: false }
                        ]
                    });
                }
            }catch(e){ console.warn('vendedor DataTable init failed', e); }
        }
    }catch(err){ console.error('renderVendedorTable error', err); tbody.innerHTML = '<tr><td colspan="9" style="color:var(--muted);">No fue posible renderizar resumen por vendedor.</td></tr>'; }
}

// Render small inline SVG sparklines for each vendedor row
function renderSparklines(){
    try{
        const cells = document.querySelectorAll('.sparkline-cell');
        cells.forEach(cell=>{
            const raw = cell.getAttribute('data-series') || '[]';
            let series = [];
            try{ series = JSON.parse(raw); }catch(e){ series = []; }
            // draw only if we have numeric series
            if (!Array.isArray(series) || series.length === 0) {
                cell.innerHTML = '<div style="color:var(--muted);font-size:11px;text-align:center;">-</div>';
                return;
            }
            const w = 120, h = 28, pad = 4;
            const nums = series.map(n=>Number(n)||0);
            const min = Math.min(...nums);
            const max = Math.max(...nums);
            const range = (max - min) || 1;
            const points = nums.map((v,i)=>{
                const x = pad + (i/(nums.length-1||1)) * (w - pad*2);
                const y = pad + (1 - (v - min)/range) * (h - pad*2);
                return `${x},${y}`;
            }).join(' ');
            const stroke = getComputedStyle(document.documentElement).getPropertyValue('--chart-accent').trim() || '#89CFF0';
            const fill = stroke + '33';
            cell.innerHTML = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><polyline points="${points}" fill="none" stroke="${stroke}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>`;
        });
    }catch(e){ console.warn('renderSparklines failed', e); }
}

// CSV export for vendedor summary
async function exportVendedoresCSV(){
    try{
        const rows = state.latestVendedores || [];
        if (!rows.length) return showToast('No hay datos para exportar.', 'info');
        const headers = ['vendedor','quotes_count','closed_count','total_value','closed_total','close_rate_pct','avg_discount_percent','avg_margin_percent','series'];
        const lines = [headers.join(',')];
        rows.forEach(r=>{
            const closeRate = (r.quotes_count && r.closed_count) ? ((r.closed_count / r.quotes_count)*100).toFixed(2) : '';
            const series = Array.isArray(r.series) ? r.series.join(';') : '';
            const vals = [r.vendedor, r.quotes_count||0, r.closed_count||0, r.total_value||0, r.closed_total||0, closeRate, r.avg_discount_percent||'', r.avg_margin_percent||'', `"${series}"`];
            lines.push(vals.map(v=>typeof v === 'string' ? `"${v.replace(/"/g,'""')}"` : v).join(','));
        });
        const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resumen_vendedores_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }catch(e){ console.error('exportVendedoresCSV error', e); showToast('Error exportando CSV','error'); }
}

// Attach export button and ensure sparklines render after table updates
document.addEventListener('click', (e)=>{
    if (e.target && e.target.id === 'vendedor-export'){
        exportVendedoresCSV();
    }
});

// Ensure sparklines are rendered whenever the vendedor table is updated
const origRenderVendedorTable = renderVendedorTable;
renderVendedorTable = function(vendedores){
    origRenderVendedorTable(vendedores);
    // render sparklines after DOM update
    renderSparklines();
};

// Lightweight client-side table search and sort (no DataTables)
function _initVendedorTableHelpers(){
    const table = document.getElementById('vendedorTable');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    const headers = table.querySelectorAll('th');
    // Sorting
    headers.forEach((th, idx)=>{
        const sortType = th.getAttribute('data-sort') || 'string';
        th.style.cursor = 'pointer';
        th.addEventListener('click', ()=>{
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const dir = th.getAttribute('data-dir') === 'asc' ? 'desc' : 'asc';
            th.setAttribute('data-dir', dir);
            rows.sort((a,b)=>{
                const aText = a.children[idx].innerText.trim();
                const bText = b.children[idx].innerText.trim();
                if (sortType === 'number'){
                    const an = parseFloat(aText.replace(/[^0-9.-]+/g,'')) || 0;
                    const bn = parseFloat(bText.replace(/[^0-9.-]+/g,'')) || 0;
                    return dir === 'asc' ? an - bn : bn - an;
                }
                return dir === 'asc' ? aText.localeCompare(bText) : bText.localeCompare(aText);
            });
            // reattach
            rows.forEach(r=>tbody.appendChild(r));
        });
    });
    // Search
    const search = document.getElementById('vendedor-search');
    if (search){
        let last = '';
        search.addEventListener('input', ()=>{
            const q = search.value.trim().toLowerCase();
            if (q === last) return; last = q;
            Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
                const name = tr.children[0].innerText.toLowerCase();
                tr.style.display = name.indexOf(q) === -1 ? 'none' : '';
            });
        });
    }
}

// Initialize helpers once DOM is ready
document.addEventListener('DOMContentLoaded', _initVendedorTableHelpers);

async function refreshDashboard(){
    try{
        const period = document.getElementById('dash-period')?.value || '30';
        const vendedor = document.getElementById('dash-vendedor')?.value || 'all';
        const but = document.getElementById('dash-refresh'); if (but) but.disabled = true;
        const m = await fetchDashboardMetrics(period, vendedor);
        renderSummary(m);
        renderCharts(m);
        renderTable(m.recent_quotes || []);
        renderVendedorTable(m.by_vendedor || []);
        if (but) but.disabled = false;
    }catch(e){ console.error('refreshDashboard', e); showToast('Error cargando métricas','error'); const but=document.getElementById('dash-refresh'); if(but) but.disabled=false; }
}

async function initDashboard(){
    try{
        // populate vendedores selector
        const vsel = document.getElementById('dash-vendedor');
        if (vsel) {
            try{
                const res = await apiFetch('/api/vendedores?limit=200');
                (res || []).forEach(x=>{ const o = document.createElement('option'); o.value = x.id || x.nombre || 'all'; o.textContent = x.nombre || x.id; vsel.appendChild(o); });
            }catch(e){ /* ignore */ }
        }
        document.getElementById('dash-refresh')?.addEventListener('click', refreshDashboard);
        document.getElementById('dash-demo')?.addEventListener('click', ()=>{ loadDemoMetrics(); });
        document.getElementById('dash-period')?.addEventListener('change', refreshDashboard);
        document.getElementById('dash-vendedor')?.addEventListener('change', refreshDashboard);
        // primera carga
        await refreshDashboard();
    }catch(e){ console.error('initDashboard error', e); }
}

function sampleMetrics(){
    const days = [];
    const today = new Date();
    for(let i=29;i>=0;i--){
        const d = new Date(today);
        d.setDate(d.getDate()-i);
        const label = d.toISOString().slice(0,10);
        const amount = Math.round(20000 + Math.random()*80000);
        days.push({ date: label, amount });
    }
    const top_clients = [
        { name: 'IMSS CENTRO', amount: 130000 },
        { name: 'PROVECTUS MEDICAL', amount: 94358 },
        { name: 'Cliente Demo A', amount: 60000 },
        { name: 'Cliente Demo B', amount: 35000 }
    ];
    const recent = [];
    for(let i=0;i<12;i++){
        const id = 100+i;
        recent.push({ id, folio: `DEMO-${id.toString().padStart(3,'0')}`, fecha: new Date(Date.now() - i*3600*1000).toLocaleString('es-MX'), cliente: top_clients[i%top_clients.length].name, vendedor: 'vendedor-demo', valor: Math.round(10000+Math.random()*40000), valor_formatted: '$' + Math.round(10000+Math.random()*40000).toLocaleString('es-MX'), estado: 'N/A' });
    }
    return {
        period_days: 30,
        total_sales: days.reduce((s,d)=>s+d.amount,0),
        total_sales_formatted: '$' + days.reduce((s,d)=>s+d.amount,0).toLocaleString('es-MX'),
        quote_count: recent.length,
        sales_by_day: days,
        top_clients,
        avg_discount_percent: 8.5,
        avg_discount_percent_formatted: '8.50%',
        recent_quotes: recent,
        avg_value_formatted: '$' + Math.round((days.reduce((s,d)=>s+d.amount,0)/recent.length)).toLocaleString('es-MX'),
        win_rate_percent: 32,
        avg_margin_percent: 18
    };
}

function loadDemoMetrics(){
    try {
        const m = sampleMetrics();
        renderSummary(m);
        renderCharts(m);
        renderTable(m.recent_quotes || []);
        showToast('Datos demo cargados.', 'success', 2000);
    } catch (err) {
        console.error('loadDemoMetrics error', err);
        showToast('Error cargando datos demo: ' + (err.message || err), 'error', 5000);
    }
}

// ---------------------------------------------------------

// Cierre automático de cualquier bloque abierto (por si acaso)
// (No se agrega código funcional, solo se asegura el cierre de bloques)

// Tooltips use CSS pseudo-element on `.metric-info` to avoid duplication.
// Replace CSS pseudo tooltips with a JS-driven tooltip to avoid overflow
;(function(){
    // create tooltip element
    const tip = document.createElement('div');
    tip.className = 'metric-tooltip hidden';
    document.body.appendChild(tip);

    let activeTarget = null;
    let hideTimeout = null;

    function showMetricTooltip(target){
        const text = target.getAttribute('data-tooltip') || '';
        if (!text) return;
        activeTarget = target;
        tip.textContent = text;
        tip.classList.remove('hidden');
        tip.classList.add('visible');
        positionTooltip(target);
        // ensure visible
        clearTimeout(hideTimeout);
    }

    function hideMetricTooltip(){
        activeTarget = null;
        tip.classList.remove('visible');
        tip.classList.add('hidden');
    }

    function positionTooltip(target){
        if (!target) return;
        const rect = target.getBoundingClientRect();
        tip.style.maxWidth = Math.min(420, window.innerWidth - 32) + 'px';
        tip.style.left = '0px'; tip.style.top = '0px';
        tip.style.display = 'block';
        // compute after it is displayed to get size
        const tw = tip.offsetWidth;
        const th = tip.offsetHeight;
        // center above the icon by default
        let left = rect.left + rect.width/2 - tw/2;
        left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
        let top = rect.top - th - 10;
        // if not enough space above, place below
        if (top < 8) top = rect.bottom + 10;
        tip.style.left = Math.round(left) + 'px';
        tip.style.top = Math.round(top) + 'px';
    }

    // delegate events
    document.addEventListener('mouseover', (e)=>{
        const t = e.target.closest && e.target.closest('.metric-info');
        if (t) {
            showMetricTooltip(t);
        }
    });
    document.addEventListener('mouseout', (e)=>{
        const t = e.target.closest && e.target.closest('.metric-info');
        if (t) {
            // small delay to avoid flicker
            hideTimeout = setTimeout(hideMetricTooltip, 80);
        }
    });
    // reposition on scroll/resize when visible
    window.addEventListener('scroll', ()=>{ if (activeTarget) positionTooltip(activeTarget); }, true);
    window.addEventListener('resize', ()=>{ if (activeTarget) positionTooltip(activeTarget); });
})();
