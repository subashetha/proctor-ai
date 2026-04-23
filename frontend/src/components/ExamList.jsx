import { useState, useEffect } from "react";
import { listExams } from "../api/client";

export default function ExamList({ onTakeExam }) {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listExams()
      .then((r) => setExams(r.data))
      .catch(() => setError("Failed to load exams. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading exams…</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="dashboard">
      <h1 className="page-title">Available Exams</h1>
      <p className="page-sub">Select an exam to begin. The proctoring system is always active.</p>

      {exams.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <p>No exams available. Create one first!</p>
        </div>
      ) : (
        <div className="exam-grid">
          {exams.map((exam) => (
            <div key={exam.id} className="exam-card">
              <div className="exam-card-header">
                <span className="exam-id">#{exam.id}</span>
                <span className="exam-duration">⏱ {exam.duration} min</span>
              </div>
              <h3 className="exam-title">{exam.title}</h3>
              <p className="exam-meta">Duration: {exam.duration} minutes</p>
              <button className="btn primary" onClick={() => onTakeExam(exam)}>
                Start Exam →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
