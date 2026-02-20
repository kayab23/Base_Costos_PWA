$base='http://127.0.0.1:8000'
$user='admin'
$pass='Admin123!'
try {
    $login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded' -ErrorAction Stop
    $token=$login.access_token
    Write-Output "Login OK (token len: $($token.Length))"
    $url = $base + '/pricing/listas?sku=SKU123&transporte=maritimo'
    Write-Output "GET $url"
    $r = Invoke-WebRequest -Uri $url -Method Get -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 20 -UseBasicParsing -ErrorAction Stop
    Write-Output "Status: $($r.StatusCode)"
    Write-Output "Content-Type: $($r.Headers['Content-Type'])"
    Write-Output "Content-Length (estimated): $($r.RawContentLength)"
    $out = Join-Path $PSScriptRoot 'pricing_raw_body.bin'
    if ($r.Content) {
        $r.Content | Out-File -Encoding utf8 $out
        Write-Output "Saved textual content to $out"
    } elseif ($r.RawContentLength -gt 0) {
        $r.Content | Out-File -Encoding utf8 $out
        Write-Output "Saved content to $out"
    } else {
        Write-Output "No response body to save."
    }
} catch {
    Write-Output 'ERROR:'
    Write-Output $_.Exception.Message
}