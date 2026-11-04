"""Question-only bounded category; no inference or performance claims."""
from dataclasses import asdict
import pytest
from app.analysis.reference_study_analyzer import analyze_reference,VERSION
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.game.question_routing import classify_question,QuestionPolicyConfiguration
from scripts.reference_study import FRAMES
def test_fresh_frames_share_only_explicit_opt_in_category():
    signatures=set();legacy=set()
    assert len(FRAMES)==30 and len({f[1] for f in FRAMES})==30
    for family,ref,good,bad in FRAMES:
        assert good!=bad and family in {'count','negation','role','spatial'}
        q='Paraphrase this reference: '+ref
        a=analyze_reference(q)
        assert a.difficulty_score==.1 and a.research_context.scoring_version==VERSION
        assert a.verification_types==['semantic_comparison']
        kind,sig,_=classify_question(q,ref,reference_question_version=VERSION)
        assert kind=='atomic';signatures.add(sig)
        legacy.add(TaskQuestionAnalyzer().analyze(q).difficulty_score)
    assert len(signatures)==1 and len(legacy)>1
    with pytest.raises(ValueError,match='allowlist'):QuestionPolicyConfiguration(reference_question_version=VERSION)
    with pytest.raises(ValueError):classify_question(q,ref,reference_question_version='unknown')
def test_non_reference_unchanged_and_default_remains_separate():
    q='What is 2 + 3?'
    assert classify_question(q)==classify_question(q,reference_question_version=VERSION)
    q='Paraphrase this reference: A raven rests.'
    assert classify_question(q,'A raven rests.')[1]!=classify_question(q,'A raven rests.',reference_question_version=VERSION)[1]
