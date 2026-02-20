import pytest
from playwright.sync_api import sync_playwright

# Prueba de login y cierre de sesión en la app

def test_login_logout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:5173")
        # Login
        page.fill('#username', 'admin')
        page.fill('#password', 'Admin123!')
        page.click('#connect-btn')
        page.wait_for_selector('#user-role', timeout=5000, state='visible')
        page.wait_for_function("el => el.textContent.includes('Rol:'), document.querySelector('#user-role')", timeout=5000)
        assert "Rol:" in page.inner_text('#user-role')
        # Cerrar sesión
        page.click('#logout-btn')
        assert "Sesión cerrada correctamente." in page.inner_text('#status-msg')
        browser.close()
