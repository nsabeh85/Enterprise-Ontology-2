"""
Performance Monitor

Tracks timing metrics for query rewriting operations.
Calculates mean, median, p95, p99 percentiles for performance analysis.

Usage:
    monitor = PerformanceMonitor()
    monitor.record('query_rewrite', 8.5)
    stats = monitor.get_stats('query_rewrite')
    print(f"p95: {stats['p95']:.2f}ms")
"""

import time
import numpy as np
from typing import Dict, List, Optional


class PerformanceMonitor:
    """
    Track performance metrics for operations
    
    Measures: count, mean, median, p95, p99, min, max
    """
    
    def __init__(self):
        """Initialize with predefined operation categories"""
        self.measurements = {
            'query_rewrite': [],
            'lexicon_load': [],
            'total': []
        }
    
    def record(self, operation: str, time_ms: float):
        """
        Record a timing measurement
        
        Args:
            operation: Name of operation (e.g., 'query_rewrite')
            time_ms: Time in milliseconds
        """
        if operation in self.measurements:
            self.measurements[operation].append(time_ms)
        else:
            # Create new operation category if needed
            self.measurements[operation] = [time_ms]
    
    def get_stats(self, operation: str = None) -> Dict:
        """
        Get statistics for an operation
        
        Args:
            operation: Specific operation, or None for all operations
        
        Returns:
            Dictionary with performance metrics:
            - count: Number of measurements
            - mean: Average time
            - median: Middle value (p50)
            - p95: 95th percentile
            - p99: 99th percentile
            - min: Fastest time
            - max: Slowest time
        """
        if operation:
            data = self.measurements.get(operation, [])
            if not data:
                return {}
            
            return {
                'operation': operation,
                'count': len(data),
                'mean': float(np.mean(data)),
                'median': float(np.median(data)),
                'p95': float(np.percentile(data, 95)),
                'p99': float(np.percentile(data, 99)),
                'min': float(np.min(data)),
                'max': float(np.max(data))
            }
        else:
            # Return stats for all operations
            stats = {}
            for op in self.measurements:
                op_stats = self.get_stats(op)
                if op_stats:
                    stats[op] = op_stats
            return stats
    
    def print_report(self):
        """Print formatted performance report"""
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        
        stats = self.get_stats()
        
        for operation, metrics in stats.items():
            if not metrics:
                continue
                
            print(f"\n{operation.upper().replace('_', ' ')}:")
            print(f"  Samples:  {metrics['count']}")
            print(f"  Mean:     {metrics['mean']:.2f}ms")
            print(f"  Median:   {metrics['median']:.2f}ms")
            print(f"  p95:      {metrics['p95']:.2f}ms")
            print(f"  p99:      {metrics['p99']:.2f}ms")
            print(f"  Min:      {metrics['min']:.2f}ms")
            print(f"  Max:      {metrics['max']:.2f}ms")
        
        print("\n" + "="*60)
    
    def reset(self, operation: str = None):
        """
        Reset measurements
        
        Args:
            operation: Specific operation to reset, or None for all
        """
        if operation:
            if operation in self.measurements:
                self.measurements[operation] = []
        else:
            for op in self.measurements:
                self.measurements[op] = []


# Test function
if __name__ == "__main__":
    import random
    
    print("Testing PerformanceMonitor...\n")
    
    # Create monitor
    monitor = PerformanceMonitor()
    
    # Simulate 100 operations
    for i in range(100):
        delay_ms = random.uniform(5, 15)
        monitor.record('query_rewrite', delay_ms)
    
    # Print report
    monitor.print_report()
    
    # Check against requirement
    stats = monitor.get_stats('query_rewrite')
    target_p95 = 40
    
    print("\nRequirement Check:")
    if stats['p95'] < target_p95:
        print(f"✓ PASSED: p95 ({stats['p95']:.2f}ms) < {target_p95}ms")
    else:
        print(f"✗ FAILED: p95 ({stats['p95']:.2f}ms) >= {target_p95}ms")
