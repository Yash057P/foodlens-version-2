param(
    [string]$ImageName = "foodlens-viva:latest",
    [string]$ContainerName = "foodlens-viva",
    [int]$Port = 5000,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI is not installed or not on PATH."
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not running. Start Docker Desktop and retry."
}

if (-not $SkipBuild) {
    Write-Host "Building $ImageName..."
    docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed." }
}

$existing = docker ps -a --filter "name=^/$ContainerName$" --format "{{.Names}}"
if ($existing -eq $ContainerName) {
    Write-Host "Replacing existing $ContainerName container..."
    docker rm -f $ContainerName | Out-Null
}

# Refuse to test against a stale local server that would shadow Docker.
for ($attempt = 1; $attempt -le 10; $attempt++) {
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { break }
    Start-Sleep -Milliseconds 500
}
if ($listeners.Count -gt 0) {
    $listenerPids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    $owners = Get-Process -Id $listenerPids -ErrorAction SilentlyContinue | ForEach-Object { "$($_.ProcessName) (PID $($_.Id))" }
    throw "Port $Port is already in use by: $($owners -join ', '). Stop that process and retry."
}

Write-Host "Starting $ContainerName on port $Port..."
docker run -d --name $ContainerName -p "${Port}:5000" --restart unless-stopped `
    -e FEEDBACK_PATH=/app/feedback/feedback.jsonl `
    -v foodlens-feedback:/app/feedback `
    $ImageName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Container failed to start." }

$healthUri = "http://127.0.0.1:$Port/api/health"
$ready = $false
for ($attempt = 1; $attempt -le 24; $attempt++) {
    Start-Sleep -Seconds 5
    try {
        $health = Invoke-RestMethod -Uri $healthUri -TimeoutSec 3
        if ($health.status -eq "ok" -and $health.model_ready) {
            $ready = $true
            break
        }
    } catch {
        Write-Host "Waiting for warmed model ($attempt/24)..."
    }
}

if (-not $ready) {
    docker logs --tail 100 $ContainerName
    throw "FoodLens did not become ready within 120 seconds."
}

if ($Port -eq 5000) {
    python scripts/smoke_webapp.py
    if ($LASTEXITCODE -ne 0) { throw "Browser smoke test failed." }
} else {
    Write-Warning "Browser smoke test expects port 5000 and was skipped."
}

$state = docker inspect $ContainerName --format "{{.State.Status}} / {{if .State.Health}}{{.State.Health.Status}}{{else}}health pending{{end}}"
Write-Host "PASS: $ContainerName is $state"
Write-Host "Open http://localhost:$Port"
