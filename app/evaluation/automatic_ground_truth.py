
"""Automatic answer correctness evaluation using available ground truth."""

from app.ground_truth.wikidata_client import WikidataClient
from app.evaluation.answer_correctness import AnswerCorrectnessEvaluator


class AutomaticGroundTruthEvaluator:
    """Retrieve supported ground truth and evaluate an answer against it."""

    def __init__(self):
        self._wikidata = WikidataClient()
        self._evaluator = AnswerCorrectnessEvaluator()

    def evaluate(self, question: str, answer: str) -> dict | None:
        """Return ground-truth evaluation when the question is supported.

        Returns None when no supported ground truth can be retrieved.
        """

        try:
            result = self._wikidata.get_ground_truth(question)
        except (ValueError, KeyError):
            return None

        label = result.get("label")

        if not label:
            return None

        answer_is_correct = self._evaluator.evaluate(
            answer=answer,
            ground_truth=label,
        )

        return {
            "label": label,
            "source": result.get("source", "Wikidata"),
            "answer_is_correct": answer_is_correct,
        }
 