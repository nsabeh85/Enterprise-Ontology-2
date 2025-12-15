"""
Disambiguation Rules
Handles ambiguous terms using context keywords.
"""

import re

class Disambiguator:
    def __init__(self):
        """Initialize with ambiguous terms and their indicators"""
        self.ambiguous_terms = {
            'fabric': {
                'meanings': {
                    'ServiceFabric': {
                        'type': 'product',
                        'indicators': ['sf', 'virtual', 'interconnect', 'cloud', 'service', 'available', 'pricing'],
                        'indexes': ['service-fabric-index']
                    }
                }
            },
            'capacity': {
                'meanings': {
                    'power_capacity': {
                        'type': 'power',
                        'indicators': ['power', 'kw', 'mw', 'electrical', 'watt', 'kilowatt', 'megawatt', 'generator'],
                        'indexes': ['additional-properties']
                    },
                    'space_capacity': {
                        'type': 'space',
                        'indicators': ['rack', 'cage', 'cabinet', 'square', 'feet', 'space', 'sqft'],
                        'indexes': ['additional-properties']
                    }
                }
            }
        }
    
    def get_disambiguation_context(self, query: str) -> dict:
        """
        Analyze query and return disambiguation hints
        Returns all possible meanings for multi-index search
        """
        query_lower = query.lower()
        context = {}
        
        for term, config in self.ambiguous_terms.items():
            if term in query_lower:
                result = {
                    'found': True,
                    'all_meanings': list(config['meanings'].keys()),
                    'indexes': []
                }
                
                # Score each meaning based on context indicators
                scores = {}
                for meaning_name, meaning_config in config['meanings'].items():
                    score = 0
                    for indicator in meaning_config['indicators']:
                        if indicator in query_lower:
                            score += 1
                    scores[meaning_name] = score
                    result['indexes'].extend(meaning_config['indexes'])
                
                result['indexes'] = list(set(result['indexes']))
                
                # Determine likely meaning
                if scores:
                    likely = max(scores, key=scores.get)
                    result['likely_meaning'] = likely if scores[likely] > 0 else None
                else:
                    result['likely_meaning'] = None
                
                result['scores'] = scores
                context[term] = result
        
        return context

if __name__ == "__main__":
    print("Testing Disambiguator...\n")
    disambiguator = Disambiguator()
    
    test_queries = [
        "What's the fabric topology?",
        "Is ServiceFabric available?",
        "What's the power capacity?"
    ]
    
    for query in test_queries:
        context = disambiguator.get_disambiguation_context(query)
        print(f"Query: '{query}'")
        if context:
            for term, info in context.items():
                print(f"  '{term}' → {info.get('likely_meaning', 'unclear')}")
        print()