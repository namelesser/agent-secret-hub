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

Write-Host "==> 安装客户端依赖"
if ($PyLauncher) {
    & $PyLauncher.Source -3 -m venv (Join-Path $SourceDir ".venv")
} elseif ($Python) {
    & $Python.Source -m venv (Join-Path $SourceDir ".venv")
} else {
    throw "未找到 Python。请先安装 Python 3.10+。"
}
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e $SourceDir

New-Item -ItemType Directory -Force $InstallBin | Out-Null
$Wrapper = Join-Path $InstallBin "agent-secret.cmd"
Set-Content -Encoding ASCII -Path $Wrapper -Value "@echo off`r`n`"$AgentSecretExe`" %*`r`n"

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($UserPath -split ";") -notcontains $InstallBin) {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallBin", "User")
    Write-Host "已把 $InstallBin 加入用户 PATH。请重新打开终端后使用 agent-secret。"
}

Write-Host "==> 客户端安装完成"
Write-Host "命令位置：$Wrapper"

if ($ServerUrl -and $DeviceName) {
    & $AgentSecretExe login --name $DeviceName --server $ServerUrl
} else {
    Write-Host "登录示例：agent-secret login --name my-laptop --server http://服务器IP:8000"
}
