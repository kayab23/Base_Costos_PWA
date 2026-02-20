$ErrorActionPreference = 'Stop'
# Perform login
$json = & curl.exe -sS -X POST -d 'username=admin&password=Admin123!' 'http://127.0.0.1:8000/auth/login'
if (-not $json) { Write-Output 'ERROR: No response from /auth/login'; exit 2 }
try { $tok = (ConvertFrom-Json $json).access_token } catch { Write-Output 'ERROR parsing login JSON'; exit 3 }
Write-Output 'ACCESS_TOKEN=' + $tok
# Call /api/cotizaciones with token
$resp = & curl.exe -sS -H "Authorization: Bearer $tok" 'http://127.0.0.1:8000/api/cotizaciones?limit=1'
Write-Output 'COTIZACIONES_RESPONSE:'
Write-Output $resp
