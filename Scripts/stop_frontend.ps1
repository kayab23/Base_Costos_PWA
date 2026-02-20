# Stop frontend static server (http.server or process listening on port 5173)
$pids = @()
try {
    $pids += Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
} catch { }
try {
    $pids += Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'http.server' -or $_.CommandLine -match 'frontend' -or $_.CommandLine -match '5173' } | Select-Object -ExpandProperty ProcessId -ErrorAction SilentlyContinue
} catch { }
$pids = @($pids) | Where-Object { $_ } | Sort-Object -Unique
if ($pids.Count -gt 0) {
    foreach ($p in $pids) {
        try { Stop-Process -Id $p -Force -ErrorAction Stop; Write-Output "Stopped PID: $p" } catch { Write-Output "Failed to stop PID: $p" }
    }
} else {
    Write-Output 'No matching frontend processes found.'
}
# List common frontend ports status
Write-Output 'Current listeners on 5173:'
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,RemoteAddress,State,OwningProcess | Format-Table -AutoSize
