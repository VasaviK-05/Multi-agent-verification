"""Deterministic comparison between an answer and an expected ground-truth label."""

import re


class AnswerCorrectnessEvaluator:
    """Evaluates whether an answer contains the expected ground-truth label."""

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def evaluate(self, answer: str, ground_truth: str) -> bool:
        if not answer or not ground_truth:
            return False

        normalized_answer = self._normalize(answer)
        normalized_truth = self._normalize(ground_truth)

        return normalized_truth in normalized_answer
