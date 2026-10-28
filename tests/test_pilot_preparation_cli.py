"""Reusable CLIs cannot execute from historical approval or private defaults."""
import pytest


@pytest.mark.parametrize('module', [
    'app.game.offline.arithmetic_pilot', 'scripts.run_factual_diagnostic',
    'scripts.prepare_factual_study_draft', 'scripts.prepare_factual_team_pilot',
    'scripts.prepare_broader_cost_measurement',
])
def test_missing_explicit_inputs_refuse_before_creating_output(module, tmp_path):
    import importlib
    main = importlib.import_module(module).main
    output = tmp_path/'not-created'
    with pytest.raises(SystemExit) as error:
        main(['--output-dir', str(output)])
    assert error.value.code == 2
    assert not output.exists()
