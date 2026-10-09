# Question analyzer setup

`QuestionAnalyzer.analyze` still returns `domain`, `difficulty`, and `difficulty_score`. The default mode is `heuristic`. Heuristic analysis supplies conservative `direct_fact` and `arithmetic` routing hints for recognized lookup and calculation forms. An empty list preserves ranking by domain reputation and resource estimates, with no suitability bonus. When `verification_types` is not empty, the selector uses that list as a suitability hint and still uses `domain` for reputation. Subject, domain candidates, domain status, rubric ratings, analysis method, and fallback reason do not change selection, reputation, or the decision score.

This module does not load a `.env` file. Importing the answer generator can load one, because that module calls `load_dotenv`. The analyzer does not import the answer generator. Set variables in the process environment before constructing `QuestionAnalyzer`.

## Modes

`ANALYZER_MODE` is `heuristic` or `ollama`. When the variable is absent, the mode is `heuristic`, which is the existing keyword scorer.

Heuristic output uses `analysis_method` `heuristic`. It does not claim to be model analysis. `rubric_ratings` is null. `subject` is empty. `verification_types` contains a recognized routing hint or is empty. `domain_status` describes the same keyword counts:

- one specialist list wins: `clear`, and `domain` is `medical` or `technical`; this remains true even when the other list has fewer hits
- the two lists tie: `mixed`, and `domain` stays `general`
- no domain cue: `unknown`, and `domain` stays `general`

Heuristic hints are routing suggestions, not correctness judgments. Recognized lookup forms include "Who wrote Hamlet?" and "What is the capital of France?". Numeric expressions such as "What is 2 + 2?" and sum/product/difference wording receive `arithmetic`, ahead of generic factual phrasing. Explanation, hypothetical, and advice cues suppress these hints. Other who/what questions receive no hint by default.

Explicit task prefixes such as "Write a Python function" add one technical domain cue without changing the difficulty formula. Standalone language names and the word "function" are insufficient. This cue participates in the existing domain-count policy: exact ties are mixed; a unique winner remains clear. This policy does not detect every semantically mixed question.

## Enable Ollama in PowerShell

```powershell
$env:ANALYZER_MODE = "ollama"
$env:OLLAMA_URL = "http://localhost:11434/api/generate"
$env:ANALYZER_MODEL = "llama3.2:3b"
$env:ANALYZER_TIMEOUT_SECONDS = "15"
```

`OLLAMA_URL` defaults to `http://localhost:11434/api/generate`. `ANALYZER_MODEL` is the model name. If it is unset or blank, the analyzer uses `OLLAMA_MODEL`, then `llama3.2:3b`. `ANALYZER_TIMEOUT_SECONDS` defaults to 15 and must be a positive finite number. `ANALYZER_MODE` must be `heuristic` or `ollama`. Invalid values raise `ValueError` when the analyzer is constructed.

The call is one synchronous `httpx` POST. `stream` is false. `format` is a JSON-schema object requiring all eight assessment fields, limiting domain/hint labels and integer rubric values, and excluding extra fields. Generation options set `temperature` to 0 and `seed` to 0 where Ollama honors them. There are no retries. The system instruction and the question travel in different fields. The question is a JSON object, `{"question": "..."}`, and is treated as untrusted data.

This request was live-tested with Ollama `0.35.1` and `llama3.2:3b`. The
generate API's schema format is documented at
<https://docs.ollama.com/api/generate>. An older server that rejects the
format produces the existing HTTP-error fallback; the analyzer does not
retry using weaker unconstrained output. Python still strictly validates
the response, including domain/status/candidate consistency, subject
whitespace, and unique lists. A server accepting the schema does not prove
that every schema keyword is enforced by its generation grammar.

The reproduced pre-fix geography response was complete (`done: true`,
`done_reason: stop`) but omitted `subject` despite the system instruction.
Generic JSON format did not require that field. The schema requires it.
An initial schema-only trial then returned all three domains as candidates
for a clear general question. The prompt now describes matching domains
rather than domains "considered" and includes complete geography and
programming examples. Explicit code-writing requests are technical;
factual lookup and arithmetic are distinct from checking program behavior.
These remain model-generated routing hints, not correctness guarantees.

The initial cold call also exceeded the unchanged 15-second budget. Model
loading, prompt evaluation, and generation are separate from schema
validity. A cold server can legitimately fall back with `timeout`; do not
label this successful model analysis. A longer timeout can be selected
explicitly for diagnostics or a deployment's measured latency budget.
Loading the model ahead of a latency-sensitive request is an operational
choice, not an automatic retry or a changed analyzer default.

In the measured model-process reload, a valid geography assessment took
24.582 seconds wall time with a 60-second diagnostic budget: Ollama reported
6.763 seconds loading, 9.482 seconds evaluating the uncached prompt, and
5.867 seconds generating. Warm five-subject calls with the unchanged
15-second timeout all used Ollama successfully. These are observations on
one CPU host, not latency guarantees. The initial live programming output
was schema-valid and correctly technical but included excess
`direct_fact`/`arithmetic` hints. The routing contract below addresses this
recognized case; schema enforcement alone does not establish routing accuracy.

### Code-artifact routing contract

`direct_fact` asks for a factual-answer capability, and `arithmetic` asks
for a numerical-answer capability. They are obligations in orchestration,
not harmless subject tags. A request whose deliverable is code does not
require these capabilities merely because that code calculates numbers,
converts units, or looks up facts. Program behavior can instead use
`logical_rule`, `semantic_comparison`, `consistency`, or documentation
retrieval through `evidence_retrieval`. These hints do not guarantee that
an available verifier can check the program.

The analyzer applies this rule conservatively to explicit write/implement/
debug/refactor/create/generate requests for a function, program, script,
class, or code in Python, JavaScript, TypeScript, Java, or C++. It accepts
bounded modifiers such as "sorting function" and polite request prefixes.
Any nonempty continuation separated by a sentence boundary, comma, or
and/also/then/additionally leaves all hint types available. Coordination
inside a program specification is ambiguous too and stays unrestricted. Thus
"write a function that adds integers" remains a code-artifact task, while
"write a function; calculate 2 + 2" retains the separate numerical obligation.
Requests to give/provide an answer, tell me a fact, or ask a separate
question retain their answer capabilities. Unknown or ambiguous task forms remain unrestricted; this is not a general
natural-language parser or a universal routing-accuracy guarantee.

For recognized code-only tasks, the request schema excludes `direct_fact`
and `arithmetic`. A separate Python check rejects either hint even if the
server returns it in otherwise structurally valid JSON. Such a result uses
the existing whole-assessment heuristic fallback with `invalid_routing`;
the analyzer does not delete hints, fabricate fields, rewrite domains, or
report the rejected assessment as successful Ollama analysis. Other domain,
subject, rubric, and mixed-domain rules are unchanged. On fallback, explicit
additional answer clauses in a recognized code request are separately passed
through the existing heuristic hint recognizer. Bounded give/provide/tell-me
phrases are normalized to factual lookup or calculation wording. Recognized
hints are added to the whole heuristic result without changing its domain,
score, or failure reason. This preserves the confirmed capital lookup and
2 + 2 obligations even on timeout or malformed model output. Program-relative
clauses such as "that returns a country's capital" and "that adds two integers"
are not separate answer tasks. Unrecognized wording remains a heuristic
limitation; this is not a general mixed-task parser.

In a controlled trace of the actual earlier four-hint output, default
ranking was rule, semantic, evidence, confidence. The rule and evidence
abstained; two agreeing generic votes scored 0.95 numerically but exhausted
the candidates with missing arithmetic and direct-fact coverage, yielding
public uncertainty. Removing those inappropriate *requested* capabilities
at the analyzer boundary permits an approved stop once the same two
contributors meet the existing cuts. Coverage safeguards are unchanged.
This controlled trace verifies wiring, not the correctness of generated code.

The follow-up warm live checks covered Python sorting (including a modifier
before "function"), JavaScript integer addition, and Python unit conversion.
All passed both structural and routing validation at the unchanged timeout;
none requested factual/numerical answer coverage. A mixed request for a
sorting function followed by "What is 2 + 2?" retained `arithmetic`.
The model still sometimes selected all four allowed nonfactual hints, so
hint relevance is not guaranteed. One successful call took 16.294 seconds
wall time: HTTPX's 15-second timeout applies to network operations, not an
absolute deadline including client setup. Warm calls passing the default
timeout do not imply that cold calls pass it; the measured cold reload
above required more than 15 seconds and can still trigger timeout fallback.


### Mixed-task follow-up verification

The code-only recognizer now leaves coordinated or separate clauses
unrestricted rather than relying on a finite list of second-task verbs.
Regression cases include give/provide/tell-me requests, separate questions,
ambiguous program coordination, and code-only capital lookup/integer addition.
Connected controlled checks confirm that generic agreement cannot replace
missing direct-fact/arithmetic coverage, including after analyzer fallback.
No stopping or coverage implementation was changed.

In the bounded follow-up live matrix on Ollama 0.35.1 / llama3.2:3b, three
of five calls produced strictly valid Ollama assessments: the code-plus-
arithmetic request (8.806 seconds), code-plus-Hamlet request (8.040 seconds),
and code-only integer addition (7.964 seconds). Two calls returned invalid
domain metadata and used strict fallback: code-plus-France (16.128 seconds,
retaining direct_fact) and code-only capital lookup (8.455 seconds, no answer
obligation). These are fallbacks, not successful model classifications.
All used the default 15-second network-operation timeout after a separately
reported operational model-load request. An initial matrix also observed a
timeout on code-plus-France; its fallback retained direct_fact.

The arithmetic multi-task output included an excess direct_fact hint alongside
arithmetic. The unrestricted schema keeps separately requested capabilities
eligible; it does not prove every model-selected hint is relevant. The model
can still produce inconsistent domain metadata or excessive requirements,
leading to fallback or justified public uncertainty. Python validation,
downstream factual coverage, and cold-start timeout behavior remain strict.

## Rubric

The model returns three integers, each 0, 1, or 2. It does not return a score, a band, or a confidence.

| Rating | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `reasoning_depth` | direct check of one fact or one calculation | a few linked steps | substantial multi-step reasoning or a proof |
| `evidence_burden` | self-contained, or one straightforward source | a specialized source or several facts | multiple independent sources, or conflicting or time-sensitive evidence |
| `constraint_interactions` | one simple requirement | several mostly independent requirements | interacting conditions, exceptions, or edge cases |

Python sets:

```text
difficulty_score = round((reasoning_depth + evidence_burden + constraint_interactions) / 6, 2)
```

The band cuts are unchanged: below 0.35 is `easy`, below 0.65 is `medium`, and 0.65 or above is `hard`. This mapping is an initial rubric. It is not a probability and it has not been fitted on labeled questions. Length, punctuation, specialist vocabulary, and words such as "why" are not inputs to the score.

Primary domains stay `general`, `medical`, and `technical`. A clear non-specialist subject uses `domain` `general`, `domain_status` `clear`, and `domain_candidates` `["general"]`. An unknown question uses `domain` `general`, `domain_status` `unknown`, an empty candidate list, and an empty subject. A mixed question uses `domain` `general` so existing downstream code still sees one domain, with at least two candidates in the metadata.

`verification_types` may contain one to four labels, without duplicates, from:

`direct_fact`, `arithmetic`, `logical_rule`, `semantic_comparison`, `evidence_retrieval`, `consistency`.

## Fallback

Blank text raises `ValueError`. A non-string raises `TypeError`. Neither makes a request.

If Ollama times out, returns an HTTP error, or returns an envelope or object that fails validation, `analyze` returns the heuristic result. `analysis_method` is `heuristic_fallback`. `fallback_reason` is one of:

- `timeout`
- `http_error`
- `malformed_envelope`
- `malformed_json`
- `invalid_schema`
- `invalid_routing`: structurally valid hints violate the code-artifact contract.
- `error_envelope`: Ollama returned an error field.
- `incomplete_envelope`: done was missing or was not exactly true.
- `duplicate_key`: the assessment JSON contained a repeated key.

Excessively nested JSON at either decoding boundary uses `malformed_envelope` or `malformed_json`, respectively, and returns the same heuristic fields as direct analysis. The recursion limit is unchanged.

The reason does not include the question, the response body, or the exception text. Other exceptions are not caught.

## Smoke test

Heuristic, which does not contact Ollama:

```powershell
$env:ANALYZER_MODE = "heuristic"
@'
from app.analysis.question_analyzer import QuestionAnalyzer
analysis = QuestionAnalyzer().analyze("What is 2 + 2?")
print(
    analysis.analysis_method,
    analysis.domain,
    analysis.subject,
    analysis.verification_types,
    analysis.difficulty_score,
    analysis.difficulty,
    analysis.fallback_reason,
)
'@ | .\.venv\Scripts\python.exe -
```

Ollama, after the variables in the section above are set:

```powershell
@'
from app.analysis.question_analyzer import QuestionAnalyzer
analysis = QuestionAnalyzer().analyze("What is 2 + 2?")
print(
    analysis.analysis_method,
    analysis.domain,
    analysis.subject,
    analysis.verification_types,
    analysis.difficulty_score,
    analysis.difficulty,
    analysis.fallback_reason,
)
'@ | .\.venv\Scripts\python.exe -
```

A live Ollama print shows whether the call connected. It is not a measured test of classification quality.

## Capture a live integration failure

Run this from the repository root with the existing virtual environment. It
uses the actual analyzer and a recording HTTP transport, not supplied model
responses. It changes no persistent configuration and does not download a
model. The explicit empty environment mapping selects the documented local
endpoint and `llama3.2:3b`, without printing unrelated environment values.
The raw responses below contain only the fixed diagnostic questions; avoid
using confidential questions when sharing a capture.

The first two calls compare the reported 15- and 60-second behavior. The
remaining calls exercise five subjects with a 60-second diagnostic budget.
That budget is not a proposed production default. A cold load can consume
time before generation; compare Ollama's `load_duration`, `total_duration`,
`eval_count`, and `done_reason` with wall time. Durations in the envelope are
nanoseconds. A later call may benefit from the first call loading the model.

```powershell
@'
import json
import time
import httpx
from app.analysis.question_analyzer import QuestionAnalyzer
from app.analysis import model_assessment as schema

def schema_error(payload):
    if not isinstance(payload, dict):
        return "assessment must be an object"
    if set(payload) != schema.EXPECTED_KEYS:
        return {"missing": sorted(schema.EXPECTED_KEYS - set(payload)),
                "unexpected": sorted(set(payload) - schema.EXPECTED_KEYS)}
    checks = [
        ("domain", lambda: schema._label(payload["domain"], schema.PRIMARY_DOMAINS)),
        ("domain_status", lambda: schema._label(payload["domain_status"], schema.DOMAIN_STATUSES)),
        ("subject", lambda: schema._subject(payload["subject"], payload["domain_status"])),
        ("domain_candidates", lambda: schema._candidates(payload["domain_candidates"])),
        ("verification_types", lambda: schema._verification_types(payload["verification_types"])),
    ]
    checks += [(name, lambda name=name: schema._rating(payload[name]))
               for name in schema.RUBRIC_FIELDS]
    checks.append(("domain consistency", lambda: schema._check_domain_consistency(
        payload["domain"], payload["domain_status"], payload["domain_candidates"])))
    for field, check in checks:
        try:
            check()
        except schema.AnalyzerResponseError:
            return {"failed_check": field, "payload": payload}
    return None

class RecordingClient:
    def __init__(self):
        self.response = None
    def post(self, url, *, json, timeout):
        limits = httpx.Timeout(timeout, connect=3, write=3, pool=3)
        self.response = httpx.post(url, json=json, timeout=limits)
        return self.response

with httpx.Client(timeout=3) as client:
    print("VERSION", client.get("http://localhost:11434/api/version").text)
    tags = client.get("http://localhost:11434/api/tags")
    tags.raise_for_status()
    print("MODELS", [item["name"] for item in tags.json().get("models", [])])

cases = [("baseline", "What is the capital of France?", timeout) for timeout in (15, 60)]
cases += [(subject, question, 60) for subject, question in [
    ("geography", "What is the capital of France?"),
    ("history", "Who was the first president of the United States?"),
    ("arithmetic", "What is 2 + 2?"),
    ("programming", "Write a Python function to sort a list."),
    ("medical", "What is hypertension?"),
]]
for subject, question, timeout in cases:
    recorder = RecordingClient()
    analyzer = QuestionAnalyzer(mode="ollama", timeout_seconds=timeout,
                                client=recorder, environ={})
    started = time.perf_counter()
    analysis = analyzer.analyze(question)
    elapsed = time.perf_counter() - started
    validity = "no response"
    routing_validity = "not evaluated"
    if recorder.response is not None:
        print("RAW_ENVELOPE", recorder.response.text)
        try:
            payload = schema.parse_envelope(recorder.response.json())
            assessment = schema.validate_assessment(payload)
            validity = "valid"
            try:
                schema.validate_routing(assessment, question)
                routing_validity = "valid"
            except schema.AnalyzerResponseError as error:
                routing_validity = error.code
        except schema.AnalyzerResponseError as error:
            validity = {"code": error.code}
            if error.code == "invalid_schema":
                validity["detail"] = schema_error(payload)
        except (json.JSONDecodeError, RecursionError):
            validity = "malformed outer JSON"
    print(json.dumps({"case": subject, "timeout_seconds": timeout,
        "analysis_source": analysis.analysis_method,
        "fallback_reason": analysis.fallback_reason,
        "domain": analysis.domain, "subject": analysis.subject,
        "verification_hints": analysis.verification_types,
        "difficulty": analysis.difficulty, "schema_validity": validity,
        "routing_validity": routing_validity,
        "elapsed_seconds": round(elapsed, 3)}, ensure_ascii=False))
'@ | .\.venv\Scripts\python.exe -B -
```

The field diagnostic deliberately reuses the current strict checks; it does
not fill missing fields, coerce ratings, or change the fallback. A successful
live assessment requires `schema_validity: "valid"`, `routing_validity: "valid"`, and
`analysis_source: "ollama"` with no fallback reason. Schema validity alone
does not establish domain/subject accuracy. Preserve the raw invalid output
as a regression fixture only after reproducing it. Check the installed API
version and structured-output support before proposing a JSON-schema format
change. The pre-fix generic `format: "json"` guaranteed neither required
keys nor the allowed values; the current request supplies a schema, and
Python validation remains authoritative.

## Limitations

- The default analyzer mode is `heuristic`. Unrecognized questions retain an empty `verification_types` list and the previous ranking; recognized heuristic hints intentionally change suitability ranking. A non-empty list can change verifier order. It does not change how many verifiers the difficulty range requests, and it does not change vote weights. The other metadata fields are not read by the selector or the decision engine. Reputation still uses `domain` only.
- The rubric cuts are the old uncalibrated thresholds.
- Only three primary domains exist. Finer subject text is not a new domain key.
- Heuristic fallback can still mark a question hard because it is long or contains "why". That path is labeled `heuristic_fallback`.
- One failed request is not retried. The default wait is 15 seconds.
- `temperature` 0 does not make every model deterministic.


## Derived research context (v1)

Every `QuestionAnalyzer.analyze()` result now has an optional
`research_context` dataclass, attached after its final legacy fields are
complete. Old positional/keyword `QuestionAnalysis` construction still works
and defaults this field to `None`. Direct low-level `heuristic_analysis()`
construction remains unchanged. No additional Ollama call or response-schema
field is introduced. Strict validation, fallback reasons, domain policy,
legacy hints, scores, and thresholds are unchanged.

Fields:

- `context_version`: `question_context_v1`, the context contract identifier.
- `verification_requirements`: unique existing labels in canonical order:
  direct_fact, arithmetic, logical_rule, semantic_comparison,
  evidence_retrieval, consistency. Legacy `verification_types` keeps its
  original order/content. Unrecognized legacy labels are not requirements.
- `requirement_weights`: all six labels, each assigned `1/N` if among the N
  identified unique requirements, otherwise zero. These are uncalibrated
  relative demand weights, not probabilities, accuracy, or information gain.
- `requirements_known`: true iff at least one supported requirement was
  identified; it does not establish completeness. Zero weight on another
  label does not prove that obligation is absent. This flag must not be used
  as a complete-coverage stopping condition. An all-zero vector with false means unknown requirements,
  not evidence that verification demand is zero.
- `normalized_rubric`: reasoning_depth, evidence_burden, and
  constraint_interactions divided by two, or `None` when ratings are absent.
  The rubric is an ordinal feature vector, not a correctness probability.
- `domain_status`, `analysis_method`: copied categorical provenance; no
  numerical confidence is inferred from them.
- `scoring_version`: `heuristic_surface_features_v1` for the existing
  weighted surface features, including fallback; `rubric_sum_over_six_v1`
  for successful Ollama ratings. These identify the current formulas,
  rounding and bands described above; changing those requires a new version.

Each output owns fresh context/list/dictionary containers, detached from its
legacy hints and rubric. Context is an output snapshot: later mutation of
legacy fields does not automatically rebuild it. `dataclasses.asdict()` and
FastAPI's `jsonable_encoder()` recursively serialize it. The existing
`/validate` response does not expose the complete analyzer object, so this
change neither extends that endpoint nor alters shared API schemas. Python
research callers can consume `analysis.research_context` or serialize the
analysis explicitly.

Examples (from existing validated or fallback outputs, not new rules):

- A validated code-only assessment with `verification_types=["logical_rule"]`
  yields requirements `["logical_rule"]`, weight one on logical_rule and
  zero on the other five labels. A heuristic code-only result with no hints
  instead has unknown requirements and an all-zero vector; the context does
  not invent capabilities that the analyzer did not identify.
- A code-plus-answer assessment with hints `["logical_rule", "arithmetic"]`
  yields canonical `["arithmetic", "logical_rule"]` with weights 0.5 each.
  On timeout for "Write a Python function to sort a list and provide the
  answer to 2 + 2.", fallback preserves `["arithmetic"]`; context therefore
  assigns arithmetic one, with `analysis_method="heuristic_fallback"` and
  `normalized_rubric=None`. It is built after the additional-clause hints.

Future selection may consume these inputs alongside independently specified
capabilities, resource constraints and reputation, with explicit missing-data
handling. The current selector ignores research_context and continues reading
legacy fields. This change does not infer an answer, ground truth, reputation,
costs, utility, coalitions, incentives, equilibrium, or information gain.
It does not establish game-theoretic behavior or research novelty.

### Small offline semantic evaluation

`tests/fixtures/analyzer_semantic_examples.json` contains ten illustrative
human-authored semantic expectations. They are distinct from exact parser and
unit-test assertions, are not independently annotated, and are not a research
benchmark. Null difficulty means unlabeled. Empty expected requirements on
ambiguous text mean no identifiable requirement, not known zero demand.

Run without services, downloads, external network, or new dependencies:

```powershell
.\.venv\Scripts\python.exe -B -m app.analysis.evaluate_context
```

Default evaluation explicitly uses heuristic mode with an empty environment
mapping. Capture outputs and independently re-score them:

```powershell
.\.venv\Scripts\python.exe -B -m app.analysis.evaluate_context --save-outputs $env:TEMP/analyzer-outputs.json
.\.venv\Scripts\python.exe -B -m app.analysis.evaluate_context --outputs $env:TEMP/analyzer-outputs.json
```

Supplied output format is a JSON array of objects with `id` and `analysis`
(the serialized QuestionAnalysis). IDs must match all fixture cases exactly
once. Domain/status accuracy, micro verification-type precision/recall,
labeled difficulty-band agreement, and fallback rate are reported separately,
with denominators/counts and analysis-method counts. Undefined precision or
recall is null, never silently perfect. Heuristic mode is not a fallback;
a zero fallback rate says nothing about semantic accuracy. No live mode is
implemented here. Evaluating supplied live captures does not rerun a model
or independently attest their provenance. Unit-test passes are contract
checks, not evidence of semantic or research performance.

The ten-case v2 fixture adds a long but simple single calculation (rubric
0/0/0, easy) and a short prime-number-theorem proof (2/1/2, hard). Each has
an explicit difficulty rationale: verification work, not length, determines
the semantic label. These are human judgments, not target assertions for the
heuristic; mismatches remain visible and do not tune its scoring.

Evaluator inputs are validated before metrics are computed or output captures
are written: object/list structure, required label fields, supported labels,
explicit null for unlabeled expected difficulty, and unique nonempty matching
IDs. Invalid supplied analyses or expected labels raise case/field-specific
ValueError messages. A rejected run neither creates nor overwrites the
--save-outputs target. Verification-type comparison remains set-based.
