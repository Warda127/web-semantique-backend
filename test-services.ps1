# Smart City Docker Services Test Script
# Save as: test-services.ps1
# Run: .\test-services.ps1

Write-Host "`n=== Testing Smart City Services ===" -ForegroundColor Cyan

# 1. Test Fuseki Ping
Write-Host "`n1. Testing Fuseki Ping..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3030/$/ping" -Method GET -ErrorAction Stop
    Write-Host "✅ Fuseki is running!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Fuseki not responding: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Test Datasets
Write-Host "`n2. Checking Fuseki Datasets..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3030/$/datasets" -Method GET -ErrorAction Stop
    Write-Host "✅ Datasets endpoint accessible!" -ForegroundColor Green
    if ($response.Content -match "smartcity") {
        Write-Host "✅ 'smartcity' dataset found!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  'smartcity' dataset not found in response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Cannot access datasets: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Test SPARQL Query - Count triples
Write-Host "`n3. Testing SPARQL Query (Count triples)..." -ForegroundColor Yellow
try {
    $sparqlQuery = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
    $response = Invoke-WebRequest -Uri "http://localhost:3030/smartcity/query" -Method POST -ContentType "application/sparql-query" -Body $sparqlQuery -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    $count = $json.results.bindings[0].count.value
    Write-Host "✅ SPARQL query successful! Found $count triples in database" -ForegroundColor Green
    
    if ([int]$count -gt 0) {
        Write-Host "✅ Database contains data" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database appears to be empty" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ SPARQL query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Test SPARQL Query - Sample data
Write-Host "`n4. Testing SPARQL Query (Sample data)..." -ForegroundColor Yellow
try {
    $sparqlQuery = "SELECT * WHERE { ?s ?p ?o } LIMIT 5"
    $response = Invoke-WebRequest -Uri "http://localhost:3030/smartcity/query" -Method POST -ContentType "application/sparql-query" -Body $sparqlQuery -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    $count = $json.results.bindings.Count
    Write-Host "✅ Sample query successful! Found $count sample results" -ForegroundColor Green
    
    if ($count -gt 0) {
        Write-Host "Sample triple:" -ForegroundColor Gray
        $first = $json.results.bindings[0]
        Write-Host "  Subject: $($first.s.value)" -ForegroundColor Gray
        Write-Host "  Predicate: $($first.p.value)" -ForegroundColor Gray
        Write-Host "  Object: $($first.o.value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Sample SPARQL query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Test Backend Health
Write-Host "`n5. Testing Backend Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/persons" -Method GET -ErrorAction Stop
    Write-Host "✅ Backend is responding!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend not responding: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. Test Persons API
Write-Host "`n6. Testing Persons API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/persons" -Method GET -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✅ Persons API working!" -ForegroundColor Green
    
    if ($json -is [array] -and $json.Count -gt 0) {
        Write-Host "Found $($json.Count) persons" -ForegroundColor Gray
        Write-Host "First person: $($json[0].name) ($($json[0].type))" -ForegroundColor Gray
    } elseif ($json.Count -eq 0) {
        Write-Host "⚠️  No persons found in database" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Persons API failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. Test Transport Modes API
Write-Host "`n7. Testing Transport Modes API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/transport-modes/" -Method GET -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✅ Transport Modes API working!" -ForegroundColor Green
    
    if ($json.modes -and $json.modes.Count -gt 0) {
        Write-Host "Found $($json.modes.Count) transport modes" -ForegroundColor Gray
        Write-Host "First mode: $($json.modes[0].name) ($($json.modes[0].type))" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No transport modes found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Transport Modes API failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 8. Test Parking Stations API
Write-Host "`n8. Testing Parking Stations API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/parking-stations/" -Method GET -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✅ Parking Stations API working!" -ForegroundColor Green
    
    if ($json.stations -and $json.stations.Count -gt 0) {
        Write-Host "Found $($json.stations.Count) parking stations" -ForegroundColor Gray
        Write-Host "First station: $($json.stations[0].name) ($($json.stations[0].type))" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No parking stations found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Parking Stations API failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 9. Test Travel Plans API
Write-Host "`n9. Testing Travel Plans API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/travel-plans/" -Method GET -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✅ Travel Plans API working!" -ForegroundColor Green
    
    if ($json.plans -and $json.plans.Count -gt 0) {
        Write-Host "Found $($json.plans.Count) travel plans" -ForegroundColor Gray
        Write-Host "First plan: $($json.plans[0].type) for $($json.plans[0].personName)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No travel plans found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Travel Plans API failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 10. Test AI Query API
Write-Host "`n10. Testing AI Query API..." -ForegroundColor Yellow
try {
    $testQuery = @{
        question = "Show me all persons"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/ai/query" -Method POST -ContentType "application/json" -Body $testQuery -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✅ AI Query API working!" -ForegroundColor Green
    
    if ($json.results -and $json.results.Count -gt 0) {
        Write-Host "AI found $($json.results.Count) results" -ForegroundColor Gray
        Write-Host "Generated SPARQL: $($json.sparql_query)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  AI query returned no results" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ AI Query API failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Testing Complete ===" -ForegroundColor Cyan
Write-Host "`nSummary:" -ForegroundColor White
Write-Host "- Fuseki SPARQL database should be accessible on port 3030" -ForegroundColor Gray
Write-Host "- Flask backend should be accessible on port 5000" -ForegroundColor Gray
Write-Host "- All APIs should return JSON responses" -ForegroundColor Gray
Write-Host "- If services are not running, use: docker-compose up -d" -ForegroundColor Gray