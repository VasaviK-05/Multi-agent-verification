import pytest
from pydantic import ValidationError
from app.game.category_applicability import CategoryApplicability, configuration_from_category_artifacts


def declaration(**changes):
    values = dict(artifact_id='a'*64, task_id='b'*64,
        supported_distribution='Reference-backed paraphrase comparison within frozen task identity',
        exclusions=('Arbitrary factual correctness',), reviewed_by='test fixture; not scientific certification',
        development_report='c'*64, held_out_report='d'*64, baseline_report='e'*64,
        evaluated_scenarios=('correct','incorrect','uncertain','unsupported','resource_unavailable'),
        evaluated_teams=(('semantic',),),
        semantic_contradictions=('numbers','negation','entities','relationships'))
    return CategoryApplicability(**(values | changes))


@pytest.mark.parametrize('team', [('rule',), ('evidence',), ('semantic',), ('confidence',),
    ('confidence','evidence','rule','semantic')])
def test_all_four_and_combinations_can_be_declared(team):
    assert declaration(evaluated_teams=(team,)).evaluated_teams == (team,)


@pytest.mark.parametrize('changes', [dict(held_out_report='c'*64),
    dict(evaluated_scenarios=('correct',)), dict(evaluated_teams=(('new_verifier',),)),
    dict(evaluated_teams=(('semantic','semantic'),)), dict(semantic_contradictions=('numbers',))])
def test_incomplete_review_rejected(changes):
    with pytest.raises(ValidationError):
        declaration(**changes)


def test_artifacts_are_not_implicitly_promoted():
    with pytest.raises(ValueError, match='one category declaration'):
        configuration_from_category_artifacts([], [declaration()])
