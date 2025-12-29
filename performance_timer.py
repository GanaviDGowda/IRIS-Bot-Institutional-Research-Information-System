"""
Performance Timing Decorator
Simple timing decorator for VTU performance analysis.
"""

import time
import functools
from typing import Dict, List, Any
import statistics


class PerformanceTimer:
    """Simple performance timer for collecting timing statistics."""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
    
    def record(self, function_name: str, execution_time: float):
        """Record an execution time for a function."""
        if function_name not in self.timings:
            self.timings[function_name] = []
        self.timings[function_name].append(execution_time * 1000)  # Convert to milliseconds
    
    def get_statistics(self, function_name: str) -> Dict[str, float]:
        """Get statistics for a function."""
        if function_name not in self.timings or not self.timings[function_name]:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std_dev': 0.0
            }
        
        times = self.timings[function_name]
        return {
            'count': len(times),
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all recorded functions."""
        return {name: self.get_statistics(name) for name in self.timings.keys()}
    
    def clear(self):
        """Clear all recorded timings."""
        self.timings.clear()


# Global timer instance
_timer = PerformanceTimer()


def timed_function(function_name: str = None):
    """
    Decorator to measure function execution time.
    
    Args:
        function_name: Optional custom name for the function in reports.
                      If None, uses the function's __name__
    """
    def decorator(func):
        name = function_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                _timer.record(name, execution_time)
        
        return wrapper
    return decorator


def get_timer() -> PerformanceTimer:
    """Get the global timer instance."""
    return _timer


