"""
Ontology Search API Routes
Provides REST endpoints for ontology concept search, class retrieval, and hierarchy exploration.
"""

from flask import Blueprint, jsonify, request
from ontology_search_service import OntologySearchService
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for ontology search routes
router = Blueprint('ontology_search', __name__)

# Fuseki endpoint configuration
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"

# Initialize ontology search service
ontology_service = OntologySearchService(fuseki_endpoint=FUSEKI_ENDPOINT)

@router.route('/search/concepts', methods=['GET'])
def search_concepts():
    """
    GET /api/search/concepts?q={keyword}
    Search ontology concepts by keyword with case-insensitive partial matching.
    
    Query Parameters:
        q (optional): Search keyword to match against entity labels
        
    Returns:
        JSON response with list of matching concepts including URIs, labels, and types
    """
    try:
        keyword = request.args.get('q', '').strip()
        
        logger.info(f"Searching concepts with keyword: '{keyword}'")
        
        # Execute search
        search_results = ontology_service.search_concepts_by_keyword(keyword)
        
        # Format response
        concepts = []
        for result in search_results:
            concept = {
                "uri": result.uri,
                "label": result.label,
                "type": result.class_type
            }
            
            # Add optional fields if available
            if result.description:
                concept["description"] = result.description
            if result.properties:
                concept["properties"] = result.properties
                
            concepts.append(concept)
        
        response = {
            "concepts": concepts,
            "total": len(concepts),
            "query": keyword if keyword else "all"
        }
        
        logger.info(f"Found {len(concepts)} concepts for keyword '{keyword}'")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in concept search: {str(e)}")
        return jsonify({
            "error": "Failed to search concepts",
            "message": str(e)
        }), 500

@router.route('/ontology/classes', methods=['GET'])
def get_ontology_classes():
    """
    GET /api/ontology/classes
    Retrieve all ontology classes with their metadata and relationships.
    
    Returns:
        JSON response with complete class list including labels, parent classes, and subclasses
    """
    try:
        logger.info("Retrieving all ontology classes")
        
        # Get all classes
        classes = ontology_service.get_all_classes()
        
        # Format response
        class_list = []
        for class_info in classes:
            class_data = {
                "uri": class_info.uri,
                "label": class_info.label
            }
            
            # Add optional fields if available
            if class_info.parent_class:
                class_data["parentClass"] = class_info.parent_class
            if class_info.subclasses:
                class_data["subclasses"] = class_info.subclasses
            if class_info.properties:
                class_data["properties"] = class_info.properties
                
            class_list.append(class_data)
        
        response = {
            "classes": class_list,
            "total": len(class_list)
        }
        
        logger.info(f"Retrieved {len(class_list)} ontology classes")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error retrieving classes: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve ontology classes",
            "message": str(e)
        }), 500

@router.route('/ontology/hierarchy', methods=['GET'])
def get_class_hierarchy():
    """
    GET /api/ontology/hierarchy
    Get class hierarchy structure as a nested tree representation.
    
    Returns:
        JSON response with hierarchical tree structure of classes showing parent-child relationships
    """
    try:
        logger.info("Building class hierarchy structure")
        
        # Get hierarchy
        hierarchy_data = ontology_service.get_class_hierarchy()
        
        # Check for errors in hierarchy building
        if "error" in hierarchy_data:
            return jsonify({
                "error": "Failed to build class hierarchy",
                "message": hierarchy_data["error"]
            }), 500
        
        response = {
            "hierarchy": hierarchy_data["hierarchy"],
            "metadata": {
                "totalClasses": hierarchy_data.get("total_classes", 0),
                "rootClasses": hierarchy_data.get("root_classes", 0)
            }
        }
        
        logger.info(f"Built hierarchy with {hierarchy_data.get('total_classes', 0)} classes")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error building hierarchy: {str(e)}")
        return jsonify({
            "error": "Failed to build class hierarchy",
            "message": str(e)
        }), 500

@router.route('/ontology/classes/<path:class_name>/subclasses', methods=['GET'])
def get_class_subclasses(class_name):
    """
    GET /api/ontology/classes/{class_name}/subclasses
    Get direct subclasses of a specific class.
    
    Path Parameters:
        class_name: Local name or full URI of the class
        
    Returns:
        JSON response with list of direct subclasses
    """
    try:
        # Construct full URI if only local name provided
        if not class_name.startswith('http'):
            class_uri = f"{ontology_service.ontology_namespace}{class_name}"
        else:
            class_uri = class_name
        
        logger.info(f"Getting subclasses for class: {class_uri}")
        
        # Get subclasses using the private method (we'll expose it)
        subclasses = ontology_service._get_subclasses(class_uri)
        
        # Format subclasses with labels
        subclass_list = []
        for subclass_uri in subclasses:
            subclass_list.append({
                "uri": subclass_uri,
                "label": ontology_service._extract_local_name(subclass_uri)
            })
        
        response = {
            "class": {
                "uri": class_uri,
                "label": ontology_service._extract_local_name(class_uri)
            },
            "subclasses": subclass_list,
            "total": len(subclass_list)
        }
        
        logger.info(f"Found {len(subclass_list)} subclasses for {class_name}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting subclasses for {class_name}: {str(e)}")
        return jsonify({
            "error": f"Failed to get subclasses for class {class_name}",
            "message": str(e)
        }), 500

# Health check endpoint for ontology search module
@router.route('/search/health', methods=['GET'])
def ontology_search_health():
    """
    GET /api/search/health
    Health check for ontology search functionality.
    
    Returns:
        JSON response with service status and basic connectivity information
    """
    try:
        # Test basic connectivity by trying a simple query
        test_results = ontology_service.search_concepts_by_keyword("Person")
        
        response = {
            "status": "healthy",
            "service": "ontology_search",
            "endpoint": FUSEKI_ENDPOINT,
            "test_query_results": len(test_results)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "ontology_search",
            "endpoint": FUSEKI_ENDPOINT,
            "error": str(e)
        }), 503