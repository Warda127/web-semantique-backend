"""
Enhanced SPARQL service infrastructure with validation, timeout, and error handling capabilities.
Extends the existing execute_sparql_query function with additional features.
"""

import re
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
try:
    from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST
    from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException, QueryBadFormed, EndPointNotFound
except ImportError:
    # Fallback for testing without SPARQLWrapper
    class SPARQLWrapper:
        def __init__(self, endpoint): pass
        def setQuery(self, query): pass
        def setReturnFormat(self, format): pass
        def setTimeout(self, timeout): pass
        def query(self): 
            class MockResult:
                def convert(self): return {"results": {"bindings": []}}
            return MockResult()
    
    class SPARQLWrapperException(Exception): pass
    class QueryBadFormed(Exception): pass
    class EndPointNotFound(Exception): pass
    JSON = "json"
    POST = "post"
    DIGEST = "digest"
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """SPARQL query types"""
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    ASK = "ASK"
    DESCRIBE = "DESCRIBE"
    INSERT = "INSERT"
    DELETE = "DELETE"
    UPDATE = "UPDATE"

@dataclass
class QueryResult:
    """Standardized query result structure"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    query_type: Optional[QueryType] = None
    bindings_count: Optional[int] = None

@dataclass
class ValidationResult:
    """Query validation result"""
    is_valid: bool
    error_message: Optional[str] = None
    suggestions: Optional[List[str]] = None
    query_type: Optional[QueryType] = None

@dataclass
class ConnectionStatus:
    """Fuseki connection status"""
    is_connected: bool
    endpoint_url: str
    response_time: Optional[float] = None
    error: Optional[str] = None
    last_checked: Optional[float] = None

class SPARQLQueryService:
    """
    Enhanced SPARQL service with validation, timeout, and error handling capabilities.
    Extends the existing execute_sparql_query function with additional features.
    """
    
    def __init__(self, 
                 fuseki_endpoint: str = "http://localhost:3030/smartcity/query",
                 fuseki_update_endpoint: str = "http://localhost:3030/smartcity/update",
                 default_timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize the SPARQL service.
        
        Args:
            fuseki_endpoint: SPARQL query endpoint URL
            fuseki_update_endpoint: SPARQL update endpoint URL  
            default_timeout: Default query timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.fuseki_endpoint = fuseki_endpoint
        self.fuseki_update_endpoint = fuseki_update_endpoint
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        
        # Connection pool settings
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OntologySearchBackend/1.0'
        })
        
        # Query validation patterns
        self._init_validation_patterns()
        
        logger.info(f"SPARQLQueryService initialized with endpoint: {fuseki_endpoint}")
    
    def _init_validation_patterns(self):
        """Initialize regex patterns for query validation"""
        self.query_patterns = {
            QueryType.SELECT: re.compile(r'SELECT\s+', re.IGNORECASE),
            QueryType.CONSTRUCT: re.compile(r'CONSTRUCT\s+', re.IGNORECASE),
            QueryType.ASK: re.compile(r'ASK\s+', re.IGNORECASE),
            QueryType.DESCRIBE: re.compile(r'DESCRIBE\s+', re.IGNORECASE),
            QueryType.INSERT: re.compile(r'INSERT\s+', re.IGNORECASE),
            QueryType.DELETE: re.compile(r'DELETE\s+', re.IGNORECASE),
        }
        
        # Common SPARQL injection patterns to detect
        self.injection_patterns = [
            re.compile(r';\s*DROP\s+', re.IGNORECASE),
            re.compile(r';\s*DELETE\s+', re.IGNORECASE),
            re.compile(r';\s*INSERT\s+', re.IGNORECASE),
            re.compile(r'UNION\s+SELECT.*--', re.IGNORECASE),
        ]
    
    def validate_query_syntax(self, query: str) -> ValidationResult:
        """
        Validate SPARQL query syntax and detect potential issues.
        
        Args:
            query: SPARQL query string
            
        Returns:
            ValidationResult with validation status and suggestions
        """
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Query cannot be empty",
                suggestions=["Provide a valid SPARQL query"]
            )
        
        query = query.strip()
        
        # Detect query type
        query_type = None
        for qtype, pattern in self.query_patterns.items():
            if pattern.search(query):
                query_type = qtype
                break
        
        if not query_type:
            return ValidationResult(
                is_valid=False,
                error_message="Unknown query type. Query must start with SELECT, CONSTRUCT, ASK, DESCRIBE, INSERT, or DELETE",
                suggestions=[
                    "Start your query with a valid SPARQL keyword",
                    "Example: SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
                ]
            )
        
        # Check for potential SPARQL injection
        for pattern in self.injection_patterns:
            if pattern.search(query):
                return ValidationResult(
                    is_valid=False,
                    error_message="Query contains potentially unsafe patterns",
                    suggestions=["Remove suspicious SQL-like commands", "Use proper SPARQL syntax"]
                )
        
        # Basic syntax checks
        suggestions = []
        
        # Check for balanced braces
        if query.count('{') != query.count('}'):
            return ValidationResult(
                is_valid=False,
                error_message="Unbalanced braces in query",
                suggestions=["Check that all { have matching }", "Verify WHERE clause syntax"]
            )
        
        # Check for WHERE clause in SELECT queries
        if query_type == QueryType.SELECT and 'WHERE' not in query.upper():
            suggestions.append("Consider adding a WHERE clause for better query structure")
        
        # Check for missing prefixes
        if ':' in query and 'PREFIX' not in query.upper():
            suggestions.append("Define PREFIX declarations for namespace shortcuts")
        
        return ValidationResult(
            is_valid=True,
            query_type=query_type,
            suggestions=suggestions if suggestions else None
        )
    
    def sanitize_query_input(self, query: str) -> str:
        """
        Sanitize query input to prevent injection attacks.
        
        Args:
            query: Raw query string
            
        Returns:
            Sanitized query string
        """
        if not query:
            return ""
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove comments that could hide malicious code
        query = re.sub(r'#[^\n]*', '', query)
        
        return query
    
    def execute_query_with_validation(self, 
                                    query: str, 
                                    timeout: Optional[int] = None,
                                    validate: bool = True) -> QueryResult:
        """
        Execute SPARQL query with validation and enhanced error handling.
        
        Args:
            query: SPARQL query string
            timeout: Query timeout in seconds (uses default if None)
            validate: Whether to validate query before execution
            
        Returns:
            QueryResult with execution results and metadata
        """
        start_time = time.time()
        
        # Sanitize input
        query = self.sanitize_query_input(query)
        
        # Validate query if requested
        if validate:
            validation = self.validate_query_syntax(query)
            if not validation.is_valid:
                return QueryResult(
                    success=False,
                    error=f"Query validation failed: {validation.error_message}",
                    execution_time=time.time() - start_time
                )
        
        # Use provided timeout or default
        query_timeout = timeout or self.default_timeout
        
        try:
            return self._execute_with_retry(query, query_timeout, start_time)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return QueryResult(
                success=False,
                error=f"Query execution error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _execute_with_retry(self, query: str, timeout: int, start_time: float) -> QueryResult:
        """Execute query with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                sparql = SPARQLWrapper(self.fuseki_endpoint)
                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                sparql.setTimeout(timeout)
                
                # Execute query
                results = sparql.query().convert()
                execution_time = time.time() - start_time
                
                # Count bindings if available
                bindings_count = None
                if 'results' in results and 'bindings' in results['results']:
                    bindings_count = len(results['results']['bindings'])
                
                logger.info(f"Query executed successfully in {execution_time:.3f}s, {bindings_count} results")
                
                return QueryResult(
                    success=True,
                    data=results,
                    execution_time=execution_time,
                    bindings_count=bindings_count
                )
                
            except SPARQLWrapperException as e:
                last_error = f"SPARQL error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Attempt {attempt + 1} failed: {last_error}")
                break  # Don't retry on unexpected errors
        
        return QueryResult(
            success=False,
            error=last_error,
            execution_time=time.time() - start_time
        )
    
    def execute_with_timeout(self, query: str, timeout: int) -> QueryResult:
        """
        Execute query with specific timeout.
        
        Args:
            query: SPARQL query string
            timeout: Timeout in seconds
            
        Returns:
            QueryResult with execution results
        """
        return self.execute_query_with_validation(query, timeout=timeout)
    
    def check_fuseki_connection(self) -> ConnectionStatus:
        """
        Check Fuseki server connectivity and response time.
        
        Returns:
            ConnectionStatus with connection details
        """
        start_time = time.time()
        
        try:
            # Simple ASK query to test connectivity
            test_query = "ASK { ?s ?p ?o }"
            
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(test_query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(5)  # Short timeout for connection test
            
            results = sparql.query().convert()
            response_time = time.time() - start_time
            
            return ConnectionStatus(
                is_connected=True,
                endpoint_url=self.fuseki_endpoint,
                response_time=response_time,
                last_checked=time.time()
            )
            
        except Exception as e:
            return ConnectionStatus(
                is_connected=False,
                endpoint_url=self.fuseki_endpoint,
                error=str(e),
                last_checked=time.time()
            )
    
    def get_query_statistics(self, query: str) -> Dict[str, Any]:
        """
        Analyze query and return statistics.
        
        Args:
            query: SPARQL query string
            
        Returns:
            Dictionary with query statistics
        """
        validation = self.validate_query_syntax(query)
        
        stats = {
            'query_length': len(query),
            'line_count': len(query.split('\n')),
            'query_type': validation.query_type.value if validation.query_type else None,
            'is_valid': validation.is_valid,
            'has_prefixes': 'PREFIX' in query.upper(),
            'has_filter': 'FILTER' in query.upper(),
            'has_optional': 'OPTIONAL' in query.upper(),
            'has_union': 'UNION' in query.upper(),
            'estimated_complexity': self._estimate_complexity(query)
        }
        
        return stats
    
    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity based on patterns"""
        complexity_score = 0
        
        # Count complex patterns
        if 'UNION' in query.upper():
            complexity_score += 2
        if 'OPTIONAL' in query.upper():
            complexity_score += 1
        if 'FILTER' in query.upper():
            complexity_score += 1
        if query.count('{') > 2:  # Nested patterns
            complexity_score += 1
        
        if complexity_score == 0:
            return "simple"
        elif complexity_score <= 2:
            return "moderate"
        else:
            return "complex"

# Backward compatibility: extend existing execute_sparql_query function
def execute_sparql_query(query: str, 
                        endpoint: str = "http://localhost:3030/smartcity/query",
                        timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Enhanced version of the existing execute_sparql_query function.
    Maintains backward compatibility while adding new capabilities.
    
    Args:
        query: SPARQL query string
        endpoint: SPARQL endpoint URL
        timeout: Query timeout in seconds
        
    Returns:
        Query results dictionary or None on error
    """
    service = SPARQLQueryService(fuseki_endpoint=endpoint)
    result = service.execute_query_with_validation(query, timeout=timeout)
    
    if result.success:
        return result.data
    else:
        logger.error(f"Query failed: {result.error}")
        return None

# Global service instance for easy access
_default_service = None

def get_sparql_service(endpoint: str = "http://localhost:3030/smartcity/query") -> SPARQLQueryService:
    """
    Get or create a default SPARQL service instance.
    
    Args:
        endpoint: SPARQL endpoint URL
        
    Returns:
        SPARQLQueryService instance
    """
    global _default_service
    
    if _default_service is None or _default_service.fuseki_endpoint != endpoint:
        _default_service = SPARQLQueryService(fuseki_endpoint=endpoint)
    
    return _default_service