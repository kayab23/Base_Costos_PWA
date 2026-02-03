$ErrorActionPreference = 'Stop'
# Llamada a curl.exe asegurando captura de stdout
$json = & curl.exe -sS -X POST -d 'username=admin&password=Admin123!' 'http://127.0.0.1:8000/auth/login' 2>&1
if (-not $json) {
	Write-Output 'ERROR: No se obtuvo respuesta del endpoint /auth/login'
	exit 2
}
Write-Output 'RAW_RESPONSE:'
Write-Output $json
try {
	$tok = (ConvertFrom-Json $json).access_token
} catch {
	Write-Output 'ERROR: no se pudo parsear JSON de /auth/login'
	exit 3
}
Write-Output '---ACCESS_TOKEN---'
Write-Output $tok
Write-Output '---AUTH_ME---'
& curl.exe -sS -H "Authorization: Bearer $tok" 'http://127.0.0.1:8000/auth/me'
