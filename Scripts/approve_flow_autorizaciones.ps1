$base='http://127.0.0.1:8000'

function Login($user,$pass){
    $login=Invoke-RestMethod -Uri ($base + '/auth/login') -Method Post -Body @{ username=$user; password=$pass } -ContentType 'application/x-www-form-urlencoded'
    return $login.access_token
}

try{
    Write-Output "== 1) Listar pendientes como gercom1 =="
    $token = Login 'gercom1' 'GerCom123!'
    $pend = Invoke-RestMethod -Uri ($base + '/autorizaciones/pendientes') -Method Get -Headers @{ Authorization = "Bearer $token" } -ErrorAction Stop
    $outPend = Join-Path $PSScriptRoot 'pendientes_gercom.json'
    $pend | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPend
    Write-Output "Guardado: $outPend"
    Write-Output "Contenido de pendientes (primeros 5):"
    $pend | Select-Object -First 5 | Format-List | Out-String | Write-Output

    if ($null -eq $pend -or $pend.Count -eq 0) {
        Write-Output "No hay solicitudes pendientes visibles para gercom1. Usaré fallback id=16 para la prueba de aprobación (Direccion)."
        $id = 16
    } else {
        $id = $pend[0].id
        Write-Output "Usando id=$id (primer pendiente) para intento de aprobación por gercom1"
    }

    Write-Output "== 2) Intentar aprobar id=$id como gercom1 =="
    try{
        $resp = Invoke-RestMethod -Uri ($base + "/autorizaciones/$id/aprobar") -Method Put -Headers @{ Authorization = "Bearer $token" } -Body (ConvertTo-Json @{ comentarios = 'Aprobada por gercom1 en prueba' }) -ContentType 'application/json' -ErrorAction Stop
        Write-Output "Aprobación con gercom1 OK:"; $resp | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'aprobar_gercom_resp.json'); Write-Output (Get-Content (Join-Path $PSScriptRoot 'aprobar_gercom_resp.json'))
    } catch {
        Write-Output "Aprobación por gercom1 falló:"
        Write-Output $_.Exception.Message
        if ($_.Exception.Response) {
            try { $b = $_.Exception.Response.GetResponseStream() | % { [System.IO.StreamReader]::new($_).ReadToEnd() }; Write-Output "Response body: $b" } catch { }
        }
        Write-Output "Intentaré aprobar como 'direccion1' ahora."

        # Aprobar como direccion1
        $token2 = Login 'direccion1' 'Direcc123!'
        try{
            $resp2 = Invoke-RestMethod -Uri ($base + "/autorizaciones/$id/aprobar") -Method Put -Headers @{ Authorization = "Bearer $token2" } -Body (ConvertTo-Json @{ comentarios = 'Aprobada por direccion1 en prueba' }) -ContentType 'application/json' -ErrorAction Stop
            $resp2 | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'aprobar_direccion_resp.json')
            Write-Output "Aprobación por direccion1 OK. Respuesta guardada en aprobar_direccion_resp.json"
            Write-Output (Get-Content (Join-Path $PSScriptRoot 'aprobar_direccion_resp.json'))
        } catch {
            Write-Output "Aprobación por direccion1 falló:"; Write-Output $_.Exception.Message
            if ($_.Exception.Response) { try { $b = $_.Exception.Response.GetResponseStream() | % { [System.IO.StreamReader]::new($_).ReadToEnd() }; Write-Output "Response body: $b" } catch { } }
        }
    }

    Write-Output "== 3) Listar mis solicitudes como vendedor1 =="
    $tokenv = Login 'vendedor1' 'Vend123!'
    $mis = Invoke-RestMethod -Uri ($base + '/autorizaciones/mis-solicitudes') -Method Get -Headers @{ Authorization = "Bearer $tokenv" } -ErrorAction Stop
    $mis | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'mis_solicitudes_after_approval.json')
    Write-Output "Guardado: mis_solicitudes_after_approval.json"
    Write-Output (Get-Content -Raw (Join-Path $PSScriptRoot 'mis_solicitudes_after_approval.json'))

} catch {
    Write-Output 'ERROR SCRIPT:'
    Write-Output $_.Exception.Message
}
