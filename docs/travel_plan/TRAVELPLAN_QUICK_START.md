# TravelPlan Integration - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Load Sample Data (2 minutes)

1. Open http://localhost:3030 (Fuseki UI)
2. Click on "smartcity" dataset
3. Go to "Update" tab
4. Copy and paste this query:

```sparql
PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {
  # Stations
  :StationA a :Station ; :hasName "Station A" .
  :StationB a :Station ; :hasName "Station B" .
  :StationC a :Station ; :hasName "Station C" .
  :StationD a :Station ; :hasName "Station D" .
  :Museum a :Station ; :hasName "Museum" .
  :OldTown a :Station ; :hasName "Old Town" .

  # Transport Modes
  :Metro1 a :Metro ; :hasName "Metro Line 1" .
  :Bus42 a :Bus ; :hasName "Bus 42" .
  :TourMetro a :Metro ; :hasName "Tourist Metro" .

  # Alice's Daily Commute
  :AliceDailyPlan a :DailyCommutePlan ;
    :hasStartTime "08:00:00"^^xsd:time ;
    :hasEndTime "09:00:00"^^xsd:time ;
    :hasDaysOfWeek "Monday, Tuesday, Wednesday, Thursday, Friday" ;
    :isActive true ;
    :usesTransportMode :Metro1 ;
    :hasStartStation :StationA ;
    :hasEndStation :StationB .
  :Alice :hasTravelPlan :AliceDailyPlan .

  # Bob's Single Trip
  :BobTrip a :SingleTripPlan ;
    :hasStartTime "14:30:00"^^xsd:time ;
    :usesTransportMode :Bus42 ;
    :hasStartStation :StationC ;
    :hasEndStation :StationD ;
    :isActive true .
  :Bob :hasTravelPlan :BobTrip .

  # Charlie's Tour Plan
  :CharlieTour a :TourPlan ;
    :hasStartTime "10:00:00"^^xsd:time ;
    :hasDaysOfWeek "Saturday, Sunday" ;
    :usesTransportMode :TourMetro ;
    :hasStartStation :Museum ;
    :hasEndStation :OldTown ;
    :isActive true .
  :Charlie :hasTravelPlan :CharlieTour .
}
```

5. Click "Execute"
6. You should see "Update succeeded"

### Step 2: Start Backend & Frontend

**Terminal 1 - Backend:**

```bash
cd web-semantique-backend
python app.py
```

Wait for: `Running on http://127.0.0.1:5000`

**Terminal 2 - Frontend:**

```bash
cd web-semantique-front
npm start
```

Wait for browser to open at http://localhost:3000

### Step 3: Use the UI

1. Click **🗺️ Travel Plans** in the sidebar
2. You should see 3 plans in the table
3. Click any row to see details
4. Try searching: "Alice", "Museum", "Saturday"

## 📁 Project Structure

```
SEM/
├── web-semantique-backend/
│   ├── app.py                    [✏️ Modified - registered travel_plan blueprint]
│   ├── travel_plan/              [✨ NEW]
│   │   ├── __init__.py
│   │   └── routes.py             [REST API endpoints]
│   ├── ontologie/
│   │   └── WebSemEsprit (1).rdf [✏️ Modified - added TravelPlan classes]
│   └── docs/
│       └── travel-plan-integration.md [✨ NEW - documentation]
│
└── web-semantique-front/
    └── src/
        ├── App.js                [✏️ Modified - integrated TravelPlan UI]
        ├── components/
        │   ├── Sidebar.js        [✏️ Modified - added menu item]
        │   ├── TravelPlanList.jsx    [✨ NEW]
        │   └── TravelPlanDetail.jsx  [✨ NEW]
        ├── services/
        │   └── travelPlanService.js  [✨ NEW]
        └── utils/
            └── travelPlanUtils.js    [✨ NEW]
```

## 🎯 What You Can Do

### View All Plans

Navigate to: http://localhost:3000/travelplans

### View Specific Plan

URL: http://localhost:3000/travelplans/AliceDailyPlan

### API Endpoints

- **List:** `GET http://localhost:5000/api/travel-plans/`
- **Detail:** `GET http://localhost:5000/api/travel-plans/AliceDailyPlan`
- **Create:** `POST http://localhost:5000/api/travel-plans/`

### Search & Filter

Try these searches in the UI:

- "Alice" - finds Alice's plan
- "Museum" - finds Charlie's tour
- "Metro" - finds plans using metro
- "Saturday" - finds weekend plans

## 🎨 UI Features

### Table Columns

| Column | Description                                |
| ------ | ------------------------------------------ |
| ID     | Local name of the plan                     |
| Type   | Plan type (DailyCommute, SingleTrip, etc.) |
| Person | Who owns this plan                         |
| From   | Start station                              |
| To     | End station                                |
| Mode   | Transport mode used                        |
| Time   | Start time                                 |
| Active | Whether plan is active                     |

### Interactive Features

- ✅ Click column headers to sort
- ✅ Type in search box to filter
- ✅ Click row to see details
- ✅ Click "Refresh" to reload
- ✅ Click "Retry with debug" for troubleshooting

## 🔍 Verify Installation

### Check Backend

```bash
curl http://localhost:5000/api/travel-plans/
```

Should return JSON with plans array.

### Check Frontend

1. Open browser console (F12)
2. Navigate to Travel Plans
3. Should see: `[TravelPlanList] received {count: 3, raw: {...}}`

### Check Ontology

In Fuseki UI, run this query:

```sparql
PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
SELECT ?plan ?type WHERE {
  ?plan a ?type .
  FILTER(?type = :DailyCommutePlan || ?type = :SingleTripPlan || ?type = :TourPlan)
}
```

Should return 3 results.

## 🐛 Troubleshooting

### Problem: "No travel plans returned"

**Solution:**

1. Check Fuseki is running: http://localhost:3030
2. Verify data was loaded (run SELECT query above)
3. Click "Retry with debug" button
4. Check browser console for errors

### Problem: Backend error "ModuleNotFoundError: No module named 'travel_plan'"

**Solution:**

```bash
cd web-semantique-backend
# Verify file exists
ls travel_plan/routes.py
# Restart backend
python app.py
```

### Problem: Modal doesn't open

**Solution:**

1. Check browser console for errors
2. Verify plan has an `id` field
3. Check URL changes to `/travelplans/:localName`

### Problem: CORS errors

**Solution:**

- Backend CORS is already configured in `app.py`
- Try restarting backend
- Check response headers include `Access-Control-Allow-Origin: *`

## 📊 Example Data Summary

| Person  | Plan Type        | Route                 | Mode          | Schedule            |
| ------- | ---------------- | --------------------- | ------------- | ------------------- |
| Alice   | DailyCommutePlan | Station A → Station B | Metro Line 1  | Mon-Fri 08:00-09:00 |
| Bob     | SingleTripPlan   | Station C → Station D | Bus 42        | One-time 14:30      |
| Charlie | TourPlan         | Museum → Old Town     | Tourist Metro | Sat-Sun 10:00       |

## 🎓 Next Steps

1. **Explore the UI** - Try all features
2. **Read Documentation** - Check `travel-plan-integration.md`
3. **Test API** - Use curl or Postman
4. **Add More Data** - Create your own plans
5. **Customize** - Modify components to your needs

## 📚 Documentation Files

- `TRAVELPLAN_INTEGRATION_SUMMARY.md` - Complete overview
- `docs/travel-plan-integration.md` - Technical documentation
- `TRAVELPLAN_QUICK_START.md` - This file

## ✅ Success Checklist

- [ ] Fuseki running on port 3030
- [ ] Sample data loaded (3 plans)
- [ ] Backend running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can see Travel Plans in sidebar
- [ ] Table shows 3 plans
- [ ] Can click and see details
- [ ] Search/filter works
- [ ] No console errors

**🎉 If all checked, you're ready to go!**

## 💡 Tips

- Use **debug mode** when developing
- Check **browser console** for client-side issues
- Check **terminal output** for server-side issues
- Use **Fuseki UI** to verify data
- Read **full documentation** for advanced features

---

**Need Help?** Check `TRAVELPLAN_INTEGRATION_SUMMARY.md` for complete details.
