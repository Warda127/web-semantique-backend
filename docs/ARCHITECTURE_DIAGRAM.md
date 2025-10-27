# TravelPlan Integration - Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                      http://localhost:3000                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  👥 Persons │  │  🤖 AI Chat │  │ 🚌 Transport│  │ 🗺️ Travel   ││
│  │             │  │             │  │    Modes    │  │    Plans    ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
│                                           │               │          │
│                                           │               │          │
│  ┌────────────────────────────────────────┼───────────────┼────────┐│
│  │         Frontend Components             │               │        ││
│  ├────────────────────────────────────────┼───────────────┼────────┤│
│  │                                         │               │        ││
│  │  TransportModeList/Detail          TravelPlanList/Detail       ││
│  │          ↕                                    ↕                  ││
│  │  TransportModeService              TravelPlanService            ││
│  │          ↕                                    ↕                  ││
│  │  transportUtils.js                 travelPlanUtils.js           ││
│  │                                                                  ││
│  └──────────────────────────────────────────────────────────────────┘│
│                              ↕ HTTP REST API                         │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND SERVER                               │
│                      http://localhost:5000                           │
├─────────────────────────────────────────────────────────────────────┤
│                          Flask App                                   │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  app.py (Main Flask Application + CORS)                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│           │                                    │                     │
│           ↓                                    ↓                     │
│  ┌──────────────────────┐           ┌──────────────────────┐       │
│  │  transport_mode/     │           │  travel_plan/        │       │
│  │  routes.py           │           │  routes.py           │       │
│  │  Blueprint           │           │  Blueprint           │       │
│  └──────────────────────┘           └──────────────────────┘       │
│           │                                    │                     │
│           └────────────────┬───────────────────┘                     │
│                            │                                         │
│                            ↓ SPARQL Queries                          │
└─────────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────────┐
│                      FUSEKI TRIPLE STORE                             │
│                      http://localhost:3030                           │
├─────────────────────────────────────────────────────────────────────┤
│                      Dataset: smartcity                              │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    RDF/OWL Ontology                            │ │
│  │              WebSemEsprit (1).rdf                              │ │
│  ├───────────────────────────────────────────────────────────────┤ │
│  │                                                                │ │
│  │  Classes:                                                      │ │
│  │    • Person (Citizen, Tourist, Staff)                         │ │
│  │    • Station (MetroStation, BusStation, BikeStation)          │ │
│  │    • TransportMode (Metro, Bus, Bike)                         │ │
│  │    • TravelPlan (DailyCommute, SingleTrip, Weekly, etc.)      │ │
│  │                                                                │ │
│  │  Object Properties:                                            │ │
│  │    • usesTransport, managesStation, locatedAt                 │ │
│  │    • hasTravelPlan, usesTransportMode                         │ │
│  │    • hasStartStation, hasEndStation                           │ │
│  │                                                                │ │
│  │  Data Properties:                                              │ │
│  │    • hasName, hasSpeed, hasCapacity, hasLocation              │ │
│  │    • hasStartTime, hasEndTime, hasDaysOfWeek, isActive        │ │
│  │                                                                │ │
│  │  Individuals:                                                  │ │
│  │    • Alice, Bob, Charlie                                       │ │
│  │    • Stations, TransportModes, TravelPlans                    │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagram

### TravelPlan Query Flow

```
User clicks "🗺️ Travel Plans"
         ↓
┌────────────────────────────┐
│  TravelPlanList Component  │
│  - Renders table           │
│  - Handles search/sort     │
└────────────────────────────┘
         ↓ calls
┌────────────────────────────┐
│  TravelPlanService         │
│  .getAllPlans()            │
└────────────────────────────┘
         ↓ HTTP GET
┌────────────────────────────┐
│  /api/travel-plans/        │
│  (Flask endpoint)          │
└────────────────────────────┘
         ↓ executes
┌────────────────────────────┐
│  SPARQL Query:             │
│  SELECT ?plan ?type        │
│    ?person ?startStation   │
│    ?endStation ...         │
└────────────────────────────┘
         ↓ queries
┌────────────────────────────┐
│  Fuseki RDF Store          │
│  Dataset: smartcity        │
└────────────────────────────┘
         ↓ returns RDF
┌────────────────────────────┐
│  JSON Bindings:            │
│  [{plan, type, person,     │
│    startStation, ...}]     │
└────────────────────────────┘
         ↓ transforms
┌────────────────────────────┐
│  travelPlanUtils           │
│  - extractLocalName        │
│  - formatTime              │
└────────────────────────────┘
         ↓ renders
┌────────────────────────────┐
│  Table with 8 columns:     │
│  ID | Type | Person | ...  │
└────────────────────────────┘
```

## 🗂️ File Organization

```
web-semantique-backend/
├── app.py                           [Main Flask app + CORS]
├── ai_sparql_transformer.py         [AI integration]
├── requirements.txt                 [Python dependencies]
│
├── ontologie/
│   └── WebSemEsprit (1).rdf        [OWL/RDF Ontology]
│
├── transport_mode/                  [TransportMode Module]
│   ├── __init__.py
│   └── routes.py                    [REST endpoints for transport]
│
├── travel_plan/                     [TravelPlan Module - NEW ✨]
│   ├── __init__.py
│   └── routes.py                    [REST endpoints for plans]
│
├── docs/
│   ├── transport-mode-integration.md
│   └── travel-plan-integration.md   [NEW ✨]
│
└── static/
    └── index.html

web-semantique-front/
└── src/
    ├── App.js                       [Main React app + routing]
    ├── index.js                     [React entry point]
    │
    ├── components/
    │   ├── Sidebar.js               [Navigation menu]
    │   ├── PersonSearch.js          [Person management]
    │   ├── AIChat.js                [AI chat interface]
    │   │
    │   ├── TransportModeList.jsx    [Transport list]
    │   ├── TransportModeDetail.jsx  [Transport detail]
    │   │
    │   ├── TravelPlanList.jsx       [Plan list - NEW ✨]
    │   ├── TravelPlanDetail.jsx     [Plan detail - NEW ✨]
    │   │
    │   └── css/
    │       ├── Sidebar.css
    │       ├── PersonSearch.css
    │       └── AIChat.css
    │
    ├── services/
    │   ├── api.js                   [Base API + safeFetch]
    │   ├── transportModeService.js  [Transport API calls]
    │   └── travelPlanService.js     [Plan API calls - NEW ✨]
    │
    └── utils/
        ├── transportUtils.js        [Transport helpers]
        └── travelPlanUtils.js       [Plan helpers - NEW ✨]
```

## 🔄 REST API Endpoints

### TravelPlan Endpoints

```
┌──────────────────────────────────────────────────────────────┐
│  GET /api/travel-plans/                                      │
│  Returns: { plans: [...] }                                   │
│  Query params: ?q=search&debug=1                             │
├──────────────────────────────────────────────────────────────┤
│  GET /api/travel-plans/<localname>                           │
│  Returns: { uri, type, person, startStation, ... }           │
├──────────────────────────────────────────────────────────────┤
│  POST /api/travel-plans/                                     │
│  Body: { localname, class, person, startTime, ... }          │
│  Returns: { ok: true, uri }                                  │
└──────────────────────────────────────────────────────────────┘
```

### TransportMode Endpoints

```
┌──────────────────────────────────────────────────────────────┐
│  GET /api/transport-modes/                                   │
│  Returns: { modes: [...] }                                   │
├──────────────────────────────────────────────────────────────┤
│  GET /api/transport-modes/<localname>                        │
│  Returns: { uri, type, name, speed }                         │
├──────────────────────────────────────────────────────────────┤
│  POST /api/transport-modes/                                  │
│  Body: { localname, class, name, speed }                     │
│  Returns: { ok: true, uri }                                  │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Component Interaction

```
App.js
  │
  ├─ Sidebar
  │    └─ Handles tab switching
  │
  ├─ PersonSearch
  │
  ├─ AIChat
  │
  ├─ TransportModeList
  │    │
  │    ├─ Uses: TransportModeService
  │    ├─ Uses: transportUtils
  │    └─ Opens: TransportModeDetail (modal)
  │
  └─ TravelPlanList
       │
       ├─ Uses: TravelPlanService
       ├─ Uses: travelPlanUtils
       └─ Opens: TravelPlanDetail (modal)
```

## 🔐 Security & CORS

```
Frontend (localhost:3000)
         ↓ HTTP Request
Backend (localhost:5000)
         ↓ CORS Middleware
    @app.after_request
    - Access-Control-Allow-Origin: *
    - Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
    - Access-Control-Allow-Headers: Content-Type,Authorization
         ↓ Process Request
    Flask Blueprints
         ↓ Execute SPARQL
    Fuseki (localhost:3030)
```

## 📈 Scalability

### Current Implementation

- ✅ Single backend server
- ✅ Direct SPARQL queries
- ✅ Client-side filtering/sorting

### Future Enhancements

- 🔮 Add caching layer (Redis)
- 🔮 Implement pagination
- 🔮 Add WebSocket for real-time updates
- 🔮 Add authentication/authorization
- 🔮 Add GraphQL layer
- 🔮 Implement service workers for offline

## 🧪 Testing Strategy

```
Unit Tests
  ├─ Backend: pytest for routes
  ├─ Frontend: Jest for components
  └─ Utils: Test helper functions

Integration Tests
  ├─ API endpoint tests
  ├─ SPARQL query validation
  └─ Component interaction tests

E2E Tests
  ├─ Cypress/Playwright
  └─ Full user workflows
```

## 🎨 UI/UX Flow

```
User Journey: View Travel Plans

1. User lands on homepage (/)
   └─ Sees sidebar with menu items

2. User clicks "🗺️ Travel Plans"
   └─ URL changes to /travelplans
   └─ TravelPlanList loads

3. Component fetches data
   └─ Shows loading state
   └─ Renders table with plans

4. User searches "Alice"
   └─ Client-side filter applies
   └─ Table updates instantly

5. User clicks on a plan row
   └─ Modal opens with TravelPlanDetail
   └─ URL changes to /travelplans/AliceDailyPlan
   └─ Detailed info displays

6. User clicks Close
   └─ Modal closes
   └─ URL changes back to /travelplans
   └─ List view remains
```

## 💾 Data Model

```
TravelPlan (Abstract)
   │
   ├─ SingleTripPlan
   │    └─ For one-time journeys
   │
   ├─ DailyCommutePlan
   │    └─ For daily work/school commutes
   │
   ├─ WeeklyPlan
   │    └─ For weekly recurring patterns
   │
   ├─ SeasonalPlan
   │    └─ For seasonal variations
   │
   └─ TourPlan
        └─ For multi-day tours

Relationships:
  Person --hasTravelPlan--> TravelPlan
  TravelPlan --usesTransportMode--> TransportMode
  TravelPlan --hasStartStation--> Station
  TravelPlan --hasEndStation--> Station
```

## 🎊 Summary

This architecture provides:

- ✅ **Separation of Concerns** - Clear boundaries between layers
- ✅ **Scalability** - Easy to add new features
- ✅ **Maintainability** - Consistent patterns
- ✅ **Testability** - Each layer can be tested independently
- ✅ **User Experience** - Fast, responsive UI
- ✅ **Developer Experience** - Clear structure, good documentation

---

**For detailed implementation, see:**

- `TRAVELPLAN_INTEGRATION_SUMMARY.md` - Complete overview
- `TRAVELPLAN_QUICK_START.md` - Quick setup guide
- `docs/travel-plan-integration.md` - Technical documentation
