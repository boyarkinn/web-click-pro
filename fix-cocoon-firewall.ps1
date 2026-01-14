# Скрипт для создания правил firewall для COCOON client-runner
# Запустите от имени администратора: правой кнопкой -> "Запуск от имени администратора"

$exePath = "C:\Users\aleks\OneDrive\Desktop\web-click-pro\cocoon\build\Release\client-runner.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "[ERROR] client-runner.exe не найден: $exePath" -ForegroundColor Red
    exit 1
}

Write-Host "=== Настройка Firewall для COCOON Client ===" -ForegroundColor Cyan

# Удаляем старые правила, если есть
Remove-NetFirewallRule -DisplayName "COCOON Client UDP Outbound" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "COCOON Client TCP Outbound" -ErrorAction SilentlyContinue

# Создаем правила для исходящего UDP трафика (для ADNL)
New-NetFirewallRule -DisplayName "COCOON Client UDP Outbound" `
    -Direction Outbound `
    -Program $exePath `
    -Action Allow `
    -Protocol UDP `
    -Profile Any `
    -Enabled True

# Создаем правила для исходящего TCP трафика
New-NetFirewallRule -DisplayName "COCOON Client TCP Outbound" `
    -Direction Outbound `
    -Program $exePath `
    -Action Allow `
    -Protocol TCP `
    -Profile Any `
    -Enabled True

Write-Host "[OK] Правила firewall созданы!" -ForegroundColor Green
Write-Host ""
Write-Host "Проверка правил:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "*COCOON*" | Select-Object DisplayName, Enabled, Direction, Action | Format-Table -AutoSize
