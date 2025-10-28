from flask import Blueprint, request, jsonify
import requests
import os
import re

router = Blueprint('parking_station', __name__)

FUSEKI_QUERY = os.getenv('FUSEKI_QUERY', 'http://localhost:3030/smartcity/query')
FUSEKI_UPDATE = os.getenv('FUSEKI_UPDATE', 'http://localhost:3030/smartcity/update')

def execute_sparql_query(query, expect_json=True):
    """Exécute une requête SPARQL SELECT/ASK. Lève une exception en cas d'erreur."""
    try:
        headers = {"Content-Type": "application/sparql-query", "Accept": "application/json"}
        resp = requests.post(FUSEKI_QUERY, data=query.encode('utf-8'), headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json() if expect_json else resp.text
    except Exception as e:
        raise RuntimeError(f"SPARQL query failed: {e}")

def safe_localname(name):
    """Autorise seulement un localname simple pour éviter injection / caractères dangereux."""
    if not name or not re.match(r'^[A-Za-z0-9_\-]+$', name):
        return None
    return name

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
    data = request.get_json() or {}
    localname = data.get("localname")
    station_type = data.get("type")
    name = data.get("name")

    # validation simple
    if not safe_localname(localname):
        return jsonify({"error": "invalid localname"}), 400
    if station_type not in ("CarParkingStation", "BikeParkingStation", "EVChargingStation"):
        return jsonify({"error": "invalid type"}), 400

    # cast numériques si fournis
    capacity = data.get("capacity")
    available_spaces = data.get("availableSpaces")
    price_per_hour = data.get("pricePerHour")
    try:
        capacity = int(capacity) if capacity is not None else None
        available_spaces = int(available_spaces) if available_spaces is not None else None
        price_per_hour = float(price_per_hour) if price_per_hour is not None else None
    except (ValueError, TypeError):
        return jsonify({"error": "numeric fields must be numbers"}), 400

    if capacity is not None and available_spaces is not None and available_spaces > capacity:
        return jsonify({"error": "availableSpaces cannot exceed capacity"}), 400

    base_uri = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
    uri = base_uri + localname

    triples = [f"<{uri}> a <{base_uri}{station_type}> ."]
    if name:
        safe_name = name.replace('"', '\\"')
        triples.append(f'<{uri}> <{base_uri}hasName> "{safe_name}" .')
    if capacity is not None:
        triples.append(f'<{uri}> <{base_uri}hasCapacity> "{capacity}"^^<http://www.w3.org/2001/XMLSchema#integer> .')
    if available_spaces is not None:
        triples.append(f'<{uri}> <{base_uri}hasAvailableSpaces> "{available_spaces}"^^<http://www.w3.org/2001/XMLSchema#integer> .')
    if price_per_hour is not None:
        triples.append(f'<{uri}> <{base_uri}hasPricePerHour> "{price_per_hour}"^^<http://www.w3.org/2001/XMLSchema#float> .')

    update_query = "INSERT DATA { \n" + "\n".join(triples) + "\n }"
    try:
        headers = {"Content-Type": "application/sparql-update"}
        resp = requests.post(FUSEKI_UPDATE, data=update_query.encode('utf-8'), headers=headers, timeout=10)
        resp.raise_for_status()
        return jsonify({"ok": True, "uri": uri}), 201
    except Exception as e:
        return jsonify({"error": f"Fuseki update failed: {e}"}), 500

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