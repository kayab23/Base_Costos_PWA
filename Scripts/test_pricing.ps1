$base='http://127.0.0.1:8000'
$user='admin'
$pass='Admin123!'
try {
    $login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token=$login.access_token
    Write-Output "Login OK (token len: $($token.Length))"
    $url = $base + '/pricing/listas?sku=SKU123&transporte=maritimo'
    Write-Output "GET $url"
    $resp = Invoke-RestMethod -Uri $url -Method Get -Headers @{ Authorization = "Bearer $token" } -ErrorAction Stop
    $resp | ConvertTo-Json -Depth 6 | Out-File -Encoding UTF8 .\Scripts\pricing_resp.json
    Write-Output "Saved response to .\Scripts\pricing_resp.json"
} catch {
    Write-Output 'ERROR:'
    Write-Output $_.Exception.Message
}