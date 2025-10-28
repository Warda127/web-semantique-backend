#!/usr/bin/env python3
"""
Database initialization script for loading ontology data into Fuseki.
This script loads the ontology file and creates sample data for testing.
"""

import requests
import time
import sys
from pathlib import Path

# Fuseki configuration
FUSEKI_UPDATE_ENDPOINT = "http://localhost:3030/smartcity/update"
FUSEKI_QUERY_ENDPOINT = "http://localhost:3030/smartcity/query"
ONTOLOGY_FILE = "ontologie/WebSemEsprit (1).rdf"

def check_fuseki_connection():
    """Check if Fuseki server is running"""
    try:
        response = requests.get(FUSEKI_QUERY_ENDPOINT + "?query=ASK{?s ?p ?o}", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Fuseki connection failed: {e}")
        return False

def load_ontology_file():
    """Load the RDF ontology file into Fuseki"""
    ontology_path = Path(ONTOLOGY_FILE)
    
    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ONTOLOGY_FILE}")
        return False
    
    try:
        print(f"📁 Loading ontology file: {ONTOLOGY_FILE}")
        
        # Read the RDF file
        with open(ontology_path, 'r', encoding='utf-8') as f:
            rdf_content = f.read()
        
        # Upload to Fuseki using SPARQL UPDATE
        headers = {
            'Content-Type': 'application/rdf+xml',
        }
        
        # Use POST to upload the RDF data
        response = requests.post(
            FUSEKI_UPDATE_ENDPOINT,
            data=rdf_content,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            print("✅ Ontology file loaded successfully!")
            return True
        else:
            print(f"❌ Failed to load ontology: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading ontology file: {e}")
        return False

def create_sample_data():
    """Create sample data for testing the system"""
    
    sample_data = """
    PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    
    INSERT DATA {
        # Transport Mode Classes
        :Bike rdf:type owl:Class ;
              rdfs:label "Bike" ;
              rdfs:comment "Bicycle transport mode" .
              
        :Bus rdf:type owl:Class ;
             rdfs:label "Bus" ;
             rdfs:comment "Bus transport mode" .
             
        :Metro rdf:type owl:Class ;
               rdfs:label "Metro" ;
               rdfs:comment "Metro/Subway transport mode" .
        
        # Person Classes
        :Person rdf:type owl:Class ;
                rdfs:label "Person" ;
                rdfs:comment "A person in the smart city" .
                
        :Citizen rdf:type owl:Class ;
                 rdfs:subClassOf :Person ;
                 rdfs:label "Citizen" ;
                 rdfs:comment "A citizen of the smart city" .
                 
        :Tourist rdf:type owl:Class ;
                 rdfs:subClassOf :Person ;
                 rdfs:label "Tourist" ;
                 rdfs:comment "A tourist visiting the smart city" .
                 
        :Staff rdf:type owl:Class ;
               rdfs:subClassOf :Person ;
               rdfs:label "Staff" ;
               rdfs:comment "Staff member working in the smart city" .
        
        # Station Classes
        :Station rdf:type owl:Class ;
                 rdfs:label "Station" ;
                 rdfs:comment "Transport station" .
                 
        :BikeStation rdf:type owl:Class ;
                     rdfs:subClassOf :Station ;
                     rdfs:label "Bike Station" .
                     
        :BusStation rdf:type owl:Class ;
                    rdfs:subClassOf :Station ;
                    rdfs:label "Bus Station" .
                    
        :MetroStation rdf:type owl:Class ;
                      rdfs:subClassOf :Station ;
                      rdfs:label "Metro Station" .
        
        # Travel Plan Classes
        :TravelPlan rdf:type owl:Class ;
                    rdfs:label "Travel Plan" ;
                    rdfs:comment "A travel plan for transportation" .
                    
        :SingleTripPlan rdf:type owl:Class ;
                        rdfs:subClassOf :TravelPlan ;
                        rdfs:label "Single Trip Plan" .
                        
        :DailyCommutePlan rdf:type owl:Class ;
                          rdfs:subClassOf :TravelPlan ;
                          rdfs:label "Daily Commute Plan" .
                          
        :WeeklyPlan rdf:type owl:Class ;
                    rdfs:subClassOf :TravelPlan ;
                    rdfs:label "Weekly Plan" .
        
        # Properties
        :hasName rdf:type owl:DatatypeProperty ;
                 rdfs:label "has name" ;
                 rdfs:domain owl:Thing ;
                 rdfs:range rdfs:Literal .
                 
        :hasSpeed rdf:type owl:DatatypeProperty ;
                  rdfs:label "has speed" ;
                  rdfs:domain :TransportMode ;
                  rdfs:range rdfs:Literal .
                  
        :hasTravelPlan rdf:type owl:ObjectProperty ;
                       rdfs:label "has travel plan" ;
                       rdfs:domain :Person ;
                       rdfs:range :TravelPlan .
                       
        :hasStartStation rdf:type owl:ObjectProperty ;
                         rdfs:label "has start station" ;
                         rdfs:domain :TravelPlan ;
                         rdfs:range :Station .
                         
        :hasEndStation rdf:type owl:ObjectProperty ;
                       rdfs:label "has end station" ;
                       rdfs:domain :TravelPlan ;
                       rdfs:range :Station .
                       
        :usesTransportMode rdf:type owl:ObjectProperty ;
                           rdfs:label "uses transport mode" ;
                           rdfs:domain :TravelPlan ;
                           rdfs:range owl:Thing .
        
        # Sample Individuals
        
        # Transport Mode Instances
        :CityBike rdf:type :Bike ;
                  :hasName "City Bike" ;
                  :hasSpeed "15" .
                  
        :ElectricBike rdf:type :Bike ;
                      :hasName "Electric Bike" ;
                      :hasSpeed "25" .
                      
        :CityBus rdf:type :Bus ;
                 :hasName "City Bus" ;
                 :hasSpeed "40" .
                 
        :ExpressBus rdf:type :Bus ;
                    :hasName "Express Bus" ;
                    :hasSpeed "60" .
                    
        :MetroLine1 rdf:type :Metro ;
                    :hasName "Metro Line 1" ;
                    :hasSpeed "80" .
                    
        :MetroLine2 rdf:type :Metro ;
                    :hasName "Metro Line 2" ;
                    :hasSpeed "80" .
        
        # Station Instances
        :CentralStation rdf:type :MetroStation ;
                        :hasName "Central Station" .
                        
        :UniversityStation rdf:type :MetroStation ;
                           :hasName "University Station" .
                           
        :ParkBusStop rdf:type :BusStation ;
                     :hasName "Park Bus Stop" .
                     
        :MallBusStop rdf:type :BusStation ;
                     :hasName "Mall Bus Stop" .
                     
        :BikeRental1 rdf:type :BikeStation ;
                     :hasName "Bike Rental Point 1" .
                     
        :BikeRental2 rdf:type :BikeStation ;
                     :hasName "Bike Rental Point 2" .
        
        # Person Instances
        :Alice rdf:type :Citizen ;
               :hasName "Alice Johnson" .
               
        :Bob rdf:type :Tourist ;
             :hasName "Bob Smith" .
             
        :Carol rdf:type :Staff ;
              :hasName "Carol Davis" .
              
        :David rdf:type :Citizen ;
              :hasName "David Wilson" .
        
        # Travel Plan Instances
        :AliceCommute rdf:type :DailyCommutePlan ;
                      :hasStartStation :UniversityStation ;
                      :hasEndStation :CentralStation ;
                      :usesTransportMode :MetroLine1 .
                      
        :BobTour rdf:type :SingleTripPlan ;
                 :hasStartStation :CentralStation ;
                 :hasEndStation :ParkBusStop ;
                 :usesTransportMode :CityBus .
        
        # Link persons to their travel plans
        :Alice :hasTravelPlan :AliceCommute .
        :Bob :hasTravelPlan :BobTour .
    }
    """
    
    try:
        print("🏗️  Creating sample data...")
        
        headers = {
            'Content-Type': 'application/sparql-update',
        }
        
        response = requests.post(
            FUSEKI_UPDATE_ENDPOINT,
            data=sample_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            print("✅ Sample data created successfully!")
            return True
        else:
            print(f"❌ Failed to create sample data: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def verify_data():
    """Verify that data was loaded correctly"""
    
    test_queries = [
        ("Classes", "SELECT (COUNT(DISTINCT ?class) as ?count) WHERE { ?class rdf:type owl:Class }"),
        ("Individuals", "SELECT (COUNT(DISTINCT ?individual) as ?count) WHERE { ?individual rdf:type ?class . FILTER(?class != owl:Class) }"),
        ("Transport Modes", "SELECT (COUNT(?mode) as ?count) WHERE { ?mode rdf:type ?type . FILTER(?type = <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Bike> || ?type = <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Bus> || ?type = <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Metro>) }"),
        ("Persons", "SELECT (COUNT(?person) as ?count) WHERE { ?person rdf:type <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#Person> }"),
    ]
    
    print("\n📊 Verifying loaded data:")
    
    for name, query in test_queries:
        try:
            full_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            {query}
            """
            
            response = requests.get(
                FUSEKI_QUERY_ENDPOINT,
                params={'query': full_query, 'format': 'json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                bindings = data.get('results', {}).get('bindings', [])
                if bindings:
                    count = bindings[0].get('count', {}).get('value', '0')
                    print(f"   {name}: {count}")
                else:
                    print(f"   {name}: 0")
            else:
                print(f"   {name}: Error querying")
                
        except Exception as e:
            print(f"   {name}: Error - {e}")

def main():
    """Main initialization function"""
    print("🚀 Initializing Fuseki Database...")
    print("=" * 50)
    
    # Check Fuseki connection
    if not check_fuseki_connection():
        print("❌ Please make sure Fuseki server is running on port 3030")
        print("   Run: java -jar fuseki-server.jar --update --mem /smartcity")
        sys.exit(1)
    
    print("✅ Fuseki server is running")
    
    # Load ontology file if it exists
    ontology_loaded = load_ontology_file()
    
    # Create sample data
    sample_created = create_sample_data()
    
    if sample_created:
        # Wait a moment for data to be indexed
        time.sleep(2)
        
        # Verify the data
        verify_data()
        
        print("\n" + "=" * 50)
        print("🎉 Database initialization completed!")
        print("\n📋 Next steps:")
        print("   1. Test health endpoint: http://localhost:50001/api/health")
        print("   2. Test ontology classes: http://localhost:50001/api/ontology/classes")
        print("   3. Test transport modes: http://localhost:50001/api/transport-modes/")
        print("   4. Test search: http://localhost:50001/api/search/concepts?q=Person")
        
    else:
        print("❌ Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()