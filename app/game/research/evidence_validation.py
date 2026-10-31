"""Versioned retained evidence of public coverage semantics; never an approval flag."""
from typing import Literal
from pydantic import model_validator
from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.resource_provenance import VerifierResources
from app.models.schemas import VerificationResult
from app.decision.coverage import factual_capabilities
from app.decision.vote_normalization import is_abstention

# Fixed software-validation cases, separate from study candidates/outcomes.
EXPECTED = {
    'controlled_support': ('SUPPORT', True),
    'controlled_rejection': ('REJECT', True),
    'controlled_neutral': ('UNSURE', False),
    'controlled_conflict': ('UNSURE', False),
    'real_nli_support': ('SUPPORT', True),
    'real_nli_rejection': ('REJECT', True),
    'real_nli_neutral': ('UNSURE', False),
}

class EvidenceProbe(FrozenModel):
    case_id: str
    report_json: str

class EvidenceValidation(FrozenModel):
    version: Literal['evidence_public_contract_validation_v2']
    before: VerifierResources
    after: VerifierResources
    probes: tuple[EvidenceProbe, ...]

    @model_validator(mode='after')
    def check(self):
        if self.before != self.after or self.before.verifier_name != 'evidence':
            raise ValueError('evidence validation requires stable actual evidence resource observations')
        if len(self.probes)!=len(EXPECTED) or {p.case_id for p in self.probes}!=set(EXPECTED):
            raise ValueError('complete unique controlled and real-NLI probe suite required')
        for probe in self.probes:
            row=VerificationResult.model_validate_json(probe.report_json)
            decision,covered=EXPECTED[probe.case_id]
            if (row.verifier_name!='evidence' or (row.metadata or {}).get('decision')!=decision
                    or row.passed != (decision=='SUPPORT')
                    or is_abstention(row)!=(decision=='UNSURE')
                    or ('direct_fact' in factual_capabilities(row))!=covered):
                raise ValueError('public evidence probe failed: '+probe.case_id)
            if probe.case_id=='controlled_conflict' and row.metadata.get('unsure_reason')!='conflict':
                raise ValueError('conflicting evidence must remain uncertainty without achieved coverage')
        return self

    @property
    def validation_id(self):
        return content_id(self.model_dump(mode='json'))

    def require_resources(self,manifest):
        if manifest is None:
            raise ValueError('evidence validation requires resource-bound execution v2')
        manifest.require_observation(self.before)
