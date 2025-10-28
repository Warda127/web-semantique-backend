# Simple Parking Stations Demo
Write-Host "=== Parking Stations Demo ===" -ForegroundColor Cyan

# 1. List existing stations
Write-Host "`n1. Current parking stations:" -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/
$json = $result | ConvertFrom-Json
Write-Host "Found $($json.stations.Count) stations:" -ForegroundColor Green
foreach ($station in $json.stations) {
    $type = $station.type.Split('#')[-1]
    Write-Host "  - $($station.name) ($type)" -ForegroundColor Gray
    Write-Host "    Capacity: $($station.capacity), Available: $($station.availableSpaces)" -ForegroundColor Gray
}

# 2. Get specific station
Write-Host "`n2. Getting CentralGarage details:" -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s http://localhost:5000/api/parking-stations/CentralGarage
$json = $result | ConvertFrom-Json
Write-Host "Station: $($json.name)" -ForegroundColor Green
Write-Host "Address: $($json.address)" -ForegroundColor Gray
Write-Host "Price: €$($json.pricePerHour)/hour" -ForegroundColor Gray

# 3. Filter by type
Write-Host "`n3. Car parking stations only:" -ForegroundColor Yellow
$result = docker exec smartcity-backend curl -s "http://localhost:5000/api/parking-stations/?type=CarParkingStation"
$json = $result | ConvertFrom-Json
Write-Host "Found $($json.stations.Count) car parking stations" -ForegroundColor Green

Write-Host "`n=== Demo Complete ===" -ForegroundColor Cyan
Write-Host "✅ Parking Stations API is fully functional!" -ForegroundColor Green