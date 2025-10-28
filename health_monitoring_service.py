"""
Health monitoring service for system status verification and performance monitoring.
Provides connectivity checks, data integrity validation, and system metrics.
"""

import time
import logging
import os
try:
    import psutil
except ImportError:
    # Fallback for systems without psutil
    class MockPsutil:
        @staticmethod
        def cpu_percent(interval=1):
            return 0.0
        @staticmethod
        def virtual_memory():
            class MockMemory:
                percent = 0.0
                total = 8 * 1024**3  # 8GB
                available = 4 * 1024**3  # 4GB
            return MockMemory()
        @staticmethod
        def disk_usage(path):
            class MockDisk:
                used = 100 * 1024**3  # 100GB
                total = 500 * 1024**3  # 500GB
                free = 400 * 1024**3  # 400GB
            return MockDisk()
    psutil = MockPsutil()
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
except ImportError:
    # Fallback for testing without SPARQLWrapper
    class SPARQLWrapper:
        def __init__(self, endpoint): pass
        def setQuery(self, query): pass
        def setReturnFormat(self, format): pass
        def setTimeout(self, timeout): pass
        def query(self): 
            class MockResult:
                def convert(self): return {"boolean": True, "results": {"bindings": []}}
            return MockResult()
    
    class SPARQLWrapperException(Exception): pass
    JSON = "json"

import requests
from sparql_service import SPARQLQueryService, ConnectionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    memory_total: float
    memory_available: float
    disk_usage: float
    disk_total: float
    disk_free: float
    uptime: float
    timestamp: float

@dataclass
class OntologyValidationResult:
    """Ontology data validation result"""
    is_valid: bool
    total_triples: Optional[int] = None
    class_count: Optional[int] = None
    property_count: Optional[int] = None
    individual_count: Optional[int] = None
    error_message: Optional[str] = None
    validation_time: Optional[float] = None

@dataclass
class HealthStatus:
    """Complete system health status"""
    overall_status: str  # "healthy", "degraded", "unhealthy"
    fuseki_connection: ConnectionStatus
    ontology_validation: OntologyValidationResult
    system_metrics: SystemMetrics
    timestamp: float
    errors: List[str]
    warnings: List[str]

class HealthMonitoringService:
    """
    Service for monitoring system health, Fuseki connectivity, and ontology data integrity.
    Provides comprehensive health checks and performance metrics.
    """
    
    def __init__(self, 
                 sparql_service: SPARQLQueryService,
                 ontology_namespace: str = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"):
        """
        Initialize the health monitoring service.
        
        Args:
            sparql_service: SPARQL service instance for connectivity checks
            ontology_namespace: Namespace URI for the ontology
        """
        self.sparql_service = sparql_service
        self.ontology_namespace = ontology_namespace
        self.start_time = time.time()
        
        logger.info("HealthMonitoringService initialized")
    
    def check_fuseki_connection(self) -> ConnectionStatus:
        """
        Verify Fuseki server connectivity and response time.
        
        Returns:
            ConnectionStatus with detailed connection information
        """
        logger.info("Checking Fuseki connection...")
        
        try:
            # Use the SPARQL service's connection check
            connection_status = self.sparql_service.check_fuseki_connection()
            
            if connection_status.is_connected:
                logger.info(f"Fuseki connection successful - Response time: {connection_status.response_time:.3f}s")
            else:
                logger.warning(f"Fuseki connection failed: {connection_status.error}")
            
            return connection_status
            
        except Exception as e:
            logger.error(f"Error checking Fuseki connection: {str(e)}")
            return ConnectionStatus(
                is_connected=False,
                endpoint_url=self.sparql_service.fuseki_endpoint,
                error=f"Connection check failed: {str(e)}",
                last_checked=time.time()
            )
    
    def validate_ontology_data(self) -> OntologyValidationResult:
        """
        Validate ontology data integrity and structure.
        
        Returns:
            OntologyValidationResult with validation details
        """
        logger.info("Validating ontology data...")
        start_time = time.time()
        
        try:
            # Query to count total triples
            total_triples_query = """
            SELECT (COUNT(*) as ?count)
            WHERE {
                ?s ?p ?o
            }
            """
            
            # Query to count classes
            class_count_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT (COUNT(DISTINCT ?class) as ?count)
            WHERE {{
                ?class rdf:type owl:Class
            }}
            """
            
            # Query to count properties
            property_count_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT (COUNT(DISTINCT ?property) as ?count)
            WHERE {{
                {{ ?property rdf:type owl:ObjectProperty }}
                UNION
                {{ ?property rdf:type owl:DatatypeProperty }}
            }}
            """
            
            # Query to count individuals
            individual_count_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT (COUNT(DISTINCT ?individual) as ?count)
            WHERE {{
                ?individual rdf:type ?class .
                FILTER(?class != owl:Class)
                FILTER(?class != owl:ObjectProperty)
                FILTER(?class != owl:DatatypeProperty)
                FILTER(!STRSTARTS(STR(?class), "http://www.w3.org/"))
            }}
            """
            
            # Execute validation queries
            total_triples = self._execute_count_query(total_triples_query)
            class_count = self._execute_count_query(class_count_query)
            property_count = self._execute_count_query(property_count_query)
            individual_count = self._execute_count_query(individual_count_query)
            
            validation_time = time.time() - start_time
            
            # Validate that we have reasonable data
            is_valid = (
                total_triples is not None and total_triples > 0 and
                class_count is not None and class_count > 0
            )
            
            if is_valid:
                logger.info(f"Ontology validation successful - Triples: {total_triples}, Classes: {class_count}, Properties: {property_count}, Individuals: {individual_count}")
            else:
                logger.warning("Ontology validation failed - insufficient data")
            
            return OntologyValidationResult(
                is_valid=is_valid,
                total_triples=total_triples,
                class_count=class_count,
                property_count=property_count,
                individual_count=individual_count,
                validation_time=validation_time
            )
            
        except Exception as e:
            validation_time = time.time() - start_time
            error_msg = f"Ontology validation error: {str(e)}"
            logger.error(error_msg)
            
            return OntologyValidationResult(
                is_valid=False,
                error_message=error_msg,
                validation_time=validation_time
            )
    
    def _execute_count_query(self, query: str) -> Optional[int]:
        """Execute a count query and return the result"""
        try:
            result = self.sparql_service.execute_query_with_validation(query, validate=False)
            
            if result.success and result.data:
                bindings = result.data.get("results", {}).get("bindings", [])
                if bindings and "count" in bindings[0]:
                    return int(bindings[0]["count"]["value"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing count query: {str(e)}")
            return None
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Collect system performance metrics.
        
        Returns:
            SystemMetrics with current system performance data
        """
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_total = memory.total / (1024**3)  # GB
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            disk_total = disk.total / (1024**3)  # GB
            disk_free = disk.free / (1024**3)  # GB
            
            # System uptime
            uptime = time.time() - self.start_time
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                memory_total=memory_total,
                memory_available=memory_available,
                disk_usage=disk_usage,
                disk_total=disk_total,
                disk_free=disk_free,
                uptime=uptime,
                timestamp=time.time()
            )
            
            logger.debug(f"System metrics collected - CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            # Return default metrics on error
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                memory_total=0.0,
                memory_available=0.0,
                disk_usage=0.0,
                disk_total=0.0,
                disk_free=0.0,
                uptime=time.time() - self.start_time,
                timestamp=time.time()
            )
    
    def perform_health_check(self) -> HealthStatus:
        """
        Perform comprehensive system health check.
        
        Returns:
            HealthStatus with complete system status information
        """
        logger.info("Performing comprehensive health check...")
        start_time = time.time()
        
        errors = []
        warnings = []
        
        # Check Fuseki connection
        fuseki_connection = self.check_fuseki_connection()
        if not fuseki_connection.is_connected:
            errors.append(f"Fuseki connection failed: {fuseki_connection.error}")
        elif fuseki_connection.response_time and fuseki_connection.response_time > 5.0:
            warnings.append(f"Fuseki response time is slow: {fuseki_connection.response_time:.2f}s")
        
        # Validate ontology data
        ontology_validation = self.validate_ontology_data()
        if not ontology_validation.is_valid:
            errors.append(f"Ontology validation failed: {ontology_validation.error_message}")
        elif ontology_validation.total_triples and ontology_validation.total_triples < 100:
            warnings.append(f"Low number of triples in ontology: {ontology_validation.total_triples}")
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        if system_metrics.cpu_usage > 90:
            warnings.append(f"High CPU usage: {system_metrics.cpu_usage}%")
        if system_metrics.memory_usage > 90:
            warnings.append(f"High memory usage: {system_metrics.memory_usage}%")
        if system_metrics.disk_usage > 90:
            warnings.append(f"High disk usage: {system_metrics.disk_usage}%")
        
        # Determine overall status
        if errors:
            overall_status = "unhealthy"
        elif warnings:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        health_status = HealthStatus(
            overall_status=overall_status,
            fuseki_connection=fuseki_connection,
            ontology_validation=ontology_validation,
            system_metrics=system_metrics,
            timestamp=time.time(),
            errors=errors,
            warnings=warnings
        )
        
        check_time = time.time() - start_time
        logger.info(f"Health check completed in {check_time:.3f}s - Status: {overall_status}")
        
        return health_status

# Global health monitoring service instance
_health_service = None

def get_health_monitoring_service(sparql_service: SPARQLQueryService) -> HealthMonitoringService:
    """
    Get or create a health monitoring service instance.
    
    Args:
        sparql_service: SPARQL service instance
        
    Returns:
        HealthMonitoringService instance
    """
    global _health_service
    
    if _health_service is None:
        _health_service = HealthMonitoringService(sparql_service)
    
    return _health_service