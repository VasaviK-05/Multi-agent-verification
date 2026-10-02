# Question analyzer setup

`QuestionAnalyzer.analyze` still returns `domain`, `difficulty`, and `difficulty_score`. Extra fields are metadata. The selector, reputation table, and decision engine do not read them.

This module does not load a `.env` file. Importing the answer generator can load one, because that module calls `load_dotenv`. The analyzer does not import the answer generator. Set variables in the process environment before constructing `QuestionAnalyzer`.

## Modes

`ANALYZER_MODE` is `heuristic` or `ollama`. When the variable is absent, the mode is `heuristic`, which is the existing keyword scorer.

Heuristic output uses `analysis_method` `heuristic`. It does not claim to be model analysis. `rubric_ratings` is null. `subject` and `verification_types` are empty. `domain_status` describes the same keyword counts:

- one specialist list wins: `clear`, and `domain` is `medical` or `technical`
- the two lists tie: `mixed`, and `domain` stays `general`
- no domain cue: `unknown`, and `domain` stays `general`

## Enable Ollama in PowerShell

```powershell
$env:ANALYZER_MODE = "ollama"
$env:OLLAMA_URL = "http://localhost:11434/api/generate"
$env:ANALYZER_MODEL = "llama3.2:3b"
$env:ANALYZER_TIMEOUT_SECONDS = "15"
```

`OLLAMA_URL` defaults to `http://localhost:11434/api/generate`. `ANALYZER_MODEL` is the model name. If it is unset or blank, the analyzer uses `OLLAMA_MODEL`, then `llama3.2:3b`. `ANALYZER_TIMEOUT_SECONDS` defaults to 15 and must be a positive finite number. `ANALYZER_MODE` must be `heuristic` or `ollama`. Invalid values raise `ValueError` when the analyzer is constructed.

The call is one synchronous `httpx` POST. `stream` is false. `format` is `json`. Generation options set `temperature` to 0 and `seed` to 0 where Ollama honors them. There are no retries. The system instruction and the question travel in different fields. The question is a JSON object, `{"question": "..."}`, and is treated as untrusted data.

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
- `error_envelope`: Ollama returned an error field.
- `incomplete_envelope`: done was missing or was not exactly true.
- `duplicate_key`: the assessment JSON contained a repeated key.

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

## Limitations

- Metadata does not change which verifiers run or how votes are weighted.
- The rubric cuts are the old uncalibrated thresholds.
- Only three primary domains exist. Finer subject text is not a new domain key.
- Heuristic fallback can still mark a question hard because it is long or contains "why". That path is labeled `heuristic_fallback`.
- One failed request is not retried. The default wait is 15 seconds.
- `temperature` 0 does not make every model deterministic.
