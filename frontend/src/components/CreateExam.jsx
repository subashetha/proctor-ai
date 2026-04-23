import { useState } from "react";
import { createExam } from "../api/client";

export default function CreateExam({ onCreated }) {
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (!title.trim()) return setError("Title is required.");
    if (duration <= 0) return setError("Duration must be positive.");
    setLoading(true);
    setError(null);
    try {
      await createExam({ title: title.trim(), duration: parseInt(duration) });
      setSuccess(true);
      setTimeout(onCreated, 1200);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create exam.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <h1 className="page-title">Create New Exam</h1>
      <p className="page-sub">Set up a new proctored exam session.</p>

      <div className="form-card">
        {error && <div className="error">{error}</div>}
        {success && <div className="success">✅ Exam created! Redirecting…</div>}

        <div className="field">
          <label className="field-label">Exam Title *</label>
          <input
            className="input"
            placeholder="e.g. Python Fundamentals"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="field">
          <label className="field-label">Duration (minutes) *</label>
          <input
            className="input"
            type="number"
            min={1}
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          />
        </div>

        <button
          className="btn primary"
          onClick={handleSubmit}
          disabled={loading || success}
        >
          {loading ? "Creating…" : "Create Exam →"}
        </button>
      </div>
    </div>
  );
}
