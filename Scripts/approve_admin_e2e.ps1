$base='http://127.0.0.1:8000'
$login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username='admin'; password='Admin123!' } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
$token=$login.access_token
$body = @{ comentarios = 'Aprobada por admin en prueba E2E' } | ConvertTo-Json
Invoke-RestMethod -Uri ($base + '/autorizaciones/20/aprobar') -Method Put -Headers @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' } -Body $body -ErrorAction Stop | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'aprobar_admin_resp.json')
Write-Output "Aprobación OK"
