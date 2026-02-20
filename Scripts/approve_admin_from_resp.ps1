$base='http://127.0.0.1:8000'
$resp = Get-Content (Join-Path $PSScriptRoot 'solicitud_vendedor_resp.json') -Raw | ConvertFrom-Json
$id = $resp.id
Write-Output "Aprobar solicitud id=$id"
$login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username='admin'; password='Admin123!' } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
$token=$login.access_token
$body = @{ comentarios = 'Aprobada por admin en prueba E2E' } | ConvertTo-Json
Invoke-RestMethod -Uri ($base + "/autorizaciones/$id/aprobar") -Method Put -Headers @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' } -Body $body -ErrorAction Stop | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'aprobar_admin_resp.json')
Write-Output "Aprobación OK para id=$id"
