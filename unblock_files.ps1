# Script PowerShell para desbloquear archivos RT-11 Extractor
# Ejecutar como: powershell -ExecutionPolicy Bypass -File unblock_files.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "RT-11 Extractor - Desbloqueador de Archivos" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Obtener directorio actual
$currentDir = Get-Location

# Buscar archivos .pyz bloqueados
Write-Host "Buscando archivos .pyz bloqueados..." -ForegroundColor Yellow

$pyzFiles = Get-ChildItem -Path $currentDir -Filter "*.pyz" -Recurse

if ($pyzFiles.Count -eq 0) {
    Write-Host "No se encontraron archivos .pyz en el directorio actual." -ForegroundColor Red
    Write-Host "Verifica que hayas extraído correctamente el ZIP." -ForegroundColor Yellow
    pause
    exit
}

$blockedFiles = @()
$unblockedFiles = @()

foreach ($file in $pyzFiles) {
    # Verificar si el archivo está bloqueado
    $zone = Get-Content -Path "$($file.FullName):Zone.Identifier" -ErrorAction SilentlyContinue
    
    if ($zone) {
        Write-Host "Archivo bloqueado encontrado: $($file.Name)" -ForegroundColor Red
        $blockedFiles += $file
        
        # Desbloquear archivo
        try {
            Unblock-File -Path $file.FullName
            Write-Host "  ✓ Desbloqueado exitosamente" -ForegroundColor Green
            $unblockedFiles += $file
        }
        catch {
            Write-Host "  ✗ Error desbloqueando: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Archivo OK: $($file.Name)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "RESUMEN:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Write-Host "Archivos .pyz encontrados: $($pyzFiles.Count)" -ForegroundColor White
Write-Host "Archivos bloqueados: $($blockedFiles.Count)" -ForegroundColor Red
Write-Host "Archivos desbloqueados: $($unblockedFiles.Count)" -ForegroundColor Green

if ($blockedFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "¡Todos los archivos están listos para usar!" -ForegroundColor Green
}
elseif ($unblockedFiles.Count -eq $blockedFiles.Count) {
    Write-Host ""
    Write-Host "¡Todos los archivos han sido desbloqueados exitosamente!" -ForegroundColor Green
    Write-Host "Ahora puedes ejecutar los archivos .bat normalmente." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "ADVERTENCIA: Algunos archivos no pudieron ser desbloqueados." -ForegroundColor Red
    Write-Host "Intenta ejecutar este script como Administrador." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
