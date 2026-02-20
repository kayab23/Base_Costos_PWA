param(
    [string]$base = 'http://127.0.0.1:8000',
    [string]$user = 'vendedor1',
    [string]$pass = 'Vend123!',
    [string]$sku = 'HP30B-CTO-01',
    [string]$transporte = 'maritimo'
)

try {
    $login = Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token = $login.access_token
    Write-Output "Login OK (usuario: $user, token len: $($token.Length))"

    $params = "?sku=$sku&transporte=$transporte"
    $listResp = Invoke-RestMethod -Uri ($base + '/pricing/listas' + $params) -Method Get -Headers @{ Authorization = "Bearer $token" } -ErrorAction Stop
    if (-not $listResp -or $listResp.Count -eq 0) {
        Write-Output "No se encontraron listas para SKU=$sku transporte=$transporte"
        exit 1
    }
    $row = $listResp[0]
    $precio_base = 0
    if ($null -ne $row.precio_base_mxn) { $precio_base = [double]$row.precio_base_mxn }
    elseif ($null -ne $row.costo_base_mxn) { $precio_base = [double]$row.costo_base_mxn }
    $precio_vendedor_min = 0
    if ($null -ne $row.precio_vendedor_min) { $precio_vendedor_min = [double]$row.precio_vendedor_min }
    elseif ($null -ne $row.precio_minimo_lista) { $precio_vendedor_min = [double]$row.precio_minimo_lista }

    Write-Output "Precio base: $precio_base"
    Write-Output "Precio vendedor min: $precio_vendedor_min"

    if ($precio_vendedor_min -le $precio_base) {
        Write-Output "No hay rango válido entre precio_base y precio_vendedor_min para crear solicitud. Ajusta SKU o transporte."
        exit 1
    }

    # Elegir un precio en el medio del rango (seguromente válido)
    $precio_propuesto = [math]::Round(($precio_base + $precio_vendedor_min) / 2, 2)
    Write-Output "Usando precio_propuesto calculado: $precio_propuesto"

    $payload = [PSCustomObject]@{
        sku = $sku
        transporte = $transporte
        precio_propuesto = $precio_propuesto
        cliente = 'Cliente Prueba'
        cantidad = 1
        justificacion = 'Prueba automatizada con usuario vendedor'
    }
    $json = $payload | ConvertTo-Json -Depth 5
    Write-Output "POST $base/autorizaciones/solicitar"
    $resp = Invoke-RestMethod -Uri ($base + '/autorizaciones/solicitar') -Method Post -Headers @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' } -Body $json -ErrorAction Stop
    $out = Join-Path $PSScriptRoot 'solicitud_vendedor_resp.json'
    $resp | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $out
    Write-Output "Solicitud enviada OK. Guardada en $out"
} catch {
    Write-Output 'ERROR:'
    Write-Output $_.Exception.Message
    if ($_.InvocationInfo) { Write-Output $_.InvocationInfo.PositionMessage }
    if ($_.Exception.Response) {
        try { $body = $_.Exception.Response.GetResponseStream() | % { [System.IO.StreamReader]::new($_).ReadToEnd() }; Write-Output "Response body: $body"; $body | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'solicitud_vendedor_error.json') } catch { }
    }
    exit 1
}