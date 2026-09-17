# Run from any directory. Downloads remain local; source files are never committed.
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $repoRoot
try {
    docker info --format '{{.OSType}}' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop with Linux containers, then rerun this script.' }
    foreach ($line in Get-Content -LiteralPath 'bin/SHA256SUMS') {
        $parts = $line -split '\s+'
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path 'bin' $parts[1])).Hash.ToLowerInvariant()
        if ($actual -ne $parts[0]) { throw 'Generator checksum mismatch; stop before execution.' }
    }
    if (-not (Test-Path -LiteralPath 'data/raw/scheduler_data.csv') -or -not (Test-Path -LiteralPath 'data/raw/dcgm.csv')) {
        if (Test-Path -LiteralPath 'data/raw') { throw 'Partial data/raw directory exists; inspect it before replacing anything.' }
        Invoke-WebRequest -Uri 'https://mantisgrid-hackathon.s3.us-east-1.amazonaws.com/track-2-raw.zip' -OutFile 'data/track-2-raw.zip'
        Expand-Archive -LiteralPath 'data/track-2-raw.zip' -DestinationPath 'data/raw'
    }
    docker compose run --rm prep
    if ($LASTEXITCODE -ne 0) { throw 'Preparation failed.' }
    docker compose run --rm generate
    if ($LASTEXITCODE -ne 0) { throw 'Generation failed.' }
    docker compose run --rm prep python scripts/checksum_data.py
    if ($LASTEXITCODE -ne 0) { throw 'Canonical checksum check failed.' }
    Write-Host 'Data verified. Start the shared base with: docker compose up'
} finally { Pop-Location }
