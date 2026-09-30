import { useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [context, setContext] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const generateAnswer = async () => {
    if (!question.trim()) {
      setError('Please enter a question first.')
      return
    }

    setGenerating(true)
    setError('')
    setAnswer('')
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/generate-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data = await response.json()

      setAnswer(data.answer)
    } catch (err) {
      setError(
        'Could not generate an answer. Make sure the FastAPI backend and Ollama are running.'
      )
    } finally {
      setGenerating(false)
    }
  }

  const validateAnswer = async (e) => {
    e.preventDefault()

    if (!question.trim() || !answer.trim()) {
      setError('Please enter a question and generate or enter an answer.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          answer,
          context: context.trim() || null,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(
        'Could not connect to the validation server. Make sure the FastAPI backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">MULTI-AGENT SYSTEM</p>
          <h1>Answer Validation Dashboard</h1>
          <p className="subtitle">
            Validate AI-generated answers using multiple independent
            verification agents.
          </p>
        </div>

        <div className="status-badge">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      <main className="dashboard">
        <section className="input-card">
          <div className="section-heading">
            <div>
              <p className="section-label">VALIDATION REQUEST</p>
              <h2>Enter an answer to validate</h2>
            </div>
          </div>

          <form onSubmit={validateAnswer}>
            <label htmlFor="question">Question</label>

            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What is the capital of France?"
              rows="3"
            />

            <button
              className="generate-button"
              type="button"
              onClick={generateAnswer}
              disabled={generating || loading}
            >
              {generating ? 'Generating Answer...' : 'Generate Answer'}
            </button>

            <label htmlFor="answer">Answer</label>

            <textarea
              id="answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Generate an answer using Llama or enter your own answer..."
              rows="4"
            />

            <label htmlFor="context">
              Context <span>(optional)</span>
            </label>

            <textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Add supporting context if available..."
              rows="3"
            />

            <button
              className="validate-button"
              type="submit"
              disabled={loading || generating}
            >
              {loading ? 'Validating...' : 'Validate Answer'}
            </button>
          </form>

          {error && <div className="error-message">{error}</div>}
        </section>

        <section className="flow-card">
          <div className="section-heading">
            <div>
              <p className="section-label">VALIDATION PIPELINE</p>
              <h2>How the system works</h2>
            </div>
          </div>

          <div className="flow">
            <div className="flow-step">
              <span>01</span>
              <strong>Question Analyzer</strong>
              <small>Analyzes question complexity</small>
              <em>ANALYSIS</em>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-step">
              <span>02</span>
              <strong>Verifier Selector</strong>
              <small>Selects suitable verifiers</small>
              <em>SELECTION</em>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-step">
              <span>03</span>
              <strong>Verifier Agents</strong>
              <small>Semantic · Evidence · Rule · Confidence</small>
              <em>VERIFICATION</em>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-step">
              <span>04</span>
              <strong>Decision Engine</strong>
              <small>Aggregates verification results</small>
              <em>DECISION</em>
            </div>
          </div>
        </section>

        {result && (
          <section className="results-section">
            <div className="result-summary">
              <div>
                <p className="section-label">FINAL DECISION</p>
                <h2>{result.final_status}</h2>
              </div>

              <div className="score">
                <span>Final Score</span>
                <strong>
                  {typeof result.final_score === 'number'
                    ? result.final_score.toFixed(2)
                    : '—'}
                </strong>
              </div>
            </div>

            <div className="verifier-grid">
              {result.results?.map((verifier) => (
                <div
                  className="verifier-card"
                  key={verifier.verifier_name}
                >
                  <div className="verifier-header">
                    <h3>{verifier.verifier_name}</h3>

                    <span
                      className={
                        verifier.passed
                          ? 'passed-badge'
                          : 'failed-badge'
                      }
                    >
                      {verifier.passed ? 'Passed' : 'Failed'}
                    </span>
                  </div>

                  <div className="verifier-score">
                    <div className="score-row">
                      <span>Verification Score</span>

                      <strong>
                        {typeof verifier.score === 'number'
                          ? verifier.score.toFixed(2)
                          : '—'}
                      </strong>
                    </div>

                    <div className="score-bar">
                      <div
                        className="score-fill"
                        style={{
                          width: `${
                            typeof verifier.score === 'number'
                              ? verifier.score * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>

                    <span className="score-percent">
                      {typeof verifier.score === 'number'
                        ? `${Math.round(
                            verifier.score * 100
                          )}% confidence`
                        : 'Score unavailable'}
                    </span>
                  </div>

                  <div className="reasoning">
                    <span>Reasoning</span>
                    <p>
                      {verifier.reasoning ||
                        'No reasoning provided.'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App