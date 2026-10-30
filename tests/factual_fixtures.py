"""Public six-row example texts plus synthetic reserved positions for unit tests.

No private study snapshots, final candidates, labels, reports or model files are read.
These examples exercise proposal contracts; they supply no empirical performance claim.
"""
import json
from pathlib import Path

PREPARATION_TEXTS = ((1,
  'What is the capital of Germany?',
  'The capital of Germany is Berlin.',
  'Germany is a country in Central Europe. Berlin is the capital and largest city of Germany.'),
 (2,
  'What is the capital of India?',
  'The capital of India is New Delhi.',
  'India is a country in South Asia. New Delhi is the capital of India.'),
 (3,
  'What is Python?',
  'Python is a high-level, general-purpose programming language.',
  'Python is a high-level, general-purpose programming language. It is widely used for web '
  'development, data analysis, artificial intelligence, and scientific computing.'),
 (4,
  'What is artificial intelligence?',
  'Artificial intelligence is a field of computer science concerned with creating systems '
  'capable of performing tasks that normally require human intelligence.',
  'Artificial intelligence is a field of computer science concerned with creating systems '
  'capable of performing tasks that normally require human intelligence, such as reasoning, '
  'learning, and perception.'),
 (5,
  'What is machine learning?',
  'Machine learning is a branch of artificial intelligence that enables computer systems to '
  'learn patterns from data and make predictions or decisions without being explicitly '
  'programmed for every task.',
  'Machine learning is a branch of artificial intelligence that enables computer systems to '
  'learn patterns from data and make predictions or decisions without being explicitly '
  'programmed for every task.'),
 (6,
  'Who developed the theory of relativity?',
  'Albert Einstein developed the theory of relativity.',
  'Albert Einstein was a German-born theoretical physicist. He developed the theory of '
  'relativity and received the Nobel Prize in Physics in 1921.'))


def candidate_inputs():
    rows = [dict(question=f'SYNTHETIC reserved fixture {i}', answer='SYNTHETIC answer',
                 context='SYNTHETIC reference') for i in range(10)]
    for index, question, answer, reference in PREPARATION_TEXTS:
        rows[index] = dict(question=question, answer=answer, context=reference)
    adapter = json.loads(Path('docs/verifier_project_adapter.template.json').read_text())
    adapter.update(index_dir='build/factual-feasibility-draft-v1/index',
                   index_receipt='build/factual-feasibility-draft-v1/index-receipt.json')
    return rows, adapter


def draft_request():
    from scripts.prepare_factual_study_draft import draft_package
    rows, adapter = candidate_inputs()
    return draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')['recording-request.draft.json']
