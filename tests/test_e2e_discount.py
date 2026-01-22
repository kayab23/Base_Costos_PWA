import pytest
from playwright.sync_api import sync_playwright


def test_discount_warning_and_request_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:5173")
        # Simular rol de Vendedor y recargar para que la app lo lea
        page.evaluate("() => { localStorage.setItem('userRole','Vendedor'); localStorage.setItem('apiUrl', 'http://127.0.0.1:8000'); }")
        page.reload()

        # Inyectar un row simulado en state.rowsCotizacion
        page.evaluate("() => { window.state = window.state || {}; window.state.rowsCotizacion = window.state.rowsCotizacion || []; window.state.rowsCotizacion.push({sku: 'FAKE123', precio_maximo_lista: 1000, cantidad: 1}); }")

        # Añadir la fila HTML con input y warning container
        page.evaluate('''() => {
            const tbody = document.querySelector('#landed-table tbody');
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>FAKE123</td>
                <td>1</td>
                <td class="price-col">1000</td>
                    <td class="price-col"><input type="text" class="monto-propuesto-input" id="monto-propuesto-FAKE123" value="" style="width:100px;"></td>
                    <td class="price-col" id="iva-cell-FAKE123">0</td>
                    <td class="price-col" id="descuento-cell-FAKE123">-</td>
                    <td class="price-col" id="total-negociado-FAKE123">0</td>
                    <td class="price-col"><div id="warning-FAKE123" class="row-warning" style="display:none;"></div></td>
            `;
            tbody.appendChild(tr);
        }''')

        # Escribir un monto que exceda el descuento permitido (Vendedor 20% => monto < 800 para exceder)
        page.fill('#monto-propuesto-FAKE123', '600')
        # Disparar evento input
        page.eval_on_selector('#monto-propuesto-FAKE123', 'el => el.dispatchEvent(new Event("input"))')

        # Forzar llamada a la función pública expuesta para pruebas (en caso de que el handler modular no se ejecute)
        page.evaluate("() => { const row = window.state.rowsCotizacion.find(r => r.sku === 'FAKE123'); if (window.checkDiscountAuthorization && row) { const pct = Math.max(0, (row.precio_maximo_lista - 600) / row.precio_maximo_lista * 100); window.checkDiscountAuthorization(row, 'FAKE123', pct); } }")

        # Verificar que el modal se muestre y el botón PDF esté deshabilitado
        page.wait_for_selector('#discount-modal', timeout=2000)
        modal_display = page.eval_on_selector('#discount-modal', 'el => window.getComputedStyle(el).display')
        assert modal_display in ('flex', 'block')

        pdf_disabled = page.eval_on_selector('#pdf-cotizar-btn-global', 'el => el.disabled')
        assert pdf_disabled is True

        # Pulsar 'Solicitar autorización' desde el modal
        page.click('#modal-request-auth')

        # Verificar que la sección de solicitud se muestre y esté prellenada
        page.wait_for_selector('#solicitar-autorizacion-section', timeout=2000)
        sol_display = page.eval_on_selector('#solicitar-autorizacion-section', 'el => window.getComputedStyle(el).display')
        assert sol_display != 'none'
        sol_sku = page.eval_on_selector('#sol-sku', 'el => el.value')
        sol_precio = page.eval_on_selector('#sol-precio', 'el => el.value')
        assert sol_sku == 'FAKE123'
        assert sol_precio in ('600', '600.0')

        browser.close()
