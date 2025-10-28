from flask import Blueprint, jsonify, request
try:
    from SPARQLWrapper import SPARQLWrapper, JSON
except ImportError:
    # Fallback for testing without SPARQLWrapper
    class SPARQLWrapper:
        def __init__(self, endpoint): pass
        def setQuery(self, query): pass
        def setReturnFormat(self, format): pass
        def query(self): 
            class MockResult:
                def convert(self): return {"results": {"bindings": []}}
            return MockResult()
    JSON = "json"

from sparql_service import get_sparql_service

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

router = Blueprint('transport_mode', __name__)

# Fuseki endpoints (adjust dataset name if needed)
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"
FUSEKI_UPDATE = "http://localhost:3030/smartcity/update"

# Get enhanced SPARQL service instance
sparql_service = get_sparql_service(FUSEKI_ENDPOINT)

def execute_sparql_query(query):
    """Enhanced SPARQL query execution with validation and timeout"""
    result = sparql_service.execute_query_with_validation(query)
    
    if result.success:
        return result.data
    else:
        print(f"[transport_mode] Enhanced SPARQL error: {result.error} (endpoint={FUSEKI_ENDPOINT})")
        return None

@router.route('/', methods=['GET'])
def list_transport_modes():
    """
    GET /api/transport-modes/
    Primary query: select individuals of classes Bike, Bus, Metro (your ontology uses these class names).
    Optional params:
      - q : filter by name substring
      - debug=1 : include diagnostic info
    """
    q = request.args.get('q', '').replace('"', '\\"')
    debug = request.args.get('debug', '0') == '1'

    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
    filter_clause = f'FILTER regex(str(?name), "{q}", "i")' if q else ""

    # Primary SPARQL: match explicit classes Bike, Bus, Metro (as in your Fuseki query)
    primary_q = f"""
    PREFIX sc: <{ns}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?mode ?type ?name ?speed
    WHERE {{
      ?mode a ?type .
      FILTER(?type = sc:Bike || ?type = sc:Bus || ?type = sc:Metro)
      OPTIONAL {{ ?mode sc:hasName ?name . }}
      OPTIONAL {{ ?mode sc:hasSpeed ?speed . }}
      {filter_clause}
    }}
    ORDER BY ?mode
    """
    print("[transport_mode] Running primary Bike/Bus/Metro query")
    print(primary_q)
    results = execute_sparql_query(primary_q)
    bindings = results.get("results", {}).get("bindings", []) if results else []

    tried_prefixes = []
    used_class_detection = None

    if bindings:
        modes = []
        for b in bindings:
            modes.append({
                "uri": b["mode"]["value"],
                "type": b.get("type", {}).get("value"),
                "name": b.get("name", {}).get("value"),
                "speed": b.get("speed", {}).get("value")
            })
        resp = {"modes": modes}
        return jsonify(resp)

    # fallback: try previous candidate-prefix based queries and detection (preserve existing behavior)
    # record tried prefixes for debug
    base_uri = ns.rstrip('#/')
    candidate_prefixes = [base_uri + "#", base_uri + "/", base_uri]
    tried_prefixes.extend(candidate_prefixes)

    # Try the older TransportMode-based attempts (in case some datasets use a TransportMode class)
    sparql_template = """
    PREFIX : <{prefix}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?mode ?name ?speed
    WHERE {{
        ?mode rdf:type :TransportMode .
        OPTIONAL {{ ?mode :hasName ?name . }}
        OPTIONAL {{ ?mode :hasSpeed ?speed . }}
        {filter}
    }}
    """
    for prefix in candidate_prefixes:
        query = sparql_template.format(prefix=prefix, filter=filter_clause)
        print(f"[transport_mode] Trying TransportMode prefix: {prefix}")
        res = execute_sparql_query(query)
        binds = res.get("results", {}).get("bindings", []) if res else []
        if binds:
            modes = []
            for b in binds:
                modes.append({
                    "uri": b["mode"]["value"],
                    "name": b.get("name", {}).get("value"),
                    "speed": b.get("speed", {}).get("value")
                })
            resp = {"modes": modes, "_used_prefix": prefix}
            return jsonify(resp)

    # Detect classes and try per-class instance queries (exclude RDF/OWL schema classes)
    detect_q = """
    SELECT DISTINCT ?class WHERE {
      ?s a ?class .
    } LIMIT 200
    """
    det = execute_sparql_query(detect_q)
    classes = (det.get("results", {}).get("bindings", []) if det else [])
    classes_list = [c["class"]["value"] for c in classes]

    def is_system_class(u):
        return u.startswith("http://www.w3.org/2000/01/rdf-schema") or u.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns") or u.startswith("http://www.w3.org/2002/07/owl#")

    collected = {}
    used_classes = []
    for class_uri in classes_list:
        if is_system_class(class_uri):
            continue
        # try instances for this class
        if '#' in class_uri:
            base = class_uri.rsplit('#', 1)[0] + '#'
        else:
            base = class_uri.rsplit('/', 1)[0] + '/'
        hasName_uri = base + "hasName"
        hasSpeed_uri = base + "hasSpeed"
        inst_q = f"""
        SELECT ?mode ?name ?speed WHERE {{
          ?mode a <{class_uri}> .
          OPTIONAL {{ ?mode <{hasName_uri}> ?name . }}
          OPTIONAL {{ ?mode <{hasSpeed_uri}> ?speed . }}
          {filter_clause}
        }} LIMIT 100
        """
        inst_res = execute_sparql_query(inst_q)
        binds = inst_res.get("results", {}).get("bindings", []) if inst_res else []
        if binds:
            used_classes.append(class_uri)
            for b in binds:
                uri = b["mode"]["value"]
                if uri not in collected:
                    collected[uri] = {
                        "uri": uri,
                        "type": class_uri,
                        "name": b.get("name", {}).get("value"),
                        "speed": b.get("speed", {}).get("value")
                    }

    if collected:
        modes = list(collected.values())
        resp = {"modes": modes}
        if used_classes:
            resp["_detected_class"] = used_classes[0]
        return jsonify(resp)

    # still nothing: return empty with debug info if requested
    resp = {"modes": []}
    if debug:
        resp["_tried_prefixes"] = tried_prefixes
        resp["_classes_sample"] = classes_list
    return jsonify(resp), 200

@router.route('/<path:localname>', methods=['GET'])
def get_transport_mode(localname):
    """
    Try to find an instance matching localname among Bike/Bus/Metro first,
    then fallback to other detection strategies.
    """
    q_local = localname.replace('"', '\\"')
    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    # try Bike/Bus/Metro specific lookup
    single_q = f"""
    PREFIX sc: <{ns}>
    SELECT ?mode ?type ?name ?speed WHERE {{
      ?mode a ?type .
      FILTER(?type = sc:Bike || ?type = sc:Bus || ?type = sc:Metro)
      OPTIONAL {{ ?mode sc:hasName ?name . }}
      OPTIONAL {{ ?mode sc:hasSpeed ?speed . }}
      FILTER(strafter(str(?mode), "{q_local}") = "{q_local}")
    }} LIMIT 1
    """
    res = execute_sparql_query(single_q)
    binds = res.get("results", {}).get("bindings", []) if res else []
    if binds:
        b = binds[0]
        return jsonify({
            "uri": b["mode"]["value"],
            "type": b.get("type", {}).get("value"),
            "name": b.get("name", {}).get("value"),
            "speed": b.get("speed", {}).get("value")
        })

    # fallback: try other classes (existing logic)
    # reuse detection approach from list_transport_modes to search other classes
    det = execute_sparql_query("""
    SELECT DISTINCT ?class WHERE {
      ?s a ?class .
    } LIMIT 200
    """)
    classes = (det.get("results", {}).get("bindings", []) if det else [])
    for c in classes:
        class_uri = c["class"]["value"]
        if class_uri.startswith("http://www.w3.org/2000/01/rdf-schema") or class_uri.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns") or class_uri.startswith("http://www.w3.org/2002/07/owl#"):
            continue
        if '#' in class_uri:
            base = class_uri.rsplit('#', 1)[0] + '#'
        else:
            base = class_uri.rsplit('/', 1)[0] + '/'
        hasName_uri = base + "hasName"
        hasSpeed_uri = base + "hasSpeed"
        inst_q = f"""
        SELECT ?mode ?name ?speed WHERE {{
          ?mode a <{class_uri}> .
          OPTIONAL {{ ?mode <{hasName_uri}> ?name . }}
          OPTIONAL {{ ?mode <{hasSpeed_uri}> ?speed . }}
          FILTER(strafter(str(?mode), "{q_local}") = "{q_local}")
        }} LIMIT 1
        """
        res2 = execute_sparql_query(inst_q)
        binds2 = res2.get("results", {}).get("bindings", []) if res2 else []
        if binds2:
            b = binds2[0]
            return jsonify({
                "uri": b["mode"]["value"],
                "type": class_uri,
                "name": b.get("name", {}).get("value"),
                "speed": b.get("speed", {}).get("value")
            })

    return jsonify({"error": "Not found"}), 404

@router.route('/', methods=['POST'])
def create_transport_mode():
    """
    POST /api/transport-modes/
    JSON body fields:
      - uri (optional) : full URI for the new individual
      - localname (optional) : local name to append to ontology base (used if uri not provided)
      - class (optional) : class URI to use for rdf:type (if omitted defaults to NamedIndividual)
      - name (optional) : value for hasName
      - speed (optional) : value for hasSpeed
    Example:
      {"localname":"BikeX","class":"http://...#Bike","name":"Bike X","speed":"12"}
    """
    data = request.get_json() or {}
    uri = data.get("uri")
    localname = data.get("localname")
    class_uri = data.get("class")
    name = data.get("name")
    speed = data.get("speed")

    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    if not uri:
        if not localname:
            return jsonify({"error": "uri or localname required"}), 400
        uri = base_uri + localname

    triples = []
    if class_uri:
        triples.append(f"<{uri}> a <{class_uri}> .")
    else:
        triples.append(f"<{uri}> a <http://www.w3.org/2002/07/owl#NamedIndividual> .")

    prop_base = base_uri
    hasName_uri = prop_base + "hasName"
    hasSpeed_uri = prop_base + "hasSpeed"

    if name is not None:
        safe_name = name.replace('"', '\\"')
        triples.append(f'<{uri}> <{hasName_uri}> "{safe_name}" .')

    if speed is not None:
        safe_speed = str(speed).replace('"', '\\"')
        triples.append(f'<{uri}> <{hasSpeed_uri}> "{safe_speed}" .')

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
