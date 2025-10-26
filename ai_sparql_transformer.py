import re
from typing import Dict, List

class SimpleSPARQLTransformer:
    def __init__(self):
        # Patterns de questions avec regex simples
        self.patterns = {
            'all_persons': {
                'patterns': [
                    r'.*(tous|tout|liste|affiche).*(personne|gens|utilisateur)',
                    r'.*(montre|donne).*(personne|gens)',
                    r'^qui.*$'
                ],
                'template': """
                PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?person ?name ?type WHERE {
                    ?person rdf:type :Person .
                    OPTIONAL { ?person :hasName ?name . }
                    OPTIONAL {
                        ?person rdf:type ?type .
                        FILTER(?type != :Person)
                    }
                }
                """
            },
            'search_by_name': {
                'patterns': [
                    r'.*(trouve|cherche|recherche).*',
                    r'.*(qui est|qui s\'appelle).*',
                    r'.*(donne|montre).*(information|détail).*'
                ],
                'template': """
                PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?person ?name ?type WHERE {
                    ?person rdf:type :Person .
                    ?person :hasName ?name .
                    FILTER regex(?name, "{name}", "i")
                    OPTIONAL {
                        ?person rdf:type ?type .
                        FILTER(?type != :Person)
                    }
                }
                """
            },
            'by_person_type': {
                'patterns': [
                    r'.*(citoyen|citoyens|habitant)',
                    r'.*(staff|employé|employés)',
                    r'.*(touriste|touristes|visiteur)'
                ],
                'template': """
                PREFIX : <http://www.semanticweb.org/monpc/ontologies/2025/9/untitled-ontology-4#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?person ?name ?type WHERE {
                    ?person rdf:type :Person .
                    ?person :hasName ?name .
                    ?person rdf:type :{person_type} .
                    OPTIONAL {
                        ?person rdf:type ?other_type .
                        FILTER(?other_type != :Person && ?other_type != :{person_type})
                    }
                }
                """
            }
        }
        
        # Mapping des types
        self.type_mapping = {
            'citoyen': 'Citizen', 'citoyens': 'Citizen', 'habitant': 'Citizen',
            'staff': 'Staff', 'employé': 'Staff', 'employés': 'Staff',
            'touriste': 'Tourist', 'touristes': 'Tourist', 'visiteur': 'Tourist'
        }
        
        # Noms communs pour l'extraction
        self.common_names = ['alice', 'bob', 'charlie', 'david', 'eve', 'frank', 'grace']

    def extract_name(self, question: str) -> str:
        """Extrait un nom potentiel de la question"""
        question_lower = question.lower()
        
        # Cherche des noms propres (mots avec majuscules entourés d'espaces)
        words = question.split()
        for word in words:
            if word.istitle() and len(word) > 2 and word.lower() not in ['qui', 'quel', 'quelle', 'quels', 'quelles']:
                return word
        
        # Cherche dans les noms communs
        for name in self.common_names:
            if name in question_lower:
                return name.capitalize()
        
        # Cherche après "qui est" ou "qui s'appelle"
        patterns = [
            r'qui est (.+?)(?:\?|$|\.)',
            r'qui s\'appelle (.+?)(?:\?|$|\.)',
            r'trouve (.+?)(?:\?|$|\.)',
            r'cherche (.+?)(?:\?|$|\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                return match.group(1).strip().capitalize()
        
        return ""

    def extract_person_type(self, question: str) -> str:
        """Extrait le type de personne de la question"""
        question_lower = question.lower()
        
        for fr_type, en_type in self.type_mapping.items():
            if fr_type in question_lower:
                return en_type
        
        return ""

    def classify_question(self, question: str) -> str:
        """Classifie le type de question"""
        question_lower = question.lower()
        
        for q_type, pattern_data in self.patterns.items():
            for pattern in pattern_data['patterns']:
                if re.search(pattern, question_lower):
                    return q_type
        
        return 'all_persons'  # Par défaut

    def generate_sparql(self, question: str) -> str:
        """Génère une requête SPARQL à partir d'une question naturelle"""
        question_type = self.classify_question(question)
        
        if question_type == 'search_by_name':
            name = self.extract_name(question)
            if name:
                return self.patterns['search_by_name']['template'].format(name=name)
            else:
                # Si pas de nom trouvé, retourne toutes les personnes
                return self.patterns['all_persons']['template']
        
        elif question_type == 'by_person_type':
            person_type = self.extract_person_type(question)
            if person_type:
                return self.patterns['by_person_type']['template'].format(person_type=person_type)
            else:
                return self.patterns['all_persons']['template']
        
        else:
            return self.patterns['all_persons']['template']

# Instance globale
sparql_transformer = SimpleSPARQLTransformer()

# Test de la transformation
if __name__ == "__main__":
    test_questions = [
        "Qui sont toutes les personnes ?",
        "Trouve Alice",
        "Montre-moi les citoyens",
        "Qui est Bob Martin ?",
        "Liste le staff"
    ]
    
    for question in test_questions:
        sparql = sparql_transformer.generate_sparql(question)
        print(f"Question: {question}")
        print(f"SPARQL: {sparql}")
        print("-" * 50)