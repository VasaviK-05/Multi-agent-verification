"""Offline preparation validation only, using explicit temporary synthetic inputs."""
import json
import pytest
from tests.preparation_fixtures import synthetic_adapter_file
from scripts.preparation_config import preparation_adapter

def test_explicit_adapter_preserves_settings_without_loading_resources(tmp_path,monkeypatch):
    from app.benchmark import project_adapter
    path,data=synthetic_adapter_file(tmp_path)
    monkeypatch.setattr(project_adapter,'inspect_setup',lambda *a:pytest.fail('preparation inspected resources'))
    root=tmp_path/'new-study'
    actual=preparation_adapter(path,root).model_dump(mode='json')
    for key,value in data.items():
        if key not in {'corpus_path','index_dir','index_receipt','service_observation'}:assert actual[key]==value
    assert actual['corpus_path']==str(root/'corpus.json')
    assert actual['index_dir']==str(root/'index-v2')
    assert actual['index_receipt']==str(root/'index-receipt.json')
    assert actual['service_observation']==str(root/'service-observation.json')
    assert not root.exists()

@pytest.mark.parametrize('case',['none','missing_file','malformed','array','missing_field','wrong_version','bad_setting','remote_service','duplicate','nonfinite'])
@pytest.mark.parametrize('script',['factual','multitask'])
def test_bad_configuration_fails_before_preparation_outputs(tmp_path,monkeypatch,case,script):
    from scripts import factual_policy42,multitask_policy42
    path,data=synthetic_adapter_file(tmp_path)
    if case=='none':path=None
    elif case=='missing_file':path=tmp_path/'not-supplied.json'
    elif case=='malformed':path.write_text('{bad JSON')
    elif case=='array':path.write_text('[]')
    elif case=='duplicate':path.write_text('{"version":"one","version":"two"}')
    elif case=='nonfinite':path.write_text('{"temperature":NaN}')
    else:
        if case=='missing_field':del data['n_samples']
        elif case=='wrong_version':data['version']='invalid-version'
        elif case=='bad_setting':data['n_samples']=0
        elif case=='remote_service':data['ollama_url']='https://example.org/api/generate'
        path.write_text(json.dumps(data))
    root=tmp_path/'no-output'
    if script=='factual':call=lambda:factual_policy42.prepare(root,adapter_config=path)
    else:
        monkeypatch.setattr(multitask_policy42,'ROOT',root)
        monkeypatch.setattr(multitask_policy42,'read',lambda *a:pytest.fail('historical inputs read before config validation'))
        call=lambda:multitask_policy42.prepare(adapter_config=path)
    with pytest.raises(ValueError,match='adapter-config'):call()
    assert not root.exists()

@pytest.mark.parametrize('script',['factual','multitask'])
def test_cli_requires_explicit_config_without_writes(tmp_path,monkeypatch,capsys,script):
    from scripts import factual_policy42,multitask_policy42
    root=tmp_path/'no-output'
    if script=='factual':main=factual_policy42.main;args=['prepare','--root',str(root)]
    else:
        monkeypatch.setattr(multitask_policy42,'ROOT',root)
        main=multitask_policy42.main;args=['prepare']
    with pytest.raises(SystemExit) as failure:main(args)
    assert failure.value.code==2 and '--adapter-config' in capsys.readouterr().err
    assert not root.exists()
    assert main(args+['--adapter-config',str(tmp_path/'missing.json')])==2
    output=json.loads(capsys.readouterr().out)
    assert output['status']=='preparation_input_error' and not output['new_policy_created']
    assert not root.exists()

def test_factual_cli_valid_synthetic_preparation(tmp_path,monkeypatch):
    from scripts.factual_policy42 import main
    from app.benchmark import project_adapter
    from app.game.offline.records import FinalTestReservation
    config,settings=synthetic_adapter_file(tmp_path);root=tmp_path/'study'
    (root/'sources').mkdir(parents=True);countries=[];geo=[]
    for i in range(120):
        iso=chr(65+i//26)+chr(65+i%26)
        countries.append(dict(cca2=iso,name=dict(common='Country'+iso),capital=['City'+iso],unMember=True))
        geo.append('\t'.join([iso,'','','','Country'+iso,'City'+iso]))
    (root/'sources/countries.json').write_text(json.dumps(countries))
    (root/'sources/geonames-countryInfo.txt').write_text('\n'.join(geo))
    monkeypatch.setattr(project_adapter,'inspect_setup',lambda *a:pytest.fail('resource inspection in preparation'))
    assert main(['prepare','--root',str(root),'--adapter-config',str(config)])==0
    actual=json.loads((root/'adapter.json').read_text())
    assert actual['n_samples']==settings['n_samples'] and actual['temperature']==settings['temperature']
    assert len(FinalTestReservation.model_validate_json((root/'reservation.json').read_text()).examples)==40

def test_multitask_prepares_without_historical_adapter_file(tmp_path,monkeypatch):
    from scripts import multitask_policy42 as campaign
    from app.game.offline.records import FinalTestReservation
    config,settings=synthetic_adapter_file(tmp_path)
    old=tmp_path/'build/factual-policy42-20261029';sources=old/'sources';sources.mkdir(parents=True)
    countries=[];geo=[]
    for i in range(120):
        iso=chr(65+i//26)+chr(65+i%26);country='Country'+iso
        countries.append(dict(cca2=iso,name=dict(common=country),unMember=True,
            currencies={'USD':{'name':'SYNTHETIC dollar'}},area=1000+i))
        fields=[iso,'','','',country,'SYNTHETIC city','','100000','','','USD']
        geo.append('\t'.join(fields))
    (sources/'countries.json').write_text(json.dumps(countries))
    (sources/'geonames-countryInfo.txt').write_text('\n'.join(geo))
    (sources/'LICENSE').write_text('SYNTHETIC fixture, no external data')
    (sources/'countries-revision.json').write_text('{"revision":"SYNTHETIC"}')
    (old/'dataset-audit.json').write_text('{"rows":[]}')
    assert not (old/'adapter.json').exists()
    monkeypatch.chdir(tmp_path);output=tmp_path/'new-multitask'
    monkeypatch.setattr(campaign,'ROOT',output)
    assert campaign.main(['prepare','--adapter-config',str(config)])==0
    actual=json.loads((output/'adapter.json').read_text())
    assert actual['n_samples']==settings['n_samples'] and actual['temperature']==settings['temperature']
    for cohort in campaign.COHORTS:
        prepared=json.loads((output/cohort/'preparation.json').read_text())
        assert len(prepared['examples'])==80
        assert len(FinalTestReservation.model_validate_json((output/cohort/'reservation.json').read_text()).examples)==40
