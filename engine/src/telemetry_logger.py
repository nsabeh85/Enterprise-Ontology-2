"""
Telemetry Logger
Logs query pipeline telemetry for analysis and A/B testing.
"""

import json
import hashlib
from datetime import datetime, timezone
import uuid
import os

class TelemetryLogger:
    def __init__(self, storage_path='outputs/telemetry_logs.jsonl'):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        directory = os.path.dirname(self.storage_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy (SHA-256)"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def generate_query_id(self) -> str:
        """Generate unique query ID"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        return f"query_{timestamp}_{unique_id}"
    
    def log_query(self, query_id, user_id, original_query, rewritten_query, performance, metadata=None):
        """Log a complete query event"""
        log_entry = {
            'query_id': query_id,
            'user_id_hash': self._hash_user_id(user_id),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'original_query': original_query,
            'matched_entities': rewritten_query.get('matched_entities', []),
            'expanded_terms': rewritten_query.get('expanded_terms', []),
            'expansion_count': rewritten_query.get('expansion_count', 0),
            'query_rewrite_time_ms': performance.get('time_ms', 0),
            'retrieval_time_ms': None,
            'generation_time_ms': None,
            'first_answer_success': None,
            'user_feedback': None,
            'metadata': metadata or {}
        }
        
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def read_logs(self, limit=None):
        """Read telemetry logs"""
        logs = []
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except FileNotFoundError:
            return []
        
        if limit:
            logs = logs[-limit:]
        return logs
    
    def get_statistics(self):
        """Get basic statistics from logs"""
        logs = self.read_logs()
        if not logs:
            return {'total_queries': 0}
        
        return {
            'total_queries': len(logs),
            'unique_users': len(set(log['user_id_hash'] for log in logs)),
            'avg_rewrite_time_ms': sum(log['query_rewrite_time_ms'] for log in logs) / len(logs),
            'queries_with_matches': sum(1 for log in logs if log['matched_entities']),
            'queries_without_matches': sum(1 for log in logs if not log['matched_entities'])
        }

if __name__ == "__main__":
    print("Testing TelemetryLogger...\n")
    logger = TelemetryLogger('outputs/test_telemetry.jsonl')
    
    # Test hashing
    test_user = "john.doe@company.com"
    hashed = logger._hash_user_id(test_user)
    print(f"Original: {test_user}")
    print(f"Hashed: {hashed}")
    print(f"✓ Privacy protected\n")
    
    # Test logging
    query_id = logger.generate_query_id()
    logger.log_query(
        query_id=query_id,
        user_id=test_user,
        original_query="Test query",
        rewritten_query={'matched_entities': ['ServiceFabric'], 'expansion_count': 3},
        performance={'time_ms': 8.5}
    )
    print(f"✓ Logged query: {query_id}")
    print(f"✓ File: {logger.storage_path}")