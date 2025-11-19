import time
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import functools

class PerformanceRecorder:
    """
    Records and stores performance metrics for functions and classes.
    
    Attributes:
        results_dir (Path): Directory to store performance results
        baseline_file (Path): File for baseline performance data
        history_file (Path): File for historical performance data
    """
    
    def __init__(self, results_dir: str = "tests/performance/results"):
        """
        Initialize the performance recorder.
        
        Args:
            results_dir: Directory to store performance results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.results_dir / "performance_baseline.json"
        self.history_file = self.results_dir / "performance_history.json"
        self._current_measurements = {}
    
    def measure_function(self, func_name: str, class_name: str = None):
        """
        Decorator to measure function execution time.
        
        Args:
            func_name: Name of the function being measured
            class_name: Name of the class if it's a method
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                execution_time = end_time - start_time
                full_name = f"{class_name}.{func_name}" if class_name else func_name
                
                self.record_measurement(full_name, execution_time)
                return result
            return wrapper
        return decorator
    
    def record_measurement(self, name: str, execution_time: float):
        """
        Record a single performance measurement.
        
        Args:
            name: Name of the function/class being measured
            execution_time: Execution time in seconds
        """
        self._current_measurements[name] = execution_time
    
    def save_baseline(self):
        """Save current measurements as baseline for future comparison."""
        baseline_data = {
            "timestamp": datetime.now().isoformat(),
            "measurements": self._current_measurements
        }
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
    
    def save_to_history(self, tag: str = None):
        """
        Save current measurements to history.
        
        Args:
            tag: Optional tag to identify this performance run
        """
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "tag": tag or "untagged",
            "measurements": self._current_measurements.copy()
        }
        
        # Load existing history
        history = self._load_history()
        history.append(history_entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def compare_with_baseline(self) -> Dict[str, Any]:
        """
        Compare current measurements with baseline.
        
        Returns:
            Dictionary containing comparison results
        """
        if not self.baseline_file.exists():
            return {"error": "No baseline data available"}
        
        with open(self.baseline_file, 'r') as f:
            baseline_data = json.load(f)
        
        baseline = baseline_data["measurements"]
        current = self._current_measurements
        
        comparison = {}
        for name, current_time in current.items():
            if name in baseline:
                baseline_time = baseline[name]
                improvement = baseline_time - current_time
                improvement_percent = (improvement / baseline_time) * 100
                
                comparison[name] = {
                    "baseline": baseline_time,
                    "current": current_time,
                    "improvement_seconds": improvement,
                    "improvement_percent": improvement_percent,
                    "is_faster": improvement > 0
                }
        
        return comparison
    
    def _load_history(self) -> List[Dict]:
        """Load performance history from file."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []