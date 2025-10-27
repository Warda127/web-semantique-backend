# TravelPlan Integration Documentation

## Overview

Complete integration for TravelPlan management in the SmartCity semantic web application. This follows the same architecture pattern as TransportMode integration.

## Backend Structure

### Module: `travel_plan/`

- `__init__.py` - Package marker
- `routes.py` - Flask blueprint with REST endpoints

### Endpoints

#### GET `/api/travel-plans/`

Lists all travel plans from the ontology.

**Query Parameters:**

- `q` (optional): Filter by person name, station name, or other related properties
- `debug` (optional): Set to `1` to include diagnostic information

**Response:**

```json
{
  "plans": [
    {
      "uri": "http://.../AliceDailyPlan",
      "type": "http://.../DailyCommutePlan",
      "person": "http://.../Alice",
      "personName": "Alice",
      "startStation": "http://.../StationA",
      "startStationName": "Station A",
      "endStation": "http://.../StationB",
      "endStationName": "Station B",
      "transportMode": "http://.../Metro1",
      "transportModeName": "Metro Line 1",
      "startTime": "08:00:00",
      "endTime": "09:00:00",
      "daysOfWeek": "Monday, Tuesday, Wednesday, Thursday, Friday",
      "isActive": "true"
    }
  ]
}
```

#### GET `/api/travel-plans/<localname>`

Fetches a specific travel plan by its local name.

**Response:** Single plan object (same structure as array item above)

#### POST `/api/travel-plans/`

Creates a new travel plan in Fuseki.

**Request Body:**

```json
{
  "localname": "BobTrip",
  "class": "http://.../SingleTripPlan",
  "person": "http://.../Bob",
  "startStation": "http://.../StationC",
  "endStation": "http://.../StationD",
  "transportMode": "http://.../Bus42",
  "startTime": "14:30:00",
  "isActive": true
}
```

**Fields:**

- `uri` (optional): Full URI for the new individual
- `localname` (optional): Local name to append to ontology base (used if uri not provided)
- `class` (required): Class URI (SingleTripPlan, DailyCommutePlan, WeeklyPlan, SeasonalPlan, TourPlan)
- `person` (optional): Person URI that has this plan
- `startStation` (optional): Start station URI
- `endStation` (optional): End station URI
- `transportMode` (optional): Transport mode URI
- `startTime` (optional): Start time (xsd:time format like "08:00:00")
- `endTime` (optional): End time
- `daysOfWeek` (optional): Days string (e.g., "Monday, Tuesday, Wednesday")
- `isActive` (optional): Boolean value

**Response:**

```json
{
  "ok": true,
  "uri": "http://.../BobTrip"
}
```

## Frontend Structure

### Services: `src/services/travelPlanService.js`

Service layer for TravelPlan API communication.

**Methods:**

- `getAllPlans(debug)` - Fetches all travel plans
- `getPlanByLocalName(localName, debug)` - Fetches specific plan

Both methods return `{ plans/plan, raw }` where raw contains debug info.

### Utils: `src/utils/travelPlanUtils.js`

Helper functions for TravelPlan data manipulation.

**Functions:**

- `extractLocalName(uri)` - Extracts local name from URI
- `extractTypeName(typeUri)` - Extracts type name from type URI
- `formatTime(time)` - Formats xsd:time values
- `formatBoolean(bool)` - Formats boolean values to Yes/No
- `filterPlans(plans, query)` - Filters plans by text search

### Components

#### `TravelPlanList.jsx`

Displays a table of all travel plans with:

- Search/filter functionality
- Sortable columns (ID, Type, Person, From, To, Mode, Time, Active)
- Click to view details
- Debug information panel

**Props:**

- `onSelect(plan)` - Callback when a plan is selected
- `debug` (boolean) - Enable debug mode

#### `TravelPlanDetail.jsx`

Shows detailed information about a single travel plan:

- Plan type and URI
- Person information
- Route (from/to stations)
- Transport mode
- Schedule (times, days, active status)
- Raw JSON data
- Debug information (when showDebug=true)

**Props:**

- `plan` (object) - The travel plan to display
- `showDebug` (boolean) - Show debug section

### App Integration

The `App.js` file handles:

- Route mapping: `/travelplans` → list view
- Route mapping: `/travelplans/:localName` → detail modal
- Tab switching via Sidebar
- Modal dialogs for plan details
- URL state synchronization

### Sidebar Navigation

Added new menu item:

```
🗺️ Travel Plans
```

## Ontology Classes

### TravelPlan (Parent Class)

Base class for all travel plans.

### Subclasses

1. **SingleTripPlan** - One-time, non-recurring journey
2. **DailyCommutePlan** - Regular daily travel (home/work/school)
3. **WeeklyPlan** - Regular weekly travel pattern
4. **SeasonalPlan** - Seasonal patterns (summer/winter, tourist seasons)
5. **TourPlan** - Multi-day exploration itinerary

## Object Properties

- `hasTravelPlan` - Links Person to TravelPlan
- `usesTransportMode` - Links TravelPlan to TransportMode
- `hasStartStation` - Links TravelPlan to start Station
- `hasEndStation` - Links TravelPlan to end Station

## Data Properties

- `hasStartTime` (xsd:time) - Plan start time
- `hasEndTime` (xsd:time) - Plan end time
- `hasDaysOfWeek` (xsd:string) - Days the plan is active
- `isActive` (xsd:boolean) - Whether the plan is currently active

## Example SPARQL Queries

### Insert Sample Data

```sparql
PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {
  :StationA a :Station ; :hasName "Station A" .
  :StationB a :Station ; :hasName "Station B" .
  :Metro1 a :Metro ; :hasName "Metro Line 1" .

  :AliceDailyPlan a :DailyCommutePlan ;
    :hasStartTime "08:00:00"^^xsd:time ;
    :hasEndTime "09:00:00"^^xsd:time ;
    :hasDaysOfWeek "Monday, Tuesday, Wednesday, Thursday, Friday" ;
    :isActive true ;
    :usesTransportMode :Metro1 ;
    :hasStartStation :StationA ;
    :hasEndStation :StationB .
  :Alice :hasTravelPlan :AliceDailyPlan .
}
```

### Query All Plans

```sparql
PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?person ?plan ?planType ?start ?end ?days ?active ?modeName ?startName ?endName
WHERE {
  ?person :hasTravelPlan ?plan .
  ?plan rdf:type ?planType .
  OPTIONAL { ?plan :hasStartTime ?start . }
  OPTIONAL { ?plan :hasEndTime ?end . }
  OPTIONAL { ?plan :hasDaysOfWeek ?days . }
  OPTIONAL { ?plan :isActive ?active . }
  OPTIONAL { ?plan :usesTransportMode ?mode . OPTIONAL { ?mode :hasName ?modeName . } }
  OPTIONAL { ?plan :hasStartStation ?s . OPTIONAL { ?s :hasName ?startName . } }
  OPTIONAL { ?plan :hasEndStation ?e . OPTIONAL { ?e :hasName ?endName . } }
}
```

## Usage Examples

### 1. Alice's Daily Commute

- **Type:** DailyCommutePlan
- **Schedule:** Mon-Fri, 08:00-09:00
- **Route:** Station A → Station B
- **Mode:** Metro Line 1
- **Active:** Yes

### 2. Bob's Single Trip

- **Type:** SingleTripPlan
- **Schedule:** One-time at 14:30
- **Route:** Station C → Station D
- **Mode:** Bus 42
- **Active:** Yes

### 3. Charlie's Tour

- **Type:** TourPlan
- **Schedule:** Weekends at 10:00
- **Route:** Museum → Old Town
- **Mode:** Tourist Metro
- **Active:** Yes

## Testing

1. **Start Backend:**

   ```bash
   cd web-semantique-backend
   python app.py
   ```

2. **Start Frontend:**

   ```bash
   cd web-semantique-front
   npm start
   ```

3. **Load Sample Data:**

   - Open Fuseki UI at http://localhost:3030
   - Go to dataset "smartcity" → Update tab
   - Paste the INSERT DATA queries from the examples

4. **Test UI:**
   - Navigate to http://localhost:3000/travelplans
   - Verify list displays correctly
   - Click on a plan to see details
   - Test search/filter functionality

## Troubleshooting

### No Plans Showing

1. Verify Fuseki is running and data is loaded
2. Click "Retry with debug" to see backend queries
3. Check browser console for errors
4. Verify backend endpoint at http://localhost:5000/api/travel-plans/

### Modal Not Opening

1. Check browser console for JavaScript errors
2. Verify plan has valid `id` field
3. Check URL updates to `/travelplans/:localName`

### CORS Errors

- Ensure backend CORS middleware is active in `app.py`
- Verify `Access-Control-Allow-Origin: *` in response headers

## Architecture Benefits

1. **Consistency** - Follows same pattern as TransportMode integration
2. **Reusability** - Shared utils and service patterns
3. **Maintainability** - Clear separation of concerns
4. **Extensibility** - Easy to add new plan types
5. **User Experience** - Intuitive navigation and search
6. **Developer Experience** - Debug mode for troubleshooting

## Future Enhancements

1. Add plan creation form in UI
2. Add plan editing/deletion
3. Add plan validation (e.g., time conflicts)
4. Add calendar view for plans
5. Add plan recommendations based on user patterns
6. Add capacity planning visualization
7. Add integration with real-time transport data
