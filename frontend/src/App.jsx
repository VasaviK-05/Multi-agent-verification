import { useState } from "react";
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

  const handleQuestionChange = (e) => {
    const textarea = e.target;

    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;

    setQuestion(textarea.value);
  };

  const handleContextChange = (e) => {
    const textarea = e.target;

    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;

    setContext(textarea.value);
  };

  const enterPresentationMode = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error("Fullscreen mode could not be enabled:", error);
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
    if (!question.trim()) {
      setError("Please enter a question first.");
      return;
    }

    setGenerating(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/generate-answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate answer.");
      }

      const data = await response.json();

      setSubmittedQuestion(question.trim());
      setAnswer(data.answer || "");
    } catch (err) {
      setError(err.message || "Unable to generate answer.");
    } finally {
      setGenerating(false);
    }
  };

  const validateAnswer = async (providedContext = "") => {
    if (!question.trim() || !answer.trim()) {
      setError("Question and answer are required.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/validate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
          answer: answer.trim(),
          context: providedContext.trim() || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed.");
      }

      const data = await response.json();

      setResult(data);
      setShowResults(true);

      const historyItem = {
        question: question,
        answer: answer,
        context: providedContext,
        result: data,
      };

      setHistory((prev) => [historyItem, ...prev]);
    } catch (err) {
      setError(err.message || "Unable to validate the answer.");
    } finally {
      setLoading(false);
    }
  };

  const submitContext = async () => {
    await validateAnswer(context);
  };

  const skipContext = async () => {
    setContext("");
    await validateAnswer("");
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
    if (score === null || score === undefined) {
      return 0;
    }

    return Math.round(score * 100);
  };

  const getStatusClass = (verifier) => {
    if (verifier.metadata?.pipeline_role === "abstention") {
      return "abstained";
    }

    return verifier.passed ? "passed" : "failed";
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span></span>
          </div>

          <div className="brand-name">
            <strong>MAV</strong>
            <span>Multi-Agent Validator</span>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewChat}
        >
          <span className="plus">+</span>
          <span>New Validation</span>
        </button>

        <button
          className="presentation-button"
          onClick={enterPresentationMode}
        >
          ⛶ Presentation Mode
        </button>

        <div className="previous-section">
          <h3>PREVIOUS QUESTIONS</h3>

          {history.length === 0 ? (
            <p className="empty-history">
              Your validated questions will appear here.
            </p>
          ) : (
            <div className="history-list">
              {history.map((item, index) => (
                <button
                  key={index}
                  className="history-item"
                  onClick={() => openHistory(item)}
                >
                  {item.question}
                </button>
              ))}
            </div>
          )}
        </div>
      </aside>

      <main className="main-content">
        {!showResults ? (
          <>
            <div className="page-header">
              <div className="eyebrow">
                MULTI-AGENT SYSTEM
              </div>

              <h1>Answer Validation</h1>
            </div>

            <div className="chat-container">
              {!submittedQuestion && !answer ? (
                <div className="welcome-area">
                  <div className="welcome-icon brand-mark">
                    <span></span>
                  </div>

                  <h2>Ask a question</h2>

                  <p>
                    Generate an answer with Llama and validate it
                    using multiple independent agents.
                  </p>
                </div>
              ) : (
                <div className="conversation">
                  {submittedQuestion && (
                    <div className="message user-message">
                      <div className="message-label">
                        You
                      </div>

                      <div className="user-bubble">
                        {submittedQuestion}
                      </div>
                    </div>
                  )}

                  {answer && (
                    <div className="message ai-message">
                      <div className="ai-response">
                        {answer}
                      </div>
                    </div>
                  )}

                  {answer && (
                    <div className="message ai-message context-message">
                      <div className="ai-response context-response">
                        Do you have any supporting context?
                      </div>

                      <div className="context-hint">
                        Optional — it can help the verification agents
                        assess the answer.
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {!answer && (
              <div className="composer-area">
                <div className="composer">
                  <textarea
                    className="question-composer"
                    placeholder="Ask a question..."
                    value={question}
                    onChange={handleQuestionChange}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        generateAnswer();
                      }
                    }}
                    rows="1"
                  />

                  <button
                    className="send-button"
                    onClick={generateAnswer}
                    disabled={generating}
                    title="Generate Answer"
                  >
                    {generating ? "..." : "↑"}
                  </button>
                </div>

                <p className="composer-hint">
                  Press Enter to generate an answer
                </p>
              </div>
            )}

            {answer && !loading && (
              <div className="composer-area context-composer-area">
                <div className="composer">
                  <textarea
                    className="question-composer"
                    placeholder="Add supporting context (optional)..."
                    value={context}
                    onChange={handleContextChange}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        submitContext();
                      }
                    }}
                    rows="1"
                  />

                  <button
                    className="send-button"
                    onClick={submitContext}
                    title="Validate Answer"
                  >
                    ↑
                  </button>
                </div>

                <button
                  className="skip-button"
                  onClick={skipContext}
                  disabled={loading}
                >
                  Skip & Validate
                </button>

                <p className="composer-hint">
                  Press Enter to validate with this context
                </p>
              </div>
            )}

            {loading && (
              <div className="validation-loading">
                <span className="loading-dot"></span>
                Validating your answer...
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </>
        ) : (
          <>
            <div className="results-header">
              <div className="eyebrow">
                MULTI-AGENT SYSTEM
              </div>

              <h1>Validation Results</h1>
            </div>

            <div className="verifier-section">
              <h2>Verifier Results</h2>

              <div className="verifier-grid">
                {result?.results
                  ?.filter(
                    (verifier) =>
                      verifier.metadata?.pipeline_role === "vote"
                  )
                  .map((verifier, index) => (
                    <div
                      className="verifier-card"
                      key={index}
                    >
                      <div className="verifier-top">
                        <h3>
                          {verifier.verifier_name}
                        </h3>

                        <span
                          className={`status-badge ${getStatusClass(
                            verifier
                          )}`}
                        >
                          {verifier.metadata?.pipeline_role ===
                          "abstention"
                            ? "Abstained"
                            : verifier.passed
                            ? "Passed"
                            : "Failed"}
                        </span>
                      </div>

                      <div className="score-number">
                        {getScorePercentage(verifier.score)}%
                      </div>

                      <div className="score-bar">
                        <div
                          className="score-fill"
                          style={{
                            width: `${getScorePercentage(
                              verifier.score
                            )}%`,
                          }}
                        ></div>
                      </div>

                      {verifier.reasoning && (
                        <p className="reasoning">
                          {verifier.reasoning}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            </div>

            <div className="final-result-card">
              <div className="final-result-left">
                <div className="final-label">
                  FINAL SCORE
                </div>

                <div className="final-score">
                  {getScorePercentage(
                    result?.final_score
                  )}
                  %
                </div>
              </div>

              <div className="final-result-right">
                <div className="final-label">
                  FINAL DECISION
                </div>

                <div
                  className={`final-status ${
                    result?.final_status === "passed"
                      ? "final-passed"
                      : result?.final_status === "failed"
                      ? "final-failed"
                      : "final-uncertain"
                  }`}
                >
                  {result?.final_status
                    ? result.final_status
                        .charAt(0)
                        .toUpperCase() +
                      result.final_status.slice(1)
                    : "Uncertain"}
                </div>
              </div>
            </div>

            <button
              className="back-button"
              onClick={() => setShowResults(false)}
            >
              ← Back
            </button>
          </>
        )}
      </main>
    </div>
  );
}

export default App;