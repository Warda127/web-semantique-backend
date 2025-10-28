"""
OntologySearchService - Handles general ontology concept search functionality.
Extends existing person search capabilities to cover the complete WebSemEsprit ontology.
"""

import re
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
class SearchResult:
    """Represents a search result from ontology concept search"""
    uri: str
    label: str
    class_type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

@dataclass
class ClassInfo:
    """Represents information about an ontology class"""
    uri: str
    label: str
    parent_class: Optional[str] = None
    subclasses: Optional[List[str]] = None
    properties: Optional[List[str]] = None

@dataclass
class HierarchyNode:
    """Represents a node in the class hierarchy tree"""
    uri: str
    label: str
    children: List['HierarchyNode']
    parent: Optional[str] = None

class OntologySearchService:
    """
    Service for searching and exploring ontology concepts.
    Provides keyword-based search, class listings, and hierarchy exploration.
    """
    
    def __init__(self, fuseki_endpoint: str = "http://localhost:3030/smartcity/query"):
        """
        Initialize the ontology search service.
        
        Args:
            fuseki_endpoint: SPARQL endpoint URL for ontology queries
        """
        self.fuseki_endpoint = fuseki_endpoint
        self.sparql_service = get_sparql_service(fuseki_endpoint)
        self.ontology_namespace = "http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#"
        
        logger.info(f"OntologySearchService initialized with endpoint: {fuseki_endpoint}")
    
    def search_concepts_by_keyword(self, keyword: str) -> List[SearchResult]:
        """
        Search for ontology concepts by keyword with case-insensitive partial matching.
        
        Args:
            keyword: Search keyword to match against entity labels
            
        Returns:
            List of SearchResult objects matching the keyword
        """
        if not keyword or not keyword.strip():
            # Return all available classes when no keyword provided
            return self._get_all_concepts()
        
        keyword = keyword.strip()
        
        # SPARQL query for keyword-based concept search
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?concept ?label ?type
WHERE {{
    ?concept rdf:type ?type .
    OPTIONAL {{ ?concept rdfs:label ?label . }}
    OPTIONAL {{ ?concept :hasName ?label . }}
    FILTER(
        regex(str(?concept), "{keyword}", "i") ||
        regex(str(?label), "{keyword}", "i")
    )
}}
ORDER BY ?concept
LIMIT 50"""
        
        logger.info(f"Executing search query for keyword: {keyword}")
        
        # Use direct SPARQLWrapper to avoid validation issues
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            search_results = []
            for binding in results.get("results", {}).get("bindings", []):
                search_result = SearchResult(
                    uri=binding["concept"]["value"],
                    label=binding.get("label", {}).get("value", self._extract_local_name(binding["concept"]["value"])),
                    class_type=binding.get("type", {}).get("value", "Unknown")
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} concepts matching keyword '{keyword}'")
            return search_results
            
        except Exception as e:
            logger.error(f"Direct SPARQL execution failed: {str(e)}")
            return []

    
    def get_all_classes(self) -> List[ClassInfo]:
        """
        Retrieve complete class listings from the ontology.
        
        Returns:
            List of ClassInfo objects representing all ontology classes
        """
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?class ?label ?parent ?comment
WHERE {{
            ?class rdf:type rdfs:Class .
            OPTIONAL {{ ?class rdfs:label ?label . }}
            OPTIONAL {{ ?class rdfs:subClassOf ?parent . }}
            OPTIONAL {{ ?class rdfs:comment ?comment . }}
            
            # Filter out system classes
            FILTER(!strstarts(str(?class), "http://www.w3.org/2000/01/rdf-schema"))
            FILTER(!strstarts(str(?class), "http://www.w3.org/1999/02/22-rdf-syntax-ns"))
            FILTER(!strstarts(str(?class), "http://www.w3.org/2002/07/owl#"))
        }}
ORDER BY ?class"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            classes = []
            for binding in results.get("results", {}).get("bindings", []):
                class_info = ClassInfo(
                    uri=binding["class"]["value"],
                    label=binding.get("label", {}).get("value", self._extract_local_name(binding["class"]["value"])),
                    parent_class=binding.get("parent", {}).get("value")
                )
                classes.append(class_info)
            
            # Get subclasses for each class
            for class_info in classes:
                class_info.subclasses = self._get_subclasses(class_info.uri)
            
            logger.info(f"Retrieved {len(classes)} ontology classes")
            return classes
            
        except Exception as e:
            logger.error(f"Get all classes failed: {str(e)}")
            return []
    
    def get_class_hierarchy(self) -> Dict[str, Any]:
        """
        Get hierarchical class relationships as a nested tree structure.
        
        Returns:
            Dictionary representing the class hierarchy tree
        """
        # Get all classes with their parent relationships
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?class ?label ?parent ?parentLabel
WHERE {{
            ?class rdf:type rdfs:Class .
            OPTIONAL {{ ?class rdfs:label ?label . }}
            OPTIONAL {{ 
                ?class rdfs:subClassOf ?parent .
                ?parent rdf:type rdfs:Class .
                OPTIONAL {{ ?parent rdfs:label ?parentLabel . }}
            }}
            
            # Filter out system classes
            FILTER(!strstarts(str(?class), "http://www.w3.org/2000/01/rdf-schema"))
            FILTER(!strstarts(str(?class), "http://www.w3.org/1999/02/22-rdf-syntax-ns"))
            FILTER(!strstarts(str(?class), "http://www.w3.org/2002/07/owl#"))
        }}
ORDER BY ?parent ?class"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
        except Exception as e:
            logger.error(f"Get class hierarchy failed: {str(e)}")
            return {"hierarchy": [], "error": str(e)}
        
        # Build hierarchy tree
        nodes = {}
        root_nodes = []
        
        for binding in results.get("results", {}).get("bindings", []):
            class_uri = binding["class"]["value"]
            class_label = binding.get("label", {}).get("value", self._extract_local_name(class_uri))
            parent_uri = binding.get("parent", {}).get("value")
            
            # Create node if it doesn't exist
            if class_uri not in nodes:
                nodes[class_uri] = HierarchyNode(
                    uri=class_uri,
                    label=class_label,
                    children=[],
                    parent=parent_uri
                )
            
            # Update parent reference
            nodes[class_uri].parent = parent_uri
            
            # Create parent node if it doesn't exist and is within our ontology
            if parent_uri and parent_uri.startswith(self.ontology_namespace):
                if parent_uri not in nodes:
                    parent_label = binding.get("parentLabel", {}).get("value", self._extract_local_name(parent_uri))
                    nodes[parent_uri] = HierarchyNode(
                        uri=parent_uri,
                        label=parent_label,
                        children=[],
                        parent=None
                    )
        
        # Build parent-child relationships
        for node in nodes.values():
            if node.parent and node.parent in nodes:
                nodes[node.parent].children.append(node)
            else:
                # Root node (no parent or parent outside our ontology)
                root_nodes.append(node)
        
        # Convert to serializable format
        def node_to_dict(node: HierarchyNode) -> Dict[str, Any]:
            return {
                "uri": node.uri,
                "label": node.label,
                "children": [node_to_dict(child) for child in node.children]
            }
        
        hierarchy = [node_to_dict(node) for node in root_nodes]
        
        logger.info(f"Built class hierarchy with {len(nodes)} nodes and {len(root_nodes)} root classes")
        return {
            "hierarchy": hierarchy,
            "total_classes": len(nodes),
            "root_classes": len(root_nodes)
        }
    
    def _get_all_concepts(self) -> List[SearchResult]:
        """Get all available concepts when no keyword is provided"""
        query = f"""PREFIX : <{self.ontology_namespace}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?concept ?label ?type
WHERE {{
    ?concept rdf:type ?type .
    OPTIONAL {{ ?concept rdfs:label ?label . }}
    OPTIONAL {{ ?concept :hasName ?label . }}
    FILTER(!strstarts(str(?concept), "http://www.w3.org/2000/01/rdf-schema"))
    FILTER(!strstarts(str(?concept), "http://www.w3.org/1999/02/22-rdf-syntax-ns"))
    FILTER(!strstarts(str(?concept), "http://www.w3.org/2002/07/owl#"))
}}
ORDER BY ?concept
LIMIT 100"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            concepts = []
            for binding in results.get("results", {}).get("bindings", []):
                concept = SearchResult(
                    uri=binding["concept"]["value"],
                    label=binding.get("label", {}).get("value", self._extract_local_name(binding["concept"]["value"])),
                    class_type=binding.get("type", {}).get("value", "Unknown")
                )
                concepts.append(concept)
            
            return concepts
            
        except Exception as e:
            logger.error(f"Get all concepts failed: {str(e)}")
            return []
    
    def _get_subclasses(self, class_uri: str) -> List[str]:
        """Get direct subclasses of a given class"""
        query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?subclass
WHERE {{
    ?subclass rdfs:subClassOf <{class_uri}> .
}}"""
        
        try:
            sparql = SPARQLWrapper(self.fuseki_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            subclasses = []
            for binding in results.get("results", {}).get("bindings", []):
                subclasses.append(binding["subclass"]["value"])
            
            return subclasses
            
        except Exception as e:
            logger.error(f"Get subclasses failed: {str(e)}")
            return []
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI for display purposes"""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri