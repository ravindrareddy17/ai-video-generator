# ==============================================================================
# Pre-Reset Backup Script for The Shortest Orbit / AI Video Generator V2
# RUN THIS SCRIPT BEFORE RESETTING YOUR LAPTOP!
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "   AI VIDEO GENERATOR V2 - PRE-RESET BACKUP UTILITY    " -ForegroundColor Yellow
Write-Host "========================================================`n" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
if (-not (Test-Path "$ProjectRoot\requirements.txt")) {
    $ProjectRoot = (Get-Item .).FullName
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDirName = "ShortestOrbit_SecretBackup_$Timestamp"
$BackupFolder = Join-Path (Split-Path $ProjectRoot -Parent) $BackupDirName
$ZipFilePath = Join-Path (Split-Path $ProjectRoot -Parent) "ShortestOrbit_BACKUP_SAVE_TO_PENDRIVE_$Timestamp.zip"

Write-Host "[1/4] Creating temporary backup staging directory at:" -ForegroundColor White
Write-Host "      $BackupFolder" -ForegroundColor Gray
New-Item -ItemType Directory -Force -Path $BackupFolder | Out-Null
New-Item -ItemType Directory -Force -Path "$BackupFolder\automation\database" | Out-Null
New-Item -ItemType Directory -Force -Path "$BackupFolder\data" | Out-Null

# List of critical secret and state files to back up
$CriticalFiles = @(
    ".env",
    "client_secret.json",
    "token.pickle",
    "token_base64.txt"
)

Write-Host "`n[2/4] Copying secret configuration and OAuth tokens..." -ForegroundColor White
$CopiedCount = 0
foreach ($file in $CriticalFiles) {
    $src = Join-Path $ProjectRoot $file
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $BackupFolder -Force
        Write-Host "   [+] Backed up: $file" -ForegroundColor Green
        $CopiedCount++
    } else {
        Write-Host "   [-] Not found (optional/missing): $file" -ForegroundColor DarkGray
    }
}

Write-Host "`n[3/4] Copying database state and analytics..." -ForegroundColor White
# Copy automation databases
$DbFiles = Get-ChildItem -Path "$ProjectRoot\automation\database" -Filter "*.db" -ErrorAction SilentlyContinue
foreach ($db in $DbFiles) {
    Copy-Item -Path $db.FullName -Destination "$BackupFolder\automation\database" -Force
    Write-Host "   [+] Backed up DB: automation\database\$($db.Name)" -ForegroundColor Green
}

# Copy central data folder files
$DataFiles = Get-ChildItem -Path "$ProjectRoot\data" -File -ErrorAction SilentlyContinue
foreach ($df in $DataFiles) {
    Copy-Item -Path $df.FullName -Destination "$BackupFolder\data" -Force
    Write-Host "   [+] Backed up Data: data\$($df.Name)" -ForegroundColor Green
}

Write-Host "`n[4/4] Creating single compressed ZIP archive..." -ForegroundColor White
if (Test-Path $ZipFilePath) { Remove-Item -Force $ZipFilePath }
Compress-Archive -Path "$BackupFolder\*" -DestinationPath $ZipFilePath -CompressionLevel Optimal

# Clean up unzipped staging folder
Remove-Item -Recurse -Force $BackupFolder

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "           BACKUP COMPLETED SUCCESSFULLY!              " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "`nYour backup archive is saved at:" -ForegroundColor Yellow
Write-Host ">>> $ZipFilePath <<<`n" -ForegroundColor Cyan
Write-Host "ACTION REQUIRED BEFORE YOU RESET YOUR LAPTOP:" -ForegroundColor Red
Write-Host "1. Copy this ZIP file to a USB Pen Drive or upload it to Google Drive." -ForegroundColor Yellow
Write-Host "2. After resetting Windows and reinstalling the project, extract this" -ForegroundColor Yellow
Write-Host "   ZIP file back into your project folder." -ForegroundColor Yellow
Write-Host "========================================================`n" -ForegroundColor Cyan
