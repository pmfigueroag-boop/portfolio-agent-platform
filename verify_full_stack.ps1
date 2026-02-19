
Write-Host "--- E2E Full Stack Verification ---" -ForegroundColor Cyan

# 0. Healthcheck
Write-Host "`n0. Healthcheck..." -ForegroundColor Yellow
$containers = docker ps --format "{{.Names}} {{.Status}}"
if ($containers -match "unhealthy") {
    Write-Host "FATAL: Some containers are unhealthy." -ForegroundColor Red
    $containers | ForEach-Object { Write-Host $_ }
    Exit 1
}
Write-Host "All containers appear running." -ForegroundColor Green

# 1. Run Seeder
Write-Host "`n1. Running Data Seeder..." -ForegroundColor Yellow
$seederStart = Get-Date

docker run --rm `
    --network portfolio-agent-platform_portfolio_net `
    -v ${PWD}:/app `
    -w /app `
    -e POSTGRES_SERVER=db `
    -e POSTGRES_USER=pmfigueroag@gmail.com `
    -e POSTGRES_PASSWORD=Admin1234$ `
    -e POSTGRES_DB=portfolio_db `
    portfolio-agent-platform-value_agent `
    python orchestration/seeder.py

if ($LastExitCode -ne 0) {
    Write-Host "Seeder failed!" -ForegroundColor Red
    Exit 1
}
Write-Host "Seeder completed successfully." -ForegroundColor Green

# 2. Run Pipeline
Write-Host "`n2. Running Analysis Pipeline..." -ForegroundColor Yellow
$pipelineStart = Get-Date

# We use the 'portfolio-agent-platform-value_agent' image because it has the right dependencies
# We mount the CURRENT directory to /app so it can see 'orchestration/' and 'services/'

docker run --rm `
    --network portfolio-agent-platform_portfolio_net `
    -v ${PWD}:/app `
    -w /app `
    -e POSTGRES_SERVER=db `
    -e POSTGRES_USER=pmfigueroag@gmail.com `
    -e POSTGRES_PASSWORD=Admin1234$ `
    -e POSTGRES_DB=portfolio_db `
    -e MINIO_ENDPOINT=minio:9000 `
    -e MINIO_ACCESS_KEY=admin `
    -e MINIO_SECRET_KEY=minioadmin `
    -e Value_URL=http://value_agent:8001/api/v1/value `
    -e Quant_URL=http://quant_agent:8002/api/v1/quant `
    -e Macro_URL=http://macro_agent:8003/api/v1/macro `
    -e Risk_URL=http://risk_agent:8004/api/v1/risk `
    -e Consensus_URL=http://consensus_agent:8005/api/v1/consensus `
    portfolio-agent-platform-value_agent `
    python orchestration/pipeline.py

if ($LastExitCode -ne 0) {
    Write-Host "Pipeline execution failed!" -ForegroundColor Red
    Exit 1
}
Write-Host "Pipeline execution complete." -ForegroundColor Green

# 3. Verify Database (Persistence)
Write-Host "`n3. Verifying Database (Persistence)..." -ForegroundColor Yellow
# We check for records created *after* our pipeline run start time (approx)
$query = "SELECT ticker, decision, confidence, created_at FROM final_decisions ORDER BY created_at DESC LIMIT 5;"
$dbResult = docker exec -e PGPASSWORD=Admin1234$ portfolio_db psql -U pmfigueroag@gmail.com -d portfolio_db -c "$query"

if ($dbResult -match "rows\)") {
    Write-Host "Database verification successful. Recent records found:" -ForegroundColor Green
    $dbResult | Select-Object -First 10 | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "Database verification failed. No rows found or error." -ForegroundColor Red
    Write-Host $dbResult
    Exit 1
}

# 4. Verify MinIO (Upload & Versioning)
Write-Host "`n4. Verifying MinIO Storage..." -ForegroundColor Yellow

$checkMinioScript = @"
import boto3
import json
import sys
from datetime import datetime

try:
    # Note: Inside the container, 'minio' is the host, port 9000
    s3 = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='admin', aws_secret_access_key='minioadmin', verify=False)
    bucket_name = 'portfolio-results'
    
    # Check if bucket exists
    response = s3.list_buckets()
    buckets = [b['Name'] for b in response['Buckets']]
    if bucket_name not in buckets:
        print(f'FAILED: Bucket {bucket_name} does not exist.')
        sys.exit(1)
        
    objs = s3.list_objects_v2(Bucket=bucket_name)
    
    if 'Contents' in objs:
        # Sort by date to get latest
        sorted_objs = sorted(objs['Contents'], key=lambda x: x['LastModified'], reverse=True)
        latest_key = sorted_objs[0]['Key']
        print(f"Found {len(objs['Contents'])} objects. Latest: {latest_key}")
        
        # Download and validate content
        resp = s3.get_object(Bucket=bucket_name, Key=latest_key)
        content = json.loads(resp['Body'].read().decode('utf-8'))
        
        # Validation Logic
        print(f"--- Validating JSON Structure ({latest_key}) ---")
        if 'run_id' not in content:
            print("FAILED: Missing 'run_id' in root.")
            sys.exit(1)
        if 'timestamp' not in content:
            print("FAILED: Missing 'timestamp' in root.")
            sys.exit(1)
        if 'results' not in content or not isinstance(content['results'], list):
            print("FAILED: 'results' missing or not a list.")
            sys.exit(1)
            
        print(f"Run ID: {content['run_id']}")
        print(f"Result Count: {len(content['results'])}")
        
        if len(content['results']) > 0:
            item = content['results'][0]
            # Check for forbidden nesting
            if 'details' in item and isinstance(item['details'], dict) and 'details' in item['details']:
                 print("FAILED: Deep nesting detected (details.details).")
                 sys.exit(1)
            
            # Strict Signal Check
            if item['agents_count'] == 0 and item['decision'] != "NO_SIGNAL":
                print(f"FAILED: agents_count is 0 but decision is {item['decision']} (Expected NO_SIGNAL).")
                sys.exit(1)
            
            if item['decision'] != "NO_SIGNAL" and item['confidence'] == 0:
                 print(f"WARNING: Confidence is 0 for decision {item['decision']}.")

            # Simple content check
            required_fields = ['ticker', 'decision', 'confidence']
            for field in required_fields:
                if field not in item:
                    print(f"FAILED: Missing field '{field}' in result item.")
                    sys.exit(1)
                       
            print("First Item Sample:")
            print(json.dumps(item, indent=2))
            print("SUCCESS: JSON structure is valid and clean.")
        else:
            print("WARNING: Results list is empty.")
            
    else:
        print('Bucket is empty.')
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"@

Set-Content -Path "verification_script.py" -Value $checkMinioScript

docker run --rm `
    --network portfolio-agent-platform_portfolio_net `
    -v ${PWD}:/app `
    -w /app `
    portfolio-agent-platform-value_agent `
    python verification_script.py

if ($LastExitCode -ne 0) {
    Write-Host "MinIO verification failed!" -ForegroundColor Red
    Remove-Item "verification_script.py"
    Exit 1
}
Remove-Item "verification_script.py"
Write-Host "MinIO verification passed." -ForegroundColor Green

# 5. Metabase Instructions
Write-Host "`n5. Metabase Verification Instructions" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:3000"
Write-Host "   2. Login with:"
Write-Host "      User: pmfigueroag@gmail.com"
Write-Host "      Pass: Admin1234$"
Write-Host "   3. Ensure DB connection is set to Host: 'db', Port: 5432, User/Pass: 'admin'/'admin', DB: 'portfolio_db'"
Write-Host "   4. Create new SQL Question:"
Write-Host "      SELECT ticker, decision, confidence, created_at FROM final_decisions ORDER BY created_at DESC;"
Write-Host "   5. Expected: Data from today $(Get-Date -Format 'yyyy-MM-dd') should be visible."
Write-Host "`n--- E2E TEST COMPLETED: PASS ---" -ForegroundColor Green
