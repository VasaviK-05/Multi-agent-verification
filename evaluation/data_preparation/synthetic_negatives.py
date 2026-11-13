"""Deterministic synthetic incorrect candidates for GSM8K and HotpotQA.

Every generator is a pure function of the gold answer and its source record, so the
same inputs always yield the same candidate. Outputs are SYNTHETIC_INCORRECT under the
provisional automated protocol; they are plausible-looking errors, not natural model
errors, and they are never human verified.
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from fractions import Fraction
from typing import Iterable

from evaluation.data_preparation.build_verified_subset import normalize_numeric

GENERATOR_VERSION = "synthetic_negatives_v1"
GSM8K_TRANSFORMS = (("gold_plus_one", 1), ("gold_minus_one", -1), ("gold_plus_two", 2))
ROUNDING_OR_RATIO_CUE = re.compile(r"round(?:ed|ing)?|nearest|approximately|approx\.?|about|roughly|estimate|"
                                   r"percentage|percent|%|ratio|probability|fraction|how many times", re.I)
_PUNCT = re.compile(r"[^a-z0-9]+")
_ARTICLES = {"a", "an", "the"}
_NUMBER = re.compile(r"(?<![A-Za-z0-9.,])(\d{1,3}(?:,\d{3})+|\d+)(?![A-Za-z0-9]|[.,]\d)")


def normalize_answer(text: object) -> str:
    value = normalize_numeric(text)
    if value is not None:
        return f"num:{value.numerator}/{value.denominator}"
    return " ".join(t for t in _PUNCT.sub(" ", str(text).lower()).split() if t not in _ARTICLES)


def opaque_id(namespace: str, group_id: str, answer: str) -> str:
    """Candidate ID that carries no class, position or generation information."""
    digest = hashlib.sha256(f"{namespace}|{group_id}|{normalize_answer(answer)}".encode()).hexdigest()
    return f"{namespace}-{digest[:20]}"


def _format_like(value: Fraction, template: str) -> str | None:
    body = template.strip()
    prefix = "$" if body.startswith("$") else ""
    body = body.lstrip("$")
    if "/" in body:
        return prefix + (str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}")
    decimals = len(body.split(".", 1)[1]) if "." in body else 0
    number = Decimal(value.numerator) / Decimal(value.denominator)
    if decimals == 0 and value.denominator != 1:
        return None
    text = f"{number:,.{decimals}f}" if "," in body else f"{number:.{decimals}f}"
    return prefix + text


def gsm8k_negative(gold: str, taken: Iterable[str] = ()) -> dict | None:
    """First of gold+1, gold-1, gold+2 that is new in the group and keeps the gold's format.

    A negative result is skipped for nonnegative golds because a sign change would
    reveal the class.
    """
    value = normalize_numeric(gold)
    if value is None:
        return None
    used = {normalize_answer(x) for x in taken} | {normalize_answer(gold)}
    for name, delta in GSM8K_TRANSFORMS:
        candidate = value + delta
        if candidate < 0 <= value:
            continue
        text = _format_like(candidate, gold)
        if text is None or normalize_answer(text) in used or normalize_numeric(text) != candidate:
            continue
        return {"answer": text, "transformation": name, "delta": delta}
    return None


def gsm8k_quality_flags(question: str) -> dict:
    """Signals that the integer answer might tolerate a nearby value (higher synthetic-label risk)."""
    return {"how_many_question": "how many" in question.lower(),
            "rounding_or_ratio_cue_present": bool(ROUNDING_OR_RATIO_CUE.search(question))}


def strip_disambiguation(title: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", str(title)).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _PUNCT.sub(" ", str(text).lower()).split() if t and t not in _ARTICLES}


def _overlaps(a: str, b: str) -> bool:
    na, nb = normalize_answer(a), normalize_answer(b)
    return bool(na and nb and (na == nb or na in nb or nb in na or _tokens(a) & _tokens(b)))


def _yes_no(gold: str) -> dict | None:
    lowered = gold.strip().lower()
    if lowered not in {"yes", "no"}:
        return None
    flipped = "no" if lowered == "yes" else "yes"
    if gold.strip()[:1].isupper():
        flipped = flipped.capitalize()
    return {"answer": flipped, "transformation": "yes_no_complement"}


def _comparison_other(gold: str, question_type: str | None, supporting_titles: list[str]) -> dict | None:
    if question_type != "comparison":
        return None
    options = list(dict.fromkeys(strip_disambiguation(t) for t in supporting_titles if str(t).strip()))
    matches = [o for o in options if normalize_answer(o) == normalize_answer(gold)]
    if len(options) != 2 or len(matches) != 1:
        return None
    other = next(o for o in options if o != matches[0])
    if _overlaps(other, gold):
        return None
    return {"answer": other, "transformation": "comparison_other_entity"}


def _numeric_increment(gold: str) -> dict | None:
    match = _NUMBER.search(gold)
    if not match:
        return None
    raw = match.group(1)
    value = int(raw.replace(",", "")) + 1
    replacement = f"{value:,}" if "," in raw else str(value)
    return {"answer": gold[:match.start(1)] + replacement + gold[match.end(1):], "transformation": "numeric_increment"}


def _distractor_title(gold: str, question: str, context: list[dict], supporting_titles: list[str], key: str,
                      used: set[str]) -> dict | None:
    support = {str(t) for t in supporting_titles}
    question_norm = normalize_answer(question)
    eligible = []
    for item in context:
        title = str(item.get("title", ""))
        option = strip_disambiguation(title)
        norm = normalize_answer(option)
        if (not norm or title in support or _overlaps(option, gold) or norm in used
                or f" {norm} " in f" {question_norm} "):
            continue
        eligible.append(option)
    if not eligible:
        return None
    choice = min(dict.fromkeys(eligible), key=lambda o: hashlib.sha256(f"{key}|{o}".encode()).hexdigest())
    return {"answer": choice, "transformation": "distractor_paragraph_title"}


def hotpotqa_negative(gold: str, *, question: str, question_type: str | None, context: list[dict],
                      supporting_titles: list[str], key: str, taken: Iterable[str] = ()) -> dict | None:
    """Yes/no complement, then the other compared entity, then a number increment, then a distractor title."""
    used = {normalize_answer(x) for x in taken} | {normalize_answer(gold)}
    for candidate in (_yes_no(gold), _comparison_other(gold, question_type, supporting_titles), _numeric_increment(gold)):
        if candidate and normalize_answer(candidate["answer"]) not in used:
            return candidate
    return _distractor_title(gold, question, context, supporting_titles, key, used)


def surface_features(answer: str) -> dict:
    text = str(answer).strip()
    return {"chars": len(text), "tokens": len(text.split()), "has_digit": any(c.isdigit() for c in text),
            "initial_upper": text[:1].isupper(), "has_parenthesis": "(" in text or ")" in text,
            "yes_no": text.lower() in {"yes", "no"}}


def surface_feature_summary(rows: list[tuple[str, str, str]]) -> dict:
    """Mean surface features per (benchmark, label class), to check that format does not reveal class."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for benchmark, label_class, answer in rows:
        groups.setdefault((benchmark, label_class), []).append(surface_features(answer))
    out: dict[str, dict] = {}
    for (benchmark, label_class), features in sorted(groups.items()):
        n = len(features)
        out.setdefault(benchmark, {})[label_class] = {"n": n, **{
            key: round(sum(float(f[key]) for f in features) / n, 4) for key in features[0]}}
    return out
