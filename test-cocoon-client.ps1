# Тестовый скрипт для запуска COCOON client-runner
# Запуск из корня проекта

$ErrorActionPreference = "Stop"

# Получаем текущую директорию (корень проекта)
$ProjectRoot = $PSScriptRoot
$CocoonDir = Join-Path $ProjectRoot "cocoon"
$BuildDir = Join-Path $CocoonDir "build\Release"
$ConfigFile = Join-Path $CocoonDir "client-config.json"
$ClientRunner = Join-Path $BuildDir "client-runner.exe"

Write-Host "=== Тест запуска COCOON Client ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Cocoon Dir: $CocoonDir" -ForegroundColor Gray
Write-Host "Build Dir: $BuildDir" -ForegroundColor Gray

# Проверки
Write-Host "`nПроверка файлов..." -ForegroundColor Yellow

if (-not (Test-Path $ClientRunner)) {
    Write-Host "[ERROR] client-runner.exe не найден: $ClientRunner" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] client-runner.exe найден" -ForegroundColor Green

if (-not (Test-Path $ConfigFile)) {
    Write-Host "[ERROR] Конфигурационный файл не найден: $ConfigFile" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Конфигурационный файл найден" -ForegroundColor Green

# Проверка DLL
$RequiredDLLs = @("libcrypto-3-x64.dll", "libssl-3-x64.dll", "libsodium.dll")
foreach ($dll in $RequiredDLLs) {
    $dllPath = Join-Path $BuildDir $dll
    if (Test-Path $dllPath) {
        Write-Host "[OK] $dll найден" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] $dll не найден" -ForegroundColor Yellow
    }
}

Write-Host "`nЗапуск client-runner..." -ForegroundColor Cyan
Write-Host "Команда: $ClientRunner --config `"$ConfigFile`" -v3" -ForegroundColor Gray
Write-Host "Для остановки нажмите Ctrl+C`n" -ForegroundColor Yellow

# Запуск (из корня cocoon, чтобы пути в конфиге работали)
Set-Location $CocoonDir
try {
    & $ClientRunner --config $ConfigFile -v3
} catch {
    Write-Host "`n[ERROR] Ошибка при запуске: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
