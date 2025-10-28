# Notes: activate venv and install deps (run inside project folder)
#   cd "c:\Users\Mon Pc\Desktop\web-semantique-backend"
#   python -m venv venv      # if venv not created yet
#   # Activate (Windows cmd)
#   venv\Scripts\activate
#   # or PowerShell:
#   .\venv\Scripts\Activate.ps1
#   # Install dependencies:
#   pip install -r requirements.txt
#   # Alternatively:
#   pip install Flask SPARQLWrapper rdflib requests fastapi uvicorn
import os

from flask import Flask, request, jsonify
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

from ai_sparql_transformer import sparql_transformer
from transport_mode.routes import router as transport_mode_router
from travel_plan.routes import router as travel_plan_router
from parking_station.routes import router as parking_station_router
from ontology_search.routes import router as ontology_search_router
from transport_recommendation.routes import router as transport_recommendation_router
from custom_query.routes import router as custom_query_router
from health_monitoring.routes import router as health_monitoring_router
from sparql_service import SPARQLQueryService, get_sparql_service

app = Flask(__name__)
FUSEKI_ENDPOINT = os.getenv('FUSEKI_QUERY', "http://localhost:3030/smartcity/query")
FUSEKI_UPDATE = os.getenv('FUSEKI_UPDATE', "http://localhost:3030/smartcity/update")


def execute_sparql_query(query):
    """Exécute une requête SPARQL sur Fuseki"""
    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"Erreur SPARQL: {e} (endpoint={FUSEKI_ENDPOINT})")
        return None
# Middleware CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
 # transport mode routes
# Register transport-mode blueprint so TransportMode endpoints are available under /api/transport-modes
app.register_blueprint(transport_mode_router, url_prefix='/api/transport-modes')

# travel plan routes
# Register travel-plan blueprint so TravelPlan endpoints are available under /api/travel-plans
app.register_blueprint(travel_plan_router, url_prefix='/api/travel-plans')

app.register_blueprint(parking_station_router, url_prefix='/api/parking-stations')

 
# Configuration Fuseki - Use environment variable set in docker-compose.yml
# The environment variable FUSEKI_QUERY is already set at the top of the file
# ontology search routes
# Register ontology-search blueprint for concept search and class exploration
app.register_blueprint(ontology_search_router, url_prefix='/api')

# transport recommendation routes
# Register transport-recommendation blueprint for intelligent transport suggestions
app.register_blueprint(transport_recommendation_router, url_prefix='/api')

# custom query routes
# Register custom-query blueprint for SPARQL query execution
app.register_blueprint(custom_query_router, url_prefix='/api')

# health monitoring routes
# Register health-monitoring blueprint for system status monitoring
app.register_blueprint(health_monitoring_router, url_prefix='/api')
 
# Configuration Fuseki
# Use the dataset name shown in the Fuseki UI. Your UI shows dataset "smartcity",
# so use the dataset SPARQL endpoint /{dataset}/query (or /{dataset}/sparql on some Fuseki versions).
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"
FUSEKI_UPDATE_ENDPOINT = "http://localhost:3030/smartcity/update"

# Initialize enhanced SPARQL service
sparql_service = SPARQLQueryService(
    fuseki_endpoint=FUSEKI_ENDPOINT,
    fuseki_update_endpoint=FUSEKI_UPDATE_ENDPOINT,
    default_timeout=30,
    max_retries=3
)

def execute_sparql_query(query):
    """
    Enhanced SPARQL query execution with validation and timeout capabilities.
    Maintains backward compatibility with existing code.
    """
    result = sparql_service.execute_query_with_validation(query)
    
    if result.success:
        return result.data
    else:
        print(f"Enhanced SPARQL Error: {result.error} (endpoint={FUSEKI_ENDPOINT})")
        return None

# SUPPRIMEZ la route index qui utilise le template HTML
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/api/persons')
def get_persons():
    """API pour récupérer toutes les personnes"""
    query = """
    PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT ?person ?name ?type
    WHERE {
        ?person rdf:type :Person .
        OPTIONAL { ?person :hasName ?name . }
        OPTIONAL {
            ?person rdf:type ?type .
            FILTER(?type != :Person)
        }
    }
    """
    
    results = execute_sparql_query(query)
    
    if results:
        persons = []
        for result in results["results"]["bindings"]:
            person = {
                "uri": result["person"]["value"],
                "name": result.get("name", {}).get("value", "Sans nom"),
                "type": result.get("type", {}).get("value", "Person")
            }
            persons.append(person)
        
        return jsonify(persons)
    else:
        return jsonify({"error": "Erreur lors de la requête"}), 500

@app.route('/api/search/persons')
def search_persons():
    """Recherche de personnes par nom"""
    search_term = request.args.get('q', '')
    
    query = """
    PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT ?person ?name ?type
    WHERE {
        ?person rdf:type :Person .
        ?person :hasName ?name .
        FILTER regex(?name, "%s", "i")
        OPTIONAL {
            ?person rdf:type ?type .
            FILTER(?type != :Person)
        }
    }
    """ % search_term
    
    results = execute_sparql_query(query)
    
    if results:
        persons = []
        for result in results["results"]["bindings"]:
            person = {
                "uri": result["person"]["value"],
                "name": result.get("name", {}).get("value", "Sans nom"),
                "type": result.get("type", {}).get("value", "Person")
            }
            persons.append(person)
        
        return jsonify(persons)
    else:
        return jsonify({"error": "Erreur lors de la recherche"}), 500



@app.route('/api/search/stations')
def search_stations():
    """Recherche de stations par nom"""
    search_term = request.args.get('q', '')

    query = """
    PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?station ?name ?type ?location ?capacity
    WHERE {
        ?station rdf:type :Station .
        ?station :hasName ?name .
        FILTER regex(?name, "%s", "i")
        OPTIONAL { ?station rdf:type ?type . FILTER(?type != :Station) }
        OPTIONAL { ?station :hasLocation ?location . }
        OPTIONAL { ?station :hasCapacity ?capacity . }
    }
    """ % search_term

    results = execute_sparql_query(query)

    if results:
        stations = []
        for result in results["results"]["bindings"]:
            station = {
                "uri": result["station"]["value"],
                "name": result.get("name", {}).get("value", "Sans nom"),
                "type": result.get("type", {}).get("value", "Station"),
                "location": result.get("location", {}).get("value", ""),
                "capacity": result.get("capacity", {}).get("value", "")
            }
            stations.append(station)
        return jsonify(stations)
    else:
        return jsonify({"error": "Erreur lors de la recherche"}), 500




@app.route('/api/ai/query', methods=['POST'])
def ai_query():
    """Endpoint pour les questions en langage naturel"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({"error": "Aucune question fournie"}), 400
        
        # Générer la requête SPARQL avec l'IA
        sparql_query = sparql_transformer.generate_sparql(question)
        
        # Exécuter la requête avec le service amélioré
        result = sparql_service.execute_query_with_validation(sparql_query)
        
        if result.success:
            persons = []
            for binding in result.data["results"]["bindings"]:
                person = {
                    "uri": binding["person"]["value"],
                    "name": binding.get("name", {}).get("value", "Sans nom"),
                    "type": binding.get("type", {}).get("value", "Person")
                }
                persons.append(person)
            
            return jsonify({
                "question": question,
                "sparql_query": sparql_query,
                "results": persons,
                "execution_time": result.execution_time,
                "bindings_count": result.bindings_count
            })
        else:
            return jsonify({
                "error": f"Erreur lors de l'exécution de la requête: {result.error}",
                "execution_time": result.execution_time
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"Erreur IA: {str(e)}"}), 500



@app.route('/api/sparql/validate', methods=['POST'])
def validate_sparql():
    """Endpoint to validate SPARQL queries without executing them"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Validate the query
        validation = sparql_service.validate_query_syntax(query)
        
        # Get query statistics
        stats = sparql_service.get_query_statistics(query)
        
        return jsonify({
            "validation": {
                "is_valid": validation.is_valid,
                "error_message": validation.error_message,
                "suggestions": validation.suggestions,
                "query_type": validation.query_type.value if validation.query_type else None
            },
            "statistics": stats
        })
        
    except Exception as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 500

if __name__ == '__main__':
    # CRITICAL: Bind to 0.0.0.0 to accept connections from outside the container
    app.run(host='0.0.0.0', port=5000, debug=True)
