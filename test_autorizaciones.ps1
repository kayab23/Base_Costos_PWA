# Script de prueba para sistema de autorizaciones

Write-Host "`n=== CASO DE PRUEBA: Autorización de Descuento ===" -ForegroundColor Cyan
Write-Host "Escenario: Vendedor solicita precio de $20,000 para HP30B-CTO-01 (min actual: $21,646.56)`n"

# 1. Vendedor crea solicitud
Write-Host "1. VENDEDOR1 crea solicitud..." -ForegroundColor Yellow
$vendedorAuth = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("vendedor1:Vendedor123!"))
$solicitudBody = @{
    sku = "HP30B-CTO-01"
    transporte = "Maritimo"
    precio_propuesto = 20000
    cliente = "Constructora ABC SA"
    cantidad = 100
    justificacion = "Cliente importante con volumen recurrente. Competencia ofrece $19,800. Estratégico para Q1 2026."
} | ConvertTo-Json

try {
    $solicitud = Invoke-RestMethod -Uri "http://localhost:8000/autorizaciones/solicitar" `
        -Method POST `
        -Headers @{ Authorization = $vendedorAuth } `
        -Body $solicitudBody `
        -ContentType "application/json"
    
    Write-Host "   ✓ Solicitud creada. ID: $($solicitud.id)" -ForegroundColor Green
    Write-Host "   - SKU: $($solicitud.sku)"
    Write-Host "   - Precio propuesto: $($solicitud.precio_propuesto.ToString('N2'))"
    Write-Host "   - Descuento adicional: $($solicitud.descuento_adicional_pct.ToString('N2'))%"
    Write-Host "   - Estado: $($solicitud.estado)"
    $solicitudId = $solicitud.id
} catch {
    Write-Host "   ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Gerencia Comercial ve pendientes
Write-Host "`n2. GERCOM1 consulta solicitudes pendientes..." -ForegroundColor Yellow
$gercomAuth = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("gercom1:GerCom123!"))

try {
    $pendientes = Invoke-RestMethod -Uri "http://localhost:8000/autorizaciones/pendientes" `
        -Method GET `
        -Headers @{ Authorization = $gercomAuth }
    
    Write-Host "   ✓ Solicitudes pendientes: $($pendientes.Count)" -ForegroundColor Green
    foreach ($p in $pendientes) {
        Write-Host "   - ID $($p.id): $($p.sku) - `$$($p.precio_propuesto.ToString('N2')) (solicitante: $($p.solicitante))"
    }
} catch {
    Write-Host "   ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Gerencia Comercial aprueba
Write-Host "`n3. GERCOM1 aprueba la solicitud..." -ForegroundColor Yellow
$aprobarBody = @{
    comentarios = "Aprobado. Cliente estratégico con historial de compras. El volumen justifica el descuento."
} | ConvertTo-Json

try {
    $aprobada = Invoke-RestMethod -Uri "http://localhost:8000/autorizaciones/$solicitudId/aprobar" `
        -Method PUT `
        -Headers @{ Authorization = $gercomAuth } `
        -Body $aprobarBody `
        -ContentType "application/json"
    
    Write-Host "   ✓ Solicitud aprobada" -ForegroundColor Green
    Write-Host "   - Estado: $($aprobada.estado)"
    Write-Host "   - Autorizador: $($aprobada.autorizador)"
    Write-Host "   - Comentarios: $($aprobada.comentarios_autorizador)"
} catch {
    Write-Host "   ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Vendedor verifica resultado
Write-Host "`n4. VENDEDOR1 consulta sus solicitudes..." -ForegroundColor Yellow

try {
    $misSolicitudes = Invoke-RestMethod -Uri "http://localhost:8000/autorizaciones/mis-solicitudes" `
        -Method GET `
        -Headers @{ Authorization = $vendedorAuth }
    
    Write-Host "   ✓ Mis solicitudes: $($misSolicitudes.Count)" -ForegroundColor Green
    foreach ($s in $misSolicitudes) {
        $color = switch ($s.estado) {
            "Aprobada" { "Green" }
            "Rechazada" { "Red" }
            default { "Yellow" }
        }
        Write-Host "   - ID $($s.id): $($s.sku) - Estado: $($s.estado)" -ForegroundColor $color
        if ($s.autorizador) {
            Write-Host "     Autorizado por: $($s.autorizador)"
        }
        if ($s.comentarios_autorizador) {
            Write-Host "     Comentarios: $($s.comentarios_autorizador)"
        }
    }
} catch {
    Write-Host "   ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== PRUEBA COMPLETADA ===" -ForegroundColor Cyan
Write-Host "El vendedor ahora puede cotizar HP30B-CTO-01 a $20,000 con autorización aprobada.`n"
