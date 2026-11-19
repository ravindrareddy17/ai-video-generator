# ==============================================================================
# Post-Reset Restore Script for The Shortest Orbit / AI Video Generator V2
# RUN THIS SCRIPT AFTER YOU REINSTALL WINDOWS AND CLONE THE REPO!
# ==============================================================================

param(
    [string]$BackupZipOrFolderPath = ""
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "   AI VIDEO GENERATOR V2 - POST-RESET RESTORE UTILITY  " -ForegroundColor Yellow
Write-Host "========================================================`n" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
if (-not (Test-Path "$ProjectRoot\requirements.txt")) {
    $ProjectRoot = (Get-Item .).FullName
}

# Auto-locate backup zip in parent directory or current directory if not specified
if (-not $BackupZipOrFolderPath) {
    $ZipCandidates = Get-ChildItem -Path (Split-Path $ProjectRoot -Parent), $ProjectRoot -Filter "*ShortestOrbit*BACKUP*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($ZipCandidates -and $ZipCandidates.Count -gt 0) {
        $BackupZipOrFolderPath = $ZipCandidates[0].FullName
        Write-Host "Found latest backup archive automatically:" -ForegroundColor Green
        Write-Host ">>> $BackupZipOrFolderPath`n" -ForegroundColor Cyan
    }
}

if (-not $BackupZipOrFolderPath -or -not (Test-Path $BackupZipOrFolderPath)) {
    Write-Host "[!] Backup file not detected automatically." -ForegroundColor Yellow
    $BackupZipOrFolderPath = Read-Host "Please enter the full path to your Backup ZIP file or Folder"
}

if (-not (Test-Path $BackupZipOrFolderPath)) {
    Write-Host "[ERROR] Could not find: $BackupZipOrFolderPath" -ForegroundColor Red
    exit 1
}

$TempExtract = Join-Path $env:TEMP "ShortestOrbit_Restore_Temp"
if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null

if ((Get-Item $BackupZipOrFolderPath).Extension -eq ".zip") {
    Write-Host "[1/3] Extracting backup ZIP archive..." -ForegroundColor White
    Expand-Archive -Path $BackupZipOrFolderPath -DestinationPath $TempExtract -Force
    $SourceRoot = $TempExtract
} else {
    $SourceRoot = $BackupZipOrFolderPath
}

Write-Host "`n[2/3] Restoring secrets (.env, client_secret.json, token.pickle)..." -ForegroundColor White
$Secrets = @(".env", "client_secret.json", "token.pickle", "token_base64.txt")
foreach ($sec in $Secrets) {
    $secPath = Join-Path $SourceRoot $sec
    if (Test-Path $secPath) {
        Copy-Item -Path $secPath -Destination $ProjectRoot -Force
        Write-Host "   [+] Restored: $sec" -ForegroundColor Green
    }
}

Write-Host "`n[3/3] Restoring database files and analytics state..." -ForegroundColor White
New-Item -ItemType Directory -Force -Path "$ProjectRoot\automation\database" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectRoot\data" | Out-Null

if (Test-Path "$SourceRoot\automation\database") {
    Get-ChildItem -Path "$SourceRoot\automation\database" -Filter "*.db" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination "$ProjectRoot\automation\database" -Force
        Write-Host "   [+] Restored DB: automation\database\$($_.Name)" -ForegroundColor Green
    }
}

if (Test-Path "$SourceRoot\data") {
    Get-ChildItem -Path "$SourceRoot\data" -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination "$ProjectRoot\data" -Force
        Write-Host "   [+] Restored Data: data\$($_.Name)" -ForegroundColor Green
    }
}

# Cleanup temp
if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "           RESTORE COMPLETED SUCCESSFULLY!             " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "All secret API keys, OAuth tokens, and databases are restored.`n" -ForegroundColor Yellow
Write-Host "Next step: Run 'python verify_environment.py' to test!" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan
