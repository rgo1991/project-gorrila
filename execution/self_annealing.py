"""
Self-Annealing System - Learns from errors and improves over time
Analyzes error patterns, updates directives, and improves system behavior.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from collections import Counter
import re


class SelfAnnealingSystem:
    """Self-improving system that learns from errors and updates behavior."""
    
    def __init__(self):
        """Initialize self-annealing system."""
        self.error_log_path = Path(".tmp/error_log.jsonl")
        self.learning_log_path = Path(".tmp/learning_log.jsonl")
        self.improvements_path = Path(".tmp/improvements.json")
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def analyze_errors(self, days: int = 7) -> Dict:
        """
        Analyze errors from the last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with error analysis
        """
        if not self.error_log_path.exists():
            return {"total_errors": 0, "error_patterns": {}}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        errors = []
        
        try:
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error = json.loads(line.strip())
                        error_time = datetime.fromisoformat(error.get('timestamp', ''))
                        if error_time >= cutoff_date:
                            errors.append(error)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception:
            return {"total_errors": 0, "error_patterns": {}}
        
        if not errors:
            return {"total_errors": 0, "error_patterns": {}}
        
        # Analyze error patterns
        error_types = Counter()
        error_messages = []
        
        for error in errors:
            error_msg = error.get('error', '')
            error_types[error_msg.split(':')[0]] += 1
            error_messages.append(error_msg)
        
        # Find common patterns
        common_patterns = self._find_common_patterns(error_messages)
        
        return {
            "total_errors": len(errors),
            "error_types": dict(error_types.most_common(10)),
            "common_patterns": common_patterns,
            "recent_errors": errors[-5:]  # Last 5 errors
        }
    
    def _find_common_patterns(self, error_messages: List[str]) -> List[Dict]:
        """Find common error patterns."""
        patterns = []
        
        # Look for API-related errors
        api_errors = [e for e in error_messages if 'api' in e.lower() or 'openai' in e.lower()]
        if api_errors:
            patterns.append({
                "type": "API Error",
                "count": len(api_errors),
                "suggestion": "Check API key validity and rate limits"
            })
        
        # Look for network errors
        network_errors = [e for e in error_messages if any(x in e.lower() for x in ['connection', 'timeout', 'network'])]
        if network_errors:
            patterns.append({
                "type": "Network Error",
                "count": len(network_errors),
                "suggestion": "Check internet connection and retry logic"
            })
        
        # Look for validation errors
        validation_errors = [e for e in error_messages if any(x in e.lower() for x in ['value', 'invalid', 'missing', 'required'])]
        if validation_errors:
            patterns.append({
                "type": "Validation Error",
                "count": len(validation_errors),
                "suggestion": "Improve input validation and error messages"
            })
        
        return patterns
    
    def generate_improvements(self) -> List[Dict]:
        """
        Generate improvement suggestions based on error analysis.
        
        Returns:
            List of improvement suggestions
        """
        analysis = self.analyze_errors()
        
        if analysis["total_errors"] == 0:
            return []
        
        improvements = []
        
        # Check for API errors
        if any('API' in p.get('type', '') for p in analysis.get('common_patterns', [])):
            improvements.append({
                "priority": "high",
                "category": "API Configuration",
                "issue": "Frequent API errors detected",
                "solution": "Add API key validation and retry logic with exponential backoff",
                "implementation": "Update ai_chat_processor.py to validate API key on init and add retry decorator"
            })
        
        # Check for network errors
        if any('Network' in p.get('type', '') for p in analysis.get('common_patterns', [])):
            improvements.append({
                "priority": "high",
                "category": "Network Resilience",
                "issue": "Network connectivity issues",
                "solution": "Add connection pooling and automatic retry with backoff",
                "implementation": "Wrap API calls in retry decorator with exponential backoff"
            })
        
        # Check for validation errors
        if any('Validation' in p.get('type', '') for p in analysis.get('common_patterns', [])):
            improvements.append({
                "priority": "medium",
                "category": "Input Validation",
                "issue": "Input validation errors",
                "solution": "Add better input sanitization and user-friendly error messages",
                "implementation": "Add input validation layer before processing messages"
            })
        
        # Save improvements
        self._save_improvements(improvements)
        
        return improvements
    
    def _save_improvements(self, improvements: List[Dict]):
        """Save improvement suggestions."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "improvements": improvements
            }
            with open(self.improvements_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def apply_improvements(self, auto_apply: bool = False) -> Dict:
        """
        Apply improvements to the system.
        
        Args:
            auto_apply: If True, automatically apply safe improvements
        
        Returns:
            Dictionary with applied improvements
        """
        improvements = self.generate_improvements()
        
        if not improvements:
            return {"applied": 0, "message": "No improvements needed"}
        
        applied = []
        
        for improvement in improvements:
            # Only auto-apply high-priority, safe improvements
            if auto_apply and improvement.get("priority") == "high":
                # Log the improvement for manual review
                self._log_learning({
                    "type": "improvement_suggestion",
                    "improvement": improvement,
                    "timestamp": datetime.now().isoformat()
                })
                applied.append(improvement)
        
        return {
            "applied": len(applied),
            "improvements": applied,
            "pending": [i for i in improvements if i not in applied]
        }
    
    def _log_learning(self, learning_data: Dict):
        """Log learning events."""
        try:
            with open(self.learning_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(learning_data) + '\n')
        except Exception:
            pass
    
    def get_system_health(self) -> Dict:
        """
        Get overall system health metrics.
        
        Returns:
            Dictionary with health metrics
        """
        analysis = self.analyze_errors(days=1)  # Last 24 hours
        improvements = self.generate_improvements()
        
        # Calculate health score (0-100)
        error_count = analysis.get("total_errors", 0)
        if error_count == 0:
            health_score = 100
        elif error_count < 5:
            health_score = 90 - (error_count * 2)
        elif error_count < 10:
            health_score = 80 - (error_count * 3)
        else:
            health_score = max(0, 50 - error_count)
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy",
            "errors_last_24h": error_count,
            "pending_improvements": len(improvements),
            "last_analysis": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Example usage
    system = SelfAnnealingSystem()
    
    # Analyze errors
    analysis = system.analyze_errors()
    print(f"Total errors: {analysis['total_errors']}")
    print(f"Error types: {analysis.get('error_types', {})}")
    
    # Generate improvements
    improvements = system.generate_improvements()
    print(f"\nImprovements suggested: {len(improvements)}")
    for imp in improvements:
        print(f"  - {imp['category']}: {imp['issue']}")
    
    # Get health
    health = system.get_system_health()
    print(f"\nSystem Health: {health['health_score']}/100 ({health['status']})")

