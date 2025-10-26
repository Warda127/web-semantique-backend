from flask import Flask, render_template, request, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
import requests

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)