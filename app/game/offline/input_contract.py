"""Verbatim question content for game-owned offline requests and replay records.

This additive input contract changes no identifier, application API or verifier.
Content is never stripped; whitespace participates in hashing and dispatch.
"""
from typing import Annotated

from pydantic import AfterValidator, StrictStr

QUESTION_INPUT_CONTRACT = 'verbatim_question_text_v1'


def question_text(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('question must be nonblank text')
    return value


QuestionText = Annotated[StrictStr, AfterValidator(question_text)]
