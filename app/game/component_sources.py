"""Finite, source-backed V2 descriptors. Parsing never consumes source values."""
from decimal import Decimal
import re
from typing import Literal
from pydantic import model_validator
from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.component_binding import ComponentPlan, BindingError, bind_answer, _NUMBER, digest

VERSION='fact_plus_sum_binding_v2'


class Descriptor(FrozenModel):
    source_id: str
    entity: str
    measure: Literal['area','population']

    @model_validator(mode='after')
    def check(self):
        if (not self.source_id.strip() or self.entity!=self.entity.strip()
            or re.fullmatch(r"[A-Za-z][A-Za-z '\-]{0,79}",self.entity) is None):
            raise ValueError('descriptor requires a bounded source-backed entity name')
        return self


class Catalog(FrozenModel):
    version: Literal['source_backed_component_catalog_v2']='source_backed_component_catalog_v2'
    source_manifest_id: str
    descriptors: tuple[Descriptor,...]

    @model_validator(mode='after')
    def check(self):
        keys=[(d.entity.casefold(),d.measure) for d in self.descriptors]
        if not keys or len(keys)!=len(set(keys)):
            raise ValueError('catalog needs unique unambiguous entity/measure descriptors')
        return self


class SourceFact(FrozenModel):
    descriptor: Descriptor
    value: str
    corpus_row_json: str
    independent_source_line: str
    independent_country_json: str

    @model_validator(mode='after')
    def check(self):
        import json
        d=self.descriptor;row=json.loads(self.corpus_row_json)
        columns=self.independent_source_line.split('\t')
        if len(columns)<8 or columns[0]!=d.source_id:
            raise ValueError('independent GeoNames source identity differs')
        country=json.loads(self.independent_country_json)
        if country.get('cca2')!=d.source_id or country.get('name',{}).get('common')!=d.entity:
            raise ValueError('independent country entity/ISO identity differs')
        expected=str(country['area']) if d.measure=='area' else columns[7]
        if re.fullmatch(_NUMBER,self.value) is None or Decimal(self.value)!=Decimal(expected):
            raise ValueError('independent base value differs from supplied label')
        units=' square kilometres' if d.measure=='area' else ''
        if (row.get('id')!=d.source_id or row.get('text')!=f'The {d.measure} of {d.entity} is {self.value}{units}.'
            or row.get('url')!=f'https://www.geonames.org/countries/{d.source_id}/'):
            raise ValueError('corpus identity/fact differs from independently established source')
        return self


class SourceManifest(FrozenModel):
    version: Literal['compound_sources_v2']='compound_sources_v2'
    evidence_kind: Literal['empirical','synthetic_test_fixture']
    corpus_sha256: str
    independent_source_sha256: str
    independent_countries_sha256: str
    facts: tuple[SourceFact,...]

    @model_validator(mode='after')
    def check(self):
        for digest_value in (self.corpus_sha256,self.independent_source_sha256,self.independent_countries_sha256):
            if re.fullmatch('[0-9a-f]{64}',digest_value) is None:
                raise ValueError('source files require SHA256 identities')
        keys=[(f.descriptor.source_id,f.descriptor.measure) for f in self.facts]
        if not keys or len(keys)!=len(set(keys)):
            raise ValueError('source manifest needs unique source/measure identities')
        Catalog(source_manifest_id='validation',descriptors=tuple(f.descriptor for f in self.facts))
        return self

    @property
    def manifest_id(self):return content_id(self.model_dump(mode='json'))

    @property
    def catalog(self):
        return Catalog(source_manifest_id=self.manifest_id,descriptors=tuple(f.descriptor for f in self.facts))


def source_manifest(corpus_bytes,independent_bytes,countries_bytes,*,evidence_kind='empirical'):
    import hashlib,json
    rows=json.loads(corpus_bytes)
    country_rows=json.loads(countries_bytes)
    countries={r['cca2']:r for r in country_rows}
    lines=[line for line in independent_bytes.decode('utf-8').splitlines() if line and not line.startswith('#')]
    independent={line.split('\t')[0]:line for line in lines}
    if len(countries)!=len(country_rows) or len(independent)!=len(lines):raise ValueError('duplicate independent source identity')
    if len({row['id'] for row in rows})!=len(rows):raise ValueError('duplicate corpus source identity')
    facts=[]
    for row in rows:
        match=re.fullmatch(rf'The (area|population) of (.+) is ({_NUMBER})( square kilometres)?\.',row['text'])
        if not match:continue
        d=Descriptor(source_id=row['id'],entity=match[2],measure=match[1])
        if row['id'] not in independent:raise ValueError('missing independent source record')
        facts.append(SourceFact(descriptor=d,value=match[3],corpus_row_json=json.dumps(row,sort_keys=True),
            independent_source_line=independent[row['id']],independent_country_json=json.dumps(countries[row['id']],sort_keys=True)))
    return SourceManifest(evidence_kind=evidence_kind,corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),
        independent_source_sha256=hashlib.sha256(independent_bytes).hexdigest(),
        independent_countries_sha256=hashlib.sha256(countries_bytes).hexdigest(),facts=tuple(facts))


def question_plan(question,catalog):
    catalog=Catalog.model_validate(catalog)
    if not isinstance(question,str) or len(question)>1000:raise BindingError('unsupported_category: bounded V2 question required')
    match=re.fullmatch(rf'What is the (area|population) of (.+), and what is that (area|population) plus ({_NUMBER})( square kilometres)?\? Give both values\.',question.strip(),re.I)
    if not match or match[1].lower()!=match[3].lower():raise BindingError('unsupported_category: finite V2 fact-plus-addition grammar required')
    choices=[d for d in catalog.descriptors if d.entity.casefold()==match[2].casefold() and d.measure==match[1].lower()]
    if len(choices)!=1 or bool(match[5])!=(match[1].lower()=='area'):
        raise BindingError('unsupported_category: entity/measure/units not in source catalog')
    d=choices[0]
    return ComponentPlan(d.measure,d.entity,match[4],version=VERSION)


def validation_id(root,bound):
    if not isinstance(root,str) or not root.strip():raise BindingError('identity: root ID required')
    return digest([VERSION,root,bound.component_id,bound.binding_id])


def component_analysis(bound):
    """Opt-in V2 task typing after finite-grammar binding, including multiword entities."""
    from app.analysis.task_analyzer import TaskQuestionAnalyzer
    from app.analysis.research_context import build_research_context
    analysis=TaskQuestionAnalyzer().analyze(bound.question)
    analysis.verification_types=[bound.requirement]
    analysis.research_context=build_research_context(analysis)
    analysis.research_context.scoring_version='source_backed_component_questions_v2'
    return analysis


def validate_source_material(manifest,files):
    """Recheck serialized empirical facts against actual immutable raw files."""
    from pathlib import Path
    import hashlib
    required={'corpus.json','geonames-countryInfo.txt','countries.json'}
    by_name={Path(path).name:(Path(path),digest_value) for path,digest_value in files}
    if len(files)!=3 or set(by_name)!=required:raise ValueError('empirical sources require the three actual raw material files')
    for path,digest_value in by_name.values():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest_value:raise ValueError('independent source material changed')
    actual=source_manifest(*(by_name[name][0].read_bytes() for name in ('corpus.json','geonames-countryInfo.txt','countries.json')),
        evidence_kind=manifest.evidence_kind)
    if actual!=manifest:raise ValueError('serialized source manifest differs from actual independent material')
