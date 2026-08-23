# PNG Folder Watch — First-time self-contained runtime installer
# Downloads standalone portable Python runtime and installs dependencies

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $ScriptDir "runtime"
$PythonExe = Join-Path $RuntimeDir "python.exe"
$PythonwExe = Join-Path $RuntimeDir "pythonw.exe"

function Write-Step {
    param([string]$Message)
    Write-Host "[$([DateTime]::Now.ToString('HH:mm:ss'))] $Message" -ForegroundColor Cyan
}

if (Test-Path $PythonExe) {
    Write-Step "Runtime already initialized at $RuntimeDir."
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  PNG Folder Watch — First-Time Self-Contained Setup" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Step "Preparing lightweight self-contained Python runtime..."

$TarGz = Join-Path $ScriptDir "python_standalone.tar.gz"
$PythonUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/20260814/cpython-3.11.16%2B20260814-x86_64-pc-windows-msvc-install_only.tar.gz"

try {
    Write-Step "Downloading self-contained Python runtime..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PythonUrl -OutFile $TarGz -UseBasicParsing

    Write-Step "Extracting runtime..."
    tar -xzf $TarGz -C $ScriptDir
    if (Test-Path (Join-Path $ScriptDir "python")) {
        if (Test-Path $RuntimeDir) {
            Remove-Item -Recurse -Force $RuntimeDir
        }
        Rename-Item -Path (Join-Path $ScriptDir "python") -NewName "runtime" -Force
    }
    if (Test-Path $TarGz) {
        Remove-Item -Path $TarGz -Force
    }

    Write-Step "Installing required libraries (Pillow, watchdog, pystray, psutil)..."
    & $PythonExe -m pip install --no-warn-script-location --no-cache-dir watchdog Pillow pystray psutil | Out-Null

    # Ensure pythonw exists
    if (-not (Test-Path $PythonwExe) -and (Test-Path $PythonExe)) {
        Copy-Item -Path $PythonExe -Destination $PythonwExe
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  Setup completed successfully! Starting PNG Folder Watch..." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "Error during automatic download: $_" -ForegroundColor Red
    Write-Host "Attempting fallback to local Python virtual environment..." -ForegroundColor Yellow

    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Step "Creating local virtual environment using system Python..."
        & python -m venv $RuntimeDir
        $VenvPip = Join-Path $RuntimeDir "Scripts\pip.exe"
        & $VenvPip install --no-warn-script-location watchdog Pillow pystray psutil
        $VenvPython = Join-Path $RuntimeDir "Scripts\python.exe"
        $VenvPythonw = Join-Path $RuntimeDir "Scripts\pythonw.exe"
        Copy-Item -Path $VenvPython -Destination $PythonExe -Force
        Copy-Item -Path $VenvPythonw -Destination $PythonwExe -Force
        Write-Step "Fallback setup complete!"
    } else {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            "An error occurred while downloading the self-contained runtime.`nPlease check your internet connection and try running PNGWatch.bat again.",
            "PNG Folder Watch Setup Error",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        )
        exit 1
    }
}
