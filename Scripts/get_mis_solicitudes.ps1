$base='http://127.0.0.1:8000'
$user='vendedor1'
$pass='Vend123!'
try {
    $login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token=$login.access_token
    Write-Output "Login OK (token len: $($token.Length))"
    $resp = Invoke-RestMethod -Uri ($base + '/autorizaciones/mis-solicitudes') -Method Get -Headers @{ Authorization = "Bearer $token" } -ErrorAction Stop
    $out = Join-Path $PSScriptRoot 'mis_solicitudes_vendedor.json'
    $resp | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $out
    Write-Output "Saved to $out"
} catch {
    Write-Output 'ERROR:'
    Write-Output $_.Exception.Message
}
