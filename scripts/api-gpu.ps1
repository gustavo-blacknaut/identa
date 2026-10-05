param(
    [string]$Python = "",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$api = Join-Path $root "apps\api"

if (-not $Python) {
    foreach ($candidate in @(".venv\Scripts\python.exe", ".venv-gpu\Scripts\python.exe")) {
        $path = Join-Path $root $candidate
        if (Test-Path $path) { $Python = $path; break }
    }
}
if (-not $Python -or -not (Test-Path $Python)) {
    throw "Ambiente Python não encontrado. Crie com: python -m venv .venv e pip install -e `"apps/api[gpu-directml,tesseract]`""
}

$values = @{}
foreach ($line in Get-Content (Join-Path $root ".env")) {
    if ($line -match '^\s*([A-Z0-9_]+)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
}
foreach ($required in @("POSTGRES_PASSWORD", "IDENTA_SECRET_KEY")) {
    if (-not $values[$required]) { throw "$required não está definido no .env" }
}
foreach ($entry in $values.GetEnumerator()) {
    if ($entry.Key.StartsWith("IDENTA_")) { Set-Item -Path "Env:$($entry.Key)" -Value $entry.Value }
}

$user = if ($values["POSTGRES_USER"]) { $values["POSTGRES_USER"] } else { "identa" }
$database = if ($values["POSTGRES_DB"]) { $values["POSTGRES_DB"] } else { "identa" }
$pgPort = if ($values["POSTGRES_HOST_PORT"]) { $values["POSTGRES_HOST_PORT"] } else { "5432" }
$password = [uri]::EscapeDataString($values["POSTGRES_PASSWORD"])
$env:IDENTA_DATABASE_URL = "postgresql+psycopg://${user}:${password}@127.0.0.1:${pgPort}/${database}"
$env:IDENTA_STORAGE_DIR = Join-Path $root "storage"
$env:IDENTA_OCR_MODEL_DIR = Join-Path $api "models"
$env:IDENTA_OCR_DEVICE = "auto"

Push-Location $api
try {
    & $Python -m identa.cli check-config
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m identa.cli download-models
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m uvicorn identa.main:create_app --factory --host 127.0.0.1 --port $Port --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
}
finally {
    Pop-Location
}
