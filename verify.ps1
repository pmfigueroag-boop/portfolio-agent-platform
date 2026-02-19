$ErrorActionPreference = "Stop"

Write-Host "--- Portfolio Platform Verification ---" -ForegroundColor Cyan

# 1. Check Docker Containers
Write-Host "`n1. Checking Container Status..." -ForegroundColor Yellow
$containers = docker ps --format "{{.Names}}: {{.Status}}"
$running = $containers | Select-String "Up"
if ($running) {
    Write-Host "Containers are running." -ForegroundColor Green
    $containers
}
else {
    Write-Host "No running containers found!" -ForegroundColor Red
    exit 1
}

# 2. Check Database Connection
Write-Host "`n2. Verifying Database Connection..." -ForegroundColor Yellow
# Default credentials used in docker-compose
$DB_USER = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "admin" }
$DB_NAME = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "portfolio_db" }

try {
    # Attempt to list tables
    docker exec portfolio_db psql -U $DB_USER -d $DB_NAME -c "\dt"
    Write-Host "Database connection successful!" -ForegroundColor Green
}
catch {
    Write-Host "Database connection failed!" -ForegroundColor Red
    Write-Error $_
}

# 3. Check Agent Health Endpoints
Write-Host "`n3. Checking Agent Endpoints..." -ForegroundColor Yellow

$agents = @(
    @{Name = "Value Agent"; Port = 8001 },
    @{Name = "Quant Agent"; Port = 8002 },
    @{Name = "Macro Agent"; Port = 8003 },
    @{Name = "Risk Agent"; Port = 8004 },
    @{Name = "Consensus Agent"; Port = 8005 }
)

foreach ($agent in $agents) {
    $url = "http://localhost:$($agent.Port)/health"
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 5
        if ($response.status -eq "ok") {
            Write-Host "$($agent.Name): OK ($url)" -ForegroundColor Green
        }
        else {
            Write-Host "$($agent.Name): BAD RESPONSE ($url)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "$($agent.Name): UNREACHABLE ($url)" -ForegroundColor Red
    }
}

Write-Host "`n--- Verification Complete ---" -ForegroundColor Cyan
