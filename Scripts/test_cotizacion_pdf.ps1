# Test script: login and POST to /cotizacion/pdf
$base = 'http://127.0.0.1:8000'
$user = 'admin'
$pass = 'Admin123!'

Write-Output "Logging in to $base/auth/login with user $user"
try {
    $loginResp = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -Body @{ username = $user; password = $pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token = $loginResp.access_token
    if (-not $token) { Write-Output "Login did not return access_token"; exit 2 }
    Write-Output "Login OK, token length: $($token.Length)"
} catch {
    Write-Output "Login error: $($_.Exception.Message)"
    exit 1
}

$json = @'
{
  "cliente": "Demo Cliente",
  "items": [
    {
      "sku": "SKU123",
      "descripcion": "Producto demo",
      "cantidad": 2,
      "precio_maximo": 1000,
      "precio_maximo_lista": 1000,
      "precio_vendedor_min": 800,
      "precio_minimo_lista": 800,
      "monto_propuesto": 850,
      "logo_path": null,
      "proveedor": "Prov",
      "origen": "MX"
    }
  ]
}
'@

Write-Output "--- Request JSON ---"
Write-Output $json

$outFile = Join-Path $PSScriptRoot 'tmp_cotizacion.pdf'
try {
    Write-Output "POSTing to $base/cotizacion/pdf ..."
    $headers = @{ Authorization = "Bearer $token" }
    Invoke-WebRequest -Uri "$base/cotizacion/pdf" -Method Post -Headers $headers -Body $json -ContentType 'application/json' -TimeoutSec 20 -OutFile $outFile -ErrorAction Stop
    $fi = Get-Item $outFile
    Write-Output "Saved PDF to $outFile (size: $($fi.Length) bytes)"
} catch {
    Write-Output "Request error: $($_.Exception.Message)"
    if ($_.Exception.Response -ne $null) {
        try { $txt = $_.Exception.Response.GetResponseStream() | Select-Object -First 1 }
        catch { }
    }
    exit 3
}

Write-Output "Done."