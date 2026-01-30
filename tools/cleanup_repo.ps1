<#
Cleanup script for removing temporary test artifacts safely.
Run from the repository root:
  powershell -ExecutionPolicy Bypass -File .\tools\cleanup_repo.ps1
This script will remove known test response JSONs, temporary outputs and __pycache__ directories.
It will NOT remove source code or the virtualenv by default.
#>
$candidates = @(
    'tmp_app_js.txt',
    'Scripts\aprobar_admin_resp.json',
    'Scripts\aprobar_direccion_id17_resp.json',
    'Scripts\aprobar_direccion_resp.json',
    'Scripts\aprobar_sse_resp.json',
    'Scripts\aprobar_sse_resp2.json',
    'Scripts\aprobar_admin_resp.json',
    'Scripts\mis_solicitudes_after_approval.json',
    'Scripts\mis_solicitudes_after_attempt17.json',
    'Scripts\mis_solicitudes_after_reintento.json',
    'Scripts\mis_solicitudes_vendedor.json',
    'Scripts\mis_solicitudes_vendedor_after_aprobacion.json',
    'Scripts\pendientes_gercom.json',
    'Scripts\precios_id17.json',
    'Scripts\pricing_resp.json',
    'Scripts\pricing_raw_body.bin',
    'Scripts\solicitud_resp_error.json',
    'Scripts\solicitud_sse_resp.json',
    'Scripts\solicitud_sse_resp2.json',
    'Scripts\solicitud_vendedor_resp.json',
    'Scripts\sse_output.txt'
)

Write-Host "Cleaning temporary/testing artifacts..." -ForegroundColor Cyan

$root = Get-Location

foreach ($f in $candidates) {
    $path = Join-Path $root $f
    if (Test-Path $path) {
        try {
            Remove-Item -Force -LiteralPath $path -ErrorAction Stop
            Write-Host "Removed: $f" -ForegroundColor Green
        } catch {
            Write-Host "Failed to remove: $f - $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Not found (skipping): $f" -ForegroundColor DarkGray
    }
}

# Remove compiled python caches
Get-ChildItem -Path $root -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' } | ForEach-Object {
    try { Remove-Item -Recurse -Force -LiteralPath $_.FullName; Write-Host "Removed __pycache__: $($_.FullName)" -ForegroundColor Green } catch { Write-Host "Failed to remove __pycache__: $($_.FullName)" -ForegroundColor Yellow }
}

# Optionally remove *.pyc files
Get-ChildItem -Path $root -Recurse -Include '*.pyc' -File -ErrorAction SilentlyContinue | ForEach-Object {
    try { Remove-Item -Force -LiteralPath $_.FullName; Write-Host "Removed pyc: $($_.FullName)" -ForegroundColor Green } catch { }
}

Write-Host "Cleanup complete. Review git status and commit changes if desired." -ForegroundColor Cyan