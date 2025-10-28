"""
Custom Query API Routes
Provides REST endpoints for executing custom SPARQL SELECT queries with validation and error handling.
"""

from flask import Blueprint, jsonify, request
from custom_query_service import CustomQueryService
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for custom query routes
router = Blueprint('custom_query', __name__)

# Fuseki endpoint configuration
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"

# Initialize custom query service
query_service = CustomQueryService(fuseki_endpoint=FUSEKI_ENDPOINT)

@router.route('/sparql/query', methods=['POST'])
def execute_custom_query():
    """
    POST /api/sparql/query
    Execute custom SPARQL SELECT queries with validation and standardized formatting.
    
    Request Body:
        {
            "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
            "timeout": 30,  // optional, seconds
            "format": true  // optional, whether to format results
        }
        
    Returns:
        JSON response with query results, execution metadata, and error handling
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "code": "INVALID_CONTENT_TYPE"
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'query' not in data:
            return jsonify({
                "error": "Request must contain 'query' field",
                "code": "MISSING_QUERY",
                "example": {
                    "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
                }
            }), 400
        
        query = data.get('query', '').strip()
        timeout = data.get('timeout')
        format_results = data.get('format', True)
        
        # Validate timeout parameter
        if timeout is not None:
            try:
                timeout = int(timeout)
                if timeout <= 0 or timeout > 300:  # Max 5 minutes
                    return jsonify({
                        "error": "Timeout must be between 1 and 300 seconds",
                        "code": "INVALID_TIMEOUT"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Timeout must be a valid integer",
                    "code": "INVALID_TIMEOUT_FORMAT"
                }), 400
        
        logger.info(f"Executing custom query with timeout: {timeout}s")
        
        # Execute query
        result = query_service.execute_custom_query(
            query=query,
            timeout=timeout,
            format_results=format_results
        )
        
        if result.success:
            response = {
                "success": True,
                "data": result.data,
                "metadata": result.metadata
            }
            
            logger.info(f"Query executed successfully in {result.execution_time:.3f}s")
            return jsonify(response)
        else:
            # Return structured error response
            error_response = {
                "success": False,
                "error": {
                    "message": result.error,
                    "code": _get_error_code(result.error),
                    "suggestions": _get_error_suggestions(result.error)
                },
                "metadata": result.metadata or {}
            }
            
            # Determine appropriate HTTP status code
            status_code = _get_error_status_code(result.error)
            
            logger.warning(f"Query execution failed: {result.error}")
            return jsonify(error_response), status_code
            
    except Exception as e:
        logger.error(f"Unexpected error in custom query execution: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "message": "Internal server error during query execution",
                "code": "INTERNAL_ERROR",
                "details": str(e)
            }
        }), 500

@router.route('/sparql/validate', methods=['POST'])
def validate_query():
    """
    POST /api/sparql/validate
    Validate SPARQL query syntax without executing it.
    
    Request Body:
        {
            "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        }
        
    Returns:
        JSON response with validation results and query statistics
    """
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "code": "INVALID_CONTENT_TYPE"
            }), 400
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Request must contain 'query' field",
                "code": "MISSING_QUERY"
            }), 400
        
        query = data.get('query', '').strip()
        
        logger.info("Validating SPARQL query syntax")
        
        # Validate query
        result = query_service.validate_query_syntax(query)
        
        if result.success:
            response = {
                "valid": True,
                "data": result.data,
                "metadata": result.metadata
            }
            return jsonify(response)
        else:
            response = {
                "valid": False,
                "error": {
                    "message": result.error,
                    "code": _get_error_code(result.error),
                    "suggestions": _get_validation_suggestions(result.error)
                },
                "metadata": result.metadata or {}
            }
            return jsonify(response), 400
            
    except Exception as e:
        logger.error(f"Error in query validation: {str(e)}")
        return jsonify({
            "valid": False,
            "error": {
                "message": "Internal error during validation",
                "code": "VALIDATION_ERROR",
                "details": str(e)
            }
        }), 500

@router.route('/sparql/examples', methods=['GET'])
def get_query_examples():
    """
    GET /api/sparql/examples
    Get example SPARQL queries for the ontology.
    
    Returns:
        JSON response with example queries and descriptions
    """
    try:
        examples = query_service.get_query_examples()
        
        response = {
            "examples": examples["examples"],
            "metadata": {
                "namespace": examples["namespace"],
                "endpoint": examples["endpoint"],
                "total_examples": len(examples["examples"])
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting query examples: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve query examples",
            "message": str(e)
        }), 500

@router.route('/sparql/health', methods=['GET'])
def custom_query_health():
    """
    GET /api/sparql/health
    Health check for custom query functionality.
    
    Returns:
        JSON response with service status and connectivity information
    """
    try:
        # Test with a simple query
        test_query = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"
        result = query_service.execute_custom_query(test_query, timeout=5)
        
        if result.success:
            response = {
                "status": "healthy",
                "service": "custom_query",
                "endpoint": FUSEKI_ENDPOINT,
                "test_execution_time": result.execution_time,
                "capabilities": {
                    "query_validation": True,
                    "timeout_support": True,
                    "result_formatting": True,
                    "error_handling": True
                }
            }
            return jsonify(response)
        else:
            response = {
                "status": "unhealthy",
                "service": "custom_query",
                "endpoint": FUSEKI_ENDPOINT,
                "error": result.error
            }
            return jsonify(response), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "service": "custom_query",
            "endpoint": FUSEKI_ENDPOINT,
            "error": str(e)
        }), 503

def _get_error_code(error_message: str) -> str:
    """Generate appropriate error code based on error message"""
    if not error_message:
        return "UNKNOWN_ERROR"
    
    error_lower = error_message.lower()
    
    if "syntax" in error_lower or "malformed" in error_lower:
        return "SYNTAX_ERROR"
    elif "timeout" in error_lower:
        return "TIMEOUT_ERROR"
    elif "connection" in error_lower or "endpoint" in error_lower:
        return "CONNECTION_ERROR"
    elif "validation" in error_lower:
        return "VALIDATION_ERROR"
    elif "empty" in error_lower:
        return "EMPTY_QUERY"
    elif "too long" in error_lower:
        return "QUERY_TOO_LONG"
    elif "dangerous" in error_lower:
        return "DANGEROUS_QUERY"
    elif "select" in error_lower and "only" in error_lower:
        return "INVALID_QUERY_TYPE"
    else:
        return "EXECUTION_ERROR"

def _get_error_status_code(error_message: str) -> int:
    """Determine appropriate HTTP status code based on error"""
    if not error_message:
        return 500
    
    error_lower = error_message.lower()
    
    if any(term in error_lower for term in ["syntax", "validation", "malformed", "empty", "dangerous"]):
        return 400  # Bad Request
    elif "timeout" in error_lower:
        return 408  # Request Timeout
    elif any(term in error_lower for term in ["connection", "endpoint"]):
        return 503  # Service Unavailable
    else:
        return 500  # Internal Server Error

def _get_error_suggestions(error_message: str) -> list:
    """Generate helpful suggestions based on error message"""
    if not error_message:
        return []
    
    error_lower = error_message.lower()
    suggestions = []
    
    if "syntax" in error_lower:
        suggestions.extend([
            "Check SPARQL syntax for missing brackets or semicolons",
            "Verify PREFIX declarations are properly formatted",
            "Ensure WHERE clause is properly structured"
        ])
    elif "timeout" in error_lower:
        suggestions.extend([
            "Add LIMIT clause to reduce result set size",
            "Optimize query with more specific FILTER conditions",
            "Consider breaking complex query into smaller parts"
        ])
    elif "empty" in error_lower:
        suggestions.append("Provide a valid SPARQL SELECT query")
    elif "select" in error_lower and "only" in error_lower:
        suggestions.extend([
            "Use SELECT queries only for custom queries",
            "Example: SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
        ])
    elif "dangerous" in error_lower:
        suggestions.extend([
            "Remove modification operations (INSERT, DELETE, DROP)",
            "Use only SELECT queries for data retrieval"
        ])
    
    return suggestions

def _get_validation_suggestions(error_message: str) -> list:
    """Generate validation-specific suggestions"""
    suggestions = _get_error_suggestions(error_message)
    
    if not suggestions:
        suggestions = [
            "Check query syntax against SPARQL 1.1 specification",
            "Use /api/sparql/examples to see valid query patterns"
        ]
    
    return suggestions