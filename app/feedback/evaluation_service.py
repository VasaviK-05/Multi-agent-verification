"""Evaluation service — placeholder implementation."""

from typing import Optional


class EvaluationService:
    """Handles feedback, ground truth, and future learning updates.

    TODO: Implement reliable feedback collection.
    TODO: Implement ground truth management.
    TODO: Implement learning/reputation update triggers.
    """

    def submit_feedback(
        self,
        validation_id: str,
        is_correct: bool,
        comment: Optional[str] = None,
    ) -> None:
        """Record user feedback on a validation result.

        Scaffold: no-op placeholder.
        """
        # TODO: Persist feedback and trigger reputation updates
        pass

    def get_ground_truth(self, question: str) -> Optional[str]:
        """Retrieve ground truth answer for a question.

        Scaffold: returns None.
        """
        # TODO: Look up ground truth from database
        return None

    def trigger_learning_update(self, validation_id: str) -> None:
        """Trigger learning/reputation updates from evaluation data.

        Scaffold: no-op placeholder.
        """
        # TODO: Implement learning loop
        pass
