"""
Query Rewriter v2 - Enhanced Version

Combines all components:
- Basic query expansion (from v1)
- Performance monitoring
- Telemetry logging
- Disambiguation
- Enhanced normalization

Version: 0.2.0
Last Updated: 2025-11-21
Changes: Added enhanced normalization (whitespace, punctuation removal)
"""

import json
import re
import time
from performance_monitor import PerformanceMonitor
from telemetry_logger import TelemetryLogger
from disambiguation_rules import Disambiguator

__version__ = "0.2.0"

# Global instances
_monitor = PerformanceMonitor()
_telemetry = TelemetryLogger()
_disambiguator = Disambiguator()


def load_lexicon(lexicon_path='data/ontology_runtime.json'):
    """Load the ontology runtime artifact"""
    try:
        with open(lexicon_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Lexicon file not found at {lexicon_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in lexicon: {e}")
        return None


def normalize_query(user_input: str) -> str:
    """
    Enhanced query normalization
    
    Process:
    1. Lowercase
    2. Strip leading/trailing whitespace
    3. Normalize multiple spaces to single space
    4. Remove punctuation (except hyphens and spaces)
    
    Args:
        user_input: Original query string
    
    Returns:
        Normalized query string
    
    Examples:
        "  Is  SF   available???  " -> "is sf available"
        "What's the capacity?" -> "whats the capacity"
    """
    query = user_input.lower()
    query = query.strip()
    query = ' '.join(query.split())
    query = re.sub(r'[^\w\s-]', '', query)
    return query


def rewrite_query(user_input: str, 
                  lexicon: dict,
                  track_performance=False,
                  log_telemetry=False,
                  use_disambiguation=True,
                  user_id='anonymous') -> dict:
    """
    Enhanced query rewriting with all features
    
    Args:
        user_input: Original user query
        lexicon: Loaded ontology runtime artifact
        track_performance: Enable performance monitoring
        log_telemetry: Enable telemetry logging
        use_disambiguation: Enable disambiguation
        user_id: User identifier (hashed if logging enabled)
    
    Returns:
        {
            'original_query': str,
            'matched_entities': list,
            'expanded_terms': list,
            'expansion_count': int,
            'disambiguation_context': dict (if enabled),
            'performance': dict (if tracking),
            'query_id': str (if logging)
        }
    """
    start_time = time.time()
    
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
    
    # 1. Get disambiguation context
    disambiguation_context = {}
    if use_disambiguation:
        disambiguation_context = _disambiguator.get_disambiguation_context(user_input)
    
    # 2. Enhanced normalization
    query_lower = normalize_query(user_input)
    
    # 3. Match canonical entity names
    matched_entities = []
    for entity_name, entity_data in lexicon['entities'].items():
        entity_lower = entity_name.lower()
        pattern = r'\b' + re.escape(entity_lower) + r'\b'
        
        if re.search(pattern, query_lower):
            matched_entities.append(entity_name)
    
    # 4. Match synonyms
    for entity_name, entity_data in lexicon['entities'].items():
        if entity_name in matched_entities:
            continue
        
        synonyms = entity_data.get('synonyms', [])
        for syn in synonyms:
            syn_lower = syn.lower()
            pattern = r'\b' + re.escape(syn_lower) + r'\b'
            
            if re.search(pattern, query_lower):
                matched_entities.append(entity_name)
                break
    
    # 5. Expand with synonyms and related terms
    expanded_terms = []
    for entity_name in matched_entities:
        entity_data = lexicon['entities'][entity_name]
        
        # Canonical (1.0)
        expanded_terms.append({
            'term': entity_name,
            'weight': 1.0,
            'source': 'canonical'
        })
        
        # Synonyms (0.8)
        for syn in entity_data.get('synonyms', []):
            expanded_terms.append({
                'term': syn,
                'weight': 0.8,
                'source': 'synonym'
            })
        
        # Related terms (0.6, max 3)
        for related in entity_data.get('related_terms', [])[:3]:
            expanded_terms.append({
                'term': related,
                'weight': 0.6,
                'source': 'related'
            })
    
    # 6. Limit to 8 expansions
    if len(expanded_terms) > 8:
        expanded_terms = expanded_terms[:8]
    
    # Calculate timing
    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    
    # 7. Track performance
    if track_performance:
        _monitor.record('query_rewrite', total_time_ms)
    
    # Build result
    result = {
        'original_query': user_input,
        'matched_entities': matched_entities,
        'expanded_terms': expanded_terms,
        'expansion_count': len(expanded_terms),
        'disambiguation_context': disambiguation_context
    }
    
    if track_performance:
        result['performance'] = {
            'total_time_ms': round(total_time_ms, 2)
        }
    
    # 8. Log telemetry
    if log_telemetry:
        query_id = _telemetry.generate_query_id()
        _telemetry.log_query(
            query_id=query_id,
            user_id=user_id,
            original_query=user_input,
            rewritten_query=result,
            performance={'time_ms': total_time_ms},
            metadata={'has_disambiguation': bool(disambiguation_context)}
        )
        result['query_id'] = query_id
    
    return result


def get_performance_report():
    """Get performance statistics"""
    return _monitor.get_stats()


def print_performance_report():
    """Print formatted performance report"""
    stats = _monitor.get_stats('query_rewrite')
    if stats:
        print("\nPerformance Statistics:")
        print(f"  Queries: {stats['count']}")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  p95: {stats['p95']:.2f}ms")


def get_telemetry_statistics():
    """Get telemetry statistics"""
    return _telemetry.get_statistics()


# Test function
if __name__ == "__main__":
    print(f"Testing Enhanced Query Rewriter v{__version__}...\n")
    
    # Load lexicon
    lexicon = load_lexicon()
    if not lexicon:
        print("Failed to load lexicon")
        exit(1)
    
    print(f"Loaded {len(lexicon['entities'])} entities\n")
    
    # Test normalization
    print("Testing Enhanced Normalization:")
    print("="*60)
    test_cases = [
        "  Is  SF   available???  ",
        "What's the capacity?",
        "Tell me about co-location"
    ]
    
    for test in test_cases:
        normalized = normalize_query(test)
        print(f"Before: '{test}'")
        print(f"After:  '{normalized}'")
        print()
    
    print("="*60)
    
    # Test queries with ALL features enabled
    test_queries = [
        "Is SF available at DFW10?",
        "What's the fabric topology?",
        "Tell me about colocation",
        "Power capacity at PHX10"
    ]
    
    print("\nTesting with ALL features enabled:")
    print("="*60)
    
    for query in test_queries:
        result = rewrite_query(
            query, 
            lexicon,
            track_performance=True,
            log_telemetry=True,
            use_disambiguation=True,
            user_id='test_user_123'
        )
        
        print(f"\nQuery: {query}")
        print(f"  Matched: {result['matched_entities']}")
        print(f"  Expansions: {result['expansion_count']}")
        print(f"  Time: {result['performance']['total_time_ms']:.2f}ms")
        if result['disambiguation_context']:
            print(f"  Disambiguation: {list(result['disambiguation_context'].keys())}")
    
    print("\n" + "="*60)
    print_performance_report()
    
    print("\nTelemetry Statistics:")
    stats = get_telemetry_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✓ Enhanced Query Rewriter v{__version__} Complete!")