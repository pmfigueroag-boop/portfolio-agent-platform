#!/bin/sh
# Get session token
TOKEN=$(curl -s -X POST http://localhost:3000/api/session \
  -H "Content-Type: application/json" \
  -d '{"username": "pmfigueroag@gmail.com", "password": "Admin1234$"}' | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "FAIL: Could not get session token. Trying common passwords..."
  # Try without $
  TOKEN=$(curl -s -X POST http://localhost:3000/api/session \
    -H "Content-Type: application/json" \
    -d '{"username": "pmfigueroag@gmail.com", "password": "Admin1234"}' | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
  echo "FAIL: Could not authenticate. Please provide your Metabase password."
  exit 1
fi

echo "SUCCESS: Got session token: $TOKEN"

# Add PostgreSQL database
RESULT=$(curl -s -X POST http://localhost:3000/api/database \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: $TOKEN" \
  -d '{
    "name": "Portfolio DB",
    "engine": "postgres",
    "details": {
      "host": "db",
      "port": 5432,
      "dbname": "portfolio_db",
      "user": "metabase_user",
      "password": "metabase123",
      "ssl": false,
      "tunnel-enabled": false
    },
    "is_full_sync": true,
    "auto_run_queries": true
  }')

echo "Database add result: $RESULT"
