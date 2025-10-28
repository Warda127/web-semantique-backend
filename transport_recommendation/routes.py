"""
Transport Recommendation API Routes
Provides REST endpoints for transport recommendations based on user types and custom criteria.
"""

from flask import Blueprint, jsonify, request
from transport_recommendation_service import TransportRecommendationService
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for transport recommendation routes
router = Blueprint('transport_recommendation', __name__)

# Fuseki endpoint configuration
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"

# Initialize transport recommendation service
recommendation_service = TransportRecommendationService(fuseki_endpoint=FUSEKI_ENDPOINT)

@router.route('/recommendations/<user_type>', methods=['GET'])
def get_recommendations_for_user_type(user_type):
    """
    GET /api/recommendations/{user_type}
    Get transport recommendations for a specific user type.
    
    Path Parameters:
        user_type: Type of user (citizen, tourist, staff)
        
    Returns:
        JSON response with recommended transport modes and stations ranked by relevance
    """
    try:
        # Validate user type
        valid_user_types = ['citizen', 'tourist', 'staff']
        if user_type.lower() not in valid_user_types:
            return jsonify({
                "error": f"Invalid user type: {user_type}",
                "valid_types": valid_user_types
            }), 400
        
        logger.info(f"Getting recommendations for user type: {user_type}")
        
        # Get recommendations
        recommendations = recommendation_service.get_recommendations_for_user_type(user_type)
        
        # Format response
        recommendation_list = []
        for rec in recommendations:
            recommendation_data = {
                "transportMode": rec.transport_mode,
                "stations": rec.stations,
                "relevanceScore": rec.relevance_score,
                "reasoning": rec.reasoning
            }
            
            # Add properties if available
            if rec.properties:
                recommendation_data["properties"] = rec.properties
                
            recommendation_list.append(recommendation_data)
        
        response = {
            "userType": user_type,
            "recommendations": recommendation_list,
            "total": len(recommendation_list)
        }
        
        logger.info(f"Generated {len(recommendation_list)} recommendations for {user_type}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting recommendations for {user_type}: {str(e)}")
        return jsonify({
            "error": f"Failed to get recommendations for user type {user_type}",
            "message": str(e)
        }), 500

@router.route('/transport/<transport_type>/stations', methods=['GET'])
def get_transport_stations(transport_type):
    """
    GET /api/transport/{transport_type}/stations
    Get stations for a specific transport type.
    
    Path Parameters:
        transport_type: Type of transport (bike, bus, metro)
        
    Returns:
        JSON response with list of stations compatible with the transport type
    """
    try:
        # Normalize transport type
        transport_type_normalized = transport_type.lower().capitalize()
        
        # Validate transport type
        valid_transport_types = ['Bike', 'Bus', 'Metro']
        if transport_type_normalized not in valid_transport_types:
            return jsonify({
                "error": f"Invalid transport type: {transport_type}",
                "valid_types": [t.lower() for t in valid_transport_types]
            }), 400
        
        logger.info(f"Getting stations for transport type: {transport_type_normalized}")
        
        # Get transport-station mappings
        transport_stations = recommendation_service.get_transport_stations_mapping()
        
        # Get stations for the specified transport type
        stations = transport_stations.get(transport_type_normalized, [])
        
        # Format station data with additional details
        station_list = []
        for station_name in stations:
            station_data = {
                "name": station_name,
                "transportType": transport_type_normalized,
                "uri": f"{recommendation_service.ontology_namespace}{station_name}"
            }
            station_list.append(station_data)
        
        response = {
            "transportType": transport_type_normalized,
            "stations": station_list,
            "total": len(station_list)
        }
        
        logger.info(f"Found {len(station_list)} stations for {transport_type_normalized}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting stations for {transport_type}: {str(e)}")
        return jsonify({
            "error": f"Failed to get stations for transport type {transport_type}",
            "message": str(e)
        }), 500

@router.route('/recommendations/custom', methods=['POST'])
def get_custom_recommendations():
    """
    POST /api/recommendations/custom
    Get personalized recommendations based on custom criteria.
    
    Request Body:
        JSON object with custom preferences and constraints:
        {
            "userType": "citizen|tourist|staff",
            "preferences": {
                "speed": "high|medium|low",
                "cost": "high|medium|low",
                "environmental": "high|medium|low"
            },
            "constraints": {
                "maxDistance": number,
                "availableTime": number,
                "accessibility": boolean
            }
        }
        
    Returns:
        JSON response with personalized recommendations based on the provided criteria
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Request body is required",
                "expected_format": {
                    "userType": "citizen|tourist|staff",
                    "preferences": {"speed": "high|medium|low", "cost": "high|medium|low"},
                    "constraints": {"maxDistance": "number", "availableTime": "number"}
                }
            }), 400
        
        user_type = data.get('userType', 'citizen')
        preferences = data.get('preferences', {})
        constraints = data.get('constraints', {})
        
        logger.info(f"Getting custom recommendations for user type: {user_type}")
        
        # Get base recommendations for user type
        base_recommendations = recommendation_service.get_recommendations_for_user_type(user_type)
        
        # Apply custom scoring based on preferences and constraints
        custom_recommendations = []
        for rec in base_recommendations:
            # Calculate custom relevance score
            custom_score = rec.relevance_score
            
            # Apply preference modifiers
            if preferences.get('speed') == 'high' and rec.transport_mode == 'Metro':
                custom_score += 0.2
            elif preferences.get('speed') == 'low' and rec.transport_mode == 'Bike':
                custom_score += 0.1
            
            if preferences.get('environmental') == 'high' and rec.transport_mode == 'Bike':
                custom_score += 0.3
            elif preferences.get('environmental') == 'medium' and rec.transport_mode == 'Metro':
                custom_score += 0.1
            
            if preferences.get('cost') == 'low' and rec.transport_mode == 'Bike':
                custom_score += 0.2
            
            # Apply constraint modifiers
            if constraints.get('accessibility') and rec.transport_mode in ['Bus', 'Metro']:
                custom_score += 0.1
            
            # Cap score at 1.0
            custom_score = min(1.0, custom_score)
            
            # Generate custom reasoning
            custom_reasoning = rec.reasoning
            if custom_score > rec.relevance_score:
                custom_reasoning += f" (Enhanced match for your preferences: {', '.join(preferences.keys())})"
            
            custom_rec = {
                "transportMode": rec.transport_mode,
                "stations": rec.stations,
                "relevanceScore": custom_score,
                "originalScore": rec.relevance_score,
                "reasoning": custom_reasoning,
                "matchedPreferences": [pref for pref in preferences.keys() 
                                     if _preference_matches_transport(pref, preferences[pref], rec.transport_mode)]
            }
            
            if rec.properties:
                custom_rec["properties"] = rec.properties
                
            custom_recommendations.append(custom_rec)
        
        # Sort by custom relevance score
        custom_recommendations.sort(key=lambda x: x['relevanceScore'], reverse=True)
        
        response = {
            "userType": user_type,
            "appliedPreferences": preferences,
            "appliedConstraints": constraints,
            "recommendations": custom_recommendations,
            "total": len(custom_recommendations)
        }
        
        logger.info(f"Generated {len(custom_recommendations)} custom recommendations")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating custom recommendations: {str(e)}")
        return jsonify({
            "error": "Failed to generate custom recommendations",
            "message": str(e)
        }), 500

def _preference_matches_transport(preference: str, preference_value: str, transport_mode: str) -> bool:
    """Helper function to check if a preference matches a transport mode"""
    matches = {
        'speed': {
            'high': ['Metro'],
            'medium': ['Bus'],
            'low': ['Bike']
        },
        'environmental': {
            'high': ['Bike'],
            'medium': ['Metro'],
            'low': ['Bus']
        },
        'cost': {
            'low': ['Bike'],
            'medium': ['Bus', 'Metro'],
            'high': []
        }
    }
    
    return transport_mode in matches.get(preference, {}).get(preference_value, [])

# Health check endpoint for transport recommendation module
@router.route('/recommendations/health', methods=['GET'])
def transport_recommendation_health():
    """
    GET /api/recommendations/health
    Health check for transport recommendation functionality.
    
    Returns:
        JSON response with service status and basic functionality test
    """
    try:
        # Test basic functionality by getting recommendations for citizen
        test_recommendations = recommendation_service.get_recommendations_for_user_type('citizen')
        
        # Test transport-station mapping
        transport_stations = recommendation_service.get_transport_stations_mapping()
        
        response = {
            "status": "healthy",
            "service": "transport_recommendation",
            "endpoint": FUSEKI_ENDPOINT,
            "test_recommendations_count": len(test_recommendations),
            "transport_modes_available": len(transport_stations)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "transport_recommendation",
            "endpoint": FUSEKI_ENDPOINT,
            "error": str(e)
        }), 503