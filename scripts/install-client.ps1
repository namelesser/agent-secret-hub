param(
    [string]$ServerUrl = "",
    [string]$DeviceName = "",
    [string]$InstallBin = "$env:LOCALAPPDATA\AgentSecretHub\bin"
)

$ErrorActionPreference = "Stop"
$SourceDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $SourceDir ".venv\Scripts\python.exe"
$AgentSecretExe = Join-Path $SourceDir ".venv\Scripts\agent-secret.exe"
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
$Python = Get-Command python -ErrorAction SilentlyContinue

Write-Host "==> Install client dependencies"
if ($PyLauncher) {
    & $PyLauncher.Source -3 -m venv (Join-Path $SourceDir ".venv")
} elseif ($Python) {
    & $Python.Source -m venv (Join-Path $SourceDir ".venv")
} else {
    throw "Python not found. Install Python 3.10+ first."
}
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e $SourceDir

New-Item -ItemType Directory -Force $InstallBin | Out-Null
$Wrapper = Join-Path $InstallBin "agent-secret.cmd"
$PowerShellWrapper = Join-Path $InstallBin "agent-secret.ps1"
Set-Content -Encoding UTF8 -Path $PowerShellWrapper -Value @"
`$ErrorActionPreference = "SilentlyContinue"
if (Test-Path "$SourceDir\.git") {
    git -C "$SourceDir" fetch origin main *> `$null
    if (`$LASTEXITCODE -eq 0) {
        git -C "$SourceDir" checkout main *> `$null
        git -C "$SourceDir" reset --hard origin/main *> `$null
        & "$VenvPython" -m pip install -e "$SourceDir" *> `$null
    }
}
& "$AgentSecretExe" @args
exit `$LASTEXITCODE
"@
Set-Content -Encoding ASCII -Path $Wrapper -Value "@echo off`r`npowershell -ExecutionPolicy Bypass -File `"$PowerShellWrapper`" %*`r`n"

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($UserPath -split ";") -notcontains $InstallBin) {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallBin", "User")
    Write-Host "Added $InstallBin to user PATH. Reopen the terminal before using agent-secret."
}

Write-Host "==> Client install complete"
Write-Host "Command path: $Wrapper"

if ($ServerUrl -and $DeviceName) {
    & $AgentSecretExe login --name $DeviceName --server $ServerUrl
} else {
    Write-Host "Login example: agent-secret login --name my-laptop --server http://SERVER_IP:8000"
}
