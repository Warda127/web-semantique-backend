# 🚗 Parking Station API Documentation

## Base URL
```
http://localhost:5000/api/parking-stations
```

---

## Endpoints

### 1. List All Parking Stations
**GET** `/api/parking-stations/`

List all parking stations with optional filtering.

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Filter by name (case-insensitive substring match) |
| `type` | string | Filter by parking type: `CarParkingStation`, `BikeParkingStation`, or `EVChargingStation` |

#### Example Requests
```bash
# Get all parking stations
GET /api/parking-stations/

# Filter by name
GET /api/parking-stations/?q=downtown

# Filter by type
GET /api/parking-stations/?type=CarParkingStation

# Combine filters
GET /api/parking-stations/?q=central&type=BikeParkingStation
```

#### Response (200 OK)
```json
{
  "stations": [
    {
      "uri": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#ParkingStation1",
      "type": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#CarParkingStation",
      "name": "Downtown Parking",
      "capacity": "200",
      "availableSpaces": "45",
      "pricePerHour": "2.5",
      "address": "123 Main Street",
      "latitude": "36.8065",
      "longitude": "10.1815",
      "operatingHours": "24/7"
    }
  ]
}
```

---

### 2. Get Specific Parking Station
**GET** `/api/parking-stations/<localname>`

Retrieve details of a specific parking station by its local name.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `localname` | string | The local name part of the station URI (e.g., "ParkingStation1") |

#### Example Request
```bash
GET /api/parking-stations/ParkingStation1
```

#### Response (200 OK)
```json
{
  "uri": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#ParkingStation1",
  "type": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#CarParkingStation",
  "name": "Downtown Parking",
  "capacity": "200",
  "availableSpaces": "45",
  "pricePerHour": "2.5",
  "address": "123 Main Street",
  "latitude": "36.8065",
  "longitude": "10.1815",
  "operatingHours": "24/7"
}
```

#### Response (404 Not Found)
```json
{
  "error": "Not found"
}
```

---

### 3. Create Parking Station
**POST** `/api/parking-stations/`

Create a new parking station in the ontology.

#### Request Body
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `localname` | string | ✅ Yes | Unique identifier for the station |
| `type` | string | ✅ Yes | One of: `CarParkingStation`, `BikeParkingStation`, `EVChargingStation` |
| `name` | string | No | Human-readable name |
| `capacity` | integer | No | Total parking spaces |
| `availableSpaces` | integer | No | Currently available spaces |
| `pricePerHour` | float | No | Price per hour in local currency |
| `address` | string | No | Street address |
| `latitude` | float | No | GPS latitude |
| `longitude` | float | No | GPS longitude |
| `operatingHours` | string | No | Operating hours (e.g., "24/7", "08:00-20:00") |

#### Example Request
```json
POST /api/parking-stations/
Content-Type: application/json

{
  "localname": "CentralPark",
  "type": "CarParkingStation",
  "name": "Central Park Garage",
  "capacity": 150,
  "availableSpaces": 75,
  "pricePerHour": 3.0,
  "address": "456 Park Avenue",
  "latitude": 36.8100,
  "longitude": 10.1850,
  "operatingHours": "06:00-22:00"
}
```

#### Response (201 Created)
```json
{
  "ok": true,
  "uri": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#CentralPark"
}
```

#### Response (400 Bad Request)
```json
{
  "error": "localname required"
}
```

---

### 4. Update Parking Station
**PUT** `/api/parking-stations/<localname>`

Update parking station information (typically used to update available spaces).

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `localname` | string | The local name of the station to update |

#### Request Body
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availableSpaces` | integer | ✅ Yes | New available spaces count |

#### Example Request
```json
PUT /api/parking-stations/CentralPark
Content-Type: application/json

{
  "availableSpaces": 60
}
```

#### Response (200 OK)
```json
{
  "ok": true,
  "uri": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#CentralPark",
  "availableSpaces": 60
}
```

#### Response (400 Bad Request)
```json
{
  "error": "availableSpaces required"
}
```

---

### 5. Delete Parking Station
**DELETE** `/api/parking-stations/<localname>`

Remove a parking station from the ontology.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `localname` | string | The local name of the station to delete |

#### Example Request
```bash
DELETE /api/parking-stations/CentralPark
```

#### Response (200 OK)
```json
{
  "ok": true,
  "message": "Parking station deleted"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 500 Internal Server Error
```json
{
  "error": "Fuseki update failed",
  "status": 500,
  "body": "Error details..."
}
```

### Timeout Error
```json
{
  "error": "Update error: Connection timeout"
}
```

---

## Parking Station Types

The API supports three types of parking stations:

1. **CarParkingStation** - Standard car parking
2. **BikeParkingStation** - Bicycle parking
3. **EVChargingStation** - Electric vehicle charging station

---

## PowerShell Testing Commands

```powershell
# List all stations
curl http://localhost:5000/api/parking-stations/

# Filter by name
curl "http://localhost:5000/api/parking-stations/?q=central"

# Get specific station
curl http://localhost:5000/api/parking-stations/ParkingStation1

# Create new station
curl -X POST http://localhost:5000/api/parking-stations/ `
  -H "Content-Type: application/json" `
  -d '{\"localname\":\"TestParking\",\"type\":\"CarParkingStation\",\"name\":\"Test Parking\",\"capacity\":100,\"availableSpaces\":50}'

# Update available spaces
curl -X PUT http://localhost:5000/api/parking-stations/TestParking `
  -H "Content-Type: application/json" `
  -d '{\"availableSpaces\":45}'

# Delete station
curl -X DELETE http://localhost:5000/api/parking-stations/TestParking
```

---

## Notes

- All URI fields in responses use the full ontology namespace
- Numeric fields (capacity, availableSpaces, pricePerHour, latitude, longitude) are returned as strings in the response but should be sent as numbers in requests
- The `type` parameter in GET requests and the `type` field in POST requests use only the local class name (e.g., "CarParkingStation"), not the full URI
- Available spaces should never exceed capacity (but this is not enforced by the API)
