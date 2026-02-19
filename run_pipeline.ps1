$ErrorActionPreference = "Stop"

Write-Host "Starting Portfolio Analysis Pipeline (in Docker context)..." -ForegroundColor Cyan

# Determine the network name (usually project_default or similar)
$networkName = "portfolio-agent-platform_portfolio_net"
try {
    docker network inspect $networkName > $null 2>&1
}
catch {
    # Fallback if name is different (e.g. just portfolio_net if explicitly named)
    $networkName = "portfolio_net"
}

Write-Host "Using Network: $networkName" -ForegroundColor DarkGray

docker run --rm --network $networkName `
    -v ${PWD}/orchestration:/app/orchestration `
    -v ${PWD}/services:/app/services `
    -e PYTHONPATH=/app `
    -e Value_URL="http://portfolio_value_agent:8001/api/v1/value" `
    -e Quant_URL="http://portfolio_quant_agent:8002/api/v1/quant" `
    -e Macro_URL="http://portfolio_macro_agent:8003/api/v1/macro" `
    -e Risk_URL="http://portfolio_risk_agent:8004/api/v1/risk" `
    -e Consensus_URL="http://portfolio_consensus_agent:8005/api/v1/consensus" `
    -e POSTGRES_SERVER="db" `
    portfolio-agent-platform-value_agent `
    python /app/orchestration/pipeline.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Pipeline Completed Successfully!" -ForegroundColor Green
}
else {
    Write-Host "Pipeline Failed!" -ForegroundColor Red
}
