$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root '.streamlit.pid'
if (Test-Path -LiteralPath $PidFile) {
    $AppPid = [int](Get-Content -LiteralPath $PidFile)
    Stop-Process -Id $AppPid -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PidFile -Force
    Write-Host '服务已停止'
} else { Write-Host '未找到运行记录' }

