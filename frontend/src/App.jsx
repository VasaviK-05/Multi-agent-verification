import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [context, setContext] = useState("");
  const [questionId, setQuestionId] = useState(null);

  const [result, setResult] = useState(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const [history, setHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [reputation, setReputation] = useState([]);
  const [showReputation, setShowReputation] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const [sessionQuestions, setSessionQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  /*
   * Sessions are returned newest-first by the backend.
   * We display them as Session 1, Session 2, etc.
   * The actual session_id remains unchanged.
   */
  const getSessionLabel = (session, index) => {
    if (session?.title && /^Session \d+$/i.test(session.title)) {
      return session.title;
    }

    return `Session ${index + 1}`;
  };

  useEffect(() => {
    const fetchSessions = async () => {
      setSessionsLoading(true);

      try {
        const response = await fetch(`${API_URL}/sessions`);

        if (!response.ok) {
          throw new Error("Failed to load sessions.");
        }

        const data = await response.json();

        setSessions(data);

        if (data.length > 0) {
          setActiveSessionId(data[0].session_id);
        }
      } catch (err) {
        console.error("Unable to load sessions:", err);
      } finally {
        setSessionsLoading(false);
      }
    };

    fetchSessions();
     const fetchReputation = async () => {
      try {
        const response = await fetch(`${API_URL}/reputation`);

        if (!response.ok) {
          throw new Error("Failed to load verifier reputation.");
        }

        const data = await response.json();
        setReputation(data);
      } catch (err) {
        console.error("Unable to load verifier reputation:", err);
      }
    };

    fetchReputation();
  }, []);

  useEffect(() => {
    if (!activeSessionId) {
      setSessionQuestions([]);
      return;
    }

    const fetchSessionQuestions = async () => {
      setQuestionsLoading(true);

      try {
        const response = await fetch(
          `${API_URL}/sessions/${activeSessionId}/questions`
        );

        if (!response.ok) {
          throw new Error("Failed to load session questions.");
        }

        const data = await response.json();

        setSessionQuestions(data);
      } catch (err) {
        console.error("Unable to load session questions:", err);
        setSessionQuestions([]);
      } finally {
        setQuestionsLoading(false);
      }
    };

    fetchSessionQuestions();
  }, [activeSessionId]);

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

  const startNewChat = async () => {
    setError("");

    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "New Validation",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create a new session.");
      }

      const newSession = await response.json();

      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.session_id);

      setQuestion("");
      setSubmittedQuestion("");
      setAnswer("");
      setContext("");
      setResult(null);
      setFeedbackSubmitted(false);
      setSessionQuestions([]);
      setShowResults(false);
      setQuestionId(null);
    } catch (err) {
      setError(err.message || "Unable to create a new session.");
    }
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

      setQuestionId(data.question_id);
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
          session_id: activeSessionId,
          question_id: questionId,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed.");
      }

      const data = await response.json();

      setResult(data);
      setShowResults(true);

      if (activeSessionId) {
        const questionsResponse = await fetch(
          `${API_URL}/sessions/${activeSessionId}/questions`
        );

        if (questionsResponse.ok) {
          const questions = await questionsResponse.json();
          setSessionQuestions(questions);
        }
      }

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

  const submitFeedback = async (isCorrect) => {
    if (!result?.validation_id) {
      setError("No validation result is available for feedback.");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          validation_id: result.validation_id,
          is_correct: isCorrect,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        throw new Error(
          errorData?.detail || "Failed to submit feedback."
        );
      }

      setError("");
      setFeedbackSubmitted(true);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to submit feedback. Please try again."
      );
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

      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">
         
    <div className="brand">
      <div className="brand-mark">
        <span></span>
          </div>

        <div className="brand-name">
          <strong>MAV</strong>
           <span>Multi-Agent Validator</span>
         </div>

       <button
          className="settings-button"
          onClick={() => setShowReputation((prev) => !prev)}
          title="Verifier Reputation"
       >
        ⚙
       </button>
    </div>

    {showReputation && (
  <div className="reputation-panel">
    <div className="reputation-panel-header">
      <span>VERIFIER REPUTATION</span>
      <button
        className="reputation-close"
        onClick={() => setShowReputation(false)}
        title="Close"
      >
        ×
      </button>
    </div>

    {reputation.length === 0 ? (
      <p className="reputation-empty">No reputation data available.</p>
    ) : (
      Object.entries(
        reputation.reduce((groups, item) => {
          const score =
            (item.alpha / (item.alpha + item.beta)) * 100;

          if (
            !groups[item.verifier_name] ||
            score > groups[item.verifier_name].score
          ) {
            groups[item.verifier_name] = {
              domain: item.domain,
              score,
            };
          }

          return groups;
        }, {})
      ).map(([verifierName, item]) => (
        <div className="reputation-item" key={verifierName}>
          <div className="reputation-verifier">
            {verifierName}
          </div>

          <div className="reputation-domain">
            Strongest domain: {item.domain}
          </div>

          <div className="reputation-score">
            <span>Reputation</span>
            <strong>{item.score.toFixed(1)}%</strong>
          </div>
        </div>
      ))
    )}
  </div>
)}
        
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

          <div className="previous-heading">
            <span>SESSIONS</span>
            {sessions.length > 0 && (
              <span className="history-count">
                {sessions.length}
              </span>
            )}
          </div>

          {sessionsLoading ? (
            <p className="empty-history">
              Loading sessions...
            </p>
          ) : sessions.length === 0 ? (
            <p className="empty-history">
              No sessions yet.
            </p>
          ) : (
            <div className="history-list">

              {sessions.map((session, index) => (
                <button
                  key={session.session_id}
                  className={`history-item ${
                    activeSessionId === session.session_id
                      ? "active"
                      : ""
                  }`}
                  onClick={() => {
                    setActiveSessionId(session.session_id);
                    setShowResults(false);
                    setResult(null);
                    setError("");
                  }}
                >
                  {getSessionLabel(session, index)}
                </button>
              ))}

            </div>
          )}

          {activeSessionId && (
            <div className="session-questions">

              <div className="previous-heading questions-heading">
                <span>QUESTIONS</span>
              </div>

              {questionsLoading ? (
                <p className="empty-history">
                  Loading questions...
                </p>
              ) : sessionQuestions.length === 0 ? (
                <p className="empty-history">
                  No questions in this session.
                </p>
              ) : (
                <div className="history-list">

                  {sessionQuestions.map((item) => (
                    <button
                      key={item.validation_id}
                      className="history-item"
                      onClick={() => {
                        setQuestionId(item.question_id);
                        setQuestion(item.question);
                        setSubmittedQuestion(item.question);
                        setAnswer(item.generated_answer);
                        setResult(null);
                        setShowResults(false);
                        setError("");
                      }}
                    >
                      {item.question}
                    </button>
                  ))}

                </div>
              )}

            </div>
          )}

        </div>

      </aside>

      {/* ================= MAIN CONTENT ================= */}

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

              {/* ================= EMPTY STATE ================= */}

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

                /* ================= CONVERSATION ================= */

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

                      <div className="message-label">
                        MAV
                      </div>

                      <div className="ai-response">
                        {answer}
                      </div>

                    </div>
                  )}

                  {answer && (
                    <div className="message ai-message context-message">

                      <div className="message-label">
                        MAV
                      </div>

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

            {/* ================= QUESTION INPUT ================= */}

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

            {/* ================= CONTEXT INPUT ================= */}

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

              <div className="composer-actions">
                <button
                  className="skip-button"
                  onClick={skipContext}
                  disabled={loading}
                >
                  Skip & Validate
                </button>
              </div>

              <p className="composer-hint">
                Press Enter to validate with this context
              </p>  

              </div>
            )}

            {/* ================= VALIDATION LOADING ================= */}

            {loading && (
              <div className="validation-loading">
                <span className="loading-dot"></span>
                Validating your answer...
              </div>
            )}

          

            {/* ================= ERROR ================= */}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

          </>
        ) : (

          /* ================= RESULTS PAGE ================= */

          <>

            <div className="results-header">

              <div className="eyebrow">
                MULTI-AGENT SYSTEM
              </div>

              <h1>Validation Results</h1>

            </div>

            {/* ================= VERIFIER RESULTS ================= */}

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

            {/* ================= FINAL RESULT ================= */}

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

            {/* ================= FEEDBACK ================= */}

            <div className="feedback-section">

              <h3>
                Was this validation helpful?
              </h3>

              {!feedbackSubmitted ? (

                <div className="feedback-buttons">

                  <button
                    className="feedback-button"
                    onClick={() =>
                      submitFeedback(true)
                    }
                  >
                    ✓ Correct
                  </button>

                  <button
                    className="feedback-button"
                    onClick={() =>
                      submitFeedback(false)
                    }
                  >
                    ✕ Incorrect
                  </button>

                </div>

              ) : (

                <p className="feedback-success">
                  Thank you! Your feedback has been recorded.
                </p>

              )}

            </div>

            {/* ================= BACK BUTTON ================= */}

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