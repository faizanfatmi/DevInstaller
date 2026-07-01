<#
.SYNOPSIS
    DevInstaller cross-platform setup script (Windows).

.DESCRIPTION
    Fetches the latest release, downloads the Windows installer asset, verifies
    it (SHA256 when a checksum asset is published), installs it silently, and
    logs progress throughout.

.NOTES
    Configuration via environment variables (all optional):
      DEVINSTALLER_PROVIDER    'gitlab' (default) or 'github'
      DEVINSTALLER_GITLAB_HOST GitLab host (default: gitlab.com)
      DEVINSTALLER_PROJECT     URL-encoded GitLab project path or numeric ID
                               (default: faizan-fatmi-group%2Fdevinstaller)
      DEVINSTALLER_GITHUB_REPO 'owner/repo' when PROVIDER=github
      DEVINSTALLER_VERSION     release tag to install (default: latest)

.EXAMPLE
    irm <url>/install.ps1 | iex
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$AppName     = 'DevInstaller'
$Provider    = if ($env:DEVINSTALLER_PROVIDER)    { $env:DEVINSTALLER_PROVIDER }    else { 'gitlab' }
$GitLabHost  = if ($env:DEVINSTALLER_GITLAB_HOST) { $env:DEVINSTALLER_GITLAB_HOST } else { 'gitlab.com' }
$Project     = if ($env:DEVINSTALLER_PROJECT)     { $env:DEVINSTALLER_PROJECT }     else { 'faizan-fatmi-group%2Fdevinstaller' }
$GitHubRepo  = $env:DEVINSTALLER_GITHUB_REPO
$Version     = if ($env:DEVINSTALLER_VERSION)     { $env:DEVINSTALLER_VERSION }     else { 'latest' }

function Write-Info  { param($m) Write-Host "[devinstaller] $m" -ForegroundColor Cyan }
function Write-Ok    { param($m) Write-Host "[devinstaller] $m" -ForegroundColor Green }
function Write-Warn2 { param($m) Write-Host "[devinstaller] $m" -ForegroundColor Yellow }
function Write-Stage { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Die         { param($m) Write-Host "[devinstaller] ERROR: $m" -ForegroundColor Red; exit 1 }

function Get-AssetUrls {
    if ($Provider -eq 'github') {
        if (-not $GitHubRepo) { Die 'DEVINSTALLER_GITHUB_REPO must be set when PROVIDER=github.' }
        $api = if ($Version -eq 'latest') {
            "https://api.github.com/repos/$GitHubRepo/releases/latest"
        } else {
            "https://api.github.com/repos/$GitHubRepo/releases/tags/$Version"
        }
        Write-Info "Resolving GitHub release: $api"
        $rel = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'devinstaller' }
        return @($rel.assets | ForEach-Object { $_.browser_download_url })
    }
    else {
        $base = "https://$GitLabHost/api/v4/projects/$Project/releases"
        $api  = if ($Version -eq 'latest') { "$base/permalink/latest" } else { "$base/$Version" }
        Write-Info "Resolving GitLab release: $api"
        $rel = Invoke-RestMethod -Uri $api
        return @($rel.assets.links | ForEach-Object { $_.direct_asset_url })
    }
}

function Select-Asset {
    param([string[]] $Urls)
    $asset = $Urls | Where-Object { $_ -match '\.exe($|\?)' } | Select-Object -First 1
    if (-not $asset) { $asset = $Urls | Where-Object { $_ -match '\.msi($|\?)' } | Select-Object -First 1 }
    if (-not $asset) { Die 'No .exe or .msi asset found in the release.' }
    $checksum = $Urls | Where-Object { $_ -eq "$asset.sha256" } | Select-Object -First 1
    return [PSCustomObject]@{ Asset = $asset; Checksum = $checksum }
}

function Test-Checksum {
    param([string] $File, [string] $ChecksumUrl)
    if (-not $ChecksumUrl) { Write-Warn2 'No published checksum; skipping verification.'; return }
    $expected = (Invoke-WebRequest -Uri $ChecksumUrl -UseBasicParsing).Content.Trim().Split()[0]
    if (-not $expected) { Write-Warn2 'Checksum asset empty; skipping.'; return }
    $actual = (Get-FileHash -Path $File -Algorithm SHA256).Hash.ToLower()
    if ($expected.ToLower() -ne $actual) {
        Die "Checksum mismatch! expected=$expected actual=$actual"
    }
    Write-Ok 'Checksum verified.'
}

try {
    Write-Stage "$AppName setup"
    Write-Info "Detected platform: windows/$env:PROCESSOR_ARCHITECTURE"

    Write-Stage 'Resolving latest release'
    $urls = Get-AssetUrls
    if (-not $urls -or $urls.Count -eq 0) { Die 'No downloadable assets found in the release.' }
    $sel = Select-Asset -Urls $urls
    Write-Info "Selected asset: $($sel.Asset)"

    Write-Stage 'Downloading'
    $tmp  = Join-Path $env:TEMP ([System.IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $tmp | Out-Null
    $name = [System.IO.Path]::GetFileName(($sel.Asset -split '\?')[0])
    $file = Join-Path $tmp $name
    try {
        Invoke-WebRequest -Uri $sel.Asset -OutFile $file -UseBasicParsing
    } catch {
        Die "Download failed: $($_.Exception.Message)"
    }
    Write-Ok "Downloaded $name"

    Write-Stage 'Verifying'
    Test-Checksum -File $file -ChecksumUrl $sel.Checksum

    Write-Stage 'Installing'
    if ($file -match '\.msi$') {
        $p = Start-Process msiexec.exe -ArgumentList "/i `"$file`" /qn" -Wait -PassThru
    } else {
        # NSIS/Inno silent switches; /S covers NSIS, /VERYSILENT covers Inno.
        $p = Start-Process -FilePath $file -ArgumentList '/S','/VERYSILENT','/NORESTART' -Wait -PassThru
    }
    if ($p.ExitCode -ne 0) { Die "Installer exited with code $($p.ExitCode)." }
    Write-Ok 'Installer completed.'

    Write-Stage 'Done'
    Write-Ok "$AppName installed successfully."
}
catch {
    Die $_.Exception.Message
}
finally {
    if ($tmp -and (Test-Path $tmp)) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
}
