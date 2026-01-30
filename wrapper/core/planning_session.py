"""
Planning session state management.

Tracks interactive planning progress and user preferences.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from wrapper.core.files import (
    load_planning_session,
    save_planning_session,
)


class PlanningSession:
    """Manages interactive planning session state."""
    
    def __init__(self):
        """Initialize or load existing session."""
        self.state = load_planning_session() or self._create_default_state()
    
    def _create_default_state(self) -> dict:
        """Create default session state."""
        return {
            "started": datetime.now().isoformat(),
            "phase": "not_started",  # not_started, phase_planning, step_detailing, complete
            "current_phase_idx": 0,
            "phases": [],
            "user_preferences": {},
            "planning_context": [],
            "last_updated": datetime.now().isoformat(),
        }
    
    def save(self) -> None:
        """Persist session to disk."""
        self.state["last_updated"] = datetime.now().isoformat()
        save_planning_session(self.state)
    
    def set_phase(self, phase: str) -> None:
        """Set current planning phase."""
        self.state["phase"] = phase
        self.save()
    
    def get_phase(self) -> str:
        """Get current planning phase."""
        return self.state.get("phase", "not_started")
    
    def add_phase_data(self, phase_data: dict) -> None:
        """Add a phase to the plan."""
        self.state["phases"].append(phase_data)
        self.save()
    
    def get_phases(self) -> List[dict]:
        """Get all phases."""
        return self.state.get("phases", [])
    
    def set_current_phase_idx(self, idx: int) -> None:
        """Set index of phase currently being detailed."""
        self.state["current_phase_idx"] = idx
        self.save()
    
    def get_current_phase_idx(self) -> int:
        """Get index of phase currently being detailed."""
        return self.state.get("current_phase_idx", 0)
    
    def record_preference(self, key: str, value: Any) -> None:
        """Record user preference (e.g., 'complexity': 'conservative')."""
        self.state["user_preferences"][key] = value
        self.save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.state["user_preferences"].get(key, default)
    
    def add_context(self, question: str, answer: Any, reasoning: Optional[str] = None) -> None:
        """
        Record a planning decision for context.
        
        This helps LLM understand user's thinking in later steps.
        """
        self.state["planning_context"].append({
            "question": question,
            "answer": answer,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()
    
    def get_context_summary(self, last_n: int = 5) -> str:
        """Get summary of recent planning decisions."""
        context_items = self.state.get("planning_context", [])[-last_n:]
        
        if not context_items:
            return "No previous planning context"
        
        lines = []
        for item in context_items:
            line = f"- {item['question']} → {item['answer']}"
            if item.get('reasoning'):
                line += f" ({item['reasoning']})"
            lines.append(line)
        
        return "\n".join(lines)
    
    def is_complete(self) -> bool:
        """Check if planning session is complete."""
        return self.state.get("phase") == "complete"
    
    def clear(self) -> None:
        """Clear session (start fresh)."""
        self.state = self._create_default_state()
        self.save()
