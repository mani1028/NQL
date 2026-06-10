import json
import os
from datetime import datetime
from typing import Dict, Any

class FeedbackManager:
    """Manages user feedback and creates retraining datasets."""
    def __init__(self, feedback_file: str = "nql/ml/data/feedback_v3.jsonl"):
        self.feedback_file = feedback_file
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)

    def record_feedback(self, question: str, predicted_plan: Dict[str, Any], user_correction: Optional[Dict[str, Any]] = None, rating: int = 1):
        """
        Saves user feedback to a JSONL file.
        Rating: 1 for correct, 0 for incorrect.
        user_correction: The corrected JSON plan if provided.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "prediction": predicted_plan,
            "correction": user_correction,
            "rating": rating
        }
        
        with open(self.feedback_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def export_retraining_set(self) -> str:
        """Processes corrections into a format suitable for MiniLM fine-tuning."""
        # Implementation for converting JSONL to dataset.json format
        return self.feedback_file
