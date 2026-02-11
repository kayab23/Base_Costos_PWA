$ErrorActionPreference = 'Stop'
# Llamada a curl.exe asegurando captura de stdout
# Usa variables de entorno `TEST_LOGIN_USER` y `TEST_LOGIN_PASS` si existen, sino valores por defecto
$user = if ($env:TEST_LOGIN_USER) { $env:TEST_LOGIN_USER } else { 'admin' }
$pass = if ($env:TEST_LOGIN_PASS) { $env:TEST_LOGIN_PASS } else { 'Admin123!' }
$body = "username=$user&password=$pass"
$json = & curl.exe -sS -X POST -d $body 'http://127.0.0.1:8000/auth/login' 2>&1
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
