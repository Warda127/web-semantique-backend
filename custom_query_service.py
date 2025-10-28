"""
CustomQueryService - Handles custom SPARQL query processing with validation and sanitization.
Provides standardized JSON response formatting for query results.
"""

import re
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from sparql_service import SPARQLQueryService, QueryResult, ValidationResult, QueryType
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
class CustomQueryResult:
    """Standardized result format for custom SPARQL queries"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    query_type: Optional[str] = None
    bindings_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomQueryService:
    """
    Service for processing custom SPARQL queries with enhanced validation and formatting.
    Implements SPARQL query validation, sanitization, timeout handling, and standardized JSON responses.
    """
    
    def __init__(self, fuseki_endpoint: str = "http://localhost:3030/smartcity/query"):
        """
        Initialize the custom query service.
        
        Args:
            fuseki_endpoint: SPARQL endpoint URL for query execution
        """
        self.fuseki_endpoint = fuseki_endpoint
        self.sparql_service = SPARQLQueryService(
            fuseki_endpoint=fuseki_endpoint,
            default_timeout=30,
            max_retries=2
        )
        self.ontology_namespace = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
        
        # Query execution limits
        self.max_query_length = 10000
        self.max_results_limit = 1000
        self.default_timeout = 30
        
        logger.info(f"CustomQueryService initialized with endpoint: {fuseki_endpoint}")
    
    def execute_custom_query(self, 
                           query: str, 
                           timeout: Optional[int] = None,
                           format_results: bool = True) -> CustomQueryResult:
        """
        Execute custom SPARQL SELECT query with validation and standardized formatting.
        
        Args:
            query: SPARQL query string
            timeout: Query timeout in seconds (uses default if None)
            format_results: Whether to format results in standardized JSON format
            
        Returns:
            CustomQueryResult with execution results and metadata
        """
        start_time = time.time()
        
        # Input validation
        validation_result = self._validate_custom_query(query)
        if not validation_result.success:
            return validation_result
        
        # Execute query using enhanced SPARQL service
        query_timeout = timeout or self.default_timeout
        sparql_result = self.sparql_service.execute_query_with_validation(
            query, 
            timeout=query_timeout,
            validate=True
        )
        
        execution_time = time.time() - start_time
        
        if not sparql_result.success:
            return CustomQueryResult(
                success=False,
                error=sparql_result.error,
                execution_time=execution_time,
                query_type=self._detect_query_type(query)
            )
        
        # Format results if requested
        if format_results:
            formatted_data = self._format_query_results(sparql_result.data, query)
        else:
            formatted_data = sparql_result.data
        
        # Create metadata
        metadata = {
            "query_length": len(query),
            "execution_time": execution_time,
            "bindings_count": sparql_result.bindings_count,
            "query_type": self._detect_query_type(query),
            "endpoint": self.fuseki_endpoint,
            "timeout_used": query_timeout
        }
        
        return CustomQueryResult(
            success=True,
            data=formatted_data,
            execution_time=execution_time,
            query_type=self._detect_query_type(query),
            bindings_count=sparql_result.bindings_count,
            metadata=metadata
        )
    
    def validate_query_syntax(self, query: str) -> CustomQueryResult:
        """
        Validate SPARQL query syntax without executing it.
        
        Args:
            query: SPARQL query string to validate
            
        Returns:
            CustomQueryResult with validation status and suggestions
        """
        validation_result = self._validate_custom_query(query)
        
        if validation_result.success:
            # Get additional query statistics
            stats = self.sparql_service.get_query_statistics(query)
            
            return CustomQueryResult(
                success=True,
                data={
                    "is_valid": True,
                    "query_type": self._detect_query_type(query),
                    "statistics": stats,
                    "suggestions": self._get_query_suggestions(query)
                },
                metadata={"validation_only": True}
            )
        else:
            return validation_result
    
    def _validate_custom_query(self, query: str) -> CustomQueryResult:
        """
        Comprehensive validation for custom SPARQL queries.
        
        Args:
            query: SPARQL query string
            
        Returns:
            CustomQueryResult with validation status
        """
        if not query or not query.strip():
            return CustomQueryResult(
                success=False,
                error="Query cannot be empty",
                metadata={"validation_error": "empty_query"}
            )
        
        query = query.strip()
        
        # Check query length
        if len(query) > self.max_query_length:
            return CustomQueryResult(
                success=False,
                error=f"Query too long. Maximum length is {self.max_query_length} characters",
                metadata={"validation_error": "query_too_long", "query_length": len(query)}
            )
        
        # Only allow SELECT queries for custom queries
        query_type = self._detect_query_type(query)
        if query_type != "SELECT":
            return CustomQueryResult(
                success=False,
                error="Only SELECT queries are allowed for custom queries",
                metadata={"validation_error": "invalid_query_type", "detected_type": query_type}
            )
        
        # Use SPARQL service validation
        validation = self.sparql_service.validate_query_syntax(query)
        if not validation.is_valid:
            return CustomQueryResult(
                success=False,
                error=validation.error_message,
                metadata={
                    "validation_error": "syntax_error",
                    "suggestions": validation.suggestions
                }
            )
        
        # Check for potentially dangerous patterns
        dangerous_patterns = self._check_dangerous_patterns(query)
        if dangerous_patterns:
            return CustomQueryResult(
                success=False,
                error=f"Query contains potentially dangerous patterns: {', '.join(dangerous_patterns)}",
                metadata={"validation_error": "dangerous_patterns", "patterns": dangerous_patterns}
            )
        
        return CustomQueryResult(success=True)
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of SPARQL query"""
        query_upper = query.upper().strip()
        
        # Look for query type keywords anywhere in query (after prefixes)
        if 'SELECT ' in query_upper:
            return "SELECT"
        elif 'CONSTRUCT ' in query_upper:
            return "CONSTRUCT"
        elif 'ASK ' in query_upper:
            return "ASK"
        elif 'DESCRIBE ' in query_upper:
            return "DESCRIBE"
        elif 'INSERT ' in query_upper:
            return "INSERT"
        elif 'DELETE ' in query_upper:
            return "DELETE"
        else:
            return "UNKNOWN"
    
    def _check_dangerous_patterns(self, query: str) -> List[str]:
        """Check for potentially dangerous query patterns"""
        dangerous_patterns = []
        query_upper = query.upper()
        
        # Check for modification operations (should not be in SELECT queries)
        if any(op in query_upper for op in ['INSERT', 'DELETE', 'DROP', 'CLEAR', 'LOAD']):
            dangerous_patterns.append("modification_operations")
        
        # Check for system function calls
        if any(func in query_upper for func in ['SYSTEM', 'EXEC', 'SHELL']):
            dangerous_patterns.append("system_functions")
        
        # Check for excessive UNION operations (potential DoS)
        union_count = query_upper.count('UNION')
        if union_count > 10:
            dangerous_patterns.append("excessive_unions")
        
        return dangerous_patterns
    
    def _format_query_results(self, raw_results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Format SPARQL query results into standardized JSON format.
        
        Args:
            raw_results: Raw SPARQL results from SPARQLWrapper
            query: Original query string for context
            
        Returns:
            Formatted results dictionary
        """
        if not raw_results or 'results' not in raw_results:
            return {
                "variables": [],
                "bindings": [],
                "bindings_count": 0,
                "formatted": True
            }
        
        results = raw_results['results']
        variables = results.get('vars', [])
        bindings = results.get('bindings', [])
        
        # Format bindings for better readability
        formatted_bindings = []
        for binding in bindings:
            formatted_binding = {}
            for var in variables:
                if var in binding:
                    value_info = binding[var]
                    formatted_binding[var] = {
                        "value": value_info.get("value", ""),
                        "type": value_info.get("type", "literal"),
                        "datatype": value_info.get("datatype"),
                        "xml:lang": value_info.get("xml:lang")
                    }
                    
                    # Add human-readable label for URIs
                    if value_info.get("type") == "uri":
                        formatted_binding[var]["local_name"] = self._extract_local_name(value_info.get("value", ""))
                else:
                    formatted_binding[var] = None
            
            formatted_bindings.append(formatted_binding)
        
        return {
            "variables": variables,
            "bindings": formatted_bindings,
            "bindings_count": len(formatted_bindings),
            "formatted": True,
            "query_info": {
                "query_type": self._detect_query_type(query),
                "has_limit": "LIMIT" in query.upper(),
                "has_order": "ORDER" in query.upper()
            }
        }
    
    def _get_query_suggestions(self, query: str) -> List[str]:
        """Generate helpful suggestions for query optimization"""
        suggestions = []
        query_upper = query.upper()
        
        # Performance suggestions
        if "LIMIT" not in query_upper:
            suggestions.append("Consider adding a LIMIT clause to prevent large result sets")
        
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            suggestions.append("ORDER BY without LIMIT can be expensive for large datasets")
        
        # Namespace suggestions
        if ":" in query and "PREFIX" not in query_upper:
            suggestions.append("Define PREFIX declarations for better readability")
        
        # Filter suggestions
        if "OPTIONAL" in query_upper and "FILTER" not in query_upper:
            suggestions.append("Consider adding FILTER clauses to optimize OPTIONAL patterns")
        
        return suggestions
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI for display purposes"""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri
    
    def get_query_examples(self) -> Dict[str, Any]:
        """
        Get example SPARQL queries for the ontology.
        
        Returns:
            Dictionary with example queries and descriptions
        """
        examples = {
            "basic_concepts": {
                "description": "Get all concepts in the ontology",
                "query": f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?concept ?type
WHERE {{
    ?concept rdf:type ?type .
}}
LIMIT 20"""
            },
            "transport_modes": {
                "description": "Get all transport modes",
                "query": f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?transport ?name
WHERE {{
    ?transport rdf:type :TransportMode .
    OPTIONAL {{ ?transport :hasName ?name . }}
}}"""
            },
            "persons_and_transport": {
                "description": "Find persons and their transport preferences",
                "query": f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?person ?name ?transport
WHERE {{
    ?person rdf:type :Person .
    ?person :hasName ?name .
    ?person :usesTransport ?transport .
}}"""
            },
            "class_hierarchy": {
                "description": "Explore class hierarchy relationships",
                "query": f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?parent ?label
WHERE {{
    ?class rdfs:subClassOf ?parent .
    OPTIONAL {{ ?class rdfs:label ?label . }}
}}"""
            }
        }
        
        return {
            "examples": examples,
            "namespace": self.ontology_namespace,
            "endpoint": self.fuseki_endpoint
        }