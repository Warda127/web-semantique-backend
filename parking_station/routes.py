from flask import Blueprint, request, jsonify
import requests

router = Blueprint('parking_station', __name__)

# Fuseki configuration
FUSEKI_QUERY = "http://localhost:3030/smartcity/query"
FUSEKI_UPDATE = "http://localhost:3030/smartcity/update"


def execute_sparql_query(query):
    """Execute SPARQL SELECT query"""
    try:
        headers = {"Content-Type": "application/sparql-query", "Accept": "application/json"}
        resp = requests.post(FUSEKI_QUERY, data=query.encode('utf-8'), headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"SPARQL query error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Error executing SPARQL query: {e}")
        return None


@router.route('/', methods=['GET'])
def list_parking_stations():
    """
    GET /api/parking-stations/
    List all parking stations
    Optional params:
      - q : filter by name substring
      - type : filter by parking type (CarParkingStation, BikeParkingStation, EVChargingStation)
    """
    q = request.args.get('q', '').replace('"', '\\"')
    parking_type = request.args.get('type', '')

    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    # Build filter clauses
    name_filter = f'FILTER regex(str(?name), "{q}", "i")' if q else ""
    type_filter = ""
    if parking_type:
        type_filter = f"FILTER(?type = <{ns}{parking_type}>)"

    query = f"""
    PREFIX sc: <{ns}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?station ?type ?name ?capacity ?availableSpaces ?pricePerHour ?address ?latitude ?longitude ?operatingHours
    WHERE {{
      ?station a ?type .
      FILTER(?type = sc:CarParkingStation || ?type = sc:BikeParkingStation || ?type = sc:EVChargingStation)
      OPTIONAL {{ ?station sc:hasName ?name . }}
      OPTIONAL {{ ?station sc:hasCapacity ?capacity . }}
      OPTIONAL {{ ?station sc:hasAvailableSpaces ?availableSpaces . }}
      OPTIONAL {{ ?station sc:hasPricePerHour ?pricePerHour . }}
      OPTIONAL {{ ?station sc:hasAddress ?address . }}
      OPTIONAL {{ ?station sc:hasLatitude ?latitude . }}
      OPTIONAL {{ ?station sc:hasLongitude ?longitude . }}
      OPTIONAL {{ ?station sc:hasOperatingHours ?operatingHours . }}
      {name_filter}
      {type_filter}
    }}
    ORDER BY ?name
    """

    results = execute_sparql_query(query)
    bindings = results.get("results", {}).get("bindings", []) if results else []

    stations = []
    for b in bindings:
        stations.append({
            "uri": b["station"]["value"],
            "type": b.get("type", {}).get("value"),
            "name": b.get("name", {}).get("value"),
            "capacity": b.get("capacity", {}).get("value"),
            "availableSpaces": b.get("availableSpaces", {}).get("value"),
            "pricePerHour": b.get("pricePerHour", {}).get("value"),
            "address": b.get("address", {}).get("value"),
            "latitude": b.get("latitude", {}).get("value"),
            "longitude": b.get("longitude", {}).get("value"),
            "operatingHours": b.get("operatingHours", {}).get("value")
        })

    return jsonify({"stations": stations})


@router.route('/<path:localname>', methods=['GET'])
def get_parking_station(localname):
    """
    GET /api/parking-stations/<localname>
    Fetch a specific parking station by its localname
    """
    q_local = localname.replace('"', '\\"')
    ns = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    query = f"""
    PREFIX sc: <{ns}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?station ?type ?name ?capacity ?availableSpaces ?pricePerHour ?address ?latitude ?longitude ?operatingHours
    WHERE {{
      ?station a ?type .
      FILTER(?type = sc:CarParkingStation || ?type = sc:BikeParkingStation || ?type = sc:EVChargingStation)
      FILTER(strafter(str(?station), "#") = "{q_local}" || strends(str(?station), "/{q_local}"))

      OPTIONAL {{ ?station sc:hasName ?name . }}
      OPTIONAL {{ ?station sc:hasCapacity ?capacity . }}
      OPTIONAL {{ ?station sc:hasAvailableSpaces ?availableSpaces . }}
      OPTIONAL {{ ?station sc:hasPricePerHour ?pricePerHour . }}
      OPTIONAL {{ ?station sc:hasAddress ?address . }}
      OPTIONAL {{ ?station sc:hasLatitude ?latitude . }}
      OPTIONAL {{ ?station sc:hasLongitude ?longitude . }}
      OPTIONAL {{ ?station sc:hasOperatingHours ?operatingHours . }}
    }}
    LIMIT 1
    """

    res = execute_sparql_query(query)
    binds = res.get("results", {}).get("bindings", []) if res else []

    if binds:
        b = binds[0]
        return jsonify({
            "uri": b["station"]["value"],
            "type": b.get("type", {}).get("value"),
            "name": b.get("name", {}).get("value"),
            "capacity": b.get("capacity", {}).get("value"),
            "availableSpaces": b.get("availableSpaces", {}).get("value"),
            "pricePerHour": b.get("pricePerHour", {}).get("value"),
            "address": b.get("address", {}).get("value"),
            "latitude": b.get("latitude", {}).get("value"),
            "longitude": b.get("longitude", {}).get("value"),
            "operatingHours": b.get("operatingHours", {}).get("value")
        })

    return jsonify({"error": "Not found"}), 404


@router.route('/', methods=['POST'])
def create_parking_station():
    """
    POST /api/parking-stations/
    Create a new parking station
    JSON body fields:
      - localname (required) : local name for the parking station
      - type (required) : class type (CarParkingStation, BikeParkingStation, EVChargingStation)
      - name (optional) : human-readable name
      - capacity (optional) : total parking spaces
      - availableSpaces (optional) : currently available spaces
      - pricePerHour (optional) : price per hour
      - address (optional) : street address
      - latitude (optional) : GPS latitude
      - longitude (optional) : GPS longitude
      - operatingHours (optional) : e.g., "24/7" or "08:00-20:00"
    """
    data = request.get_json() or {}
    localname = data.get("localname")
    station_type = data.get("type")
    name = data.get("name")
    capacity = data.get("capacity")
    available_spaces = data.get("availableSpaces")
    price_per_hour = data.get("pricePerHour")
    address = data.get("address")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    operating_hours = data.get("operatingHours")

    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"

    if not localname:
        return jsonify({"error": "localname required"}), 400

    if not station_type:
        return jsonify({"error": "type required (CarParkingStation, BikeParkingStation, or EVChargingStation)"}), 400

    uri = base_uri + localname

    # Build INSERT DATA query
    triples = []
    triples.append(f"<{uri}> a <{base_uri}{station_type}> .")

    if name:
        safe_name = name.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasName> "{safe_name}" .')

    if capacity is not None:
        triples.append(f'<{uri}> <{base_uri}hasCapacity> "{capacity}"^^<http://www.w3.org/2001/XMLSchema#integer> .')

    if available_spaces is not None:
        triples.append(
            f'<{uri}> <{base_uri}hasAvailableSpaces> "{available_spaces}"^^<http://www.w3.org/2001/XMLSchema#integer> .')

    if price_per_hour is not None:
        triples.append(
            f'<{uri}> <{base_uri}hasPricePerHour> "{price_per_hour}"^^<http://www.w3.org/2001/XMLSchema#float> .')

    if address:
        safe_address = address.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasAddress> "{safe_address}" .')

    if latitude is not None:
        triples.append(f'<{uri}> <{base_uri}hasLatitude> "{latitude}"^^<http://www.w3.org/2001/XMLSchema#float> .')

    if longitude is not None:
        triples.append(f'<{uri}> <{base_uri}hasLongitude> "{longitude}"^^<http://www.w3.org/2001/XMLSchema#float> .')

    if operating_hours:
        safe_hours = operating_hours.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasOperatingHours> "{safe_hours}" .')

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


@router.route('/<path:localname>', methods=['PUT'])
def update_parking_station(localname):
    """
    PUT /api/parking-stations/<localname>
    Update parking station (typically available spaces)
    """
    data = request.get_json() or {}
    available_spaces = data.get("availableSpaces")

    if available_spaces is None:
        return jsonify({"error": "availableSpaces required"}), 400

    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
    uri = base_uri + localname

    # Delete old value and insert new one
    update_query = f"""
    PREFIX sc: <{base_uri}>

    DELETE {{
      <{uri}> sc:hasAvailableSpaces ?oldSpaces .
    }}
    INSERT {{
      <{uri}> sc:hasAvailableSpaces "{available_spaces}"^^<http://www.w3.org/2001/XMLSchema#integer> .
    }}
    WHERE {{
      OPTIONAL {{ <{uri}> sc:hasAvailableSpaces ?oldSpaces . }}
    }}
    """

    try:
        headers = {"Content-Type": "application/sparql-update"}
        resp = requests.post(FUSEKI_UPDATE, data=update_query.encode('utf-8'), headers=headers, timeout=10)
        if resp.status_code in (200, 201, 204):
            return jsonify({"ok": True, "uri": uri, "availableSpaces": available_spaces})
        else:
            return jsonify({"error": "Fuseki update failed", "status": resp.status_code}), 500
    except Exception as e:
        return jsonify({"error": f"Update error: {str(e)}"}), 500


@router.route('/<path:localname>', methods=['DELETE'])
def delete_parking_station(localname):
    """
    DELETE /api/parking-stations/<localname>
    Remove a parking station from the ontology
    """
    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
    uri = base_uri + localname

    update_query = f"""
    DELETE WHERE {{
      <{uri}> ?p ?o .
    }}
    """

    try:
        headers = {"Content-Type": "application/sparql-update"}
        resp = requests.post(FUSEKI_UPDATE, data=update_query.encode('utf-8'), headers=headers, timeout=10)
        if resp.status_code in (200, 201, 204):
            return jsonify({"ok": True, "message": "Parking station deleted"})
        else:
            return jsonify({"error": "Fuseki delete failed", "status": resp.status_code}), 500
    except Exception as e:
        return jsonify({"error": f"Delete error: {str(e)}"}), 500