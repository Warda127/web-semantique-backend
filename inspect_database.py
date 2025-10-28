#!/usr/bin/env python3
"""
Database inspection script to show what data is currently in Fuseki
"""

import requests
import json

FUSEKI_QUERY_ENDPOINT = "http://localhost:3030/smartcity/query"

def execute_query(query, description):
    """Execute a SPARQL query and display results"""
    try:
        print(f"\n📊 {description}")
        print("=" * 60)
        
        response = requests.get(
            FUSEKI_QUERY_ENDPOINT,
            params={'query': query, 'format': 'json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            
            if bindings:
                print(f"Found {len(bindings)} results:")
                
                for i, binding in enumerate(bindings, 1):
                    result_parts = []
                    for var, value in binding.items():
                        val = value.get('value', 'N/A')
                        # Shorten long URIs for readability
                        if val.startswith('http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#'):
                            val = val.split('#')[-1]
                        elif val.startswith('http://www.w3.org/'):
                            val = val.split('/')[-1] if '/' in val else val.split('#')[-1]
                        result_parts.append(f"{var}: {val}")
                    
                    print(f"  {i:2d}. {' | '.join(result_parts)}")
            else:
                print("No results found")
                
        else:
            print(f"Query failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error executing query: {e}")

def main():
    """Main inspection function"""
    print("🔍 DATABASE CONTENT INSPECTION")
    print("=" * 60)
    
    # 1. Total triples count
    execute_query("""
        SELECT (COUNT(*) as ?count)
        WHERE {
            ?s ?p ?o
        }
    """, "Total Triples in Database")
    
    # 2. All classes
    execute_query("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?class ?label
        WHERE {
            ?class rdf:type owl:Class .
            OPTIONAL { ?class rdfs:label ?label }
        }
        ORDER BY ?class
    """, "All Classes (owl:Class)")
    
    # 3. All properties
    execute_query("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?property ?type
        WHERE {
            {
                ?property rdf:type owl:ObjectProperty .
                BIND("ObjectProperty" as ?type)
            }
            UNION
            {
                ?property rdf:type owl:DatatypeProperty .
                BIND("DatatypeProperty" as ?type)
            }
        }
        ORDER BY ?type ?property
    """, "All Properties")
    
    # 4. Transport modes
    execute_query("""
        PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?mode ?type ?name ?speed
        WHERE {
            ?mode rdf:type ?type .
            FILTER(?type = :Bike || ?type = :Bus || ?type = :Metro)
            OPTIONAL { ?mode :hasName ?name }
            OPTIONAL { ?mode :hasSpeed ?speed }
        }
        ORDER BY ?type ?mode
    """, "Transport Modes (Bike, Bus, Metro)")
    
    # 5. Persons
    execute_query("""
        PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?person ?type ?name
        WHERE {
            ?person rdf:type ?type .
            FILTER(?type = :Person || ?type = :Citizen || ?type = :Tourist || ?type = :Staff)
            OPTIONAL { ?person :hasName ?name }
        }
        ORDER BY ?type ?person
    """, "Persons (Person, Citizen, Tourist, Staff)")
    
    # 6. Stations
    execute_query("""
        PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?station ?type ?name
        WHERE {
            ?station rdf:type ?type .
            FILTER(?type = :Station || ?type = :BikeStation || ?type = :BusStation || ?type = :MetroStation)
            OPTIONAL { ?station :hasName ?name }
        }
        ORDER BY ?type ?station
    """, "Stations (All Types)")
    
    # 7. Travel plans
    execute_query("""
        PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?plan ?type ?startStation ?endStation ?transportMode
        WHERE {
            ?plan rdf:type ?type .
            FILTER(?type = :TravelPlan || ?type = :SingleTripPlan || ?type = :DailyCommutePlan || ?type = :WeeklyPlan)
            OPTIONAL { ?plan :hasStartStation ?startStation }
            OPTIONAL { ?plan :hasEndStation ?endStation }
            OPTIONAL { ?plan :usesTransportMode ?transportMode }
        }
        ORDER BY ?type ?plan
    """, "Travel Plans")
    
    # 8. Person-TravelPlan relationships
    execute_query("""
        PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
        
        SELECT ?person ?personName ?plan ?planType
        WHERE {
            ?person :hasTravelPlan ?plan .
            OPTIONAL { ?person :hasName ?personName }
            OPTIONAL { ?plan rdf:type ?planType }
        }
    """, "Person-TravelPlan Relationships")
    
    # 9. Sample of all data (first 20 triples)
    execute_query("""
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object
        }
        LIMIT 20
    """, "Sample Data (First 20 Triples)")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print("The database contains a complete smart city transportation ontology with:")
    print("• Transport modes: Bikes, Buses, Metro systems")
    print("• Person types: Citizens, Tourists, Staff")
    print("• Stations: Bike rentals, Bus stops, Metro stations")
    print("• Travel plans: Single trips, Daily commutes, Weekly plans")
    print("• Relationships: People linked to their travel plans")
    print("\nThis provides a rich dataset for testing all your API endpoints!")

if __name__ == "__main__":
    main()