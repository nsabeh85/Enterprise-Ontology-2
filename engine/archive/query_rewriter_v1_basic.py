"""
Query Rewriter v1 - Basic Version

Core query expansion engine without performance tracking, telemetry, or disambiguation.
Those features will be added in v2 after building the supporting components.
"""

import json
import re


def load_lexicon(lexicon_path='data/ontology_runtime.json'):
    """
    Load the ontology runtime artifact
    
    Args:
        lexicon_path: Path to JSON runtime artifact
    
    Returns:
        Dictionary with entities
    """
    try:
        with open(lexicon_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Lexicon file not found at {lexicon_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in lexicon: {e}")
        return None


def rewrite_query(user_input: str, lexicon: dict) -> dict:
    """
    Expand user query with synonyms and related terms
    
    Process:
    1. Normalize query (lowercase)
    2. Match canonical entity names
    3. Match synonyms
    4. Expand with synonyms (weight 0.8)
    5. Add related terms (weight 0.6, max 3)
    6. Limit to 8 expansions
    
    Args:
        user_input: Original user query string
        lexicon: Loaded ontology runtime artifact
    
    Returns:
        {
            'original_query': str,
            'matched_entities': list[str],
            'expanded_terms': list[dict],
            'expansion_count': int
        }
    """
    # Validate inputs
    if not user_input or not user_input.strip():
        return {
            'original_query': user_input,
            'matched_entities': [],
            'expanded_terms': [],
            'expansion_count': 0
        }
    
    if not lexicon or 'entities' not in lexicon:
        return {
            'original_query': user_input,
            'matched_entities': [],
            'expanded_terms': [],
            'expansion_count': 0
        }
    
    # 1. Normalize query
    query_lower = user_input.lower()
    
    # 2. Match canonical entity names
    matched_entities = []
    
    for entity_name, entity_data in lexicon['entities'].items():
        entity_lower = entity_name.lower()
        
        # Use word boundaries to avoid false matches
        pattern = r'\b' + re.escape(entity_lower) + r'\b'
        
        if re.search(pattern, query_lower):
            matched_entities.append(entity_name)
    
    # 3. Match synonyms
    for entity_name, entity_data in lexicon['entities'].items():
        if entity_name in matched_entities:
            continue  # Already matched
        
        synonyms = entity_data.get('synonyms', [])
        for syn in synonyms:
            syn_lower = syn.lower()
            pattern = r'\b' + re.escape(syn_lower) + r'\b'
            
            if re.search(pattern, query_lower):
                matched_entities.append(entity_name)
                break  # Stop after first synonym match
    
    # 4. Expand with synonyms and related terms
    expanded_terms = []
    
    for entity_name in matched_entities:
        entity_data = lexicon['entities'][entity_name]
        
        # Add canonical term (weight 1.0)
        expanded_terms.append({
            'term': entity_name,
            'weight': 1.0,
            'source': 'canonical'
        })
        
        # Add synonyms (weight 0.8)
        for syn in entity_data.get('synonyms', []):
            expanded_terms.append({
                'term': syn,
                'weight': 0.8,
                'source': 'synonym'
            })
        
        # Add related terms (weight 0.6, max 3 per entity)
        for related in entity_data.get('related_terms', [])[:3]:
            expanded_terms.append({
                'term': related,
                'weight': 0.6,
                'source': 'related'
            })
    
    # 5. Limit to 8 expansions (Phase 2 requirement)
    if len(expanded_terms) > 8:
        expanded_terms = expanded_terms[:8]
    
    return {
        'original_query': user_input,
        'matched_entities': matched_entities,
        'expanded_terms': expanded_terms,
        'expansion_count': len(expanded_terms)
    }


# Test function when run directly
if __name__ == "__main__":
    print("Testing query_rewriter v1 (basic)...\n")
    
    # Load lexicon
    lexicon = load_lexicon()
    
    if not lexicon:
        print("Failed to load lexicon")
        exit(1)
    
    print(f"Loaded {len(lexicon['entities'])} entities\n")
    
    # Test queries
    test_queries = [
        "Is SF available at DFW10?",
        "Tell me about colocation",
        "What's the capacity?",
    ]
    
    for query in test_queries:
        result = rewrite_query(query, lexicon)
        print(f"Query: {query}")
        print(f"Matched: {result['matched_entities']}")
        print(f"Expansions: {result['expansion_count']}")
        if result['expansion_count'] > 0:
            print("Top 3 terms:")
            for term in result['expanded_terms'][:3]:
                print(f"  - {term['term']} (weight: {term['weight']})")
        print()