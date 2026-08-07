$ErrorActionPreference = "Stop"
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ReleaseVenv = Join-Path $ProjectRoot ".venv-release"
$ReleasePython = Join-Path $ReleaseVenv "Scripts\python.exe"
$SupportedOrder = @("3.12", "3.11", "3.10")

function Invoke-Checked {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [string]$Label
    )
    Write-Host "==> $Label"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE" }
}

function Get-PythonRecord {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $Resolved = [IO.Path]::GetFullPath($Path)
    $Version = & $Resolved -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $Version) { return $null }
    $Parts = $Version.Trim().Split(".")
    if ($Parts.Count -lt 2) { return $null }
    [pscustomobject]@{
        Path = $Resolved
        Version = $Version.Trim()
        Minor = "$($Parts[0]).$($Parts[1])"
    }
}

function Add-PythonCandidate {
    param([Collections.Generic.List[string]]$Candidates, [string]$Path)
    if (-not $Path) { return }
    $Resolved = [IO.Path]::GetFullPath($Path)
    if (-not $Candidates.Contains($Resolved)) { $Candidates.Add($Resolved) }
}

$Candidates = [Collections.Generic.List[string]]::new()
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    Write-Host "==> Installed Python launchers (py -0p)"
    & $PyLauncher.Source -0p
    if ($LASTEXITCODE -ne 0) { throw "py -0p failed with exit code $LASTEXITCODE" }
    foreach ($Minor in $SupportedOrder) {
        $Path = & $PyLauncher.Source "-$Minor" -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $Path) { Add-PythonCandidate $Candidates $Path.Trim() }
    }
} else {
    Write-Host "py launcher not found; checking installed local interpreter locations."
}

$CodexRuntimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes"
if (Test-Path -LiteralPath $CodexRuntimeRoot) {
    Get-ChildItem -LiteralPath $CodexRuntimeRoot -Filter python.exe -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*\dependencies\python\python.exe" } |
        ForEach-Object { Add-PythonCandidate $Candidates $_.FullName }
}

$CondaCommand = Get-Command conda -ErrorAction SilentlyContinue
if ($CondaCommand) {
    try {
        $CondaInfo = ((& conda info --json 2>$null) -join "`n") | ConvertFrom-Json
        $CondaBase = [IO.Path]::GetFullPath([string]$CondaInfo.root_prefix)
        foreach ($Environment in @($CondaInfo.envs)) {
            if (-not $Environment) { continue }
            $EnvironmentRoot = [IO.Path]::GetFullPath([string]$Environment)
            if ($EnvironmentRoot -ieq $CondaBase) { continue }
            Add-PythonCandidate $Candidates (Join-Path $EnvironmentRoot "python.exe")
        }
    } catch {
        Write-Warning "Unable to enumerate non-base Conda environments: $($_.Exception.Message)"
    }
}

$PathPython = Get-Command python -ErrorAction SilentlyContinue
if ($PathPython -and $PathPython.Source) { Add-PythonCandidate $Candidates $PathPython.Source }

$Records = @($Candidates | ForEach-Object { Get-PythonRecord $_ } | Where-Object { $null -ne $_ })
foreach ($Record in $Records) {
    if ($Record.Minor -eq "3.13") {
        Write-Host "Rejected Python 3.13 interpreter: $($Record.Path) ($($Record.Version))"
    } elseif ($Record.Minor -notin $SupportedOrder) {
        Write-Host "Rejected unsupported interpreter: $($Record.Path) ($($Record.Version))"
    }
}

$Selected = $null
foreach ($Minor in $SupportedOrder) {
    $Selected = $Records | Where-Object { $_.Minor -eq $Minor } | Select-Object -First 1
    if ($Selected) { break }
}
if (-not $Selected) {
    throw "No supported Python 3.10, 3.11, or 3.12 interpreter was found. Install Python 3.12, then rerun this script. Suggested command: winget install -e --id Python.Python.3.12"
}

$Recreate = -not (Test-Path -LiteralPath $ReleasePython -PathType Leaf)
if (-not $Recreate) {
    $Existing = Get-PythonRecord $ReleasePython
    $Recreate = (-not $Existing) -or ($Existing.Minor -ne $Selected.Minor)
}
if ($Recreate -and (Test-Path -LiteralPath $ReleaseVenv)) {
    $ResolvedVenv = [IO.Path]::GetFullPath($ReleaseVenv)
    if (-not $ResolvedVenv.StartsWith($ProjectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing recursive removal outside project root: $ResolvedVenv"
    }
    Remove-Item -LiteralPath $ResolvedVenv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $ReleasePython -PathType Leaf)) {
    Invoke-Checked $Selected.Path @("-m", "venv", $ReleaseVenv) "Create .venv-release with Python $($Selected.Minor)"
}

$ReleaseRecord = Get-PythonRecord $ReleasePython
if (-not $ReleaseRecord -or $ReleaseRecord.Minor -notin $SupportedOrder) {
    $Actual = if ($ReleaseRecord) { $ReleaseRecord.Version } else { "unknown" }
    throw "Unsupported release Python: $ReleasePython ($Actual). Expected Python 3.10, 3.11, or 3.12."
}

Invoke-Checked $ReleasePython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") "Upgrade pip, setuptools, and wheel"
Invoke-Checked $ReleasePython @("-m", "pip", "install", "build", "twine", "pytest", "psutil", "ruff", "mypy") "Install release verification dependencies"
Invoke-Checked $ReleasePython @("-m", "pip", "install", "-e", $ProjectRoot) "Install project source and runtime dependencies"
Invoke-Checked $ReleasePython @("-c", "import build, twine, pytest, psutil; print('verification dependencies: ok')") "Verify release dependency imports"

Write-Host "Release Python executable: $ReleasePython"
Write-Host "Release Python version: $($ReleaseRecord.Version)"
Write-Host "RELEASE ENVIRONMENT SETUP: PASS"
