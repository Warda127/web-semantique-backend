"""
TransportRecommendationService - Provides intelligent transport recommendations based on user context.
Utilizes semantic relationships in the WebSemEsprit ontology to suggest relevant transport modes and stations.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from sparql_service import get_sparql_service
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

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Recommendation:
    """Represents a transport recommendation with relevance scoring"""
    transport_mode: str
    stations: List[str]
    relevance_score: float
    reasoning: str
    properties: Optional[Dict[str, Any]] = None

class TransportRecommendationService:
    """
    Service for providing intelligent transport recommendations based on user context.
    Analyzes semantic relationships to suggest relevant transport modes and stations.
    """
    
    def __init__(self, fuseki_endpoint: str = "http://localhost:3030/smartcity/query"):
        """
        Initialize the transport recommendation service.
        
        Args:
            fuseki_endpoint: SPARQL endpoint URL for ontology queries
        """
        self.fuseki_endpoint = fuseki_endpoint
        self.sparql_service = get_sparql_service(fuseki_endpoint)
        self.ontology_namespace = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
        
        # User type to transport mode mappings based on semantic relationships
        self.user_type_preferences = {
            "citizen": {
                "preferred_modes": ["Bus", "Metro", "Bike"],
                "weights": {"Bus": 0.8, "Metro": 0.9, "Bike": 0.7}
            },
            "tourist": {
                "preferred_modes": ["Metro", "Bus", "Bike"],
                "weights": {"Metro": 0.9, "Bus": 0.8, "Bike": 0.6}
            },
            "staff": {
                "preferred_modes": ["Bike", "Bus", "Metro"],
                "weights": {"Bike": 0.9, "Bus": 0.7, "Metro": 0.6}
            }
        }
        
        logger.info(f"TransportRecommendationService initialized with endpoint: {fuseki_endpoint}")
    
    def get_recommendations_for_user_type(self, user_type: str) -> List[Recommendation]:
        """
        Get transport recommendations for a specific user type with contextual suggestions.
        
        Args:
            user_type: Type of user (citizen, tourist, staff)
            
        Returns:
            List of Recommendation objects ranked by relevance
        """
        user_type = user_type.lower()
        
        if user_type not in self.user_type_preferences:
            logger.warning(f"Unknown user type: {user_type}. Using default recommendations.")
            user_type = "citizen"  # Default fallback
        
        logger.info(f"Generating recommendations for user type: {user_type}")
        
        # Get transport-station mappings
        transport_stations = self.get_transport_stations_mapping()
        
        recommendations = []
        preferences = self.user_type_preferences[user_type]
        
        for transport_mode in preferences["preferred_modes"]:
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(user_type, transport_mode)
            
            # Get stations for this transport mode
            stations = transport_stations.get(transport_mode, [])
            
            # Generate reasoning
            reasoning = self._generate_reasoning(user_type, transport_mode, relevance_score)
            
            # Get additional properties
            properties = self._get_transport_properties(transport_mode)
            
            recommendation = Recommendation(
                transport_mode=transport_mode,
                stations=stations,
                relevance_score=relevance_score,
                reasoning=reasoning,
                properties=properties
            )
            
            recommendations.append(recommendation)
        
        # Sort by relevance score (highest first)
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Generated {len(recommendations)} recommendations for {user_type}")
        return recommendations
    
    def calculate_relevance_score(self, user_type: str, transport_mode: str) -> float:
        """
        Calculate relevance score for a transport mode based on user type and semantic relationships.
        
        Args:
            user_type: Type of user (citizen, tourist, staff)
            transport_mode: Transport mode to score (Bike, Bus, Metro)
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        user_type = user_type.lower()
        
        # Base score from user preferences
        base_score = self.user_type_preferences.get(user_type, {}).get("weights", {}).get(transport_mode, 0.5)
        
        # Query semantic relationships to enhance scoring
        relationship_bonus = self._get_semantic_relationship_bonus(user_type, transport_mode)
        
        # Query transport properties for additional scoring factors
        property_bonus = self._get_property_bonus(transport_mode)
        
        # Calculate final score (capped at 1.0)
        final_score = min(1.0, base_score + relationship_bonus + property_bonus)
        
        logger.debug(f"Relevance score for {user_type}-{transport_mode}: {final_score} "
                    f"(base: {base_score}, relationship: {relationship_bonus}, property: {property_bonus})")
        
        return final_score
    
    def get_transport_stations_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping of transport modes to their compatible stations using semantic relationships.
        
        Returns:
            Dictionary mapping transport mode names to lists of station names
        """
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?transportMode ?transportName ?station ?stationName ?stationType
WHERE {{
    # Get transport modes
    ?transport rdf:type ?transportMode .
    FILTER(?transportMode = :Bike || ?transportMode = :Bus || ?transportMode = :Metro)
    OPTIONAL {{ ?transport :hasName ?transportName . }}
    
    # Get stations and their types
    ?stationInstance rdf:type ?stationType .
    FILTER(?stationType = :BikeStation || ?stationType = :BusStation || ?stationType = :MetroStation)
    OPTIONAL {{ ?stationInstance :hasName ?stationName . }}
    
    # Map transport modes to compatible station types
    BIND(
        IF(?transportMode = :Bike && ?stationType = :BikeStation, ?stationInstance,
        IF(?transportMode = :Bus && ?stationType = :BusStation, ?stationInstance,
        IF(?transportMode = :Metro && ?stationType = :MetroStation, ?stationInstance,
        ?UNDEF))) AS ?station
    )
    
    FILTER(BOUND(?station))
}}
ORDER BY ?transportMode ?station"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            transport_stations = {}
            
            for binding in results.get("results", {}).get("bindings", []):
                transport_mode = self._extract_local_name(binding["transportMode"]["value"])
                station_name = binding.get("stationName", {}).get("value", 
                                         self._extract_local_name(binding["station"]["value"]))
                
                if transport_mode not in transport_stations:
                    transport_stations[transport_mode] = []
                
                if station_name not in transport_stations[transport_mode]:
                    transport_stations[transport_mode].append(station_name)
            
            logger.info(f"Retrieved transport-station mappings: {len(transport_stations)} transport modes")
            return transport_stations
            
        except Exception as e:
            logger.error(f"Failed to get transport-station mapping: {str(e)}")
            # Return fallback mapping
            return {
                "Bike": ["BikeStation1", "BikeStation2"],
                "Bus": ["BusStation1", "BusStation2"],
                "Metro": ["MetroStation1", "MetroStation2"]
            }
    
    def _get_semantic_relationship_bonus(self, user_type: str, transport_mode: str) -> float:
        """Get bonus score based on semantic relationships in the ontology"""
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT (COUNT(*) as ?relationshipCount)
WHERE {{
    ?person rdf:type :{user_type.capitalize()} .
    ?transport rdf:type :{transport_mode} .
    
    # Check for usesTransport relationships
    OPTIONAL {{ ?person :usesTransport ?transport . }}
}}"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            bindings = results.get("results", {}).get("bindings", [])
            if bindings:
                count = int(bindings[0].get("relationshipCount", {}).get("value", "0"))
                # Convert count to bonus (0.0 to 0.2 range)
                return min(0.2, count * 0.05)
            
        except Exception as e:
            logger.debug(f"Semantic relationship query failed: {str(e)}")
        
        return 0.0
    
    def _get_property_bonus(self, transport_mode: str) -> float:
        """Get bonus score based on transport mode properties"""
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?speed ?capacity
WHERE {{
    ?transport rdf:type :{transport_mode} .
    OPTIONAL {{ ?transport :hasSpeed ?speed . }}
    OPTIONAL {{ ?transport :hasCapacity ?capacity . }}
}}
LIMIT 1"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            bindings = results.get("results", {}).get("bindings", [])
            if bindings:
                binding = bindings[0]
                speed = binding.get("speed", {}).get("value")
                capacity = binding.get("capacity", {}).get("value")
                
                bonus = 0.0
                
                # Speed bonus (higher speed = higher bonus, max 0.1)
                if speed:
                    try:
                        speed_val = float(speed)
                        bonus += min(0.1, speed_val / 100.0)  # Normalize speed
                    except ValueError:
                        pass
                
                # Capacity bonus (higher capacity = higher bonus, max 0.1)
                if capacity:
                    try:
                        capacity_val = float(capacity)
                        bonus += min(0.1, capacity_val / 1000.0)  # Normalize capacity
                    except ValueError:
                        pass
                
                return bonus
            
        except Exception as e:
            logger.debug(f"Property bonus query failed: {str(e)}")
        
        return 0.0
    
    def _generate_reasoning(self, user_type: str, transport_mode: str, relevance_score: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        reasoning_templates = {
            "citizen": {
                "Bus": "Buses provide reliable public transport for daily commuting with good coverage.",
                "Metro": "Metro offers fast and efficient transport for urban travel with high frequency.",
                "Bike": "Bikes provide eco-friendly transport for short to medium distances with health benefits."
            },
            "tourist": {
                "Metro": "Metro provides quick access to major tourist attractions with comprehensive network coverage.",
                "Bus": "Buses offer scenic routes and access to various tourist destinations throughout the city.",
                "Bike": "Bikes allow flexible exploration of tourist areas at your own pace."
            },
            "staff": {
                "Bike": "Bikes offer flexible and cost-effective transport for staff with parking convenience.",
                "Bus": "Buses provide reliable transport for staff commuting with predictable schedules.",
                "Metro": "Metro offers fast transport for staff working in central business districts."
            }
        }
        
        base_reasoning = reasoning_templates.get(user_type, {}).get(transport_mode, 
                                                f"{transport_mode} is suitable for {user_type} users.")
        
        # Add score-based qualifier
        if relevance_score >= 0.8:
            qualifier = "Highly recommended: "
        elif relevance_score >= 0.6:
            qualifier = "Recommended: "
        else:
            qualifier = "Consider: "
        
        return qualifier + base_reasoning
    
    def _get_transport_properties(self, transport_mode: str) -> Dict[str, Any]:
        """Get additional properties for a transport mode"""
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?property ?value
WHERE {{
    ?transport rdf:type :{transport_mode} .
    ?transport ?property ?value .
    FILTER(?property != rdf:type)
}}"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            properties = {}
            for binding in results.get("results", {}).get("bindings", []):
                prop_name = self._extract_local_name(binding["property"]["value"])
                prop_value = binding["value"]["value"]
                properties[prop_name] = prop_value
            
            return properties
            
        except Exception as e:
            logger.debug(f"Properties query failed: {str(e)}")
            return {}
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI for display purposes"""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri