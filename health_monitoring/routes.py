"""
Health Monitoring API Routes
Provides REST endpoints for system health checks, Fuseki connectivity verification, 
and ontology loading status monitoring.
"""

from flask import Blueprint, jsonify
from health_monitoring_service import HealthMonitoringService, get_health_monitoring_service
from sparql_service import get_sparql_service
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for health monitoring routes
router = Blueprint('health_monitoring', __name__)

# Fuseki endpoint configuration
FUSEKI_ENDPOINT = "http://localhost:3030/smartcity/query"

@router.route('/health', methods=['GET'])
def system_health_check():
    """
    GET /api/health
    Comprehensive system health check endpoint for monitoring system status.
    
    Returns:
        JSON response with:
        - Overall system status (healthy/degraded/unhealthy)
        - Fuseki connectivity and response time metrics
        - Ontology loading status verification
        - System performance metrics
        - Detailed error and warning information
    """
    try:
        logger.info("Performing comprehensive system health check")
        
        # Get SPARQL service instance
        sparql_service = get_sparql_service(FUSEKI_ENDPOINT)
        
        # Get health monitoring service instance
        health_service = get_health_monitoring_service(sparql_service)
        
        # Perform comprehensive health check
        health_status = health_service.perform_health_check()
        
        # Format response
        response = {
            "status": health_status.overall_status,
            "timestamp": datetime.fromtimestamp(health_status.timestamp).isoformat(),
            "fuseki": {
                "connected": health_status.fuseki_connection.is_connected,
                "endpoint": health_status.fuseki_connection.endpoint_url,
                "responseTime": health_status.fuseki_connection.response_time,
                "lastChecked": datetime.fromtimestamp(health_status.fuseki_connection.last_checked).isoformat() if health_status.fuseki_connection.last_checked else None,
                "error": health_status.fuseki_connection.error
            },
            "ontology": {
                "valid": health_status.ontology_validation.is_valid,
                "totalTriples": health_status.ontology_validation.total_triples,
                "classCount": health_status.ontology_validation.class_count,
                "propertyCount": health_status.ontology_validation.property_count,
                "individualCount": health_status.ontology_validation.individual_count,
                "validationTime": health_status.ontology_validation.validation_time,
                "error": health_status.ontology_validation.error_message
            },
            "system": {
                "cpuUsage": health_status.system_metrics.cpu_usage,
                "memoryUsage": health_status.system_metrics.memory_usage,
                "memoryTotal": round(health_status.system_metrics.memory_total, 2),
                "memoryAvailable": round(health_status.system_metrics.memory_available, 2),
                "diskUsage": health_status.system_metrics.disk_usage,
                "diskTotal": round(health_status.system_metrics.disk_total, 2),
                "diskFree": round(health_status.system_metrics.disk_free, 2),
                "uptime": round(health_status.system_metrics.uptime, 2)
            },
            "issues": {
                "errors": health_status.errors,
                "warnings": health_status.warnings
            }
        }
        
        # Set appropriate HTTP status code
        if health_status.overall_status == "healthy":
            status_code = 200
        elif health_status.overall_status == "degraded":
            status_code = 200  # Still operational but with warnings
        else:  # unhealthy
            status_code = 503  # Service unavailable
        
        logger.info(f"Health check completed - Status: {health_status.overall_status}")
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Health check endpoint error: {str(e)}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": f"Health check failed: {str(e)}",
            "fuseki": {
                "connected": False,
                "endpoint": FUSEKI_ENDPOINT,
                "error": "Health check service unavailable"
            }
        }), 500

@router.route('/health/fuseki', methods=['GET'])
def fuseki_health_check():
    """
    GET /api/health/fuseki
    Specific Fuseki connectivity health check.
    
    Returns:
        JSON response with detailed Fuseki connection status and metrics
    """
    try:
        logger.info("Checking Fuseki connectivity")
        
        # Get SPARQL service instance
        sparql_service = get_sparql_service(FUSEKI_ENDPOINT)
        
        # Get health monitoring service instance
        health_service = get_health_monitoring_service(sparql_service)
        
        # Check Fuseki connection
        connection_status = health_service.check_fuseki_connection()
        
        response = {
            "service": "fuseki",
            "connected": connection_status.is_connected,
            "endpoint": connection_status.endpoint_url,
            "responseTime": connection_status.response_time,
            "lastChecked": datetime.fromtimestamp(connection_status.last_checked).isoformat() if connection_status.last_checked else None,
            "error": connection_status.error,
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if connection_status.is_connected else 503
        
        logger.info(f"Fuseki health check - Connected: {connection_status.is_connected}")
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Fuseki health check error: {str(e)}")
        return jsonify({
            "service": "fuseki",
            "connected": False,
            "endpoint": FUSEKI_ENDPOINT,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@router.route('/health/ontology', methods=['GET'])
def ontology_health_check():
    """
    GET /api/health/ontology
    Specific ontology data validation and integrity check.
    
    Returns:
        JSON response with ontology loading status and data integrity metrics
    """
    try:
        logger.info("Validating ontology data integrity")
        
        # Get SPARQL service instance
        sparql_service = get_sparql_service(FUSEKI_ENDPOINT)
        
        # Get health monitoring service instance
        health_service = get_health_monitoring_service(sparql_service)
        
        # Validate ontology data
        validation_result = health_service.validate_ontology_data()
        
        response = {
            "service": "ontology",
            "valid": validation_result.is_valid,
            "totalTriples": validation_result.total_triples,
            "classCount": validation_result.class_count,
            "propertyCount": validation_result.property_count,
            "individualCount": validation_result.individual_count,
            "validationTime": validation_result.validation_time,
            "error": validation_result.error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if validation_result.is_valid else 503
        
        logger.info(f"Ontology validation - Valid: {validation_result.is_valid}")
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Ontology health check error: {str(e)}")
        return jsonify({
            "service": "ontology",
            "valid": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@router.route('/health/system', methods=['GET'])
def system_metrics_check():
    """
    GET /api/health/system
    System performance metrics endpoint.
    
    Returns:
        JSON response with current system performance metrics including CPU, memory, and disk usage
    """
    try:
        logger.info("Collecting system performance metrics")
        
        # Get SPARQL service instance
        sparql_service = get_sparql_service(FUSEKI_ENDPOINT)
        
        # Get health monitoring service instance
        health_service = get_health_monitoring_service(sparql_service)
        
        # Get system metrics
        system_metrics = health_service.get_system_metrics()
        
        response = {
            "service": "system",
            "metrics": {
                "cpu": {
                    "usage": system_metrics.cpu_usage,
                    "unit": "percent"
                },
                "memory": {
                    "usage": system_metrics.memory_usage,
                    "total": round(system_metrics.memory_total, 2),
                    "available": round(system_metrics.memory_available, 2),
                    "unit": "GB"
                },
                "disk": {
                    "usage": system_metrics.disk_usage,
                    "total": round(system_metrics.disk_total, 2),
                    "free": round(system_metrics.disk_free, 2),
                    "unit": "GB"
                },
                "uptime": {
                    "seconds": round(system_metrics.uptime, 2),
                    "formatted": f"{int(system_metrics.uptime // 3600)}h {int((system_metrics.uptime % 3600) // 60)}m"
                }
            },
            "timestamp": datetime.fromtimestamp(system_metrics.timestamp).isoformat()
        }
        
        logger.info(f"System metrics collected - CPU: {system_metrics.cpu_usage}%")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"System metrics error: {str(e)}")
        return jsonify({
            "service": "system",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500