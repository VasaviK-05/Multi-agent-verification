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
