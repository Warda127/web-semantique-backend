from flask import Flask, request, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
from ai_sparql_transformer import sparql_transformer

app = Flask(__name__)

# Middleware CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configuration Fuseki
FUSEKI_ENDPOINT = "http://localhost:3030/semantiqueweb/sparql"

def execute_sparql_query(query):
    """Exécute une requête SPARQL sur Fuseki"""
    sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"Erreur SPARQL: {e}")
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
        
        # Exécuter la requête
        results = execute_sparql_query(sparql_query)
        
        if results:
            persons = []
            for result in results["results"]["bindings"]:
                person = {
                    "uri": result["person"]["value"],
                    "name": result.get("name", {}).get("value", "Sans nom"),
                    "type": result.get("type", {}).get("value", "Person")
                }
                persons.append(person)
            
            return jsonify({
                "question": question,
                "sparql_query": sparql_query,
                "results": persons
            })
        else:
            return jsonify({"error": "Erreur lors de l'exécution de la requête"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Erreur IA: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)