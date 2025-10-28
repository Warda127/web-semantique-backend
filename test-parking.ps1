# Improved Smart City Services Test Script
# Tests from host machine with proper error handling

Write-Host "`n=== Testing Smart City Services (From Host) ===" -ForegroundColor Cyan

# Configuration
$FusekiUrl = "http://localhost:3030"
$BackendUrl = "http://localhost:5000"
$Timeout = 10

# Function to test endpoint with retries
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Description,
        [int]$Retries = 3,
        [int]$RetryDelay = 2
    )
    
    Write-Host "`nTesting: $Description" -ForegroundColor Yellow
    Write-Host "URL: $Url" -ForegroundColor Gray
    
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $Timeout -UseBasicParsing
            Write-Host "✅ SUCCESS (Status: $($response.StatusCode))" -ForegroundColor Green
            return $response
        }
        catch {
            $errorMsg = $_.Exception.Message
            if ($i -lt $Retries) {
                Write-Host "⚠️  Attempt $i failed: $errorMsg" -ForegroundColor Yellow
                Write-Host "   Retrying in $RetryDelay seconds..." -ForegroundColor Gray
                Start-Sleep -Seconds $RetryDelay
            }
            else {
                Write-Host "❌ FAILED after $Retries attempts" -ForegroundColor Red
                Write-Host "   Error: $errorMsg" -ForegroundColor Red
                
                # Additional debugging
                if ($errorMsg -match "connection was refused") {
                    Write-Host "   → Container might not be running or ports not exposed" -ForegroundColor Yellow
                }
                elseif ($errorMsg -match "timed out") {
                    Write-Host "   → Service is slow to respond or not ready" -ForegroundColor Yellow
                }
                return $null
            }
        }
    }
}

# Pre-flight check: Verify containers are running
Write-Host "`n=== Pre-flight Checks ===" -ForegroundColor Cyan
Write-Host "Checking Docker containers..." -ForegroundColor Yellow

try {
    $containers = docker ps --format "{{.Names}}" 2>$null
    
    $expectedContainers = @("smartcity-fuseki", "smartcity-backend")
    $runningContainers = @()
    
    foreach ($container in $expectedContainers) {
        if ($containers -contains $container) {
            Write-Host "✅ $container is running" -ForegroundColor Green
            $runningContainers += $container
            
            # Check port mapping
            $portInfo = docker port $container 2>$null
            if ($portInfo) {
                Write-Host "   Ports: $portInfo" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "❌ $container is NOT running" -ForegroundColor Red
        }
    }
    
    if ($runningContainers.Count -eq 0) {
        Write-Host "`n❌ No containers are running!" -ForegroundColor Red
        Write-Host "Run: docker-compose up -d" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "❌ Docker is not available: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test 1: Fuseki Ping
$result = Test-Endpoint -Url "$FusekiUrl/`$/ping" -Description "Fuseki Ping Endpoint"

# Test 2: Backend Health (Persons API)
$result = Test-Endpoint -Url "$BackendUrl/api/persons" -Description "Backend Persons API"

if ($result) {
    try {
        $json = $result.Content | ConvertFrom-Json
        if ($json -is [array]) {
            Write-Host "   Found $($json.Count) persons" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   Could not parse JSON response" -ForegroundColor Yellow
    }
}

# Test 3: Parking Stations - List All
$result = Test-Endpoint -Url "$BackendUrl/api/parking-stations/" -Description "Parking Stations List API"

if ($result) {
    try {
        $json = $result.Content | ConvertFrom-Json
        if ($json.stations -and $json.stations.Count -gt 0) {
            Write-Host "   Found $($json.stations.Count) parking stations:" -ForegroundColor Gray
            foreach ($station in $json.stations[0..2]) {  # Show first 3
                Write-Host "     • $($station.name) - Capacity: $($station.capacity)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "   ⚠️  No parking stations found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "   Could not parse JSON response" -ForegroundColor Yellow
    }
}

# Test 4: Parking Station by ID
$result = Test-Endpoint -Url "$BackendUrl/api/parking-stations/CentralGarage" -Description "Specific Parking Station"

# Test 5: Transport Modes
$result = Test-Endpoint -Url "$BackendUrl/api/transport-modes/" -Description "Transport Modes API"

# Test 6: Travel Plans
$result = Test-Endpoint -Url "$BackendUrl/api/travel-plans/" -Description "Travel Plans API"

# Test 7: SPARQL Query Test (using Invoke-RestMethod for POST)
Write-Host "`nTesting: SPARQL Triple Count Query" -ForegroundColor Yellow
try {
    $sparqlQuery = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
    $response = Invoke-RestMethod -Uri "$FusekiUrl/smartcity/query" `
        -Method POST `
        -Headers @{
            "Accept" = "application/sparql-results+json"
            "Content-Type" = "application/sparql-query"
        } `
        -Body $sparqlQuery `
        -TimeoutSec $Timeout
    
    $count = $response.results.bindings[0].count.value
    Write-Host "✅ SUCCESS - Database contains $count triples" -ForegroundColor Green
}
catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "If tests failed from host but work with docker exec, try:" -ForegroundColor Yellow
Write-Host "1. Verify Flask binds to 0.0.0.0 (not 127.0.0.1)" -ForegroundColor White
Write-Host "2. Check Windows Firewall isn't blocking ports 3030/5000" -ForegroundColor White
Write-Host "3. Restart Docker Desktop" -ForegroundColor White
Write-Host "4. Run: docker-compose down && docker-compose up -d --build" -ForegroundColor White
Write-Host "5. Check container logs: docker logs smartcity-backend" -ForegroundColor White

Write-Host "`n=== Complete ===" -ForegroundColor Cyan