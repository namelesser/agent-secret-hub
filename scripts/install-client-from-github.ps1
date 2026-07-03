param(
    [string]$RepoUrl = "https://github.com/namelesser/agent-secret-hub.git",
    [string]$Branch = "main",
    [string]$InstallDir = "$env:USERPROFILE\.agent-secret-hub\app",
    [string]$ServerUrl = "",
    [string]$DeviceName = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git not found. Install Git for Windows first: https://git-scm.com/download/win"
}

Write-Host "==> Fetch project: $RepoUrl"
if (Test-Path (Join-Path $InstallDir ".git")) {
    git -C $InstallDir fetch origin $Branch
    git -C $InstallDir checkout $Branch
    git -C $InstallDir reset --hard "origin/$Branch"
} else {
    if (Test-Path $InstallDir) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
    }
    git clone --branch $Branch $RepoUrl $InstallDir
}

Write-Host "==> Run client installer"
$script = Join-Path $InstallDir "scripts\install-client.ps1"
& powershell -ExecutionPolicy Bypass -File $script -ServerUrl $ServerUrl -DeviceName $DeviceName
