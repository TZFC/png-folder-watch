# PNG Folder Watch — First-time self-contained runtime installer
# Downloads standalone portable Python runtime and installs dependencies

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $ScriptDir "runtime"
$PythonExe = Join-Path $RuntimeDir "python.exe"
$PythonwExe = Join-Path $RuntimeDir "pythonw.exe"

function Write-Step {
    param([string]$Message)
    Write-Host "[$([DateTime]::Now.ToString('HH:mm:ss'))] $Message" -ForegroundColor Cyan
}

function Download-FileWithProgress {
    param (
        [string]$DownloadUrl,
        [string]$DestinationPath
    )

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
    $request = [System.Net.HttpWebRequest]::Create($DownloadUrl)
    $request.Timeout = 120000
    $request.UserAgent = "PNGFolderWatch-Setup"
    $response = $request.GetResponse()
    $totalBytes = $response.ContentLength
    $responseStream = $response.GetResponseStream()
    $targetStream = [System.IO.File]::Create($DestinationPath)

    $buffer = New-Object byte[] 65536
    $downloadedBytes = 0
    $lastUpdate = [DateTime]::MinValue
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        while (($bytesRead = $responseStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $targetStream.Write($buffer, 0, $bytesRead)
            $downloadedBytes += $bytesRead

            $now = [DateTime]::Now
            if (($now - $lastUpdate).TotalMilliseconds -ge 100 -or $downloadedBytes -eq $totalBytes) {
                $lastUpdate = $now
                $elapsedSec = [Math]::Max(0.01, $sw.Elapsed.TotalSeconds)
                $speedMBps = [Math]::Round(($downloadedBytes / 1MB) / $elapsedSec, 2)

                if ($totalBytes -gt 0) {
                    $percent = [Math]::Min(100, [int](($downloadedBytes / $totalBytes) * 100))
                    $downloadedMB = [Math]::Round($downloadedBytes / 1MB, 1)
                    $totalMB = [Math]::Round($totalBytes / 1MB, 1)
                    
                    # 30-char visual progress bar: [████████████░░░░░░░░░] 60%  28.0 / 46.2 MB (9.5 MB/s)
                    $barWidth = 30
                    $filled = [Math]::Min($barWidth, [Math]::Max(0, [int]($barWidth * ($percent / 100))))
                    $empty = $barWidth - $filled
                    $barStr = [string]::new([char]0x2588, $filled) + [string]::new([char]0x2591, $empty)
                    
                    $statusText = "`r  [$barStr] $percent%  $downloadedMB / $totalMB MB ($speedMBps MB/s)    "
                    Write-Host -NoNewline $statusText -ForegroundColor Cyan
                } else {
                    $downloadedMB = [Math]::Round($downloadedBytes / 1MB, 1)
                    Write-Host -NoNewline "`r  $downloadedMB MB downloaded ($speedMBps MB/s)    " -ForegroundColor Cyan
                }
            }
        }
        Write-Host ""
    }
    finally {
        $sw.Stop()
        if ($targetStream) { $targetStream.Dispose() }
        if ($responseStream) { $responseStream.Dispose() }
        if ($response) { $response.Dispose() }
    }
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
    Write-Step "Downloading self-contained Python runtime package..."
    Download-FileWithProgress -DownloadUrl $PythonUrl -DestinationPath $TarGz -Activity "Downloading Python runtime"

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
