import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const getResponseErrorMessage = async (response, fallback) => {
  const errorData = await response.json().catch(() => null);

  const detail = errorData?.detail;
  if (typeof detail?.message === "string" && detail.message.trim()) {
    return detail.message;
  }
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return fallback;
};

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
  const [creatingSession, setCreatingSession] = useState(false);
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

  // Synchronous refs prevent duplicate events before React re-renders. A view
  // revision invalidates responses after navigation, resets or a new attempt.
  const viewRevision = useRef(0);
  const generationRequest = useRef(null);
  const validationRequest = useRef(null);
  const pendingSession = useRef(null);
  const activeSession = useRef(null);
  const sessionsRevision = useRef(0);
  const questionsRevision = useRef(0);

  const selectSession = useCallback((sessionId) => {
    if (activeSession.current !== sessionId) {
      activeSession.current = sessionId;
      questionsRevision.current += 1;
      setSessionQuestions([]);
      setQuestionsLoading(false);
    }
    setActiveSessionId(sessionId);
  }, []);

  const resetConversation = () => {
    viewRevision.current += 1;
    generationRequest.current = null;
    validationRequest.current = null;
    pendingSession.current = null;
    setCreatingSession(false);
    setGenerating(false);
    setLoading(false);
    setQuestion("");
    setSubmittedQuestion("");
    setAnswer("");
    setContext("");
    setQuestionId(null);
    setResult(null);
    setShowResults(false);
    setFeedbackSubmitted(false);
    setError("");
    return viewRevision.current;
  };

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
    let cancelled = false;
    const revision = viewRevision.current;
    const listRevision = ++sessionsRevision.current;
    const fetchSessions = async () => {
      setSessionsLoading(true);

      try {
        const response = await fetch(`${API_URL}/sessions`);

        if (!response.ok) {
          throw new Error("Failed to load sessions.");
        }

        const data = await response.json();

        if (cancelled || sessionsRevision.current !== listRevision) return;
        setSessions(data);

        if (data.length > 0 && viewRevision.current === revision) {
          selectSession(data[0].session_id);
        }
      } catch (err) {
        console.error("Unable to load sessions:", err);
      } finally {
        if (!cancelled && sessionsRevision.current === listRevision) setSessionsLoading(false);
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
        if (!cancelled) setReputation(data);
      } catch (err) {
        console.error("Unable to load verifier reputation:", err);
      }
    };

    fetchReputation();
    return () => {
      cancelled = true;
      viewRevision.current += 1;
      generationRequest.current = null;
      validationRequest.current = null;
      pendingSession.current = null;
    };
  }, [selectSession]);

  useEffect(() => {
    if (!activeSessionId) {
      setSessionQuestions([]);
      setQuestionsLoading(false);
      return;
    }
    let cancelled = false;
    const revision = ++questionsRevision.current;
    const isCurrent = () => !cancelled && questionsRevision.current === revision && activeSession.current === activeSessionId;
    setSessionQuestions([]);

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

        if (isCurrent()) setSessionQuestions(data);
      } catch (err) {
        console.error("Unable to load session questions:", err);
        if (isCurrent()) setSessionQuestions([]);
      } finally {
        if (isCurrent()) setQuestionsLoading(false);
      }
    };

    fetchSessionQuestions();
    return () => { cancelled = true; };
  }, [activeSessionId]);

  const handleQuestionChange = (e) => {
    if (pendingSession.current || generationRequest.current || validationRequest.current) return;
    const textarea = e.target;

    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;

    setQuestion(textarea.value);
  };

  const handleContextChange = (e) => {
    if (pendingSession.current) return;
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
    if (pendingSession.current) return;
    // Invalidate old work, but retain the conversation until creation succeeds.
    const request = { revision: ++viewRevision.current };
    generationRequest.current = null;
    validationRequest.current = null;
    pendingSession.current = request;
    setGenerating(false);
    setLoading(false);
    setCreatingSession(true);
    setError("");
    const isCurrent = () => pendingSession.current === request && viewRevision.current === request.revision;

    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Validation" }),
      });
      if (!response.ok) throw new Error("Session creation failed.");
      const newSession = await response.json();
      if (!isCurrent()) return;
      if (typeof newSession?.session_id !== "string" || !newSession.session_id.trim()) {
        throw new Error("Invalid session response.");
      }
      sessionsRevision.current += 1;
      setSessionsLoading(false);
      setSessions((prev) => [newSession, ...prev]);
      selectSession(newSession.session_id);
      // Establish the ID before releasing the pending guard and clearing input.
      resetConversation();
    } catch {
      if (isCurrent()) setError("Unable to create a new session. Please try again.");
    } finally {
      if (isCurrent()) {
        pendingSession.current = null;
        setCreatingSession(false);
      }
    }
  };

  const generateAnswer = async () => {
    if (pendingSession.current || generationRequest.current || validationRequest.current) return;
    if (!question.trim()) {
      setError("Please enter a question first.");
      return;
    }

    const requestQuestion = question.trim();
    const request = { revision: resetConversation(), sessionId: activeSession.current };
    setQuestion(question);
    generationRequest.current = request;
    const isCurrent = () => generationRequest.current === request && viewRevision.current === request.revision;
    setGenerating(true);

    try {
      const response = await fetch(`${API_URL}/generate-answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: requestQuestion,
          session_id: request.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(await getResponseErrorMessage(response, "Failed to generate answer."));
      }

      const data = await response.json().catch(() => null);

      if (!isCurrent()) return;
      if (typeof data?.answer !== "string" || !data.answer.trim()) {
        throw new Error("The server did not return a valid answer. Please try again.");
      }
      setQuestionId(data.question_id ?? null);
      setSubmittedQuestion(requestQuestion);
      setAnswer(data.answer);
      if (request.sessionId) {
        const revision = ++questionsRevision.current;
        const isLatestList = () => questionsRevision.current === revision && activeSession.current === request.sessionId;
        setQuestionsLoading(true);
        try {
          const historyResponse = await fetch(`${API_URL}/sessions/${request.sessionId}/questions`);
          if (historyResponse.ok) {
            const items = await historyResponse.json();
            if (isCurrent() && isLatestList()) setSessionQuestions(items);
          }
        } catch {
          if (isCurrent()) setError("Answer saved, but session history could not be refreshed.");
        } finally {
          if (isLatestList()) setQuestionsLoading(false);
        }
      }
    } catch (err) {
      if (isCurrent()) setError(err.message || "Unable to generate answer.");
    } finally {
      if (isCurrent()) {
        generationRequest.current = null;
        setGenerating(false);
      }
    }
  };

  const validateAnswer = async (providedContext = "") => {
    if (pendingSession.current || generationRequest.current || validationRequest.current) return;
    if (!question.trim() || !answer.trim()) {
      setError("Question and answer are required.");
      return;
    }

    const request = { revision: viewRevision.current, sessionId: activeSession.current };
    validationRequest.current = request;
    const isCurrent = () => validationRequest.current === request && viewRevision.current === request.revision;
    setLoading(true);
    setError("");

    let failureMessage = "Unable to validate the answer. Please try again.";
    try {
      const response = await fetch(`${API_URL}/validate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
          answer,
          context: providedContext.trim() || null,
          session_id: request.sessionId,
          question_id: questionId,
        }),
      });

      if (!response.ok) {
        failureMessage = await getResponseErrorMessage(response, "Validation failed.");
        throw new Error("Validation request failed.");
      }

      const data = await response.json();

      if (!isCurrent()) return;
      setResult(data);
      setShowResults(true);

      if (request.sessionId) {
        const revision = ++questionsRevision.current;
        const isLatestList = () => questionsRevision.current === revision && activeSession.current === request.sessionId;
        setQuestionsLoading(true);
        try {
          const questionsResponse = await fetch(`${API_URL}/sessions/${request.sessionId}/questions`);
          if (questionsResponse.ok) {
            const questions = await questionsResponse.json();
            if (isCurrent() && isLatestList()) setSessionQuestions(questions);
          }
        } finally {
          if (isLatestList()) setQuestionsLoading(false);
        }
      }

      if (!isCurrent()) return;
      const historyItem = {
        question_id: questionId,
        session_id: request.sessionId,
        question: question,
        answer: answer,
        context: providedContext,
        result: data,
      };

      setHistory((prev) => [historyItem, ...prev]);
    } catch {
      if (isCurrent()) setError(failureMessage);
    } finally {
      if (isCurrent()) {
        validationRequest.current = null;
        setLoading(false);
      }
    }
  };

  const submitFeedback = async (isCorrect) => {
    const revision = viewRevision.current;
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

      if (viewRevision.current !== revision) return;
      setError("");
      setFeedbackSubmitted(true);
    } catch (requestError) {
      if (viewRevision.current !== revision) return;
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
    if (pendingSession.current) return;
    setContext("");
    await validateAnswer("");
  };

  const openHistory = (item) => {
    resetConversation();
    setQuestionId(item.question_id ?? null);
    selectSession(item.session_id ?? null);
    setQuestion(item.question);
    setSubmittedQuestion(item.question);
    setAnswer(item.answer);
    setContext(item.context || "");
    setResult(item.result);
    setShowResults(Boolean(item.result));
    setError("");
  };

  const getScorePercentage = (score) => {
    if (score === null || score === undefined) {
      return 0;
    }

    return Math.round(score * 100);
  };

  const isVerifierAbstention = (verifier, executionAudit) => {
    const isGameMode = ["game", "flexible_game"].includes(
      executionAudit?.execution_mode
    );
    const decision = verifier.metadata?.decision?.toUpperCase?.();
    const attempts = Array.isArray(executionAudit?.attempts)
      ? executionAudit.attempts
      : [];
    const attempt = attempts.find(
      (item) => item.verifier_name === verifier.verifier_name
    );

    return (
      verifier.metadata?.pipeline_role === "abstention" ||
      (isGameMode &&
        (decision === "UNSURE" ||
          decision === "UNCERTAIN" ||
          attempt?.state === "abstention"))
    );
  };

  const getStatusClass = (verifier, executionAudit) => {
    if (isVerifierAbstention(verifier, executionAudit)) {
      return "abstained";
    }

    return verifier.passed ? "passed" : "failed";
  };

  const isGameModeResult = ["game", "flexible_game"].includes(
    result?.execution_audit?.execution_mode
  );
  const verifierResults = (Array.isArray(result?.results) ? result.results : [])
    .filter((verifier) =>
      isGameModeResult || verifier.metadata?.pipeline_role === "vote"
    );
  const executionAudit = result?.execution_audit;
  const overrideReasons = Array.isArray(executionAudit?.override_reasons)
    ? executionAudit.override_reasons.filter(Boolean)
    : [];
  const auditTeam = Array.isArray(executionAudit?.team)
    ? executionAudit.team.filter(Boolean)
    : [];
  const attemptedVerifiers = Array.isArray(executionAudit?.attempted_verifiers)
    ? executionAudit.attempted_verifiers.filter(Boolean)
    : [];
  const auditAttempts = Array.isArray(executionAudit?.attempts)
    ? executionAudit.attempts
    : [];
  const auditComponents = Array.isArray(executionAudit?.components)
    ? executionAudit.components
    : [];
  const requiredCoverage = Array.isArray(executionAudit?.required)
    ? executionAudit.required
    : [];
  const achievedCoverage = Array.isArray(executionAudit?.achieved)
    ? executionAudit.achieved
    : [];
  const unresolvedCoverage = Array.isArray(executionAudit?.unresolved)
    ? executionAudit.unresolved
    : [];
  const compatibilityProofs = [
    ["Pre-dispatch", executionAudit?.pre_dispatch_compatibility_proof],
    ["Component", executionAudit?.resource_compatibility],
    ["Post-dispatch", executionAudit?.resource_compatibility_after],
    ["Singleton", executionAudit?.singleton_resource_compatibility],
    ["Reference", executionAudit?.reference_resource_compatibility],
    ["Reference post-dispatch", executionAudit?.reference_resource_compatibility_after],
  ].filter(([, proof]) => proof && typeof proof === "object");
  const hasExecutionDetails = Boolean(
    executionAudit &&
      (executionAudit.execution_mode ||
        executionAudit.policy_bundle_id ||
        executionAudit.policy_id ||
        executionAudit.artifact_id ||
        executionAudit.policy_category ||
        executionAudit.selected_strategy_id ||
        auditTeam.length > 0 ||
        attemptedVerifiers.length > 0 ||
        auditAttempts.length > 0 ||
        auditComponents.length > 0 ||
        requiredCoverage.length > 0 ||
        achievedCoverage.length > 0 ||
        unresolvedCoverage.length > 0 ||
        compatibilityProofs.length > 0 ||
        executionAudit.aggregation ||
        overrideReasons.length > 0)
  );
  const formattedFinalScore = isGameModeResult
    ? typeof result?.final_score === "number" &&
      Number.isFinite(result.final_score)
      ? `${result.final_score >= 0 ? "+" : ""}${result.final_score.toFixed(2)}`
      : "Unavailable"
    : `${getScorePercentage(result?.final_score)}%`;

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
          disabled={creatingSession}
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
                    resetConversation();
                    selectSession(session.session_id);
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
                      key={item.validation_id || `generated-${item.question_id}`}
                      className="history-item"
                      onClick={() => {
                        resetConversation();
                        setQuestionId(item.question_id ?? null);
                        setQuestion(item.question);
                        setSubmittedQuestion(item.question);
                        setAnswer(item.generated_answer);
                        setContext(item.context || "");
                        setResult(null);
                        setShowResults(false);
                        setError("");
                      }}
                    >
                      {item.question}
                      {item.history_state === "generated_only" && <small> - Not validated</small>}
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
                    Generate an answer and validate it
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
                    disabled={generating || loading || creatingSession}
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
                    disabled={generating || loading || creatingSession}
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
                    disabled={creatingSession}
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
                    disabled={creatingSession}
                    title="Validate Answer"
                  >
                    ↑
                  </button>

                </div>

              <div className="composer-actions">
                <button
                  className="skip-button"
                  onClick={skipContext}
                  disabled={loading || creatingSession}
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

                {verifierResults.length === 0 ? (
                  <div className="no-verifiers">
                    <strong>No verifier results</strong>
                    No verifier results were returned for this validation.
                  </div>
                ) : (
                  verifierResults.map((verifier, index) => (

                    <div
                      className="verifier-card"
                      key={index}
                    >

                      <div className="verifier-top">

                        <h3>
                          {verifier.verifier_name}
                        </h3>

                        <span
                          className={`status-badge ${getStatusClass(verifier, executionAudit)}`}
                        >
                          {isVerifierAbstention(verifier, executionAudit)
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

                  ))
                )}

              </div>

            </div>

            {/* ================= FINAL RESULT ================= */}

            <div className="final-result-card">

              <div className="final-result-left">

                <div className="final-label">
                  {isGameModeResult ? "FINAL SCORE · SIGNED" : "FINAL SCORE"}
                </div>

                <div className="final-score">
                  {formattedFinalScore}
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

            {hasExecutionDetails && (
              <section className="execution-audit-card">
                <h2>Game Execution</h2>
                <div className="execution-audit-grid">
                  {executionAudit.execution_mode && (
                    <div className="execution-audit-item">
                      <span>Execution mode</span>
                      <strong>{executionAudit.execution_mode}</strong>
                    </div>
                  )}
                  {executionAudit.policy_bundle_id && (
                    <div className="execution-audit-item">
                      <span>Policy bundle</span>
                      <strong>{executionAudit.policy_bundle_id}</strong>
                    </div>
                  )}
                  {executionAudit.policy_category && (
                    <div className="execution-audit-item">
                      <span>Policy category</span>
                      <strong>{executionAudit.policy_category}</strong>
                    </div>
                  )}
                  {executionAudit.policy_id && (
                    <div className="execution-audit-item">
                      <span>Policy ID</span>
                      <strong>{executionAudit.policy_id}</strong>
                    </div>
                  )}
                  {executionAudit.artifact_id && (
                    <div className="execution-audit-item">
                      <span>Artifact ID</span>
                      <strong>{executionAudit.artifact_id}</strong>
                    </div>
                  )}
                  {executionAudit.selected_strategy_id && (
                    <div className="execution-audit-item">
                      <span>Selected strategy</span>
                      <strong>{executionAudit.selected_strategy_id}</strong>
                    </div>
                  )}
                  {auditTeam.length > 0 && (
                    <div className="execution-audit-item">
                      <span>Selected verifier team</span>
                      <strong>{auditTeam.join(", ")}</strong>
                    </div>
                  )}
                  {executionAudit.aggregation && (
                    <div className="execution-audit-item">
                      <span>Aggregation</span>
                      <strong>{executionAudit.aggregation}</strong>
                    </div>
                  )}
                  {attemptedVerifiers.length > 0 && (
                    <div className="execution-audit-item">
                      <span>Attempted verifiers</span>
                      <strong>{attemptedVerifiers.join(", ")}</strong>
                    </div>
                  )}
                  {(requiredCoverage.length > 0 ||
                    achievedCoverage.length > 0 ||
                    unresolvedCoverage.length > 0) && (
                    <div className="execution-audit-item">
                      <span>Coverage</span>
                      <strong>
                        Required: {requiredCoverage.join(", ") || "none"}
                        {" · "}Achieved: {achievedCoverage.join(", ") || "none"}
                        {unresolvedCoverage.length > 0
                          ? ` · Unresolved: ${unresolvedCoverage.join(", ")}`
                          : ""}
                      </strong>
                    </div>
                  )}
                  {executionAudit.routing_signature && (
                    <div className="execution-audit-item">
                      <span>Route signature</span>
                      <strong>
                        {Array.isArray(executionAudit.routing_signature)
                          ? executionAudit.routing_signature.join(" · ")
                          : String(executionAudit.routing_signature)}
                      </strong>
                    </div>
                  )}
                  {auditComponents.length > 0 && (
                    <div className="execution-audit-item execution-audit-guards">
                      <span>Component decisions and coverage</span>
                      <ul>
                        {auditComponents.map((component, index) => (
                          <li key={component?.component_id || index}>
                            {component?.component_id || "Component"}
                            {component?.public_status
                              ? `: ${component.public_status}`
                              : ""}
                            {component?.binding_id
                              ? ` · binding ${component.binding_id}`
                              : ""}
                            {Array.isArray(component?.required)
                              ? ` · required ${component.required.join(", ")}`
                              : ""}
                            {Array.isArray(component?.achieved)
                              ? ` · achieved ${component.achieved.join(", ") || "none"}`
                              : ""}
                            {Array.isArray(component?.unresolved) &&
                            component.unresolved.length > 0
                              ? ` · unresolved ${component.unresolved.join(", ")}`
                              : ""}
                            {Array.isArray(component?.reasons) &&
                            component.reasons.length > 0
                              ? ` · guards ${component.reasons.join(", ")}`
                              : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {auditAttempts.length > 0 && (
                    <div className="execution-audit-item execution-audit-guards">
                      <span>Verifier attempts</span>
                      <ul>
                        {auditAttempts.map((attempt, index) => (
                          <li key={attempt?.call_id || index}>
                            {[attempt?.component_id, attempt?.verifier_name]
                              .filter(Boolean)
                              .join(" · ") || "Verifier attempt"}
                            {attempt?.state ? `: ${attempt.state}` : ""}
                            {attempt?.binding_id
                              ? ` · binding ${attempt.binding_id}`
                              : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {compatibilityProofs.length > 0 && (
                    <div className="execution-audit-item execution-audit-guards">
                      <span>Resource compatibility proofs</span>
                      <ul>
                        {compatibilityProofs.map(([label, proof]) => (
                          <li key={label}>
                            {label}: {proof.proof_id || proof.binding_id || "verified"}
                            {proof.historical_manifest_id
                              ? ` · historical ${proof.historical_manifest_id}`
                              : proof.historical_resource_manifest_id
                              ? ` · historical ${proof.historical_resource_manifest_id}`
                              : ""}
                            {proof.observed_manifest_id
                              ? ` · observed ${proof.observed_manifest_id}`
                              : proof.observed_resource_manifest_id
                              ? ` · observed ${proof.observed_resource_manifest_id}`
                              : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {overrideReasons.length > 0 && (
                    <div className="execution-audit-item execution-audit-guards">
                      <span>Guard / override reason</span>
                      <ul>
                        {overrideReasons.map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </section>
            )}

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
              onClick={() => {
                if (pendingSession.current) {
                  viewRevision.current += 1;
                  pendingSession.current = null;
                  setCreatingSession(false);
                }
                setShowResults(false);
              }}
            >
              ← Back
            </button>

          </>
        )}

        {error && (
          <div className="error-message">{error}</div>
        )}

      </main>

    </div>
  );
}

export default App;
