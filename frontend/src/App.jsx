import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement));

  useEffect(() => {
    const syncFullscreen = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  const resizeTextarea = (event, updateValue) => {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
    updateValue(textarea.value);
  };

  const enterPresentationMode = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (fullscreenError) {
      console.error("Fullscreen mode could not be enabled:", fullscreenError);
    }
  };

  const startNewChat = () => {
    setQuestion("");
    setSubmittedQuestion("");
    setAnswer("");
    setContext("");
    setResult(null);
    setError("");
    setShowResults(false);
  };

  const generateAnswer = async () => {
    if (generating || loading) return;
    if (!question.trim()) {
      setError("Enter a question before generating an answer.");
      return;
    }

    setGenerating(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/generate-answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });

      if (!response.ok) throw new Error("Failed to generate an answer. Please try again.");
      const data = await response.json();
      setSubmittedQuestion(question.trim());
      setAnswer(data.answer || "");
    } catch (requestError) {
      setError(requestError.message || "Unable to generate the answer. Check your connection and try again.");
    } finally {
      setGenerating(false);
    }
  };

  const validateAnswer = async (providedContext = "") => {
    if (loading || generating) return;
    if (!question.trim() || !answer.trim()) {
      setError("A question and generated answer are required before validation.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          answer: answer.trim(),
          context: providedContext.trim() || null,
        }),
      });

      if (!response.ok) throw new Error("Validation failed. Please try again.");
      const data = await response.json();
      setResult(data);
      setShowResults(true);
      setHistory((previous) => [
        {
          question,
          answer,
          context: providedContext,
          result: data,
        },
        ...previous,
      ]);
    } catch (requestError) {
      setError(requestError.message || "Unable to validate the answer. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const submitContext = () => validateAnswer(context);

  const skipContext = () => {
    setContext("");
    validateAnswer("");
  };

  const openHistory = (item) => {
    setQuestion(item.question);
    setSubmittedQuestion(item.question);
    setAnswer(item.answer);
    setContext(item.context || "");
    setResult(item.result);
    setShowResults(true);
    setError("");
  };

  const getScorePercentage = (score) => {
    if (score === null || score === undefined || Number.isNaN(Number(score))) return 0;
    return Math.round(Number(score) * 100);
  };

  const scoreBarWidth = (score) => Math.max(0, Math.min(100, getScorePercentage(score)));
  const voteResults = (result?.results || []).filter(
    (verifier) => verifier.metadata?.pipeline_role === "vote",
  );
  const status = (result?.final_status || "uncertain").toLowerCase();

  return (
    <div className="app">
      <aside className="sidebar" aria-label="Validation history">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true"><span /></div>
          <div className="brand-name">
            <strong>MAV</strong>
            <span>Multi-Agent Validator</span>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewChat}
          data-testid="button-new-validation"
          type="button"
        >
          <span className="plus" aria-hidden="true">+</span>
          <span>New validation</span>
        </button>

        <button
          className="presentation-button"
          onClick={enterPresentationMode}
          data-testid="button-presentation-mode"
          type="button"
          aria-pressed={isFullscreen}
        >
          <span className="presentation-glyph" aria-hidden="true" />
          {isFullscreen ? "Exit presentation mode" : "Presentation mode"}
        </button>

        <section className="previous-section" aria-labelledby="history-heading">
          <h2 className="previous-heading" id="history-heading">
            <span>Recent validations</span>
            <span className="history-count" data-testid="text-history-count">
              {String(history.length).padStart(2, "0")}
            </span>
          </h2>
          {history.length === 0 ? (
            <p className="empty-history" data-testid="text-history-empty">
              Your validated questions will be kept here for this session.
            </p>
          ) : (
            <div className="history-list">
              {history.map((item, index) => (
                <button
                  key={`${item.question}-${index}`}
                  className="history-item"
                  onClick={() => openHistory(item)}
                  data-testid={`button-history-${index}`}
                  type="button"
                  title={item.question}
                >
                  {item.question}
                </button>
              ))}
            </div>
          )}
        </section>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" aria-hidden="true" />
            Independent agents · Session only
          </div>
        </div>
      </aside>

      <main className="main-content">
        <div className="main-topline">
          <div className="eyebrow">
            <span className="eyebrow-mark" aria-hidden="true" />
            Evidence before certainty
          </div>
          <span className="run-index">MAV / VALIDATION</span>
        </div>

        {!showResults ? (
          <>
            <header className="page-header">
              <div className="eyebrow">Multi-agent answer review</div>
              <h1>Ask with confidence.<br />Verify with evidence.</h1>
              <p>
                Generate an answer, then challenge it with independent verifier agents.
                See every vote and how the final decision was reached.
              </p>
            </header>

            <div className="chat-container">
              {!submittedQuestion && !answer ? (
                <div className="welcome-area">
                  <div className="welcome-icon brand-mark" aria-hidden="true"><span /></div>
                  <h2>Start with a question</h2>
                  <p>Your question becomes the claim. MAV will generate an answer, then put it through independent review.</p>
                </div>
              ) : (
                <div className="conversation">
                  {submittedQuestion && (
                    <div className="message user-message">
                      <div className="message-label">Question</div>
                      <div className="user-bubble" data-testid="text-submitted-question">{submittedQuestion}</div>
                    </div>
                  )}
                  {answer && (
                    <div className="message ai-message">
                      <div className="message-label">Generated answer</div>
                      <div className="ai-response" data-testid="text-generated-answer">{answer}</div>
                    </div>
                  )}
                  {answer && (
                    <div className="message ai-message context-message">
                      <div className="ai-response context-response">Add evidence or context for the reviewers</div>
                      <div className="context-hint">Optional · source details can help agents assess the answer.</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {!answer && (
              <form
                className="composer-area"
                onSubmit={(event) => {
                  event.preventDefault();
                  generateAnswer();
                }}
              >
                <div className="composer">
                  <textarea
                    className="question-composer"
                    placeholder="What would you like to verify?"
                    value={question}
                    onChange={(event) => resizeTextarea(event, setQuestion)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        generateAnswer();
                      }
                    }}
                    rows="1"
                    aria-label="Question to verify"
                    data-testid="input-question"
                    disabled={generating}
                  />
                  <button
                    className="send-button"
                    type="submit"
                    onClick={(event) => {
                      if (!question.trim()) {
                        event.preventDefault();
                        generateAnswer();
                      }
                    }}
                    disabled={generating}
                    title="Generate answer"
                    aria-label="Generate answer"
                    data-testid="button-generate-answer"
                  >
                    {generating ? <span className="loading-mark" aria-hidden="true" /> : <span className="send-arrow" aria-hidden="true">↑</span>}
                  </button>
                </div>
                <p className="composer-hint">Enter to generate · Shift + Enter for a new line</p>
              </form>
            )}

            {answer && !loading && (
              <form
                className="composer-area context-composer-area"
                onSubmit={(event) => {
                  event.preventDefault();
                  submitContext();
                }}
              >
                <div className="composer">
                  <textarea
                    className="question-composer"
                    placeholder="Add supporting context (optional)"
                    value={context}
                    onChange={(event) => resizeTextarea(event, setContext)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        submitContext();
                      }
                    }}
                    rows="1"
                    aria-label="Optional supporting context"
                    data-testid="input-context"
                    disabled={loading}
                  />
                  <button
                    className="send-button"
                    type="submit"
                    disabled={loading}
                    title="Validate answer"
                    aria-label="Validate answer with context"
                    data-testid="button-validate-answer"
                  >
                    <span className="send-arrow" aria-hidden="true">↑</span>
                  </button>
                </div>
                <div className="composer-actions">
                  <button
                    className="skip-button"
                    onClick={skipContext}
                    disabled={loading}
                    type="button"
                    data-testid="button-skip-context"
                  >
                    Skip context and validate
                  </button>
                </div>
                <p className="composer-hint">Enter to validate with this context</p>
              </form>
            )}

            {generating && (
              <div className="loading-panel" role="status" aria-live="polite" data-testid="status-generating">
                <span className="loading-mark" aria-hidden="true" />
                <span className="loading-copy">
                  <strong>Preparing an answer</strong>
                  <span>Generating a response to your question…</span>
                </span>
              </div>
            )}
            {loading && (
              <div className="loading-panel" role="status" aria-live="polite" data-testid="status-validating">
                <span className="loading-mark" aria-hidden="true" />
                <span className="loading-copy">
                  <strong>Independent review in progress</strong>
                  <span>Verifier agents are assessing the answer and evidence…</span>
                </span>
              </div>
            )}
            {error && <div className="error-message" role="alert" data-testid="status-error">{error}</div>}
          </>
        ) : (
          <>
            <header className="results-header">
              <div className="results-heading-row">
                <div>
                  <div className="eyebrow">Validation complete</div>
                  <h1>Decision record</h1>
                  <p className="results-question" data-testid="text-result-question">{submittedQuestion}</p>
                </div>
                <button
                  className="back-button"
                  onClick={() => setShowResults(false)}
                  type="button"
                  data-testid="button-back-to-answer"
                >
                  <span className="back-arrow" aria-hidden="true">←</span> Answer
                </button>
              </div>
            </header>

            <div className="results-content">
              <section className="final-result-card" aria-label="Final validation decision">
                <div className="final-result-left">
                  <div className="final-label">Final score</div>
                  <div className="final-score" data-testid="text-final-score">
                    {getScorePercentage(result?.final_score)}<span>%</span>
                  </div>
                </div>
                <div className="final-result-right decision-block">
                  <div className="final-label">Final decision</div>
                  <div
                    className={`final-status ${status === "passed" ? "final-passed" : status === "failed" ? "final-failed" : "final-uncertain"}`}
                    data-testid="status-final-decision"
                    aria-label={`Final decision: ${status}`}
                  >
                    {status}
                  </div>
                  <div className="decision-caption">Determined from the independent verifier votes below.</div>
                </div>
              </section>

              <section className="verifier-section" aria-labelledby="verifier-heading">
                <div className="section-title-row">
                  <h2 id="verifier-heading">Verifier votes</h2>
                  <span className="section-kicker">{String(voteResults.length).padStart(2, "0")} voting agents</span>
                </div>
                {voteResults.length > 0 ? (
                  <div className="verifier-grid">
                    {voteResults.map((verifier, index) => (
                      <article
                        className="verifier-card"
                        key={`${verifier.verifier_name || "verifier"}-${index}`}
                        style={{ animationDelay: `${Math.min(index * 55, 275)}ms` }}
                        data-testid={`card-verifier-${index}`}
                      >
                        <div className="verifier-top">
                          <div className="verifier-title">
                            <span className="verifier-index">AGENT {String(index + 1).padStart(2, "0")}</span>
                            <h3>{verifier.verifier_name || `Verifier ${index + 1}`}</h3>
                          </div>
                          <span className={`status-badge ${verifier.passed ? "" : "failed"}`} data-testid={`status-verifier-${index}`}>
                            {verifier.passed ? "Passed" : "Failed"}
                          </span>
                        </div>
                        <div className="score-row">
                          <div className="score-number" data-testid={`text-verifier-score-${index}`}>
                            {getScorePercentage(verifier.score)}%
                          </div>
                          <span className="score-caption">confidence score</span>
                        </div>
                        <div className="score-bar" aria-label={`Score ${getScorePercentage(verifier.score)} percent`}>
                          <div className="score-fill" style={{ width: `${scoreBarWidth(verifier.score)}%` }} />
                        </div>
                        {verifier.reasoning && (
                          <p className="reasoning" data-testid={`text-verifier-reasoning-${index}`}>{verifier.reasoning}</p>
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="no-verifiers" data-testid="text-no-verifiers">
                    <strong>No voting results to display</strong>
                    This validation response did not include verifier results with a voting role.
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;