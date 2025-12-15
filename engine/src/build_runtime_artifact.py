import yaml
import json
from datetime import datetime
import os

def build_runtime_artifact(
    lexicon_path='data/lexicon_v01_final.yaml',
    output_path='data/ontology_runtime.json'
):
    """
    Convert lexicon YAML to optimized JSON runtime artifact
    
    Processes all sections:
    - products
    - facilities
    - technical_terms
    - partners
    - geographic_terms
    """
    print(f"Loading lexicon from {lexicon_path}...")
    
    # Error handling for file loading
    try:
        with open(lexicon_path, 'r') as f:
            lexicon = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: Lexicon file not found at {lexicon_path}")
        return None
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML format: {e}")
        return None
    
    # Build runtime structure
    runtime = {
        'version': lexicon.get('version', '0.1'),
        'domain': lexicon.get('domain', 'data_center_infrastructure'),
        'build_timestamp': datetime.now().isoformat(),
        'entities': {},
        'entity_count': 0
    }
    
    # Process products
    if 'products' in lexicon:
        for item in lexicon['products']:
            canonical = item.get('canonical')
            if canonical:
                runtime['entities'][canonical] = {
                    'type': item.get('type', 'product'),
                    'category': item.get('category', ''),
                    'synonyms': item.get('synonyms', []),
                    'related_terms': item.get('related_terms', []),
                    'definition': item.get('definition', '')
                }
    
    # Process facilities
    if 'facilities' in lexicon:
        for item in lexicon['facilities']:
            canonical = item.get('canonical')
            if canonical:
                runtime['entities'][canonical] = {
                    'type': item.get('type', 'facility'),
                    'market': item.get('market', ''),
                    'region': item.get('region', ''),
                    'synonyms': item.get('synonyms', []),
                    'address': item.get('address', ''),
                    'related_terms': item.get('related_terms', [])  # Added for consistency
                }
    
    # Process technical terms
    if 'technical_terms' in lexicon:
        for item in lexicon['technical_terms']:
            canonical = item.get('canonical')
            if canonical:
                runtime['entities'][canonical] = {
                    'type': item.get('type', 'technical'),
                    'synonyms': item.get('synonyms', []),
                    'related_terms': item.get('related_terms', []),
                    'definition': item.get('definition', ''),
                    'category': item.get('category', '')  # Added for consistency
                }
    
    # Process partners
    if 'partners' in lexicon:
        for item in lexicon['partners']:
            canonical = item.get('canonical')
            if canonical:
                runtime['entities'][canonical] = {
                    'type': item.get('type', 'partner'),
                    'synonyms': item.get('synonyms', []),
                    'related_terms': item.get('related_terms', []),
                    'definition': item.get('definition', ''),
                    'category': item.get('category', '')  # Added for consistency
                }
    
    # Process geographic terms
    if 'geographic_terms' in lexicon:
        for item in lexicon['geographic_terms']:
            canonical = item.get('canonical')
            if canonical:
                runtime['entities'][canonical] = {
                    'type': item.get('type', 'region'),
                    'synonyms': item.get('synonyms', []),
                    'key_markets': item.get('key_markets', []),
                    'related_terms': item.get('related_terms', [])  # Added for consistency
                }
    
    runtime['entity_count'] = len(runtime['entities'])
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as JSON
    print(f"Saving runtime artifact to {output_path}...")
    try:
        with open(output_path, 'w') as f:
            json.dump(runtime, f, indent=2)
    except IOError as e:
        print(f"ERROR: Could not write to {output_path}: {e}")
        return None
    
    # Print summary
    print("\n" + "="*60)
    print("Runtime Artifact Built Successfully")
    print("="*60)
    print(f"Version: {runtime['version']}")
    print(f"Domain: {runtime['domain']}")
    print(f"Entities: {runtime['entity_count']}")
    print(f"File: {output_path}")
    
    # Calculate file size
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Size: {size_kb:.2f} KB")
    print("="*60 + "\n")
    
    return runtime


if __name__ == "__main__":
    artifact = build_runtime_artifact()
    if artifact:
        print("✅ Build completed successfully")
    else:
        print("❌ Build failed")