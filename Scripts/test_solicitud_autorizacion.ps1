$base='http://127.0.0.1:8000'
$user='admin'
$pass='Admin123!'
try {
    $login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token=$login.access_token
    Write-Output "Login OK (token len: $($token.Length))"
    $payload = @{ 
        sku = 'SKU123';
        transporte = 'maritimo';
        precio_propuesto = 16000.0;
        cliente = 'Cliente de Prueba';
        cantidad = 1;
        justificacion = 'Prueba automatizada - verificar 422'
    }
    $json = $payload | ConvertTo-Json -Depth 5
    Write-Output "POST $base/autorizaciones/solicitar"
    $resp = Invoke-WebRequest -Uri ($base + '/autorizaciones/solicitar') -Method Post -Headers @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' } -Body $json -ErrorAction Stop -UseBasicParsing
    Write-Output "Status: $($resp.StatusCode)"
    $out = Join-Path $PSScriptRoot 'solicitud_resp.json'
    if ($resp.Content) { $resp.Content | Out-File -Encoding utf8 $out; Write-Output "Saved response to $out" } else { Write-Output "Empty response body" }
} catch {
    Write-Output 'ERROR:'
    if ($_.Exception.Response) {
        try { $body = $_.Exception.Response.GetResponseStream() | % { [System.IO.StreamReader]::new($_).ReadToEnd() }; Write-Output "Response body: $body"; $body | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'solicitud_resp_error.json') } catch { }
        try { $status = $_.Exception.Response.StatusCode.value__; Write-Output "Status: $status" } catch { }
    }
    Write-Output $_.Exception.Message
}