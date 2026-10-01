$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw '请先创建 .venv 并安装 requirements.txt' }
$Process = Start-Process -FilePath $Python -ArgumentList @('-m','streamlit','run',(Join-Path $Root 'app.py'),'--server.address','127.0.0.1','--server.port','8503','--server.headless','true') -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$Process.Id | Set-Content -LiteralPath (Join-Path $Root '.streamlit.pid')
Write-Host "已启动：http://127.0.0.1:8503 (PID $($Process.Id))"

