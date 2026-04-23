import { useState, useEffect, useRef } from "react";
import { submitExam } from "../api/client";

const QUESTIONS = [
  "Explain the difference between supervised and unsupervised learning.",
  "Write a Python function to reverse a linked list.",
  "What is the time complexity of QuickSort in the worst case?",
  "Describe the concept of Retrieval-Augmented Generation (RAG).",
  "What is the difference between INNER JOIN and LEFT JOIN in SQL?",
];

export default function TakeExam({ exam, onDone }) {
  const [userName, setUserName] = useState("");
  const [answers, setAnswers] = useState({});
  const [pasteDetected, setPasteDetected] = useState(false);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [tabSwitches, setTabSwitches] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [startTime]);

  // Tab-switch / focus-loss detection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitches((n) => n + 1);
        setWarnings((w) => w.includes("tab") ? w : [...w, "tab"]);
      }
    };
    const handleBlur = () => {
      setTabSwitches((n) => n + 1);
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleBlur);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleBlur);
    };
  }, []);

  const handlePaste = (qId) => {
    setPasteDetected(true);
    if (!warnings.includes("paste")) {
      setWarnings((w) => [...w, "paste"]);
    }
  };

  const handleAnswer = (qId, value) => {
    setAnswers((prev) => ({ ...prev, [qId]: value }));
  };

  const handleSubmit = async () => {
    if (!userName.trim()) {
      setError("Please enter your name before submitting.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const r = await submitExam(exam.id, {
        user_name: userName.trim(),
        answers,
        time_taken_seconds: elapsed,
        paste_detected: pasteDetected,
        tab_switch_count: tabSwitches,
      });
      setResult(r.data);
      setSubmitted(true);
      clearInterval(timerRef.current);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const timeLeft = exam.duration * 60 - elapsed;
  const timeColor = timeLeft < 120 ? "red" : timeLeft < 300 ? "orange" : "inherit";

  const fmt = (s) => {
    const m = Math.floor(Math.abs(s) / 60);
    const sec = Math.abs(s) % 60;
    return `${s < 0 ? "-" : ""}${m}:${sec.toString().padStart(2, "0")}`;
  };

  if (submitted && result) {
    return (
      <div className="dashboard">
        <div className={`result-card ${result.suspicious ? "flagged-card" : "clean-card"}`}>
          <div className="result-icon">{result.suspicious ? "🚨" : "✅"}</div>
          <h2>{result.suspicious ? "Submission Flagged" : "Submission Accepted"}</h2>
          <p><strong>Name:</strong> {result.user_name}</p>
          <p><strong>Exam:</strong> {exam.title}</p>
          <p><strong>Time taken:</strong> {result.time_taken_seconds}s</p>
          {result.suspicious && (
            <div className="flags-list">
              <strong>Detected issues:</strong>
              <ul>
                {result.flag_reasons.map((r, i) => (
                  <li key={i} className="flag-item">{r}</li>
                ))}
              </ul>
              {result.audit_log && (
                <div className="audit-log">
                  <strong>🤖 AI Audit Note:</strong>
                  <p>{result.audit_log}</p>
                </div>
              )}
            </div>
          )}
          <button className="btn primary" onClick={onDone} style={{ marginTop: "1.5rem" }}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="exam-header">
        <div>
          <h1 className="page-title">{exam.title}</h1>
          <p className="page-sub">Duration: {exam.duration} minutes • Proctoring active</p>
        </div>
        <div className="timer" style={{ color: timeColor }}>
          {timeLeft >= 0 ? fmt(timeLeft) : `+${fmt(-timeLeft)}`}
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="warning-bar">
          {warnings.includes("paste") && <div>⚠️ Paste event detected — recorded by proctoring system.</div>}
          {warnings.includes("tab") && <div>👁️ Tab switch detected ({tabSwitches}x) — recorded by proctoring system.</div>}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <div className="section">
        <label className="field-label">Your Name *</label>
        <input
          className="input"
          placeholder="Enter your full name"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
        />
      </div>

      {QUESTIONS.map((q, i) => {
        const qId = `q${i + 1}`;
        return (
          <div key={qId} className="question-card">
            <div className="question-num">Question {i + 1}</div>
            <p className="question-text">{q}</p>
            <textarea
              className="textarea"
              rows={5}
              placeholder="Type your answer here…"
              value={answers[qId] || ""}
              onChange={(e) => handleAnswer(qId, e.target.value)}
              onPaste={() => handlePaste(qId)}
            />
          </div>
        );
      })}

      <button
        className="btn primary submit-btn"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "Submitting…" : "Submit Exam →"}
      </button>
    </div>
  );
}
