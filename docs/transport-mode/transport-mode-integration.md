# Transport Mode Integration Guide

## Backend API Contract

### Endpoints
1. GET /api/transport-modes/
   - Returns list of all transport modes
   - Response: { modes: TransportMode[] }
   - Optional query param: ?debug=1 for additional debug info

2. GET /api/transport-modes/{localname}
   - Returns single transport mode by local name (e.g., "Bike_01")
   - Response: TransportMode object

### Data Models
```typescript
interface TransportMode {
  uri: string;        // Full URI (e.g., "http://.../ontologies/.../Bike_01")
  type: string;       // Class URI (e.g., "http://.../ontologies/.../Bike")
  name: string|null;  // Optional name
  speed: string;      // Speed value (convert to number for display/sorting)
}
```

### Example Response
```json
{
  "modes": [
    {
      "uri": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Bike_01",
      "type": "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Bike",
      "name": null,
      "speed": "20"
    }
  ]
}
```

## Integration Requirements

### Service Layer
1. Create a TransportModeService:
   - Methods for fetching all modes and single mode
   - Error handling and response transformation
   - Optional debug mode support

### UI Components
1. Search/Filter:
   - Input field for text search
   - Client-side filtering on:
     - Local name (e.g., "Bike_01")
     - Type (e.g., "Bike", "Bus", "Metro")
     - Speed (support numeric comparisons)

2. List View:
   - Table/grid showing:
     - ID (local name from URI)
     - Type (shortened)
     - Speed (as number)
   - Sorting capabilities
   - Responsive design

3. Detail View:
   - Show full URI
   - All properties
   - Debug information when enabled

### Data Processing
1. URI handling:
   - Extract local name: uri.split(/[#/]/).pop()
   - Extract type name: type.split(/[#/]/).pop()

2. Speed handling:
   - Convert string to number
   - Support numeric filtering
   - Format for display

## Prompt for GitHub Copilot

You are tasked with integrating a Transport Mode feature into an existing frontend project. The backend provides a REST API for querying transport modes (bikes, buses, metro) from an RDF/OWL ontology. Create the necessary service and UI components following these requirements:

1. Create a TransportModeService class/module that:
   - Encapsulates API calls to /api/transport-modes/
   - Handles errors and response transformation
   - Supports debug mode
   - Integrates with existing HTTP client/fetch setup

2. Create a TransportModeList component that:
   - Shows a searchable, sortable list of transport modes
   - Implements client-side filtering across ID, type, speed
   - Matches the existing person list styling/layout
   - Supports responsive design

3. Create a TransportModeDetail component that:
   - Shows full details when a transport is selected
   - Displays debug information when enabled
   - Matches existing detail view patterns

4. Data utilities for:
   - URI/type string processing
   - Speed number conversion/formatting
   - Search/filter logic

The implementation should:
- Match existing project patterns and styling
- Reuse shared components where possible
- Support the same debug features as person entity
- Handle all error cases gracefully

Show me the service layer implementation first, then the main component structure.
