from app.pdf.generar_pdf import generar_pdf_politica_entrega

payload = {
    "cliente": "ACME S.A. de C.V.",
    "items": [
        {
            "sku": "ABC-123",
            "descripcion": "Producto de prueba A con descripción larga para comprobar salto de línea en PDF.",
            "cantidad": 2,
            "precio_maximo": 10000.0,
            "precio_maximo_lista": 10000.0,
            "precio_vendedor_min": 8000.0,
            "precio_minimo_lista": 8000.0,
            "monto_propuesto": 9000.0,
            "proveedor": "Proveedor A",
            "origen": "México"
        },
        {
            "sku": "XYZ-789",
            "descripcion": "Producto de prueba B",
            "cantidad": 1,
            "precio_maximo": 5000.0,
            "precio_maximo_lista": 5000.0,
            "precio_vendedor_min": 4000.0,
            "precio_minimo_lista": 4000.0,
            "monto_propuesto": 4500.0,
            "proveedor": "Proveedor B",
            "origen": "USA"
        },
        {
            "sku": "1199-00052-02",
            "descripcion": "Producto ejemplo solicitado por usuario para ver Total Máximo vs Monto Propuesto.",
            "cantidad": 2,
            "precio_maximo": 2584.3,
            "precio_maximo_lista": 2584.3,
            "precio_vendedor_min": 2000.0,
            "precio_minimo_lista": 2000.0,
            "monto_propuesto": 2100.0,
            "proveedor": "Proveedor C",
            "origen": "México"
        }
    ]
}

pdf_bytes = generar_pdf_politica_entrega(payload)
with open('test_cotizacion.pdf', 'wb') as f:
    f.write(pdf_bytes)
print('PDF generado: test_cotizacion.pdf')
