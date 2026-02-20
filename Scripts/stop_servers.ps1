# Stop servers listening on port 8000 and processes matching uvicorn/app.main:app
$pids = @()
Try {
    $pids += Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
} Catch { }
Try {
    $pids += Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn|app.main:app' } | Select-Object -ExpandProperty ProcessId -ErrorAction SilentlyContinue
} Catch { }
$pids = @($pids) | Where-Object { $_ } | Sort-Object -Unique
if ($pids.Count -gt 0) {
    foreach ($p in $pids) {
        try { Stop-Process -Id $p -Force -ErrorAction Stop; Write-Output "Stopped PID: $p" } catch { Write-Output "Failed to stop PID: $p" }
    }
} else {
    Write-Output 'No matching processes found.'
}
Write-Output 'Current listeners on 8000:'
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,RemoteAddress,State,OwningProcess | Format-Table -AutoSize
