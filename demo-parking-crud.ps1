# Parking Stations CRUD Operations Demo
Write-Host "`n=== Parking Stations CRUD Demo ===" -ForegroundColor Cyan

# Demo 1: List all existing parking stations
Write-Host "`n1. Listing all existing parking stations..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/
$json = $result | ConvertFrom-Json
Write-Host "✅ Found $($json.stations.Count) existing parking stations:" -ForegroundColor Green
foreach ($station in $json.stations) {
    Write-Host "  📍 $($station.name)" -ForegroundColor Gray
    Write-Host "     Type: $($station.type.Split('#')[-1])" -ForegroundColor Gray
    Write-Host "     Capacity: $($station.capacity) | Available: $($station.availableSpaces)" -ForegroundColor Gray
    Write-Host "     Price: €$($station.pricePerHour)/hour" -ForegroundColor Gray
    Write-Host "     Address: $($station.address)" -ForegroundColor Gray
    Write-Host ""
}

# Demo 2: Create a new car parking station
Write-Host "`n2. Creating a new car parking station..." -ForegroundColor Yellow
$newCarStation = @{
    localname = "DowntownGarage"
    type = "CarParkingStation"
    name = "Downtown Business Garage"
    capacity = 150
    availableSpaces = 75
    pricePerHour = 4.0
} | ConvertTo-Json

# Write to temp file and create station
$newCarStation | Out-File -FilePath "temp-car-station.json" -Encoding UTF8
docker cp temp-car-station.json smartcity-backend:/tmp/temp-car-station.json
$result = docker exec smartcity-backend sh -c "curl -s -X POST -H 'Content-Type: application/json' -d @/tmp/temp-car-station.json http://localhost:5000/api/parking-stations/"
$json = $result | ConvertFrom-Json
Write-Host "✅ Created car parking station: $($json.uri)" -ForegroundColor Green

# Demo 3: Create a new bike parking station
Write-Host "`n3. Creating a new bike parking station..." -ForegroundColor Yellow
$newBikeStation = @{
    localname = "UniversityBikes"
    type = "BikeParkingStation"
    name = "University Campus Bike Park"
    capacity = 80
    availableSpaces = 25
    pricePerHour = 1.0
} | ConvertTo-Json

$newBikeStation | Out-File -FilePath "temp-bike-station.json" -Encoding UTF8
docker cp temp-bike-station.json smartcity-backend:/tmp/temp-bike-station.json
$result = docker exec smartcity-backend sh -c "curl -s -X POST -H 'Content-Type: application/json' -d @/tmp/temp-bike-station.json http://localhost:5000/api/parking-stations/"
$json = $result | ConvertFrom-Json
Write-Host "✅ Created bike parking station: $($json.uri)" -ForegroundColor Green

# Demo 4: Create an EV charging station
Write-Host "`n4. Creating a new EV charging station..." -ForegroundColor Yellow
$newEVStation = @{
    localname = "MallChargers"
    type = "EVChargingStation"
    name = "Shopping Mall EV Chargers"
    capacity = 20
    availableSpaces = 8
    pricePerHour = 6.5
} | ConvertTo-Json

$newEVStation | Out-File -FilePath "temp-ev-station.json" -Encoding UTF8
docker cp temp-ev-station.json smartcity-backend:/tmp/temp-ev-station.json
$result = docker exec smartcity-backend sh -c "curl -s -X POST -H 'Content-Type: application/json' -d @/tmp/temp-ev-station.json http://localhost:5000/api/parking-stations/"
$json = $result | ConvertFrom-Json
Write-Host "✅ Created EV charging station: $($json.uri)" -ForegroundColor Green

# Demo 5: List all stations again to see the new ones
Write-Host "`n5. Listing all parking stations after creation..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/
$json = $result | ConvertFrom-Json
Write-Host "✅ Now we have $($json.stations.Count) total parking stations:" -ForegroundColor Green
foreach ($station in $json.stations) {
    $type = $station.type.Split('#')[-1]
    $emoji = switch ($type) {
        "CarParkingStation" { "🚗" }
        "BikeParkingStation" { "🚲" }
        "EVChargingStation" { "⚡" }
        default { "📍" }
    }
    Write-Host "  $emoji $($station.name) ($type)" -ForegroundColor Gray
}

# Demo 6: Filter by type
Write-Host "`n6. Filtering by CarParkingStation type..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s "http://localhost:5000/api/parking-stations/?type=CarParkingStation"
$json = $result | ConvertFrom-Json
Write-Host "✅ Found $($json.stations.Count) car parking stations:" -ForegroundColor Green
foreach ($station in $json.stations) {
    Write-Host "  🚗 $($station.name)" -ForegroundColor Gray
}

# Demo 7: Search by name
Write-Host "`n7. Searching for stations with 'Garage' in the name..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s "http://localhost:5000/api/parking-stations/?q=Garage"
$json = $result | ConvertFrom-Json
Write-Host "✅ Found $($json.stations.Count) stations matching 'Garage':" -ForegroundColor Green
foreach ($station in $json.stations) {
    Write-Host "  📍 $($station.name)" -ForegroundColor Gray
}

# Demo 8: Update available spaces (simulate parking activity)
Write-Host "`n8. Simulating parking activity - updating available spaces..." -ForegroundColor Yellow
$updateData = @{ availableSpaces = 60 } | ConvertTo-Json
$updateData | Out-File -FilePath "temp-update.json" -Encoding UTF8
docker cp temp-update.json smartcity-backend:/tmp/temp-update.json

$result = docker exec smartcity-backend sh -c "curl -s -X PUT -H 'Content-Type: application/json' -d @/tmp/temp-update.json http://localhost:5000/api/parking-stations/DowntownGarage"
$json = $result | ConvertFrom-Json
Write-Host "✅ Updated DowntownGarage available spaces to: $($json.availableSpaces)" -ForegroundColor Green

# Demo 9: Verify the update
Write-Host "`n9. Verifying the update..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/DowntownGarage
$json = $result | ConvertFrom-Json
Write-Host "✅ DowntownGarage now has $($json.availableSpaces) available spaces out of $($json.capacity)" -ForegroundColor Green

# Demo 10: Clean up - delete the demo stations
Write-Host "`n10. Cleaning up demo stations..." -ForegroundColor Yellow
$demoStations = @("DowntownGarage", "UniversityBikes", "MallChargers")
foreach ($station in $demoStations) {
    $result = docker exec smartcity-backend curl -s -X DELETE http://localhost:5000/api/parking-stations/$station
    $json = $result | ConvertFrom-Json
    Write-Host "✅ Deleted $station: $($json.message)" -ForegroundColor Green
}

# Demo 11: Final count
Write-Host "`n11. Final parking stations count..." -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/
$json = $result | ConvertFrom-Json
Write-Host "✅ Back to original $($json.stations.Count) parking stations" -ForegroundColor Green

# Clean up temp files
Remove-Item -Path "temp-*.json" -ErrorAction SilentlyContinue

Write-Host "`n=== CRUD Demo Complete ===" -ForegroundColor Cyan
Write-Host "`n🎉 Parking Stations API Summary:" -ForegroundColor White
Write-Host "✅ CREATE: Successfully created car, bike, and EV parking stations" -ForegroundColor Green
Write-Host "✅ READ: Listed all stations, filtered by type, searched by name" -ForegroundColor Green
Write-Host "✅ UPDATE: Modified available spaces to simulate real-time updates" -ForegroundColor Green
Write-Host "✅ DELETE: Removed demo stations to clean up" -ForegroundColor Green
Write-Host "`n📊 Features demonstrated:" -ForegroundColor White
Write-Host "  - Multiple parking station types (Car, Bike, EV)" -ForegroundColor Gray
Write-Host "  - Real-time availability tracking" -ForegroundColor Gray
Write-Host "  - Type-based filtering" -ForegroundColor Gray
Write-Host "  - Name-based search" -ForegroundColor Gray
Write-Host "  - Full CRUD operations" -ForegroundColor Gray
Write-Host "  - Data persistence in SPARQL database" -ForegroundColor Gray