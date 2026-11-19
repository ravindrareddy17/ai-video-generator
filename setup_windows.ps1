# ==============================================================================
# One-Click Setup Script for The Shortest Orbit / AI Video Generator V2
# RUN THIS ON YOUR CLEAN/RESET WINDOWS MACHINE TO CONFIGURE EVERYTHING AUTOMATICALLY!
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host "   THE SHORTEST ORBIT - AUTOMATED WINDOWS WORKSTATION SETUP        " -ForegroundColor Yellow
Write-Host "====================================================================`n" -ForegroundColor Cyan

$ProjectRoot = $PSScriptRoot
if (-not (Test-Path "$ProjectRoot\requirements.txt")) {
    $ProjectRoot = (Get-Item .).FullName
}
Set-Location $ProjectRoot

# ------------------------------------------------------------------------------
# STEP 1: Verify Windows Package Manager (Winget) & Core Tools
# ------------------------------------------------------------------------------
Write-Host "[STEP 1/6] Checking Core System Tools (Git, Python 3.12, FFmpeg)..." -ForegroundColor White

$HasWinget = (Get-Command winget -ErrorAction SilentlyContinue) -ne $null

# 1. Check Git
$HasGit = (Get-Command git -ErrorAction SilentlyContinue) -ne $null
if (-not $HasGit) {
    Write-Host "[-] Git CLI is missing." -ForegroundColor Yellow
    if ($HasWinget) {
        Write-Host "    Installing Git via winget..." -ForegroundColor Cyan
        winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
    } else {
        Write-Host "    Please download and install Git from: https://git-scm.com/download/win" -ForegroundColor Red
    }
} else {
    Write-Host "[+] Git CLI detected: $(git --version)" -ForegroundColor Green
}

# 2. Check Python
$HasPython = (Get-Command python -ErrorAction SilentlyContinue) -ne $null
if (-not $HasPython) {
    Write-Host "[-] Python is missing." -ForegroundColor Yellow
    if ($HasWinget) {
        Write-Host "    Installing Python 3.12 via winget..." -ForegroundColor Cyan
        winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements
        Write-Host "    NOTE: If python is not recognized yet, restart your PowerShell terminal." -ForegroundColor Yellow
    } else {
        Write-Host "    Please download Python 3.12 from: https://www.python.org/downloads/" -ForegroundColor Red
    }
} else {
    Write-Host "[+] Python detected: $(python --version)" -ForegroundColor Green
}

# 3. Check FFmpeg
$HasFFmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue) -ne $null
if (-not $HasFFmpeg) {
    Write-Host "[-] FFmpeg is missing from PATH." -ForegroundColor Yellow
    if ($HasWinget) {
        Write-Host "    Installing FFmpeg (Gyan build) via winget..." -ForegroundColor Cyan
        winget install --id Gyan.FFmpeg -e --source winget --accept-source-agreements --accept-package-agreements
        Write-Host "    NOTE: You may need to restart PowerShell for FFmpeg PATH to refresh." -ForegroundColor Yellow
    } else {
        Write-Host "    Download FFmpeg full build from https://www.gyan.dev/ffmpeg/builds/ and add 'bin' to PATH." -ForegroundColor Red
    }
} else {
    Write-Host "[+] FFmpeg detected." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# STEP 2: Initialize Required Directories
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 2/6] Initializing Required Directories..." -ForegroundColor White
$DirsToCreate = @(
    "downloads",
    "output",
    "temp",
    "logs",
    "data",
    "audio",
    "captions",
    "assets\branding",
    "assets\fonts",
    "assets\animations",
    "assets\music",
    "automation\database"
)

foreach ($d in $DirsToCreate) {
    $targetDir = Join-Path $ProjectRoot $d
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Write-Host "   [+] Created directory: $d" -ForegroundColor Green
    } else {
        Write-Host "   [.] Directory exists: $d" -ForegroundColor DarkGray
    }
}

# ------------------------------------------------------------------------------
# STEP 3: Setup Python Environment & Dependencies
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 3/6] Installing Python Dependencies from requirements.txt..." -ForegroundColor White

python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] pip upgrade exited with code $LASTEXITCODE. Continuing..." -ForegroundColor Yellow
}

pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] All Python dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Dependency installation encountered issues. Check logs above." -ForegroundColor Red
}

# ------------------------------------------------------------------------------
# STEP 4: Configuration & Secrets Check
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 4/6] Checking Project Configuration & Secrets..." -ForegroundColor White

if (-not (Test-Path "$ProjectRoot\.env")) {
    if (Test-Path "$ProjectRoot\.env.example") {
        Copy-Item -Path "$ProjectRoot\.env.example" -Destination "$ProjectRoot\.env"
        Write-Host "[!] '.env' file did not exist. Created a fresh '.env' from '.env.example'." -ForegroundColor Yellow
        Write-Host "    ACTION: Open '.env' and paste your API keys (or run restore_after_reset.ps1)!" -ForegroundColor Red
    }
} else {
    Write-Host "[+] '.env' file is present." -ForegroundColor Green
}

if (-not (Test-Path "$ProjectRoot\client_secret.json")) {
    Write-Host "[!] 'client_secret.json' is missing." -ForegroundColor Yellow
    Write-Host "    ACTION: Restore it from your backup ZIP or download it from Google Cloud Console." -ForegroundColor Yellow
} else {
    Write-Host "[+] 'client_secret.json' is present." -ForegroundColor Green
}

if (-not (Test-Path "$ProjectRoot\token.pickle")) {
    Write-Host "[!] 'token.pickle' is missing." -ForegroundColor Yellow
    Write-Host "    ACTION: Restore it from backup or run 'python get_fresh_token.py' to authenticate." -ForegroundColor Yellow
} else {
    Write-Host "[+] 'token.pickle' is present." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# STEP 5: Run Full Diagnostic Verification
# ------------------------------------------------------------------------------
Write-Host "`n[STEP 5/6] Running System Verification Suite (verify_environment.py)..." -ForegroundColor White
python verify_environment.py

# ------------------------------------------------------------------------------
# STEP 6: Completion Summary
# ------------------------------------------------------------------------------
Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host "                 SETUP & CONFIGURATION FINISHED                    " -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "Quick Launch Commands:" -ForegroundColor Yellow
Write-Host "  1. Test Single Video Run:   python python/main.py --no-upload" -ForegroundColor White
Write-Host "  2. Run Full Local Pipeline: .\run_pipeline.bat" -ForegroundColor White
Write-Host "  3. Open Channel Dashboard:  .\run_dashboard.bat" -ForegroundColor White
Write-Host "  4. Refresh YouTube Token:   python get_fresh_token.py" -ForegroundColor White
Write-Host "====================================================================`n" -ForegroundColor Cyan
