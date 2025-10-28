import os
from flask import Blueprint, jsonify, request
from SPARQLWrapper import SPARQLWrapper, JSON

# Robust import for requests (fallback to urllib shim if not installed)
try:
    import requests
except Exception:
    import urllib.request as _ur
    import urllib.error as _ue

    class _SimpleResponse:
        def __init__(self, code, text):
            self.status_code = code
            self.text = text

    class _SimpleRequests:
        @staticmethod
        def post(url, data, headers=None, timeout=None):
            if isinstance(data, str):
                data = data.encode('utf-8')
            req = _ur.Request(url, data=data, headers=headers or {}, method='POST')
            try:
                with _ur.urlopen(req, timeout=timeout) as resp:
                    return _SimpleResponse(resp.getcode(), resp.read().decode('utf-8'))
            except _ue.HTTPError as e:
                body = None
                try:
                    body = e.read().decode('utf-8')
                except Exception:
                    body = str(e)
                return _SimpleResponse(getattr(e, "code", 500), body)

    requests = _SimpleRequests()

router = Blueprint('travel_plan', __name__)

# Fuseki endpoints - use environment variables from docker-compose
FUSEKI_ENDPOINT = os.getenv('FUSEKI_QUERY', "http://localhost:3030/smartcity/query")
FUSEKI_UPDATE = os.getenv('FUSEKI_UPDATE', "http://localhost:3030/smartcity/update")

def execute_sparql_query(query):
    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"[travel_plan] SPARQL error: {e} (endpoint={FUSEKI_ENDPOINT})")
        return None

@router.route('/', methods=['GET'])
def list_travel_plans():
    """
    GET /api/travel-plans/
    Query: select individuals of TravelPlan classes (SingleTripPlan, DailyCommutePlan, WeeklyPlan, SeasonalPlan, TourPlan)
    Optional params:
      - q : filter by related properties (person name, station name, etc.)
      - debug=1 : include diagnostic info
    """
    q = request.args.get('q', '').replace('"', '\\"')
    debug = request.args.get('debug', '0') == '1'

    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
    filter_clause = f'FILTER regex(str(?personName), "{q}", "i")' if q else ""

    # Primary SPARQL: match all TravelPlan subclasses
    primary_q = f"""
    PREFIX sc: <{ns}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?plan ?type ?person ?personName ?startStation ?startStationName ?endStation ?endStationName 
           ?transportMode ?transportModeName ?startTime ?endTime ?daysOfWeek ?isActive
    WHERE {{
      ?plan a ?type .
      FILTER(?type = sc:SingleTripPlan || ?type = sc:DailyCommutePlan || ?type = sc:WeeklyPlan || 
             ?type = sc:SeasonalPlan || ?type = sc:TourPlan || ?type = sc:TravelPlan)
      
      OPTIONAL {{ 
        ?person sc:hasTravelPlan ?plan .
        OPTIONAL {{ ?person sc:hasName ?personName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:hasStartStation ?startStation . 
        OPTIONAL {{ ?startStation sc:hasName ?startStationName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:hasEndStation ?endStation . 
        OPTIONAL {{ ?endStation sc:hasName ?endStationName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:usesTransportMode ?transportMode . 
        OPTIONAL {{ ?transportMode sc:hasName ?transportModeName . }}
      }}
      OPTIONAL {{ ?plan sc:hasStartTime ?startTime . }}
      OPTIONAL {{ ?plan sc:hasEndTime ?endTime . }}
      OPTIONAL {{ ?plan sc:hasDaysOfWeek ?daysOfWeek . }}
      OPTIONAL {{ ?plan sc:isActive ?isActive . }}
      
      {filter_clause}
    }}
    ORDER BY ?plan
    """
    print("[travel_plan] Running TravelPlan query")
    print(primary_q)
    results = execute_sparql_query(primary_q)
    bindings = results.get("results", {}).get("bindings", []) if results else []

    if bindings:
        plans = []
        for b in bindings:
            plans.append({
                "uri": b["plan"]["value"],
                "type": b.get("type", {}).get("value"),
                "person": b.get("person", {}).get("value"),
                "personName": b.get("personName", {}).get("value"),
                "startStation": b.get("startStation", {}).get("value"),
                "startStationName": b.get("startStationName", {}).get("value"),
                "endStation": b.get("endStation", {}).get("value"),
                "endStationName": b.get("endStationName", {}).get("value"),
                "transportMode": b.get("transportMode", {}).get("value"),
                "transportModeName": b.get("transportModeName", {}).get("value"),
                "startTime": b.get("startTime", {}).get("value"),
                "endTime": b.get("endTime", {}).get("value"),
                "daysOfWeek": b.get("daysOfWeek", {}).get("value"),
                "isActive": b.get("isActive", {}).get("value")
            })
        resp = {"plans": plans}
        return jsonify(resp)

    # fallback: return empty with debug info if requested
    resp = {"plans": []}
    if debug:
        resp["_query"] = primary_q
    return jsonify(resp), 200

@router.route('/<path:localname>', methods=['GET'])
def get_travel_plan(localname):
    """
    GET /api/travel-plans/<localname>
    Fetch a specific travel plan by its localname
    """
    q_local = localname.replace('"', '\\"')
    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    single_q = f"""
    PREFIX sc: <{ns}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT ?plan ?type ?person ?personName ?startStation ?startStationName ?endStation ?endStationName 
           ?transportMode ?transportModeName ?startTime ?endTime ?daysOfWeek ?isActive
    WHERE {{
      ?plan a ?type .
      FILTER(?type = sc:SingleTripPlan || ?type = sc:DailyCommutePlan || ?type = sc:WeeklyPlan || 
             ?type = sc:SeasonalPlan || ?type = sc:TourPlan || ?type = sc:TravelPlan)
      FILTER(strafter(str(?plan), "#") = "{q_local}" || strends(str(?plan), "/{q_local}"))
      
      OPTIONAL {{ 
        ?person sc:hasTravelPlan ?plan .
        OPTIONAL {{ ?person sc:hasName ?personName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:hasStartStation ?startStation . 
        OPTIONAL {{ ?startStation sc:hasName ?startStationName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:hasEndStation ?endStation . 
        OPTIONAL {{ ?endStation sc:hasName ?endStationName . }}
      }}
      OPTIONAL {{ 
        ?plan sc:usesTransportMode ?transportMode . 
        OPTIONAL {{ ?transportMode sc:hasName ?transportModeName . }}
      }}
      OPTIONAL {{ ?plan sc:hasStartTime ?startTime . }}
      OPTIONAL {{ ?plan sc:hasEndTime ?endTime . }}
      OPTIONAL {{ ?plan sc:hasDaysOfWeek ?daysOfWeek . }}
      OPTIONAL {{ ?plan sc:isActive ?isActive . }}
    }}
    LIMIT 1
    """
    res = execute_sparql_query(single_q)
    binds = res.get("results", {}).get("bindings", []) if res else []
    
    if binds:
        b = binds[0]
        return jsonify({
            "uri": b["plan"]["value"],
            "type": b.get("type", {}).get("value"),
            "person": b.get("person", {}).get("value"),
            "personName": b.get("personName", {}).get("value"),
            "startStation": b.get("startStation", {}).get("value"),
            "startStationName": b.get("startStationName", {}).get("value"),
            "endStation": b.get("endStation", {}).get("value"),
            "endStationName": b.get("endStationName", {}).get("value"),
            "transportMode": b.get("transportMode", {}).get("value"),
            "transportModeName": b.get("transportModeName", {}).get("value"),
            "startTime": b.get("startTime", {}).get("value"),
            "endTime": b.get("endTime", {}).get("value"),
            "daysOfWeek": b.get("daysOfWeek", {}).get("value"),
            "isActive": b.get("isActive", {}).get("value")
        })

    return jsonify({"error": "Not found"}), 404

@router.route('/', methods=['POST'])
def create_travel_plan():
    """
    POST /api/travel-plans/
    JSON body fields:
      - uri (optional) : full URI for the new individual
      - localname (optional) : local name to append to ontology base (used if uri not provided)
      - class (required) : class URI (SingleTripPlan, DailyCommutePlan, etc.)
      - person (optional) : person URI that has this plan
      - startStation (optional) : start station URI
      - endStation (optional) : end station URI
      - transportMode (optional) : transport mode URI
      - startTime (optional) : start time (xsd:time format)
      - endTime (optional) : end time
      - daysOfWeek (optional) : days string
      - isActive (optional) : boolean
    Example:
      {
        "localname": "AlicePlan",
        "class": "http://.../DailyCommutePlan",
        "person": "http://.../Alice",
        "startTime": "08:00:00",
        "daysOfWeek": "Monday, Tuesday, Wednesday, Thursday, Friday",
        "isActive": true
      }
    """
    data = request.get_json() or {}
    uri = data.get("uri")
    localname = data.get("localname")
    class_uri = data.get("class")
    person = data.get("person")
    start_station = data.get("startStation")
    end_station = data.get("endStation")
    transport_mode = data.get("transportMode")
    start_time = data.get("startTime")
    end_time = data.get("endTime")
    days_of_week = data.get("daysOfWeek")
    is_active = data.get("isActive")

    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    if not uri:
        if not localname:
            return jsonify({"error": "uri or localname required"}), 400
        uri = base_uri + localname

    if not class_uri:
        return jsonify({"error": "class required (e.g., SingleTripPlan, DailyCommutePlan)"}), 400

    triples = []
    triples.append(f"<{uri}> a <{class_uri}> .")

    # Object properties
    if person:
        triples.append(f"<{person}> <{base_uri}hasTravelPlan> <{uri}> .")
    
    if start_station:
        triples.append(f"<{uri}> <{base_uri}hasStartStation> <{start_station}> .")
    
    if end_station:
        triples.append(f"<{uri}> <{base_uri}hasEndStation> <{end_station}> .")
    
    if transport_mode:
        triples.append(f"<{uri}> <{base_uri}usesTransportMode> <{transport_mode}> .")

    # Data properties
    if start_time is not None:
        safe_time = start_time.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasStartTime> "{safe_time}"^^<http://www.w3.org/2001/XMLSchema#time> .')
    
    if end_time is not None:
        safe_time = end_time.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasEndTime> "{safe_time}"^^<http://www.w3.org/2001/XMLSchema#time> .')
    
    if days_of_week is not None:
        safe_days = days_of_week.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasDaysOfWeek> "{safe_days}" .')
    
    if is_active is not None:
        bool_val = "true" if is_active else "false"
        triples.append(f'<{uri}> <{base_uri}isActive> "{bool_val}"^^<http://www.w3.org/2001/XMLSchema#boolean> .')

    update_query = "INSERT DATA { \n" + "\n".join(triples) + "\n }"

    try:
        headers = {"Content-Type": "application/sparql-update"}
        resp = requests.post(FUSEKI_UPDATE, data=update_query.encode('utf-8'), headers=headers, timeout=10)
        if resp.status_code in (200, 201, 204):
            return jsonify({"ok": True, "uri": uri}), 201
        else:
            return jsonify({"error": "Fuseki update failed", "status": resp.status_code, "body": resp.text}), 500
    except Exception as e:
        return jsonify({"error": f"Update error: {str(e)}"}), 500


