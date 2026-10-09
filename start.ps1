$ErrorActionPreference = 'Stop'
$projectPath = $PSScriptRoot
$backendPath = Join-Path $projectPath 'backend'
$frontendPath = Join-Path $projectPath 'frontend'
$pythonPath = Join-Path $backendPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    $pythonPath = (Get-Command python).Source
}
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules'))) {
    throw 'Frontend dependencies are missing. Run npm ci in frontend first.'
}
& $pythonPath -c 'import fastapi, uvicorn, multipart'
if ($LASTEXITCODE -ne 0) { throw 'Install backend/requirements.txt first.' }
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $backendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backendPath 'server.log') -RedirectStandardError (Join-Path $backendPath 'server-error.log')
}
if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
    $npmPath = (Get-Command npm.cmd).Source
    Start-Process -FilePath $npmPath -ArgumentList 'run dev' -WorkingDirectory $frontendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $frontendPath 'server.log') -RedirectStandardError (Join-Path $frontendPath 'server-error.log')
}
Write-Output 'Job Hunt OS: http://127.0.0.1:5173'
Write-Output 'API docs: http://127.0.0.1:8000/docs'
